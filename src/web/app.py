"""
Web demo interface untuk pipeline cyber news digest. Endpoint untuk
memicu pipeline lengkap (scraping -> summarization -> arsip & tren)
dengan progress log real-time (SSE), dan endpoint terpisah untuk 3 tab
dashboard (Beranda, Arsip, Tren Siber) yang membaca langsung dari
database - source kebenaran tunggal, jadi data tetap ada untuk demo
walau server di-restart tanpa perlu scraping ulang.
"""
import asyncio
import json
import logging
import queue
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
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

app = FastAPI(title="Cyber News Digest - Demo")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

log_queue: "queue.Queue[dict]" = queue.Queue()
sedang_berjalan = False


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
    akhir langsung tersimpan ke database lewat proses_arsip_dan_tren() -
    tidak ada lagi cache JSON manual, database adalah sumber kebenarannya.
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


@app.post("/api/run")
async def mulai_pipeline():
    """Memicu pipeline di background thread. Progres dipantau lewat /api/stream."""
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
async def batalkan_pipeline():
    """Menandai pipeline sebagai tidak berjalan lagi dari sisi status server (lihat
    docstring versi sebelumnya soal keterbatasan pembatalan paksa thread Python)."""
    global sedang_berjalan
    sedang_berjalan = False
    log_queue.put({"type": "log", "level": "WARNING", "message": "Pipeline dibatalkan oleh pengguna."})
    log_queue.put({"type": "selesai", "sukses": False, "error": "dibatalkan"})
    return {"status": "dibatalkan"}


@app.get("/api/beranda")
async def ambil_beranda():
    """Tab Beranda: berita & CVE, MASING-MASING dari tanggal terbarunya sendiri."""
    data = ambil_data_terbaru_per_kategori(hari=7)
    ada_data = bool(data["berita"]) or bool(data["cve"])
    return {
        "status": "ok" if ada_data else "kosong",
        "tanggal_berita": data["tanggal_berita"],
        "tanggal_cve": data["tanggal_cve"],
        "waktu_terakhir_scraping": data.get("waktu_terakhir_scraping"),
        "berita": data["berita"],
        "cve": data["cve"],
    }


@app.get("/api/arsip")
async def ambil_arsip():
    """Tab Arsip: seluruh grup tanggal (7 hari terakhir), terurut terbaru -> terlama."""
    grup_per_tanggal = ambil_riwayat_dikelompokkan_per_hari(hari=7)
    daftar_hari = [
        {"tanggal": tanggal, "berita": isi["berita"], "cve": isi["cve"]}
        for tanggal, isi in grup_per_tanggal.items()
    ]
    return {"status": "ok" if daftar_hari else "kosong", "hari": daftar_hari}


@app.get("/api/tren")
async def ambil_tren():
    """Tab Tren Siber: membaca prediksi tren dan agregat visualisasi statistik langsung dari database."""
    prediksi = ambil_prediksi_tren_terakhir()
    if not prediksi:
        return {"status": "kosong", "prediksi_berita": "", "prediksi_cve": "", "tanggal_dihitung": None, "statistik": None}

    # 1. Ambil statistik dashboard yang sudah tersimpan di database (instan, < 5ms tanpa dedup ulang)
    statistik = None
    raw_stat = dict(prediksi).get("statistik_json")
    if raw_stat:
        try:
            statistik = json.loads(raw_stat)
        except Exception:
            statistik = None

    # 2. Fallback: jika belum tersimpan di DB (inisialisasi awal), hitung 1x lalu simpan ke DB
    if not statistik:
        df_14 = ambil_riwayat_tren(hari=14)
        statistik = susun_statistik_dashboard(df_14)
        try:
            simpan_prediksi_tren(
                prediksi["prediksi_berita"],
                prediksi["prediksi_cve"],
                kasus_wilayah_ai=dict(prediksi).get("kasus_wilayah_ai"),
                statistik_json=json.dumps(statistik, ensure_ascii=False),
            )
        except Exception as err:
            logging.getLogger().error(f"Gagal menyimpan cache statistik ke DB: {err}")

    # 3. Ambil hasil analisis AI kasus wilayah jika ada
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
        "prediksi_berita": prediksi["prediksi_berita"],
        "prediksi_cve": prediksi["prediksi_cve"],
        "tanggal_dihitung": prediksi["tanggal_dihitung"],
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


@app.get("/")
async def halaman_utama(request: Request):
    return templates.TemplateResponse(request, "index.html")