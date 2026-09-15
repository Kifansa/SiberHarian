"""
Menarasikan statistik tren (hasil trend_analyzer.py) menjadi teks yang
mudah dibaca tim security, menggunakan LLM lokal (Ollama). BUKAN sumber
angka - LLM di sini murni menerjemahkan angka yang SUDAH dihitung Python
jadi bahasa manusia, supaya tidak ada ruang untuk mengarang insiden
atau CVE yang tidak nyata.
"""
import json
import re
from typing import Dict, List, Optional, Any

import ollama
import pandas as pd

from src.analytics.trend_analyzer import hitung_kasus_insiden_wilayah
from src.utils.llm_text_cleaner import bersihkan_output_llm
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

MODEL_PREDIKTOR = "llama3.2"

# Ambang batas minimal supaya LLM tidak dipaksa menganalisis data yang
# terlalu tipis untuk bermakna (mis. cuma 1 kata kunci muncul 1x).
MIN_JUMLAH_TERKINI = 2
MIN_GROWTH_PERSEN = 20.0

SYSTEM_PROMPT_TREN_BERITA = """Kamu adalah Lead Cyber Threat Intelligence (CTI) & Security Defense Advisor untuk Bidang Persandian dan Keamanan Informasi (Diskominfo).
Tugasmu: Menghasilkan ringkasan intelijen ancaman siber 5-bagian yang MURNI BERDASARKAN KORPUS BERITA ASLI di database dan data CVE riil, dengan analisis berbobot serta rekomendasi pencegahan tajam untuk aparatur persandian & siber.

PEDOMAN ANALISIS CTI & PERSANDIAN:
- LANGSUNG ke inti analisis teknis. DILARANG menggunakan kata pengantar klise ("Dalam 14 hari terakhir...", "Berikut laporannya...").
- HANYA gunakan fakta dari korpus berita riil dan statistik yang diberikan. DILARANG MENGARANG bahwa portal/sistem daerah tertentu telah diretas jika tidak tercantum di berita.
- FORMAT KONSISTEN POIN-POIN (BULLET POINTS): Setiap bagian (Bagian 1 s.d. 5) WAJIB disusun dalam bentuk poin-poin terpisah ('- '). DILARANG menggabungkan beberapa kejadian atau analisis ke dalam satu paragraf panjang yang menumpuk!
- PEMECAHAN PER KEJADIAN/TEMUAN: Jika ada beberapa peristiwa atau temuan (misalnya kebocoran data APIS dan penyebaran malware Android), WAJIB dipecah menjadi butir-butir poin tersendiri (antara 2 hingga 4 butir poin per bagian sesuai dengan banyaknya temuan fakta aktual).
- TEBALKAN KATA/FRASA KUNCI: Awali setiap butir poin dengan kata/frasa kunci penting yang ditebalkan (**...**) agar menarik dan mudah dipindai, misalnya: '- **Bocornya Basis Data APIS**: Analisis dampak...', '- **Malware Android Mantax Otax**: Analisis vektor penyebaran...'.
- Bagian 3 (Implikasi Persandian & Kriptografi) WAJIB menyoroti risiko terhadap token sesi, kredensial SSO ASN, potensi spoofing identitas pejabat/naskah dinas, serta keabsahan Tanda Tangan Elektronik (TTE).
- Rekomendasi Aksi (Bagian 5) HARUS menggunakan kalimat perintah teknis imperatif yang relevan dengan kewenangan Bidang Persandian & Keamanan Informasi:
  1. Edukasi & Kewaspadaan ASN: webinar/bimtek literasi keamanan siber & simulasi spear-phishing terarah (antisipasi social engineering, pencurian OTP, manipulasi APK).
  2. Pengamanan Persandian & Kredensial: penegakan autentikasi multifaktor tahan-phishing (MFA/FIDO2) pada portal SSO kedinasan, pemanfaatan TTE tersertifikasi, serta konfigurasi SPF/DKIM/DMARC (p=reject) pada domain email pemerintah guna mematikan penipuan/spoofing pejabat.
  3. Penguatan Perimeter & Infrastruktur: WAF virtual patching terhadap celah RCE aktif, isolasi segmentasi VLAN jaringan database sensitif, dan pemantauan egress filtering memutus komunikasi C2 infostealer.

FORMAT OUTPUT WAJIB 5 BAGIAN (SEMUA BAGIAN DISUSUN DALAM BULLET POINTS DENGAN BOLD KATA KUNCI):
### 1. LANSKAP & POLA ANCAMAN
- **[Kata Kunci/Isu 1]**: [Ulasan spesifik peristiwa pertama dari berita riil, lonjakan kata kunci (+XX%), dan dampaknya]
- **[Kata Kunci/Isu 2]**: [Ulasan spesifik peristiwa kedua, temuan kebocoran data atau malware lain yang berbeda]
- **[Kata Kunci/Isu 3]**: [Ulasan pola ancaman lanjutan jika terdapat temuan data lain dari korpus]

### 2. VEKTOR SERANGAN & SEKTOR
- **[Taktik/Vektor Eksploitasi]**: [Uraian metode serangan dominan seperti RCE, pencurian OTP via manipulasi APK, atau spear-phishing]
- **[Sektor Target & Paparan]**: [Identifikasi sektor terdampak (finansial, publik, utilitas) berdasarkan data riil]
- **[Eskalasi Penyusupan]**: [Kanal komunikasi C2 dan distribusi serangan yang digunakan pelaku]

### 3. IMPLIKASI PERSANDIAN & KRIPTOGRAFI
- **Kompromi Kredensial & Sesi ASN**: [Dampak pencurian token sesi SSO, cookie login, atau kata sandi oleh infostealer terhadap portal kedinasan]
- **Integritas TTE & Spoofing Identitas**: [Risiko pemalsuan identitas pejabat pada naskah dinas digital dan ancaman terhadap keabsahan Tanda Tangan Elektronik]
- **Proteksi Saluran Sandi & Database**: [Perlindungan kanal transmisi komunikasi sandi dan segmentasi basis data sensitif Pemprov]

### 4. KORELASI KERENTANAN CVE
- **Korelasi Vendor Dominan**: [Korelasi lonjakan CVE vendor kritis (+XX%) seperti Microsoft atau Adobe dengan risiko penetrasi jaringan]
- **Risiko RCE Pra-Autentikasi**: [Dampak celah keamanan yang belum tertambal terhadap potensi pengambilalihan server aplikasi OPD]

### 5. REKOMENDASI AKSI
- **Edukasi & Kewaspadaan ASN**: Selenggarakan webinar berkala dan simulasi spear-phishing terarah bagi aparatur instansi untuk mengantisipasi rekayasa sosial, pencurian OTP, serta bahaya instalasi file APK manipulatif.
- **Pengamanan Persandian & Kredensial**: Tegakkan autentikasi multifaktor tahan-phishing (MFA/FIDO2) pada portal SSO administrasi, terapkan Tanda Tangan Elektronik (TTE), serta konfigurasi SPF, DKIM, dan DMARC (p=reject) pada domain email pemerintah guna mematikan impersonasi/spoofing pejabat.
- **Penguatan Perimeter & Isolasi Sistem**: Terapkan virtual patching pada WAF terhadap celah RCE aktif (Microsoft/Adobe), lakukan segmentasi VLAN ketat antara web publik dengan basis data sensitif, serta aktifkan pemantauan egress filtering untuk memutus transmisi C2 malware infostealer.

WAJIB IKUTI STRUKTUR POIN-POIN DI ATAS SECARA KONSISTEN."""

