from src.utils.config_loader import ConfigLoader

from src.utils.settings_manager import SettingsManager

import json

import logging

import re

from pathlib import Path

from typing import Dict, Any, Optional, List, Tuple

from src.utils.llm_adapter import GeminiLLMAdapter



from src.analytics.encyclopedia_lookup import search_encyclopedia, search_encyclopedia_per_incident



logger = logging.getLogger(__name__)





def _call_llm_text(system_prompt: str, user_prompt: str, model: str = None, num_predict: int = 450) -> str:

    return GeminiLLMAdapter.chat(

        system_prompt=system_prompt,

        user_prompt=user_prompt,

        max_tokens=num_predict

    )





def _bersihkan_tanggal_jika_ada(teks: str) -> str:

    teks = re.sub(

        r'\b(pada tanggal|tanggal|pada)\s+\d{1,2}\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember|jan|feb|mar|apr|mei|jun|jul|agu|sep|okt|nov|des)\s*\d{0,4}\b',

        '',

        teks,

        flags=re.IGNORECASE

    )

    return teks





def _petakan_taksonomi_insiden(inc: dict) -> Tuple[str, str]:

    """

    Memetakan insiden ke taksonomi resmi eCSIRT (11 kategori tertutup).

    Mengembalikan tuple: (kategori_display, induk_ecsirt).

    """

    from src.cti.preparer import TAXONOMY_DISPLAY_NAMES, ECSIRT_PARENT_MAPPINGS



    # 0. Cek kategori_taksonomi langsung pada objek klaster jika sudah dipetakan

    kat_slug = inc.get("kategori_taksonomi")

    if kat_slug and kat_slug in TAXONOMY_DISPLAY_NAMES and kat_slug != "tidak_dapat_ditentukan":

        return TAXONOMY_DISPLAY_NAMES[kat_slug], ECSIRT_PARENT_MAPPINGS.get(kat_slug, "other:unspecified")



    # 1. Cek apakah ada record di intelijen_berita_tervalidasi

    try:

        from src.storage.db import ambil_intelijen_berita

        for art in inc.get("artikel_list", []):

            ident = art.get("identifier")

            if ident:

                rec = ambil_intelijen_berita(ident)

                if rec and rec.get("kategori_insiden") and rec.get("kategori_insiden") != "Tidak Dapat Ditentukan":

                    kat_name = rec.get("kategori_insiden")

                    for k, v in TAXONOMY_DISPLAY_NAMES.items():

                        if kat_name.lower() in [v.lower(), k.lower()]:

                            return v, ECSIRT_PARENT_MAPPINGS.get(k, "other:unspecified")

                    return kat_name, ECSIRT_PARENT_MAPPINGS.get("akses_tidak_sah", "intrusions:account-compromise")

    except Exception:

        pass



    # 2. Cek pemetaan MITRE ATT&CK jika ada

    m_list = inc.get("mitre_mapping", [])

    if m_list:

        top_tid = str(m_list[0].get("id", "") or "")

        if top_tid.startswith("T1486"):

            return TAXONOMY_DISPLAY_NAMES["ransomware"], ECSIRT_PARENT_MAPPINGS["ransomware"]

        elif top_tid.startswith("T1190"):

            return TAXONOMY_DISPLAY_NAMES["eksploitasi_kerentanan"], ECSIRT_PARENT_MAPPINGS["eksploitasi_kerentanan"]

        elif top_tid.startswith("T1566"):

            return TAXONOMY_DISPLAY_NAMES["phishing_penipuan"], ECSIRT_PARENT_MAPPINGS["phishing_penipuan"]



    # 3. Heuristik pemetaan berbasis teks insiden

    nama = str(inc.get("nama_insiden", "")).lower()

    fakta = str(inc.get("uraian_fakta") or "").lower()

    teks = f"{nama} {fakta}"



    if any(k in teks for k in ["ransomware", "tebusan", "enkripsi file"]):

        k = "ransomware"

    elif any(k in teks for k in ["bocor", "breach", "kebocoran data", "dijual", "basis data", "data sensitif"]):

        k = "data_breach"

    elif any(k in teks for k in ["ddos", "dos", "lumpuh", "ketersediaan", "down"]):

        k = "ddos"

    elif any(k in teks for k in ["deface", "judi", "slot", "web defacement", "halaman depan"]):

        k = "defacement"

    elif any(k in teks for k in ["zero-day", "0-day", "rce", "cve-", "exploit", "kerentanan", "celah keamanan", "celah"]):

        k = "eksploitasi_kerentanan"

    elif any(k in teks for k in ["phishing", "penipuan", "apk", "palsu", "scam", "social engineering"]):

        k = "phishing_penipuan"

    elif any(k in teks for k in ["malware", "trojan", "infostealer", "stealer", "backdoor", "webshell"]):

        k = "malware"

    elif any(k in teks for k in ["akses", "kredensial", "sso", "akun", "login", "password"]):

        k = "akses_tidak_sah"

    else:

        k = "tidak_dapat_ditentukan"



    return TAXONOMY_DISPLAY_NAMES.get(k, "Tidak Dapat Ditentukan"), ECSIRT_PARENT_MAPPINGS.get(k, "other:unspecified")





def _format_distribusi_ecsirt(data_makro: dict = None) -> str:

    """

    Format ringkasan distribusi taksonomi insiden tervalidasi eCSIRT untuk Titik 2 (Bagian 1).

    """

    lines = ["**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:"]

    found_from_db = False

    try:

        from src.storage.db import DEFAULT_DB_PATH, _koneksi

        with _koneksi(DEFAULT_DB_PATH) as conn:

            cursor = conn.execute(

                """

                SELECT kategori_insiden, COUNT(*) as jml

                FROM intelijen_berita_tervalidasi

                WHERE kategori_insiden != 'Tidak Dapat Ditentukan'

                GROUP BY kategori_insiden

                ORDER BY jml DESC

                LIMIT 4

                """

            )

            rows = cursor.fetchall()

            if rows:

                found_from_db = True

                for r in rows:

                    lines.append(f"- **{r[0]}**: {r[1]} laporan berita tervalidasi")

    except Exception:

        pass



    if not found_from_db:

        lines.append("- (Belum ada data distribusi taksonomi tervalidasi pada periode ini)")



    return "\n".join(lines)





