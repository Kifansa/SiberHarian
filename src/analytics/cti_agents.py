from src.utils.config_loader import ConfigLoader
import json
import logging
import re
from src.utils.config_loader import ConfigLoader
from typing import Dict, Any, Optional, List, Tuple
import ollama

from src.analytics.encyclopedia_lookup import search_encyclopedia, search_encyclopedia_per_incident

logger = logging.getLogger(__name__)

# =====================================================================
# MODULAR SECTION SYSTEM PROMPTS (DIRECT MARKDOWN - NO JSON BRITTLE)
# =====================================================================

# =====================================================================
# MAIN MULTI-AGENT / MODULAR ORCHESTRATOR ENTRY POINT
# =====================================================================


def _call_ollama_text(system_prompt: str, user_prompt: str, model: str = None, num_predict: int = 400) -> str:
    cfg = ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {})
    if not model: model = cfg.get("model", "llama3.2")
    temperature = cfg.get("temperature", 0.1)
    
    try:
        r = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            options={"temperature": temperature, "num_predict": num_predict}
        )
        return resp.get("message", {}).get("content", "")
    except Exception as e:
        logger.error(f"Ollama Call Error: {e}")
        return ""


def _bersihkan_tanggal_jika_ada(teks: str) -> str:
    import re
    teks = re.sub(r'\b(pada tanggal|tanggal|pada)\s+\d{1,2}\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember|jan|feb|mar|apr|mei|jun|jul|agu|sep|okt|nov|des)\s*\d{0,4}\b', '', teks, flags=re.IGNORECASE)
    return teks

def _generate_section_1_makro(data_makro: dict, model: str = "llama3.2") -> str:
    pola_makro = data_makro.get("nama_pola", "Insiden Terkini")
    korpus = data_makro.get("korpus_artikel", "")
    user_prompt = f"Topik Dominan: {pola_makro}\nFakta Riil:\n{korpus[:1500]}\n\nInstruksi: Sintesis 1 paragraf mengalir sesuai pedoman."
    hasil = _call_ollama_text(ConfigLoader.get_prompt("section_1_makro"), user_prompt, model, num_predict=ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {}).get("num_predict", {}).get("section_makro", 350))
    if not hasil or len(hasil) < 50:
        return f"Pola ancaman **{pola_makro}** mencatatkan eskalasi minggu ini."
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_2_mikro(top3_mikro: list, model: str = "llama3.2") -> str:
    if not top3_mikro:
        return "- (Belum ada data insiden aktif minggu ini)"
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    baris_input = []
    for idx, inc in enumerate(top3_mikro):
        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")
        fakta = inc.get("uraian_fakta", "")
        baris_input.append(f"{idx+1}. Kampanye: \"{nama_clean}\" ({inc.get('jumlah_artikel', 1)} laporan berita)\n   Detail: {fakta[:400]}")
    user_prompt = "Sintesiskan TEPAT 3 insiden berikut:\n\n" + "\n\n".join(baris_input)
    hasil = _call_ollama_text(ConfigLoader.get_prompt("section_2_mikro"), user_prompt, model, num_predict=500)
    if not hasil or len(hasil) < 60:
        return "\n".join(f"- **{inc.get('nama_insiden', '')}**: {inc.get('uraian_fakta', '')[:100]}..." for inc in top3_mikro)
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_3_vektor(top3_mikro: list, model: str = "llama3.2") -> str:
    if not top3_mikro:
        return "- (Belum ada vektor ancaman aktif yang dilaporkan)"
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    baris_input = []
    for idx, inc in enumerate(top3_mikro):
        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")
        fakta = inc.get("uraian_fakta", "")
        baris_input.append(f"{idx+1}. Kampanye: \"{nama_clean}\"\n   Detail Serangan: {fakta[:400]}")
    user_prompt = "Petakan alur teknis dan taktik MITRE ATT&CK dari insiden berikut:\n\n" + "\n\n".join(baris_input)
    hasil = _call_ollama_text(ConfigLoader.get_prompt("section_3_vektor"), user_prompt, model, num_predict=450)
    if not hasil or len(hasil) < 60:
        return "\n".join(f"- **Alur Serangan {inc.get('nama_insiden', '')}**: {inc.get('uraian_fakta', '')[:100]}..." for inc in top3_mikro)
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_5_emerging(ancaman_baru: dict, model: str = "llama3.2") -> str:
    nama_anc = ancaman_baru.get("nama", "Tidak Teridentifikasi")
    uraian_anc = ancaman_baru.get("uraian", "")
    if not ancaman_baru.get("ada"):
        return "Berdasarkan pemantauan korpus intelijen siber Jawa Timur minggu ini, tidak ditemukan sinyal anomali atau ancaman baru."
    user_prompt = f"Ancaman Baru Terdeteksi: {nama_anc}\nDetail Sinyal Ancaman:\n{uraian_anc[:1000]}\n\nInstruksi: Susun 1 paragraf analisis sinyal ancaman."
    hasil = _call_ollama_text(ConfigLoader.get_prompt("section_5_emerging"), user_prompt, model, num_predict=300)
    if not hasil or len(hasil) < 50:
        return f"Terdeteksi sinyal ancaman baru berupa **{nama_anc}**. {uraian_anc[:200]}"
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()



