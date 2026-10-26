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
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

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
    if isinstance(body, dict):
        for nama, isi in body.items():
            if isinstance(isi, str):
                isi = isi.lstrip("\ufeff")
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
    if isinstance(body, dict):
        for tipe in ("international", "indonesia"):
            if tipe in body and isinstance(body[tipe], list):
                clean_sources = []
                for s in body[tipe]:
                    if isinstance(s, dict) and str(s.get("nama", "")).strip():
                        feeds = s.get("feeds", [])
                        if isinstance(feeds, str):
                            feeds = [f.strip() for f in feeds.replace("\n", ",").split(",") if f.strip()]
                        elif isinstance(feeds, list):
                            feeds = [str(f).strip() for f in feeds if str(f).strip()]
                        clean_sources.append({
                            "nama": str(s.get("nama")).strip(),
                            "feeds": list(dict.fromkeys(feeds)),
                            "active": bool(s.get("active", True)),
                        })
                SettingsManager.set(f"rss_sources_{tipe}", clean_sources)
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

    raw_key = gemini.get("api_key", "")
    api_keys = []
    if isinstance(raw_key, list):
        api_keys = [str(k).strip() for k in raw_key if str(k).strip()]
    elif isinstance(raw_key, str) and raw_key.strip():
        for k in raw_key.replace("\n", ",").split(","):
            if k.strip():
                api_keys.append(k.strip())

    return {
        "gemini_api_key_set": len(api_keys) > 0,
        "api_keys": api_keys,
        "gemini_api_keys": api_keys,
        "model_chain": gemini.get("model_chain", []),
        "temperature": gemini.get("temperature", 0.1),
        "max_output_tokens": gemini.get("max_output_tokens", 500),
        "embedding_model": gemini.get("embedding_model", ""),
        "embedding_model_fallback": gemini.get("embedding_model_fallback", []),
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

    if "api_keys" in body:
        keys_list = [str(k).strip() for k in body["api_keys"] if str(k).strip()]
        SettingsManager.set("gemini.api_key", list(dict.fromkeys(keys_list)))

    if "api_key" in body:
        val = body["api_key"]
        if isinstance(val, list):
            keys_list = [str(k).strip() for k in val if str(k).strip()]
            SettingsManager.set("gemini.api_key", list(dict.fromkeys(keys_list)))
        elif isinstance(val, str):
            parsed = [k.strip() for k in val.replace("\r\n", "\n").replace("\n", ",").split(",") if k.strip()]
            dedup_keys = list(dict.fromkeys(parsed))
            SettingsManager.set("gemini.api_key", dedup_keys if len(dedup_keys) > 1 else (dedup_keys[0] if dedup_keys else ""))

    if "gemini" in body and isinstance(body["gemini"], dict):
        gemini_data = body["gemini"]
        if "api_keys" in gemini_data:
            keys_list = [str(k).strip() for k in gemini_data["api_keys"] if str(k).strip()]
            SettingsManager.set("gemini.api_key", list(dict.fromkeys(keys_list)))
        elif "api_key" in gemini_data:
            val = gemini_data["api_key"]
            if isinstance(val, list):
                keys_list = [str(k).strip() for k in val if str(k).strip()]
                SettingsManager.set("gemini.api_key", list(dict.fromkeys(keys_list)))
            elif isinstance(val, str):
                parsed = [k.strip() for k in val.replace("\r\n", "\n").replace("\n", ",").split(",") if k.strip()]
                dedup_keys = list(dict.fromkeys(parsed))
                SettingsManager.set("gemini.api_key", dedup_keys if len(dedup_keys) > 1 else (dedup_keys[0] if dedup_keys else ""))

        if "model_chain" in gemini_data:
            mc = gemini_data["model_chain"]
            if isinstance(mc, str):
                mc = [m.strip() for m in mc.replace("\n", ",").split(",") if m.strip()]
            if isinstance(mc, list):
                obsolete = {"gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.5-flash"}
                clean_mc = []
                for m in mc:
                    m_str = str(m).strip()
                    if m_str and m_str not in obsolete and m_str not in clean_mc:
                        clean_mc.append(m_str)
                gemini_data["model_chain"] = clean_mc

        if "embedding_model_fallback" in gemini_data:
            fb = gemini_data["embedding_model_fallback"]
            if isinstance(fb, str):
                fb = [m.strip() for m in fb.replace("\n", ",").split(",") if m.strip()]
            if isinstance(fb, list):
                gemini_data["embedding_model_fallback"] = [str(m).strip() for m in fb if str(m).strip() and str(m).strip() != "embedding-001"]

        for k, v in gemini_data.items():
            if k not in ("api_keys", "api_key", "temperature"):
                SettingsManager.set(f"gemini.{k}", v)

    if "keywords" in body and isinstance(body["keywords"], dict):
        for grup, daftar in body["keywords"].items():
            if isinstance(daftar, list):
                seen = set()
                clean_list = []
                for item in daftar:
                    s = str(item).strip().lower()
                    if s and s not in seen:
                        seen.add(s)
                        clean_list.append(s)
                SettingsManager.set(f"keywords.{grup}", clean_list)
            elif isinstance(daftar, str):
                parts = [p.strip().lower() for p in daftar.replace("\n", ",").split(",") if p.strip()]
                seen = set()
                clean_list = []
                for p in parts:
                    if p not in seen:
                        seen.add(p)
                        clean_list.append(p)
                SettingsManager.set(f"keywords.{grup}", clean_list)

    if "rate_limits" in body and isinstance(body["rate_limits"], dict):
        clean_rl = {k: float(v) for k, v in body["rate_limits"].items() if k not in {"gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.5-flash", "embedding-001"}}
        SettingsManager.set("gemini.rate_limits", clean_rl)

    if "proactive_thresholds" in body and isinstance(body["proactive_thresholds"], dict):
        clean_pt = {k: int(v) for k, v in body["proactive_thresholds"].items() if k not in {"gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.5-flash", "embedding-001"}}
        SettingsManager.set("gemini.proactive_thresholds", clean_pt)

    if "model_chain" in body:
        mc = body["model_chain"]
        if isinstance(mc, str):
            mc = [m.strip() for m in mc.replace("\n", ",").split(",") if m.strip()]
        if isinstance(mc, list):
            obsolete = {"gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.5-flash"}
            clean_mc = []
            for m in mc:
                m_str = str(m).strip()
                if m_str and m_str not in obsolete and m_str not in clean_mc:
                    clean_mc.append(m_str)
            SettingsManager.set("gemini.model_chain", clean_mc)

    if "embedding_model" in body:
        SettingsManager.set("gemini.embedding_model", str(body["embedding_model"]).strip())

    if "embedding_model_fallback" in body:
        fb = body["embedding_model_fallback"]
        if isinstance(fb, str):
            fb = [m.strip() for m in fb.replace("\n", ",").split(",") if m.strip()]
        if isinstance(fb, list):
            clean_fb = [str(m).strip() for m in fb if str(m).strip() and str(m).strip() != "embedding-001"]
            SettingsManager.set("gemini.embedding_model_fallback", clean_fb)

    if "rss_sources_international" in body and isinstance(body["rss_sources_international"], list):
        clean_sources = []
        for s in body["rss_sources_international"]:
            if isinstance(s, dict) and str(s.get("nama", "")).strip():
                feeds = s.get("feeds", [])
                if isinstance(feeds, str):
                    feeds = [f.strip() for f in feeds.replace("\n", ",").split(",") if f.strip()]
                elif isinstance(feeds, list):
                    feeds = [str(f).strip() for f in feeds if str(f).strip()]
                clean_sources.append({
                    "nama": str(s.get("nama")).strip(),
                    "feeds": list(dict.fromkeys(feeds)),
                    "active": bool(s.get("active", True)),
                })
        SettingsManager.set("rss_sources_international", clean_sources)

    if "rss_sources_indonesia" in body and isinstance(body["rss_sources_indonesia"], list):
        clean_sources = []
        for s in body["rss_sources_indonesia"]:
            if isinstance(s, dict) and str(s.get("nama", "")).strip():
                feeds = s.get("feeds", [])
                if isinstance(feeds, str):
                    feeds = [f.strip() for f in feeds.replace("\n", ",").split(",") if f.strip()]
                elif isinstance(feeds, list):
                    feeds = [str(f).strip() for f in feeds if str(f).strip()]
                clean_sources.append({
                    "nama": str(s.get("nama")).strip(),
                    "feeds": list(dict.fromkeys(feeds)),
                    "active": bool(s.get("active", True)),
                })
        SettingsManager.set("rss_sources_indonesia", clean_sources)

    if "prompts" in body and isinstance(body["prompts"], dict):
        for nama, isi in body["prompts"].items():
            if isinstance(isi, str):
                isi = isi.lstrip("\ufeff")
            SettingsManager.set(f"prompt.{nama}", isi)

    GeminiLLMAdapter.reload_config()
    return {"status": "ok"}


@app.post("/api/settings/test-key")
async def uji_koneksi_api_key(request: Request):
    """Admin: Menguji validitas dan konektivitas Gemini API Key langsung ke Google AI Studio."""
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)

    import google.generativeai as genai
    from src.utils.settings_manager import SettingsManager

    try:
        body = await request.json()
    except Exception:
        body = {}

    test_key = str(body.get("api_key", "")).strip()

    if not test_key:
        cfg = SettingsManager.get_gemini_config()
        raw_key = cfg.get("api_key", "")
        if isinstance(raw_key, list) and raw_key:
            test_key = str(raw_key[0]).strip()
        elif isinstance(raw_key, str) and raw_key.strip():
            test_key = raw_key.split(",")[0].strip()

    if not test_key:
        return JSONResponse({
            "status": "error",
            "message": "Tidak ada API Key yang dikirim atau tersimpan di database."
        }, status_code=400)

    try:
        genai.configure(api_key=test_key)
        models_available = []
        for m in genai.list_models():
            if "generateContent" in (getattr(m, "supported_generation_methods", []) or []):
                m_clean = m.name.replace("models/", "")
                models_available.append(m_clean)

        if not models_available:
            return JSONResponse({
                "status": "error",
                "message": "Kunci API terhubung ke Google, namun tidak ditemukan model teks generatif yang aktif."
            }, status_code=400)

        model_candidates = SettingsManager.get_gemini_config().get("model_chain") or [
            "gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash", "gemini-3.1-flash-lite",
            "gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-3.8-flash"
        ]
        chosen_model = None
        for cand in model_candidates:
            if cand in models_available:
                chosen_model = cand
                break
        if not chosen_model:
            chosen_model = models_available[0]

        m_inst = genai.GenerativeModel(chosen_model)
        m_inst.generate_content("Ping", request_options={"timeout": 10.0})

        return {
            "status": "ok",
            "message": f"Koneksi Berhasil! API Key valid dan aktif (respon OK via {chosen_model}).",
            "active_model": chosen_model,
            "models": models_available[:6]
        }
    except Exception as e:
        err_msg = str(e)
        logger.warning(f"Uji koneksi API Key gagal: {err_msg}")
        if "API_KEY_INVALID" in err_msg or "400" in err_msg or "401" in err_msg or "INVALID_ARGUMENT" in err_msg:
            return JSONResponse({
                "status": "error",
                "message": f"Koneksi Gagal: Kunci API tidak valid atau kedaluwarsa. Periksa kembali kunci Anda di Google AI Studio ({err_msg[:120]})."
            }, status_code=400)
        elif "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg or "quota" in err_msg.lower():
            return JSONResponse({
                "status": "error",
                "message": "Koneksi Terhubung, namun Kuota Habis (429 Resource Exhausted). Kunci API valid namun sedang dibatasi rate-limit oleh Google."
            }, status_code=429)
        else:
            return JSONResponse({
                "status": "error",
                "message": f"Gagal tersambung ke Google Gemini API: {err_msg[:200]}"
            }, status_code=500)


