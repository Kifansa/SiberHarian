"""
Orkestrasi pipeline harian: pengumpulan berita keamanan siber (RSS)
dan deduplikasi menjadi satu alur yang menghasilkan dataset siap pakai
untuk tahap summarization & analisis CTI.
"""
from pathlib import Path
from typing import Optional

import yaml

from src.classifier.relevance_classifier import filter_artikel_relevan
from src.dedup.deduplicator import deteksi_duplikat_hybrid, filter_belum_terkirim
from src.scraper.pipeline import jalankan_pipeline_berita
from src.storage.db import DEFAULT_DB_PATH, init_db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

CONFIG_PATH = Path(__file__).resolve().parents[1] / "config" / "config.yaml"


def muat_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def jalankan_pipeline_harian(config: Optional[dict] = None, db_path: Path = DEFAULT_DB_PATH) -> dict:
    """
    Menjalankan alur pengumpulan data berita harian:
    1. Pastikan database state siap.
    2. Kumpulkan berita (RSS) -> filter sudah-terkirim -> klasifikasi -> dedup hybrid.

    Returns:
        dict {"berita": DataFrame} - siap dipakai tahap summarization berikutnya.
    """
    config = config or muat_config()
    init_db(db_path)

    # --- BERITA ---
    logger.info("MEMULAI PENGUMPULAN BERITA")
    df_berita_mentah = jalankan_pipeline_berita(config)
    df_berita_baru = filter_belum_terkirim(df_berita_mentah, "berita", "link", db_path)
    df_berita_relevan = filter_artikel_relevan(df_berita_baru)
    df_berita_final = deteksi_duplikat_hybrid(df_berita_relevan)

    # --- RINGKASAN HASIL AKHIR ---
    logger.info("#" * 60)
    logger.info("RINGKASAN PIPELINE HARIAN")
    logger.info(f"  Berita siap diproses  : {len(df_berita_final)}")
    logger.info("#" * 60)

    return {"berita": df_berita_final}