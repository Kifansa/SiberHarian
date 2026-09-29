from src.utils.config_loader import ConfigLoader
from src.utils.settings_manager import SettingsManager
import json
import logging
import re
from typing import Dict, Any, Optional, List, Tuple
from src.utils.llm_adapter import GeminiLLMAdapter

from src.analytics.encyclopedia_lookup import search_encyclopedia, search_encyclopedia_per_incident

logger = logging.getLogger(__name__)

# =====================================================================
# MODULAR SECTION SYSTEM PROMPTS (DIRECT MARKDOWN - NO JSON BRITTLE)
# =====================================================================

# =====================================================================
# MAIN MULTI-AGENT / MODULAR ORCHESTRATOR ENTRY POINT
# =====================================================================


def _call_llm_text(system_prompt: str, user_prompt: str, model: str = None, num_predict: int = 400) -> str:
    return GeminiLLMAdapter.chat(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=num_predict
    )


def _bersihkan_tanggal_jika_ada(teks: str) -> str:
    import re
    teks = re.sub(r'\b(pada tanggal|tanggal|pada)\s+\d{1,2}\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember|jan|feb|mar|apr|mei|jun|jul|agu|sep|okt|nov|des)\s*\d{0,4}\b', '', teks, flags=re.IGNORECASE)
    return teks

def _generate_section_1_makro(data_makro: dict, model: str = None) -> str:
    pola_makro = data_makro.get("nama_pola", "Insiden Terkini")
    korpus = data_makro.get("korpus_artikel", "")
    user_prompt = f"Topik Dominan: {pola_makro}\nFakta Riil:\n{korpus[:1500]}\n\nInstruksi: Sintesis 1 paragraf mengalir sesuai pedoman."
    hasil = _call_llm_text(SettingsManager.get_prompt("section_1_makro"), user_prompt, model, num_predict=ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {}).get("num_predict", {}).get("section_makro", 350))
    if not hasil or len(hasil) < 50:
        return f"Pola ancaman **{pola_makro}** mencatatkan eskalasi minggu ini."
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_2_mikro(top3_mikro: list, model: str = None) -> str:
    if not top3_mikro:
        return "- (Belum ada data insiden aktif minggu ini)"
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    baris_input = []
    for idx, inc in enumerate(top3_mikro):
        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")
        fakta = inc.get("uraian_fakta", "")
        baris_input.append(f"{idx+1}. Kampanye: \"{nama_clean}\" ({inc.get('jumlah_artikel', 1)} laporan berita)\n   Detail: {fakta[:400]}")
    user_prompt = "Sintesiskan TEPAT 3 insiden berikut:\n\n" + "\n\n".join(baris_input)
    hasil = _call_llm_text(SettingsManager.get_prompt("section_2_mikro"), user_prompt, model, num_predict=500)
    if not hasil or len(hasil) < 60:
        return "\n".join(f"- **{inc.get('nama_insiden', '')}**: {inc.get('uraian_fakta', '')[:100]}..." for inc in top3_mikro)
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_3_vektor(top3_mikro: list, model: str = None) -> str:
    if not top3_mikro:
        return "- (Belum ada vektor ancaman aktif yang dilaporkan)"
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    baris_input = []
    for idx, inc in enumerate(top3_mikro):
        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")
        fakta = inc.get("uraian_fakta", "")
        mitre_list = inc.get("mitre_mapping", [])
        if mitre_list:
            top_m = mitre_list[0]
            mitre_ref = f"MITRE ATT&CK [{top_m.get('id', '')}]: {top_m.get('technique', '')} (Taktik: {top_m.get('tactic', '')})"
        else:
            mitre_ref = "MITRE ATT&CK [T1190]: Exploit Public-Facing Application (Taktik: Initial Access)"

        baris_input.append(
            f"{idx+1}. Kampanye: \"{nama_clean}\"\n"
            f"   Rujukan Terverifikasi: {mitre_ref}\n"
            f"   Detail Serangan: {fakta[:350]}"
        )
    user_prompt = (
        "Petakan alur teknis dan taktik MITRE ATT&CK dari insiden berikut.\n"
        "WAJIB sebutkan TEPAT teknik MITRE ATT&CK yang terverifikasi untuk masing-masing kampanye. "
        "DILARANG mengarang kode teknik fiktif:\n\n"
        + "\n\n".join(baris_input)
    )
    hasil = _call_llm_text(SettingsManager.get_prompt("section_3_vektor"), user_prompt, model, num_predict=450)
    if not hasil or len(hasil) < 60:
        fallback_lines = []
        for inc in top3_mikro:
            nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")
            m_list = inc.get("mitre_mapping", [])
            m_tag = f"[{m_list[0]['id']} {m_list[0]['technique']}]" if m_list else "[T1190 Exploit Public-Facing Application]"
            fallback_lines.append(f"- **Alur Serangan {nama_clean}**: Menggunakan taktik dan teknik {m_tag}. Dampak teknis: {inc.get('uraian_fakta', '')[:120]}...")
        return "\n".join(fallback_lines)
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_5_emerging(ancaman_baru: dict, model: str = None) -> str:
    nama_anc = ancaman_baru.get("nama", "Tidak Teridentifikasi")
    uraian_anc = ancaman_baru.get("uraian", "")
    if not ancaman_baru.get("ada"):
        return "Berdasarkan pemantauan korpus intelijen siber Jawa Timur minggu ini, tidak ditemukan sinyal anomali atau ancaman baru."
    user_prompt = f"Ancaman Baru Terdeteksi: {nama_anc}\nDetail Sinyal Ancaman:\n{uraian_anc[:1000]}\n\nInstruksi: Susun 1 paragraf analisis sinyal ancaman."
    hasil = _call_llm_text(SettingsManager.get_prompt("section_5_emerging"), user_prompt, model, num_predict=300)
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
    model: str = None,
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
    if 'celah' in teks or 'rce' in teks or 'vulnerability' in teks or 'exploit' in teks: return 'Eksploitasi Celah Keamanan (RCE)'
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
    laporan.append('### 3. VEKTOR SERANGAN & MITRE ATT&CK')
    laporan.append('### 4. REKOMENDASI AKSI')
    for idx, inc in enumerate(top3_mikro):
        nama, _ = _bersihkan_judul_dan_publisher(inc.get('nama_insiden', f'Insiden {idx+1}'), '')
        fakta = inc.get('uraian_fakta', '')
        sektor = _deteksi_sektor_spesifik(fakta)
        senjata = _deteksi_senjata_spesifik(fakta)
        laporan[1] += f'\n- **Target {sektor}**: Menggunakan metode {senjata} pada kasus {nama}.'
        
        mitre_list = inc.get("mitre_mapping", [])
        if mitre_list:
            m = mitre_list[0]
            laporan[2] += f'\n- **Alur Serangan {nama}**: Terpetakan pada taktik **{m["tactic"]}** via teknik **[{m["id"]}] {m["technique"]}** (keyakinan: {int(m["score"]*100)}%). Dampak: {fakta[:120]}...'
        else:
            laporan[2] += f'\n- **Alur Serangan {nama}**: Terpetakan pada taktik Initial Access via eksploitasi celah web. Dampak: {fakta[:120]}...'

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