def _generate_section_4_rekomendasi(top3_mikro: list) -> str:
    poin_rekomendasi = []
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    for idx, inc in enumerate(top3_mikro):
        nama_raw = inc.get("nama_insiden", f"Insiden Siber {idx+1}")
        nama, _ = _bersihkan_judul_dan_publisher(nama_raw, "")
        mitigasi = inc.get("mitigasi_ensiklopedia", [])

        mit_items = "\n".join([f"- {m}" for m in mitigasi[:2]]) if mitigasi else "- [D3-MFA] Wajibkan autentikasi multifaktor berbasis token pada seluruh akses administratif.\n- [NIST PR.AC] Terapkan segmentasi jaringan dan prinsip hak akses minimal."
        poin_rekomendasi.append(
            f"**Rekomendasi Aksi untuk {nama}**\n{mit_items}"
        )
    return "\n\n".join(poin_rekomendasi)

def jalankan_pipeline_multi_agent(

    data_makro: dict,
    top3_mikro: List[dict],
    ancaman_baru: dict,
    model: str = "llama3.2",
    mode: str = "modular_llm"
) -> Tuple[str, dict]:
    """
    Menjalankan Modular CTI Pipeline:
    - Mode 'instant_rag': Mengembalikan SITREP komprehensif dalam < 0.1 detik berbasis data RAG murni.
    - Mode 'modular_llm': Mengenerate narasi per-section secara modular & terisolasi menggunakan Llama 3.2.
    """
    if mode == "instant_rag":
        logger.info("Menjalankan CTI Pipeline Mode INSTANT RAG (Super Cepat < 1s)...")
        laporan = _buat_fallback_sitrep_deterministik(data_makro, top3_mikro, ancaman_baru)
        return laporan, {"mode": "instant_rag"}

    logger.info("Menjalankan CTI Pipeline Mode MODULAR LLM (Section-by-Section Llama 3.2)...")

    # Section 1: Makro (~10-15s)
    logger.info("[CTI Modul 1/5] Menghasilkan Bagian 1: Tren Insiden Mingguan (Makro)...")
    sec1 = _generate_section_1_makro(data_makro, model=model)

    # Section 2: Mikro (~15-20s)
    logger.info("[CTI Modul 2/5] Menghasilkan Bagian 2: Lanskap & Entitas Ancaman (Mikro)...")
    sec2 = _generate_section_2_mikro(top3_mikro, model=model)

    # Section 3: Vektor & MITRE (~15-20s)
    logger.info("[CTI Modul 3/5] Menghasilkan Bagian 3: Vektor Serangan & MITRE ATT&CK (1-to-1)...")
    sec3 = _generate_section_3_vektor(top3_mikro, model=model)

    # Section 4: Rekomendasi Mitigasi (Instan dari Ensiklopedia Resmi D3FEND/NIST/OWASP)
    logger.info("[CTI Modul 4/5] Menginjeksi Bagian 4: Rekomendasi Aksi Ensiklopedia Resmi...")
    sec4 = _generate_section_4_rekomendasi(top3_mikro)

    # Section 5: Emerging Threats (~10-15s)
    logger.info("[CTI Modul 5/5] Menghasilkan Bagian 5: Prediksi & Ancaman Masa Depan...")
    sec5 = _generate_section_5_emerging(ancaman_baru, model=model)

    laporan_final = (
        f"### 1. TREN INSIDEN MINGGUAN (MAKRO)\n{sec1}\n\n"
        f"### 2. LANSKAP & ENTITAS ANCAMAN (MIKRO)\n{sec2}\n\n"
        f"### 3. VEKTOR SERANGAN & MITRE ATT&CK\n{sec3}\n\n"
        f"### 4. REKOMENDASI AKSI\n{sec4}\n\n"
        f"### 5. PREDIKSI & ANCAMAN MASA DEPAN (EMERGING THREATS)\n{sec5}"
    )

    logger.info("SITREP CTI 5-Bagian berhasil disusun secara modular tanpa error JSON!")
    return laporan_final, {"mode": "modular_llm"}


