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

SYSTEM_PROMPT_TREN_BERITA = """Kamu adalah Lead Cyber Threat Intelligence (CTI) Analyst. Tugasmu menyusun laporan intelijen ancaman siber eksekutif yang tajam, komprehensif, dan actionable bagi tim security berdasarkan data statistik dan sampel insiden riil mingguan.

Format analisismu dalam 4 bagian terstruktur:

1. 🌐 LANSKAP & POLA ANCAMAN UTAMA
   Ringkas pola peretasan/serangan utama yang terdeteksi dari sampel insiden aktual dan tren kata kunci yang naik.

2. 🎯 VEKTOR SERANGAN (TTPs) & SEKTOR TERPAPAR
   Jelaskan taktik utama penyerang (misal malware infostealer, phishing bertema AI/pajak, eksploitasi RCE) dan sektor/vertikal industri yang paling banyak dibidik.

3. 🔗 HUBUNGAN KERENTANAN & ANCAMAN
   Jelaskan hubungan antara insiden ancaman di lapangan dengan eksposur kerentanan sistem atau teknologi yang diserang.

4. 🛡️ REKOMENDASI MITIGASI BERTINGKAT
   - Prioritas: Langkah teknis darurat (misal: blokir IoC/domain phishing, audit akses privilege, isolasi endpoint terindikasi).
   - Tindak Lanjut Jangka Panjang: Langkah mitigasi preventif (misal: audit dependency code, simulasi phishing karyawan, review backup).

ATURAN KETAT:
- HANYA gunakan fakta dari data dan sampel judul yang diberikan. JANGAN mengarang nama korban, instansi, CVE, atau angka di luar data.
- Gunakan gaya bahasa profesional Cyber Threat Intelligence, padat, lugas, dan bernilai strategis bagi tim security/CISO.
- WAJIB gunakan format list (bullet points). DILARANG KERAS menggunakan format tabel (markdown table).
- JANGAN menambahkan catatan tambahan, penjelasan skor, atau kesimpulan apa pun di akhir analisis.
- Langsung tulis isi analisisnya tanpa kalimat pembuka seperti "Berikut laporannya:".
"""

