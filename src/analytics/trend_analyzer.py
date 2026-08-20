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


def _split_periode(df: pd.DataFrame, kolom_tanggal: str = "tanggal_dicatat") -> tuple:
    """Membagi df jadi 2 subset: periode terkini vs baseline, berdasarkan tanggal_dicatat."""
    if df.empty:
        return df, df

    df = df.copy()
    df[kolom_tanggal] = pd.to_datetime(df[kolom_tanggal])
    sekarang = datetime.now()
    batas_terkini = sekarang - timedelta(days=HARI_PERIODE_TERKINI)
    batas_baseline = sekarang - timedelta(days=HARI_PERIODE_TERKINI + HARI_PERIODE_BASELINE)

    df_terkini = df[df[kolom_tanggal] >= batas_terkini]
    df_baseline = df[(df[kolom_tanggal] >= batas_baseline) & (df[kolom_tanggal] < batas_terkini)]
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

    df_berita = df_berita.sort_values("tanggal_dicatat").reset_index(drop=True)
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


def hitung_tren_vendor_cve(df_riwayat: pd.DataFrame, top_n: int = 8) -> List[Dict]:
    """
    Tren jumlah CVE per vendor antara periode terkini vs baseline. Vendor
    'Lainnya / Belum Teridentifikasi' dikecualikan karena tidak actionable
    buat pembaca (bukan nama vendor yang jelas).
    """
    df_cve = df_riwayat[df_riwayat["kategori"] == "cve"].copy()
    df_cve = df_cve[df_cve["vendor"].notna() & (df_cve["vendor"] != "Lainnya / Belum Teridentifikasi")]
    if df_cve.empty:
        return []

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
        jumlah_critical_terkini = int((df_terkini[df_terkini["vendor"] == vendor]["severity"] == "CRITICAL").sum())
        hasil.append({
            "vendor": vendor,
            "jumlah_terkini": jumlah_terkini,
            "jumlah_baseline": jumlah_baseline,
            "jumlah_critical_terkini": jumlah_critical_terkini,
            "growth_persen": _hitung_growth(jumlah_terkini, jumlah_baseline),
        })

    hasil.sort(key=lambda x: (x["growth_persen"], x["jumlah_terkini"]), reverse=True)
    return hasil[:top_n]


def susun_ringkasan_statistik_tren(df_riwayat: pd.DataFrame) -> Dict:
    """
    Titik masuk utama modul ini: menyusun seluruh statistik tren jadi satu
    dict, dipisah jelas antara domain 'berita' dan 'cve' - supaya modul
    trend_predictor.py (LLM) bisa memprosesnya jadi 2 narasi terpisah.
    """
    if df_riwayat.empty:
        logger.info("riwayat_tren kosong, tidak ada statistik tren yang bisa dihitung.")
        return {
            "berita": {"kata_kunci_naik": [], "tren_kategori": {"insiden_spesifik": None, "analisis_relevan": None}},
            "cve": {"vendor_naik": []},
        }

    statistik = {
        "berita": {
            "kata_kunci_naik": hitung_tren_kata_kunci_berita(df_riwayat),
            "tren_kategori": hitung_tren_kategori_berita(df_riwayat),
        },
        "cve": {
            "vendor_naik": hitung_tren_vendor_cve(df_riwayat),
        },
    }
    logger.info(
        f"Statistik tren tersusun: {len(statistik['berita']['kata_kunci_naik'])} kata kunci naik, "
        f"{len(statistik['cve']['vendor_naik'])} vendor CVE naik."
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