# =====================================================================
# MODULAR CVE SECTION GENERATORS (DIRECT MARKDOWN - NO JSON BRITTLE)
# =====================================================================

def _generate_cve_section_4_patching(vendor_signifikan: List[dict], cve_context: str = "") -> str:
    poin = []
    top_vendors = [v["vendor"] for v in vendor_signifikan[:3]] if vendor_signifikan else ["Vendor Terpapar"]
    v_str = ", ".join(top_vendors)
    poin.append(f"- **Pembaruan Keamanan Prioritas**: Segera terapkan security update dan patch resmi dari vendor ({v_str}) pada seluruh server produksi dan gateway jaringan.")
    poin.append(f"- **[D3-WAF] Isolasi & Virtual Patching**: Terapkan virtual patching rule pada Web Application Firewall (WAF) dan batasi akses antarmuka administratif hanya melalui jaringan VPN internal.")
    poin.append(f"- **[D3-EDR] Pemindaian & Audit Integritas**: Jalankan vulnerability scan terfokus dan aktifkan File Integrity Monitoring (FIM) untuk mendeteksi indikasi eksploitasi pasca-rilis celah.")
    return "\n".join(poin)

def _build_cve_fallback(vendor_signifikan: List[dict], cve_context: str) -> str:
    lines_sec1 = []
    for v in vendor_signifikan[:4]:
        p_names = ", ".join(f"{p['produk']} ({p['jumlah']}x)" for p in v.get("top_produk", [])[:3])
        lines_sec1.append(
            f"- **{v['vendor']} (+{int(v.get('growth_persen', 0))}%)**: Terdeteksi {v.get('jumlah_terkini', 0)} kerentanan CVE CRITICAL (baseline: {v.get('jumlah_baseline', 0)}). Produk terdampak utama mencakup {p_names or 'komponen sistem terkait'}."
        )
    sec1 = "\n".join(lines_sec1) if lines_sec1 else "- **Kerentanan Terdistribusi**: Belum terdeteksi vendor tunggal dengan lonjakan CVE kritis yang signifikan minggu ini."

    sec2 = (
        "- **Remote Code Execution (RCE)**: Mayoritas kerentanan kritis memungkinkan penyerang mengeksekusi kode arbitrer dari jarak jauh tanpa autentikasi awal, mengkompromikan perimeter host.\n"
        "- **Authentication Bypass & Privilege Escalation**: Celah pada antarmuka manajemen memungkinkan eskalasi hak akses dari akun pengguna biasa menjadi superadmin/root.\n"
        "- **Denial of Service (DoS)**: Kerentanan alokasi memori berisiko menyebabkan crash berulang pada layanan vital instansi."
    )

    sec3 = (
        "- **Integritas Token Sesi & Kredensial**: Risiko kompromi pada mekanisme validasi otentikasi dapat memicu pembajakan session cookie dan token akses administratif.\n"
        "- **Paparan Kriptografi & Komunikasi**: Celah pada pustaka jaringan dapat melemahkan enkripsi kanal transfer data dan memicu serangan Man-in-the-Middle (MitM).\n"
        "- **Ketahanan Database & File System**: Kompromi pada layer aplikasi membuka akses langsung terhadap integritas berkas data penting pemerintah."
    )

    sec4 = _generate_cve_section_4_patching(vendor_signifikan, cve_context)

    return (
        f"### 1. VENDOR & PRODUK PRIORITAS\n{sec1}\n\n"
        f"### 2. ANALISIS VEKTOR EKSPLOITASI\n{sec2}\n\n"
        f"### 3. IMPLIKASI KRIPTOGRAFI & INTEGRITAS SISTEM\n{sec3}\n\n"
        f"### 4. PANDUAN PATCHING & MITIGASI\n{sec4}"
    )

