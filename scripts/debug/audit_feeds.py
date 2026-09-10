"""
Audit script untuk menguji keandalan teknis seluruh RSS feed dan artikel
dari config/config.yaml.
"""
import sys
import os
import json
import time
from pathlib import Path
from collections import defaultdict
import feedparser
import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.scraper.sources import muat_config
from src.scraper.extractor import ekstrak_teks_hybrid, normalisasi_tanggal
from src.utils.http_client import buat_session_retry

def audit_all():
    config = muat_config()
    session = buat_session_retry()
    timeout = 15

    # 1. Kumpulkan semua sumber
    sources = []
    for s in config.get("rss_sources_indonesia", []):
        for url in s["feeds"]:
            sources.append({"name": s["nama"], "url": url, "region": "Indonesia", "cat": "umum"})
    for s in config.get("rss_sources_international", []):
        for url in s["feeds"]:
            sources.append({"name": s["nama"], "url": url, "region": "International", "cat": "trusted_cyber"})

    print(f"Total feed yang diaudit: {len(sources)}")
    print("=" * 80)

    report = []

    for idx, item in enumerate(sources, 1):
        s_name = item["name"]
        feed_url = item["url"]
        region = item["region"]

        res = {
            "name": s_name,
            "region": region,
            "url": feed_url,
            "feed_status_code": None,
            "feed_error": None,
            "entries_count": 0,
            "bozo": False,
            "bozo_exception": None,
            "date_format_sample": None,
            "date_parse_ok": False,
            "date_normalized": None,
            "article_tests": []
        }

        t0 = time.time()
        try:
            resp = session.get(feed_url, timeout=timeout)
            res["feed_status_code"] = resp.status_code
            res["feed_latency"] = round(time.time() - t0, 2)

            if resp.status_code != 200:
                res["feed_error"] = f"HTTP {resp.status_code}"
            else:
                feed = feedparser.parse(resp.content)
                res["bozo"] = bool(feed.get("bozo"))
                if res["bozo"] and feed.get("bozo_exception"):
                    res["bozo_exception"] = str(feed.get("bozo_exception"))[:100]

                entries = feed.entries
                res["entries_count"] = len(entries)

                if entries:
                    sample_entry = entries[0]
                    raw_date = sample_entry.get("published", "") or sample_entry.get("updated", "")
                    res["date_format_sample"] = raw_date
                    norm = normalisasi_tanggal(raw_date)
                    res["date_normalized"] = norm
                    res["date_parse_ok"] = bool(norm)

                    # Test scraping pada 2 sample artikel
                    for entry in entries[:2]:
                        art_link = entry.get("link", "").strip()
                        art_title = entry.get("title", "").strip()
                        if not art_link:
                            continue

                        art_res = {
                            "link": art_link,
                            "title": art_title[:40],
                            "http_status": None,
                            "text_length": 0,
                            "success": False,
                            "error": None,
                            "meta_date": None
                        }

                        try:
                            # Cek status direct
                            art_resp = session.get(art_link, timeout=12)
                            art_res["http_status"] = art_resp.status_code

                            # Cek dengan ekstrak_teks_hybrid
                            teks, tgl_meta = ekstrak_teks_hybrid(art_link, session, timeout=12)
                            art_res["meta_date"] = tgl_meta
                            if teks:
                                art_res["text_length"] = len(teks)
                                art_res["success"] = len(teks) > 100
                            else:
                                art_res["error"] = "Teks kosong / < 100 char"
                        except Exception as ea:
                            art_res["error"] = str(ea)[:100]

                        res["article_tests"].append(art_res)
                        time.sleep(0.5)

        except Exception as e:
            res["feed_error"] = str(e)[:150]

        report.append(res)
        status_sym = "[OK]" if res["entries_count"] > 0 and (not res["article_tests"] or any(a["success"] for a in res["article_tests"])) else "[FAIL/WARN]"
        print(f"[{idx}/{len(sources)}] {status_sym} {s_name} ({region}) -> entries: {res['entries_count']}, feed_status: {res['feed_status_code']}, date_ok: {res['date_parse_ok']}")
        if res.get("article_tests"):
            for a in res["article_tests"]:
                print(f"      Article: HTTP {a['http_status']} | Len: {a['text_length']} | Success: {a['success']} | Err: {a['error']} | Link: {a['link'][:70]}")
        if res.get("feed_error"):
            print(f"      Feed Error: {res['feed_error']}")
        sys.stdout.flush()

    out_file = PROJECT_ROOT / "scripts" / "debug" / "audit_feed_report.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"\nHasil disimpan di: {out_file}")

if __name__ == "__main__":
    audit_all()