def _format_rujukan_mitre(top3_mikro: list) -> str:

    """

    Format rujukan terverifikasi MITRE ATT&CK Enterprise untuk Titik 4 (Bagian 3).

    """

    lines = ["**Rujukan Terverifikasi MITRE ATT&CK Enterprise**:"]

    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher

    seen_techniques = set()

    found_any = False

    for inc in top3_mikro:

        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")

        mitre_list = inc.get("mitre_mapping", [])

        if mitre_list:

            top_m = mitre_list[0]

            tid = top_m.get("id")

            tname = top_m.get("technique")

            ttactic = top_m.get("tactic")

            if tid and tname:

                clean_path = tid.replace(".", "/")

                link = f"https://attack.mitre.org/techniques/{clean_path}/"

                key = (tid, tname)

                if key not in seen_techniques:

                    seen_techniques.add(key)

                    lines.append(f"- **[{tid}] {tname}** (Taktik: {ttactic or 'Initial Access'}) — [{link}]({link})")

                    found_any = True

            elif ttactic:

                key = ("tactic", ttactic)

                if key not in seen_techniques:

                    seen_techniques.add(key)

                    lines.append(f"- Taktik ATT&CK: **{ttactic}** (Teknik spesifik tidak ditentukan)")

                    found_any = True



    if not found_any:

        lines.append("- Alur serangan tidak terpetakan pada teknik spesifik ATT&CK")



    return "\n".join(lines)





def _ambil_kontrol_nist_untuk_insiden(inc: dict, controls_all: list, max_items: int = 2) -> List[dict]:

    """

    Mencari kontrol NIST SP 800-53 Rev 5 / CSF 2.0 yang relevan terhadap karakteristik insiden

    secara dinamis dari data/prepared/nist_controls.json (hanya jika insiden memiliki konteks/teknik).

    """

    if not controls_all:

        return []



    m_list = inc.get("mitre_mapping", [])

    fakta = str(inc.get("uraian_fakta") or "").lower()

    nama = str(inc.get("nama_insiden", "")).lower()

    teks = f"{nama} {fakta}"



    # Jika insiden sama sekali tidak memiliki mitre_mapping dan uraian_fakta kosong, jangan memaksakan kontrol

    if not m_list and not fakta.strip():

        return []



    target_titles = []

    if any(k in teks for k in ["ransomware", "enkripsi", "backup", "tebusan", "T1486"]):

        target_titles.extend(["system backup", "contingency plan", "malicious code protection", "information system backup"])

    if any(k in teks for k in ["celah", "kerentanan", "zero-day", "0-day", "cve", "exploit", "rce", "patch", "T1190"]):

        target_titles.extend(["flaw remediation", "vulnerability monitoring", "boundary protection", "software, firmware, and information integrity"])

    if any(k in teks for k in ["phishing", "penipuan", "kredensial", "akun", "login", "password", "sso", "T1566", "T1078"]):

        target_titles.extend(["identification and authentication", "access enforcement", "account management", "security awareness"])

    if any(k in teks for k in ["ddos", "denial of service", "lumpuh", "trafik"]):

        target_titles.extend(["denial-of-service protection", "boundary protection", "capacity"])

    if any(k in teks for k in ["bocor", "breach", "data", "eksfiltrasi"]):

        target_titles.extend(["transmission confidentiality", "protection of information at rest", "access enforcement", "audit"])

    if any(k in teks for k in ["malware", "trojan", "backdoor", "stealer", "infostealer"]):

        target_titles.extend(["malicious code protection", "system monitoring", "boundary protection", "access enforcement"])



    if not target_titles:

        target_titles = ["access enforcement", "boundary protection", "identification and authentication"]



    matched = []

    seen_ids = set()

    for kw in target_titles:

        for c in controls_all:

            cid = c.get("control_id") or c.get("id")

            ctitle = str(c.get("title", ""))

            if cid and cid not in seen_ids and kw in ctitle.lower():

                seen_ids.add(cid)

                matched.append(c)

                if len(matched) >= max_items:

                    return matched

    return matched





def _format_mitigasi_d3fend_nist(top3_mikro: list) -> Tuple[str, str]:

    """

    Format rekomendasi mitigasi D3FEND deterministik dan NIST untuk Titik 5 (Bagian 4).

    """

    from src.storage.db import ambil_d3fend_mitigasi_by_attack_id

    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher



    d3_lines = ["**Saran Mitigasi Terverifikasi MITRE D3FEND (Lookup Deterministik)**:"]

    seen_d3 = set()

    found_any_d3 = False

    for inc in top3_mikro:

        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")

        m_list = inc.get("mitre_mapping", [])

        tid = m_list[0].get("id") if m_list and m_list[0].get("id") else None

        if tid:

            mitigasi_d3 = ambil_d3fend_mitigasi_by_attack_id(tid)

            if mitigasi_d3:

                for d in mitigasi_d3[:2]:

                    did = d.get("technique_id")

                    dname = d.get("name")

                    dtactic = d.get("tactic")

                    ddef = d.get("definition") or f"Penerapan teknik pertahanan {dname}"

                    if did and did not in seen_d3:

                        seen_d3.add(did)

                        d3_lines.append(f"- **[{did}] {dname}** (Taktik: {dtactic}) untuk mitigasi {tid} pada *{nama_clean}*: {ddef}")

                        found_any_d3 = True



    if not found_any_d3:

        d3_lines.append("- Tidak ditemukan pemetaan mitigasi D3FEND spesifik untuk teknik ini")



    # Referensi NIST SP 800-53 / CSF 2.0

    nist_lines = ["**Referensi Standar NIST Tambahan**:"]

    try:

        nist_prep = Path(__file__).resolve().parents[2] / "data" / "prepared" / "nist_controls.json"

        if nist_prep.exists():

            controls_all = json.loads(nist_prep.read_text(encoding="utf-8"))

            seen_nist = set()

            matched_all = []

            for inc in top3_mikro:

                for c in _ambil_kontrol_nist_untuk_insiden(inc, controls_all, max_items=2):

                    cid = c.get("control_id") or c.get("id")

                    if cid and cid not in seen_nist:

                        seen_nist.add(cid)

                        matched_all.append(c)

            if not matched_all and top3_mikro:

                matched_all = [

                    c for c in controls_all

                    if any(k in c.get("title", "").lower() for k in ["access enforcement", "boundary protection", "identification and authentication"])

                ][:2]

            if matched_all:

                for c in matched_all[:4]:

                    cid = c.get("control_id") or c.get("id")

                    ctitle = c.get("title")

                    cfw = c.get("framework") or "NIST SP 800-53 Rev 5"

                    cstmt = str(c.get("statement") or c.get("description") or "Kontrol mitigasi pertahanan sistem informasi.").strip()

                    if len(cstmt) > 160:

                        cstmt = cstmt[:157] + "..."

                    nist_lines.append(f"- **[{cid}] {ctitle}** ({cfw}): {cstmt}")

            else:

                nist_lines.append("- Referensi kontrol NIST tambahan tidak tersedia")

        else:

            nist_lines.append("- Referensi kontrol NIST tambahan tidak tersedia")

    except Exception:

        nist_lines.append("- Referensi kontrol NIST tambahan tidak tersedia")



    return "\n".join(d3_lines), "\n".join(nist_lines)





