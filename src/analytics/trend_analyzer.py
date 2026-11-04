"""
Analisis tren statistik dari riwayat_tren (14 hari terakhir). Modul ini
MURNI perhitungan Python (tanpa LLM) - tugasnya menghasilkan angka yang
pasti dan bisa diverifikasi, sebagai dasar objektif sebelum dinarasikan
oleh LLM di modul trend_predictor.py.

Prinsip pembagian periode: window 14 hari dibagi jadi
- periode TERKINI: 7 hari terakhir
- periode BASELINE: 7 hari sebelumnya
Growth dihitung dari rata-rata HARIAN (bukan total mentah).
"""
from collections import Counter
from datetime import datetime
import re
from typing import Any, Dict, List, Optional
from rapidfuzz import fuzz

import pandas as pd
from src.utils.config_loader import ConfigLoader

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

HARI_PERIODE_TERKINI = 7
THRESHOLD_DEDUP_TREN = 88  
HARI_PERIODE_BASELINE = 7  # total window 14 hari (7 terkini + 7 baseline)

_SUMBER_INTERNASIONAL = set(ConfigLoader.get_rules("sumber_internasional"))
VEKTOR_RULES = ConfigLoader.get_rules("vektor_rules")
SEKTOR_RULES = ConfigLoader.get_rules("sektor_rules")


def _split_periode(df: pd.DataFrame, kolom_tanggal: str = "tanggal_publish") -> tuple:
    """Membagi df jadi 2 subset: periode terkini (7 tanggal unik terbaru) vs baseline (7 tanggal unik sebelumnya)."""
    if df.empty:
        return df, df

    df = df.copy()
    col_tgl = kolom_tanggal if kolom_tanggal in df.columns else ("tanggal_dicatat" if "tanggal_dicatat" in df.columns else None)
    if col_tgl is None:
        return df, pd.DataFrame(columns=df.columns)
    tgl_series = df[col_tgl].fillna("").astype(str).str.slice(0, 10)
    tanggal_unik = sorted(tgl_series[tgl_series.str.match(r"^\d{4}-\d{2}-\d{2}$")].unique(), reverse=True)

    if not tanggal_unik:
        return df, df

    tanggal_terkini = set(tanggal_unik[:HARI_PERIODE_TERKINI])
    tanggal_baseline = set(tanggal_unik[HARI_PERIODE_TERKINI:HARI_PERIODE_TERKINI + HARI_PERIODE_BASELINE])

    df_terkini = df[tgl_series.isin(tanggal_terkini)].copy()
    df_baseline = df[tgl_series.isin(tanggal_baseline)].copy()
    return df_terkini, df_baseline


def _hitung_growth(jumlah_terkini: int, jumlah_baseline: int) -> float:
    """
    Persentase growth dari rata-rata harian baseline ke rata-rata harian terkini.
    Mengatasi small-base distortion:
    - Jika baseline == 0 dan terkini >= 2, dihitung sebagai kemunculan baru terkonfirmasi (100% per unit tambahan, maks 500%).
    - Jika baseline == 0 dan terkini < 2 (hanya 1 artikel terisolasi), dihitung 0.0% agar tidak menimbulkan alarm lonjakan palsu.
    """
    rata_terkini = jumlah_terkini / HARI_PERIODE_TERKINI
    rata_baseline = jumlah_baseline / HARI_PERIODE_BASELINE

    if rata_baseline == 0:
        if jumlah_terkini >= 2:
            return round(min(100.0 * (jumlah_terkini - 1), 500.0), 1)
        return 0.0
    return round(((rata_terkini - rata_baseline) / rata_baseline) * 100, 1)

def _dedup_ringan_lintas_hari(df_berita: pd.DataFrame, kolom_judul: str = "judul") -> pd.DataFrame:
    """
    Dedup RINGAN khusus untuk PERHITUNGAN TREN - supaya 1 insiden yang
    di-follow-up berkali-kali dalam beberapa hari (mis. "Bank X diretas"
    lalu "Update: Bank X akui data bocor") tidak dihitung sebagai banyak
    insiden terpisah dan membuat angka growth kata kunci bias naik.

    PENTING: ini TIDAK mengubah/menghapus apa pun di riwayat_tren atau
    tab Arsip - fungsi ini cuma bikin salinan sementara yang dipakai
    SAAT menghitung statistik tren saja. Representatif yang diambil
    adalah kemunculan PALING AWAL (bukan follow-up terakhir), supaya
    tren mencerminkan kapan topik itu mulai muncul.

    Pakai rapidfuzz (perbandingan string murah), BUKAN embedding LLM -
    supaya tidak menambah beban komputasi API tiap kali statistik dihitung.
    """
    if df_berita.empty or len(df_berita) <= 1:
        return df_berita

    kolom_tgl = "tanggal_publish" if "tanggal_publish" in df_berita.columns else "tanggal_dicatat"
    df_berita = df_berita.sort_values(kolom_tgl).reset_index(drop=True)
    sudah_diproses = set()
    baris_representatif = []

    for i in range(len(df_berita)):
        if i in sudah_diproses:
            continue
        judul_i = str(df_berita.loc[i, kolom_judul] or "")
        nums_i = re.findall(r"\d+", judul_i)
        tgl_i_str = str(df_berita.loc[i, kolom_tgl] or "")[:10] if kolom_tgl in df_berita.columns else ""
        baris_representatif.append(df_berita.loc[i].to_dict())
        sudah_diproses.add(i)

        for j in range(i + 1, len(df_berita)):
            if j in sudah_diproses:
                continue
            if tgl_i_str and kolom_tgl in df_berita.columns:
                tgl_j_str = str(df_berita.loc[j, kolom_tgl] or "")[:10]
                if len(tgl_i_str) == 10 and len(tgl_j_str) == 10:
                    try:
                        d_i = datetime.strptime(tgl_i_str, "%Y-%m-%d")
                        d_j = datetime.strptime(tgl_j_str, "%Y-%m-%d")
                        if abs((d_j - d_i).days) > 7:
                            continue
                    except ValueError:
                        pass
            judul_j = str(df_berita.loc[j, kolom_judul] or "")
            nums_j = re.findall(r"\d+", judul_j)
            if nums_i and nums_j and nums_i != nums_j:
                continue
            if fuzz.token_sort_ratio(judul_i, judul_j) >= THRESHOLD_DEDUP_TREN:
                sudah_diproses.add(j)  # dianggap follow-up insiden yang sama

    df_hasil = pd.DataFrame(baris_representatif)
    if len(df_hasil) < len(df_berita):
        logger.info(
            f"Dedup ringan untuk tren: {len(df_berita)} -> {len(df_hasil)} artikel unik "
            f"(follow-up insiden yang sama dalam 7 hari digabung)."
        )
    return df_hasil


