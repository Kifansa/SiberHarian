"""
Session HTTP dengan retry otomatis (exponential backoff), dipakai oleh
seluruh modul yang melakukan request (RSS fetch, scraping artikel,
decode Google News URL). Diterapkan di level adapter HTTP sehingga
retry berlaku otomatis tanpa logika manual di tiap pemanggil.
"""
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

DEFAULT_USER_AGENT = "News Project (+https://kifansa.my/id; kifansanf@gmail.com)"


def buat_session_retry(
    user_agent: str = DEFAULT_USER_AGENT,
    max_retry: int = 3,
    backoff_factor: float = 1.5,
) -> requests.Session:
    """Membuat requests.Session dengan retry otomatis dan identitas bot transparan."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "id,en;q=0.8",
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