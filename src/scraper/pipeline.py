"""
Orkestrasi pipeline pengumpulan berita cybersecurity dari seluruh
sumber RSS (media internasional, media Indonesia, Google News).
Alur: kumpulkan entri RSS -> filter window waktu 24 jam -> filter
kata kunci -> ekstraksi konten lengkap.
"""
import re
import time as time_module
from datetime import datetime, timedelta, timezone
from typing import List

import feedparser
import pandas as pd
import requests

from collections import Counter

from src.scraper.extractor import (
    dapatkan_url_asli,
    ekstrak_teks_hybrid,
    normalisasi_tanggal,
)
from src.scraper.robots_checker import boleh_scrape
from src.scraper.sources import (
    FilterKataKunci,
    bangun_daftar_feed_google_news,
    bangun_daftar_feed_rss,
    muat_config,
)
from src.utils.http_client import buat_session_retry
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Pola judul noise (podcast, audio, webinar marketing, event promo) yang langsung diabaikan
POLA_NOISE_JUDUL = re.compile(
    r"\b(podcast|stormcast|webinar|virtual event|whitepaper|download guide|cfp tracker|squid blogging)\b",
    re.IGNORECASE,
)


def _ekstrak_media_google_news(entry: dict, judul: str):
    media = None
    src = entry.get("source")
    if src:
        media = getattr(src, "title", None) if hasattr(src, "title") else src.get("title") if isinstance(src, dict) else None

    judul_bersih = judul
    if " - " in judul:
        bagian = judul.rsplit(" - ", 1)
        if len(bagian) == 2 and len(bagian[1].strip()) < 50:
            if not media:
                media = bagian[1].strip()
            judul_bersih = bagian[0].strip()

    return media or "Google News", judul_bersih


def parse_rss_feeds(
    daftar_feed: List[tuple], url_ditemukan: set, session: requests.Session, timeout: int
) -> List[dict]:
    """
    Mem-parsing sekumpulan RSS feed generik, mengembalikan entri baru
    (judul + link) yang belum pernah terlihat. daftar_feed berisi
    tuple (rss_url, sumber_nama, butuh_decode).
    """
    entri = []
    for rss_url, sumber_nama, butuh_decode, kategori in daftar_feed:
        # Tambahkan parameter cache-busting supaya tidak dapat respons basi dari CDN
        pemisah = "&" if "?" in rss_url else "?"
        url_dengan_cache_bust = f"{rss_url}{pemisah}_cb={int(time_module.time())}"
        try:
            resp = session.get(url_dengan_cache_bust, timeout=timeout)
        except requests.exceptions.RequestException as e:
            logger.warning(f"[GAGAL REQUEST] {sumber_nama} ({rss_url}): {e}")
            continue

        if resp.status_code != 200:
            logger.warning(f"[HTTP {resp.status_code}] {sumber_nama} ({rss_url})")
            continue

        feed = feedparser.parse(resp.content)
        if not feed.entries:
            alasan = getattr(feed, "bozo_exception", None)
            logger.warning(f"[FEED KOSONG] {sumber_nama} ({rss_url}) — {alasan or 'tidak diketahui'}")
            continue

        entri_baru = 0
        for entry in feed.entries:
            judul = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            tanggal_rss = entry.get("published", "") or entry.get("updated", "")

            if sumber_nama == "Google News":
                nama_media, judul = _ekstrak_media_google_news(entry, judul)
            else:
                nama_media = sumber_nama

            if judul and link and link not in url_ditemukan:
                url_ditemukan.add(link)
                entri.append({
                    "judul": judul,
                    "url": link,
                    "tanggal_rss": tanggal_rss,
                    "sumber_nama": nama_media,
                    "butuh_decode": butuh_decode,
                    "kategori": kategori,
                })
                entri_baru += 1

        logger.info(f"[OK] {sumber_nama} — {len(feed.entries)} entri.")
    return entri