def _susun_paragraf_insiden_rag(

    nama_kategori: str,

    fakta_rag: dict,

    jumlah_artikel: int = 0,

    growth_persen: float = 0.0,

    uraian_fallback: str = "",

    is_emerging: bool = False,

    nama_kasus: str = "",

) -> str:

    """

    Menyusun 1 paragraf penjelasan komprehensif berbasis fakta RAG untuk 1 kasus utama

    pada Bagian 1 (INSIDEN MELONJAK DRASTIS dari [ POLA ANCAMAN ]) dan

    Bagian 5 (PREDIKSI TREN ANCAMAN SIBER dari [ SINYAL ANCAMAN BARU ]).

    Mencakup rangkuman kasus utuh: kejadiannya apa, aktor siapa, siapa yang terdampak,

    di mana lokasinya, bagaimana alur insidennya dari awal sampai akhir, dan dampaknya apa.

    """

    if not fakta_rag or (not fakta_rag.get("kejadian") and not fakta_rag.get("nama_kasus")):

        if uraian_fallback:

            label_awalan = "Sinyal ancaman baru" if is_emerging else "Kasus yang melonjak drastis"

            return (

                f"{label_awalan} pada pemantauan minggu ini terfokus pada **{nama_kategori}**. "

                f"{uraian_fallback.strip()}"

            )

        return (

            f"Kasus pada kategori **{nama_kategori}** tercatat mengalami peningkatan aktivitas sebanyak "

            f"{jumlah_artikel} laporan ({growth_persen:+.0f}% dibanding periode sebelumnya) dalam pemantauan minggu ini."

        )



    nama_kasus_utama = nama_kasus or fakta_rag.get("nama_kasus") or fakta_rag.get("kejadian", nama_kategori)

    aktor = fakta_rag.get("aktor", "Pelaku belum teridentifikasi secara spesifik dalam laporan berita")

    terdampak = fakta_rag.get("pihak_terdampak", "entitas sistem terkait")

    lokasi = fakta_rag.get("lokasi_kejadian", "ekosistem digital terkait")

    senjata = fakta_rag.get("senjata_metode", nama_kategori)

    alur = fakta_rag.get("alur_serangan", "")

    dampak = fakta_rag.get("dampak", "gangguan keamanan sistem")



    stat_str = ""

    if jumlah_artikel > 0:

        stat_str = f" dengan {jumlah_artikel} laporan insiden ({growth_persen:+.0f}% vs minggu lalu)"



    if is_emerging:

        pembuka = (

            f"Berdasarkan deteksi **[ SINYAL ANCAMAN BARU ]**, pemantauan minggu ini menyoroti kasus **{nama_kasus_utama}** "

            f"(kategori {nama_kategori}{stat_str})."

        )

    else:

        pembuka = (

            f"Berdasarkan perhitungan **[ POLA ANCAMAN ]**, kasus yang melonjak drastis pada minggu ini adalah "

            f"**{nama_kasus_utama}** (kategori {nama_kategori}{stat_str})."

        )



    paragraf = (

        f"{pembuka} "

        f"Rangkuman kasus ini menunjukkan bahwa aksi penyerangan dilancarkan oleh **{aktor}** yang menyasar **{terdampak}** di lingkup **{lokasi}**. "

        f"Terkait bagaimana kejadian dan alur insidennya berlangsung, penyerang memanfaatkan metode **{senjata}** dengan alur serangan: {alur} "

        f"Insiden ini menimbulkan dampak nyata berupa **{dampak}**."

    )

    return paragraf