def hitung_tren_kata_kunci_berita(
    df_riwayat: pd.DataFrame, top_n: int = 10, df_berita_dedup: Optional[pd.DataFrame] = None
) -> List[Dict]:
    """
    Menghitung tren kemunculan tiap kata kunci individual dari kolom
    'kata_kunci' (string dipisah koma) pada baris berkategori 'berita'.
    Mengembalikan top-N kata kunci dengan growth tertinggi.
    """
    if df_berita_dedup is not None:
        df_berita = df_berita_dedup
    else:
        df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
        if df_berita.empty:
            return []
        df_berita = _dedup_ringan_lintas_hari(df_berita)   

    if df_berita.empty:
        return []

    df_terkini, df_baseline = _split_periode(df_berita)

    def _hitung_per_kata_kunci(df_subset: pd.DataFrame) -> Dict[str, int]:
        counter: Dict[str, int] = {}
        for daftar_str in df_subset["kata_kunci"].dropna():
            for kk in [k.strip() for k in daftar_str.split(",") if k.strip()]:
                counter[kk] = counter.get(kk, 0) + 1
        return counter

    hitung_terkini = _hitung_per_kata_kunci(df_terkini)
    hitung_baseline = _hitung_per_kata_kunci(df_baseline)

    semua_kata_kunci = set(hitung_terkini) | set(hitung_baseline)
    hasil = []
    for kk in semua_kata_kunci:
        jumlah_terkini = hitung_terkini.get(kk, 0)
        jumlah_baseline = hitung_baseline.get(kk, 0)
        # Hanya tampilkan kata kunci yang masih aktif di periode terkini,
        # supaya tidak melaporkan "tren naik" untuk sesuatu yang sudah hilang.
        if jumlah_terkini == 0:
            continue
        hasil.append({
            "kata_kunci": kk,
            "jumlah_terkini": jumlah_terkini,
            "jumlah_baseline": jumlah_baseline,
            "growth_persen": _hitung_growth(jumlah_terkini, jumlah_baseline),
        })

    hasil.sort(key=lambda x: (x["growth_persen"] > 0, x["growth_persen"], x["jumlah_terkini"]), reverse=True)
    return hasil[:top_n]


def hitung_tren_kategori_berita(
    df_riwayat: pd.DataFrame, df_berita_dedup: Optional[pd.DataFrame] = None
) -> Dict:
    """
    Tren jumlah insiden_spesifik vs analisis_relevan antara periode
    terkini vs baseline - indikator kasar apakah volume insiden NYATA
    (bukan cuma pembahasan umum) sedang naik.
    """
    if df_berita_dedup is not None:
        df_berita = df_berita_dedup
    else:
        df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
        if df_berita.empty:
            return {"insiden_spesifik": None, "analisis_relevan": None}
        df_berita = _dedup_ringan_lintas_hari(df_berita)

    if df_berita.empty:
        return {"insiden_spesifik": None, "analisis_relevan": None}

    df_terkini, df_baseline = _split_periode(df_berita)
    hasil = {}
    for kat in ("insiden_spesifik", "analisis_relevan"):
        jumlah_terkini = int((df_terkini["kategori_relevansi"] == kat).sum())
        jumlah_baseline = int((df_baseline["kategori_relevansi"] == kat).sum())
        hasil[kat] = {
            "jumlah_terkini": jumlah_terkini,
            "jumlah_baseline": jumlah_baseline,
            "growth_persen": _hitung_growth(jumlah_terkini, jumlah_baseline),
        }
    return hasil

def ambil_sampel_judul_insiden(
    df_riwayat: pd.DataFrame, maks: int = 15, df_berita_dedup: Optional[pd.DataFrame] = None
) -> List[Dict]:
    """
    Mengambil sampel judul artikel insiden_spesifik dari periode TERKINI
    (7 hari terakhir), sudah di-dedup ringan supaya 1 insiden yang
    di-follow-up berkali-kali tidak mendominasi sampel. Dipakai sebagai
    konteks KONKRET untuk LLM mengenali JENIS pola insiden - bukan cuma
    angka kata kunci abstrak.
    """
    if df_berita_dedup is not None:
        df_berita = df_berita_dedup
    else:
        df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
        if df_berita.empty:
            return []
        df_berita = _dedup_ringan_lintas_hari(df_berita)

    if df_berita.empty:
        return []

    df_terkini, _ = _split_periode(df_berita)
    df_insiden = df_terkini[df_terkini["kategori_relevansi"] == "insiden_spesifik"]

    return [
        {"judul": row["judul"], "sumber": row["sumber"]}
        for _, row in df_insiden.head(maks).iterrows()
    ]


def _kata_kunci_cocok(kata: str, teks: str) -> bool:
    if not kata or not teks:
        return False
    return bool(re.search(rf"\b{re.escape(kata.lower())}\b", teks))


def hitung_tren_vektor_serangan(
    df_riwayat: pd.DataFrame, df_berita_dedup: Optional[pd.DataFrame] = None
) -> List[Dict]:
    if df_berita_dedup is not None:
        df_berita = df_berita_dedup
    else:
        df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
        if df_berita.empty:
            return []
        df_berita = _dedup_ringan_lintas_hari(df_berita)

    if df_berita.empty:
        return []

    vektor_counts = {v: 0 for v in VEKTOR_RULES}
    for _, row in df_berita.iterrows():
        teks = (str(row.get("judul", "")) + " " + str(row.get("ringkasan_atau_narasi", "")) + " " + str(row.get("kata_kunci", ""))).lower()
        for v_nama, v_words in VEKTOR_RULES.items():
            if any(_kata_kunci_cocok(w, teks) for w in v_words):
                vektor_counts[v_nama] += 1

    hasil = [{"vektor": v, "jumlah": c} for v, c in vektor_counts.items()]
    hasil.sort(key=lambda x: x["jumlah"], reverse=True)
    return hasil


def hitung_distribusi_taktik_mitre(
    df_riwayat: pd.DataFrame, df_berita_dedup: Optional[pd.DataFrame] = None
) -> List[Dict[str, Any]]:
    """
    Menghitung distribusi pemetaan taktik MITRE ATT&CK dari korpus insiden terkini.
    Mengelompokkan indikator ke dalam taktik standar industri keamanan siber.
    """
    if df_berita_dedup is not None:
        df_berita = df_berita_dedup
    else:
        df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
        if df_berita.empty:
            return []
        df_berita = _dedup_ringan_lintas_hari(df_berita)

    if df_berita.empty:
        return []

    df_terkini, _ = _split_periode(df_berita)
    if df_terkini.empty:
        df_terkini = df_berita

    from src.analytics.encyclopedia_lookup import load_encyclopedia
    mitre_db = load_encyclopedia("mitre.json")

    taktik_counter: Dict[str, int] = Counter()

    for _, row in df_terkini.iterrows():
        teks = f"{row.get('judul', '')} {row.get('ringkasan_atau_narasi', '')} {row.get('kata_kunci', '')}".lower()
        taktik_ditemukan = set()
        for entry in mitre_db:
            taktik = entry.get("tactic", "Initial Access")
            taktik_list = [t.strip() for t in taktik.split("/")]
            kws = entry.get("keywords", [])
            if any(_kata_kunci_cocok(k, teks) for k in kws):
                for t in taktik_list:
                    taktik_ditemukan.add(t)

        for t in taktik_ditemukan:
            taktik_counter[t] += 1

    if not taktik_counter:
        taktik_counter["Initial Access"] = max(1, len(df_terkini))

    total = sum(taktik_counter.values()) or 1
    hasil = []
    for taktik, count in taktik_counter.most_common(6):
        hasil.append({
            "taktik": taktik,
            "jumlah": count,
            "persen": round((count / total) * 100, 1)
        })
    return hasil


