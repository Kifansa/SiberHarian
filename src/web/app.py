"""
Web demo interface untuk pipeline cyber news digest. Endpoint untuk
memicu pipeline lengkap (scraping -> summarization -> arsip & tren)
dengan progress log real-time (SSE), dan endpoint terpisah untuk
dashboard publik (Berita & Statistik, Arsip) serta panel administratif
Tim CTI Diskominfo Jatim dengan navigasi sidebar.
"""
import asyncio
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import queue
import threading
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.analytics.pasca_proses import proses_arsip_dan_tren
from src.analytics.trend_analyzer import susun_statistik_dashboard
from src.pipeline_harian import jalankan_pipeline_harian
from src.storage.db import (
    ambil_prediksi_tren_terakhir,
    ambil_riwayat_dikelompokkan_per_hari,
    ambil_riwayat_tren,
    simpan_prediksi_tren,
    ambil_data_terbaru_per_kategori,
    ambil_statistik_publik,
)
from src.summarizer.llm_summarizer import proses_summarization_harian

BASE_DIR = Path(__file__).parent

app = FastAPI(title="SiberHarian - CSIRT Diskominfo Jatim")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

log_queue: "queue.Queue[dict]" = queue.Queue()
sedang_berjalan = False

SESSION_SECRET = os.getenv("SESSION_SECRET", "siberharian-csirt-jatim-auth-secret-key-2026")


@app.on_event("startup")
async def on_startup():
    """Inisialisasi database dan pastikan tabel serta akun admin siap."""
    from src.storage.db import DEFAULT_DB_PATH, init_db
    init_db(DEFAULT_DB_PATH)


def buat_token_sesi(username: str) -> str:
    sig = hmac.new(SESSION_SECRET.encode(), username.encode(), hashlib.sha256).hexdigest()
    return f"{username}:{sig}"


