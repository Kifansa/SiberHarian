"""
Orkestrasi pipeline harian: menggabungkan pengumpulan berita (RSS),
pengumpulan CVE (NVD API), dan deduplikasi menjadi satu alur yang
menghasilkan dataset siap pakai untuk tahap summarization & notifikasi.
"""
from pathlib import Path
from typing import Optional

import yaml

from src.classifier.relevance_classifier import filter_artikel_relevan
from src.dedup.deduplicator import deteksi_duplikat_hybrid, filter_belum_terkirim
from src.scraper.cve_fetcher import ambil_cve_terbaru, susun_struktur_digest_cve
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
    Menjalankan seluruh alur pengumpulan data harian:
    1. Pastikan database state siap.
    2. Kumpulkan berita (RSS) -> filter sudah-terkirim -> dedup hybrid.
    3. Kumpulkan CVE (NVD) -> filter sudah-terkirim -> susun struktur digest.

    Returns:
        dict {"berita": DataFrame, "cve_struktur": dict} - siap dipakai
        tahap summarization berikutnya.
    """
    config = config or muat_config()
    init_db(db_path)

    # --- BERITA ---
    logger.info("MEMULAI PENGUMPULAN BERITA")
    df_berita_mentah = jalankan_pipeline_berita(config)
    df_berita_baru = filter_belum_terkirim(df_berita_mentah, "berita", "link", db_path)
    df_berita_relevan = filter_artikel_relevan(df_berita_baru)
    df_berita_final = deteksi_duplikat_hybrid(df_berita_relevan)

    # --- CVE ---
    logger.info("#" * 60)
    logger.info("MEMULAI PENGUMPULAN CVE")
    logger.info("#" * 60)
    cve_cfg = config["cve_source"]
    pipeline_cfg = config["pipeline"]
    df_cve_mentah = ambil_cve_terbaru(
        base_url=cve_cfg["base_url"],
        window_hours=pipeline_cfg.get("window_hours", 24),
        min_cvss_score=cve_cfg.get("min_cvss_score", 7.0),
        daftar_vendor_dikenal=config.get("known_vendors", []),
        timeout=cve_cfg.get("request_timeout", 30),
    )
    df_cve_baru = filter_belum_terkirim(df_cve_mentah, "cve", "cve_id", db_path)
    cve_struktur = susun_struktur_digest_cve(df_cve_baru)

    # --- RINGKASAN HASIL AKHIR ---
    logger.info("#" * 60)
    logger.info("RINGKASAN PIPELINE HARIAN")
    logger.info(f"  Berita siap diproses  : {len(df_berita_final)}")
    logger.info(f"  Mode CVE hari ini     : {cve_struktur['mode']}")
    logger.info("#" * 60)

    return {"berita": df_berita_final, "cve_struktur": cve_struktur}