def _generate_section_1_makro(data_makro: dict, model: str = None) -> str:

    """

    Bagian 1: INSIDEN MELONJAK DRASTIS.

    Menjelaskan hasil [ POLA ANCAMAN ] secara paragraf mencakup semua data yang didapatkan

    dari berita (kejadiannya apa, aktornya siapa, siapa yang terdampak, kejadiannya bagaimana,

    alur insidennya bagaimana, dan dampaknya apa).

    """

    pola_makro = data_makro.get("nama_pola", "Insiden Terkini")

    korpus = data_makro.get("korpus_artikel", "")

    fakta_rag = data_makro.get("fakta_rag") or {}

    jml_art = int(data_makro.get("jumlah_artikel", 0) or 0)

    growth = float(data_makro.get("growth_persen", 0.0) or 0.0)



    cfg_llm = ((ConfigLoader.get_config() or {}).get("cti_analysis") or {}).get("llm") or {}

    num_pred = (cfg_llm.get("num_predict") or {}).get("section_makro", 450)

    korpus_max = (cfg_llm.get("truncation") or {}).get("korpus_max", 2200)



    user_prompt = (

        f"Hasil [ POLA ANCAMAN ] (Ancaman Melonjak Drastis): {pola_makro} ({jml_art} laporan, pertumbuhan {growth:+.0f}% vs minggu lalu)\n\n"

        f"Data Ekstraksi RAG & Fakta Berita Terkait:\n{korpus[:korpus_max]}\n\n"

        "Instruksi Wajib:\n"

        "Tuliskan penjelasan hasil [ POLA ANCAMAN ] di atas dalam bentuk PARAGRAF mengalir (bukan bullet points). "

        "Paragraf WAJIB menjelaskan seluruh data yang didapatkan dari berita meliputi:\n"

        "1. Kejadiannya apa (insiden/kasus apa saja yang terjadi pada kategori ini),\n"

        "2. Aktornya siapa (pelaku/kelompok peretas yang terlibat berdasarkan berita),\n"

        "3. Siapa yang terdampak (entitas korban dan sektor yang disasar),\n"

        "4. Kejadiannya bagaimana & alur insidennya bagaimana (kronologi cara serangan berlangsung),\n"

        "5. Dampaknya apa bagi pihak yang terdampak.\n"

        "Gunakan murni fakta dari berita di atas tanpa mengarang insiden di luar korpus."

    )

    hasil = _call_llm_text(SettingsManager.get_prompt("section_1_makro"), user_prompt, model, num_predict=num_pred)

    if not hasil or len(hasil) < 50:

        hasil_narasi = _susun_paragraf_insiden_rag(

            nama_kategori=data_makro.get("kategori_display", pola_makro),

            fakta_rag=fakta_rag,

            jumlah_artikel=jml_art,

            growth_persen=growth,

            uraian_fallback=korpus,

            is_emerging=False,

            nama_kasus=data_makro.get("nama_kasus", pola_makro),

        )

    else:

        cleaned = re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

        # Pastikan berbentuk paragraf (jika LLM mengembalikan bullet, gabungkan menjadi paragraf)

        lines = [re.sub(r'^[\*\-•]\s+', '', ln.strip()) for ln in cleaned.splitlines() if ln.strip()]

        hasil_narasi = " ".join(lines)



    return hasil_narasi





def _generate_section_2_mikro(top3_mikro: list, model: str = None) -> str:

    """

    Bagian 2: TREN INSIDEN MINGGUAN.

    Mengambil 3 tren insiden yang paling banyak (di luar yang naik drastis di Bagian 1)

    dan dibuat list. Setiap poin menjelaskan gambaran besar insiden, siapa aktornya,

    siapa yang terdampak, di mana kejadiannya, dan apa dampaknya berdasarkan data RAG dari berita.

    """

    if not top3_mikro:

        return "- (Belum ada data insiden aktif minggu ini)"



    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher

    baris_input = []

    for idx, inc in enumerate(top3_mikro):

        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")

        fakta_rag = inc.get("fakta_rag") or {}

        if fakta_rag and fakta_rag.get("korpus_terstruktur"):

            detail_rag = fakta_rag["korpus_terstruktur"][:750]

        else:

            detail_rag = str(inc.get("uraian_fakta") or "")[:600]

        baris_input.append(

            f"{idx+1}. Nama Tren Insiden: \"{nama_clean}\"\n"

            f"   Ekstraksi Fakta RAG:\n{detail_rag}"

        )



    user_prompt = (

        "Berikut adalah 3 tren insiden siber terbanyak minggu ini (di luar kategori yang melonjak drastis di Bagian 1).\n"

        "Buatlah LIST (3 butir poin menggunakan '- ') untuk ketiga tren insiden berikut.\n"

        "Untuk SETIAP tren insiden, jelaskan secara lengkap berdasarkan data RAG dari berita:\n"

        "1. Gambaran besar insidennya (kejadiannya apa),\n"

        "2. Siapa aktornya (pelaku penyerang),\n"

        "3. Siapa yang terdampak (entitas korban/sektor),\n"

        "4. Di mana kejadiannya (lokasi/lingkup kejadian),\n"

        "5. Apa dampaknya (kerugian/dampak nyata yang dialami korban).\n"

        "Format tiap butir: - **[Nama Tren Insiden]**: [Penjelasan langsung gambaran besar kejadian, pelaku, pihak terdampak, lokasi, dan dampak tanpa mencantumkan jumlah laporan berita atau kata pengantar]\n\n"

        + "\n\n".join(baris_input)

    )

    hasil = _call_llm_text(SettingsManager.get_prompt("section_2_mikro"), user_prompt, model, num_predict=650)

    if not hasil or len(hasil) < 60:

        fallback_items = []

        for inc in top3_mikro:

            nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")

            fakta_rag = inc.get("fakta_rag") or {}

            if fakta_rag and fakta_rag.get("kejadian") not in [None, "-", ""]:

                fallback_items.append(

                    f"- **{nama_clean}**: "

                    f"Penyerangan dilancarkan oleh **{fakta_rag.get('aktor')}** terhadap pihak/sektor terdampak **{fakta_rag.get('pihak_terdampak')}** "

                    f"di lingkup **{fakta_rag.get('lokasi_kejadian')}**. Insiden berlangsung dengan alur serangan: {fakta_rag.get('alur_serangan')}, "

                    f"serta menimbulkan dampak nyata berupa **{fakta_rag.get('dampak')}**."

                )

            else:

                fakta = str(inc.get("uraian_fakta") or "")

                sektor = _deteksi_sektor_spesifik(fakta) or "Umum / Pemerintahan"

                dampak = _deteksi_dampak_spesifik(fakta) or "Gangguan integritas sistem dan keamanan data"

                fallback_items.append(

                    f"- **{nama_clean}** (Sektor Terdampak: {sektor}. Dampak: {dampak}): {fakta[:180]}"

                )

        hasil_narasi = "\n".join(fallback_items)

    else:

        hasil_narasi = re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()



    return hasil_narasi