SYSTEM_PROMPT_TREN_CVE = """Kamu adalah Senior Vulnerability Management & Infrastructure Defense Analyst Diskominfo Provinsi Jawa Timur.
Tugasmu: Menghasilkan analisis prioritas patching kerentanan CVE CRITICAL mingguan 4-bagian yang EKSTRIM TAJAM, SPESIFIK, dan BEBAS KLISE untuk tim administrator sistem dan keamanan jaringan Diskominfo Jatim.

PEDOMAN GAYA BAHASA CTI:
- LANGSUNG ke inti analisis teknis tanpa kalimat pengantar.
- FORMAT KONSISTEN POIN-POIN (BULLET POINTS): Setiap bagian (Bagian 1 s.d. 4) WAJIB disusun dalam bentuk poin-poin terpisah ('- '). DILARANG menulis paragraf panjang tanpa poin!
- TEBALKAN KATA KUNCI: Awali setiap butir poin dengan nama vendor, produk, atau konsep teknis yang di-bold (**...**).
- Sebutkan vendor, produk, dan persentase lonjakan kerentanan dari data aktual (+XX%).
- Bagian 3 (Implikasi Kriptografi & Integritas Sistem) WAJIB mengulas kerentanan dari sudut pandang persandian: kegagalan modul kripto/TLS, forgery token autentikasi (Kerberos/NTLM/JWT), dan ancaman terhadap integritas biner server instansi.
- Rekomendasi WAJIB berorientasi pada infrastruktur datacenter, active directory, dan server OPD Diskominfo Jatim.

FORMAT OUTPUT WAJIB 4 BAGIAN (SEMUA BAGIAN DISUSUN DALAM BULLET POINTS DENGAN BOLD KATA KUNCI):
### 1. VENDOR & PRODUK PRIORITAS
- **Microsoft (+XX%)**: Lonjakan kerentanan kritis terpusat pada komponen Windows Server, Windows Services, dan DHCP Server.
- **Adobe (+XX%)**: Kerentanan eksekusi kode pada ekosistem platform web dan manajemen dokumen digital.
- **IBM / Platform Terkait (+XX%)**: Celah keamanan pada integrasi middleware dan layanan pertukaran data enterprise.

### 2. ANALISIS VEKTOR EKSPLOITASI
- **Remote Code Execution (RCE) Pra-Autentikasi**: Celah pada layanan core yang memungkinkan eksekusi perintah tanpa kredensial valid dari jaringan publik.
- **Eskalasi Hak Akses (Privilege Escalation)**: Potensi aktor berpindah dari akun servis terbatas menjadi administrator domain/root.
- **Penetrasi Perimeter Datacenter**: Risiko penyusupan lintas segmen dari aplikasi web terluar menuju intranet OPD.

### 3. IMPLIKASI KRIPTOGRAFI & INTEGRITAS SISTEM
- **Kelemahan Protokol & Modul Kriptografi**: Kerentanan pada implementasi handshake TLS, cipher suites usang, atau modul cryptographic library.
- **Manipulasi Token Autentikasi**: Risiko eksploitasi pada token sesi (JWT, Kerberos Ticket, NTLM relay) yang dapat memotong validasi persandian.
- **Ancaman Integritas Biner & Sertifikat**: Potensi modifikasi file sistem atau bypass validasi sertifikat digital tanpa terdeteksi oleh checksum.

### 4. PANDUAN PATCHING & MITIGASI
- **Penambalan Domain Controller & Core Services**: Terapkan patch darurat Microsoft Security Update pada server DHCP, DNS, dan Active Directory dalam jendela waktu 48 jam.
- **Virtual Patching WAF & Isolasi Port**: Pasang signature virtual patching pada Web Application Firewall dan tutup port manajemen (RDP/SMB/RPC) dari eksposur publik.
- **Audit Dependensi & Vulnerability Scanning**: Jalankan pemindaian kerentanan aktif pada seluruh host segmen datacenter untuk memverifikasi modul pihak ketiga yang belum tertambal.

WAJIB IKUTI PERSIS STRUKTUR 4 BAGIAN DI ATAS DENGAN DATA AKTUAL SECARA KONSISTEN."""