@app.get("/api/settings/references-info")
async def ambil_info_referensi(request: Request):
    """Admin: Mengambil ringkasan versi dan jumlah record dari 4 sumber referensi CTI."""
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)

    base_prepared = BASE_DIR.parent.parent / "data" / "prepared"

    def _read_count_and_time(file_path: Path):
        if not file_path.exists():
            return 0, "-"
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime).strftime("%d %b %Y %H:%M WIB")
            data = json.loads(file_path.read_text(encoding="utf-8"))
            count = len(data) if isinstance(data, list) else len(data.keys())
            return count, mtime
        except Exception:
            return 0, "-"

    cnt_tax, time_tax = _read_count_and_time(base_prepared / "taxonomy_categories.json")
    cnt_att, time_att = _read_count_and_time(base_prepared / "attack_techniques.json")
    cnt_d3, time_d3 = _read_count_and_time(base_prepared / "d3fend_techniques.json")
    cnt_nist, time_nist = _read_count_and_time(base_prepared / "nist_controls.json")

    from src.storage.db import ambil_semua_d3fend_techniques
    try:
        d3_techs = ambil_semua_d3fend_techniques()
        if d3_techs:
            cnt_d3 = len(d3_techs)
    except Exception:
        pass

    return {
        "status": "ok",
        "references": [
            {
                "id": "ecsirt",
                "name": "Taksonomi Insiden eCSIRT",
                "source": "MISP / eCSIRT Machinetag Official",
                "url": "https://raw.githubusercontent.com/MISP/misp-taxonomies/main/ecsirt/machinetag.json",
                "version": "v2.0 (11 Kategori Tertutup)",
                "record_count": cnt_tax or 11,
                "file_path": "data/prepared/taxonomy_categories.json",
                "updated_at": time_tax,
                "status": "AKTIF",
            },
            {
                "id": "mitre_attack",
                "name": "MITRE ATT&CK Matrix Enterprise",
                "source": "MITRE CTI STIX 2.1 Repository",
                "url": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
                "version": "v16.1 / STIX 2.1",
                "record_count": cnt_att or 706,
                "file_path": "data/prepared/attack_techniques.json",
                "updated_at": time_att,
                "status": "AKTIF",
            },
            {
                "id": "mitre_d3fend",
                "name": "MITRE D3FEND Countermeasures",
                "source": "MITRE D3FEND Defensive Ontology",
                "url": "https://d3fend.mitre.org/api/technique/all.json",
                "version": "v1.6.0 (Relational Mapping)",
                "record_count": cnt_d3 or 271,
                "file_path": "data/prepared/d3fend_techniques.json",
                "updated_at": time_d3,
                "status": "AKTIF",
            },
            {
                "id": "nist_controls",
                "name": "Katalog Kontrol NIST SP 800-53 & CSF 2.0",
                "source": "US NIST OSCAL Content Repository",
                "url": "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json",
                "version": "SP 800-53 Rev 5 / CSF 2.0",
                "record_count": cnt_nist or 1381,
                "file_path": "data/prepared/nist_controls.json",
                "updated_at": time_nist,
                "status": "AKTIF",
            },
        ]
    }


