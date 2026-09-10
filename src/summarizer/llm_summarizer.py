"""
Modul summarization menggunakan model LLM lokal (Ollama) untuk meringkas
berita insiden siber dan menarasikan CVE kritis. Seluruh proses berjalan
lokal - tidak ada konten yang dikirim ke API pihak ketiga.
"""
from typing import Optional
import re
import ollama
import pandas as pd

from src.utils.logger import setup_logger
from src.utils.llm_text_cleaner import bersihkan_output_llm

logger = setup_logger(__name__)

MODEL_SUMMARIZER = "llama3.2"  # ganti sesuai model yang sudah kamu pull di Ollama
MAKS_KARAKTER_ARTIKEL = 4000  # batasi panjang teks masuk ke LLM, hemat context & waktu proses


SYSTEM_PROMPT_BERITA = """Kamu adalah asisten yang meringkas berita insiden keamanan siber untuk
dibaca oleh tim keamanan siber sebuah perusahaan. Tulis ringkasan dalam Bahasa Indonesia yang:
- Faktual, padat, 2-3 kalimat saja.
- Fokus pada: APA yang terjadi, SIAPA/organisasi apa yang terdampak, DAMPAK atau data yang bocor (jika ada).
- Tidak menambahkan opini, spekulasi, kesimpulan, atau dampak/risiko yang TIDAK disebutkan secara
  eksplisit di teks asli. Jika teks asli tidak menyebutkan dampaknya, jangan mengarang dampaknya sendiri.
- Tulis ulang dengan kata-katamu sendiri, jangan menyalin kalimat panjang secara verbatim.
- ISTILAH TEKNIS: jika ada istilah teknis/nama algoritma/nama produk yang TIDAK memiliki padanan
  Bahasa Indonesia yang jelas dan umum (contoh: nama algoritma kriptografi, nama teknis produk),
  PERTAHANKAN istilah aslinya dalam Bahasa Inggris. JANGAN memaksakan terjemahan yang menghasilkan
  kata tidak bermakna. Contoh SALAH: "lattice cryptography" diterjemahkan jadi "kripsi gawang" (tidak
  bermakna). Contoh BENAR: tetap tulis "lattice cryptography" apa adanya.
- Kata "attacker"/"threat actor" dalam konteks keamanan siber SELALU berarti "penyerang", BUKAN
  "serangga" atau istilah lain yang tidak berhubungan.
- Langsung tulis ringkasannya saja, tanpa kalimat pembuka seperti "Berikut ringkasannya:" atau
  mengulang judul artikel di awal.
"""

SYSTEM_PROMPT_CVE = """Kamu adalah asisten yang menjelaskan kerentanan keamanan (CVE) untuk tim
keamanan siber perusahaan. Tulis penjelasan dalam Bahasa Indonesia yang:
- 2-3 kalimat, jelas dan mudah dipahami (hindari jargon berlebihan).
- Sebutkan nama Vendor/Pengembang dan nama Produk/Komponen spesifik yang terdampak secara jelas pada kalimat pertama (contoh: "Kerentanan ditemukan pada produk [Produk] dari [Vendor]...").
- Jika baris Produk/Vendor berlabel "Lainnya / Belum Teridentifikasi", cobalah identifikasi nama pembuat/vendor dan produk dari teks deskripsi bahasa Inggris.
- PENTING: Jika nama vendor benar-benar TIDAK DITEMUKAN atau tidak disebutkan dalam deskripsi, kamu WAJIB tetap mencantumkan "Lainnya / Belum Teridentifikasi" pada nama vendornya (contoh: "Kerentanan pada vendor Lainnya / Belum Teridentifikasi yang mempengaruhi..."). JANGAN menggantinya dengan istilah samar seperti "sebuah sistem", "aplikasi pihak ketiga", atau menebak-nebak vendor tanpa bukti, agar tim keamanan tetap dapat memantau entri yang belum terpetakan.
- Jelaskan: jenis kerentanannya apa secara teknis, dan risiko konkret jika dieksploitasi.
- HANYA jelaskan risiko/dampak yang SECARA EKSPLISIT disebutkan atau bisa disimpulkan LANGSUNG dari
  teks deskripsi yang diberikan. JANGAN menambahkan skenario serangan spesifik (misal: "bisa untuk
  phishing", "bisa untuk pencurian identitas") kecuali itu disebutkan eksplisit di deskripsi asli.
  Jika deskripsi tidak menyebut dampak konkret, cukup jelaskan JENIS kerentanannya secara teknis
  tanpa mengarang skenario dampaknya.
- ISTILAH TEKNIS: pertahankan istilah aslinya dalam Bahasa Inggris jika tidak ada padanan Indonesia
  yang jelas (nama fungsi, nama library, istilah kriptografi spesifik). Jangan memaksakan terjemahan.
- Kata "attacker" SELALU berarti "penyerang", BUKAN "serangga".
- Langsung tulis penjelasannya saja, tanpa kalimat pembuka, tanpa mengulang judul/CVE ID di awal kalimat.
"""


