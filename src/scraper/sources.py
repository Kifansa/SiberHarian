"""
Memuat konfigurasi dari config.yaml dan 
menyiapkan struktur data yang dibutuhkan tahap pengumpulan berita.
"""
import re
import math
import urllib.parse
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "config.yaml"


def muat_config(path: Path = CONFIG_PATH) -> dict:
    """Membaca file config.yaml dan mengembalikannya sebagai dict."""
    if not path.exists():
        raise FileNotFoundError(f"File konfigurasi tidak ditemukan: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def bangun_daftar_feed_rss(config: dict) -> List[Tuple[str, str, bool, str]]:
    """
    Menggabungkan RSS internasional + Indonesia. Elemen ke-4 (kategori)
    membedakan perlakuan filter:
    - "trusted_cyber": media berita cybersecurity, SEMUA kontennya
      relevan by definition -> tidak perlu filter kata kunci judul.
    - "umum": media umum yang isinya campur topik -> wajib difilter.
    """
    daftar_feed = []
    for sumber in SettingsManager.get_rss_sources("international"):
        if sumber.get("active", True) is not False:
            for url in sumber["feeds"]:
                daftar_feed.append((url, sumber["nama"], False, "trusted_cyber"))
    for sumber in SettingsManager.get_rss_sources("indonesia"):
        if sumber.get("active", True) is not False:
            for url in sumber["feeds"]:
                daftar_feed.append((url, sumber["nama"], False, "umum"))
    return daftar_feed


def bangun_daftar_feed_google_news(config: dict) -> List[Tuple[str, str, bool, str]]:
    """
    Membangun daftar feed Google News berdasarkan kata kunci query di
    config.yaml. Parameter 'when:Xd' otomatis mengikuti window_hours di
    config (dibulatkan ke atas ke satuan hari), supaya tidak perlu diubah
    manual tiap kali window_hours diganti (mis. 7 hari saat awal, lalu
    1 hari untuk cron harian rutin).
    """
    gn_config = config.get("google_news", {})
    hl = gn_config.get("hl", "id")
    gl = gn_config.get("gl", "ID")
    ceid = gn_config.get("ceid", "ID:id")

    window_hours = config.get("pipeline", {}).get("window_hours", 24)
    # Dibulatkan ke ATAS supaya window jam yang tidak genap kelipatan 24 jam
    # tetap tercakup penuh (mis. 36 jam -> 2 hari, bukan terpotong jadi 1 hari).
    jumlah_hari_gn = max(1, math.ceil(window_hours / 24))

    daftar_feed = []
    for kw in gn_config.get("query_keywords", []):
        for q in (kw, f"{kw} when:{jumlah_hari_gn}d"):
            encoded_q = urllib.parse.quote(q)
            rss_url = f"https://news.google.com/rss/search?q={encoded_q}&hl={hl}&gl={gl}&ceid={ceid}"
            daftar_feed.append((rss_url, "Google News", True, "umum"))
    return daftar_feed

from src.utils.settings_manager import SettingsManager

def _kumpulkan_semua_kata_kunci(config: dict) -> Dict[str, List[str]]:
    kw = SettingsManager.get_keywords()
    return {
        "english": kw.get("english", []),
        "mandiri": kw.get("indonesia_mandiri", []),
        "objek_data": kw.get("objek_data_sensitif", []),
        "objek_aset": kw.get("objek_aset_digital", []),
        "indikator": kw.get("indikator_insiden", []),
        "ambigu": kw.get("ambigu_butuh_konteks", []),
    }


def _compile_regex(daftar_kata: List[str]) -> re.Pattern:
    """
    Compile regex gabungan dengan word boundary (\\b) agar tidak
    menangkap kata sebagai substring kata lain (mis. 'nik' di dalam
    'teknik', atau 'hack' di dalam 'backpack').
    """
    if not daftar_kata:
        return re.compile(r"(?!x)x")
    return re.compile(r"\b(?:" + "|".join(re.escape(k) for k in daftar_kata) + r")\b", re.IGNORECASE)


class FilterKataKunci:
    """
    Membungkus seluruh pola regex kata kunci dan logika keputusan
    relevansi teks, supaya modul lain (pipeline.py) cukup panggil
    satu method `.relevan(teks)` tanpa perlu tahu detail kombinasinya.
    """

    def __init__(self, config: dict):
        kw = _kumpulkan_semua_kata_kunci(config)
        self.pola_mandiri_en = _compile_regex(kw["english"] + kw["mandiri"])
        self.pola_objek_data = _compile_regex(kw["objek_data"])
        self.pola_objek_aset = _compile_regex(kw["objek_aset"])
        self.pola_indikator = _compile_regex(kw["indikator"])
        self.pola_ambigu = _compile_regex(kw["ambigu"])
        semua_kata = kw["english"] + kw["mandiri"] + kw["objek_data"] + kw["objek_aset"] + kw["indikator"] + kw["ambigu"]
        self.pola_semua = _compile_regex(semua_kata)

    def relevan(self, teks: str) -> bool:
        """
        True jika teks mengandung kata kunci insiden yang tidak ambigu,
        ATAU mengandung kombinasi objek (data sensitif/aset digital) +
        indikator insiden dalam teks yang sama.
        """
        if not teks:
            return False
        if self.pola_mandiri_en.search(teks):
            return True
        if self.pola_objek_data.search(teks) and self.pola_indikator.search(teks):
            return True
        if self.pola_objek_aset.search(teks) and self.pola_indikator.search(teks):
            return True
        if self.pola_ambigu.search(teks) and (
            self.pola_objek_aset.search(teks) or self.pola_indikator.search(teks)
        ):
            return True
        return False

    def temukan_kata_kunci(self, teks: str) -> List[str]:
        """Mengembalikan daftar unik kata kunci yang ditemukan (untuk kolom anotasi)."""
        return list(set(self.pola_semua.findall(teks)))

