"""Endpoint pipeline harian dan streaming log SSE."""

import asyncio
import json
import logging
import queue
import threading

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from src.analytics.pasca_proses import proses_arsip_dan_tren
from src.pipeline_harian import jalankan_pipeline_harian
from src.summarizer.llm_summarizer import proses_summarization_harian
from src.web.auth import cek_admin_autentikasi, tolak_autentikasi

router = APIRouter()
log_queue: "queue.Queue[dict]" = queue.Queue()
sedang_berjalan = False


class QueueLogHandler(logging.Handler):
    """Mendorong setiap log record ke queue untuk di-stream ke frontend."""

    def emit(self, record: logging.LogRecord) -> None:
        log_queue.put(
            {"type": "log", "level": record.levelname, "message": self.format(record)}
        )


def _pasang_handler_global() -> None:
    handler = QueueLogHandler()
    handler.setFormatter(
        logging.Formatter("%(levelname)-8s | %(message)s", datefmt="%H:%M:%S")
    )
    root_logger = logging.getLogger()
    if not any(isinstance(h, QueueLogHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


_pasang_handler_global()


def _jalankan_pipeline_di_thread() -> None:
    """Menjalankan pipeline lengkap secara sinkron di thread terpisah."""
    global sedang_berjalan
    try:
        log_queue.put(
            {
                "type": "log",
                "level": "INFO",
                "message": "Memulai pipeline harian...",
            }
        )
        hasil_mentah = jalankan_pipeline_harian()
        hasil_ringkas = proses_summarization_harian(hasil_mentah)
        proses_arsip_dan_tren(hasil_ringkas)
        log_queue.put({"type": "selesai", "sukses": True})
    except Exception as e:
        log_queue.put(
            {"type": "log", "level": "ERROR", "message": f"Pipeline gagal: {e}"}
        )
        log_queue.put({"type": "selesai", "sukses": False, "error": str(e)})
    finally:
        sedang_berjalan = False


@router.post("/api/run")
async def mulai_pipeline(request: Request):
    """Memicu pipeline di background thread. Khusus admin CTI."""
    if not cek_admin_autentikasi(request):
        return tolak_autentikasi()

    global sedang_berjalan
    if sedang_berjalan:
        return {"status": "sudah_berjalan"}
    sedang_berjalan = True
    while not log_queue.empty():
        log_queue.get()
    threading.Thread(target=_jalankan_pipeline_di_thread, daemon=True).start()
    return {"status": "dimulai"}


@router.get("/api/stream")
async def stream_log():
    """SSE yang mengalirkan log real-time selama pipeline berjalan."""

    async def generator():
        while True:
            try:
                item = await asyncio.get_event_loop().run_in_executor(
                    None, log_queue.get, True, 1.0
                )
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("type") == "selesai":
                    break
            except queue.Empty:
                yield ": keep-alive\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")


@router.post("/api/cancel")
async def batalkan_pipeline(request: Request):
    """Menandai pembatalan pipeline. Khusus admin CTI."""
    if not cek_admin_autentikasi(request):
        return tolak_autentikasi()

    global sedang_berjalan
    sedang_berjalan = False
    log_queue.put(
        {
            "type": "log",
            "level": "WARNING",
            "message": "Pipeline dibatalkan oleh pengguna.",
        }
    )
    log_queue.put({"type": "selesai", "sukses": False, "error": "dibatalkan"})
    return {"status": "dibatalkan"}
