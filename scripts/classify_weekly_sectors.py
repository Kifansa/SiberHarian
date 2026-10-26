#!/usr/bin/env python3
"""
CLI Script: Batch Klasifikasi Sektor Korban Mingguan (10 Sektor IIV Perpres 82/2022).
Memuat seluruh berita 7 hari terakhir dari database, melakukan klasifikasi sektor
dengan validasi kutipan bukti ketat (guardrail substring), dan menyimpan hasilnya
ke tabel intelijen_berita_tervalidasi.
"""

import sys
import argparse
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Tambahkan root directory ke sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.db import (
    DEFAULT_DB_PATH,
    init_db,
    _koneksi,
    simpan_intelijen_berita,
    ambil_intelijen_berita,
)
from src.cti.analyzer import CTINewsAnalyzer, guard_sector_and_quote
from src.cti.preparer import CLOSED_10_IIV_SECTORS, IIV_SECTOR_DISPLAY_NAMES
from src.utils.logger import setup_logger

logger = setup_logger("scripts.classify_weekly_sectors")


def load_weekly_news(db_path: Path, days: int = 7) -> List[Dict[str, Any]]:
    """
    Memuat berita dari tabel riwayat_tren untuk 7 hari terakhir.
    Mendukung filter tanggal relatif terkini atau 7 tanggal unik terbaru dalam database.
    """
    init_db(db_path)
    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            """
            SELECT id, identifier, judul, sumber, ringkasan_atau_narasi, link, tanggal_publish, tanggal_dicatat
            FROM riwayat_tren
            WHERE kategori = 'berita'
            ORDER BY id DESC
            """
        )
        all_news = [dict(r) for r in cur.fetchall()]

    if not all_news:
        return []

    # Kumpulkan tanggal unik dari tanggal_publish / tanggal_dicatat
    dates = []
    for art in all_news:
        raw_tgl = art.get("tanggal_publish") or art.get("tanggal_dicatat") or ""
        tgl_str = str(raw_tgl)[:10]
        if len(tgl_str) == 10 and tgl_str[4] == "-" and tgl_str[7] == "-":
            dates.append(tgl_str)

    unique_dates = sorted(set(dates), reverse=True)
    if unique_dates:
        target_dates = set(unique_dates[:days])
        filtered_news = [
            art for art in all_news
            if (str(art.get("tanggal_publish") or art.get("tanggal_dicatat") or "")[:10]) in target_dates
        ]
        if filtered_news:
            return filtered_news

    # Fallback jika tanggal tidak berpola YYYY-MM-DD standar: ambil n artikel terbaru
    return all_news[:100]


def classify_weekly_news_sectors(
    db_path: Path = DEFAULT_DB_PATH,
    days: int = 7,
    limit: Optional[int] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Menjalankan pipeline klasifikasi sektor korban pada berita mingguan.
    """
    news_items = load_weekly_news(db_path, days=days)
    if limit and limit > 0:
        news_items = news_items[:limit]

    total_news = len(news_items)
    logger.info(f"Memproses klasifikasi sektor untuk {total_news} berita mingguan.")

    if total_news == 0:
        return {
            "status": "EMPTY",
            "total_processed": 0,
            "valid_quotes_count": 0,
            "quote_validity_rate": 0.0,
            "sector_distribution": {},
        }

    analyzer = CTINewsAnalyzer(db_path=db_path)
    sector_distribution: Dict[str, int] = {s: 0 for s in CLOSED_10_IIV_SECTORS}
    valid_quotes = 0
    records_saved = 0

    for idx, item in enumerate(news_items, 1):
        art_id = item.get("identifier") or f"art_{item.get('id')}"
        judul = item.get("judul", "")
        ringkasan = item.get("ringkasan_atau_narasi", "")
        teks_berita = item.get("teks_asli") or f"{judul}. {ringkasan}".strip()

        # Jalankan klasifikasi sektor
        sec_res = analyzer.classify_sector(item)
        sektor = sec_res["sektor_target"]
        conf = sec_res["confidence_sektor"]
        quote = sec_res["kutipan_bukti_sektor"]
        alasan = sec_res["alasan_sektor"]

        sector_distribution[sektor] = sector_distribution.get(sektor, 0) + 1

        if sektor != "Tidak dapat ditentukan" and quote:
            valid_quotes += 1

        if not dry_run:
            # Ambil record intelijen yang sudah ada atau buat baru
            existing_intel = ambil_intelijen_berita(art_id, db_path=db_path)
            if existing_intel:
                existing_intel["sektor_target"] = sektor
                existing_intel["confidence_sektor"] = conf
                existing_intel["kutipan_bukti_sektor"] = quote
                existing_intel["alasan_sektor"] = alasan
                simpan_intelijen_berita(existing_intel, db_path=db_path)
            else:
                # Jalankan full analyze_news yang sudah meng-attach sektor
                analyzer.analyze_news(item, persist=True)
            records_saved += 1

    validity_rate = (valid_quotes / total_news) if total_news > 0 else 0.0

    return {
        "status": "SUCCESS",
        "total_processed": total_news,
        "records_saved": records_saved,
        "valid_quotes_count": valid_quotes,
        "quote_validity_rate": round(validity_rate, 4),
        "sector_distribution": sector_distribution,
    }


def main():
    parser = argparse.ArgumentParser(description="Batch runner klasifikasi sektor IIV mingguan SiberHarian.")
    parser.add_argument("--db-path", type=str, default=str(DEFAULT_DB_PATH), help="Jalur file basis data SQLite.")
    parser.add_argument("--days", type=int, default=7, help="Rentang hari berita (default: 7).")
    parser.add_argument("--limit", type=int, default=None, help="Batas maksimum berita yang diproses.")
    parser.add_argument("--dry-run", action="store_true", help="Jalankan klasifikasi tanpa menyimpan ke basis data.")

    args = parser.parse_args()
    db_file = Path(args.db_path)

    try:
        res = classify_weekly_news_sectors(
            db_path=db_file,
            days=args.days,
            limit=args.limit,
            dry_run=args.dry_run,
        )

        print("==================================================================")
        print("  BATCH KLASIFIKASI SEKTOR KORBAN 10 IIV PERPRES 82/2022")
        print("==================================================================")
        print(f"Basis Data       : {db_file}")
        print(f"Total Berita     : {res['total_processed']}")
        print(f"Disimpan ke DB   : {res.get('records_saved', 0)}")
        print(f"Validitas Kutipan: {res['quote_validity_rate'] * 100:.1f}% ({res['valid_quotes_count']}/{res['total_processed']})")
        print("------------------------------------------------------------------")
        print("Distribusi Sektor Korban Terpapar:")
        for sec, cnt in sorted(res["sector_distribution"].items(), key=lambda x: x[1], reverse=True):
            if cnt > 0:
                print(f"  - {sec:38}: {cnt} berita")
        print("==================================================================")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Gagal menjalankan klasifikasi mingguan: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