def ambil_user_dari_sesi(request: Request) -> Optional[dict]:
    cookie = request.cookies.get("cti_session")
    if not cookie or ":" not in cookie:
        return None
    parts = cookie.split(":", 1)
    if len(parts) != 2:
        return None
    username, sig = parts
    expected_sig = hmac.new(SESSION_SECRET.encode(), username.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None
    from src.utils.admin_auth import get_admin_user
    return get_admin_user(username)


def cek_admin_autentikasi(request: Request) -> bool:
    return ambil_user_dari_sesi(request) is not None


def cek_superadmin_autentikasi(request: Request) -> bool:
    user = ambil_user_dari_sesi(request)
    return user is not None and user.get("role") == "superadmin"


class QueueLogHandler(logging.Handler):
    """Tiap log record didorong ke queue supaya bisa di-stream real-time ke frontend."""

    def emit(self, record: logging.LogRecord) -> None:
        log_queue.put({"type": "log", "level": record.levelname, "message": self.format(record)})


def _pasang_handler_global() -> None:
    handler = QueueLogHandler()
    handler.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s", datefmt="%H:%M:%S"))
    root_logger = logging.getLogger()
    if not any(isinstance(h, QueueLogHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


_pasang_handler_global()


def _jalankan_pipeline_di_thread() -> None:
    """
    Menjalankan pipeline lengkap secara sinkron di thread terpisah. Hasil
    akhir langsung tersimpan ke database lewat proses_arsip_dan_tren().
    """
    global sedang_berjalan
    try:
        log_queue.put({"type": "log", "level": "INFO", "message": "Memulai pipeline harian..."})
        hasil_mentah = jalankan_pipeline_harian()
        hasil_ringkas = proses_summarization_harian(hasil_mentah)
        proses_arsip_dan_tren(hasil_ringkas)
        log_queue.put({"type": "selesai", "sukses": True})
    except Exception as e:
        log_queue.put({"type": "log", "level": "ERROR", "message": f"Pipeline gagal: {e}"})
        log_queue.put({"type": "selesai", "sukses": False, "error": str(e)})
    finally:
        sedang_berjalan = False


# ==============================================================================
# Endpoint Autentikasi Admin
# ==============================================================================

@app.post("/api/auth/login")
async def api_auth_login(request: Request):
    """Memvalidasi kredensial admin dan menerbitkan session cookie."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Format data tidak valid."}, status_code=400)

    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()

    from src.utils.admin_auth import verifikasi_admin
    is_valid, role = verifikasi_admin(username, password)
    if is_valid:
        token = buat_token_sesi(username)
        res = JSONResponse({"status": "ok", "redirect": "/admin"})
        res.set_cookie(
            key="cti_session",
            value=token,
            httponly=True,
            max_age=86400 * 7,  # 7 hari
            samesite="lax",
        )
        return res

    return JSONResponse(
        {"status": "error", "message": "Nama pengguna atau kata sandi tidak valid."},
        status_code=401,
    )


@app.post("/api/auth/logout")
async def api_auth_logout():
    """Menghapus session cookie admin dan logout."""
    res = JSONResponse({"status": "ok", "redirect": "/"})
    res.delete_cookie(key="cti_session")
    return res




@app.post("/api/settings/prompts")
async def simpan_prompts(request: Request):
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)
    if not cek_superadmin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Hanya superadmin yang dapat mengubah prompt."}, status_code=403)

    body = await request.json()
    from src.utils.settings_manager import SettingsManager
    for nama, isi in body.items():
        SettingsManager.set(f"prompt.{nama}", isi)
    return {"status": "ok"}


@app.get("/api/settings/prompts/{nama}")
async def get_prompt_lengkap(nama: str, request: Request):
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)
    from src.utils.settings_manager import SettingsManager
    return {"status": "ok", "isi": SettingsManager.get_prompt(nama)}


@app.post("/api/settings/rss")
async def simpan_rss(request: Request):
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)
    if not cek_superadmin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Hanya superadmin yang dapat mengubah sumber RSS."}, status_code=403)

    body = await request.json()
    from src.utils.settings_manager import SettingsManager
    if "international" in body:
        SettingsManager.set("rss_sources_international", body["international"])
    if "indonesia" in body:
        SettingsManager.set("rss_sources_indonesia", body["indonesia"])
    return {"status": "ok"}


@app.post("/api/settings/admin/password")
async def ubah_password(request: Request):
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)
    body = await request.json()
    password_baru = (body.get("password_baru") or "").strip()
    if not password_baru:
        return JSONResponse({"status": "error", "message": "Password baru tidak boleh kosong."}, status_code=400)

    user = ambil_user_dari_sesi(request)
    if not user:
        return JSONResponse({"status": "error", "message": "Sesi tidak valid."}, status_code=401)

    from src.utils.admin_auth import ubah_password_admin
    if ubah_password_admin(user["username"], password_baru):
        return {"status": "ok"}
    return JSONResponse({"status": "error", "message": "Gagal mengubah kata sandi."}, status_code=500)


@app.get("/api/auth/status")
async def api_auth_status(request: Request):
    """Mengecek status autentikasi admin beserta role aktif."""
    user = ambil_user_dari_sesi(request)
    if user:
        return {
            "authenticated": True,
            "username": user["username"],
            "role": user.get("role", "viewer")
        }
    return {"authenticated": False, "username": None, "role": None}


# ==============================================================================
# Endpoint Pipeline & Streaming
# ==============================================================================

@app.post("/api/run")
async def mulai_pipeline(request: Request):
    """Memicu pipeline di background thread. Khusus admin CTI."""
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)

    global sedang_berjalan
    if sedang_berjalan:
        return {"status": "sudah_berjalan"}
    sedang_berjalan = True
    while not log_queue.empty():
        log_queue.get()
    threading.Thread(target=_jalankan_pipeline_di_thread, daemon=True).start()
    return {"status": "dimulai"}


@app.get("/api/stream")
async def stream_log():
    """SSE - mengalirkan log real-time selama pipeline berjalan."""
    async def generator():
        while True:
            try:
                item = await asyncio.get_event_loop().run_in_executor(None, log_queue.get, True, 1.0)
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("type") == "selesai":
                    break
            except queue.Empty:
                yield ": keep-alive\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")


@app.post("/api/cancel")
async def batalkan_pipeline(request: Request):
    """Menandai pembatalan pipeline. Khusus admin CTI."""
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)

    global sedang_berjalan
    sedang_berjalan = False
    log_queue.put({"type": "log", "level": "WARNING", "message": "Pipeline dibatalkan oleh pengguna."})
    log_queue.put({"type": "selesai", "sukses": False, "error": "dibatalkan"})
    return {"status": "dibatalkan"}


# ==============================================================================
# Endpoint Data & Analitik
# ==============================================================================

@app.get("/api/beranda")
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


@app.get("/api/arsip")
async def ambil_arsip():
    """Tab Arsip: seluruh grup tanggal (7 hari terakhir), terurut terbaru -> terlama."""
    grup_per_tanggal = ambil_riwayat_dikelompokkan_per_hari(hari=7)
    daftar_hari = [
        {"tanggal": tanggal, "berita": isi.get("berita", [])}
        for tanggal, isi in grup_per_tanggal.items()
    ]
    return {"status": "ok" if daftar_hari else "kosong", "hari": daftar_hari}


@app.get("/api/tren")
async def ambil_tren():
    """Tab Tren Siber: membaca prediksi tren dan agregat visualisasi statistik langsung dari database."""
    prediksi = ambil_prediksi_tren_terakhir()
    if not prediksi:
        return {"status": "kosong", "prediksi_berita": "", "tanggal_dihitung": None, "statistik": None}

    statistik = None
    raw_stat = dict(prediksi).get("statistik_json")
    if raw_stat:
        try:
            statistik = json.loads(raw_stat)
        except Exception:
            statistik = None

    if statistik:
        # Bersihkan field usang yang sudah dihapus
        statistik.pop("threat_posture", None)
        statistik.pop("matriks_tindakan", None)
        statistik.pop("skor_threat_posture", None)

        # Pastikan fitur baru taktik_mitre dan cve_watchlist tersedia
        perlu_simpan_ulang = False
        if "taktik_mitre" not in statistik or "cve_watchlist" not in statistik:
            from src.analytics.trend_analyzer import hitung_distribusi_taktik_mitre, ekstrak_radar_cve_watchlist
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

        if perlu_simpan_ulang or (raw_stat and ("threat_posture" in raw_stat or "matriks_tindakan" in raw_stat)):
            try:
                simpan_prediksi_tren(
                    prediksi["prediksi_berita"],
                    kasus_wilayah_ai=dict(prediksi).get("kasus_wilayah_ai"),
                    statistik_json=json.dumps(statistik, ensure_ascii=False),
                )
            except Exception as err:
                logging.getLogger().error(f"Gagal memperbarui cache statistik ke DB: {err}")

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
            logging.getLogger().error(f"Gagal menyimpan cache statistik ke DB: {err}")

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


@app.get("/api/statistik-publik")
async def api_statistik_publik():
    """Tab Statistik Publik: Agregat visualisasi fakta siber empiris untuk masyarakat umum."""
    return ambil_statistik_publik()


@app.get("/api/ensiklopedia")
async def api_ensiklopedia(q: Optional[str] = None):
    """Endpoint eksplorasi ensiklopedia referensi standar keamanan siber (MITRE, D3FEND, NIST, OWASP, CWE, BSSN)."""
    from src.analytics.encyclopedia_lookup import get_all_framework_counts, search_encyclopedia
    if q:
        keywords = [k.strip() for k in q.split(",") if k.strip()]
        return {"query": q, "hasil": search_encyclopedia(keywords)}
    return {"status": "ok", "frameworks": get_all_framework_counts()}


@app.get("/api/settings")
async def ambil_settings(request: Request):
    """Admin: Membaca konfigurasi yang bisa diubah."""
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)

    from src.utils.settings_manager import SettingsManager
    gemini = SettingsManager.get_gemini_config()
    from src.utils.config_loader import ConfigLoader
    return {
        "gemini_api_key_set": bool(gemini.get("api_key")),
        "model_chain": gemini.get("model_chain", []),
        "temperature": gemini.get("temperature", 0.1),
        "max_output_tokens": gemini.get("max_output_tokens", 500),
        "embedding_model": gemini.get("embedding_model", ""),
        "keywords": SettingsManager.get_keywords(),
        "rss_sources_international": SettingsManager.get_rss_sources("international"),
        "rss_sources_indonesia": SettingsManager.get_rss_sources("indonesia"),
        "prompts": SettingsManager.get_all_prompts_info(),
    }


@app.post("/api/settings")
async def simpan_settings(request: Request):
    """Admin: Menyimpan perubahan konfigurasi."""
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)
    if not cek_superadmin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Hanya superadmin yang dapat mengubah pengaturan."}, status_code=403)

    from src.utils.settings_manager import SettingsManager
    from src.utils.llm_adapter import GeminiLLMAdapter

    body = await request.json()

    if "gemini" in body:
        for k, v in body["gemini"].items():
            SettingsManager.set(f"gemini.{k}", v)

    if "keywords" in body:
        for grup, daftar in body["keywords"].items():
            SettingsManager.set(f"keywords.{grup}", daftar)

    GeminiLLMAdapter.reload_config()
    return {"status": "ok"}


# ==============================================================================
# Halaman Web (HTML Pages)
# ==============================================================================

@app.get("/")
async def halaman_utama(request: Request):
    """Halaman publik terpadu: 2 tab (Dashboard dan Arsip) + tombol Login Admin."""
    from src.storage.db import DEFAULT_DB_PATH, ambil_statistik_publik
    statistik = None
    try:
        statistik = ambil_statistik_publik(DEFAULT_DB_PATH)
    except Exception as e:
        logging.getLogger().error(f"Gagal mengambil statistik SSR: {e}")
    return templates.TemplateResponse(request, "index.html", context={"statistik": statistik})


@app.get("/login")
async def halaman_login(request: Request):
    """Halaman login admin Tim CTI. Jika sudah terautentikasi, otomatis redirect ke /admin."""
    if cek_admin_autentikasi(request):
        return RedirectResponse(url="/admin", status_code=303)
    return templates.TemplateResponse(request, "login.html")


@app.get("/admin")
async def halaman_admin(request: Request):
    """Panel operasional Tim CTI CSIRT Jatim dengan sidebar kiri (default: Tren CTI)."""
    if not cek_admin_autentikasi(request):
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(request, "admin.html")


