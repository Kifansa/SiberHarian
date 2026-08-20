"""
Menarasikan statistik tren (hasil trend_analyzer.py) menjadi teks yang
mudah dibaca tim security, menggunakan LLM lokal (Ollama). BUKAN sumber
angka - LLM di sini murni menerjemahkan angka yang SUDAH dihitung Python
jadi bahasa manusia, supaya tidak ada ruang untuk mengarang insiden
atau CVE yang tidak nyata.
"""
from typing import Dict, List, Optional

import ollama

from src.utils.llm_text_cleaner import bersihkan_output_llm
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

MODEL_PREDIKTOR = "llama3.2"

# Ambang batas minimal supaya LLM tidak dipaksa menganalisis data yang
# terlalu tipis untuk bermakna (mis. cuma 1 kata kunci muncul 1x).
MIN_JUMLAH_TERKINI = 2
MIN_GROWTH_PERSEN = 20.0

SYSTEM_PROMPT_TREN_BERITA = """Kamu adalah analis intelijen ancaman siber yang membaca data STATISTIK
tren mingguan (bukan artikel utuh) untuk membantu tim keamanan siber sebuah perusahaan mengantisipasi
ancaman yang berpotensi meningkat.

Kamu akan diberi data terstruktur:
- Daftar kata kunci insiden siber yang frekuensinya NAIK dalam 3 hari terakhir dibanding 4 hari
  sebelumnya (dengan angka jumlah & persentase growth).
- Perbandingan jumlah artikel insiden_spesifik vs analisis_relevan.

ATURAN KETAT:
- HANYA gunakan angka yang diberikan. JANGAN mengarang insiden, korban, organisasi, atau kejadian
  spesifik yang TIDAK ada di data ini (data ini agregat kata kunci, bukan artikel individual).
- JANGAN membuat klaim kepastian soal masa depan. Hindari kata "akan terjadi"/"pasti". Gunakan bahasa
  probabilistik yang jujur: "berpotensi meningkat", "perlu diwaspadai", "menunjukkan pola naik".
- Fokus ke: topik/kata kunci apa yang sedang naik, dan implikasi praktis yang perlu diwaspadai tim
  (contoh: "aktivitas terkait phishing meningkat, tim perlu perkuat awareness & filter email").
- Jika growth di data kecil/tidak konsisten, katakan jujur bahwa tren belum kuat - JANGAN
  memaksakan narasi dramatis dari data lemah.
- Tulis 3-5 kalimat, Bahasa Indonesia, untuk dibaca tim security (bukan akademis).
- Langsung tulis analisisnya, tanpa kalimat pembuka seperti "Berikut analisisnya:".
"""

SYSTEM_PROMPT_TREN_CVE = """Kamu adalah analis kerentanan (vulnerability management) yang membaca data
STATISTIK agregat CVE mingguan untuk membantu tim keamanan siber memprioritaskan patching.

Kamu akan diberi data terstruktur: vendor mana yang jumlah CVE HIGH/CRITICAL-nya NAIK dalam 3 hari
terakhir dibanding 4 hari sebelumnya (dengan angka jumlah, growth persen, dan jumlah CRITICAL di
antaranya).

ATURAN KETAT:
- HANYA gunakan angka yang diberikan. JANGAN mengarang CVE ID, detail teknis kerentanan, atau nama
  produk spesifik yang TIDAK ada di data ini (data ini agregat per vendor, bukan CVE individual).
- JANGAN membuat klaim kepastian soal masa depan. Gunakan bahasa probabilistik: "perlu diprioritaskan",
  "berisiko lebih tinggi untuk dieksploitasi mengingat jumlah kerentanan yang meningkat".
- Fokus ke: vendor/produk mana yang perlu diprioritaskan tim untuk patching & monitoring, berdasarkan
  volume dan jumlah CRITICAL yang meningkat.
- Jika growth di data kecil/tidak konsisten, katakan jujur bahwa belum ada vendor yang menonjol -
  JANGAN memaksakan narasi dramatis dari data lemah.
- Tulis 3-5 kalimat, Bahasa Indonesia, untuk dibaca tim security (bukan akademis).
- Langsung tulis analisisnya, tanpa kalimat pembuka seperti "Berikut analisisnya:".
"""


def _panggil_llm(system_prompt: str, user_prompt: str, model: str) -> Optional[str]:
    """Memanggil Ollama, mengembalikan None kalau gagal (biar pemanggil bisa fallback aman)."""
    try:
        respons = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.3},
        )
        return respons["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Gagal memanggil model prediktor tren ({model}): {e}")
        return None


def _filter_naik_signifikan(items: List[Dict]) -> List[Dict]:
    """
    Membuang entri yang growth-nya tidak signifikan atau jumlahnya
    terlalu sedikit untuk dipercaya sebagai tren nyata (bisa jadi cuma
    kebetulan 1 artikel nyasar).
    """
    return [
        item for item in items
        if item["jumlah_terkini"] >= MIN_JUMLAH_TERKINI and item["growth_persen"] >= MIN_GROWTH_PERSEN
    ]


