"""
Tahap PASCA-summarization: mencatat hasil akhir (sudah ada ringkasan/narasi
dari LLM) ke riwayat_tren untuk 2 kebutuhan sekaligus - tab Arsip (riwayat
7 hari lengkap) dan analisis tren. Dipanggil setelah proses_summarization_harian()
selesai, BUKAN di dalam pipeline_harian.py atau llm_summarizer.py, supaya
kedua modul itu tetap fokus di tanggung jawabnya masing-masing.
"""
from pathlib import Path
from typing import Dict, List

from src.analytics.trend_analyzer import susun_ringkasan_statistik_tren
from src.analytics.trend_predictor import proses_prediksi_tren
from src.storage.db import (
    DEFAULT_DB_PATH,
    ambil_riwayat_tren,
    bersihkan_riwayat_tren_lama,
    catat_untuk_tren,
    simpan_prediksi_tren,
)
from src.storage.db import (
    DEFAULT_DB_PATH,
    ambil_riwayat_tren,
    bersihkan_riwayat_tren_lama,
    catat_terkirim,
    catat_untuk_tren,
    simpan_prediksi_tren,
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _susun_item_arsip_berita(df_berita_ringkas) -> List[Dict]:
    """Meratakan DataFrame berita (sudah ada kolom 'ringkasan') jadi list dict siap disimpan."""
    return [
        {
            "kategori": "berita",
            "identifier": row["link"],
            "judul": row["judul"],
            "sumber": row["sumber"],
            "kata_kunci": row.get("kata_kunci", ""),
            "kategori_relevansi": row.get("kategori_relevansi", ""),
            "severity": "",
            "vendor": "",
            "tanggal_publish": row.get("tanggal", ""),
            "ringkasan_atau_narasi": row.get("ringkasan", ""),
            "link": row["link"],
        }
        for _, row in df_berita_ringkas.iterrows()
    ]


import re
from src.scraper.cve_fetcher import _ATURAN_EKOSISTEM_VENDOR, ekstrak_produk_cve


def _susun_item_arsip_cve(cve_struktur: Dict) -> List[Dict]:
    """Meratakan struktur CVE (sudah ada 'narasi') jadi list dict siap disimpan."""
    if cve_struktur.get("mode") != "ada_critical":
        return []
    hasil = []
    for grup in cve_struktur["grup_critical"]:
        for cve in grup["cve_list"]:
            vendor = grup.get("vendor", "")
            narasi = cve.get("narasi", "")
            produk = cve.get("produk", "")

            # Fallback cerdas: jika vendor masih belum teridentifikasi, cek dari narasi LLM
            if not vendor or vendor == "Lainnya / Belum Teridentifikasi":
                teks_cari = f"{produk} {narasi}"
                for pola, vendor_name in _ATURAN_EKOSISTEM_VENDOR:
                    if re.search(pola, teks_cari, re.IGNORECASE):
                        vendor = vendor_name
                        break

            # Fallback produk jika masih kosong atau (lihat deskripsi) / -
            if not produk or produk in ["-", "(lihat deskripsi)", "Lainnya / Belum Teridentifikasi"]:
                produk = ekstrak_produk_cve(narasi_id=narasi, vendor=vendor)

            hasil.append({
                "kategori": "cve",
                "identifier": cve["cve_id"],
                "judul": cve["cve_id"],
                "sumber": "NVD",
                "kata_kunci": "",
                "kategori_relevansi": "",
                "severity": cve.get("severity", ""),
                "vendor": vendor if vendor else "Lainnya / Belum Teridentifikasi",
                "tanggal_publish": cve.get("tanggal_publish", ""),
                "ringkasan_atau_narasi": narasi,
                "link": cve["link"],
                "skor_cvss": cve.get("skor_cvss"),
                "produk": produk,
            })
    return hasil


def proses_arsip_dan_tren(hasil_ringkas: Dict, db_path: Path = DEFAULT_DB_PATH) -> Dict:
    """
    Titik masuk utama: menerima hasil dari proses_summarization_harian()
    (berita + cve_struktur yang SUDAH ada ringkasan/narasi), mencatatnya ke
    riwayat_tren untuk Arsip, menghitung statistik tren, lalu meminta LLM
    menarasikan prediksi tren. Mengembalikan hasil_ringkas yang sama, plus
    key baru 'prediksi_tren'.
    """
    logger.info("=" * 60)
    logger.info("MENCATAT ARSIP & MENGHITUNG TREN")
    logger.info("=" * 60)

    item_arsip = (
        _susun_item_arsip_berita(hasil_ringkas["berita"])
        + _susun_item_arsip_cve(hasil_ringkas["cve_struktur"])
    )

    # Bersihkan data > 7 hari DULU, baru catat data hari ini - supaya window
    # arsip & tren selalu "bergeser" (rolling), bukan menumpuk selamanya.
    bersihkan_riwayat_tren_lama(hari_retensi=7, db_path=db_path)

    if item_arsip:
        catat_untuk_tren(item_arsip, db_path)
    else:
        logger.info("Tidak ada item baru untuk dicatat ke riwayat_tren pada run ini.")

    # Tandai semua item run ini sebagai "sudah diproses", supaya run
    # berikutnya (filter_belum_terkirim di pipeline_harian.py) tidak
    # mengambil & memproses ulang artikel/CVE yang sama selama masih
    # dalam window waktu.
    item_berita = [i for i in item_arsip if i["kategori"] == "berita"]
    item_cve = [i for i in item_arsip if i["kategori"] == "cve"]

    if item_berita:
        catat_terkirim(
            [{"identifier": i["identifier"], "judul": i["judul"], "sumber": i["sumber"]} for i in item_berita],
            kategori="berita", db_path=db_path,
        )
    if item_cve:
        catat_terkirim(
            [{"identifier": i["identifier"], "judul": i["judul"], "sumber": i["sumber"]} for i in item_cve],
            kategori="cve", db_path=db_path,
        )

    df_riwayat = ambil_riwayat_tren(hari=7, db_path=db_path)
    statistik_tren = susun_ringkasan_statistik_tren(df_riwayat)
    prediksi_tren = proses_prediksi_tren(statistik_tren)

    simpan_prediksi_tren(
        prediksi_tren["prediksi_berita"], prediksi_tren["prediksi_cve"], db_path
    )

    logger.info("SELESAI MENCATAT ARSIP & MENGHITUNG TREN.")

    return {**hasil_ringkas, "prediksi_tren": prediksi_tren}