def ekstrak_radar_cve_watchlist(
    df_riwayat: pd.DataFrame, df_berita_dedup: Optional[pd.DataFrame] = None
) -> List[Dict[str, Any]]:
    """
    Mengekstrak kerentanan aktif (CVE, Zero-Day, RCE, Eksploitasi Celah)
    yang terekam dalam korpus berita insiden 7 hari terakhir.
    """
    if df_berita_dedup is not None:
        df_berita = df_berita_dedup
    else:
        df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
        if df_berita.empty:
            return []
        df_berita = _dedup_ringan_lintas_hari(df_berita)

    if df_berita.empty:
        return []

    df_terkini, _ = _split_periode(df_berita)
    if df_terkini.empty:
        df_terkini = df_berita

    cve_regex = re.compile(r'\b(CVE-\d{4}-\d{4,7})\b', re.IGNORECASE)
    software_keywords = [
        "fortinet", "palo alto", "ivanti", "cisco", "microsoft", "windows", "exchange",
        "linux", "apache", "nginx", "laravel", "wordpress", "vmware", "citrix",
        "checkpoint", "openssl", "roundcube", "zimbra", "google chrome", "android", "ios", "vpn"
    ]

    temuan = {}

    for _, row in df_terkini.iterrows():
        judul = str(row.get("judul", ""))
        narasi = str(row.get("ringkasan_atau_narasi", ""))
        sumber = str(row.get("sumber", "Media Intelijen"))
        link = str(row.get("link", ""))
        teks_gabung = f"{judul} {narasi}"

        cve_matches = cve_regex.findall(teks_gabung)
        for cve in cve_matches:
            cve_upper = cve.upper()
            app_target = "Komponen Server / Gateway"
            teks_lower = teks_gabung.lower()
            for sw in software_keywords:
                if _kata_kunci_cocok(sw, teks_lower):
                    app_target = sw.title()
                    break

            if cve_upper not in temuan:
                temuan[cve_upper] = {
                    "cve_id": cve_upper,
                    "aplikasi_terdampak": app_target,
                    "status_urgensi": "Eksploitasi Aktif",
                    "jumlah_laporan": 1,
                    "sumber_terakhir": sumber,
                    "contoh_kasus": judul[:90],
                    "judul_lengkap": judul,
                    "ringkasan": narasi,
                    "link": link
                }
            else:
                temuan[cve_upper]["jumlah_laporan"] += 1

        teks_lower = teks_gabung.lower()
        if not cve_matches and re.search(r"\b(?:zero-day|0-day|rce|remote code execution|celah kritis)\b", teks_lower):
            label = "Kerentanan Zero-Day" if ("zero-day" in teks_lower or "0-day" in teks_lower) else "Celah Kritis RCE"
            app_target = "Layanan Web Publik"
            for sw in software_keywords:
                if _kata_kunci_cocok(sw, teks_lower):
                    app_target = sw.title()
                    break

            key = f"{label} ({app_target})"
            if key not in temuan:
                temuan[key] = {
                    "cve_id": label,
                    "aplikasi_terdampak": app_target,
                    "status_urgensi": "Pantauan Eksploitasi",
                    "jumlah_laporan": 1,
                    "sumber_terakhir": sumber,
                    "contoh_kasus": judul[:90],
                    "judul_lengkap": judul,
                    "ringkasan": narasi,
                    "link": link
                }
            else:
                temuan[key]["jumlah_laporan"] += 1

    daftar_cve = list(temuan.values())
    daftar_cve.sort(key=lambda x: x["jumlah_laporan"], reverse=True)
    return daftar_cve[:6]


def hitung_tren_sektor_target(
    df_riwayat: pd.DataFrame, df_berita_dedup: Optional[pd.DataFrame] = None
) -> List[Dict]:
    if df_berita_dedup is not None:
        df_berita = df_berita_dedup
    else:
        df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
        if df_berita.empty:
            return []
        df_berita = _dedup_ringan_lintas_hari(df_berita)

    if df_berita.empty:
        return []

    df_terkini, df_baseline = _split_periode(df_berita)

    def _hitung_sektor(df_sub: pd.DataFrame) -> Dict[str, int]:
        counts = {s: 0 for s in SEKTOR_RULES}
        if df_sub.empty:
            return counts
        for _, row in df_sub.iterrows():
            teks = (str(row.get("judul", "")) + " " + str(row.get("ringkasan_atau_narasi", "")) + " " + str(row.get("kata_kunci", ""))).lower()
            for s_nama, s_words in SEKTOR_RULES.items():
                if any(_kata_kunci_cocok(w, teks) for w in s_words):
                    counts[s_nama] += 1
        return counts

    hitung_terkini = _hitung_sektor(df_terkini)
    hitung_baseline = _hitung_sektor(df_baseline)
    hitung_total = _hitung_sektor(df_berita)
    total_semua = max(sum(hitung_total.values()), 1)

    hasil = []
    for s in SEKTOR_RULES:
        c_tot = hitung_total[s]
        c_cur = hitung_terkini[s]
        c_base = hitung_baseline[s]
        growth = _hitung_growth(c_cur, c_base)
        pct = round((c_tot / total_semua) * 100, 1)
        hasil.append({
            "sektor": s,
            "jumlah": c_tot,
            "jumlah_terkini": c_cur,
            "jumlah_baseline": c_base,
            "growth_persen": growth,
            "persen_total": pct
        })

    hasil.sort(key=lambda x: (x["jumlah"], x["growth_persen"]), reverse=True)
    return hasil


# Frasa idiomatik/umum yang tidak boleh disalahartikan sebagai wilayah Jawa Timur (Batu / Malang)
_REGEX_AMBIGU_JATIM = re.compile(
    r'\b(?:batu\s+bara|batubara|batu\s+ginjal|batu\s+akik|kepala\s+batu|gula\s+batu|batu\s+bata|'
    r'batu\s+karang|batu\s+apung|batu\s+mulia|nasib\s+malang|malang\s+melintang|malang\s+nian|'
    r'malang\s+tak\s+dapat|korban\s+yang\s+malang|pria\s+malang|wanita\s+malang|gadis\s+malang|'
    r'bocah\s+malang|orang\s+malang)\b',
    re.IGNORECASE
)

