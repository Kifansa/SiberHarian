"""Komposisi aplikasi web SiberHarian.

Aplikasi memasang router publik, pipeline, dan pengaturan, lalu
menyiapkan basis data serta validasi keamanan saat startup.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from src.storage.db import DEFAULT_DB_PATH, init_db
from src.web.auth import (
    ambil_user_dari_sesi,
    buat_token_sesi,
    cek_admin_autentikasi,
    cek_superadmin_autentikasi,
    validasi_keamanan_startup,
)
from src.web.routes_pipeline import log_queue, router as router_pipeline, sedang_berjalan
from src.web.routes_public import ambil_tren, router as router_public
from src.web.routes_settings import router as router_settings
from src.web.templating import BASE_DIR, templates

__all__ = [
    "BASE_DIR",
    "ambil_tren",
    "ambil_user_dari_sesi",
    "app",
    "buat_token_sesi",
    "cek_admin_autentikasi",
    "cek_superadmin_autentikasi",
    "log_queue",
    "sedang_berjalan",
    "templates",
]


@asynccontextmanager
async def _masa_hidup(app: FastAPI):
    """Menyiapkan basis data dan memvalidasi konfigurasi keamanan."""
    validasi_keamanan_startup()
    init_db(DEFAULT_DB_PATH)
    yield


app = FastAPI(
    title="SiberHarian - CSIRT Diskominfo Jatim",
    lifespan=_masa_hidup,
)

_static_dir = Path(BASE_DIR) / "static"
app.mount("/static", StaticFiles(directory=_static_dir), name="static")
app.include_router(router_public)
app.include_router(router_pipeline)
app.include_router(router_settings)