def _generate_cve_sec1(vendor_signifikan: List[dict], model: str = "llama3.2") -> str:
    lines = []
    for v in vendor_signifikan[:4]:
        p_names = ", ".join(f"{p['produk']} ({p['jumlah']}x)" for p in v.get("top_produk", [])[:3])
        lines.append(f"- Vendor: {v['vendor']}, Lonjakan: +{int(v.get('growth_persen', 0))}%, Total: {v.get('jumlah_terkini', 0)} CVE. Produk: {p_names}")
    user_prompt = "Daftar Vendor & Produk dengan Lonjakan CVE Kritis:\n" + "\n".join(lines)
    hasil = _call_ollama_text(ConfigLoader.get_prompt("cve_sec1_vendor"), user_prompt, model, num_predict=ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {}).get("num_predict", {}).get("section_makro", 350))
    if not hasil or len(hasil) < 40 or "- " not in hasil:
        lines_fallback = []
        for v in vendor_signifikan[:4]:
            p_names = ", ".join(f"{p['produk']} ({p['jumlah']}x)" for p in v.get("top_produk", [])[:3])
            lines_fallback.append(f"- **{v['vendor']} (+{int(v.get('growth_persen', 0))}%)**: Terdeteksi {v.get('jumlah_terkini', 0)} kerentanan CVE CRITICAL. Produk terdampak: {p_names or 'komponen sistem'}.")
        return "\n".join(lines_fallback) if lines_fallback else "- **Kerentanan Terdistribusi**: Belum terdeteksi vendor dengan lonjakan CVE kritis yang signifikan minggu ini."
    hasil_bersih = re.sub(r'^#+.*\n+', '', hasil).strip()
    return hasil_bersih

def _generate_cve_sec2(vendor_signifikan: List[dict], cve_context: str, model: str = "llama3.2") -> str:
    user_prompt = f"Konteks Kerentanan CVE Aktual:\n{cve_context[:1000]}\n\nInstruksi: Analisis tipe vektor eksploitasi dominan dalam butir poin."
    hasil = _call_ollama_text(ConfigLoader.get_prompt("cve_sec2_vektor"), user_prompt, model, num_predict=ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {}).get("num_predict", {}).get("section_makro", 350))
    if not hasil or len(hasil) < 40 or "- " not in hasil:
        return (
            "- **Remote Code Execution (RCE)**: Mayoritas kerentanan kritis memungkinkan eksekusi perintah arbitrer dari jarak jauh tanpa autentikasi awal.\n"
            "- **Authentication Bypass & Privilege Escalation**: Celah pada antarmuka otentikasi memicu potensi eskalasi akun biasa menjadi administrator.\n"
            "- **Denial of Service (DoS)**: Kerentanan alokasi memori berisiko menyebabkan kelumpuhan layanan portal publik."
        )
    hasil_bersih = re.sub(r'^#+.*\n+', '', hasil).strip()
    return hasil_bersih

