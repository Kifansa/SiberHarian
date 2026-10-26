#!/usr/bin/env python3
"""
CLI Script: Pembaruan Berkala MITRE ATT&CK Enterprise (Tahap 5).
Mendukung pengecekan versi idempoten, drop guard, diff report, re-embedding inkremental,
dan penandaan teknik revoked historis.
"""

import sys
import argparse
from pathlib import Path

# Tambahkan root directory ke sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.cti.updater import CTISourceUpdater, DropDetectionError
from src.utils.logger import setup_logger

logger = setup_logger("scripts.update_attack")


def main():
    parser = argparse.ArgumentParser(description="Pembaruan berkala dataset MITRE ATT&CK Enterprise.")
    parser.add_argument("--force", action="store_true", help="Paksa pembaruan meskipun versi hulu tidak berubah.")
    parser.add_argument("--date", type=str, default=None, help="Tanggal folder staging (YYYY-MM-DD).")
    parser.add_argument("--mirror-base-url", type=str, default=None, help="URL basis mirror internal jika ada.")
    parser.add_argument("--proxy", type=str, default=None, help="URL proxy HTTP/HTTPS.")
    parser.add_argument("--db-path", type=str, default=None, help="Jalur basis data SQLite.")

    args = parser.parse_args()

    proxies = None
    if args.proxy:
        proxies = {"http": args.proxy, "https": args.proxy}

    kwargs = {}
    if args.mirror_base_url:
        kwargs["mirror_base_url"] = args.mirror_base_url
    if proxies:
        kwargs["proxies"] = proxies
    if args.db_path:
        kwargs["db_path"] = Path(args.db_path)

    updater = CTISourceUpdater(**kwargs)

    try:
        result = updater.update_attack(date_str=args.date, force=args.force)
        status = result.get("status")
        if status == "UP_TO_DATE":
            print(f"[IDEMPOTENT] {result.get('message')}")
            sys.exit(0)
        elif status == "SUCCESS":
            print(f"[SUCCESS] Pembaruan MITRE ATT&CK selesai. Versi: {result.get('version')}")
            print(f"  - Total teknik aktif: {result.get('total_active_techniques')}")
            diff = result.get("diff", {})
            print(f"  - Diff: {diff.get('counts')}")
            print(f"  - Insiden historis di-flag (revoked): {result.get('historical_incidents_flagged')}")
            swap = result.get("atomic_swap", {})
            print(f"  - Re-embedded: {swap.get('reembedded_count')} | Reused: {swap.get('reused_count')}")
            sys.exit(0)
        else:
            print(f"[FAILED] {result}")
            sys.exit(1)
    except DropDetectionError as e:
        print(f"[ABORTED - DROP GUARD] {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] Terjadi kegagalan pembaruan: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
