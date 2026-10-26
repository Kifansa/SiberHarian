#!/usr/bin/env python3
"""
CLI Script: Evaluasi Kinerja Pipeline Intelijen Siber CTI (Tahap 6).
Menghitung Precision, Recall, F1 per kategori taksonomi insiden,
serta akurasi teknik MITRE ATT&CK dari dataset yang telah diverifikasi manual.
"""

import sys
import json
import argparse
from pathlib import Path

# Tambahkan root directory ke sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cti.evaluator import calculate_evaluation_metrics, DEFAULT_DRAFT_CSV_PATH
from src.utils.logger import setup_logger

logger = setup_logger("scripts.evaluate_pipeline")


def main():
    parser = argparse.ArgumentParser(description="Kalkulasi metrik evaluasi pipeline intelijen siber CTI.")
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(DEFAULT_DRAFT_CSV_PATH),
        help="Jalur berkas dataset CSV yang dievaluasi.",
    )
    parser.add_argument(
        "--format",
        type=str,
        choices=["table", "json"],
        default="table",
        help="Format keluaran metrik: table (markdown/ascii) atau json.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Jalur berkas keluaran untuk menyimpan hasil evaluasi JSON.",
    )

    args = parser.parse_args()

    if args.format == "json":
        import logging
        for name in list(logging.root.manager.loggerDict.keys()):
            l = logging.getLogger(name)
            l.setLevel(logging.WARNING)
            for h in l.handlers:
                h.setLevel(logging.WARNING)


    csv_path = Path(args.dataset)
    if not csv_path.exists():
        print(f"[ERROR] Berkas dataset tidak ditemukan: {csv_path}", file=sys.stderr)
        sys.exit(1)

    try:
        results = calculate_evaluation_metrics(csv_path)

        if args.output:
            out_file = Path(args.output)
            out_file.parent.mkdir(parents=True, exist_ok=True)
            out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"[INFO] Hasil evaluasi JSON disimpan di: {out_file}")

        if args.format == "json":
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            status = results.get("status")
            if status == "NO_VERIFIED_ROWS":
                print(f"[PERINGATAN] {results.get('message')}")
                print(f"Total baris dalam dataset: {results.get('total_rows')} (0 terverifikasi).")
            elif status == "EMPTY_DATASET":
                print(f"[PERINGATAN] {results.get('message')}")
            else:
                print("==================================================================")
                print("  LAPORAN EVALUASI PIPELINE INTELIJEN SIBER (SIBERHARIAN CTI)")
                print("==================================================================")
                print(f"Dataset Evaluasi: {csv_path}")
                print(f"Total Sampel: {results.get('total_rows')} | Terverifikasi: {results.get('verified_rows')}")
                print("------------------------------------------------------------------")
                print(results.get("summary_table", ""))
                print("==================================================================")

        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] Evaluasi pipeline gagal: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