def _format_kata_kunci_untuk_prompt(daftar_kk: List[Dict]) -> str:
    baris = [
        f"- '{kk['kata_kunci']}': muncul {kk['jumlah_terkini']}x dalam 3 hari terakhir "
        f"(sebelumnya {kk['jumlah_baseline']}x dalam 4 hari), growth {kk['growth_persen']}%"
        for kk in daftar_kk
    ]
    return "\n".join(baris)


def _format_vendor_untuk_prompt(daftar_vendor: List[Dict]) -> str:
    baris = [
        f"- {v['vendor']}: {v['jumlah_terkini']} CVE dalam 3 hari terakhir "
        f"({v['jumlah_critical_terkini']} di antaranya CRITICAL), sebelumnya {v['jumlah_baseline']} CVE "
        f"dalam 4 hari, growth {v['growth_persen']}%"
        for v in daftar_vendor
    ]
    return "\n".join(baris)


def prediksi_tren_berita(statistik_berita: Dict, model: str = MODEL_PREDIKTOR) -> str:
    """
    Menghasilkan narasi tren berita insiden siber. Mengembalikan pesan
    fallback (BUKAN memanggil LLM) kalau data tidak cukup signifikan -
    supaya tidak ada narasi dipaksakan dari data lemah/kosong.
    """
    kk_signifikan = _filter_naik_signifikan(statistik_berita.get("kata_kunci_naik", []))

    if not kk_signifikan:
        logger.info("Tidak ada kata kunci berita dengan tren naik signifikan, skip pemanggilan LLM.")
        return (
            "Belum terdeteksi pola tren yang signifikan pada topik berita insiden siber "
            "dalam 7 hari terakhir. Data masih terlalu sedikit atau relatif stabil dibanding periode sebelumnya."
        )

    tren_kategori = statistik_berita.get("tren_kategori", {})
    insiden_info = tren_kategori.get("insiden_spesifik") or {}

    user_prompt = (
        f"Kata kunci dengan tren naik signifikan (3 hari terakhir vs 4 hari sebelumnya):\n"
        f"{_format_kata_kunci_untuk_prompt(kk_signifikan)}\n\n"
        f"Jumlah artikel insiden_spesifik: {insiden_info.get('jumlah_terkini', 0)} dalam 3 hari terakhir "
        f"(sebelumnya {insiden_info.get('jumlah_baseline', 0)} dalam 4 hari), "
        f"growth {insiden_info.get('growth_persen', 0)}%."
    )

    hasil = _panggil_llm(SYSTEM_PROMPT_TREN_BERITA, user_prompt, model)
    if hasil is None:
        # Fallback aman: tetap tampilkan data mentah kalau LLM gagal dipanggil
        return "Analisis LLM gagal dijalankan. Data mentah: " + _format_kata_kunci_untuk_prompt(kk_signifikan)

    return bersihkan_output_llm(hasil)


def prediksi_tren_cve(statistik_cve: Dict, model: str = MODEL_PREDIKTOR) -> str:
    """Menghasilkan narasi tren CVE per vendor. Sama prinsipnya dengan prediksi_tren_berita di atas."""
    vendor_signifikan = _filter_naik_signifikan(statistik_cve.get("vendor_naik", []))

    if not vendor_signifikan:
        logger.info("Tidak ada vendor CVE dengan tren naik signifikan, skip pemanggilan LLM.")
        return (
            "Belum terdeteksi vendor dengan lonjakan CVE yang signifikan dalam 7 hari terakhir. "
            "Volume kerentanan relatif stabil dibanding periode sebelumnya."
        )

    user_prompt = (
        f"Vendor dengan tren jumlah CVE naik signifikan (3 hari terakhir vs 4 hari sebelumnya):\n"
        f"{_format_vendor_untuk_prompt(vendor_signifikan)}"
    )

    hasil = _panggil_llm(SYSTEM_PROMPT_TREN_CVE, user_prompt, model)
    if hasil is None:
        return "Analisis LLM gagal dijalankan. Data mentah: " + _format_vendor_untuk_prompt(vendor_signifikan)

    return bersihkan_output_llm(hasil)


def proses_prediksi_tren(statistik_tren: Dict, model: str = MODEL_PREDIKTOR) -> Dict[str, str]:
    """
    Titik masuk utama modul ini: menerima output susun_ringkasan_statistik_tren()
    dari trend_analyzer.py, mengembalikan 2 narasi terpisah siap tampil di web.
    """
    logger.info("Menyusun prediksi tren berita...")
    narasi_berita = prediksi_tren_berita(statistik_tren["berita"], model)

    logger.info("Menyusun prediksi tren CVE...")
    narasi_cve = prediksi_tren_cve(statistik_tren["cve"], model)

    return {"prediksi_berita": narasi_berita, "prediksi_cve": narasi_cve}


if __name__ == "__main__":
    # Testing manual: python -m src.analytics.trend_predictor
    from src.analytics.trend_analyzer import susun_ringkasan_statistik_tren
    from src.storage.db import ambil_riwayat_tren

    df = ambil_riwayat_tren(hari=7)
    statistik = susun_ringkasan_statistik_tren(df)
    hasil = proses_prediksi_tren(statistik)

    print("=== PREDIKSI TREN BERITA ===")
    print(hasil["prediksi_berita"])
    print("\n=== PREDIKSI TREN CVE ===")
    print(hasil["prediksi_cve"])