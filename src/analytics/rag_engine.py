"""
Modul RAG (Retrieval-Augmented Generation) & Analisis Pola Ancaman CTI.
Mengambil fakta artikel riil dari riwayat_tren di SQLite untuk diinjeksikan
ke prompt LLM (grounded context), serta menghitung proyeksi 1 pola serangan
terdepan (1 kata) berdasarkan momentum eskalasi historis.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import math
import pandas as pd
from src.utils.config_loader import ConfigLoader
import re
from collections import Counter

from src.utils.llm_adapter import GeminiLLMAdapter
from src.utils.logger import setup_logger
from src.cti.preparer import CLOSED_11_TAXONOMY_CATEGORIES, TAXONOMY_DISPLAY_NAMES

logger = setup_logger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "state.db"

_EMBEDDING_CACHE: Dict[str, List[float]] = {}
_MITRE_EMBEDDING_CACHE: Dict[str, List[float]] = {}


_REGEX_PENEGAKAN_HUKUM = re.compile(
    r"\b(tangkap|ditangkap|penangkapan|menangkap|diringkus|tertangkap|sidang|divonis|vonis|ekstradisi|didakwa|dihukum\s+penjara|"
    r"arrest|arrested|arresting|indicted|extradited|sentenced|pleads guilty|convicted|detained)\b",
    re.IGNORECASE
)


def is_berita_penegakan_hukum(row_or_dict: dict) -> bool:
    """
    Mendeteksi apakah artikel merupakan pelaporan aksi penegakan hukum (penangkapan, peradilan, vonis)
    terhadap pelaku/hacker, bukan laporan insiden serangan siber aktif.
    """
    judul = str(row_or_dict.get("judul", "")).strip()
    if _REGEX_PENEGAKAN_HUKUM.search(judul):
        return True
    ringkasan = str(row_or_dict.get("ringkasan_atau_narasi", ""))[:300]
    if _REGEX_PENEGAKAN_HUKUM.search(ringkasan):
        if re.search(r"\b(polisi|aparat|fbi|europol|interpol|kejaksaan|satreskrim|bareskrim|polda|polres|otoritas|penyidik|tersangka|terdakwa|pelaku|hacker|dalang|pembobol)\b", ringkasan, re.I):
            return True
    return False


def _ambil_batas_preview_berita() -> int:
    try:
        cfg = ConfigLoader.get_config() or {}
        cti = cfg.get("cti_analysis") or {}
        rag = cti.get("rag") or {}
        trunc = rag.get("truncation") or {}
        return int(trunc.get("berita_preview", 220))
    except Exception:
        return 220


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Menghitung cosine similarity antara dua vector embedding."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = 0.0
    sum_a = 0.0
    sum_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        sum_a += a * a
        sum_b += b * b
    if sum_a <= 0.0 or sum_b <= 0.0:
        return 0.0
    return dot / (math.sqrt(sum_a) * math.sqrt(sum_b))


def extract_threat_entity_organic(judul: str, narasi: str = "", kata_kunci: str = "") -> str:
    """
    Mengekstrak nama spesifik malware, exploit, zero-day, backdoor, botnet, atau modus serangan
    secara langsung dan organik dari teks berita tanpa menggunakan klasifikasi kaku.
    Contoh output:
    - 'Backdoor TASK#STOMP'
    - 'NetScaler Zero-Day'
    - 'Ransomware LockBit'
    - 'Trojan RemControl'
    - 'Botnet CARBONATO'
    - 'Phishing APK'
    - 'Penipuan Online'
    - 'Pencurian Kripto'
    """
    judul_clean = re.sub(r'[\"\'\`“”‘’]', '', str(judul or "")).strip()
    narasi_clean = re.sub(r'[\"\'\`“”‘’]', '', str(narasi or "")).strip()
    teks = f"{judul_clean}. {narasi_clean}"

    STOP_TERMS = {
        'pada', 'pencuri', 'yang', 'dan', 'untuk', 'dengan', 'dari', 'tersebut', 'kini',
        'baru', 'aktif', 'menyerang', 'seperti', 'antara', 'uses', 'hides', 'gives',
        'steals', 'from', 'terintegrasi', 'berbahaya', 'dalam', 'bisa', 'akan', 'hacks',
        'sistem', 'server', 'komputer', 'perangkat', 'jaringan', 'terhadap', 'adalah',
        'sejumlah', 'banyak', 'beberapa', 'sebuah', 'suatu', 'the', 'a', 'an', 'of', 'in',
        'on', 'at', 'to', 'for', 'ini', 'itu', 'atas', 'oleh', 'di', 'ke', 'juga', 'tagar',
        'terdeteksi', 'ditemukan', 'menginfeksi', 'menyasar', 'menargetkan', 'melumpuhkan',
        'membajak', 'meretas', 'mencuri', 'curi', 'bobol', 'membobol', 'serang', 'terpasang',
        'bernama', 'ponsel', 'android', 'iphone', 'murah', 'diam', 'secara'
    }

    # 0. Pola 'Malware/Ransomware/Backdoor (baru) bernama <Nama>'
    m_named = re.search(
        r'\b(Backdoor|Malware|Ransomware|Trojan|Infostealer|Stealer|Botnet|Spyware)(?:\s+\w+){0,2}\s+bernama\s+([A-Z0-9][A-Za-z0-9#@_\-\.]{2,25}(?:\s+[A-Z0-9][A-Za-z0-9#@_\-\.]{2,20})?)\b',
        teks, re.IGNORECASE
    )
    if m_named:
        return f"{m_named.group(1).title()} {m_named.group(2).strip()}"

    # 1. Pola Malware/Backdoor/Ransomware/Trojan/Infostealer/Botnet/Spyware + Nama Entitas Spesifik (Huruf Kapital)
    m_malware = re.search(
        r'\b(Backdoor|Malware|Ransomware|Trojan|Infostealer|Stealer|Botnet|Spyware)\s+([A-Z0-9][A-Za-z0-9#@_\-\.]{2,25}(?:\s+[A-Z0-9][A-Za-z0-9]{2,20})?)\b',
        teks
    )
    if m_malware:
        tipe = m_malware.group(1).title()
        nama = m_malware.group(2).strip()
        first_word = nama.split()[0].lower()
        if first_word not in STOP_TERMS and nama.lower() not in STOP_TERMS and len(nama) > 2:
            return f"{tipe} {nama}"

    # 2. Pola Zero-Day atau CVE Produk / Vendor spesifik
    m_zero = re.search(r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)\s+(?:Zero-Days?|0-Days?)\b', teks, re.IGNORECASE)
    if m_zero and m_zero.group(1).lower() not in STOP_TERMS:
        return f"{m_zero.group(1)} Zero-Day"

    m_cve = re.search(r'\b(CVE-\d{4}-\d{4,7})\b', teks, re.IGNORECASE)
    if m_cve:
        m_prod = re.search(r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)\s+(?:Zero-Days?|0-Days?|Celah|Kerentanan|CVE)', judul_clean, re.IGNORECASE)
        if m_prod and m_prod.group(1).lower() not in STOP_TERMS:
            return f"{m_prod.group(1)} ({m_cve.group(1).upper()})"
        return m_cve.group(1).upper()

    # 3. APT / Aktor Ancaman Terorganisir
    m_apt = re.search(r'\b(APT[0-9]+|[A-Z][a-z0-9]+\s+(?:Typhoon|Spider|Blizzard|Bear|Panda|Chollima|Kitten|Jackal)|Lazarus|ShinyHunters|RansomHub|LockBit)\b', teks, re.IGNORECASE)
    if m_apt:
        return f"Aktor {m_apt.group(1).title()}"

    # 4. Modus Serangan dengan Preposisi (misal: "Peretasan terhadap FBI" -> "Peretasan FBI")
    m_prep = re.search(r'\b(Peretasan|Pencurian|Kebocoran|Pembobolan)\s+(?:terhadap|pada|oleh|di|ke|dari|untuk|dan|yang)\s+([A-Z0-9][a-zA-Z0-9\.\#\-]+(?:\s+[A-Z0-9][a-zA-Z0-9\.\#\-]+)?)', teks, re.IGNORECASE)
    if m_prep:
        target = m_prep.group(2).strip()
        first_w = target.split()[0].lower()
        if first_w not in STOP_TERMS and len(target) > 2:
            return f"{m_prep.group(1).title()} {target.title()}"

    # 5. Pola Serangan / Modus Spesifik Lainnya
    m_modus = re.search(
        r'\b(Judi\s+Online|Pencurian\s+Kripto|Penipuan\s+Online|Situs\s+Palsu|Phishing\s+APK|Data\s+Breach\s+[A-Z][a-zA-Z0-9]+|Kartu\s+Kredit\s+Dibobol|Kebocoran\s+Data\s+[A-Z][a-zA-Z0-9]+|Peretasan\s+[A-Z][a-zA-Z0-9]+)\b',
        teks, re.IGNORECASE
    )
    if m_modus:
        val = m_modus.group(1).title()
        words = val.split()
        if len(words) > 1 and words[1].lower() not in STOP_TERMS:
            return val

    # 6. Fallback organik aman (menghindari pemotongan judul sembarang seperti 'Ratusan Supermarket Prancis')
    return "Insiden Siber"


def resolve_article_taxonomy_category(row_or_dict: Any, return_display: bool = False) -> str:
    """
    Mengidentifikasi kategori taksonomi insiden dari artikel berita
    berdasarkan 11 kategori tertutup eCSIRT (CLOSED_11_TAXONOMY_CATEGORIES).
    Jika return_display=True, mengembalikan TAXONOMY_DISPLAY_NAMES.
    """
    if row_or_dict is None:
        cat = "tidak_dapat_ditentukan"
        return TAXONOMY_DISPLAY_NAMES.get(cat, cat) if return_display else cat

    if hasattr(row_or_dict, "to_dict"):
        data = row_or_dict.to_dict()
    elif isinstance(row_or_dict, dict):
        data = row_or_dict
    else:
        try:
            data = dict(row_or_dict)
        except Exception:
            data = {}

    cat_found = None
    explicit_field_found = False

    # 1. Cek langsung field taksonomi di artikel jika ada
    for field in ["kategori_insiden", "kategori_taksonomi", "kategori_utama", "taxonomy_category", "kategori"]:
        val = str(data.get(field, "")).strip()
        if not val or val.lower() in ["berita", "none", "nan", "tidak ada"]:
            continue
        val_norm = val.lower().replace("-", "_").replace(" ", "_")
        if val_norm in CLOSED_11_TAXONOMY_CATEGORIES:
            cat_found = val_norm
            explicit_field_found = True
            break
        for k, v in TAXONOMY_DISPLAY_NAMES.items():
            if val.lower() == v.lower() or val.lower() == k.lower():
                cat_found = k
                explicit_field_found = True
                break
        if cat_found:
            break

    # 2. Cek record di intelijen_berita_tervalidasi via identifier / link
    if not cat_found:
        ident = data.get("identifier") or data.get("link")
        if ident:
            try:
                from src.storage.db import ambil_intelijen_berita
                rec = ambil_intelijen_berita(str(ident))
                if rec and rec.get("kategori_insiden"):
                    rec_kat = str(rec.get("kategori_insiden")).strip()
                    for k, v in TAXONOMY_DISPLAY_NAMES.items():
                        if rec_kat.lower() in [v.lower(), k.lower()]:
                            cat_found = k
                            break
            except Exception:
                pass

    # 3. Cek pemetaan MITRE ATT&CK jika ada
    if not cat_found:
        m_list = data.get("mitre_mapping", [])
        if isinstance(m_list, list) and m_list:
            top_tid = str(m_list[0].get("id", "")) if isinstance(m_list[0], dict) else str(m_list[0])
            if top_tid.startswith("T1486"):
                cat_found = "ransomware"
            elif top_tid.startswith("T1190"):
                cat_found = "eksploitasi_kerentanan"
            elif top_tid.startswith("T1566"):
                cat_found = "phishing_penipuan"

    # 4. Heuristik NLP dari konten teks (judul, ringkasan, kata kunci)
    if not explicit_field_found and (not cat_found or cat_found in ["tidak_dapat_ditentukan", "lainnya"]):
        judul = str(data.get("judul", "")).lower()
        narasi = str(data.get("ringkasan_atau_narasi", "") or data.get("ringkasan", "") or data.get("narasi", "")).lower()
        kata_kunci = str(data.get("kata_kunci", "")).lower()
        teks = f"{judul} {narasi} {kata_kunci}"

        if any(k in teks for k in ["ransomware", "tebusan", "enkripsi file", "mengenkripsi"]):
            cat_found = "ransomware"
        elif any(k in teks for k in ["bocor", "breach", "kebocoran data", "dijual di forum", "basis data", "data pribadi", "pembocoran data"]):
            cat_found = "data_breach"
        elif any(k in teks for k in ["ddos", "dos", "lumpuh", "ketersediaan", "denial of service", "banjir trafik"]):
            cat_found = "ddos"
        elif any(k in teks for k in ["deface", "defacement", "web deface", "slot", "judi", "peretasan web"]):
            cat_found = "defacement"
        elif any(k in teks for k in ["zero-day", "0-day", "rce", "cve-", "cve", "exploit", "kerentanan", "celah keamanan", "celah", "vulnerability"]):
            cat_found = "eksploitasi_kerentanan"
        elif any(k in teks for k in ["malware", "trojan", "infostealer", "stealer", "backdoor", "spyware", "botnet", "webshell"]):
            cat_found = "malware"
        elif any(k in teks for k in ["phishing", "penipuan", "apk", "palsu", "scam", "social engineering"]):
            cat_found = "phishing_penipuan"
        elif any(k in teks for k in ["akses tidak sah", "kredensial", "sso", "pembobolan akun", "kompromi akun", "pencurian akun", "login", "password", "unauthorized access"]):
            cat_found = "akses_tidak_sah"
        elif any(k in teks for k in ["pelecehan", "konten berbahaya", "spam", "hoaks"]):
            cat_found = "pelecehan_konten"
        elif any(k in teks for k in ["peretasan", "hacked", "dibobol", "menyerang"]):
            cat_found = "akses_tidak_sah"
        elif not cat_found:
            cat_found = "tidak_dapat_ditentukan"

    if cat_found not in CLOSED_11_TAXONOMY_CATEGORIES:
        cat_found = "tidak_dapat_ditentukan"

    if return_display:
        return TAXONOMY_DISPLAY_NAMES.get(cat_found, "Tidak Dapat Ditentukan")
    return cat_found


def _bagi_periode_terkini_baseline(df_dedup: pd.DataFrame) -> tuple:
    """
    Membagi dataframe berita ke periode terkini vs baseline.
    Jika baseline kosong karena tanggal unik < 8 pada dataset uji,
    dilakukan pembagian proporsional berdasarkan tanggal unik agar periode historis tetap terbentuk.
    """
    from src.analytics.trend_analyzer import _split_periode
    df_terkini, df_baseline = _split_periode(df_dedup)
    if df_baseline.empty and not df_dedup.empty and "tanggal_publish" in df_dedup.columns:
        tgl_s = df_dedup["tanggal_publish"].fillna("").astype(str).str.slice(0, 10)
        u_dates = sorted(tgl_s[tgl_s.str.match(r"^\d{4}-\d{2}-\d{2}$")].unique(), reverse=True)
        if len(u_dates) >= 2:
            split_idx = max(1, len(u_dates) // 2)
            dates_terkini = set(u_dates[:split_idx])
            dates_baseline = set(u_dates[split_idx:])
            df_terkini = df_dedup[tgl_s.isin(dates_terkini)].copy()
            df_baseline = df_dedup[tgl_s.isin(dates_baseline)].copy()
    if df_terkini.empty:
        df_terkini = df_dedup
    return df_terkini, df_baseline



_SECURITY_VENDORS_STOP = {
    "kaspersky", "crowdstrike", "mandiant", "zimperium", "sophos", "trend micro",
    "bssn", "google", "microsoft", "fortinet", "palo alto", "check point", "checkpoint",
    "cisco", "eset", "sentinelone", "bitdefender", "symantec", "cert", "csirt",
    "cisa", "fbi", "europol", "interpol", "polri", "bareskrim", "kominfo", "diskominfo"
}


def extract_structured_rag_facts(articles: List[Any], label_kelompok: str = "") -> Dict[str, Any]:
    """
    Mengekstrak elemen fakta terstruktur (RAG) dari kumpulan artikel berita:
    - kejadian: apa saja insiden/kasus yang terjadi (gambaran besar)
    - aktor: siapa aktor/pelaku penyerang yang disebutkan di berita
    - pihak_terdampak: siapa entitas/sektor yang terdampak
    - lokasi_kejadian: di mana kejadian berlangsung
    - senjata_metode: menggunakan senjata/alat/metode apa
    - alur_serangan: bagaimana kejadiannya & alur insiden dari awal sampai akhir
    - dampak: apa dampak nyata yang ditimbulkan terhadap korban
    """
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher

    if not articles:
        return {
            "kejadian": "-",
            "aktor": "Pelaku belum teridentifikasi dalam laporan berita",
            "pihak_terdampak": "Entitas terdampak belum dirinci secara spesifik",
            "lokasi_kejadian": "Lokasi tidak dirinci secara spesifik dalam berita",
            "senjata_metode": "Metode serangan siber sesuai kategori insiden",
            "alur_serangan": "Rincian kronologi teknis belum dijabarkan lebih lanjut dalam laporan sumber.",
            "dampak": "Gangguan keamanan sistem dan risiko paparan aset digital",
            "judul_kasus_list": [],
            "narasi_kasus_list": [],
            "korpus_terstruktur": "(Tidak ada artikel berita terkait)",
        }

    judul_list = []
    narasi_list = []
    gabungan_teks_list = []
    sumber_list = []
    identifiers = []

    for art in articles:
        data = art.to_dict() if hasattr(art, "to_dict") else (dict(art) if not isinstance(art, dict) else art)
        raw_j = str(data.get("judul", "")).strip()
        clean_j, _ = _bersihkan_judul_dan_publisher(raw_j, str(data.get("sumber", "")))
        narasi = str(data.get("ringkasan_atau_narasi", "") or data.get("ringkasan", "") or "").strip()
        kw = str(data.get("kata_kunci", "")).strip()
        sumber = str(data.get("sumber", "Media")).strip()
        ident = str(data.get("identifier", "") or data.get("link", "")).strip()

        if clean_j and clean_j not in judul_list:
            judul_list.append(clean_j)
        if narasi and narasi not in narasi_list:
            narasi_list.append(narasi)
        if sumber and sumber not in sumber_list:
            sumber_list.append(sumber)
        if ident:
            identifiers.append(ident)
        gabungan_teks_list.append(f"{clean_j}. {narasi}. {kw}")

    full_text = " ".join(gabungan_teks_list)
    full_lower = full_text.lower()

    # 1. Ekstraksi Aktor Penyerang
    aktor_found = []
    known_actors = re.findall(
        r"\b(APT\d+|[A-Z][a-z0-9]+\s+(?:Typhoon|Spider|Blizzard|Bear|Panda|Chollima|Kitten|Jackal)|"
        r"Lazarus|ShinyHunters|RansomHub|LockBit|BlackCat|ALPHV|Clop|Kimsuky|Sandworm|MuddyWater|"
        r"Mustang\s+Panda|BlueNoroff|Brain\s+Cipher|Bjorka|Medusa|Akira|Qilin|Rhysida|BlackBasta|Lapsus\$)\b",
        full_text,
        re.IGNORECASE,
    )
    for ak in known_actors:
        ak_clean = ak.strip()
        if ak_clean.lower() not in _SECURITY_VENDORS_STOP and ak_clean not in aktor_found:
            aktor_found.append(ak_clean)

    for m_ak in re.finditer(
        r"\b(?:kelompok\s+peretas|grup\s+hacker|sindikat\s+peretas|peretas\s+asal\s+[A-Z][a-z]+|hacker\s+asal\s+[A-Z][a-z]+|kelompok\s+hacker)\s+([A-Z][A-Za-z0-9_\-#]{2,25})?",
        full_text,
    ):
        phrase = m_ak.group(0).strip()
        if not any(v in phrase.lower() for v in _SECURITY_VENDORS_STOP) and phrase not in aktor_found:
            aktor_found.append(phrase)

    if aktor_found:
        aktor_str = ", ".join(aktor_found[:3])
    elif any(k in full_lower for k in ["peretas", "hacker", "penyerang", "sindikat", "pelaku"]):
        aktor_str = "Aktor ancaman / kelompok peretas yang belum diungkap identitas resminya dalam berita"
    else:
        aktor_str = "Pelaku belum teridentifikasi secara spesifik dalam laporan berita"

    # 2. Ekstraksi Pihak / Entitas & Sektor Terdampak
    sektor_terdeteksi = []
    if identifiers:
        try:
            from src.storage.db import ambil_intelijen_berita
            for ident in identifiers[:8]:
                rec = ambil_intelijen_berita(ident)
                if rec and rec.get("sektor_target") and rec.get("sektor_target") != "Tidak dapat ditentukan":
                    sek = rec.get("sektor_target")
                    if sek not in sektor_terdeteksi:
                        sektor_terdeteksi.append(sek)
        except Exception:
            pass

    sektor_heuristik_map = [
        ("Administrasi Pemerintahan", ["pemerintah", "pemprov", "pemkab", "pemkot", "dinas", "kementerian", "instansi", "asn", "bssn", "desa"]),
        ("Keuangan & Perbankan", ["bank", "perbankan", "keuangan", "finansial", "kripto", "crypto", "rekening", "nasabah", "fintech", "asuransi"]),
        ("Teknologi Informasi & Komunikasi (TIK)", ["server", "cloud", "perangkat lunak", "aplikasi", "sistem operasi", "jaringan", "telekomunikasi", "isp", "data center", "github", "npm", "open source", "plugin", "wordpress", "windows", "linux", "android", "apple", "google", "microsoft", "cisco", "fortinet"]),
        ("Kesehatan", ["rumah sakit", "rsud", "medis", "kesehatan", "pasien", "klinik", "farmasi"]),
        ("Pendidikan", ["kampus", "universitas", "sekolah", "pendidikan", "mahasiswa", "akademik"]),
        ("Transportasi", ["bandara", "penerbangan", "maskapai", "pelabuhan", "kereta", "logistik", "transportasi"]),
        ("Energi & Sumber Daya Mineral", ["energi", "listrik", "pln", "migas", "pertamina", "tambang", "gardu"]),
        ("Pertahanan & Keamanan", ["militer", "pertahanan", "kepolisian", "polri", "tni", "intelijen", "fbi"]),
        ("Pangan", ["pangan", "pertanian", "perkebunan", "supermarket", "ritel", "distribusi makanan"]),
        ("Layanan Publik & Pengguna Digital", ["pengguna", "masyarakat", "publik", "konsumen", "warga", "pelanggan", "media sosial", "akun"]),
    ]
    for sek_label, kws in sektor_heuristik_map:
        if any(k in full_lower for k in kws) and sek_label not in sektor_terdeteksi:
            sektor_terdeteksi.append(sek_label)

    # Cari entitas korban spesifik dari judul
    entitas_korban = []
    for j in judul_list[:4]:
        entitas_korban.append(j)

    if sektor_terdeteksi:
        pihak_terdampak_str = f"Sektor {', '.join(sektor_terdeteksi[:2])}"
    else:
        pihak_terdampak_str = "Entitas korban pada sistem terkait"

    # 3. Ekstraksi Lokasi / Di Mana Kejadiannya
    lokasi_found = []
    lokasi_candidates = [
        ("Jawa Timur", ["jawa timur", "jatim", "surabaya", "malang", "sidoarjo", "gresik", "banyuwangi", "jember", "kediri"]),
        ("Indonesia (Nasional)", ["indonesia", "jakarta", "nasional", "kementerian", "komdigi", "bssn", "polri", "tanah air", "nusantara"]),
        ("Amerika Serikat", ["amerika serikat", "as", "u.s.", "united states", "fbi", "cisa", "washington", "california"]),
        ("Eropa", ["eropa", "inggris", "uk", "prancis", "jerman", "belanda", "uni eropa", "italia", "spanyol"]),
        ("Asia-Pasifik", ["jepang", "korea", "china", "tiongkok", "singapura", "australia", "india", "taiwan", "vietnam", "malaysia"]),
    ]
    for lok_label, kws in lokasi_candidates:
        if any(re.search(r"\b" + re.escape(k) + r"\b", full_lower) for k in kws):
            lokasi_found.append(lok_label)

    if lokasi_found:
        lokasi_str = ", ".join(lokasi_found[:3])
    else:
        lokasi_str = "Ekosistem Digital Lintas Wilayah / Global"

    # 4. Ekstraksi Senjata / Alat / Metode Serangan
    senjata_found = []
    cves = re.findall(r"\bCVE-\d{4}-\d{4,7}\b", full_text, re.IGNORECASE)
    for c in cves:
        cu = c.upper()
        if cu not in senjata_found:
            senjata_found.append(cu)

    named_tools = re.findall(
        r"\b(?:malware|ransomware|trojan|spyware|stealer|botnet|backdoor|rat)\s+(?:bernama\s+)?([A-Z][A-Za-z0-9_-]{2,20}(?:\s+[A-Z][A-Za-z0-9_-]{2,20})?)\b",
        full_text,
    )
    _STOP_TOOL_WORDS = {
        "sasar", "menargetkan", "baru", "terdeteksi", "android", "windows",
        "iphone", "linux", "yang", "dan", "di", "pada", "untuk", "dengan",
        "jenis", "berbahaya", "resmi", "tersebut", "ini", "ponsel", "perangkat"
    }
    for nt in named_tools:
        tokens = [t for t in nt.split() if t.lower() not in _STOP_TOOL_WORDS]
        if tokens:
            clean_tool = f"Malware {' '.join(tokens)}"
            if clean_tool not in senjata_found:
                senjata_found.append(clean_tool)

    metode_map = [
        ("Ransomware & Enkripsi Penyanderaan Data", ["ransomware", "tebusan", "enkripsi file", "mengenkripsi"]),
        ("Eksploitasi Celah Keamanan / Zero-Day", ["zero-day", "0-day", "rce", "exploit", "celah keamanan", "kerentanan", "cve-"]),
        ("Malware / Infostealer & Backdoor", ["malware", "infostealer", "stealer", "trojan", "backdoor", "spyware", "botnet", "rat"]),
        ("Phishing & Rekayasa Sosial (Social Engineering)", ["phishing", "penipuan", "tautan palsu", "scam", "social engineering", "apk palsu"]),
        ("Serangan DDoS / Banjir Trafik Jaringan", ["ddos", "denial of service", "banjir trafik"]),
        ("Penyusupan Akun & Pencurian Kredensial", ["kredensial", "password", "pembobolan akun", "akses tidak sah", "brute force", "sso"]),
        ("Web Defacement & Injeksi Konten Ilegal", ["deface", "defacement", "slot", "judi online", "ubah tampilan"]),
    ]
    for m_label, kws in metode_map:
        if any(k in full_lower for k in kws) and m_label not in senjata_found:
            senjata_found.append(m_label)

    senjata_str = ", ".join(senjata_found[:3]) if senjata_found else (label_kelompok or "Eksploitasi Siber Terarah")

    # 5. Ekstraksi Dampak Nyata
    dampak_found = []
    dampak_map = [
        ("kebocoran serta eksfiltrasi data sensitif/pribadi (data breach)", ["bocor", "breach", "kebocoran data", "data pribadi", "dijual", "eksfiltrasi", "database bocor"]),
        ("terenkripsinya sistem operasional dan penyanderaan basis data disertai tuntutan tebusan", ["ransomware", "tebusan", "terenkripsi", "mengenkripsi", "terkunci"]),
        ("kelumpuhan layanan dan terganggunya ketersediaan akses sistem", ["lumpuh", "down", "tidak dapat diakses", "gangguan layanan", "ddos", "offline"]),
        ("pengambilalihan akses sistem/akun secara tidak sah dan kompromi kredensial pengguna", ["akses tidak sah", "pembobolan akun", "kredensial", "password", "kompromi akun", "ambil alih", "remote code execution", "rce", "backdoor"]),
        ("kerugian finansial dan pencurian aset digital korban", ["kerugian", "finansial", "dana", "rekening", "kripto", "uang", "pencurian"]),
        ("perubahan tampilan situs web (defacement) dan rusaknya integritas konten layanan", ["deface", "defacement", "ubah tampilan", "judi"]),
    ]
    for d_label, kws in dampak_map:
        if any(k in full_lower for k in kws) and d_label not in dampak_found:
            dampak_found.append(d_label)

    dampak_str = "; ".join(dampak_found[:3]) if dampak_found else "risiko kompromi keamanan sistem dan gangguan operasional pada entitas sasaran"

    # 6. Kejadian & Alur Serangan dari Berita (Rangkuman 1 Kasus Utuh)
    nama_kasus_utama = judul_list[0] if judul_list else (label_kelompok or "Insiden Siber")
    kejadian_str = nama_kasus_utama
    narasi_terpilih = []
    for n in narasi_list:
        n_clean = n.strip()
        if n_clean and not any(n_clean[:60].lower() in exist.lower() for exist in narasi_terpilih):
            narasi_terpilih.append(n_clean)
    if narasi_terpilih:
        alur_str = " ".join(narasi_terpilih[:2])
    else:
        alur_str = "Penyerang melancarkan aksi eksploitasi dan penetrasi sistem hingga menimbulkan dampak operasional."

    # 7. Susun Korpus Terstruktur untuk Prompt LLM
    detail_berita_lines = []
    for idx, art in enumerate(articles[:6]):
        data = art.to_dict() if hasattr(art, "to_dict") else (dict(art) if not isinstance(art, dict) else art)
        j_raw = str(data.get("judul", "-")).strip()
        j_clean, _ = _bersihkan_judul_dan_publisher(j_raw, "")
        r_raw = str(data.get("ringkasan_atau_narasi", "") or data.get("ringkasan", "")).strip()
        detail_berita_lines.append(f'  {idx+1}. Judul Kasus: "{j_clean}"\n     Fakta & Alur Kejadian: {r_raw}')

    korpus_terstruktur = (
        f"- Kategori / Tren Insiden: {label_kelompok or kejadian_str}\n"
        f"- Gambaran Kejadian (Kasus Terkait): {kejadian_str}\n"
        f"- Aktor Penyerang: {aktor_str}\n"
        f"- Siapa yang Terdampak (Korban & Sektor): {pihak_terdampak_str}\n"
        f"- Di Mana Kejadiannya (Lokasi/Lingkup): {lokasi_str}\n"
        f"- Senjata / Alat / Metode Serangan: {senjata_str}\n"
        f"- Kronologi & Alur Insiden dari Awal sampai Akhir: {alur_str}\n"
        f"- Dampak Insiden: {dampak_str}\n"
        f"- Fakta Berita Sumber:\n" + "\n".join(detail_berita_lines)
    )

    return {
        "nama_kasus": nama_kasus_utama,
        "kejadian": kejadian_str,
        "aktor": aktor_str,
        "pihak_terdampak": pihak_terdampak_str,
        "lokasi_kejadian": lokasi_str,
        "senjata_metode": senjata_str,
        "alur_serangan": alur_str,
        "dampak": dampak_str,
        "judul_kasus_list": judul_list,
        "narasi_kasus_list": narasi_list,
        "korpus_terstruktur": korpus_terstruktur,
    }


class RAGEngine:
    """
    Engine RAG sederhana dan teroptimasi untuk mengambil korpus berita riil
    dan mengevaluasi proyeksi pola serangan berdasarkan data historis.
    """

    def __init__(self, df_riwayat: Optional[pd.DataFrame] = None):
        self.df_riwayat = df_riwayat if df_riwayat is not None else pd.DataFrame()
        self.df_berita = pd.DataFrame()

        if not self.df_riwayat.empty:
            if "kategori" in self.df_riwayat.columns:
                cond = (self.df_riwayat["kategori"] == "berita")
                if "kategori_relevansi" in self.df_riwayat.columns:
                    cond = cond & (self.df_riwayat["kategori_relevansi"] == "insiden_spesifik")
                self.df_berita = self.df_riwayat[cond].copy()
            else:
                self.df_berita = self.df_riwayat.copy()

    def _extract_top_keywords(self, df: pd.DataFrame, top_n: int = 10) -> List[str]:
        """Ekstrak kata kunci dominan dari dataset secara dinamis."""
        all_keywords = []
        for _, row in df.iterrows():
            kws = str(row.get('kata_kunci', '')).split(',')
            for kw in kws:
                clean_kw = kw.strip().lower()
                if len(clean_kw) > 2:
                    all_keywords.append(clean_kw)
        
        if not all_keywords:
            return []
        return [k for k, v in Counter(all_keywords).most_common(top_n)]

    def retrieve_berita_semantic(self, query: str, limit: int = 5) -> List[tuple]:
        """
        Mengambil artikel berita paling relevan secara semantik menggunakan
        vector embeddings gemini-embedding-001 (Gemini Embedding 1) dan cosine similarity.
        Mengembalikan list of (score, sumber, judul, ringkasan, tanggal).
        """
        if self.df_berita.empty or not query:
            return []

        try:
            query_emb = GeminiLLMAdapter.embed_text(query)
            if not query_emb:
                return []

            results = []
            sample_df = self.df_berita.head(30)
            items_to_embed = []
            keys_to_embed = []
            for _, row in sample_df.iterrows():
                judul = str(row.get("judul", "")).strip()
                ringkasan = str(row.get("ringkasan_atau_narasi", "")).strip()
                tanggal = str(row.get("tanggal_publish", "")).split()[0]
                teks = f"{judul}. {ringkasan}".strip()
                cache_key = f"{judul}_{tanggal}"
                if cache_key not in _EMBEDDING_CACHE and teks:
                    items_to_embed.append(teks)
                    keys_to_embed.append(cache_key)

            if items_to_embed:
                batch_embs = GeminiLLMAdapter.embed_documents(items_to_embed, batch_size=50)
                for k, emb in zip(keys_to_embed, batch_embs):
                    if emb:
                        _EMBEDDING_CACHE[k] = emb

            for _, row in sample_df.iterrows():
                judul = str(row.get("judul", "")).strip()
                ringkasan = str(row.get("ringkasan_atau_narasi", "")).strip()
                sumber = str(row.get("sumber", "Media")).strip()
                tanggal = str(row.get("tanggal_publish", "")).split()[0]
                cache_key = f"{judul}_{tanggal}"
                doc_emb = _EMBEDDING_CACHE.get(cache_key)
                if doc_emb:
                    sim = _cosine_similarity(query_emb, doc_emb)
                    results.append((sim, sumber, judul, ringkasan, tanggal))

            results.sort(key=lambda x: x[0], reverse=True)
            return results[:limit]
        except Exception as e:
            logger.debug(f"Semantic embedding search bypassed: {e}")
            return []

    def map_incident_to_mitre_semantic(
        self,
        incident_title: str,
        incident_narrative: str = "",
        keywords: Optional[List[str]] = None,
        top_k: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Memetakan insiden siber ke taktik dan teknik MITRE ATT&CK secara semantik (Hybrid Multi-Stage RAG).
        Tahap 1: Mengambil taktik & teknik dari data/encyclopedia/mitre.json.
        Tahap 2: Menghitung vector similarity teks insiden terhadap teknik MITRE via text-embedding.
        Tahap 3: Fallback anggun ke RapidFuzz token matching jika embedding offline / kuota limit tercapai.
        Mengembalikan daftar taktik & teknik MITRE terverifikasi dengan skor kemiripan semantik.
        """
        from src.analytics.encyclopedia_lookup import load_encyclopedia
        from rapidfuzz import fuzz

        mitre_db = load_encyclopedia("mitre.json")
        if not mitre_db:
            return []

        query_text = f"{incident_title}. {incident_narrative}".strip()
        if keywords:
            query_text += f" Kata kunci: {', '.join(keywords)}"

        results = []

        # 1. Semantic Vector Retrieval menggunakan text-embedding & Cosine Similarity
        try:
            query_emb = GeminiLLMAdapter.embed_text(query_text[:1000])
            if query_emb:
                missing_keys = []
                missing_texts = []
                for entry in mitre_db:
                    tid = entry.get("id", "")
                    if tid and tid not in _MITRE_EMBEDDING_CACHE:
                        doc_text = f"MITRE {tid} {entry.get('technique', '')} ({entry.get('tactic', '')}). {', '.join(entry.get('keywords', []))}"
                        missing_keys.append(tid)
                        missing_texts.append(doc_text)

                if missing_texts:
                    batch_embs = GeminiLLMAdapter.embed_documents(missing_texts, batch_size=30)
                    for k, emb in zip(missing_keys, batch_embs):
                        if emb:
                            _MITRE_EMBEDDING_CACHE[k] = emb

                for entry in mitre_db:
                    tid = entry.get("id", "")
                    doc_emb = _MITRE_EMBEDDING_CACHE.get(tid)
                    if doc_emb:
                        sim = _cosine_similarity(query_emb, doc_emb)
                        results.append({
                            "id": tid,
                            "tactic": entry.get("tactic", "Enterprise"),
                            "technique": entry.get("technique", ""),
                            "score": round(sim, 3),
                            "method": "semantic_vector"
                        })
        except Exception as e:
            logger.debug(f"MITRE vector embedding search bypassed: {e}")

        # 2. Fallback Deterministik RapidFuzz Lexical Scoring
        if not results or (results and max(r["score"] for r in results) < 0.40):
            fuzzy_results = []
            q_lower = query_text.lower()
            for entry in mitre_db:
                kw_str = " ".join(entry.get("keywords", [])).lower()
                target_text = f"{entry.get('technique', '').lower()} {entry.get('tactic', '').lower()} {kw_str}"
                score_ratio = fuzz.token_set_ratio(q_lower, target_text) / 100.0

                for kw in entry.get("keywords", []):
                    if kw.lower() in q_lower:
                        score_ratio = min(1.0, score_ratio + 0.15)
                        break

                fuzzy_results.append({
                    "id": entry.get("id", ""),
                    "tactic": entry.get("tactic", "Enterprise"),
                    "technique": entry.get("technique", ""),
                    "score": round(score_ratio, 3),
                    "method": "lexical_fuzzy"
                })
            results = fuzzy_results

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def retrieve_berita_context(
        self,
        top_keywords: List[str],
        top_vectors: Optional[List[str]] = None,
        limit: int = 7
    ) -> str:
        """
        Mengambil sampel artikel berita asli paling relevan berdasarkan kecocokan
        semantik (vector embeddings) dan frekuensi kata kunci tren (lexical).
        """
        if self.df_berita.empty:
            return "(Tidak ada korpus berita pada database)"

        # Bersihkan list kata kunci pencarian
        kw_set = [k.lower().strip() for k in top_keywords if k and len(k.strip()) > 2]
        vector_set = [v.lower().strip() for v in (top_vectors or []) if v]

        # 1. Coba Semantic Vector Retrieval lebih dulu
        query_gabung = " ".join(kw_set[:5] + vector_set[:3])
        if query_gabung:
            semantic_matches = self.retrieve_berita_semantic(query_gabung, limit=limit)
            if semantic_matches and semantic_matches[0][0] >= 0.65:
                judul_terpilih = set()
                chunks = []
                preview_max = _ambil_batas_preview_berita()
                for sim, sumber, judul, ringkasan, tanggal in semantic_matches:
                    if judul in judul_terpilih:
                        continue
                    judul_terpilih.add(judul)
                    ringkas_teks = ringkasan[:preview_max] + ("..." if len(ringkasan) > preview_max else "") if ringkasan else judul
                    chunks.append(f"- [{sumber} | {tanggal}] \"{judul}\": {ringkas_teks}")
                    if len(chunks) >= limit:
                        break
                if chunks:
                    return "\n".join(chunks)

        # 2. Fallback Lexical Scoring jika embedding belum aktif / similarity rendah
        scored_articles = []
        for _, row in self.df_berita.iterrows():
            judul = str(row.get("judul", "")).strip()
            ringkasan = str(row.get("ringkasan_atau_narasi", "")).strip()
            kata_kunci = str(row.get("kata_kunci", "")).strip()
            sumber = str(row.get("sumber", "Media")).strip()

            teks_gabung = f"{judul} {ringkasan} {kata_kunci}".lower()

            score = 0
            # Pembobotan defensif terhadap None
            rag_cfg = ((ConfigLoader.get_config() or {}).get("cti_analysis") or {}).get("rag") or {}
            scoring_cfg = rag_cfg.get("scoring") or {}
            w_title = scoring_cfg.get("title_match_weight", 3)
            w_body = scoring_cfg.get("body_match_weight", 1)
            w_vector = scoring_cfg.get("vector_match_weight", 1)

            for kw in kw_set:
                if kw in judul.lower():
                    score += w_title
                elif kw in teks_gabung:
                    score += w_body

            for vec in vector_set:
                if vec in teks_gabung:
                    score += w_vector

            if score > 0:
                tanggal = str(row.get("tanggal_publikasi", "Tanggal tidak diketahui")).split()[0]
                scored_articles.append((score, sumber, judul, ringkasan, tanggal))

        # Urutkan berdasarkan relevansi skor tertinggi
        scored_articles.sort(key=lambda x: x[0], reverse=True)

        # Ambil deduplikasi judul agar beragam
        judul_terpilih = set()
        chunks = []
        preview_max = _ambil_batas_preview_berita()
        for _, sumber, judul, ringkasan, tanggal in scored_articles:
            if judul in judul_terpilih:
                continue
            judul_terpilih.add(judul)

            ringkas_teks = ringkasan[:preview_max] + ("..." if len(ringkasan) > preview_max else "") if ringkasan else judul
            chunks.append(f"- [{sumber} | {tanggal}] \"{judul}\": {ringkas_teks}")

            if len(chunks) >= limit:
                break

        if not chunks:
            # Fallback ke artikel terkini
            for _, row in self.df_berita.head(limit).iterrows():
                sumber = row.get("sumber", "Media")
                tanggal = str(row.get("tanggal_publikasi", "Tanggal tidak diketahui")).split()[0]
                judul = row.get("judul", "-")
                ringkas_teks = str(row.get("ringkasan_atau_narasi", ""))[:200]
                chunks.append(f"- [{sumber} | {tanggal}] \"{judul}\": {ringkas_teks}")

        return "\n".join(chunks)



    def retrieve_regional_context(self, cluster_items: List[Dict], wilayah_label: str, limit: int = 10) -> str:
        """
        Menyusun korpus fakta artikel riil untuk analisis makro ancaman wilayah (RAG).
        """
        if not cluster_items:
            return f"(Tidak ada insiden siber aktif pada wilayah {wilayah_label} dalam database)"

        chunks = []
        preview_max = _ambil_batas_preview_berita()
        for c in cluster_items[:limit]:
            sumber = c.get("sumber", "Media")
            judul = c.get("judul", "-")
            ringkasan = c.get("ringkasan", "")
            tgl = c.get("tanggal", "")
            liputan = c.get("jumlah_liputan", 1)
            media_lain = f" + media lain ({', '.join(c.get('media_lain', [])[:2])})" if c.get("media_lain") else ""
            link = c.get("link", "#")

            ringkas_teks = ringkasan[:preview_max] + ("..." if len(ringkasan) > preview_max else "") if ringkasan else judul
            chunks.append(
                f"- [{sumber} | {tgl} | Liputan: {liputan} media{media_lain}] \"{judul}\"\n"
                f"  Konteks Insiden: {ringkas_teks}\n"
                f"  Link: {link}"
            )

        return "\n".join(chunks)

    def hitung_prediksi_pola_serangan(self) -> Dict[str, Any]:
        """
        Menganalisis data historis untuk mengidentifikasi 1 kategori taksonomi insiden
        yang dominan minggu ini berdasarkan agregasi 11 kategori tertutup eCSIRT,
        lengkap dengan jumlah terkini, growth persen, dan subteks 'vs minggu lalu'.
        """
        fallback = {
            "pola": "Akses Tidak Sah / Pembobolan Akun",
            "pola_lengkap": "Akses Tidak Sah / Pembobolan Akun",
            "kategori_taksonomi": "akses_tidak_sah",
            "growth_persen": 0.0,
            "jumlah_terkini": 0,
            "tingkat_risiko": "SEDANG",
            "subteks": "vs minggu lalu",
            "taksonomi_resmi": "Akses Tidak Sah / Pembobolan Akun"
        }

        if self.df_berita.empty:
            return fallback

        from src.analytics.trend_analyzer import _dedup_ringan_lintas_hari, _hitung_growth

        df_dedup = _dedup_ringan_lintas_hari(self.df_berita)
        df_terkini, df_baseline = _bagi_periode_terkini_baseline(df_dedup)

        cat_terkini = Counter()
        for _, r in df_terkini.iterrows():
            cat = resolve_article_taxonomy_category(r)
            cat_terkini[cat] += 1

        cat_baseline = Counter()
        for _, r in df_baseline.iterrows():
            cat = resolve_article_taxonomy_category(r)
            cat_baseline[cat] += 1

        # Pilih kategori dominan. Prioritaskan kategori spesifik dibanding 'tidak_dapat_ditentukan' atau 'lainnya'
        kandidat = []
        for cat in CLOSED_11_TAXONOMY_CATEGORIES:
            cnt_cur = cat_terkini.get(cat, 0)
            if cnt_cur == 0:
                continue
            cnt_base = cat_baseline.get(cat, 0)
            growth = _hitung_growth(cnt_cur, cnt_base)
            is_generic = cat in ["tidak_dapat_ditentukan", "lainnya"]
            kandidat.append({
                "kategori": cat,
                "cnt_cur": cnt_cur,
                "cnt_base": cnt_base,
                "growth": growth,
                "is_generic": is_generic
            })

        if not kandidat:
            return fallback

        # Urutkan berdasarkan spesifik (non-generic dulu), lalu volume terbanyak (cnt_cur), lalu growth
        kandidat.sort(key=lambda x: (not x["is_generic"], x["cnt_cur"], x["growth"]), reverse=True)
        top = kandidat[0]

        dominant_cat = top["kategori"]
        dominant_display_name = TAXONOMY_DISPLAY_NAMES.get(dominant_cat, dominant_cat)
        growth_val = top["growth"]
        cnt_val = top["cnt_cur"]

        return {
            "pola": dominant_display_name,
            "pola_lengkap": dominant_display_name,
            "kategori_taksonomi": dominant_cat,
            "growth_persen": int(growth_val),
            "jumlah_terkini": cnt_val,
            "tingkat_risiko": "TINGGI" if growth_val >= 20.0 else "SEDANG",
            "subteks": "vs minggu lalu",
            "taksonomi_resmi": dominant_display_name
        }

    def hitung_prediksi_ancaman_baru(self) -> str:
        """
        Mengembalikan nama kategori taksonomi insiden baru yang sedang naik (emerging threat)
        dengan syarat ketat minimal >= 2 kasus di periode terkini dan memiliki sinyal kebaruan
        (novelty > volume). Jika tidak ada kategori yang memenuhi syarat, mengembalikan 'Kondisi Stabil'.
        """
        if self.df_berita.empty:
            return "Kondisi Stabil"

        ancaman = self.ambil_berita_ancaman_baru()
        if not ancaman.get("ada"):
            return "Kondisi Stabil"

        return ancaman.get("nama") or ancaman.get("jenis_serangan") or "Kondisi Stabil"

    def ambil_data_tren_makro_spiking(self) -> Dict[str, Any]:
        """
        Mengambil data lengkap untuk Bagian 1 (INSIDEN MELONJAK DRASTIS) yang 100% sinkron
        dengan hasil kartu KPI [ POLA ANCAMAN ] (hitung_prediksi_pola_serangan).
        Mengumpulkan seluruh berita dari kategori [ POLA ANCAMAN ] minggu ini dan mengekstrak
        fakta RAG lengkap (kejadiannya apa, aktornya siapa, siapa yang terdampak, kejadiannya bagaimana,
        alur insidennya bagaimana, dan dampaknya apa) untuk dinarasikan secara paragraf.
        """
        if self.df_berita.empty:
            return {
                "nama_pola": "Insiden Siber Terkini",
                "kategori_taksonomi": "akses_tidak_sah",
                "growth_persen": 0.0,
                "jumlah_artikel": 0,
                "korpus_artikel": "(Tidak ada data insiden riil dalam database)",
                "fakta_rag": extract_structured_rag_facts([], "Insiden Siber Terkini"),
            }

        from src.analytics.trend_analyzer import _dedup_ringan_lintas_hari

        pola_kpi = self.hitung_prediksi_pola_serangan()
        dominant_cat = pola_kpi.get("kategori_taksonomi", "akses_tidak_sah")
        dominant_display = pola_kpi.get("pola", TAXONOMY_DISPLAY_NAMES.get(dominant_cat, dominant_cat))
        growth_val = float(pola_kpi.get("growth_persen", 0.0))

        df_dedup = _dedup_ringan_lintas_hari(self.df_berita)
        df_terkini, _ = _bagi_periode_terkini_baseline(df_dedup)
        if df_terkini.empty:
            df_terkini = df_dedup

        from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
        from rapidfuzz import fuzz

        arts_pola = []
        for _, r in df_terkini.iterrows():
            if resolve_article_taxonomy_category(r) == dominant_cat:
                arts_pola.append(r)

        if not arts_pola:
            arts_pola = [r for _, r in df_terkini.head(5).iterrows()]

        # Cluster artikel dalam kategori dominan untuk mengambil 1 KASUS yang paling banyak
        clusters_makro = []
        sudah_makro = set()
        for i in range(len(arts_pola)):
            if i in sudah_makro:
                continue
            row_i = arts_pola[i]
            data_i = row_i.to_dict() if hasattr(row_i, "to_dict") else dict(row_i)
            cl_j_i, _ = _bersihkan_judul_dan_publisher(str(data_i.get("judul", "")), "")
            c_arts = [row_i]
            sudah_makro.add(i)
            for j in range(i + 1, len(arts_pola)):
                if j in sudah_makro:
                    continue
                row_j = arts_pola[j]
                data_j = row_j.to_dict() if hasattr(row_j, "to_dict") else dict(row_j)
                cl_j_j, _ = _bersihkan_judul_dan_publisher(str(data_j.get("judul", "")), "")
                if fuzz.token_set_ratio(cl_j_i.lower(), cl_j_j.lower()) >= 52:
                    sudah_makro.add(j)
                    c_arts.append(row_j)
            clusters_makro.append({"judul_utama": cl_j_i, "artikel_list": c_arts})

        clusters_makro.sort(key=lambda x: len(x["artikel_list"]), reverse=True)
        top_makro = clusters_makro[0] if clusters_makro else {"judul_utama": dominant_display, "artikel_list": arts_pola}
        arts_top_kasus = top_makro["artikel_list"]
        nama_kasus_makro = top_makro["judul_utama"]

        fakta_rag = extract_structured_rag_facts(arts_top_kasus, nama_kasus_makro)

        return {
            "nama_kasus": nama_kasus_makro,
            "nama_pola": dominant_display,
            "kategori_taksonomi": dominant_cat,
            "kategori_display": dominant_display,
            "growth_persen": growth_val,
            "jumlah_artikel": len(arts_top_kasus),
            "korpus_artikel": fakta_rag["korpus_terstruktur"],
            "fakta_rag": fakta_rag,
            "artikel_list": [r.to_dict() if hasattr(r, "to_dict") else dict(r) for r in arts_top_kasus],
        }

    def ambil_top3_insiden_mikro(self, exclude_dominant_pola: bool = True) -> List[Dict[str, Any]]:
        """
        Mengambil TOP 3 tren insiden yang paling banyak dalam minggu ini (kecuali kategori/insiden
        yang sudah naik drastis di [ POLA ANCAMAN ] / INSIDEN MELONJAK DRASTIS), lengkap dengan
        ekstraksi RAG terstruktur (siapa aktornya, apa dampaknya, siapa yang terdampak, di mana
        kejadiannya, gambaran besar insiden, senjata, alur serangan) serta pemetaan MITRE ATT&CK,
        MITRE D3FEND, dan NIST untuk setiap tren.
        """
        if self.df_berita.empty:
            return []

        from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher, _dedup_ringan_lintas_hari
        from rapidfuzz import fuzz

        df_dedup = _dedup_ringan_lintas_hari(self.df_berita)
        df_terkini, _ = _bagi_periode_terkini_baseline(df_dedup)
        if df_terkini.empty:
            df_terkini = df_dedup

        unclustered = df_terkini.to_dict("records")

        # Filter berita penegakan hukum (penangkapan/vonis hacker) agar Section 2 murni berisi serangan siber aktif
        unclustered_aktif = [r for r in unclustered if not is_berita_penegakan_hukum(r)]
        if unclustered_aktif:
            unclustered = unclustered_aktif

        # Kecualikan kasus yang sudah dibahas pada INSIDEN MELONJAK DRASTIS (Bagian 1)
        if exclude_dominant_pola:
            data_makro = self.ambil_data_tren_makro_spiking()
            makro_arts = data_makro.get("artikel_list", [])
            makro_titles = [
                _bersihkan_judul_dan_publisher(str(dr.get("judul", "")), "")[0].lower()
                for dr in makro_arts
            ]
            non_makro_cases = []
            for r in unclustered:
                title_r, _ = _bersihkan_judul_dan_publisher(str(r.get("judul", "")), "")
                if makro_titles and any(fuzz.token_set_ratio(title_r.lower(), mt) >= 60 for mt in makro_titles):
                    continue
                non_makro_cases.append(r)
            if non_makro_cases:
                unclustered = non_makro_cases

        # Cluster artikel berdasarkan KASUS (Incident Case Clustering)
        daftar_klaster = []
        sudah_diproses = set()

        for i in range(len(unclustered)):
            if i in sudah_diproses:
                continue
            row_i = unclustered[i]
            raw_j_i = str(row_i.get("judul", "")).strip()
            kw_i = str(row_i.get("kata_kunci", "")).strip()
            clean_j_i, _ = _bersihkan_judul_dan_publisher(raw_j_i, "")
            cat_i = resolve_article_taxonomy_category(row_i)

            artikel_klaster = [row_i]
            sudah_diproses.add(i)

            for j in range(i + 1, len(unclustered)):
                if j in sudah_diproses:
                    continue
                row_j = unclustered[j]
                raw_j_j = str(row_j.get("judul", "")).strip()
                clean_j_j, _ = _bersihkan_judul_dan_publisher(raw_j_j, "")

                if fuzz.token_set_ratio(clean_j_i.lower(), clean_j_j.lower()) >= 55:
                    sudah_diproses.add(j)
                    artikel_klaster.append(row_j)

            cat_display = TAXONOMY_DISPLAY_NAMES.get(cat_i, "Insiden Siber")
            cnt_spesifik = sum(1 for r in artikel_klaster if r.get("kategori_relevansi") == "insiden_spesifik")
            is_quote = any(q in clean_j_i.lower() for q in ["bill gates", "komisi i", "dpr", "peringatkan", "minta", "hanya 2 dari 10", "tips bikin"])

            daftar_klaster.append({
                "judul_utama": clean_j_i,
                "nama_kampanye": clean_j_i,
                "kategori_taksonomi": cat_i,
                "kategori_display": cat_display,
                "artikel_list": artikel_klaster,
                "jumlah_artikel": len(artikel_klaster),
                "is_actual": cnt_spesifik > 0 and not is_quote,
            })

        # Urutkan berdasarkan kasus serangan nyata, lalu jumlah berita terbanyak
        daftar_klaster.sort(key=lambda x: (x["is_actual"], x["jumlah_artikel"]), reverse=True)

        top3 = daftar_klaster[:3]

        from src.analytics.encyclopedia_lookup import search_encyclopedia_per_incident

        hasil_top3 = []
        for idx, cl in enumerate(top3):
            semua_teks = []
            kata_kunci_set = set()
            for art in cl["artikel_list"]:
                j = str(art.get("judul", ""))
                r = str(art.get("ringkasan_atau_narasi", ""))
                k = str(art.get("kata_kunci", ""))
                semua_teks.append(f'• Kasus/Laporan: "{j}"\n  Detail Kronologi & Cara Serangan: {r}')
                for item_k in k.split(","):
                    if item_k.strip():
                        kata_kunci_set.add(item_k.strip())

            gabungan_narasi = "\n".join(semua_teks[:5])
            fakta_rag = extract_structured_rag_facts(cl["artikel_list"], cl["nama_kampanye"])
            mitigasi_list = search_encyclopedia_per_incident(cl["nama_kampanye"], list(kata_kunci_set))
            mitre_mapping = self.map_incident_to_mitre_semantic(
                incident_title=cl["nama_kampanye"],
                incident_narrative=gabungan_narasi,
                keywords=list(kata_kunci_set),
                top_k=2,
            )

            hasil_top3.append({
                "urutan": idx + 1,
                "nama_insiden": cl["nama_kampanye"],
                "kategori_taksonomi": cl.get("kategori_taksonomi"),
                "jumlah_artikel": cl["jumlah_artikel"],
                "uraian_fakta": gabungan_narasi,
                "fakta_rag": fakta_rag,
                "kata_kunci": list(kata_kunci_set),
                "mitigasi_ensiklopedia": mitigasi_list,
                "mitre_mapping": mitre_mapping,
                "artikel_list": cl["artikel_list"],
            })

        return hasil_top3

    def ambil_berita_ancaman_baru(self) -> Dict[str, Any]:
        """
        Mengidentifikasi sinyal ancaman baru (emerging threats, novel malware, zero-day)
        berbasis kategori taksonomi dari korpus berita terkini untuk kartu KPI [ SINYAL ANCAMAN BARU ]
        dan Bagian 5 (PREDIKSI TREN ANCAMAN SIBER).
        Syarat mutlak:
        1. Kategori harus memiliki >= 2 kasus di periode terkini (cnt_cur >= 2). 1 kasus DITOLAK.
        2. Evaluasi skor kebaruan (novelty score): kategori baru (baseline == 0 atau lonjakan growth >= 200%)
           didukung kata kunci kebaruan.
        3. Novelty > volume: kategori baru dengan >= 2 kasus mengalahkan kategori lama dengan volume lebih tinggi.
        4. Menyertakan ekstraksi fakta_rag & korpus_artikel seluruh berita pada kategori ancaman baru tersebut
           agar Bagian 5 dapat dinarasikan secara paragraf dengan struktur yang sama seperti Bagian 1.
        """
        fallback_stabil = {
            "ada": False,
            "nama": "Kondisi Stabil",
            "jenis_serangan": "Kondisi Stabil",
            "kategori": None,
            "uraian": "(Tidak ada ancaman baru yang terdeteksi dengan minimal 2 kasus)",
            "korpus_artikel": "",
            "fakta_rag": extract_structured_rag_facts([], "Kondisi Stabil"),
            "sumber": "-",
            "judul": "-",
            "jumlah_kasus": 0,
            "growth_persen": 0.0,
        }

        if self.df_berita.empty:
            return fallback_stabil

        from src.analytics.trend_analyzer import _dedup_ringan_lintas_hari, _hitung_growth
        df_dedup = _dedup_ringan_lintas_hari(self.df_berita)
        df_terkini, df_baseline = _bagi_periode_terkini_baseline(df_dedup)

        cat_articles_terkini: Dict[str, List[Any]] = {}
        for _, r in df_terkini.iterrows():
            cat = resolve_article_taxonomy_category(r)
            cat_articles_terkini.setdefault(cat, []).append(r)

        cat_baseline = Counter()
        for _, r in df_baseline.iterrows():
            cat = resolve_article_taxonomy_category(r)
            cat_baseline[cat] += 1

        NOVELTY_KEYWORDS = [
            "baru", "novel", "emerging", "modus baru", "zero-day", "0-day",
            "cve", "lonjakan", "kritis", "varian baru", "ancaman baru",
            "spionase", "serangan baru", "tren baru", "peringatan"
        ]

        qualifying_novel = []

        for cat, arts in cat_articles_terkini.items():
            if cat in ["tidak_dapat_ditentukan", "lainnya"]:
                continue

            cnt_cur = len(arts)
            if cnt_cur < 2:
                continue

            cnt_base = cat_baseline.get(cat, 0)
            growth = _hitung_growth(cnt_cur, cnt_base)

            kw_hits = 0
            for art in arts:
                txt = (
                    str(art.get("judul", "")) + " " +
                    str(art.get("ringkasan_atau_narasi", "")) + " " +
                    str(art.get("kata_kunci", ""))
                ).lower()
                if any(w in txt for w in NOVELTY_KEYWORDS):
                    kw_hits += 1

            is_novel = False
            base_novelty = 0.0

            if cnt_base == 0:
                if df_baseline.empty:
                    if kw_hits > 0:
                        is_novel = True
                        base_novelty = 100.0
                else:
                    is_novel = True
                    base_novelty = 100.0
            elif growth >= 200.0:
                is_novel = True
                base_novelty = 50.0 + min(growth, 50.0)

            if not is_novel:
                continue

            novelty_score = (base_novelty * (1.0 + 0.5 * kw_hits)) + (cnt_cur * 0.1)

            qualifying_novel.append({
                "kategori": cat,
                "novelty_score": novelty_score,
                "cnt_cur": cnt_cur,
                "growth": growth,
                "articles": arts,
            })

        if not qualifying_novel:
            return fallback_stabil

        dominant_cat = self.hitung_prediksi_pola_serangan().get("kategori_taksonomi")
        non_dominant_novel = [q for q in qualifying_novel if q["kategori"] != dominant_cat]
        if non_dominant_novel:
            non_dominant_novel.sort(key=lambda x: x["novelty_score"], reverse=True)
            top = non_dominant_novel[0]
        else:
            qualifying_novel.sort(key=lambda x: x["novelty_score"], reverse=True)
            top = qualifying_novel[0]
        from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
        from rapidfuzz import fuzz

        top_cat = top["kategori"]
        display_name = TAXONOMY_DISPLAY_NAMES.get(top_cat, top_cat)
        arts_novel = top["articles"]

        # Cluster artikel ancaman baru untuk memilih 1 KASUS ancaman baru paling banyak
        c_novel = []
        sudah_n = set()
        for i in range(len(arts_novel)):
            if i in sudah_n:
                continue
            r_i = arts_novel[i]
            d_i = r_i.to_dict() if hasattr(r_i, "to_dict") else dict(r_i)
            cj_i, _ = _bersihkan_judul_dan_publisher(str(d_i.get("judul", "")), "")
            c_arts = [r_i]
            sudah_n.add(i)
            for j in range(i + 1, len(arts_novel)):
                if j in sudah_n:
                    continue
                r_j = arts_novel[j]
                d_j = r_j.to_dict() if hasattr(r_j, "to_dict") else dict(r_j)
                cj_j, _ = _bersihkan_judul_dan_publisher(str(d_j.get("judul", "")), "")
                if fuzz.token_set_ratio(cj_i.lower(), cj_j.lower()) >= 52:
                    sudah_n.add(j)
                    c_arts.append(r_j)
            c_novel.append({"judul_utama": cj_i, "artikel_list": c_arts})

        c_novel.sort(key=lambda x: len(x["artikel_list"]), reverse=True)
        top_novel_case = c_novel[0] if c_novel else {"judul_utama": display_name, "artikel_list": arts_novel}
        top_row = top_novel_case["artikel_list"][0]
        nama_kasus_novel = top_novel_case["judul_utama"]
        fakta_rag = extract_structured_rag_facts(top_novel_case["artikel_list"], nama_kasus_novel)

        return {
            "ada": True,
            "nama": display_name,
            "nama_kasus": nama_kasus_novel,
            "kategori": top_cat,
            "jenis_serangan": display_name,
            "uraian": str(top_row.get("ringkasan_atau_narasi", "")),
            "korpus_artikel": fakta_rag["korpus_terstruktur"],
            "fakta_rag": fakta_rag,
            "artikel_list": [r.to_dict() if hasattr(r, "to_dict") else dict(r) for r in top_novel_case["artikel_list"]],
            "sumber": str(top_row.get("sumber", "Media Intelijen")),
            "judul": str(top_row.get("judul", "-")),
            "jumlah_kasus": len(top_novel_case["artikel_list"]),
            "growth_persen": top["growth"],
        }