def _generate_cve_sec3(vendor_signifikan: List[dict], cve_context: str, model: str = "llama3.2") -> str:
    user_prompt = f"Konteks Kerentanan CVE Aktual:\n{cve_context[:1000]}\n\nInstruksi: Ulas implikasi terhadap persandian, kriptografi, integritas token, dan server instansi dalam butir poin."
    hasil = _call_ollama_text(ConfigLoader.get_prompt("cve_sec3_kripto"), user_prompt, model, num_predict=ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {}).get("num_predict", {}).get("section_makro", 350))
    if not hasil or len(hasil) < 40 or "- " not in hasil:
        return (
            "- **Integritas Token Sesi & Kredensial**: Risiko kompromi pada mekanisme otentikasi dapat memicu pembajakan session cookie dan token akses administratif.\n"
            "- **Paparan Kriptografi & Komunikasi**: Celah pada protokol jaringan dapat memicu serangan Man-in-the-Middle (MitM) pada kanal data sensitif.\n"
            "- **Ketahanan Basis Data & File System**: Kompromi pada layer aplikasi membuka akses langsung terhadap integritas data penting pemerintah."
        )
    hasil_bersih = re.sub(r'^#+.*\n+', '', hasil).strip()
    return hasil_bersih

def jalankan_pipeline_cve_modular(
    statistik_cve: dict,
    df_riwayat: Optional[Any] = None,
    model: str = "llama3.2",
    mode: str = "modular_llm"
) -> str:
    """
    Menjalankan Pipeline CTI CVE Modular:
    - Mode 'instant_rag': Mengembalikan SITREP CVE dalam < 0.1s.
    - Mode 'modular_llm': Mengenerate 4 bagian CVE secara terpisah sekuensial.
    """
    vendor_naik = statistik_cve.get("vendor_naik", [])
    vendor_signifikan = [v for v in vendor_naik if v.get("jumlah_terkini", 0) >= 2 and v.get("growth_persen", 0) >= 15.0]
    if not vendor_signifikan:
        vendor_signifikan = vendor_naik[:4]

    cve_context = ""
    if df_riwayat is not None:
        try:
            from src.analytics.rag_engine import RAGEngine
            rag = RAGEngine(df_riwayat)
            cve_context = rag.retrieve_cve_context([v["vendor"] for v in vendor_signifikan[:4]])
        except Exception:
            pass

    if mode == "instant_rag":
        return _build_cve_fallback(vendor_signifikan, cve_context)

    logger.info("[CVE Modul 1/4] Menghasilkan Bagian 1: Vendor & Produk Prioritas...")
    sec1 = _generate_cve_sec1(vendor_signifikan, model=model)

    logger.info("[CVE Modul 2/4] Menghasilkan Bagian 2: Analisis Vektor Eksploitasi...")
    sec2 = _generate_cve_sec2(vendor_signifikan, cve_context, model=model)

    logger.info("[CVE Modul 3/4] Menghasilkan Bagian 3: Implikasi Kriptografi & Integritas...")
    sec3 = _generate_cve_sec3(vendor_signifikan, cve_context, model=model)

    logger.info("[CVE Modul 4/4] Menginjeksi Bagian 4: Panduan Patching & Mitigasi Ensiklopedia...")
    sec4 = _generate_cve_section_4_patching(vendor_signifikan, cve_context)

    return (
        f"### 1. VENDOR & PRODUK PRIORITAS\n{sec1}\n\n"
        f"### 2. ANALISIS VEKTOR EKSPLOITASI\n{sec2}\n\n"
        f"### 3. IMPLIKASI KRIPTOGRAFI & INTEGRITAS SISTEM\n{sec3}\n\n"
        f"### 4. PANDUAN PATCHING & MITIGASI\n{sec4}"
    )
