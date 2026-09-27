"""
Pengecekan kepatuhan robots.txt sebelum pengumpulan konten artikel.
Menjaga etika scraping dan kepatuhan hukum sesuai UU No. 28/2014 & UU ITE.
"""
from functools import lru_cache
from typing import Dict, Optional
import urllib.robotparser
from urllib.parse import urlparse

import requests
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_BOT_USER_AGENT = "News Project (+https://kifansa.my/id; kifansanf@gmail.com)"
_ROBOTS_PARSER_CACHE: Dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}


def ambil_robots_parser(base_url: str, session: Optional[requests.Session] = None, timeout: int = 10) -> Optional[urllib.robotparser.RobotFileParser]:
    """
    Mengambil dan mem-parsing robots.txt dari domain sumber.
    Menggunakan HTTP session dengan User-Agent resmi agar tidak diblokir CDN.
    """
    if base_url in _ROBOTS_PARSER_CACHE:
        return _ROBOTS_PARSER_CACHE[base_url]

    robots_url = f"{base_url.rstrip('/')}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)

    http = session or requests.Session()
    headers = {"User-Agent": DEFAULT_BOT_USER_AGENT}

    try:
        resp = http.get(robots_url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            rp.parse(resp.text.splitlines())
            _ROBOTS_PARSER_CACHE[base_url] = rp
            return rp
        elif resp.status_code == 404:
            # 404 artinya tidak ada pembatasan robots.txt
            rp.allow_all = True
            _ROBOTS_PARSER_CACHE[base_url] = rp
            return rp
    except Exception as e:
        logger.debug(f"Gagal mengambil robots.txt dari {robots_url}: {e}")

    # Fallback: jika robots.txt tidak bisa diakses, kembalikan None (permissif)
    _ROBOTS_PARSER_CACHE[base_url] = None
    return None


def boleh_scrape(url: str, session: Optional[requests.Session] = None, user_agent: str = DEFAULT_BOT_USER_AGENT) -> bool:
    """
    Memeriksa apakah URL diizinkan untuk di-scrape berdasarkan aturan robots.txt domain tersebut.
    Mengembalikan True jika diizinkan atau jika robots.txt tidak membatasi.
    """
    if not url:
        return False

    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return True

        base_url = f"{parsed.scheme}://{parsed.netloc}"
        rp = ambil_robots_parser(base_url, session=session)

        if rp is None or getattr(rp, "allow_all", False):
            return True

        # Ambil nama bot utama dari format User-Agent (mis. 'News Project')
        bot_token = user_agent.split("(")[0].strip() or "*"
        diizinkan = rp.can_fetch(bot_token, url) or rp.can_fetch("*", url)
        return diizinkan
    except Exception as e:
        logger.debug(f"Gagal memeriksa izin robots.txt untuk {url}: {e}")
        return True