def _panggil_llm(system_prompt: str, user_prompt: str, model: str) -> Optional[str]:
    """Memanggil Ollama, mengembalikan None kalau gagal (biar pemanggil bisa fallback aman)."""
    try:
        respons = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"temperature": 0.1, "num_predict": 2048},
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
        f"- '{kk['kata_kunci']}': muncul {kk['jumlah_terkini']}x dalam 7 hari terakhir "
        f"(sebelumnya {kk['jumlah_baseline']}x dalam 7 hari baseline), growth {kk['growth_persen']}%"
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
            f"- {v['vendor']}: {v['jumlah_terkini']} CVE CRITICAL dalam 7 hari terakhir "
            f"(sebelumnya {v['jumlah_baseline']} dalam 7 hari baseline), growth {v['growth_persen']}%. "
            f"Produk terdampak: {produk_teks}"
        )
    return "\n".join(baris)


def _format_sampel_judul_untuk_prompt(daftar_judul: List[Dict]) -> str:
    if not daftar_judul:
        return "(tidak ada sampel judul insiden spesifik pada periode ini)"
    return "\n".join(f"- \"{j['judul']}\" ({j['sumber']})" for j in daftar_judul)


def prediksi_tren_berita(
    statistik_tren: Dict,
    df_riwayat: Optional[pd.DataFrame] = None,
    model: str = MODEL_PREDIKTOR
) -> str:
    statistik_berita = statistik_tren.get("berita", {})
    kk_signifikan = _filter_naik_signifikan(statistik_berita.get("kata_kunci_naik", []))

    if not kk_signifikan:
        logger.info("Tidak ada kata kunci berita dengan tren naik signifikan, skip pemanggilan LLM.")
        return (
            "Belum terdeteksi pola tren yang signifikan pada topik berita insiden siber "
            "dalam 14 hari terakhir. Data masih relatif stabil dibanding periode baseline."
        )

    kk_list = kk_signifikan[:6]
    kk_str = ", ".join([f"\"{k['kata_kunci']}\" (+{int(k['growth_persen'])}%)" for k in kk_list])

    cve_list = _filter_naik_signifikan(statistik_tren.get("cve", {}).get("vendor_naik", []))[:4]
    cve_summary = []
    for v in cve_list:
        p_names = "/".join(p['produk'] for p in v.get('top_produk', [])[:3])
        cve_summary.append(f"{v['vendor']} (+{int(v['growth_persen'])}%, produk: {p_names or 'sistem core'})")
    cve_str = "; ".join(cve_summary) if cve_summary else "Volume kerentanan vendor stabil"

    vektor_top = [f"{v['vektor']} ({v['jumlah']} artikel)" for v in statistik_tren.get("vektor_serangan", [])[:4]]
    sektor_top = [f"{s['sektor']}" for s in statistik_tren.get("sektor_target", [])[:3]]

    # RAG: Mengambil korpus fakta berita riil dari database
    rag_context = ""
    try:
        from src.analytics.rag_engine import RAGEngine
        rag_engine = RAGEngine(df_riwayat)
        rag_context = rag_engine.retrieve_berita_context(
            top_keywords=[k['kata_kunci'] for k in kk_signifikan],
            top_vectors=[v['vektor'] for v in statistik_tren.get("vektor_serangan", [])]
        )
    except Exception as err:
        logger.warning(f"Gagal mengambil konteks RAG berita: {err}")

    if not rag_context:
        sampel_judul = [f"\"{j['judul']}\"" for j in statistik_berita.get("sampel_judul_insiden", [])[:6]]
        rag_context = "; ".join(sampel_judul) if sampel_judul else "(tidak ada sampel spesifik)"

    user_prompt = (
        f"KORPUS FAKTA BERITA ASLI (RETRIEVED CONTEXT):\n"
        f"{rag_context}\n\n"
        f"STATISTIK TREN EMPIRIS:\n"
        f"- Kata Kunci Lonjakan Tertinggi: {kk_str}\n"
        f"- Lonjakan CVE Vendor Kritis: {cve_str}\n"
        f"- Vektor Serangan Dominan: {', '.join(vektor_top) if vektor_top else '-'}\n"
        f"- Sektor Target Terpapar: {', '.join(sektor_top) if sektor_top else '-'}"
    )

    hasil = _panggil_llm(SYSTEM_PROMPT_TREN_BERITA, user_prompt, model)
    if hasil is None:
        return "Analisis LLM gagal dijalankan. Data mentah: " + _format_kata_kunci_untuk_prompt(kk_signifikan)
    return bersihkan_output_llm(hasil)