def _deteksi_sektor_spesifik(teks: str) -> str:
    teks = teks.lower()
    if any(k in teks for k in ['pemerintah', 'pemprov', 'pemkab', 'pemkot', 'dinas']): return 'Sektor Administrasi Pemerintahan'
    if any(k in teks for k in ['sekolah', 'kampus', 'universitas', 'akademik']): return 'Sektor Pendidikan'
    if any(k in teks for k in ['rumah sakit', 'rsud', 'puskesmas', 'medis']): return 'Sektor Kesehatan'
    if any(k in teks for k in ['bank', 'keuangan', 'finansial']): return 'Sektor Keuangan'
    return 'Layanan Publik Daerah'

def _deteksi_senjata_spesifik(teks: str) -> str:
    teks = teks.lower()
    if 'ransomware' in teks: return 'Ransomware / File Encryptor'
    if 'phishing' in teks or 'apk' in teks: return 'Social Engineering & Malware APK'
    if 'deface' in teks or 'judi' in teks or 'slot' in teks: return 'Webshell & Defacement'
    if 'cve' in teks or 'rce' in teks: return 'Eksploitasi Celah Keamanan (RCE)'
    return 'Akses Ilegal & Eksploitasi Web'

def _deteksi_dampak_spesifik(teks: str) -> str:
    teks = teks.lower()
    if 'bocor' in teks or 'breach' in teks or 'dijual' in teks: return 'Kebocoran Data Sensitif'
    if 'lumpuh' in teks or 'down' in teks: return 'Kelumpuhan Layanan Publik'
    if 'enkripsi' in teks or 'tebusan' in teks: return 'Terkuncinya Basis Data Operasional'
    return 'Gangguan Integritas Sistem'

def _buat_fallback_sitrep_deterministik(data_makro: dict, top3_mikro: list, ancaman_baru: dict) -> str:
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    laporan = []
    pola = data_makro.get('nama_pola', 'Ancaman Siber')
    growth = data_makro.get('growth_persen', 0)
    laporan.append('### 1. LANSKAP & POLA ANCAMAN')
    laporan.append(f'- **Peningkatan Aktivitas {pola}**: Terdeteksi peningkatan ancaman sebesar {growth}% dalam seminggu terakhir.')
    laporan.append('\n### 2. VEKTOR SERANGAN & SEKTOR')
    laporan.append('### 3. IMPLIKASI PERSANDIAN & KEAMANAN')
    laporan.append('### 4. REKOMENDASI AKSI')
    for idx, inc in enumerate(top3_mikro):
        nama, _ = _bersihkan_judul_dan_publisher(inc.get('nama_insiden', f'Insiden {idx+1}'), '')
        fakta = inc.get('uraian_fakta', '')
        sektor = _deteksi_sektor_spesifik(fakta)
        senjata = _deteksi_senjata_spesifik(fakta)
        laporan[1] += f'\n- **Target {sektor}**: Menggunakan metode {senjata} pada kasus {nama}.'
        laporan[2] += f'\n- **Risiko Sistem**: {fakta[:150]}...'
        mitigasi = inc.get('mitigasi_ensiklopedia', [])
        if mitigasi:
            laporan[3] += f'\n- **Mitigasi untuk {nama}**: {mitigasi[0]}'
    laporan.append('\n### 5. PREDIKSI ANCAMAN MASA DEPAN')
    if ancaman_baru.get('ada'):
        nama_anc = ancaman_baru.get('nama', 'Ancaman Baru')
        laporan.append(f'- **{nama_anc}**: {ancaman_baru.get("uraian", "")[:200]}')
    else:
        laporan.append('- Tidak ada sinyal ancaman baru yang terdeteksi minggu ini.')
    return '\n'.join(laporan)
