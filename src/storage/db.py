"""Facade kompatibilitas untuk modul penyimpanan state SQLite.

Implementasi dipisah per tanggung jawab di ``schema``, ``dashboard``, ``intelijen``,
dan ``d3fend``. Modul ini mempertahankan kontrak import lama.
"""

from src.storage.dashboard import (
    ambil_data_terbaru_per_kategori,
    ambil_identifier_terkirim,
    ambil_metadata,
    ambil_prediksi_tren_terakhir,
    ambil_riwayat_dikelompokkan_per_hari,
    ambil_riwayat_tren,
    ambil_statistik_publik,
    ambil_waktu_terakhir_scraping,
    bersihkan_riwayat_tren_lama,
    catat_terkirim,
    catat_untuk_tren,
    simpan_metadata,
    simpan_prediksi_tren,
)
from src.storage.d3fend import (
    ambil_d3fend_mitigasi_by_attack_id,
    ambil_semua_d3fend_mappings,
    ambil_semua_d3fend_techniques,
    simpan_d3fend_attack_mappings,
    simpan_d3fend_techniques,
)
from src.storage.intelijen import (
    ambil_intelijen_berita,
    ambil_semua_intelijen_berita,
    simpan_intelijen_berita,
    simpan_koreksi_admin_intelijen,
    simpan_koreksi_admin_sektor,
    tandai_flag_tinjauan_intelijen,
)
from src.storage.schema import (
    DEFAULT_DB_PATH,
    _koneksi,
    init_db,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "_koneksi",
    "ambil_d3fend_mitigasi_by_attack_id",
    "ambil_data_terbaru_per_kategori",
    "ambil_identifier_terkirim",
    "ambil_intelijen_berita",
    "ambil_metadata",
    "ambil_prediksi_tren_terakhir",
    "ambil_riwayat_dikelompokkan_per_hari",
    "ambil_riwayat_tren",
    "ambil_semua_d3fend_mappings",
    "ambil_semua_d3fend_techniques",
    "ambil_semua_intelijen_berita",
    "ambil_statistik_publik",
    "ambil_waktu_terakhir_scraping",
    "bersihkan_riwayat_tren_lama",
    "catat_terkirim",
    "catat_untuk_tren",
    "init_db",
    "simpan_d3fend_attack_mappings",
    "simpan_d3fend_techniques",
    "simpan_intelijen_berita",
    "simpan_koreksi_admin_intelijen",
    "simpan_koreksi_admin_sektor",
    "simpan_metadata",
    "simpan_prediksi_tren",
    "tandai_flag_tinjauan_intelijen",
]
