"""
Utility pembersihan output mentah dari LLM lokal (Ollama) - dipisah
sebagai modul independen (bukan bagian dari llm_summarizer.py) supaya
modul lain yang juga generate teks via LLM (mis. trend_predictor.py)
bisa memakainya tanpa menyebabkan circular import.
"""
import re
from typing import Optional

# Pola kalimat pembuka yang sering muncul meski sudah dilarang lewat
# system prompt - jaring pengaman karena LLM terbukti tidak selalu
# patuh instruksi.
POLA_PEMBUKA_TERLARANG = re.compile(
    r"^(berikut(\s+adalah)?\s+ringkasan[^:]*:|"
    r"berikut(\s+adalah)?\s+(penjelasan|artikel)[^:]*:|"
    r"tentu[,.]?\s*|"
    r"berdasarkan\s+(teks|artikel|deskripsi)[^:]*:)\s*",
    re.IGNORECASE,
)


def _panjang_prefix_sama(a: str, b: str) -> int:
    """Menghitung panjang prefix yang SAMA PERSIS antara 2 string (case-insensitive).
    Dipakai untuk memotong pengulangan judul dengan presisi - bukan asumsi
    panjang penuh, karena judul dari RSS sering mengandung embel-embel nama
    situs (mis. '- Adatah - adatah.com') yang TIDAK pernah diulang oleh LLM."""
    a, b = a.lower(), b.lower()
    n = min(len(a), len(b))
    i = 0
    while i < n and a[i] == b[i]:
        i += 1
    return i


def bersihkan_output_llm(teks: Optional[str], judul_atau_id: str = "") -> Optional[str]:
    """
    Membersihkan output LLM dari pelanggaran format yang terbukti masih
    lolos meski sudah dilarang di system prompt:
    1. Kalimat pembuka generik ("Berikut ringkasan...", "Tentu,", dst).
    2. Pengulangan judul/CVE ID verbatim di awal kalimat pertama.
    """
    if not teks:
        return teks

    teks = teks.strip()

    for _ in range(2):
        teks_baru = POLA_PEMBUKA_TERLARANG.sub("", teks).strip()
        if teks_baru == teks:
            break
        teks = teks_baru

    teks = re.sub(r"\n{2,}", "\n", teks).strip()

    if judul_atau_id:
        panjang_sama = _panjang_prefix_sama(teks, judul_atau_id)
        if panjang_sama >= 20:
            sisa = teks[panjang_sama:].lstrip(" .:-\n")
            if len(sisa) > 20 and sisa[0].isupper():
                teks = sisa

    return teks.strip()