def prediksi_tren_cve(
    statistik_cve: Dict,
    df_riwayat: Optional[pd.DataFrame] = None,
    model: str = MODEL_PREDIKTOR
) -> str:
    """Menghasilkan narasi tren CVE per vendor, implikasi kriptografi/integritas, dan panduan mitigasi."""
    vendor_signifikan = _filter_naik_signifikan(statistik_cve.get("vendor_naik", []))

    if not vendor_signifikan:
        logger.info("Tidak ada vendor CVE dengan tren naik signifikan, skip pemanggilan LLM.")
        return (
            "Belum terdeteksi vendor dengan lonjakan CVE yang signifikan dalam 14 hari terakhir. "
            "Volume kerentanan relatif stabil dibanding periode baseline."
        )

    vendor_cve_lines = []
    for v in vendor_signifikan[:5]:
        p_names = ", ".join(f"{p['produk']} ({p['jumlah']}x)" for p in v.get('top_produk', [])[:3])
        vendor_cve_lines.append(
            f"- {v['vendor']}: {v['jumlah_terkini']} CVE CRITICAL (sebelumnya {v['jumlah_baseline']}), "
            f"growth +{int(v['growth_persen'])}%. Produk terdampak: {p_names or 'tidak teridentifikasi'}"
        )

    # RAG: Mengambil entri CVE kritis aktual dari database
    cve_rag_context = ""
    try:
        from src.analytics.rag_engine import RAGEngine
        rag_engine = RAGEngine(df_riwayat)
        cve_rag_context = rag_engine.retrieve_cve_context([v['vendor'] for v in vendor_signifikan])
    except Exception as err:
        logger.warning(f"Gagal mengambil konteks RAG CVE: {err}")

    user_prompt = (
        f"KORPUS FAKTA KERENTANAN CVE ASLI (RETRIEVED CONTEXT):\n"
        f"{cve_rag_context}\n\n"
        f"DATA AKTUAL CVE CRITICAL DATABASE:\n" + "\n".join(vendor_cve_lines)
    )

    hasil = _panggil_llm(SYSTEM_PROMPT_TREN_CVE, user_prompt, model)
    if hasil is None:
        return "Analisis LLM gagal dijalankan. Data mentah: " + _format_vendor_untuk_prompt(vendor_signifikan)

    return bersihkan_output_llm(hasil)


