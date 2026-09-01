"""
Analisis tren statistik dari riwayat_tren (7 hari terakhir). Modul ini
MURNI perhitungan Python (tanpa LLM) - tugasnya menghasilkan angka yang
pasti dan bisa diverifikasi, sebagai dasar objektif sebelum dinarasikan
oleh LLM di modul trend_predictor.py.

Prinsip pembagian periode: window 7 hari dibagi jadi
- periode TERKINI: 3 hari terakhir
- periode BASELINE: 4 hari sebelumnya
Growth dihitung dari rata-rata HARIAN (bukan total mentah), karena
panjang kedua periode berbeda (3 vs 4 hari).
"""
from rapidfuzz import fuzz
from datetime import datetime, timedelta
from typing import Dict, List

import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

HARI_PERIODE_TERKINI = 3
THRESHOLD_DEDUP_TREN = 88  
HARI_PERIODE_BASELINE = 4  # total window tetap 7 hari (3 + 4)


def _split_periode(df: pd.DataFrame, kolom_tanggal: str = "tanggal_publish") -> tuple:
    """Membagi df jadi 2 subset: periode terkini (3 tanggal unik terbaru) vs baseline (4 tanggal unik sebelumnya)."""
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


def hitung_tren_kata_kunci_berita(df_riwayat: pd.DataFrame, top_n: int = 8) -> List[Dict]:
    """
    Menghitung tren kemunculan tiap kata kunci individual dari kolom
    'kata_kunci' (string dipisah koma) pada baris berkategori 'berita'.
    Mengembalikan top-N kata kunci dengan growth tertinggi.
    """
    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
    if df_berita.empty:
        return []
    df_berita = _dedup_ringan_lintas_hari(df_berita)   

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


def hitung_tren_kategori_berita(df_riwayat: pd.DataFrame) -> Dict:
    """
    Tren jumlah insiden_spesifik vs analisis_relevan antara periode
    terkini vs baseline - indikator kasar apakah volume insiden NYATA
    (bukan cuma pembahasan umum) sedang naik.
    """
    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
    if df_berita.empty:
        return {"insiden_spesifik": None, "analisis_relevan": None}
    df_berita = _dedup_ringan_lintas_hari(df_berita)

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

def ambil_sampel_judul_insiden(df_riwayat: pd.DataFrame, maks: int = 15) -> List[Dict]:
    """
    Mengambil sampel judul artikel insiden_spesifik dari periode TERKINI
    (3 hari terakhir), sudah di-dedup ringan supaya 1 insiden yang
    di-follow-up berkali-kali tidak mendominasi sampel. Dipakai sebagai
    konteks KONKRET untuk LLM mengenali JENIS pola insiden - bukan cuma
    angka kata kunci abstrak.
    """
    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
    if df_berita.empty:
        return []
    df_berita = _dedup_ringan_lintas_hari(df_berita)

    df_terkini, _ = _split_periode(df_berita)
    df_insiden = df_terkini[df_terkini["kategori_relevansi"] == "insiden_spesifik"]

    return [
        {"judul": row["judul"], "sumber": row["sumber"]}
        for _, row in df_insiden.head(maks).iterrows()
    ]


def hitung_tren_vendor_cve(df_riwayat: pd.DataFrame, top_n: int = 8, top_produk_per_vendor: int = 3) -> List[Dict]:
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


VEKTOR_RULES = {
    "Weaponized AI & Botnet": ["ai", "claude", "otonom", "botnet", "ddos", "tsunami"],
    "Malware & Infostealer": ["malware", "trojan", "stealer", "lumma", "infostealer", "spynote", "toxicpanda", "grandoreiro", "virus", "spyware"],
    "Eksploitasi Celah RCE": ["celah", "exploit", "rce", "zero-day", "0-day", "bypass", "kerentanan", "vulnerability", "overflow", "flaw"],
    "Phishing & Social Engineering": ["phishing", "email", "sms", "smishing", "vishing", "brandname", "kuota", "bansos"],
    "Ransomware & Pemerasan": ["ransomware", "tebusan", "jadepuffer", "pemerasan"],
    "Supply Chain & Repositori": ["supply chain", "crate", "rubygems", "npm", "pypi", "repository", "package", "poison"],
    "Pembajakan Akun & Kredensial": ["credential", "stuffing", "bajak", "take over", "screen sharing", "password"],
}

SEKTOR_RULES = {
    "Pengembang & Infrastruktur TI": ["developer", "rust", "wordpress", "netscaler", "citrix", "vmware", "unix", "apple", "windows", "dns", "server", "jaringan", "cdn", "cloud"],
    "Pengguna & Konsumen Ritel": ["whatsapp", "iphone", "android", "kartu", "game", "gta", "jungkook", "warga", "pengguna", "masyarakat"],
    "Korporasi & Enterprise": ["perusahaan", "alation", "netflix", "brinks", "pnld", "bisnis", "bumn", "umkm", "industri"],
    "Pemerintahan & Instansi Publik": ["pemerintah", "pemda", "polres", "polri", "kementerian", "dprd", "tangsel", "berlin", "bgn", "bpjs", "nuklir", "taiwan", "pemkot", "desa", "irs"],
    "Finansial, Bank & Kripto": ["bank", "keuangan", "bitcoin", "kripto", "btc", "dompet", "coldcard", "swiss", "pajak", "transaksi", "visa", "biocatch", "ethereum"],
}


