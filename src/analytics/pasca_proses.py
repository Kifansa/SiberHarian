"""
Tahap PASCA-summarization: mencatat hasil akhir (sudah ada ringkasan/narasi
dari LLM) ke riwayat_tren untuk 2 kebutuhan sekaligus - tab Arsip (riwayat
7 hari lengkap) dan analisis tren. Dipanggil setelah proses_summarization_harian()
selesai, BUKAN di dalam pipeline_harian.py atau llm_summarizer.py, supaya
kedua modul itu tetap fokus di tanggung jawabnya masing-masing.
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from src.analytics.trend_analyzer import susun_ringkasan_statistik_tren, susun_statistik_dashboard
from src.analytics.trend_predictor import proses_prediksi_tren
from src.storage.db import (
    DEFAULT_DB_PATH,
    ambil_riwayat_tren,
    bersihkan_riwayat_tren_lama,
    catat_terkirim,
    catat_untuk_tren,
    simpan_metadata,
    simpan_prediksi_tren,
)
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _susun_item_arsip_berita(df_berita_ringkas) -> List[Dict]:
    """Meratakan DataFrame berita (sudah ada kolom 'ringkasan') jadi list dict siap disimpan."""
    if df_berita_ringkas.empty:
        return []
    df = df_berita_ringkas.copy()
    df['kategori'] = 'berita'
    df['identifier'] = df['link']
    df['severity'] = ''
    df['vendor'] = ''
    df['tanggal_publish'] = df.get('tanggal', '')
    df['ringkasan_atau_narasi'] = df.get('ringkasan', '')
    
    if 'kata_kunci' not in df.columns:
        df['kata_kunci'] = ''
    if 'kategori_relevansi' not in df.columns:
        df['kategori_relevansi'] = ''
        
    cols = ['kategori', 'identifier', 'judul', 'sumber', 'kata_kunci', 'kategori_relevansi', 
            'severity', 'vendor', 'tanggal_publish', 'ringkasan_atau_narasi', 'link']
    return df[cols].to_dict('records')


def proses_arsip_dan_tren(hasil_ringkas: Dict, db_path: Path = DEFAULT_DB_PATH) -> Dict:
    """
    Titik masuk utama: menerima hasil dari proses_summarization_harian()
    (berita yang SUDAH ada ringkasan), mencatatnya ke riwayat_tren untuk
    Arsip, menghitung statistik tren, lalu meminta LLM menarasikan prediksi
    tren. Mengembalikan hasil_ringkas yang sama, plus key baru 'prediksi_tren'.
    """
    logger.info("=" * 60)
    logger.info("MENCATAT ARSIP & MENGHITUNG TREN")
    logger.info("=" * 60)

    item_arsip = _susun_item_arsip_berita(hasil_ringkas["berita"])

    # Bersihkan data > 14 hari DULU, baru catat data hari ini - supaya window
    # arsip & tren selalu "bergeser" (rolling), bukan menumpuk selamanya.
    bersihkan_riwayat_tren_lama(hari_retensi=ConfigLoader.get_config().get("cti_analysis", {}).get("pasca_proses", {}).get("retention_days", 14), db_path=db_path)

    if item_arsip:
        catat_untuk_tren(item_arsip, db_path)
    else:
        logger.info("Tidak ada item baru untuk dicatat ke riwayat_tren pada run ini.")

    # Tandai semua item run ini sebagai "sudah diproses", supaya run
    # berikutnya (filter_belum_terkirim di pipeline_harian.py) tidak
    # mengambil & memproses ulang artikel yang sama selama masih
    # dalam window waktu.
    item_berita = [i for i in item_arsip if i["kategori"] == "berita"]

    if item_berita:
        catat_terkirim(
            [{"identifier": i["identifier"], "judul": i["judul"], "sumber": i["sumber"]} for i in item_berita],
            kategori="berita", db_path=db_path,
        )

    df_riwayat = ambil_riwayat_tren(hari=14, db_path=db_path)
    statistik_tren = susun_ringkasan_statistik_tren(df_riwayat)
    prediksi_tren = proses_prediksi_tren(statistik_tren, df_riwayat=df_riwayat)
    statistik_dashboard = susun_statistik_dashboard(df_riwayat, statistik_tren=statistik_tren)

    # Sinkronkan ancaman baru dengan hasil LLM
    data_analyst = prediksi_tren.get("data_analyst", {})
    if data_analyst and "emerging_threats" in data_analyst and data_analyst["emerging_threats"]:
        ancaman_obj = data_analyst["emerging_threats"][0]
        if isinstance(ancaman_obj, dict):
            ancaman_llm = ancaman_obj.get("nama_ancaman", "Menunggu Sinyal")
        else:
            ancaman_llm = str(ancaman_obj)
        # Jika panjangnya > 25 karakter, kita biarkan saja (CSS akan mengecilkan ukurannya nanti)
        statistik_dashboard["ancaman_baru"] = ancaman_llm

    kasus_wilayah_ai_json = json.dumps(prediksi_tren.get("kasus_wilayah_ai", {}), ensure_ascii=False)
    statistik_json = json.dumps(statistik_dashboard, ensure_ascii=False)
    simpan_prediksi_tren(
        prediksi_tren["prediksi_berita"],
        db_path,
        kasus_wilayah_ai=kasus_wilayah_ai_json,
        statistik_json=statistik_json,
    )
    simpan_metadata(
        "waktu_terakhir_scraping", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), db_path
    )

    logger.info("SELESAI MENCATAT ARSIP & MENGHITUNG TREN.")

    return {**hasil_ringkas, "prediksi_tren": prediksi_tren}