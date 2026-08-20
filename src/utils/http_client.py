"""
Session HTTP dengan retry otomatis (exponential backoff), dipakai oleh
seluruh modul yang melakukan request (RSS fetch, scraping artikel,
decode Google News URL). Diterapkan di level adapter HTTP sehingga
retry berlaku otomatis tanpa logika manual di tiap pemanggil.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def buat_session_retry(
    user_agent: str = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    max_retry: int = 3,
    backoff_factor: float = 1.5,
) -> requests.Session:
    """Membuat requests.Session dengan retry otomatis dan header browser-like."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        "Referer": "https://www.google.com/",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    })
    retry_strategy = Retry(
        total=max_retry,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session