def hitung_tren_vektor_serangan(df_riwayat: pd.DataFrame) -> List[Dict]:
    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
    if df_berita.empty:
        return []
    df_berita = _dedup_ringan_lintas_hari(df_berita)

    vektor_counts = {v: 0 for v in VEKTOR_RULES}
    for _, row in df_berita.iterrows():
        teks = (str(row.get("judul", "")) + " " + str(row.get("ringkasan_atau_narasi", "")) + " " + str(row.get("kata_kunci", ""))).lower()
        for v_nama, v_words in VEKTOR_RULES.items():
            if any(w in teks for w in v_words):
                vektor_counts[v_nama] += 1

    hasil = [{"vektor": v, "jumlah": c} for v, c in vektor_counts.items()]
    hasil.sort(key=lambda x: x["jumlah"], reverse=True)
    return hasil


def hitung_tren_sektor_target(df_riwayat: pd.DataFrame) -> List[Dict]:
    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"].copy()
    if df_berita.empty:
        return []
    df_berita = _dedup_ringan_lintas_hari(df_berita)

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
    if df_riwayat.empty:
        return {"skor": 1.0, "level": "RENDAH", "level_label": "RENDAH (Low)", "warna": "green"}

    df_berita = df_riwayat[df_riwayat["kategori"] == "berita"]
    df_cve = df_riwayat[df_riwayat["kategori"] == "cve"]

    total_insiden = int((df_berita["kategori_relevansi"] == "insiden_spesifik").sum()) if not df_berita.empty else 0
    total_cve = len(df_cve)
    avg_cvss = round(float(df_cve["skor_cvss"].dropna().mean()), 1) if not df_cve.empty and df_cve["skor_cvss"].notna().any() else 0.0

    skor_raw = min(10.0, max(1.0, (total_insiden * 0.035) + (total_cve * 0.012) + (avg_cvss * 0.35)))
    skor = round(skor_raw, 1)

    if skor >= 8.0:
        level = "KRITIS"
        level_label = "KRITIS (Critical)"
        warna = "red"
    elif skor >= 6.0:
        level = "TINGGI"
        level_label = "TINGGI (Elevated)"
        warna = "amber"
    elif skor >= 4.0:
        level = "SEDANG"
        level_label = "SEDANG (Moderate)"
        warna = "blue"
    else:
        level = "RENDAH"
        level_label = "RENDAH (Low)"
        warna = "green"

    return {
        "skor": skor,
        "level": level,
        "level_label": level_label,
        "warna": warna,
        "avg_cvss": avg_cvss,
        "total_insiden": total_insiden,
        "total_cve": total_cve,
    }


def susun_ringkasan_statistik_tren(df_riwayat: pd.DataFrame) -> Dict:
    """
    Titik masuk utama modul ini: menyusun seluruh statistik tren jadi satu
    dict terstruktur, mencakup domain berita, cve, threat posture, TTPs, dan sektor target.
    """
    if df_riwayat.empty:
        logger.info("riwayat_tren kosong, tidak ada statistik tren yang bisa dihitung.")
        return {
            "berita": {"kata_kunci_naik": [], "tren_kategori": {"insiden_spesifik": None, "analisis_relevan": None}},
            "cve": {"vendor_naik": []},
            "vektor_serangan": [],
            "sektor_target": [],
            "threat_posture": {"skor": 1.0, "level": "RENDAH", "level_label": "RENDAH (Low)", "warna": "green"},
        }

    statistik = {
        "berita": {
            "kata_kunci_naik": hitung_tren_kata_kunci_berita(df_riwayat),
            "tren_kategori": hitung_tren_kategori_berita(df_riwayat),
            "sampel_judul_insiden": ambil_sampel_judul_insiden(df_riwayat),
        },
        "cve": {
            "vendor_naik": hitung_tren_vendor_cve(df_riwayat),
        },
        "vektor_serangan": hitung_tren_vektor_serangan(df_riwayat),
        "sektor_target": hitung_tren_sektor_target(df_riwayat),
        "threat_posture": hitung_skor_threat_posture(df_riwayat),
    }
    logger.info(
        f"Statistik tren tersusun: {len(statistik['berita']['kata_kunci_naik'])} kata kunci naik, "
        f"{len(statistik['cve']['vendor_naik'])} vendor CVE naik, "
        f"Threat Posture {statistik['threat_posture']['level_label']} ({statistik['threat_posture']['skor']}/10)."
    )
    return statistik


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