def _panggil_llm(system_prompt: str, user_prompt: str, model: str = MODEL_SUMMARIZER) -> Optional[str]:
    """
    Memanggil model lokal via Ollama. Mengembalikan None jika gagal
    (Ollama tidak jalan, model belum di-pull, dll) supaya pemanggil
    bisa fallback dengan aman, bukan bikin seluruh pipeline crash.
    """
    try:
        respons = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.3},  # rendah supaya ringkasan konsisten, tidak "kreatif" berlebihan
        )
        return respons["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Gagal memanggil model LLM ({model}): {e}")
        return None

def ringkas_berita(judul: str, teks_asli: str, model: str = MODEL_SUMMARIZER) -> Optional[str]:
    """Meringkas satu artikel berita insiden siber jadi 2-3 kalimat Bahasa Indonesia."""
    teks_dipotong = teks_asli[:MAKS_KARAKTER_ARTIKEL]
    user_prompt = f"Judul: {judul}\n\nIsi artikel:\n{teks_dipotong}"
    hasil = _panggil_llm(SYSTEM_PROMPT_BERITA, user_prompt, model)
    return bersihkan_output_llm(hasil, judul_atau_id=judul)


def narasikan_cve(cve: dict, model: str = MODEL_SUMMARIZER) -> Optional[str]:
    """Menarasikan satu CVE (CRITICAL atau HIGH) jadi penjelasan 2-3 kalimat Bahasa Indonesia."""
    vendor = cve.get("vendor", "")
    produk = cve.get("produk", "")
    if not vendor or "Lainnya" in vendor or "Belum" in vendor:
        vendor_produk_baris = "Lainnya / Belum Teridentifikasi (Coba cari vendor & produk di deskripsi. Jika tidak ditemukan, tetap gunakan 'Lainnya / Belum Teridentifikasi')"
    else:
        vendor_produk_baris = f"{vendor} - {produk or '-'}"

    user_prompt = (
        f"CVE ID: {cve.get('cve_id', '')}\n"
        f"Skor CVSS: {cve.get('skor_cvss', '')} ({cve.get('severity', '')})\n"
        f"Produk/Vendor: {vendor_produk_baris}\n"
        f"Deskripsi asli (Inggris): {cve.get('deskripsi', '')}"
    )
    hasil = _panggil_llm(SYSTEM_PROMPT_CVE, user_prompt, model)
    return bersihkan_output_llm(hasil, judul_atau_id=cve.get("cve_id", ""))


def ringkas_semua_berita(df_berita: pd.DataFrame, model: str = MODEL_SUMMARIZER) -> pd.DataFrame:
    """
    Meringkas seluruh baris di df_berita, menambahkan kolom 'ringkasan'.
    Diproses SATU PER SATU (sequential) - model lokal biasanya hanya
    punya 1 GPU/CPU untuk melayani, jadi paralelisasi request tidak
    akan mempercepat apa pun, cuma bikin antrean di sisi Ollama.
    """
    if df_berita.empty:
        return df_berita

    df_berita = df_berita.copy()
    ringkasan_list = []

    for i, row in df_berita.iterrows():
        logger.info(f"Meringkas [{i+1}/{len(df_berita)}]: {row['judul'][:50]}...")
        ringkasan = ringkas_berita(row["judul"], row["teks_asli"], model)

        if ringkasan is None:
            # Fallback: jika LLM gagal, tetap tampilkan cuplikan teks asli
            # supaya artikel tidak hilang total dari digest.
            logger.warning(f"Fallback ke cuplikan teks asli untuk: {row['judul'][:50]}")
            ringkasan = row["teks_asli"][:200].strip() + "..."

        ringkasan_list.append(ringkasan)

    df_berita["ringkasan"] = ringkasan_list
    return df_berita


def ringkas_daftar_cve(daftar_cve: list, model: str = MODEL_SUMMARIZER) -> list:
    """Menambahkan key 'narasi' ke tiap dict CVE dalam sebuah list (in-place & return)."""
    for cve in daftar_cve:
        logger.info(f"Menarasikan {cve['severity']}: {cve['cve_id']}")
        narasi = narasikan_cve(cve, model)
        cve["narasi"] = narasi or (cve["deskripsi"][:200] + "...")
    return daftar_cve


def proses_summarization_harian(hasil_pipeline: dict, model: str = MODEL_SUMMARIZER) -> dict:
    """
    Titik masuk utama: mengambil hasil dari pipeline_harian.py (berita +
    cve_struktur mentah) dan mengembalikan versi yang sudah dilengkapi
    ringkasan/narasi dari LLM, siap dipakai modul notifier.
    """
    logger.info("=" * 60)
    logger.info("MEMULAI SUMMARIZATION (LLM LOKAL)")
    logger.info("=" * 60)

    df_berita_ringkas = ringkas_semua_berita(hasil_pipeline["berita"], model)

    cve_struktur = hasil_pipeline["cve_struktur"]
    if cve_struktur["mode"] == "ada_critical":
        for grup in cve_struktur["grup_critical"]:
            ringkas_daftar_cve(grup["cve_list"], model)

    logger.info("Menyusun prediksi tren (berita & CVE)...")

    logger.info("SELESAI SUMMARIZATION.")
    return {"berita": df_berita_ringkas, "cve_struktur": cve_struktur}