# Entitas Geografis & Instansi Jawa Timur (Provinsi + 29 Kabupaten + 9 Kota)
_KEYWORDS_JATIM_REGEX = re.compile(
    r'\b(?:' + '|'.join(re.escape(k) for k in ConfigLoader.get_rules("keywords_jawa_timur")) + r'|malang)\b',
    re.IGNORECASE
)

# Regex pembersihan dateline jurnalis di awal narasi (misal: "SURABAYA, Kompas.com - ", "SURABAYA - ")
_REGEX_DATELINE = re.compile(
    r'^(?:[A-Z\s]{3,25}(?:\([^\)]+\)|,\s*[^–\-\n]+)?\s*[-–—]\s*)'
)

# Entitas tingkat nasional murni (mencegah artikel nasional yang diliput media Jatim masuk ke Jatim)
_ENTITAS_NASIONAL_REGEX = re.compile(
    r'\b(?:pusat data nasional|pdn|pdns|kpu ri|kpu pusat|kemenkes|kemhan|kementan|kemenkeu|'
    r'kemenkominfo|komdigi|kemenkomdigi|kementerian|mabes polri|bareskrim|bssn|dpr ri|'
    r'kejaksaan agung|bank indonesia|ojk pusat|bpjs)\b',
    re.IGNORECASE
)

# Entitas & negara internasional untuk deteksi konten luar negeri
_REGEX_KONTEN_INTERNASIONAL = re.compile(
    r'\b(australia|amerika|amerika serikat|as|us|usa|new mexico|california|inggris|britania|rusia|china|tiongkok|'
    r'korea selatan|korea utara|jepang|singapura|malaysia|belanda|amsterdam|prancis|jerman|'
    r'ukraina|israel|iran|taiwan|kanada|india|global|dunia|internasional|pentagon|white house|'
    r'fbi|cia|nsa|kremlin|europol|interpol|kepco|korea electric power)\b',
    re.IGNORECASE
)

# Indikator artikel terjemahan entitas asing yang tidak boleh dianggap BUMN/target Indonesia (mis. KEPCO -> PLN)
_REGEX_ARTEFAK_ASING = re.compile(
    r'(?:\bkepco\b|\bkorea\s+electric\s+power\b|[\uac00-\ud7af])',
    re.IGNORECASE
)

# Entitas & indikator target Indonesia (Nasional di luar Jawa Timur, provinsi, kota besar, BUMN/instansi, domain .id)
# Kata ambigu seperti "mandiri" dan "garuda" wajib berpasangan dengan konteks institusi resminya.
_REGEX_TARGET_INDONESIA = re.compile(
    r'(?:\b(?:'
    r'indonesia|tanah\s+air|nusantara|nkri|ri|jakarta|dki\s+jakarta|bogor|depok|tangerang|tangsel|bekasi|'
    r'jawa\s+barat|jabar|bandung|cirebon|sukabumi|tasikmalaya|karawang|purwakarta|garut|cianjur|'
    r'jawa\s+tengah|jateng|semarang|surakarta|solo|magelang|pekalongan|tegal|cilacap|banyumas|purwokerto|'
    r'yogyakarta|jogja|diy|sleman|bantul|kulon\s+progo|gunungkidul|banten|serang|cilegon|'
    r'sumatera\s+barat|sumbar|padang|bukittinggi|payakumbuh|sumatera\s+utara|sumut|medan|deli\s+serdang|'
    r'sumatera\s+selatan|sumsel|palembang|riau|pekanbaru|kepri|batam|bintan|tanjungpinang|'
    r'aceh|banda\s+aceh|lampung|bandar\s+lampung|jambi|bengkulu|bangka\s+belitung|pangkalpinang|'
    r'bali|denpasar|badung|gianyar|bangli|buleleng|tabanan|klungkung|karangasem|jembrana|'
    r'ntb|lombok|mataram|bima|sumbawa|ntt|kupang|flores|sumba|labuan\s+bajo|'
    r'kalimantan\s+barat|kalbar|pontianak|singkawang|kalimantan\s+tengah|kalteng|palangkaraya|'
    r'kalimantan\s+selatan|kalsel|banjarmasin|banjarbaru|kalimantan\s+timur|kaltim|samarinda|balikpapan|bontang|'
    r'kalimantan\s+utara|kaltara|tarakan|ikn\s+nusantara|otorita\s+ikn|'
    r'sulawesi\s+selatan|sulsel|makassar|gowa|maros|parepare|sulawesi\s+utara|sulut|manado|bitung|tomohon|'
    r'sulawesi\s+tengah|sulteng|palu|morowali|sulawesi\s+tenggara|sultra|kendari|baubau|'
    r'gorontalo|sulawesi\s+barat|sulbar|mamuju|maluku|ambon|ternate|tidore|papua|jayapura|sorong|manokwari|merauke|timika|'
    r'kpu|bawaslu|pdn|pdns|pusat\s+data\s+nasional|kemenkes|kemhan|kementan|kemenkeu|kemendagri|kemendikbud|'
    r'kemenkominfo|kominfo|komdigi|kemenkomdigi|bssn|csirt|gov-csirt|polri|mabes\s+polri|bareskrim|polda|polres|polresta|'
    r'tni|bumn|dpr\s+ri|dprd|mpr\s+ri|kpk|kejagung|kejaksaan|mahkamah\s+agung|mahkamah\s+konstitusi|'
    r'bpjs|ojk|bank\s+indonesia|qris|pandi|diskominfo|pemprov|pemkab|pemkot|bpkpd|dukcapil|'
    r'bank\s+bri|pt\s+bri|brimo|bca|bank\s+bca|bni|bank\s+bni|bsi|bank\s+syariah\s+indonesia|btn|bank\s+btn|'
    r'bank\s+mandiri|pt\s+bank\s+mandiri|livin\s+by\s+mandiri|mandiri\s+online|nasabah\s+mandiri|atm\s+mandiri|sekuritas\s+mandiri|'
    r'garuda\s+indonesia|maskapai\s+garuda|pertamina|telkom|telkomsel|indihome|indosat|xl\s+axiata|'
    r'pln|pt\s+pln|pln\s+mobile|tokopedia|gojek|goto|bukalapak|traveloka|'
    r'universitas\s+indonesia|mahasiswa\s+ui|kampus\s+ui|ugm|universitas\s+gadjah\s+mada|itb|ipb|undip|unpad'
    r')\b|(?:\.(?:go|co|ac|or|desa|sch|net|web|my)\.id\b|\bdomain\s+\.id\b|\bsitus\s+\.id\b))',
    re.IGNORECASE
)

