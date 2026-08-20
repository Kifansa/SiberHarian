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

SYSTEM_PROMPT_KLASIFIKASI = """Kamu adalah classifier yang menentukan apakah sebuah artikel berita
layak masuk ke digest keamanan siber harian untuk tim security perusahaan.

SYARAT UTAMA: Topik artikel harus tentang KEAMANAN SIBER (peretasan, kebocoran data, malware,
penipuan online, kerentanan sistem, dll). Artikel soal AI/teknologi/bisnis pada umumnya yang
TIDAK menyinggung keamanan siber harus dianggap tidak_relevan, walau berasal dari media
keamanan siber (media seperti BleepingComputer/Dark Reading juga publish berita AI, produk, atau
bisnis umum yang tidak ada hubungannya dengan security).

Setelah dipastikan topiknya keamanan siber, klasifikasikan ke SALAH SATU dari 3 kategori:

1. insiden_spesifik - Melaporkan insiden siber NYATA & SPESIFIK dengan korban/kejadian konkret:
   organisasi/sistem/individu tertentu mengalami kebocoran data, serangan ransomware, peretasan.
   Contoh: "Peretas Curi Data Pasien Perusahaan Farmasi Amgen" -> insiden_spesifik.
   BUKAN untuk artikel tips/edukasi/panduan umum, meski soal siber - itu masuk analisis_relevan.
   PENTING: Jika sebuah artikel politik/kriminal/hukum DIPICU OLEH kebocoran/pencurian data
   (data itu jadi sebab-akibat inti cerita, bukan cuma disinggung sepintas), tetap klasifikasikan
   sebagai insiden_spesifik. Contoh: "Kebocoran Data Internal Picu Kasus Pemerasan Bupati" ->
   insiden_spesifik (kebocoran data adalah akar masalahnya, bukan sekadar disinggung).

2. analisis_relevan - Pembahasan berbasis DATA/RISET/TREN soal ancaman siber (walau tanpa satu
   insiden spesifik), ATAU artikel edukasi/panduan/tips seputar keamanan siber.
   Contoh: "Riset Kaspersky: 52% Gen Z Pernah Jadi Korban Serangan Siber" -> analisis_relevan.
   Contoh: "5 Tanda Phishing yang Wajib Diwaspadai" -> analisis_relevan.

3. tidak_relevan - Artikel yang TIDAK tentang keamanan siber, meski mengandung kata seperti
   "hacker"/"diretas"/"judi online" secara kebetulan/kiasan/konteks lain, ATAU artikel dari media
   security yang topiknya sebenarnya AI/produk/bisnis umum (bukan soal keamanan).
   Contoh: "OpenAI teases Astra, its next major AI model" -> tidak_relevan.
   Contoh: "8 Meme Anime tentang Peretas" -> tidak_relevan (hiburan).
   Contoh: "Lift House, Anti-San Francisco Hacker House di London" -> tidak_relevan.

PENTING - PRINSIP KEHATI-HATIAN: Melewatkan insiden siber penting jauh lebih berbahaya daripada
menampilkan artikel yang ternyata kurang relevan (pembaca masih bisa melewati artikel yang
kurang penting saat membaca digest). Karena itu:
- Jika kamu RAGU antara tidak_relevan dan analisis_relevan/insiden_spesifik, PILIH
  analisis_relevan (jangan tidak_relevan).
- tidak_relevan HANYA untuk kasus yang JELAS dan MERUPAKAN KEPASTIAN tinggi tidak ada
  hubungannya dengan keamanan siber (meme, gosip selebriti, kata "hacker" dalam konteks lain
  yang jelas, berita AI/bisnis/produk yang jelas tidak menyinggung security sama sekali).

Jawab HANYA dengan satu kata persis salah satu dari: insiden_spesifik, analisis_relevan, tidak_relevan
JANGAN menjawab dengan kalimat, penjelasan, atau tanda baca tambahan apa pun.
"""


def _ekstrak_label(respons_mentah: str) -> Optional[str]:
    """
    Mem-parsing output LLM jadi salah satu label valid. Model kadang
    tetap menambahkan embel-embel meski sudah dilarang (mis. titik di
    akhir, atau kalimat pembuka) - fungsi ini toleran terhadap noise
    kecil semacam itu.
    """
    teks = respons_mentah.strip().lower()
    for label in KATEGORI_VALID:
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