def _bersihkan_link(raw_link: str) -> str:
    """Ekstrak URL tunggal yang valid dari output model LLM."""
    if not raw_link or str(raw_link).strip() in ["#", "-", "None"]:
        return "#"
    urls = re.findall(r'https?://[^\s,"\'<>]+', str(raw_link))
    return urls[0] if urls else "#"


def _normalisasi_isu_utama(isu: str, kategori: str = "") -> str:
    """
    Menormalkan keyword isu_utama menjadi 1-2 kata taksonomi ancaman CTI standar.
    Mencegah penyebutan nama vendor, tools, atau nama malware spesifik.
    """
    isu = (isu or "").strip().strip('"\'')
    if not isu or isu == "-" or isu.lower() == "none":
        return "Kondisi Kondusif"

    isu_lower = isu.lower()
    if any(m in isu_lower for m in ["grayrabbit", "infostealer", "trojan", "spyware", "stealer", "agenttesla", "lumma", "malware"]):
        return "Malware & Trojan"
    if "ransom" in isu_lower:
        return "Ransomware"
    if any(b in isu_lower for b in ["bocor", "leak", "breach", "data"]):
        return "Kebocoran Data"
    if any(p in isu_lower for p in ["bajak", "takeover", "akun"]):
        return "Pembajakan Akun"
    if any(c in isu_lower for c in ["celah", "rce", "vulnerability", "exploit", "zero-day", "0-day"]):
        return "Eksploitasi Celah"
    if any(f in isu_lower for f in ["phish", "fraud", "penipuan", "social engineering"]):
        return "Phishing & Fraud"
    if any(w in isu_lower for w in ["deface", "web", "slot", "ddos"]):
        return "Serangan Web & Defacement"

    words = isu.split()
    return " ".join(words[:2])


def _normalisasi_poin_cti(val: Any) -> str:
    """Membersihkan dan menormalisasi output poin dari LLM agar selalu berupa string multiline yang bersih."""
    if not val or val == "-":
        return "-"
    if isinstance(val, list):
        items = []
        for item in val:
            s = str(item).strip()
            s = s.strip("[]'\"")
            if s:
                items.append(s if s.startswith("- ") else f"- {s}")
        return "\n".join(items) if items else "-"
    
    val_str = str(val).strip()
    if val_str.startswith("[") and val_str.endswith("]"):
        try:
            import ast
            parsed = ast.literal_eval(val_str)
            if isinstance(parsed, list):
                return _normalisasi_poin_cti(parsed)
        except Exception:
            pass
        val_str = val_str[1:-1].strip()
        parts = [p.strip().strip("'\"") for p in val_str.split("', '")]
        return "\n".join(f"- {p}" if not p.startswith("-") else p for p in parts if p)

    return val_str