def _generate_section_3_vektor(top3_mikro: list, model: str = None) -> str:

    """

    Bagian 3: VEKTOR SERANGAN TREN INSIDEN MINGGUAN.

    Dari 3 tren yang sudah dipilih di Bagian 2, menjelaskan bagaimana masing-masing alur

    kejadian insiden yang sedang tren (menggunakan senjata apa, alurnya dari awal sampai akhir bagaimana

    berdasarkan berita), lalu di akhir tiap penjelasan diberikan pemetaan vektor MITRE ATT&CK-nya.

    """

    if not top3_mikro:

        return "- (Belum ada vektor ancaman aktif yang dilaporkan)"



    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher

    baris_input = []

    for idx, inc in enumerate(top3_mikro):

        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")

        fakta_rag = inc.get("fakta_rag") or {}

        senjata_rag = fakta_rag.get("senjata_metode") or _deteksi_senjata_spesifik(str(inc.get("uraian_fakta") or "")) or "Metode tidak dirinci spesifik"

        alur_rag = fakta_rag.get("alur_serangan") or str(inc.get("uraian_fakta") or "")[:450]



        mitre_list = inc.get("mitre_mapping", [])

        if mitre_list and mitre_list[0].get("id") and mitre_list[0].get("technique"):

            top_m = mitre_list[0]

            mitre_ref = f"MITRE ATT&CK [{top_m.get('id', '')}] {top_m.get('technique', '')} (Taktik: {top_m.get('tactic', 'Initial Access')})"

        elif mitre_list and mitre_list[0].get("tactic"):

            top_m = mitre_list[0]

            mitre_ref = f"Taktik MITRE ATT&CK: {top_m.get('tactic', '')} (Teknik spesifik tidak ditentukan)"

        else:

            mitre_ref = "Alur serangan tidak terpetakan pada teknik spesifik ATT&CK"



        baris_input.append(

            f"{idx+1}. Tren Insiden: \"{nama_clean}\"\n"

            f"   Metode: {senjata_rag}\n"

            f"   Kronologi Alur Kejadian dari Awal sampai Akhir (dari Berita): {alur_rag}\n"

            f"   Pemetaan Vektor MITRE ATT&CK (Taruh di Akhir): {mitre_ref}"

        )



    user_prompt = (

        "Untuk masing-masing dari 3 tren insiden mingguan berikut, jelaskan dalam bentuk LIST (3 butir poin '- '):\n"

        "1. Metode apa yang digunakan penyerang berdasarkan berita,\n"

        "2. Bagaimana alur kejadian insidennya dari awal penetrasi, eksekusi, sampai akhir dampaknya berdasarkan fakta berita,\n"

        "3. Di AKHIR penjelasan masing-masing tren, cantumkan Pemetaan Vektor MITRE ATT&CK yang telah diverifikasi (jangan mengarang kode teknik di luar yang diberikan).\n\n"

        + "\n\n".join(baris_input)

    )

    hasil = _call_llm_text(SettingsManager.get_prompt("section_3_vektor"), user_prompt, model, num_predict=600)

    if not hasil or len(hasil) < 60:

        fallback_lines = []

        for inc in top3_mikro:

            nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")

            fakta_rag = inc.get("fakta_rag") or {}

            senjata_rag = fakta_rag.get("senjata_metode") or _deteksi_senjata_spesifik(str(inc.get("uraian_fakta") or ""))

            alur_rag = fakta_rag.get("alur_serangan") or str(inc.get("uraian_fakta") or "")[:220]

            senjata_clause = f"Serangan ini menggunakan metode **{senjata_rag}**. " if senjata_rag else ""



            m_list = inc.get("mitre_mapping", [])

            if m_list and m_list[0].get("id") and m_list[0].get("technique"):

                m_tag = f"**[{m_list[0]['id']}] {m_list[0]['technique']}** (Taktik: **{m_list[0].get('tactic', 'Initial Access')}**)"

                mitre_tail = f"Pemetaan Vektor MITRE ATT&CK: {m_tag}."

            elif m_list and m_list[0].get("tactic"):

                mitre_tail = f"Pemetaan Vektor MITRE ATT&CK: Taktik ATT&CK **{m_list[0]['tactic']}** (teknik spesifik tidak ditentukan)."

            else:

                mitre_tail = "Alur serangan tidak terpetakan pada teknik spesifik ATT&CK."



            fallback_lines.append(

                f"- **{nama_clean}**: {senjata_clause}"

                f"Alur kejadian dari awal hingga akhir: {alur_rag} "

                f"{mitre_tail}"

            )

        hasil_narasi = "\n".join(fallback_lines)

    else:

        hasil_narasi = re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()



    return hasil_narasi





def _generate_section_4_rekomendasi(top3_mikro: list) -> str:

    """

    Bagian 4: REKOMENDASI AKSI.

    Di setiap tren dari 3 tren insiden mingguan, diberikan rekomendasi aksi yang bisa dilakukan

    untuk mencegah atau mengatasi tren insidennya berdasarkan MITRE D3FEND (lookup deterministik)

    dan NIST SP 800-53 / CSF 2.0.

    Tetap mematuhi Opsi A: jika insiden kosong tanpa pemetaan teknik & tanpa mitigasi_ensiklopedia,

    tidak menyuntikkan kode statis D3-MFA / AC-2 / PR.AC-1.

    """

    if not top3_mikro:

        return "- (Belum ada rekomendasi aksi untuk periode ini)"



    from src.storage.db import ambil_d3fend_mitigasi_by_attack_id

    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher



    controls_all = []

    try:

        nist_prep = Path(__file__).resolve().parents[2] / "data" / "prepared" / "nist_controls.json"

        if nist_prep.exists():

            controls_all = json.loads(nist_prep.read_text(encoding="utf-8"))

    except Exception:

        controls_all = []



    poin_rekomendasi = []

    for idx, inc in enumerate(top3_mikro):

        nama_raw = inc.get("nama_insiden", f"Insiden Siber {idx+1}")

        nama, _ = _bersihkan_judul_dan_publisher(nama_raw, "")



        # 1. Cek mitigasi_ensiklopedia yang valid (bebas BSSN/KAMI/CSIRT/CIS/OWASP/ISO)

        mitigasi = inc.get("mitigasi_ensiklopedia", [])

        mitigasi_valid = [

            m for m in mitigasi

            if not any(tag in m for tag in ["[BSSN", "[KAMI", "[CSIRT", "[SPBE", "[CIS", "[OWASP", "[ISO"])

        ]



        # 2. Lookup deterministik MITRE D3FEND untuk teknik ATT&CK tren ini

        m_list = inc.get("mitre_mapping", [])

        tid = m_list[0].get("id") if m_list and m_list[0].get("id") else None

        tname = m_list[0].get("technique") if m_list and m_list[0].get("technique") else ""

        d3_items = ambil_d3fend_mitigasi_by_attack_id(tid) if tid else []



        # 3. Ambil kontrol NIST relevan jika tren memiliki konteks/pemetaan

        nist_items = _ambil_kontrol_nist_untuk_insiden(inc, controls_all, max_items=2) if (tid or inc.get("fakta_rag")) else []



        butir_tren = []

        if d3_items:

            for d in d3_items[:2]:

                did = d.get("technique_id")

                dname = d.get("name")

                dtactic = d.get("tactic")

                ddef = (d.get("definition") or f"Penerapan teknik pertahanan {dname}").strip()

                butir_tren.append(

                    f"- **Mitigasi Teknis MITRE D3FEND [{did}] {dname}** (Taktik: {dtactic}): "

                    f"Untuk mencegah dan mengatasi alur serangan {tid} ({tname}), terapkan langkah pertahanan: {ddef}"

                )



        if nist_items:

            for c in nist_items[:2]:

                cid = c.get("control_id") or c.get("id")

                ctitle = c.get("title")

                cfw = c.get("framework") or "NIST SP 800-53 Rev 5"

                cstmt = str(c.get("statement") or c.get("description") or "Penerapan kontrol keamanan standar.").strip()

                if len(cstmt) > 180:

                    cstmt = cstmt[:177] + "..."

                butir_tren.append(

                    f"- **Kontrol Keamanan NIST [{cid}] {ctitle}** ({cfw}): "

                    f"Langkah tata kelola & pencegahan tren insiden ini: {cstmt}"

                )



        if mitigasi_valid:

            for mv in mitigasi_valid[:2]:

                if mv not in "\n".join(butir_tren):

                    butir_tren.append(f"- {mv}")



        if not butir_tren:

            butir_tren.append("- Referensi kontrol NIST tambahan tidak tersedia")



        poin_rekomendasi.append(

            f"**Rekomendasi Aksi untuk {nama}**\n" + "\n".join(butir_tren)

        )



    return "\n\n".join(poin_rekomendasi)















