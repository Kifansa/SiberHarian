"""Halaman publik dan endpoint data dashboard SiberHarian."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from src.analytics.trend_analyzer import susun_statistik_dashboard
from src.storage.db import (
    ambil_data_terbaru_per_kategori,
    ambil_prediksi_tren_terakhir,
    ambil_riwayat_dikelompokkan_per_hari,
    ambil_riwayat_tren,
    ambil_statistik_publik,
    simpan_prediksi_tren,
)
from src.web.auth import (
    ambil_user_dari_sesi,
    cek_admin_autentikasi,
    hapus_cookie_sesi,
    pasang_cookie_sesi,
    token_csrf_request,
)
from src.web.templating import templates

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/api/auth/login")
async def api_auth_login(request: Request):
    """Memvalidasi kredensial admin dan menerbitkan session cookie."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            {"status": "error", "message": "Format data tidak valid."},
            status_code=400,
        )

    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    from src.utils.admin_auth import verifikasi_admin

    is_valid, _role = verifikasi_admin(username, password)
    if is_valid:
        res = JSONResponse({"status": "ok", "redirect": "/admin"})
        pasang_cookie_sesi(res, username)
        return res

    return JSONResponse(
        {"status": "error", "message": "Nama pengguna atau kata sandi tidak valid."},
        status_code=401,
    )


@router.post("/api/auth/logout")
async def api_auth_logout():
    """Menghapus session cookie admin dan logout."""
    res = JSONResponse({"status": "ok", "redirect": "/"})
    hapus_cookie_sesi(res)
    return res


@router.get("/api/auth/status")
async def api_auth_status(request: Request):
    """Mengecek status autentikasi admin beserta role aktif."""
    user = ambil_user_dari_sesi(request)
    if user:
        return {
            "authenticated": True,
            "username": user["username"],
            "role": user.get("role", "viewer"),
            "csrf_token": token_csrf_request(request),
        }
    return {"authenticated": False, "username": None, "role": None}


@router.get("/api/beranda")
async def ambil_beranda():
    """Tab Beranda: berita intelijen & insiden dari tanggal terbarunya."""
    data = ambil_data_terbaru_per_kategori(hari=7)
    ada_data = bool(data.get("berita"))
    return {
        "status": "ok" if ada_data else "kosong",
        "tanggal_berita": data.get("tanggal_berita"),
        "waktu_terakhir_scraping": data.get("waktu_terakhir_scraping"),
        "berita": data.get("berita", []),
    }


@router.get("/api/arsip")
async def ambil_arsip():
    """Tab Arsip: seluruh grup tanggal (7 hari terakhir), terbaru lebih dulu."""
    grup_per_tanggal = ambil_riwayat_dikelompokkan_per_hari(hari=7)
    daftar_hari = [
        {"tanggal": tanggal, "berita": isi.get("berita", [])}
        for tanggal, isi in grup_per_tanggal.items()
    ]
    return {"status": "ok" if daftar_hari else "kosong", "hari": daftar_hari}