PROMPT_SISTEM_CTI = """Kamu adalah Senior Cyber Threat Intelligence (CTI) Analyst Diskominfo Provinsi Jawa Timur.
Tugasmu: Mengevaluasi korpus artikel insiden siber pada suatu wilayah (Internasional / Nasional / Jawa Timur) dalam 7 hari terakhir dari RAG engine, lalu menyusun:
1. Analisis Makro Lanskap & Urgensi Ancaman Wilayah (alasan_urgensi).
2. Proyeksi Risiko & Potensi Ancaman Masa Depan Wilayah (potensi_ancaman).
3. Memilih 1 Contoh Studi Kasus Riil Terverifikasi sebagai bukti empiris dari korpus (nama_kejadian, ringkasan_kasus, sumber, link, lokasi).

Format Output WAJIB JSON murni:
{
  "ada_kejadian": true,
  "isu_utama": "1-2 kata nama kategori ancaman makro paling dominan (PILIH: 'Kebocoran Data', 'Malware & Trojan', 'Ransomware', 'Pembajakan Akun', 'Eksploitasi Celah', 'Phishing & Fraud', 'Serangan Web & Defacement').",
  "alasan_urgensi": "2-3 butir poin (bullet points '- ') diawali kata kunci yang ditebalkan (**...**), menganalisis makro lanskap ancaman wilayah ini secara tajam. Format: '- **[Kata Kunci 1]**: [Ulasan...]\\n- **[Kata Kunci 2]**: [Ulasan...]'. DILARANG hanya meringkas 1 judul artikel!",
  "potensi_ancaman": "2-3 butir poin (bullet points '- ') diawali kata kunci yang ditebalkan (**...**), memproyeksikan dampak eskalasi risiko ke depan bagi instansi di wilayah ini. Format: '- **[Proyeksi 1]**: [Ulasan...]\\n- **[Proyeksi 2]**: [Ulasan...]'.",
  "nama_kejadian": "SALIN PERSIS 1 judul berita asli dari korpus yang paling representatif sebagai bukti empiris (DILARANG mengarang judul baru)",
  "ringkasan_kasus": "1-2 kalimat ringkasan spesifik mengenai kejadian pada studi kasus tersebut (siapa/apa yang diserang dan dampaknya)",
  "kategori": "Tag kategori teknis dari insiden yang dipilih (misal: Malware, Kebocoran Data, Pembajakan Akun, RCE)",
  "lokasi": "Lokasi target dari insiden yang dipilih",
  "sumber": "SALIN PERSIS 1 nama media sumber dari insiden yang dipilih",
  "link": "SALIN PERSIS 1 tautan URL asli dari insiden yang dipilih (HANYA 1 URL tunggal, jangan gabungkan URL)"
}

ATURAN QA / EVALUASI KETAT:
1. 'isu_utama' WAJIB singkat (1-2 kata) dan merupakan nama kategori CTI.
2. 'alasan_urgensi' dan 'potensi_ancaman' WAJIB menggunakan format poin-poin bullet ('- ') dengan kata kunci penting ditebalkan (**...**). Analisis makro wilayah secara keseluruhan (bukan sekadar kronologi 1 kasus berita). Detail kejadian tunggal hanya boleh ditaruh di 'ringkasan_kasus'.
3. 'nama_kejadian', 'sumber', dan 'link' HARUS disalin persis dari SATU artikel kandidat terbaik pada korpus wilayah.
4. DILARANG menggunakan kata klise seperti 'di era digital saat ini', 'kita harus berhati-hati', atau nasihat normatif tanpa bobot teknis.
5. Khusus Jawa Timur: Jika ada insiden lokal pada korpus (misal di Sidoarjo, Surabaya, Polda Jatim, dll.), WAJIB ada_kejadian: true. HANYA set ada_kejadian: false dan isu_utama: 'Kondisi Kondusif' jika korpus benar-benar kosong."""


