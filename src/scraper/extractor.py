"""
Ekstraksi konten artikel dari URL: decode URL Google News, ekstraksi
teks (hybrid: BeautifulSoup langsung + fallback newspaper3k), dan
normalisasi tanggal publikasi ke format standar.
"""
import re
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from datetime import timezone
from newspaper import Article

from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def dapatkan_url_asli(google_url: str, session: requests.Session) -> str:
    """
    Mendecode URL Google News menjadi URL artikel asli.
    Mencoba library `googlenewsdecoder` dulu, fallback ke parsing
    manual atribut `data-n-v`. Jika keduanya gagal, URL asli
    dikembalikan apa adanya (artikel tetap bisa diambil, hanya link
    yang dikirim ke user nanti akan mengarah ke redirect Google).
    """
    try:
        from googlenewsdecoder import new_decoderv1
        hasil = new_decoderv1(google_url)
        if hasil.get("status"):
            return hasil.get("decoded_url")
    except Exception as e:
        logger.debug(f"Decoder googlenewsdecoder gagal untuk {google_url}: {e}")

    try:
        resp = session.get(google_url, timeout=10)
        match = re.search(r'data-n-v="([^"]+)"', resp.text)
        if match:
            return match.group(1)
    except Exception as e:
        logger.debug(f"Parser manual decode gagal untuk {google_url}: {e}")

    return google_url


def ekstrak_teks_hybrid(
    url: str, session: requests.Session, timeout: int = 15
) -> Tuple[Optional[str], Optional[str]]:
    teks_ekstraksi = None
    tanggal_mentah = None
    alasan_gagal_tahap1 = None
    alasan_gagal_tahap2 = None

    # Tahap 1: scraping langsung
    try:
        resp = session.get(url, timeout=timeout)
        if resp.status_code != 200:
            alasan_gagal_tahap1 = f"HTTP {resp.status_code}"
        else:
            soup = BeautifulSoup(resp.text, "html.parser")

            for selector, atribut in [
                ("meta[property='article:published_time']", "content"),
                ("meta[name='pubdate']", "content"),
                ("meta[name='publishdate']", "content"),
                ("meta[itemprop='datePublished']", "content"),
                ("time[datetime]", "datetime"),
            ]:
                tag = soup.select_one(selector)
                if tag and tag.get(atribut):
                    tanggal_mentah = tag.get(atribut)
                    break

            for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside"]):
                tag.decompose()

            elemen_konten = soup.find("article") or soup.find(
                "div", class_=re.compile(r"(detail|content|article|body|entry)", re.IGNORECASE)
            )
            paragraf = elemen_konten.find_all("p") if elemen_konten else soup.find_all("p")
            teks = "\n".join(
                p.get_text(separator=" ", strip=True)
                for p in paragraf if p.get_text(strip=True)
            )
            teks = re.sub(r"[ \t]+", " ", teks)

            if len(teks) > 100:
                teks_ekstraksi = teks
            else:
                alasan_gagal_tahap1 = f"teks terlalu pendek ({len(teks)} karakter)"
    except Exception as e:
        alasan_gagal_tahap1 = f"exception: {e}"

    # Tahap 2: fallback ke newspaper3k
    if not teks_ekstraksi:
        try:
            artikel = Article(url)
            artikel.download()
            artikel.parse()
            if len(artikel.text) > 100:
                teks_ekstraksi = artikel.text
            else:
                alasan_gagal_tahap2 = f"teks terlalu pendek ({len(artikel.text)} karakter)"
            if not tanggal_mentah and artikel.publish_date:
                tanggal_mentah = artikel.publish_date.isoformat()
        except Exception as e:
            alasan_gagal_tahap2 = f"exception: {e}"

    if not teks_ekstraksi:
        logger.warning(
            f"[GAGAL EKSTRAK] {url} — Tahap 1: {alasan_gagal_tahap1} | Tahap 2 (newspaper3k): {alasan_gagal_tahap2}"
        )

    return teks_ekstraksi, tanggal_mentah


def normalisasi_tanggal(tanggal_mentah: Optional[str]) -> Optional[str]:
    """
    Menormalkan tanggal dari berbagai format & zona waktu (RFC 822
    dengan offset GMT/EDT/dll dari RSS, ISO 8601 dari meta tag) menjadi
    SATU zona waktu acuan: UTC, format 'YYYY-MM-DD HH:MM:SS'.

    PENTING: tanpa konversi ke UTC, membandingkan jam dari feed berzona
    Eastern Time (AS) dengan jam dari feed berzona WIB bisa salah
    sampai 11-12 jam, menyebabkan artikel yang sebenarnya baru malah
    dianggap kadaluarsa (atau sebaliknya).
    """
    if not tanggal_mentah:
        return None
    try:
        parsed = date_parser.parse(tanggal_mentah)
        if parsed.tzinfo is None:
            # Tidak ada info zona waktu eksplisit di string - asumsikan
            # UTC (aman untuk sumber internasional; untuk sumber lokal
            # tanpa offset, risiko meleset beberapa jam ditoleransi
            # karena window 24 jam cukup longgar).
            parsed = parsed.replace(tzinfo=timezone.utc)
        else:
            parsed = parsed.astimezone(timezone.utc)
        return parsed.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.debug(f"Gagal parsing tanggal '{tanggal_mentah}': {e}")
        return None