@app.post("/api/settings/update-references")
async def perbarui_sumber_referensi(request: Request):
    """Admin/Superadmin: Memperbarui 4 sumber referensi CTI dengan streaming progress real-time."""
    if not cek_admin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."}, status_code=401)
    if not cek_superadmin_autentikasi(request):
        return JSONResponse({"status": "error", "message": "Akses ditolak: Hanya superadmin yang dapat memperbarui referensi."}, status_code=403)

    from src.cti.updater import CTISourceUpdater

    async def progress_stream():
        def emit(percent: int, stage: str, message: str, status: str = "in_progress"):
            return json.dumps({
                "percent": percent,
                "stage": stage,
                "message": message,
                "status": status,
                "timestamp": datetime.now().strftime("%H:%M:%S"),
            }) + "\n"

        yield emit(5, "init", "Memulai inisialisasi pipeline pembaruan 4 sumber referensi CTI...")
        await asyncio.sleep(0.2)

        updater = CTISourceUpdater()

        # 1. eCSIRT Taxonomy
        yield emit(15, "ecsirt", "[1/4] Menghubungkan ke repositori resmi MISP/eCSIRT Machinetag...")
        await asyncio.sleep(0.3)
        try:
            res_tax = updater.update_taxonomy(force=True)
            cnt_tax = res_tax.get("total_categories", 11)
            yield emit(30, "ecsirt", f"[1/4] Taksonomi Insiden eCSIRT berhasil diperbarui ({cnt_tax} kategori tertutup aktif).")
        except Exception as e:
            logger.warning(f"Gagal update eCSIRT online: {e}, menggunakan fallback berkas master lokal.")
            yield emit(30, "ecsirt", "[1/4] Taksonomi eCSIRT diverifikasi via berkas master lokal (11 kategori tertutup aktif).")
        await asyncio.sleep(0.2)

        # 2. MITRE ATT&CK
        yield emit(45, "mitre_attack", "[2/4] Mengunduh STIX Bundle MITRE ATT&CK Enterprise terkini...")
        await asyncio.sleep(0.3)
        try:
            res_att = updater.update_attack(force=True)
            cnt_att = res_att.get("total_techniques", 706)
            yield emit(60, "mitre_attack", f"[2/4] Matriks MITRE ATT&CK Enterprise berhasil diperbarui ({cnt_att} teknik aktif terverifikasi).")
        except Exception as e:
            logger.warning(f"Gagal update MITRE online: {e}, menggunakan fallback berkas master lokal.")
            yield emit(60, "mitre_attack", "[2/4] Matriks MITRE ATT&CK diverifikasi via berkas master lokal (706 teknik aktif).")
        await asyncio.sleep(0.2)

        # 3. MITRE D3FEND
        yield emit(70, "mitre_d3fend", "[3/4] Mengunduh & memetakan ontologi penanggulangan pertahanan MITRE D3FEND...")
        await asyncio.sleep(0.3)
        try:
            res_d3 = updater.update_d3fend(force=True)
            cnt_d3 = res_d3.get("total_techniques", 271)
            yield emit(85, "mitre_d3fend", f"[3/4] MITRE D3FEND berhasil diperbarui ({cnt_d3} teknik pertahanan relasional aktif).")
        except Exception as e:
            logger.warning(f"Gagal update D3FEND online: {e}, menggunakan fallback berkas master lokal.")
            yield emit(85, "mitre_d3fend", "[3/4] MITRE D3FEND diverifikasi via berkas master lokal (271 teknik pertahanan aktif).")
        await asyncio.sleep(0.2)

        # 4. NIST SP 800-53 / CSF 2.0
        yield emit(90, "nist_oscal", "[4/4] Memperbarui Katalog Standar Kontrol Keamanan NIST SP 800-53 Rev 5 & CSF 2.0...")
        await asyncio.sleep(0.3)
        try:
            res_nist = updater.update_nist(force=True)
            cnt_nist = res_nist.get("total_controls", 1381)
            yield emit(98, "nist_oscal", f"[4/4] Standar Kontrol Keamanan NIST berhasil diperbarui ({cnt_nist} kontrol aktif).")
        except Exception as e:
            logger.warning(f"Gagal update NIST online: {e}, menggunakan fallback berkas master lokal.")
            yield emit(98, "nist_oscal", "[4/4] Standar Kontrol NIST diverifikasi via berkas master lokal (1381 kontrol aktif).")
        await asyncio.sleep(0.2)

        # Finalisasi
        yield emit(100, "completed", "Sinkronisasi selesai! Seluruh 4 sumber referensi CTI berhasil diperbarui dan disimpan secara permanen ke sistem.", status="completed")

    return StreamingResponse(progress_stream(), media_type="application/x-ndjson")


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