def analisis_kasus_insiden_wilayah_ai(
    df_riwayat: Optional[pd.DataFrame] = None,
    kasus_wilayah_cluster: Optional[Dict] = None,
    model: str = MODEL_PREDIKTOR
) -> Dict:
    """
    Menganalisis dan menghasilkan penilaian CTI makro (lanskap ancaman wilayah, urgensi, proyeksi masa depan)
    beserta 1 contoh kasus insiden relevan untuk 3 wilayah (Internasional, Nasional, Jawa Timur)
    menggunakan RAG korpus fakta berita riil dan LLM lokal Ollama.
    """
    fallback_kosong = {
        "internasional": {
            "ada_kejadian": False, "isu_utama": "Kondisi Kondusif", "nama_kejadian": "-", "ringkasan_kasus": "", "kategori": "-",
            "lokasi": "Global", "alasan_urgensi": "-", "potensi_ancaman": "-", "sumber": "-", "link": "#"
        },
        "nasional": {
            "ada_kejadian": False, "isu_utama": "Kondisi Kondusif", "nama_kejadian": "-", "ringkasan_kasus": "", "kategori": "-",
            "lokasi": "Indonesia", "alasan_urgensi": "-", "potensi_ancaman": "-", "sumber": "-", "link": "#"
        },
        "jawa_timur": {
            "ada_kejadian": False, "isu_utama": "Kondisi Kondusif", "nama_kejadian": "-", "ringkasan_kasus": "", "kategori": "-",
            "lokasi": "Jawa Timur", "alasan_urgensi": "-", "potensi_ancaman": "-", "sumber": "-", "link": "#"
        }
    }

    # Jika cluster belum diberikan, hitung pengelompokan liputan media dari df_riwayat
    if kasus_wilayah_cluster is None:
        if df_riwayat is not None and not df_riwayat.empty:
            kasus_wilayah_cluster = hitung_kasus_insiden_wilayah(df_riwayat, top_n_per_wilayah=10)
        else:
            return fallback_kosong

    from src.analytics.rag_engine import RAGEngine
    rag_engine = RAGEngine(df_riwayat)

    # --- SINTESIS SPESIALISASI PER WILAYAH VIA RAG & OLLAMA ---
    def _sintesis_wilayah(nama_wilayah: str, label_wilayah: str) -> dict:
        cluster_items = (kasus_wilayah_cluster or {}).get(nama_wilayah, [])
        if not cluster_items:
            return {
                "ada_kejadian": False,
                "isu_utama": "Kondisi Kondusif",
                "nama_kejadian": "-",
                "ringkasan_kasus": "",
                "kategori": "-",
                "lokasi": label_wilayah,
                "alasan_urgensi": f"- **Nihil Anomali**: Nihil anomali atau insiden siber berkategori tinggi yang terverifikasi menargetkan infrastruktur di {label_wilayah} dalam 7 hari terakhir.",
                "potensi_ancaman": "- **Prioritas Hardening**: Fokus mitigasi tetap pada hardening celah sistem (unpatched CVE) dan peningkatan kewaspadaan aparatur terhadap rekayasa sosial / credential phishing.",
                "sumber": "-",
                "link": "#",
            }

        rag_context = rag_engine.retrieve_regional_context(cluster_items, label_wilayah, limit=10)

        user_content = (
            f"KORPUS FAKTA BERITA WILAYAH (RETRIEVED CONTEXT):\n"
            f"Wilayah: {label_wilayah}\n\n"
            f"{rag_context}\n\n"
            f"Instruksi CTI Wilayah:\n"
            f"- 'alasan_urgensi': Susun dalam 2-3 butir poin ('- ') diawali frasa kunci penting yang ditebalkan (**...**), analisis makro lanskap ancaman wilayah {label_wilayah} secara menyeluruh (vektor serangan, dinamika aktor, kerentanan yang sering disasar). DILARANG hanya menceritakan satu artikel!\n"
            f"- 'potensi_ancaman': Susun dalam 2-3 butir poin ('- ') diawali frasa kunci penting yang ditebalkan (**...**), proyeksikan ancaman lanjutan dan eskalasi risiko ke depan bagi instansi/wilayah ini.\n"
            f"- 'nama_kejadian': Pilih 1 artikel riil dari korpus di atas sebagai contoh kejadian relevan terverifikasi.\n"
            f"- 'ringkasan_kasus': Tuliskan 1-2 kalimat ringkasan spesifik mengenai kejadian studi kasus tersebut.\n"
            f"- 'sumber', 'link', 'lokasi': Salin persis data dari artikel yang dipilih tersebut."
        )

        try:
            resp = ollama.chat(
                model=model,
                messages=[
                    {"role": "system", "content": PROMPT_SISTEM_CTI},
                    {"role": "user", "content": user_content},
                ],
                format="json",
                options={"temperature": 0.1, "num_predict": 1024},
            )
            raw = json.loads(resp["message"]["content"].strip())
            nama = str(raw.get("nama_kejadian", "-")).strip()
            ada = bool(raw.get("ada_kejadian", True)) and nama not in ["-", "", "None"]

            isu_raw = str(raw.get("isu_utama", "")).strip()
            isu_normal = _normalisasi_isu_utama(isu_raw, str(raw.get("kategori", "")))

            return {
                "ada_kejadian": ada,
                "isu_utama": isu_normal if ada else "Kondisi Kondusif",
                "nama_kejadian": nama if ada else "-",
                "ringkasan_kasus": str(raw.get("ringkasan_kasus", "")).strip() if ada else "",
                "kategori": str(raw.get("kategori", "Insiden Siber")).strip() if ada else "-",
                "lokasi": str(raw.get("lokasi", label_wilayah)).strip() if ada else label_wilayah,
                "alasan_urgensi": _normalisasi_poin_cti(raw.get("alasan_urgensi", "-")) if ada else "-",
                "potensi_ancaman": _normalisasi_poin_cti(raw.get("potensi_ancaman", "-")) if ada else "-",
                "sumber": str(raw.get("sumber", "-")).strip() if ada else "-",
                "link": _bersihkan_link(raw.get("link", "#")) if ada else "#",
            }
        except Exception as err:
            logger.warning(f"Gagal sintesis CTI AI untuk {label_wilayah}: {err}")
            return {
                "ada_kejadian": False,
                "isu_utama": "Kondisi Kondusif",
                "nama_kejadian": "-",
                "ringkasan_kasus": "",
                "kategori": "-",
                "lokasi": label_wilayah,
                "alasan_urgensi": "-",
                "potensi_ancaman": "-",
                "sumber": "-",
                "link": "#",
            }

    hasil_intl = _sintesis_wilayah("internasional", "Internasional (Global)")
    hasil_nas = _sintesis_wilayah("nasional", "Nasional (Indonesia)")
    hasil_jatim = _sintesis_wilayah("jawa_timur", "Jawa Timur")

    return {
        "internasional": hasil_intl,
        "nasional": hasil_nas,
        "jawa_timur": hasil_jatim,
    }