def _generate_section_5_emerging(ancaman_baru: dict, model: str = None) -> str:

    """

    Bagian 5: PREDIKSI TREN ANCAMAN SIBER.

    Dibuat paragraf penjelasan dengan struktur yang sama persis dengan INSIDEN MELONJAK DRASTIS

    (kejadiannya apa, aktornya siapa, siapa yang terdampak, kejadiannya bagaimana, alur insidennya

    bagaimana, dan dampaknya apa), tetapi mengambil insiden dari [ SINYAL ANCAMAN BARU ].

    """

    if not ancaman_baru or not ancaman_baru.get("ada"):

        return (

            "Berdasarkan pemantauan **[ SINYAL ANCAMAN BARU ]** pada korpus berita minggu ini, kondisi lanskap ancaman "

            "berada pada status **Kondisi Stabil** karena belum ditemukan kategori serangan baru yang melampaui ambang "

            "batas minimal dua kasus terkonfirmasi maupun lonjakan anomali baru di luar pola tren reguler."

        )



    nama_anc = ancaman_baru.get("nama", "Ancaman Baru")

    uraian_anc = ancaman_baru.get("uraian", "")

    korpus_anc = ancaman_baru.get("korpus_artikel", "") or uraian_anc

    fakta_rag = ancaman_baru.get("fakta_rag") or {}

    jml_kasus = int(ancaman_baru.get("jumlah_kasus", 0) or 0)

    growth_anc = float(ancaman_baru.get("growth_persen", 0.0) or 0.0)



    user_prompt = (

        f"Hasil [ SINYAL ANCAMAN BARU ]: {nama_anc} ({jml_kasus} kasus terkonfirmasi minggu ini, pertumbuhan {growth_anc:+.0f}%)\n\n"

        f"Data Ekstraksi RAG & Fakta Berita Terkait:\n{korpus_anc[:2000]}\n\n"

        "Instruksi Wajib:\n"

        "Tuliskan penjelasan hasil [ SINYAL ANCAMAN BARU ] di atas dalam bentuk PARAGRAF mengalir (bukan bullet points) "

        "dengan struktur yang SAMA PERSIS seperti bagian INSIDEN MELONJAK DRASTIS, yaitu menjelaskan seluruh data dari berita meliputi:\n"

        "1. Kejadiannya apa (insiden/kasus baru apa saja yang terdeteksi pada kategori ini),\n"

        "2. Aktornya siapa (pelaku/kelompok peretas yang terlibat berdasarkan berita),\n"

        "3. Siapa yang terdampak (entitas korban dan sektor yang disasar),\n"

        "4. Kejadiannya bagaimana & alur insidennya bagaimana (kronologi cara serangan berlangsung),\n"

        "5. Dampaknya apa bagi pihak yang terdampak.\n"

        "Gunakan murni fakta dari berita di atas tanpa mengarang insiden di luar korpus."

    )

    hasil = _call_llm_text(SettingsManager.get_prompt("section_5_emerging"), user_prompt, model, num_predict=420)

    if not hasil or len(hasil) < 50:

        return _susun_paragraf_insiden_rag(

            nama_kategori=nama_anc,

            fakta_rag=fakta_rag,

            jumlah_artikel=jml_kasus,

            growth_persen=growth_anc,

            uraian_fallback=uraian_anc,

            is_emerging=True,

            nama_kasus=ancaman_baru.get("nama_kasus", ""),

        )



    cleaned = re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

    lines = [re.sub(r'^[\*\-•]\s+', '', ln.strip()) for ln in cleaned.splitlines() if ln.strip()]

    return " ".join(lines)





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

    - Mode 'modular_llm': Mengenerate narasi per-section secara modular & terisolasi menggunakan Google Gemini Modular LLM.

    """

    if mode == "instant_rag":

        logger.info("Menjalankan CTI Pipeline Mode INSTANT RAG (Super Cepat < 1s)...")

        laporan = _buat_fallback_sitrep_deterministik(data_makro, top3_mikro, ancaman_baru)

        return laporan, {"mode": "instant_rag"}



    logger.info("Menjalankan CTI Pipeline Mode MODULAR LLM (Section-by-Section Google Gemini Modular LLM)...")



    logger.info("[CTI Modul 1/5] Menghasilkan Bagian 1: Insiden Melonjak Drastis ([ POLA ANCAMAN ])...")

    sec1 = _generate_section_1_makro(data_makro, model=model)



    logger.info("[CTI Modul 2/5] Menghasilkan Bagian 2: Tren Insiden Mingguan (Top 3 di luar Pola Ancaman)...")

    sec2 = _generate_section_2_mikro(top3_mikro, model=model)



    logger.info("[CTI Modul 3/5] Menghasilkan Bagian 3: Vektor Serangan Tren Insiden Mingguan + MITRE ATT&CK...")

    sec3 = _generate_section_3_vektor(top3_mikro, model=model)



    logger.info("[CTI Modul 4/5] Menghasilkan Bagian 4: Rekomendasi Aksi per Tren berbasis MITRE D3FEND & NIST...")

    sec4 = _generate_section_4_rekomendasi(top3_mikro)



    logger.info("[CTI Modul 5/5] Menghasilkan Bagian 5: Prediksi Tren Ancaman Siber ([ SINYAL ANCAMAN BARU ])...")

    sec5 = _generate_section_5_emerging(ancaman_baru, model=model)



    laporan_final = (

        f"### 1. INSIDEN MELONJAK DRASTIS\n{sec1}\n\n"

        f"### 2. TREN INSIDEN MINGGUAN\n{sec2}\n\n"

        f"### 3. VEKTOR SERANGAN TREN INSIDEN MINGGUAN\n{sec3}\n\n"

        f"### 4. REKOMENDASI AKSI\n{sec4}\n\n"

        f"### 5. PREDIKSI TREN ANCAMAN SIBER\n{sec5}"

    )



    logger.info("SITREP CTI 5-Bagian berhasil disusun secara modular!")

    return laporan_final, {"mode": "modular_llm"}





def _deteksi_sektor_spesifik(teks: str) -> Optional[str]:

    if not teks or not isinstance(teks, str):

        return None

    teks = teks.lower()

    if any(k in teks for k in ['pemerintah', 'pemprov', 'pemkab', 'pemkot', 'dinas', 'kementerian', 'instansi']): return 'Sektor Administrasi Pemerintahan'

    if any(k in teks for k in ['sekolah', 'kampus', 'universitas', 'akademik']): return 'Sektor Pendidikan'

    if any(k in teks for k in ['rumah sakit', 'rsud', 'puskesmas', 'medis', 'kesehatan']): return 'Sektor Kesehatan'

    if any(k in teks for k in ['bank', 'keuangan', 'finansial', 'perbankan']): return 'Sektor Keuangan'

    if any(k in teks for k in ['transportasi', 'bandara', 'pelabuhan', 'kereta']): return 'Sektor Transportasi'

    if any(k in teks for k in ['energi', 'listrik', 'pln', 'migas', 'pertamina']): return 'Sektor Energi dan Sumber Daya Mineral'

    return None





def _deteksi_senjata_spesifik(teks: str) -> Optional[str]:

    if not teks or not isinstance(teks, str):

        return None

    teks = teks.lower()

    if 'ransomware' in teks or 'enkripsi file' in teks or 'tebusan' in teks: return 'Ransomware / File Encryptor'

    if 'phishing' in teks or 'social engineering' in teks or 'email tiruan' in teks: return 'Phishing / Social Engineering'

    if 'apk' in teks or 'undangan pernikahan' in teks or 'surat tilang' in teks: return 'Malware APK'

    if 'deface' in teks or 'judi' in teks or 'slot' in teks: return 'Webshell & Defacement'

    if 'celah' in teks or 'rce' in teks or 'vulnerability' in teks or 'exploit' in teks or 'zero-day' in teks or '0-day' in teks: return 'Eksploitasi Celah Keamanan (Exploit / RCE)'

    if 'infostealer' in teks or 'trojan' in teks or 'stealer' in teks: return 'Infostealer / Malware Pencuri Kredensial'

    if 'ddos' in teks or 'dos' in teks: return 'Distributed Denial of Service (DDoS)'

    return None





def _deteksi_dampak_spesifik(teks: str) -> Optional[str]:

    if not teks or not isinstance(teks, str):

        return None

    teks = teks.lower()

    if 'bocor' in teks or 'breach' in teks or 'dijual' in teks or 'kebocoran data' in teks: return 'Kebocoran Data Sensitif'

    if 'lumpuh' in teks or 'down' in teks or 'tidak dapat diakses' in teks: return 'Kelumpuhan Layanan Publik'

    if 'enkripsi' in teks or 'terkunci' in teks: return 'Terkuncinya Basis Data Operasional'

    return None





def _buat_fallback_sitrep_deterministik(data_makro: dict, top3_mikro: list, ancaman_baru: dict) -> str:

    """

    Menyusun laporan SITREP 5 bagian secara deterministik berbasis fakta RAG penuh:

    1. INSIDEN MELONJAK DRASTIS: Paragraf penjelasan [ POLA ANCAMAN ] (kejadian, aktor, siapa terdampak, bagaimana kejadian & alurnya, dampak).

    2. TREN INSIDEN MINGGUAN: List 3 tren terbanyak (di luar yang naik drastis) beserta gambaran besar, aktor, siapa terdampak, di mana kejadiannya, dan dampak.

    3. VEKTOR SERANGAN TREN INSIDEN MINGGUAN: List alur serangan 3 tren dari awal sampai akhir + senjata, diakhiri pemetaan MITRE ATT&CK.

    4. REKOMENDASI AKSI: Rekomendasi per tren berdasarkan MITRE D3FEND dan NIST.

    5. PREDIKSI TREN ANCAMAN SIBER: Paragraf penjelasan [ SINYAL ANCAMAN BARU ] dengan struktur yang sama seperti Bagian 1.

    """

    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher



    pola = data_makro.get("nama_pola", "Ancaman Siber")

    growth = float(data_makro.get("growth_persen", 0) or 0)

    jml_art = int(data_makro.get("jumlah_artikel", 0) or 0)

    fakta_makro = data_makro.get("fakta_rag") or {}

    korpus_makro = data_makro.get("korpus_artikel", "")



    # Bagian 1: Paragraf penjelasan [ POLA ANCAMAN ] untuk 1 kasus utama yang melonjak drastis

    nama_kasus_makro = data_makro.get("nama_kasus", pola)

    paragraf_sec1 = _susun_paragraf_insiden_rag(

        nama_kategori=data_makro.get("kategori_display", pola),

        fakta_rag=fakta_makro,

        jumlah_artikel=jml_art,

        growth_persen=growth,

        uraian_fallback=korpus_makro,

        is_emerging=False,

        nama_kasus=nama_kasus_makro,

    )

    sec1_full = paragraf_sec1



    # Bagian 2 & 3: List 3 Tren Insiden Mingguan & Vektor Serangannya (1 Kasus per List)

    if not top3_mikro:

        sec2_full = "- (Belum ada data insiden aktif minggu ini)"

        sec3_full = "- (Belum ada vektor ancaman aktif yang dilaporkan)"

        sec4_full = "- (Belum ada rekomendasi aksi untuk periode ini)"

    else:

        sec2_lines = []

        sec3_lines = []



        for idx, inc in enumerate(top3_mikro):

            nama, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", f"Insiden {idx+1}"), "")

            fakta = str(inc.get("uraian_fakta") or "").strip()

            fakta_rag = inc.get("fakta_rag") or {}



            if fakta_rag and (fakta_rag.get("kejadian") or fakta_rag.get("nama_kasus")):

                sec2_lines.append(

                    f"- **{nama}**: "

                    f"Penyerangan dilancarkan oleh **{fakta_rag.get('aktor')}** terhadap pihak/sektor terdampak **{fakta_rag.get('pihak_terdampak')}** "

                    f"di lingkup **{fakta_rag.get('lokasi_kejadian')}**. Insiden berlangsung dengan alur serangan: {fakta_rag.get('alur_serangan')}, "

                    f"serta menimbulkan dampak nyata berupa **{fakta_rag.get('dampak')}**."

                )

            else:

                sektor = _deteksi_sektor_spesifik(fakta) or "Umum / Pemerintahan"

                senjata = _deteksi_senjata_spesifik(fakta)

                dampak = _deteksi_dampak_spesifik(fakta) or "Gangguan integritas sistem dan potensi kebocoran data"

                fakta_deskripsi = fakta[:220] if fakta else "Insiden tercatat dalam pemantauan korpus mingguan."

                tag_sektor = f"Sektor Terdampak: {sektor}. "

                tag_senjata = f" [Metode: {senjata}]" if senjata else ""

                tag_dampak = f" [Dampak: {dampak}]"

                sec2_lines.append(f"- **{nama}** ({tag_sektor}{tag_dampak}{tag_senjata}): {fakta_deskripsi}")



            # Bagian 3: Senjata & Alur dari awal sampai akhir, diakhiri pemetaan MITRE ATT&CK

            senjata_v = fakta_rag.get("senjata_metode") or _deteksi_senjata_spesifik(fakta)

            alur_v = fakta_rag.get("alur_serangan") or (fakta[:220] if fakta else "Rincian teknis tidak dirinci dalam laporan.")

            senjata_clause = f"Menggunakan metode **{senjata_v}**. " if senjata_v else ""



            mitre_list = inc.get("mitre_mapping", [])

            if mitre_list and mitre_list[0].get("id") and mitre_list[0].get("technique"):

                m = mitre_list[0]



                mitre_ending = f"Pemetaan Vektor MITRE ATT&CK: Taktik **{m.get('tactic', 'Initial Access')}** via teknik **[{m.get('id')}] {m.get('technique')}**."

            elif mitre_list and mitre_list[0].get("tactic"):

                m = mitre_list[0]

                mitre_ending = f"Pemetaan Vektor MITRE ATT&CK: Taktik ATT&CK **{m.get('tactic')}** (teknik spesifik tidak ditentukan)."

            else:

                mitre_ending = "Alur serangan tidak terpetakan pada teknik spesifik ATT&CK."



            sec3_lines.append(

                f"- **{nama}**: {senjata_clause}"

                f"Alur kejadian dari awal hingga akhir: {alur_v} "

                f"{mitre_ending}"

            )



        sec2_full = "\n".join(sec2_lines)

        sec3_full = "\n".join(sec3_lines)

        sec4_full = _generate_section_4_rekomendasi(top3_mikro)



    # Bagian 5: Paragraf penjelasan [ SINYAL ANCAMAN BARU ] dengan struktur sama seperti Bagian 1

    if ancaman_baru and ancaman_baru.get("ada"):

        nama_anc = ancaman_baru.get("nama", "Ancaman Baru")

        fakta_anc = ancaman_baru.get("fakta_rag") or {}

        jml_anc = int(ancaman_baru.get("jumlah_kasus", 0) or 0)

        growth_anc = float(ancaman_baru.get("growth_persen", 0.0) or 0.0)

        uraian_anc = ancaman_baru.get("uraian", "")

        sec5_full = _susun_paragraf_insiden_rag(

            nama_kategori=nama_anc,

            fakta_rag=fakta_anc,

            jumlah_artikel=jml_anc,

            growth_persen=growth_anc,

            uraian_fallback=uraian_anc,

            is_emerging=True,

            nama_kasus=ancaman_baru.get("nama_kasus", ""),

        )

    else:

        sec5_full = (

            "Berdasarkan pemantauan **[ SINYAL ANCAMAN BARU ]** pada korpus berita minggu ini, kondisi lanskap ancaman "

            "berada pada status **Kondisi Stabil** dan tidak ada sinyal ancaman baru yang terdeteksi mencapai ambang "

            "batas minimal dua kasus terkonfirmasi."

        )



    return (

        f"### 1. INSIDEN MELONJAK DRASTIS\n{sec1_full}\n\n"

        f"### 2. TREN INSIDEN MINGGUAN\n{sec2_full}\n\n"

        f"### 3. VEKTOR SERANGAN TREN INSIDEN MINGGUAN\n{sec3_full}\n\n"

        f"### 4. REKOMENDASI AKSI\n{sec4_full}\n\n"

        f"### 5. PREDIKSI TREN ANCAMAN SIBER\n{sec5_full}"

    )