# Filter berita non-insiden siber (bantahan murni, penangkapan judi online konvensional, kebijakan/opini non-serangan)
_REGEX_BANTAHAN_MURNI = re.compile(
    r'\b(?:tak\s+temukan\s+indikasi\s+kebocoran|tidak\s+menemukan\s+indikasi\s+kebocoran|'
    r'tidak\s+ditemukan\s+indikasi\s+kebocoran|bantah\s+(?:isu\s+)?kebocoran\s+data|membantah\s+(?:isu\s+)?kebocoran\s+data|'
    r'tepis\s+(?:isu\s+)?kebocoran\s+data|menepis\s+kabar\s+hoaks|pastikan\s+server\s+aman|'
    r'bantah\s+terkait\s+transfer|tak\s+terkait\s+operasi\s+sekarang|tidak\s+terkait\s+operasi\s+sekarang|'
    r'pastikan\s+data\s+aman\s+tidak\s+bocor|pastikan\s+sistem\s+tidak\s+diretas)\b',
    re.IGNORECASE
)

_REGEX_KEBIJAKAN_NON_INSIDEN = re.compile(
    r'\b(?:kaji\s+bentuk\s+tim\s+tanggap|larang\s+pegawai\s+negeri\s+gunakan|larang\s+pns\s+gunakan|'
    r'ingatkan\s+kreator\s+waspadai|masuk\s+tim\s+keamanan\s+siber\s+dunia|gelar\s+sosialisasi\s+keamanan\s+siber|'
    r'tips\s+aman\s+bertransaksi|cara\s+mudah\s+mencegah\s+peretasan)\b',
    re.IGNORECASE
)


