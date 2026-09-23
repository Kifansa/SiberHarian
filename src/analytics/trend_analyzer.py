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
from rapidfuzz import fuzz
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import re

import pandas as pd
from src.utils.config_loader import ConfigLoader

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

HARI_PERIODE_TERKINI = 7
THRESHOLD_DEDUP_TREN = 88  
HARI_PERIODE_BASELINE = 7  # total window 14 hari (7 terkini + 7 baseline)


def _split_periode(df: pd.DataFrame, kolom_tanggal: str = "tanggal_publish") -> tuple:
    """Membagi df jadi 2 subset: periode terkini (7 tanggal unik terbaru) vs baseline (7 tanggal unik sebelumnya)."""
    if df.empty:
        return df, df

    df = df.copy()
    tgl_series = df[kolom_tanggal].fillna("").astype(str).str.slice(0, 10)
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
    Persentase growth dari rata-rata harian baseline ke rata-rata harian
    terkini. Kalau baseline 0 tapi terkini > 0, growth dianggap 100%
    (kemunculan baru) - bukan infinity, supaya tetap bisa diurutkan wajar.
    """
    rata_terkini = jumlah_terkini / HARI_PERIODE_TERKINI
    rata_baseline = jumlah_baseline / HARI_PERIODE_BASELINE

    if rata_baseline == 0:
        return 100.0 if rata_terkini > 0 else 0.0
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
    supaya tidak menambah beban ke Ollama tiap kali statistik dihitung.
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
        judul_i = df_berita.loc[i, kolom_judul]
        baris_representatif.append(df_berita.loc[i].to_dict())
        sudah_diproses.add(i)

        for j in range(i + 1, len(df_berita)):
            if j in sudah_diproses:
                continue
            judul_j = df_berita.loc[j, kolom_judul]
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

    hasil.sort(key=lambda x: (x["growth_persen"], x["jumlah_terkini"]), reverse=True)
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


def hitung_tren_vendor_cve(df_riwayat: pd.DataFrame, top_n: int = 10, top_produk_per_vendor: int = 3) -> List[Dict]:
    df_cve = df_riwayat[df_riwayat["kategori"] == "cve"].copy()
    df_cve = df_cve[df_cve["vendor"].notna() & (df_cve["vendor"] != "Lainnya / Belum Teridentifikasi")]
    if df_cve.empty:
        return []

    # Pastikan setiap row memiliki nama produk yang bersih & valid
    from src.scraper.cve_fetcher import ekstrak_produk_cve

    produk_list = []
    for _, row in df_cve.iterrows():
        p = str(row.get("produk", "")).strip()
        if not p or p in ["-", "(lihat deskripsi)", "None", "nan", "Lainnya / Belum Teridentifikasi"]:
            narasi = str(row.get("ringkasan_atau_narasi", ""))
            vendor = str(row.get("vendor", ""))
            p = ekstrak_produk_cve(narasi_id=narasi, vendor=vendor)
        produk_list.append(p)
    df_cve["produk"] = produk_list

    df_terkini, df_baseline = _split_periode(df_cve)
    hitung_terkini = df_terkini.groupby("vendor").size().to_dict()
    hitung_baseline = df_baseline.groupby("vendor").size().to_dict()

    semua_vendor = set(hitung_terkini) | set(hitung_baseline)
    hasil = []
    for vendor in semua_vendor:
        jumlah_terkini = hitung_terkini.get(vendor, 0)
        if jumlah_terkini == 0:
            continue
        jumlah_baseline = hitung_baseline.get(vendor, 0)
        df_vendor_terkini = df_terkini[df_terkini["vendor"] == vendor]

        # Breakdown produk spesifik yang terdampak (filter keluar nilai invalid)
        produk_valid = df_vendor_terkini["produk"].dropna()
        produk_valid = produk_valid[~produk_valid.isin(["-", "(lihat deskripsi)", "None", "nan", "Lainnya / Belum Teridentifikasi", ""])]

        if produk_valid.empty:
            top_produk = [{"produk": vendor.split('/')[0].strip(), "jumlah": int(jumlah_terkini)}]
        else:
            hitung_produk = produk_valid.value_counts().head(top_produk_per_vendor)
            top_produk = [{"produk": p, "jumlah": int(j)} for p, j in hitung_produk.items()]

        hasil.append({
            "vendor": vendor,
            "jumlah_terkini": jumlah_terkini,
            "jumlah_baseline": jumlah_baseline,
            "top_produk": top_produk,
            "growth_persen": _hitung_growth(jumlah_terkini, jumlah_baseline),
        })

    hasil.sort(key=lambda x: (x["growth_persen"], x["jumlah_terkini"]), reverse=True)
    return hasil[:top_n]







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
            if any(w in teks for w in v_words):
                vektor_counts[v_nama] += 1

    hasil = [{"vektor": v, "jumlah": c} for v, c in vektor_counts.items()]
    hasil.sort(key=lambda x: x["jumlah"], reverse=True)
    return hasil


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

    sektor_counts = {s: 0 for s in SEKTOR_RULES}
    for _, row in df_berita.iterrows():
        teks = (str(row.get("judul", "")) + " " + str(row.get("ringkasan_atau_narasi", "")) + " " + str(row.get("kata_kunci", ""))).lower()
        for s_nama, s_words in SEKTOR_RULES.items():
            if any(w in teks for w in s_words):
                sektor_counts[s_nama] += 1

    hasil = [{"sektor": s, "jumlah": c} for s, c in sektor_counts.items()]
    hasil.sort(key=lambda x: x["jumlah"], reverse=True)
    return hasil



def hitung_skor_threat_posture(df_riwayat: pd.DataFrame) -> Dict:
    """
    SEKTOR_RULES = ConfigLoader.get_rules("sektor_rules")
    VEKTOR_RULES = ConfigLoader.get_rules("vektor_rules")
    Menghitung skor threat posture komparatif: 7 hari terkini vs 7 hari baseline.
    """
    if df_riwayat.empty:
        return {
            "skor": 1.0,
            "skor_baseline": 1.0,
            "level": "RENDAH",
            "level_label": "RENDAH (Low)",
            "warna": "green",
            "growth_persen": 0.0,
            "status_tren": "Stabil",
            "avg_cvss": 0.0,
            "total_insiden": 0,
            "total_cve": 0,
            "total_insiden_baseline": 0,
            "total_cve_baseline": 0,
        }

    df_terkini, df_baseline = _split_periode(df_riwayat)

    def _hitung_sub_posture(df_sub: pd.DataFrame) -> tuple:
        if df_sub.empty:
            return 1.0, 0, 0, 0.0
        df_b = df_sub[df_sub["kategori"] == "berita"]
        df_c = df_sub[df_sub["kategori"] == "cve"]
        n_insiden = int((df_b["kategori_relevansi"] == "insiden_spesifik").sum()) if not df_b.empty else 0
        n_cve = len(df_c)
        avg_c = round(float(df_c["skor_cvss"].dropna().mean()), 1) if not df_c.empty and df_c["skor_cvss"].notna().any() else 0.0
        skor_raw = min(10.0, max(1.0, (n_insiden * 0.035) + (n_cve * 0.012) + (avg_c * 0.35)))
        return round(skor_raw, 1), n_insiden, n_cve, avg_c

    skor_terkini, total_insiden, total_cve, avg_cvss = _hitung_sub_posture(df_terkini)
    skor_baseline, total_insiden_base, total_cve_base, _ = _hitung_sub_posture(df_baseline)

    growth = _hitung_growth(int(skor_terkini * 10), int(skor_baseline * 10))
    if growth > 5.0:
        status_tren = "Meningkat"
    elif growth < -5.0:
        status_tren = "Menurun"
    else:
        status_tren = "Stabil"

    if skor_terkini >= 8.0:
        level = "KRITIS"
        level_label = "KRITIS (Critical)"
        warna = "red"
    elif skor_terkini >= 6.0:
        level = "TINGGI"
        level_label = "TINGGI (Elevated)"
        warna = "amber"
    elif skor_terkini >= 4.0:
        level = "SEDANG"
        level_label = "SEDANG (Moderate)"
        warna = "blue"
    else:
        level = "RENDAH"
        level_label = "RENDAH (Low)"
        warna = "green"

    return {
        "skor": skor_terkini,
        "skor_baseline": skor_baseline,
        "level": level,
        "level_label": level_label,
        "warna": warna,
        "growth_persen": growth,
        "status_tren": status_tren,
        "avg_cvss": avg_cvss,
        "total_insiden": total_insiden,
        "total_cve": total_cve,
        "total_insiden_baseline": total_insiden_base,
        "total_cve_baseline": total_cve_base,
        "cve_growth": _hitung_growth(total_cve, total_cve_base),
    }



def hitung_matriks_tindakan_ancaman(
    df_riwayat: pd.DataFrame, df_berita_dedup: Optional[pd.DataFrame] = None
) -> List[Dict]:
    """
    Menyusun Matriks Tindakan Ancaman Mingguan untuk proteksi website dan sistem:
    Memetakan kategori ancaman spesifik, status tren lonjakan, dan tindakan taktis.
    """
    if df_berita_dedup is not None:
        df_terkini_dedup, df_baseline_dedup = _split_periode(df_berita_dedup)
    else:
        df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
        if df_berita.empty:
            return []
        df_terkini, df_baseline = _split_periode(df_berita)
        df_terkini_dedup = _dedup_ringan_lintas_hari(df_terkini)
        df_baseline_dedup = _dedup_ringan_lintas_hari(df_baseline)

    kategori_ancaman_definisi = ConfigLoader.get_rules("kategori_ancaman")


    matriks = []
    for item in kategori_ancaman_definisi:
        kws = item["keywords"]

        def _hitung_frekuensi(df_sub: pd.DataFrame) -> int:
            if df_sub.empty:
                return 0
            cnt = 0
            for _, r in df_sub.iterrows():
                t = f"{r.get('judul', '')} {r.get('ringkasan_atau_narasi', '')} {r.get('kata_kunci', '')}".lower()
                if any(kw in t for kw in kws):
                    cnt += 1
            return cnt

        cnt_terkini = _hitung_frekuensi(df_terkini_dedup)
        cnt_baseline = _hitung_frekuensi(df_baseline_dedup)
        growth = _hitung_growth(cnt_terkini, cnt_baseline)

        urg_cfg = ConfigLoader.get_config().get("cti_analysis", {}).get("threat_posture", {}).get("urgency", {"kritis_count": 4, "kritis_growth": 50.0})
        if cnt_terkini >= urg_cfg["kritis_count"] or growth >= urg_cfg["kritis_growth"]:
            level_urgensi = "KRITIS"
            badge_warna = "red"
        elif cnt_terkini >= 2 or growth > 0:
            level_urgensi = "TINGGI"
            badge_warna = "amber"
        elif cnt_terkini > 0:
            level_urgensi = "SEDANG"
            badge_warna = "blue"
        else:
            level_urgensi = "MONITOR"
            badge_warna = "slate"

        matriks.append({
            "id": item["id"],
            "kategori": item["kategori"],
            "ikon": item["ikon"],
            "warna": item["warna"],
            "jumlah_terkini": cnt_terkini,
            "jumlah_baseline": cnt_baseline,
            "growth_persen": growth,
            "level_urgensi": level_urgensi,
            "badge_warna": badge_warna,
            "fokus_website": item["fokus_website"],
            "tindakan_taktis": item["tindakan_taktis"],
        })

    matriks.sort(key=lambda x: (x["level_urgensi"] in ["KRITIS", "TINGGI"], x["growth_persen"], x["jumlah_terkini"]), reverse=True)
    return matriks


# Media Cybersecurity Internasional (RSS Resmi Luar Negeri)


# Entitas Geografis Murni Jawa Timur (Provinsi + 29 Kabupaten + 9 Kota)
# Tanpa hardcode nama instansi/OPD karena instansi lokal selalu mengandung unsur "Jatim"/"Jawa Timur" atau nama kota/kabupatennya.


_KEYWORDS_JATIM_REGEX = re.compile(
    r'\b(?:' + '|'.join(re.escape(k) for k in ConfigLoader.get_rules("keywords_jawa_timur")) + r')\b',
    re.IGNORECASE
)

# Regex pembersihan dateline jurnalis di awal narasi (misal: "SURABAYA, Kompas.com - ", "SURABAYA - ")
_REGEX_DATELINE = re.compile(
    r'^(?:[A-Z\s]{3,25}(?:\([^\)]+\)|,\s*[^–\-\n]+)?\s*[-–—]\s*)'
)

# Entitas tingkat nasional murni (mencegah artikel nasional yang diliput media Jatim masuk ke Jatim)
_ENTITAS_NASIONAL_REGEX = re.compile(
    r'\b(?:pusat data nasional|pdn|kpu ri|kpu pusat|kemenkes|kemhan|kementerian|mabes polri|'
    r'bareskrim|bssn|dpr ri|kejaksaan agung|bank indonesia|ojk pusat|bpjs)\b',
    re.IGNORECASE
)


def _bersihkan_judul_dan_publisher(judul_raw: str, sumber_raw: str) -> tuple[str, str]:
    """
    Memisahkan judul berita asli dari nama publisher/media di akhir judul.
    Contoh: 'PDN Diretas - Detik Jatim' -> ('PDN Diretas', 'Detik Jatim')
    Pembersihan dilakukan secara berulang untuk menangani duplikasi suffix dari agregator RSS.
    """
    judul = str(judul_raw or "").strip()
    sumber = str(sumber_raw or "").strip()
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
    if any(k in t for k in ["zero-day", "celah", "vulnerability", "exploit", "cve"]):
        return "Eksploitasi Celah"
    return "Insiden Siber"


def hitung_kasus_insiden_wilayah(df_riwayat: pd.DataFrame, top_n_per_wilayah: int = 5) -> Dict[str, List[Dict]]:
    """
    Mengidentifikasi kasus insiden siber yang sedang ramai selama 7 hari terakhir
    pada 3 level wilayah: Internasional, Nasional, dan Jawa Timur.
    
    Fitur khusus:
    - Jawa Timur mendeteksi penyebutan daerah kabupaten/kota & instansi Pemprov/BUMD Jawa Timur.
      Jika tidak ada kasus insiden siber dalam 7 hari terakhir, mengembalikan list kosong []
      (ditampilkan '-' pada antarmuka dashboard).
    - Menerapkan deduplikasi / clustering liputan serupa menggunakan RapidFuzz untuk
      menghitung 'jumlah_liputan' media sebagai indikator isu yang 'sedang ramai'.
    - Pembersihan otomatis nama publisher portal berita (mis. dari Google News RSS).
    """
    hasil_kosong = {"internasional": [], "nasional": [], "jawa_timur": []}
    if df_riwayat.empty:
        return hasil_kosong

    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
    if df_berita.empty:
        return hasil_kosong

    # Ambil periode terkini (7 hari)
    df_berita["tgl"] = df_berita["tanggal_publish"].fillna("").astype(str).str.slice(0, 10)
    tanggal_unik = sorted(df_berita[df_berita["tgl"].str.match(r"^\d{4}-\d{2}-\d{2}$")]["tgl"].unique(), reverse=True)
    tanggal_terkini = set(tanggal_unik[:HARI_PERIODE_TERKINI])
    df_terkini = df_berita[df_berita["tgl"].isin(tanggal_terkini)].copy()

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

        df_sorted = df_insiden.sort_values(by=["tanggal_publish"], ascending=False).reset_index(drop=True)
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
                "tanggal": str(row_i.get("tgl", "")),
                "ringkasan": str(row_i.get("ringkasan_atau_narasi", ""))[:150],
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

        # Urutkan berdasarkan: intensitas liputan media (sedang ramai), skor relevansi, tanggal terbaru
        clusters.sort(
            key=lambda x: (x["jumlah_liputan"], x["skor_relevansi"], x["tanggal"]),
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

        is_intl = sumber_raw in _SUMBER_INTERNASIONAL or pub_tampil in _SUMBER_INTERNASIONAL

        # Evaluasi lokasi kejadian HANYA berdasarkan konten berita bersih (judul & narasi tanpa dateline & tanpa publisher)
        teks_konten_bersih = f"{judul_bersih} {narasi_bersih} {kata_kunci_raw}".lower()
        matches_jatim = bool(_KEYWORDS_JATIM_REGEX.search(teks_konten_bersih))

        is_jatim = False
        if matches_jatim and not is_intl:
            # Validasi ketat: cegah artikel nasional yang diliput media lokal Jatim keliru masuk Jatim
            # atau sekadar opini/tanggapan pakar kampus lokal atas isu peretasan nasional
            target_nasional = bool(_ENTITAS_NASIONAL_REGEX.search(judul_bersih))
            opini_pakar = any(p in judul_bersih.lower() for p in ["pakar", "analisis", "tanggapi", "komentari", "soroti", "minta", "dosen"])
            ada_target_lokal_eksplisit = any(k in judul_bersih.lower() for k in [
                "jatim", "jawa timur", "surabaya", "sidoarjo", "pamekasan", "malang",
                "lumajang", "gresik", "banyuwangi", "jember", "kediri", "madiun", "blitar",
                "mojokerto", "pasuruan", "probolinggo", "tuban", "bojonegoro"
            ])

            if target_nasional and opini_pakar:
                is_jatim = False
            elif target_nasional and not ada_target_lokal_eksplisit:
                is_jatim = False
            else:
                is_jatim = True

        if is_jatim:
            rows_jatim.append(row)
        elif is_intl:
            rows_intl.append(row)
        else:
            rows_nasional.append(row)

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
            "cve": {},
            "vektor_serangan": [],
            "sektor_target": [],
            "threat_posture": {
                "skor": 1.0,
                "level": "RENDAH",
                "level_label": "RENDAH (Low)",
                "warna": "green",
                "growth_persen": 0.0,
                "status_tren": "Stabil",
            },
            "matriks_tindakan": [],
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
        "cve": {
            "vendor_naik": hitung_tren_vendor_cve(df_riwayat, top_n=10),
        },
        "vektor_serangan": hitung_tren_vektor_serangan(df_riwayat, df_berita_dedup=df_berita_dedup),
        "sektor_target": hitung_tren_sektor_target(df_riwayat, df_berita_dedup=df_berita_dedup),
        "threat_posture": hitung_skor_threat_posture(df_riwayat),
        "matriks_tindakan": hitung_matriks_tindakan_ancaman(df_riwayat, df_berita_dedup=df_berita_dedup),
        "kasus_wilayah": hitung_kasus_insiden_wilayah(df_riwayat),
    }

    logger.info(
        f"Statistik tren mingguan tersusun: {len(statistik['berita']['kata_kunci_naik'])} kata kunci naik, "
        f"{len(statistik['cve']['vendor_naik'])} vendor CVE naik, "
        f"Threat Posture {statistik['threat_posture']['level_label']} ({statistik['threat_posture']['skor']}/10 - {statistik['threat_posture']['status_tren']}), "
        f"{len(statistik['matriks_tindakan'])} kategori matriks tindakan, "
        f"Kasus Wilayah: Intl={len(statistik['kasus_wilayah']['internasional'])}, Nas={len(statistik['kasus_wilayah']['nasional'])}, Jatim={len(statistik['kasus_wilayah']['jawa_timur'])}."
    )
    return statistik


def susun_statistik_dashboard(df_riwayat: pd.DataFrame, statistik_tren: Optional[dict] = None) -> dict:
    """
    Menyusun seluruh agregat statistik visualisasi dashboard (KPI, grafik harian, distribusi sumber & CVSS).
    Dihitung sekali saat pipeline pasca-proses selesai dan disimpan ke database agar tampilan web instan.
    """
    statistik_kosong = {
        "total_berita": 0, "total_cve": 0, "total_vendor_cve": 0, "avg_cvss": 0,
        "kata_kunci_naik": [], "vendor_naik": [], "sampel_judul_insiden": [],
        "tren_kategori": {}, "severity_breakdown": {}, "harian": [],
        "distribusi_cvss": [], "distribusi_sumber": [],
        "nasional_vs_internasional": {"nasional": 0, "internasional": 0},
        "komposisi_jenis": {}, "harian_sumber": [], "vektor_serangan": [],
        "matriks_tindakan": [],
        "threat_posture": {"skor": 1.0, "skor_baseline": 1.0, "level": "RENDAH", "level_label": "RENDAH (Low)", "warna": "green", "growth_persen": 0.0, "status_tren": "Stabil"},
        "kasus_wilayah": {"internasional": [], "nasional": [], "jawa_timur": []},
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
    df_cve = df_7[df_7["kategori"] == "cve"]

    total_berita = len(df_berita)
    total_cve = len(df_cve)
    total_vendor_cve = len(df_cve["vendor"].dropna().unique()) if not df_cve.empty and "vendor" in df_cve.columns else 0
    avg_cvss = round(float(df_cve["skor_cvss"].dropna().mean()), 1) if not df_cve.empty and df_cve["skor_cvss"].notna().any() else 0.0

    severity_counts = df_cve["severity"].dropna().value_counts().to_dict() if not df_cve.empty else {}

    # Chart Harian
    harian_list = []
    for tgl in tanggal_urut:
        df_tgl = df_7[df_7["tgl"] == tgl]
        harian_list.append({
            "tanggal": tgl,
            "berita": int((df_tgl["kategori"] == "berita").sum()),
            "cve": int((df_tgl["kategori"] == "cve").sum()),
        })

    # Distribusi CVSS
    cvss_bins = []
    if not df_cve.empty:
        cvss_vals = df_cve["skor_cvss"].dropna()
        cvss_bins = [
            {"label": "10.0", "jumlah": int((cvss_vals == 10.0).sum())},
            {"label": "9.5 - 9.9", "jumlah": int(((cvss_vals >= 9.5) & (cvss_vals < 10.0)).sum())},
            {"label": "9.0 - 9.4", "jumlah": int(((cvss_vals >= 9.0) & (cvss_vals < 9.5)).sum())},
        ]

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
        pola_serangan = {"pola": "RCE", "growth_persen": 0.0, "subteks": "Stabil"}
        ancaman_baru = "Menunggu Sinyal"

    return {
        "total_berita": total_berita,
        "total_cve": total_cve,
        "total_vendor_cve": total_vendor_cve,
        "cve_growth": statistik.get("threat_posture", {}).get("cve_growth", 0.0),
        "avg_cvss": avg_cvss,
        "ancaman_baru": ancaman_baru,
        "kata_kunci_naik": statistik.get("berita", {}).get("kata_kunci_naik", []),
        "vendor_naik": statistik.get("cve", {}).get("vendor_naik", []),
        "sampel_judul_insiden": statistik.get("berita", {}).get("sampel_judul_insiden", []),
        "tren_kategori": statistik.get("berita", {}).get("tren_kategori", {}),
        "threat_posture": statistik.get("threat_posture", {"skor": 1.0, "skor_baseline": 1.0, "level": "RENDAH", "level_label": "RENDAH (Low)", "warna": "green", "growth_persen": 0.0, "status_tren": "Stabil"}),
        "sektor_target": statistik.get("sektor_target", []),
        "severity_breakdown": severity_counts,
        "harian": harian_list,
        "distribusi_cvss": cvss_bins,
        "distribusi_sumber": distribusi_sumber,
        "nasional_vs_internasional": {"nasional": nasional_count, "internasional": internasional_count},
        "komposisi_jenis": komposisi_jenis,
        "harian_sumber": harian_sumber,
        "vektor_serangan": statistik.get("vektor_serangan", []),
        "matriks_tindakan": statistik.get("matriks_tindakan", []),
        "kasus_wilayah": statistik.get("kasus_wilayah", {"internasional": [], "nasional": [], "jawa_timur": []}),
        "prediksi_pola_serangan": pola_serangan,
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

    print("\n=== VENDOR CVE NAIK ===")
    for v in hasil["cve"]["vendor_naik"]:
        print(f"  {v['vendor']}: {v['jumlah_terkini']} (baseline {v['jumlah_baseline']}) growth {v['growth_persen']}%")