"""
Klasifikasi relevansi artikel menggunakan LLM lokal. Bertindak sebagai
filter lapis kedua setelah regex - regex terlalu kaku untuk membedakan
konteks (mis. "hacker" dalam berita insiden vs "hacker house" dalam
artikel gaya hidup startup), sementara LLM memahami makna kalimat.
"""
import re
from typing import Literal, Optional

import ollama
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

MODEL_CLASSIFIER = "llama3.2"
MAKS_KARAKTER_UNTUK_KLASIFIKASI = 1500  # cukup baca beberapa paragraf awal, tidak perlu artikel penuh

KATEGORI_VALID = {"insiden_spesifik", "analisis_relevan", "tidak_relevan"}

SYSTEM_PROMPT_KLASIFIKASI = """Kamu adalah analis intelijen keamanan siber. Klasifikasikan artikel berita ke dalam SALAH SATU dari 3 kategori berikut:

1. analisis_relevan:
   Khusus ARTIKEL EDUKASI / TIPS / PANDUAN PENCEGAHAN (EVERGREEN CONTENT), yaitu:
   - Tips keamanan password, panduan 2FA, kebiasaan pengguna, cara mencegah akun diretas/dibajak (misal: "Kebiasaan yang membuat akun mudah diretas", "Tips mengamankan WhatsApp").
   - Cara mengenali modus penipuan, phishing, smishing, dan panduan perlindungan diri bagi pengguna umum.
   - Panduan best practice keamanan siber umum yang BUKAN berita pelaporan serangan aktual di lapangan.

2. insiden_spesifik:
   Khusus BERITA KEJADIAN / PERISTIWA PENYERANGAN & ANCAMAN SIBER AKTUAL, yaitu:
   - Laporan peretasan, kebocoran data, serangan ransomware, defacement, pencurian dana / aset kripto pada korban/perusahaan/instansi.
   - Operasi serangan aktif, penyebaran malware nyata, aktivitas kelompok hacker/APT (misal: SilverFox, Storm-1175, Mr Spongebob), peretasan ribuan situs WordPress, atau kampanye phishing aktif.
   - Laporan lonjakan serangan terkini di lapangan dan penangkapan pelaku kejahatan siber.

3. tidak_relevan:
   Artikel yang SAMA SEKALI BUKAN tentang topik keamanan siber (berita AI produktivitas umum tanpa isu keamanan, gadget biasa, meme/hiburan, politik non-siber).

PANDUAN PENALARAN:
- Jika artikel memberikan saran, tips, panduan, edukasi pencegahan, tutorial, atau cara agar tidak diretas -> WAJIB 'analisis_relevan'.
- Jika artikel memberitakan kejadian peretasan riil, serangan malware aktif, atau aksi kelompok hacker/APT -> WAJIB 'insiden_spesifik'.
- Jika artikel bukan tentang keamanan siber -> WAJIB 'tidak_relevan'.

Format outputmu:
Alasan: [1 kalimat singkat]
Kategori: [insiden_spesifik / analisis_relevan / tidak_relevan]"""


def _ekstrak_label(respons_mentah: str) -> Optional[str]:
    """
    Mem-parsing output LLM jadi salah satu label valid (insiden_spesifik,
    analisis_relevan, tidak_relevan) dari format CoT / alasan + kategori.
    """
    if not respons_mentah:
        return None

    # 1. Cari baris yang mengandung 'kategori'
    for baris in respons_mentah.splitlines():
        baris_lower = baris.strip().lower()
        if "kategori" in baris_lower or "category" in baris_lower:
            for label in ("insiden_spesifik", "analisis_relevan", "tidak_relevan"):
                if label in baris_lower:
                    return label

    # 2. Periksa baris terakhir
    baris_terakhir = respons_mentah.strip().splitlines()[-1].lower()
    for label in ("insiden_spesifik", "analisis_relevan", "tidak_relevan"):
        if label in baris_terakhir:
            return label

    # 3. Fallback pencarian teks menyeluruh
    teks = respons_mentah.strip().lower()
    for label in ("insiden_spesifik", "tidak_relevan", "analisis_relevan"):
        if label in teks:
            return label

    return None


def klasifikasi_relevansi(judul: str, teks_asli: str, model: str = MODEL_CLASSIFIER) -> str:
    """
    Mengklasifikasi satu artikel. Mengembalikan 'analisis_relevan' sebagai
    fallback aman jika LLM gagal merespons/parsing gagal - lebih baik
    salah menerima (masih bisa disaring manusia saat baca digest) daripada
    salah membuang artikel yang sebenarnya penting.
    """
    teks_dipotong = teks_asli[:MAKS_KARAKTER_UNTUK_KLASIFIKASI]
    user_prompt = f"Judul: {judul}\n\nCuplikan isi:\n{teks_dipotong}"

    try:
        respons = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_KLASIFIKASI},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.0},  # 0 penuh: butuh konsistensi maksimal untuk klasifikasi
        )
        label = _ekstrak_label(respons["message"]["content"])
        if label:
            return label
        logger.warning(f"Gagal parsing label untuk '{judul[:50]}...', respons: {respons['message']['content'][:100]}")
        return "analisis_relevan"  # fallback aman
    except Exception as e:
        logger.error(f"Gagal memanggil classifier untuk '{judul[:50]}...': {e}")
        return "analisis_relevan"  # fallback aman


def filter_artikel_relevan(df: pd.DataFrame, model: str = MODEL_CLASSIFIER) -> pd.DataFrame:
    """
    Menjalankan klasifikasi untuk seluruh baris di df, membuang yang
    berlabel 'tidak_relevan', dan menyimpan kolom 'kategori_relevansi'
    untuk baris yang tersisa (berguna untuk nanti membedakan penyajian
    insiden vs analisis di pesan digest).
    """
    if df.empty:
        return df

    df = df.copy()
    label_list = []

    logger.info(f"Mengklasifikasi relevansi {len(df)} artikel...")
    for i, row in df.iterrows():
        label = klasifikasi_relevansi(row["judul"], row["teks_asli"], model)
        label_list.append(label)
        logger.info(f"[{i+1}/{len(df)}] [{label}] {row['judul'][:55]}...")

    df["kategori_relevansi"] = label_list

    jumlah_sebelum = len(df)
    df_relevan = df[df["kategori_relevansi"] != "tidak_relevan"].reset_index(drop=True)
    jumlah_dibuang = jumlah_sebelum - len(df_relevan)

    logger.info(
        f"Filter relevansi LLM: {jumlah_sebelum} -> {len(df_relevan)} "
        f"({jumlah_dibuang} dibuang sebagai tidak relevan)"
    )
    return df_relevan