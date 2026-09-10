import json
import requests
from bs4 import BeautifulSoup
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
from src.utils.http_client import buat_session_retry

s = buat_session_retry()
data = json.load(open('scripts/debug/audit_feed_report.json', encoding='utf-8'))
failed_names = ['Security Boulevard', 'CISA News', 'SANS ISC', 'Qualys Blog']

for d in data:
    if d['name'] in failed_names:
        print(f"\n==================================================")
        print(f"=== {d['name']} ({d['url']}) ===")
        print(f"==================================================")
        for a in d['article_tests']:
            link = a['link']
            print(f"\nTesting link: {link}")
            try:
                r = s.get(link, timeout=10)
                print(f"Status: {r.status_code}, content-type: {r.headers.get('content-type')}, HTML len: {len(r.text)}")
                
                # Check if Cloudflare / challenge
                if "cf-browser-verification" in r.text or "Just a moment..." in r.text:
                    print("--> BLOCKED by Cloudflare challenge!")
                
                soup = BeautifulSoup(r.text, 'html.parser')
                
                # Let's see how extractor.py tries to find content:
                # 1. tag decomposition
                for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
                    tag.decompose()
                
                elemen_konten = soup.find("article") or soup.find(
                    "div", class_=lambda c: c and any(x in str(c).lower() for x in ['detail', 'content', 'article', 'body', 'entry'])
                )
                print(f"elemen_konten found: {type(elemen_konten)}")
                if elemen_konten:
                    print(f"elemen_konten tag: <{elemen_konten.name} class='{elemen_konten.get('class')}'>")
                
                paragraf = elemen_konten.find_all("p") if elemen_konten else soup.find_all("p")
                teks = "\n".join(p.get_text(separator=" ", strip=True) for p in paragraf if p.get_text(strip=True))
                print(f"Total <p> found: {len(paragraf)}, total text length: {len(teks)}")
                if len(teks) > 0:
                    print(f"First 200 chars: {teks[:200]!r}")
                else:
                    # Why is teks 0? Let's check what tags exist in soup
                    print(f"Body text length (any tag): {len(soup.get_text(strip=True))}")
                    all_p = soup.find_all('p')
                    print(f"All <p> before/after filter: {len(all_p)}")
            except Exception as e:
                print(f"Error fetching/parsing: {e}")