def _dalam_window_waktu(tanggal_rss: str, window_hours: int) -> bool:
    """
    Mengecek apakah tanggal_rss berada dalam window waktu (default 24
    jam terakhir). Jika tanggal tidak bisa diparsing, mengembalikan
    True (ambigu -> tetap diproses, lebih baik daripada kehilangan
    berita relevan; validasi tanggal final dilakukan lagi setelah
    ekstraksi konten penuh).
    """
    tanggal_normal = normalisasi_tanggal(tanggal_rss)
    if not tanggal_normal:
        return True
    try:
        waktu_artikel = datetime.strptime(tanggal_normal, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        batas_bawah = datetime.now(timezone.utc) - timedelta(hours=window_hours)
        return waktu_artikel >= batas_bawah
    except ValueError:
        return True


def jalankan_pipeline_berita(config: dict = None) -> pd.DataFrame:
    """
    Menjalankan pipeline lengkap pengumpulan berita cybersecurity:
    RSS media internasional + Indonesia + Google News -> filter window
    24 jam -> filter kata kunci -> ekstraksi konten.

    Returns:
        DataFrame berisi artikel yang lolos filter dan berhasil diekstrak,
        dengan kolom: sumber, judul, tanggal, teks_asli, link, kata_kunci.
    """
    config = config or muat_config()
    pipeline_cfg = config.get("pipeline", {})
    window_hours = pipeline_cfg.get("window_hours", 24)
    delay = pipeline_cfg.get("request_delay_seconds", 1)
    timeout = pipeline_cfg.get("request_timeout", 15)

    session = buat_session_retry(
        max_retry=pipeline_cfg.get("max_retry", 3),
        backoff_factor=pipeline_cfg.get("backoff_factor", 1.5),
    )
    filter_kk = FilterKataKunci(config)

    # --- TAHAP 1: Kumpulkan judul & link dari semua sumber RSS ---
    logger.info("=" * 60)
    logger.info("TAHAP 1: Mengumpulkan Judul Berita dari RSS...")
    logger.info("=" * 60)

    url_ditemukan = set()
    logger.info("[+] Mengambil RSS media internasional & Indonesia...")
    entri_semua = parse_rss_feeds(bangun_daftar_feed_rss(config), url_ditemukan, session, timeout)
    logger.info("[+] Mengambil RSS Google News...")
    entri_semua += parse_rss_feeds(bangun_daftar_feed_google_news(config), url_ditemukan, session, timeout)
    logger.info(f"Total entri terkumpul: {len(entri_semua)}")

    # --- TAHAP 2: Filter awal (waktu + judul) sebelum ekstraksi ---
    lolos_window = [e for e in entri_semua if _dalam_window_waktu(e["tanggal_rss"], window_hours)]
    logger.info(f"Setelah filter window waktu ({window_hours} jam) saja: {len(lolos_window)} (dari {len(entri_semua)})")

    entri_kandidat = [
        e for e in lolos_window
        if not POLA_NOISE_JUDUL.search(e["judul"])
        and (e["kategori"] == "trusted_cyber" or filter_kk.relevan(e["judul"]))
    ]
    logger.info(f"Setelah filter kata kunci & anti-noise (media trusted_cyber dilewatkan): {len(entri_kandidat)} (dari {len(lolos_window)})")

    # --- TAHAP 3: Ekstraksi konten lengkap ---
    logger.info("=" * 60)
    logger.info("TAHAP 2: Ekstraksi Konten Berita...")
    logger.info("=" * 60)

    artikel_hasil = []
    gagal_ekstrak_per_sumber = Counter()
    gagal_window_final_per_sumber = Counter()

    for i, entri in enumerate(entri_kandidat):
        logger.info(f"  -> [{i+1}/{len(entri_kandidat)}] {entri['judul'][:60]}...")

        url_target = entri["url"]
        if entri["butuh_decode"]:
            url_target = dapatkan_url_asli(entri["url"], session)

        if not boleh_scrape(url_target, session=session):
            logger.info(f"     [-] Scraping dibatasi oleh robots.txt: {url_target}")
            continue

        time_module.sleep(delay)
        teks_artikel, tanggal_halaman = ekstrak_teks_hybrid(url_target, session, timeout)

        if not teks_artikel:
            logger.debug("     [-] Gagal ekstraksi konten, dilewati.")
            gagal_ekstrak_per_sumber[entri["sumber_nama"]] += 1
            continue

        tanggal_final = normalisasi_tanggal(tanggal_halaman) or normalisasi_tanggal(entri.get("tanggal_rss"))

        if tanggal_final:
            waktu_artikel = datetime.strptime(tanggal_final, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if waktu_artikel < datetime.now(timezone.utc) - timedelta(hours=window_hours):
                logger.debug(f"     [-] Di luar window {window_hours} jam, dilewati.")
                gagal_window_final_per_sumber[entri["sumber_nama"]] += 1
                continue

        teks_lengkap = f"{entri['judul']} {teks_artikel}".lower()
        if entri["kategori"] != "trusted_cyber" and not filter_kk.relevan(teks_lengkap):
            logger.debug("     [-] Tidak relevan setelah cek konten penuh, dilewati.")
            continue

        kata_kunci_ditemukan = filter_kk.temukan_kata_kunci(teks_lengkap)
        logger.info("     [+] SUKSES EKSTRAK!")

        artikel_hasil.append({
            "sumber": entri["sumber_nama"],
            "judul": entri["judul"],
            "tanggal": tanggal_final,
            "teks_asli": teks_artikel,
            "link": url_target,
            "kata_kunci": ", ".join(kata_kunci_ditemukan),
        })

    logger.info(f"SELESAI: {len(artikel_hasil)} artikel berhasil diekstrak & lolos filter.")
    logger.info(f"Gagal ekstraksi konten per sumber: {dict(gagal_ekstrak_per_sumber)}")
    logger.info(f"Gagal re-validasi window (tanggal final) per sumber: {dict(gagal_window_final_per_sumber)}")

    return pd.DataFrame(artikel_hasil)