def _is_bukan_insiden_siber_aktual(
    judul_bersih: str, teks_konten_bersih: str, row_dict: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Mengecualikan berita yang bukan insiden serangan siber aktual terhadap sistem/infrastruktur:
    1. Berita penegakan hukum/penangkapan pelaku judi online atau kriminal umum (via rag_engine.is_berita_penegakan_hukum).
    2. Berita bantahan murni tanpa konfirmasi kebocoran/insiden aktif.
    3. Berita kebijakan/himbauan/pencapaian umum yang tidak melaporkan insiden serangan siber.
    """
    from src.analytics.rag_engine import is_berita_penegakan_hukum
    eval_dict = row_dict or {"judul": judul_bersih, "ringkasan_atau_narasi": teks_konten_bersih}
    if is_berita_penegakan_hukum(eval_dict):
        return True

    judul_low = judul_bersih.lower()
    if _REGEX_BANTAHAN_MURNI.search(judul_low) or _REGEX_BANTAHAN_MURNI.search(teks_konten_bersih):
        return True

    if _REGEX_KEBIJAKAN_NON_INSIDEN.search(judul_low):
        return True

    # Penangkapan pelaku judi online konvensional (tanpa peretasan situs/defacement)
    if re.search(r'\b(?:judi\s+online|judol)\b', teks_konten_bersih):
        ada_penangkapan = bool(re.search(
            r'\b(?:tangkap|ditangkap|menangkap|meringkus|diringkus|mengamankan|diamankan|tersangka|pelaku|bandar|warung\s+kopi|selebgram)\b',
            teks_konten_bersih
        ))
        ada_serangan_siber = bool(re.search(
            r'\b(?:diretas|peretasan|retas|deface|defacement|disusupi|situs|domain|subdomain|website|server|injeksi)\b',
            teks_konten_bersih
        ))
        if ada_penangkapan and not ada_serangan_siber:
            return True

    return False


def _bersihkan_judul_dan_publisher(judul_raw: str, sumber_raw: str) -> tuple[str, str]:
    """
    Memisahkan judul berita asli dari nama publisher/media di akhir judul.
    Contoh: 'PDN Diretas - Detik Jatim' -> ('PDN Diretas', 'Detik Jatim')
    Pembersihan dilakukan secara berulang untuk menangani duplikasi suffix dari agregator RSS.
    """
    judul = re.sub(r"[\u200b-\u200d\ufeff]", "", str(judul_raw or "")).strip()
    sumber = re.sub(r"[\u200b-\u200d\ufeff]", "", str(sumber_raw or "")).strip()
    while " - " in judul:
        parts = judul.rsplit(" - ", 1)
        suffix = parts[1].strip()
        if len(suffix) <= 40 and not any(k in suffix.lower() for k in [
            "diretas", "bocor", "hacker", "serangan", "ransomware", "malware", "error", "waspada", "terkena"
        ]):
            judul = parts[0].strip()
            if sumber.lower() in ["google news", "", "none"]:
                sumber = suffix
        else:
            break
    return judul, (sumber if sumber else "Media")


def _deteksi_tag_insiden(text: str) -> str:
    """Mendeteksi tag kategori taktis untuk insiden siber."""
    t = text.lower()
    if any(k in t for k in ["ransomware", "tebusan", "pemerasan"]):
        return "Ransomware"
    if any(k in t for k in ["bocor", "leak", "breach", "dark web", "nasabah", "data pribadi"]):
        return "Kebocoran Data"
    if any(k in t for k in ["deface", "judi slot", "judi online", "slot", "peretasan", "hacker", "diretas", "hacked"]):
        return "Peretasan Web"
    if any(k in t for k in ["malware", "infostealer", "trojan", "stealer", "spyware"]):
        return "Malware"
    if any(k in t for k in ["phishing", "scam", "penipuan", "tautan palsu"]):
        return "Phishing"
    if any(k in t for k in ["zero-day", "celah", "vulnerability", "exploit"]):
        return "Eksploitasi Celah"
    return "Insiden Siber"


def hitung_kasus_insiden_wilayah(df_riwayat: pd.DataFrame, top_n_per_wilayah: int = 20) -> Dict[str, List[Dict]]:
    """
    Mengidentifikasi kasus insiden siber yang sedang ramai selama 7 hari terakhir
    pada 3 level wilayah dengan hierarki ketat:
    1. Jawa Timur: Eksplisit menyebut entitas, pemda, kota/kabupaten, atau instansi di Jawa Timur.
    2. Nasional: Eksplisit menyebut Indonesia atau entitas/wilayah/instansi di Indonesia (di luar Jawa Timur).
    3. Internasional: Semua berita insiden siber di luar Indonesia (termasuk insiden global yang diliput media lokal).
    """
    hasil_kosong = {"internasional": [], "nasional": [], "jawa_timur": []}
    if df_riwayat.empty:
        return hasil_kosong

    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
    if df_berita.empty:
        return hasil_kosong

    # Ambil periode terkini (7 hari)
    col_tgl = "tanggal_publish" if "tanggal_publish" in df_berita.columns else ("tanggal_dicatat" if "tanggal_dicatat" in df_berita.columns else None)
    if col_tgl is not None:
        df_berita["tgl"] = df_berita[col_tgl].fillna("").astype(str).str.slice(0, 10)
    else:
        df_berita["tgl"] = ""
    tanggal_unik = sorted(df_berita[df_berita["tgl"].str.match(r"^\d{4}-\d{2}-\d{2}$")]["tgl"].unique(), reverse=True)
    if tanggal_unik:
        tanggal_terkini = set(tanggal_unik[:HARI_PERIODE_TERKINI])
        df_terkini = df_berita[df_berita["tgl"].isin(tanggal_terkini)].copy()
    else:
        df_terkini = df_berita.copy()

    if df_terkini.empty:
        return hasil_kosong

    def _cluster_and_rank(df_subset: pd.DataFrame, limit: int) -> List[Dict]:
        if df_subset.empty:
            return []

        # Hanya ambil baris insiden_spesifik (serangan siber/peretasan nyata, bukan evergreen/edukasi)
        if "kategori_relevansi" in df_subset.columns:
            df_insiden = df_subset[df_subset["kategori_relevansi"] == "insiden_spesifik"].copy()
        else:
            df_insiden = df_subset.copy()
        if df_insiden.empty:
            return []

        sort_col = "tanggal_publish" if "tanggal_publish" in df_insiden.columns else "tgl"
        df_sorted = df_insiden.sort_values(by=[sort_col], ascending=False).reset_index(drop=True)
        clusters = []
        sudah_diproses = set()

        for i in range(len(df_sorted)):
            if i in sudah_diproses:
                continue
            row_i = df_sorted.iloc[i]
            judul_raw = str(row_i.get("judul", "")).strip()
            sumber_raw = str(row_i.get("sumber", "")).strip()

            # Bersihkan nama publisher dari judul
            judul_tampil, sumber_tampil = _bersihkan_judul_dan_publisher(judul_raw, sumber_raw)
            text_full = f"{judul_tampil} {row_i.get('ringkasan_atau_narasi', '')} {row_i.get('kata_kunci', '')}"

            cluster = {
                "judul": judul_tampil,
                "judul_asli": judul_raw,
                "sumber": sumber_tampil,
                "sumber_asli": sumber_raw,
                "link": str(row_i.get("link", "#")),
                "id": int(row_i.get("id", 0) or 0),
                "tanggal": str(row_i.get("tgl", "")),
                "tanggal_publish": str(row_i.get("tanggal_publish", row_i.get("tgl", ""))),
                "ringkasan": str(row_i.get("ringkasan_atau_narasi", ""))[:150],
                "ringkasan_atau_narasi": str(row_i.get("ringkasan_atau_narasi", "")),
                "kata_kunci": str(row_i.get("kata_kunci", "")),
                "skor_relevansi": float(row_i.get("skor_relevansi", 0.0) or 0.0),
                "tag": _deteksi_tag_insiden(text_full),
                "jumlah_liputan": 1,
                "media_lain": [],
            }
            sudah_diproses.add(i)

            for j in range(i + 1, len(df_sorted)):
                if j in sudah_diproses:
                    continue
                row_j = df_sorted.iloc[j]
                judul_j = str(row_j.get("judul", "")).strip()
                sumber_j = str(row_j.get("sumber", "")).strip()
                judul_j_tampil, sumber_j_name = _bersihkan_judul_dan_publisher(judul_j, sumber_j)

                # Periksa kecocokan kemiripan teks pada judul bersih
                if fuzz.token_sort_ratio(judul_tampil.lower(), judul_j_tampil.lower()) >= 60:
                    sudah_diproses.add(j)
                    cluster["jumlah_liputan"] += 1
                    if sumber_j_name and sumber_j_name != sumber_tampil and sumber_j_name not in cluster["media_lain"]:
                        cluster["media_lain"].append(sumber_j_name)

            clusters.append(cluster)

        # Urutkan berdasarkan: intensitas liputan media (sedang ramai), skor relevansi, tanggal terbaru, dan id artikel (deterministik penuh)
        clusters.sort(
            key=lambda x: (x["jumlah_liputan"], x["skor_relevansi"], x.get("tanggal_publish", x["tanggal"]), x.get("id", 0)),
            reverse=True
        )
        return clusters[:limit]

    rows_jatim = []
    rows_intl = []
    rows_nasional = []

    for _, row in df_terkini.iterrows():
        judul_raw = str(row.get("judul", "")).strip()
        sumber_raw = str(row.get("sumber", "")).strip()
        narasi_raw = str(row.get("ringkasan_atau_narasi", "")).strip()
        kata_kunci_raw = str(row.get("kata_kunci", "")).strip()

        judul_bersih, pub_tampil = _bersihkan_judul_dan_publisher(judul_raw, sumber_raw)
        narasi_bersih = _REGEX_DATELINE.sub("", narasi_raw)

        # Evaluasi lokasi kejadian HANYA berdasarkan konten berita bersih (judul & narasi tanpa dateline & tanpa publisher)
        teks_konten_bersih = f"{judul_bersih} {narasi_bersih} {kata_kunci_raw}".lower()
        row_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)

        # Filter berita non-insiden siber (penangkapan judol, bantahan murni, kebijakan non-insiden)
        if _is_bukan_insiden_siber_aktual(judul_bersih, teks_konten_bersih, row_dict):
            continue

        is_sumber_intl = (
            sumber_raw in _SUMBER_INTERNASIONAL
            or pub_tampil in _SUMBER_INTERNASIONAL
            or bool(_REGEX_ARTEFAK_ASING.search(f"{sumber_raw} {judul_raw} {narasi_raw}"))
        )

        # Bersihkan frasa idiomatik ambigu ("batu bara", "nasib malang", dll.) sebelum evaluasi Jatim
        teks_jatim_eval = _REGEX_AMBIGU_JATIM.sub(" ", teks_konten_bersih)
        judul_jatim_eval = _REGEX_AMBIGU_JATIM.sub(" ", judul_bersih.lower())
        matches_jatim = bool(_KEYWORDS_JATIM_REGEX.search(teks_jatim_eval))

        # Hierarki 1: Jawa Timur
        is_jatim = False
        if matches_jatim and not is_sumber_intl:
            target_nasional = bool(_ENTITAS_NASIONAL_REGEX.search(judul_bersih))
            opini_pakar = any(p in judul_bersih.lower() for p in ["pakar", "analisis", "tanggapi", "komentari", "soroti", "minta", "dosen"])
            ada_target_lokal_eksplisit = bool(_KEYWORDS_JATIM_REGEX.search(judul_jatim_eval))

            if target_nasional and opini_pakar:
                is_jatim = False
            elif target_nasional and not ada_target_lokal_eksplisit:
                is_jatim = False
            else:
                is_jatim = True

        # Hierarki 2: Nasional (wajib memiliki penyebutan eksplisit Indonesia / daerah / entitas nasional / domain .id)
        is_nasional = False
        if not is_jatim and not is_sumber_intl:
            has_id_target = bool(_REGEX_TARGET_INDONESIA.search(judul_bersih)) or bool(_REGEX_TARGET_INDONESIA.search(teks_konten_bersih))
            if has_id_target:
                is_nasional = True

        # Hierarki 3: Internasional (semua berita insiden siber di luar Jawa Timur & Nasional)
        if is_jatim:
            rows_jatim.append(row)
        elif is_nasional:
            rows_nasional.append(row)
        else:
            rows_intl.append(row)

    hasil_jatim = _cluster_and_rank(pd.DataFrame(rows_jatim), top_n_per_wilayah) if rows_jatim else []
    hasil_nas = _cluster_and_rank(pd.DataFrame(rows_nasional), top_n_per_wilayah) if rows_nasional else []
    hasil_intl = _cluster_and_rank(pd.DataFrame(rows_intl), top_n_per_wilayah) if rows_intl else []

    return {
        "internasional": hasil_intl,
        "nasional": hasil_nas,
        "jawa_timur": hasil_jatim,
    }


def susun_ringkasan_statistik_tren(df_riwayat: pd.DataFrame) -> Dict:
    """Menghitung ringkasan statistik tren mingguan dari riwayat DataFrame."""
    if df_riwayat.empty:
        logger.info("riwayat_tren kosong, tidak ada statistik tren yang bisa dihitung.")
        return {
            "berita": {},
            "vektor_serangan": [],
            "sektor_target": [],
            "kasus_wilayah": {"internasional": [], "nasional": [], "jawa_timur": []},
        }

    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
    df_berita_dedup = _dedup_ringan_lintas_hari(df_berita) if not df_berita.empty else df_berita

    statistik = {
        "berita": {
            "kata_kunci_naik": hitung_tren_kata_kunci_berita(df_riwayat, top_n=10, df_berita_dedup=df_berita_dedup),
            "tren_kategori": hitung_tren_kategori_berita(df_riwayat, df_berita_dedup=df_berita_dedup),
            "sampel_judul_insiden": ambil_sampel_judul_insiden(df_riwayat, df_berita_dedup=df_berita_dedup),
        },
        "vektor_serangan": hitung_tren_vektor_serangan(df_riwayat, df_berita_dedup=df_berita_dedup),
        "taktik_mitre": hitung_distribusi_taktik_mitre(df_riwayat, df_berita_dedup=df_berita_dedup),
        "cve_watchlist": ekstrak_radar_cve_watchlist(df_riwayat, df_berita_dedup=df_berita_dedup),
        "sektor_target": hitung_tren_sektor_target(df_riwayat, df_berita_dedup=df_berita_dedup),
        "kasus_wilayah": hitung_kasus_insiden_wilayah(df_riwayat),
    }

    logger.info(
        f"Statistik tren mingguan tersusun: {len(statistik['berita']['kata_kunci_naik'])} kata kunci naik, "
        f"Kasus Wilayah: Intl={len(statistik['kasus_wilayah']['internasional'])}, Nas={len(statistik['kasus_wilayah']['nasional'])}, Jatim={len(statistik['kasus_wilayah']['jawa_timur'])}."
    )
    return statistik


def hitung_perbandingan_wow(df_riwayat: pd.DataFrame) -> Dict:
    """
    Menghitung perbandingan metrik kunci Week-over-Week (7 hari terkini vs 7 hari baseline).
    Mencakup:
    1. Total Insiden Siber (Berita)
    2. Insiden Kritis
    3. Top Vektor Serangan Dominan
    4. Top Sektor Target Terpapar
    5. Celah Kerentanan Kritis (CVE Watchlist)
    """
    if df_riwayat.empty:
        return {}

    df_terkini, df_baseline = _split_periode(df_riwayat)
    df_terkini_b = df_terkini[df_terkini["kategori"] == "berita"] if not df_terkini.empty else pd.DataFrame()
    df_baseline_b = df_baseline[df_baseline["kategori"] == "berita"] if not df_baseline.empty else pd.DataFrame()

    terkini_total = len(df_terkini_b)
    baseline_total = len(df_baseline_b)
    growth_total = _hitung_growth(terkini_total, baseline_total)

    terkini_kritis = int((df_terkini_b["kategori_relevansi"] == "insiden_spesifik").sum()) if not df_terkini_b.empty else 0
    baseline_kritis = int((df_baseline_b["kategori_relevansi"] == "insiden_spesifik").sum()) if not df_baseline_b.empty else 0
    growth_kritis = _hitung_growth(terkini_kritis, baseline_kritis)

    # Vektor Serangan Terkini vs Baseline
    vektor_terkini = hitung_tren_vektor_serangan(df_terkini) if not df_terkini.empty else []
    vektor_baseline = hitung_tren_vektor_serangan(df_baseline) if not df_baseline.empty else []
    top_v_terkini = vektor_terkini[0]["vektor"] if vektor_terkini and vektor_terkini[0]["jumlah"] > 0 else "-"
    top_v_baseline = vektor_baseline[0]["vektor"] if vektor_baseline and vektor_baseline[0]["jumlah"] > 0 else "-"

    # Sektor Target Terkini vs Baseline
    sektor_terkini = hitung_tren_sektor_target(df_terkini) if not df_terkini.empty else []
    sektor_baseline = hitung_tren_sektor_target(df_baseline) if not df_baseline.empty else []
    top_s_terkini = sektor_terkini[0]["sektor"] if sektor_terkini and sektor_terkini[0]["jumlah"] > 0 else "-"
    top_s_baseline = sektor_baseline[0]["sektor"] if sektor_baseline and sektor_baseline[0]["jumlah"] > 0 else "-"

    # CVE Watchlist Terkini vs Baseline
    cve_terkini_list = ekstrak_radar_cve_watchlist(df_terkini) if not df_terkini.empty else []
    cve_baseline_list = ekstrak_radar_cve_watchlist(df_baseline) if not df_baseline.empty else []
    cve_terkini_count = len(cve_terkini_list)
    cve_baseline_count = len(cve_baseline_list)
    growth_cve = _hitung_growth(cve_terkini_count, cve_baseline_count)

    return {
        "total_insiden": {
            "label": "Total Insiden Siber",
            "terkini": f"{terkini_total} insiden",
            "baseline": f"{baseline_total} insiden",
            "growth": growth_total,
            "status": f"{'+' if growth_total >= 0 else ''}{growth_total}%",
            "icon": "newspaper"
        },
        "insiden_kritis": {
            "label": "Insiden Kritis Operasional",
            "terkini": f"{terkini_kritis} kasus",
            "baseline": f"{baseline_kritis} kasus",
            "growth": growth_kritis,
            "status": f"{'+' if growth_kritis >= 0 else ''}{growth_kritis}%",
            "icon": "warning"
        },
        "top_vektor": {
            "label": "Vektor Serangan Utama",
            "terkini": top_v_terkini,
            "baseline": top_v_baseline,
            "status": "Tetap" if top_v_terkini == top_v_baseline and top_v_terkini != "-" else "Bergeser",
            "icon": "alt_route"
        },
        "top_sektor": {
            "label": "Sektor Paling Terdampak",
            "terkini": top_s_terkini,
            "baseline": top_s_baseline,
            "status": "Tetap" if top_s_terkini == top_s_baseline and top_s_terkini != "-" else "Bergeser",
            "icon": "domain"
        },
        "cve_kritis": {
            "label": "Radar Eksploitasi CVE Aktif",
            "terkini": f"{cve_terkini_count} CVE",
            "baseline": f"{cve_baseline_count} CVE",
            "growth": growth_cve,
            "status": f"{'+' if growth_cve >= 0 else ''}{growth_cve}%",
            "icon": "bug_report"
        }
    }


def susun_statistik_dashboard(df_riwayat: pd.DataFrame, statistik_tren: Optional[dict] = None) -> dict:
    """
    Menyusun seluruh agregat statistik visualisasi dashboard (KPI, grafik harian, distribusi sumber & CVSS).
    Dihitung sekali saat pipeline pasca-proses selesai dan disimpan ke database agar tampilan web instan.
    """
    statistik_kosong = {
        "total_berita": 0, "total_insiden_kritis": 0,
        "kata_kunci_naik": [], "top_sektor": [], "sampel_judul_insiden": [],
        "tren_kategori": {}, "harian": [],
        "distribusi_sumber": [],
        "nasional_vs_internasional": {"nasional": 0, "internasional": 0},
        "komposisi_jenis": {}, "harian_sumber": [], "vektor_serangan": [],
        "taktik_mitre": [], "cve_watchlist": [],
        "kasus_wilayah": {"internasional": [], "nasional": [], "jawa_timur": []},
        "perbandingan_wow": {},
    }
    if df_riwayat.empty:
        return statistik_kosong

    statistik = statistik_tren or susun_ringkasan_statistik_tren(df_riwayat)

    # 7 hari terkini untuk visualisasi dashboard (KPI, grafik, distribusi)
    df_temp = df_riwayat.copy()
    df_temp["tgl"] = df_temp["tanggal_publish"].fillna("").astype(str).str.slice(0, 10)
    tanggal_unik_terbaru = sorted(df_temp[df_temp["tgl"].str.match(r"^\d{4}-\d{2}-\d{2}$")]["tgl"].unique(), reverse=True)[:7]
    tanggal_urut = sorted(tanggal_unik_terbaru)

    df_7 = df_temp[df_temp["tgl"].isin(tanggal_unik_terbaru)].copy()
    df_berita = df_7[df_7["kategori"] == "berita"]

    total_berita = len(df_berita)
    total_insiden_kritis = int((df_berita["kategori_relevansi"] == "insiden_spesifik").sum()) if not df_berita.empty else 0

    # Chart Harian
    harian_list = []
    for tgl in tanggal_urut:
        df_tgl = df_7[df_7["tgl"] == tgl]
        harian_list.append({
            "tanggal": tgl,
            "berita": int((df_tgl["kategori"] == "berita").sum()),
        })

    # Distribusi Sumber
    sumber_counts = df_berita["sumber"].value_counts().to_dict() if not df_berita.empty else {}
    distribusi_sumber = [{"sumber": s, "jumlah": int(c)} for s, c in sorted(sumber_counts.items(), key=lambda x: -x[1])]

    # Nasional vs Internasional
    nasional_count = sum(int(c) for s, c in sumber_counts.items() if s not in _SUMBER_INTERNASIONAL)
    internasional_count = sum(int(c) for s, c in sumber_counts.items() if s in _SUMBER_INTERNASIONAL)

    # Komposisi Jenis
    jenis_raw = df_berita["kategori_relevansi"].value_counts().to_dict() if not df_berita.empty else {}
    komposisi_jenis = {k: int(v) for k, v in jenis_raw.items()}

    # Harian Sumber
    harian_sumber = []
    for tgl in tanggal_urut:
        df_tgl_b = df_7[(df_7["tgl"] == tgl) & (df_7["kategori"] == "berita")]
        nas = int((~df_tgl_b["sumber"].isin(_SUMBER_INTERNASIONAL)).sum())
        intl = int((df_tgl_b["sumber"].isin(_SUMBER_INTERNASIONAL)).sum())
        harian_sumber.append({"tanggal": tgl, "nasional": nas, "internasional": intl})

    # Prediksi 1 Pola Serangan untuk KPI Dashboard
    try:
        from src.analytics.rag_engine import RAGEngine
        rag = RAGEngine(df_riwayat)
        pola_serangan = rag.hitung_prediksi_pola_serangan()
        ancaman_baru = rag.hitung_prediksi_ancaman_baru()
    except Exception as err:
        logger.warning(f"Gagal menghitung prediksi pola serangan/ancaman: {err}")
        pola_serangan = {
            "pola": "Akses Tidak Sah / Pembobolan Akun",
            "pola_lengkap": "Akses Tidak Sah / Pembobolan Akun",
            "growth_persen": 0.0,
            "jumlah_terkini": 0,
            "subteks": "vs minggu lalu",
            "taksonomi_resmi": "Akses Tidak Sah / Pembobolan Akun",
        }
        ancaman_baru = "Kondisi Stabil"

    return {
        "total_berita": total_berita,
        "total_insiden_kritis": total_insiden_kritis,
        "ancaman_baru": ancaman_baru,
        "kata_kunci_naik": statistik.get("berita", {}).get("kata_kunci_naik", []),
        "top_sektor": statistik.get("sektor_target", []),
        "sampel_judul_insiden": statistik.get("berita", {}).get("sampel_judul_insiden", []),
        "tren_kategori": statistik.get("berita", {}).get("tren_kategori", {}),
        "sektor_target": statistik.get("sektor_target", []),
        "harian": harian_list,
        "distribusi_sumber": distribusi_sumber,
        "nasional_vs_internasional": {"nasional": nasional_count, "internasional": internasional_count},
        "komposisi_jenis": komposisi_jenis,
        "harian_sumber": harian_sumber,
        "vektor_serangan": statistik.get("vektor_serangan", []),
        "taktik_mitre": statistik.get("taktik_mitre", []),
        "cve_watchlist": statistik.get("cve_watchlist", []),
        "kasus_wilayah": statistik.get("kasus_wilayah", {"internasional": [], "nasional": [], "jawa_timur": []}),
        "prediksi_pola_serangan": pola_serangan,
        "perbandingan_wow": hitung_perbandingan_wow(df_riwayat),
    }


if __name__ == "__main__":
    # Testing manual: python -m src.analytics.trend_analyzer
    from src.storage.db import ambil_riwayat_tren

    df = ambil_riwayat_tren(hari=7)
    hasil = susun_ringkasan_statistik_tren(df)

    print("=== KATA KUNCI BERITA NAIK ===")
    for kk in hasil["berita"]["kata_kunci_naik"]:
        print(f"  {kk['kata_kunci']}: {kk['jumlah_terkini']} (baseline {kk['jumlah_baseline']}) growth {kk['growth_persen']}%")

    print("\n=== TREN KATEGORI BERITA ===")
    print(hasil["berita"]["tren_kategori"])

    print("\n=== SEKTOR TARGET TERPAPAR ===")
    for s in hasil["sektor_target"]:
        print(f"  {s['sektor']}: {s['jumlah']}")