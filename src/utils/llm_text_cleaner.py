"""
Utility pembersihan output mentah dari model AI CTI - dipisah
sebagai modul independen (bukan bagian dari llm_summarizer.py) supaya
modul lain yang juga generate teks via LLM (mis. trend_predictor.py)
bisa memakainya tanpa menyebabkan circular import.
"""
import os
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


def bersihkan_output_llm(teks: Optional[str], judul_atau_id: str = "") -> Optional[str]:
    """
    Membersihkan output LLM dari pelanggaran format yang terbukti masih
    lolos meski sudah dilarang di system prompt:
    1. Kalimat pembuka generik ("Berikut ringkasan...", "Tentu,", dst).
    2. Pengulangan judul/identitas insiden verbatim di awal kalimat pertama.
    """
    if not teks:
        return teks

    teks = teks.strip()

    for _ in range(2):
        teks_baru = POLA_PEMBUKA_TERLARANG.sub("", teks).strip()
        if teks_baru == teks:
            break
        teks = teks_baru

    teks = re.sub(r"\n{3,}", "\n\n", teks).strip()

    if judul_atau_id:
        panjang_sama = len(os.path.commonprefix([teks.lower(), judul_atau_id.lower()]))
        if panjang_sama >= 20:
            sisa = teks[panjang_sama:].lstrip(" .:-\n")
            if len(sisa) > 20 and sisa[0].isupper():
                teks = sisa

    return teks.strip()