@router.get("/api/tren")
async def ambil_tren():
    """Tab Tren Siber: prediksi dan agregat statistik dari database."""
    prediksi = ambil_prediksi_tren_terakhir()
    if not prediksi:
        return {
            "status": "kosong",
            "prediksi_berita": "",
            "tanggal_dihitung": None,
            "statistik": None,
        }

    statistik = None
    raw_stat = dict(prediksi).get("statistik_json")
    if raw_stat:
        try:
            statistik = json.loads(raw_stat)
        except Exception:
            statistik = None

    if statistik:
        statistik.pop("threat_posture", None)
        statistik.pop("matriks_tindakan", None)
        statistik.pop("skor_threat_posture", None)

        perlu_simpan_ulang = False
        if "taktik_mitre" not in statistik or "cve_watchlist" not in statistik:
            from src.analytics.trend_analyzer import (
                ekstrak_radar_cve_watchlist,
                hitung_distribusi_taktik_mitre,
            )

            df_14 = ambil_riwayat_tren(hari=14)
            if not df_14.empty:
                if "taktik_mitre" not in statistik:
                    statistik["taktik_mitre"] = hitung_distribusi_taktik_mitre(df_14)
                if "cve_watchlist" not in statistik:
                    statistik["cve_watchlist"] = ekstrak_radar_cve_watchlist(df_14)
            else:
                statistik.setdefault("taktik_mitre", [])
                statistik.setdefault("cve_watchlist", [])
            perlu_simpan_ulang = True

        if perlu_simpan_ulang or (
            raw_stat and ("threat_posture" in raw_stat or "matriks_tindakan" in raw_stat)
        ):
            try:
                simpan_prediksi_tren(
                    prediksi["prediksi_berita"],
                    kasus_wilayah_ai=dict(prediksi).get("kasus_wilayah_ai"),
                    statistik_json=json.dumps(statistik, ensure_ascii=False),
                )
            except Exception as err:
                logger.error(f"Gagal memperbarui cache statistik ke DB: {err}")

    if not statistik:
        df_14 = ambil_riwayat_tren(hari=14)
        statistik = susun_statistik_dashboard(df_14)
        try:
            simpan_prediksi_tren(
                prediksi["prediksi_berita"],
                kasus_wilayah_ai=dict(prediksi).get("kasus_wilayah_ai"),
                statistik_json=json.dumps(statistik, ensure_ascii=False),
            )
        except Exception as err:
            logger.error(f"Gagal menyimpan cache statistik ke DB: {err}")

    kasus_wilayah_ai = None
    raw_ai = dict(prediksi).get("kasus_wilayah_ai")
    if raw_ai:
        try:
            kasus_wilayah_ai = json.loads(raw_ai)
        except Exception:
            kasus_wilayah_ai = None

    if kasus_wilayah_ai and statistik:
        statistik["kasus_wilayah_ai"] = kasus_wilayah_ai

    return {
        "status": "ok",
        "prediksi_berita": dict(prediksi).get("prediksi_berita", ""),
        "tanggal_dihitung": dict(prediksi).get("tanggal_dihitung"),
        "statistik": statistik,
    }


@router.get("/api/statistik-publik")
async def api_statistik_publik():
    """Tab Statistik Publik: agregat visualisasi fakta siber untuk masyarakat."""
    return ambil_statistik_publik()


@router.get("/api/ensiklopedia")
async def api_ensiklopedia(q: Optional[str] = None):
    """Eksplorasi ensiklopedia referensi standar keamanan siber."""
    from src.analytics.encyclopedia_lookup import (
        get_all_framework_counts,
        search_encyclopedia,
    )

    if q:
        keywords = [k.strip() for k in q.split(",") if k.strip()]
        return {"query": q, "hasil": search_encyclopedia(keywords)}
    return {"status": "ok", "frameworks": get_all_framework_counts()}


@router.get("/")
async def halaman_utama(request: Request):
    """Halaman publik terpadu: dashboard dan arsip."""
    from src.storage.db import DEFAULT_DB_PATH

    statistik = None
    try:
        statistik = ambil_statistik_publik(DEFAULT_DB_PATH)
    except Exception as e:
        logger.error(f"Gagal mengambil statistik SSR: {e}")
    return templates.TemplateResponse(
        request, "index.html", context={"statistik": statistik}
    )


@router.get("/login")
async def halaman_login(request: Request):
    """Halaman login admin; redirect ke /admin bila sesi sudah valid."""
    if cek_admin_autentikasi(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(request, "login.html")


@router.get("/admin")
async def halaman_admin(request: Request):
    """Panel operasional Tim CTI CSIRT Jatim."""
    user = ambil_user_dari_sesi(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
        request,
        "admin.html",
        {"is_superadmin": user.get("role") == "superadmin"},
    )