SYSTEM_PROMPT_TREN_CVE = """Kamu adalah Senior Vulnerability Management Analyst. Tugasmu menyusun rekomendasi prioritas patching dan mitigasi risiko kerentanan perangkat lunak berdasarkan data agregat CVE CRITICAL mingguan.

Format analisismu dalam 3 bagian terstruktur:

1. 🛡️ VENDOR & PRODUK PRIORITAS TINGGI
   Sebutkan vendor dan produk spesifik (dari data yang diberikan) yang paling mendesak untuk ditambal berdasarkan volume dan persentase lonjakan kerentanan.

2. ⚡ ANALISIS VEKTOR EKSPLOITASI & DAMPAK
   Jelaskan potensi risiko dampak teknis (misal: Remote Code Execution, Privilege Escalation, Denial of Service) jika produk terdampak tidak segera dimitigasi.

3. 📋 PANDUAN PATCHING & MITIGASI TAKTIS
   - Prioritas Patching Segera: Jadwal patching terencana untuk produk terpapar internet publik.
   - Mitigasi Sementara (Workaround): Penguatan kontrol akses jaringan, isolasi port, atau WAF filtering jika patch belum dapat langsung diterapkan.

ATURAN KETAT:
- HANYA gunakan vendor/produk/angka yang diberikan. JANGAN mengarang CVE ID atau nama produk di luar data ini.
- Gunakan bahasa probabilistik profesional ("berisiko tinggi dieksploitasi", "perlu diprioritaskan").
- Langsung tulis analisisnya tanpa kalimat pembuka seperti "Berikut analisisnya:".
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
    terlalu sedikit untuk dipercaya sebagai tren nyata.
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
    baris = []
    for v in daftar_vendor:
        produk_teks = (
            ", ".join(f"{p['produk']} ({p['jumlah']}x)" for p in v["top_produk"])
            if v["top_produk"] else "produk tidak teridentifikasi"
        )
        baris.append(
            f"- {v['vendor']}: {v['jumlah_terkini']} CVE CRITICAL dalam 3 hari terakhir "
            f"(sebelumnya {v['jumlah_baseline']} dalam 4 hari), growth {v['growth_persen']}%. "
            f"Produk terdampak: {produk_teks}"
        )
    return "\n".join(baris)


def _format_sampel_judul_untuk_prompt(daftar_judul: List[Dict]) -> str:
    if not daftar_judul:
        return "(tidak ada sampel judul insiden spesifik pada periode ini)"
    return "\n".join(f"- \"{j['judul']}\" ({j['sumber']})" for j in daftar_judul)


def prediksi_tren_berita(statistik_tren: Dict, model: str = MODEL_PREDIKTOR) -> str:
    statistik_berita = statistik_tren.get("berita", {})
    kk_signifikan = _filter_naik_signifikan(statistik_berita.get("kata_kunci_naik", []))

    if not kk_signifikan:
        logger.info("Tidak ada kata kunci berita dengan tren naik signifikan, skip pemanggilan LLM.")
        return (
            "Belum terdeteksi pola tren yang signifikan pada topik berita insiden siber "
            "dalam 7 hari terakhir. Data masih relatif stabil dibanding periode sebelumnya."
        )

    tren_kategori = statistik_berita.get("tren_kategori", {})
    insiden_info = tren_kategori.get("insiden_spesifik") or {}
    sampel_judul = statistik_berita.get("sampel_judul_insiden", [])

    threat_posture = statistik_tren.get("threat_posture", {})
    skor_risiko = threat_posture.get("skor", 5.0)
    level_risiko = threat_posture.get("level_label", "SEDANG (Moderate)")

    vektor_list = statistik_tren.get("vektor_serangan", [])[:4]
    vektor_str = ", ".join(f"{v['vektor']} ({v['jumlah']} artikel)" for v in vektor_list) if vektor_list else "Data vektor belum terakumulasi"

    sektor_list = statistik_tren.get("sektor_target", [])[:3]
    sektor_str = ", ".join(f"{s['sektor']} ({s['jumlah']} artikel)" for s in sektor_list) if sektor_list else "Data sektor belum terakumulasi"

    user_prompt = (
        f"Status Posture Risiko: {level_risiko} (Skor Risiko: {skor_risiko}/10)\n"
        f"Vektor Serangan Dominan Teratas: {vektor_str}\n"
        f"Sektor / Vertikal Target Teratas: {sektor_str}\n\n"
        f"Kata kunci insiden dengan tren naik signifikan (3 hari terakhir vs 4 hari sebelumnya):\n"
        f"{_format_kata_kunci_untuk_prompt(kk_signifikan)}\n\n"
        f"Jumlah artikel insiden aktual: {insiden_info.get('jumlah_terkini', 0)} dalam 3 hari terakhir "
        f"(sebelumnya {insiden_info.get('jumlah_baseline', 0)} dalam 4 hari), "
        f"growth {insiden_info.get('growth_persen', 0)}%.\n\n"
        f"Sampel judul artikel insiden siber aktual terkini:\n"
        f"{_format_sampel_judul_untuk_prompt(sampel_judul[:8])}"
    )

    hasil = _panggil_llm(SYSTEM_PROMPT_TREN_BERITA, user_prompt, model)
    if hasil is None:
        return "Analisis LLM gagal dijalankan. Data mentah: " + _format_kata_kunci_untuk_prompt(kk_signifikan)
    return bersihkan_output_llm(hasil)


def prediksi_tren_cve(statistik_cve: Dict, model: str = MODEL_PREDIKTOR) -> str:
    """Menghasilkan narasi tren CVE per vendor dan panduan mitigasi."""
    vendor_signifikan = _filter_naik_signifikan(statistik_cve.get("vendor_naik", []))

    if not vendor_signifikan:
        logger.info("Tidak ada vendor CVE dengan tren naik signifikan, skip pemanggilan LLM.")
        return (
            "Belum terdeteksi vendor dengan lonjakan CVE yang signifikan dalam 7 hari terakhir. "
            "Volume kerentanan relatif stabil dibanding periode sebelumnya."
        )

    user_prompt = (
        f"Vendor dengan tren jumlah CVE CRITICAL naik signifikan (3 hari terakhir vs 4 hari sebelumnya):\n"
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
    logger.info("Menyusun prediksi tren berita CTI...")
    narasi_berita = prediksi_tren_berita(statistik_tren, model)

    logger.info("Menyusun prediksi tren CVE...")
    narasi_cve = prediksi_tren_cve(statistik_tren.get("cve", {}), model)

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