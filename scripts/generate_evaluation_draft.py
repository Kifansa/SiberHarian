#!/usr/bin/env python3
"""
CLI Script: Pembangkitan Draf Dataset Evaluasi CTI (Tahap 6).
Mengekstrak berita dari state.db dan menghasilkan CSV berlabel otomatis
yang ditandai DRAFT_PENDING_USER_REVIEW dengan kolom verifikasi siap isi.
"""

import sys
import argparse
from pathlib import Path

# Tambahkan root directory ke sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cti.evaluator import generate_draft_dataset
from src.utils.logger import setup_logger

logger = setup_logger("scripts.generate_evaluation_draft")


def main():
    parser = argparse.ArgumentParser(description="Pembangkitan draf dataset evaluasi intelijen siber dari database.")
    parser.add_argument("--db-path", type=str, default=None, help="Jalur basis data SQLite (default: data/state.db).")
    parser.add_argument("--output", type=str, default=None, help="Jalur berkas CSV keluaran (default: data/evaluation/dataset_evaluasi_draf.csv).")
    parser.add_argument("--sample-size", type=int, default=200, help="Jumlah maksimum artikel berita yang diekstrak (default: 200).")

    args = parser.parse_args()

    kwargs = {}
    if args.db_path:
        kwargs["db_path"] = Path(args.db_path)
    if args.output:
        kwargs["output_csv_path"] = Path(args.output)
    kwargs["sample_size"] = args.sample_size

    try:
        csv_file = generate_draft_dataset(**kwargs)
        print(f"[SUCCESS] Draf dataset evaluasi berhasil dibuat:")
        print(f"  - Berkas: {csv_file}")
        print(f"  - Status entri: DRAFT_PENDING_USER_REVIEW")
        print(f"  - Petunjuk: Buka berkas CSV di atas, lalu isi kolom 'verified_kategori', 'verified_mitre_id', atau 'verified_sektor' untuk baris yang ingin diverifikasi.")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Gagal membangkitkan draf dataset evaluasi: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