def proses_prediksi_tren(
    statistik_tren: Dict,
    df_riwayat: Optional[pd.DataFrame] = None,
    model: str = MODEL_PREDIKTOR
) -> Dict:
    """
    Titik masuk utama modul ini: menerima output susun_ringkasan_statistik_tren()
    dari trend_analyzer.py, mengembalikan 2 narasi terpisah siap tampil di web
    beserta analisis makro wilayah menggunakan RAG korpus fakta berita riil dan Ollama.
    """
    logger.info("Menyusun prediksi tren berita CTI dengan RAG korpus berita riil...")
    narasi_berita = prediksi_tren_berita(statistik_tren, df_riwayat=df_riwayat, model=model)

    logger.info("Menyusun prediksi tren CVE dengan RAG data kerentanan riil...")
    narasi_cve = prediksi_tren_cve(statistik_tren.get("cve", {}), df_riwayat=df_riwayat, model=model)

    logger.info("Menganalisis penilaian CTI makro wilayah (Internasional, Nasional, Jawa Timur) dengan RAG & Ollama...")
    kasus_ai = analisis_kasus_insiden_wilayah_ai(df_riwayat=df_riwayat, model=model)

    return {
        "prediksi_berita": narasi_berita,
        "prediksi_cve": narasi_cve,
        "kasus_wilayah_ai": kasus_ai,
    }


if __name__ == "__main__":
    # Testing manual: python -m src.analytics.trend_predictor
    from src.analytics.trend_analyzer import susun_ringkasan_statistik_tren
    from src.storage.db import ambil_riwayat_tren

    df = ambil_riwayat_tren(hari=14)
    statistik = susun_ringkasan_statistik_tren(df)
    hasil = proses_prediksi_tren(statistik)

    print("=== PREDIKSI TREN BERITA ===")
    print(hasil["prediksi_berita"])
    print("\n=== PREDIKSI TREN CVE ===")
    print(hasil["prediksi_cve"])