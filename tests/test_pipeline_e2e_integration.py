"""
Test Integrasi End-to-End Pipeline & Normalisasi CTI
Memastikan:
1. Normalisasi poin CTI (_normalisasi_poin_cti) menangani semua variasi input tanpa UnboundLocalError
2. Pipeline proses_prediksi_tren mengembalikan struktur CTI lengkap (berita, analisis wilayah 3 region)
3. API read endpoints (/api/beranda, /api/arsip, /api/tren, /api/statistik-publik) berjalan tanpa error
"""
import unittest
from unittest.mock import patch
import pandas as pd
import json

from src.analytics.trend_predictor import _normalisasi_poin_cti, proses_prediksi_tren
from src.analytics.trend_analyzer import susun_ringkasan_statistik_tren, susun_statistik_dashboard
from src.storage.db import (
    DEFAULT_DB_PATH,
    ambil_riwayat_tren,
    simpan_prediksi_tren,
    ambil_prediksi_tren_terakhir,
    ambil_data_terbaru_per_kategori,
    ambil_riwayat_dikelompokkan_per_hari,
    ambil_statistik_publik
)


class TestPipelineE2EIntegration(unittest.TestCase):

    def test_normalisasi_poin_cti_edge_cases(self):
        """Memastikan fungsi _normalisasi_poin_cti toleran dan tidak melempar UnboundLocalError."""
        # 1. Nilai kosong / None
        self.assertEqual(_normalisasi_poin_cti(None), "-")
        self.assertEqual(_normalisasi_poin_cti(""), "-")
        self.assertEqual(_normalisasi_poin_cti("-"), "-")
        self.assertEqual(_normalisasi_poin_cti([]), "-")

        # 2. String teks biasa multiline
        teks_input = "- **Urgensi**: Serangan terdeteksi.\n- **Dampak**: Layanan terganggu."
        self.assertEqual(_normalisasi_poin_cti(teks_input), teks_input)

        # 3. List Python asli
        list_input = ["Poin pertama", "- Poin kedua", "Poin ketiga"]
        expected_list = "- Poin pertama\n- Poin kedua\n- Poin ketiga"
        self.assertEqual(_normalisasi_poin_cti(list_input), expected_list)

        # 4. String format array list Python / JSON
        str_array = "['Insiden A', 'Insiden B']"
        expected_array = "- Insiden A\n- Insiden B"
        self.assertEqual(_normalisasi_poin_cti(str_array), expected_array)

        # 5. String format array dengan strip quote
        str_array_quotes = '["- Insiden X", "- Insiden Y"]'
        self.assertEqual(_normalisasi_poin_cti(str_array_quotes), "- Insiden X\n- Insiden Y")

    def test_proses_prediksi_tren_structure(self):
        """Memastikan proses_prediksi_tren menghasilkan struktur dictionary CTI yang lengkap."""
        dummy_df = pd.DataFrame([
            {
                "kategori": "berita",
                "identifier": "ART-01",
                "judul": "Pemberitahuan Serangan Ransomware di Jawa Timur",
                "sumber": "Kominfo Jatim",
                "kata_kunci": "ransomware, server",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Server dinas terdampak ransomware.",
                "link": "https://jatimprov.go.id/news/1",
            },
            {
                "kategori": "berita",
                "identifier": "ART-02",
                "judul": "Global Cyber Attack Wave Hits Multiple Countries",
                "sumber": "BleepingComputer",
                "kata_kunci": "exploit, zero-day",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28 09:00:00",
                "ringkasan_atau_narasi": "Zero day flaw actively exploited globally.",
                "link": "https://bleepingcomputer.com/news/2",
            }
        ])

        statistik = susun_ringkasan_statistik_tren(dummy_df)

        with patch("src.analytics.cti_agents._call_llm_text") as mock_llm:
            mock_llm.return_value = "- **Insiden Kritis**: Terdeteksi anomali pada perimeter jaringan."
            hasil = proses_prediksi_tren(statistik, df_riwayat=dummy_df, mode="instant_rag")

            self.assertIn("prediksi_berita", hasil)
            self.assertIn("kasus_wilayah_ai", hasil)

            kasus_ai = hasil["kasus_wilayah_ai"]
            self.assertIn("internasional", kasus_ai)
            self.assertIn("nasional", kasus_ai)
            self.assertIn("jawa_timur", kasus_ai)

            for wil in ["internasional", "nasional", "jawa_timur"]:
                info = kasus_ai[wil]
                self.assertIn("isu_utama", info)
                self.assertIn("alasan_urgensi", info)
                self.assertIn("potensi_ancaman", info)
                self.assertIsInstance(info["alasan_urgensi"], str)
                self.assertIsInstance(info["potensi_ancaman"], str)
                self.assertNotEqual(info["alasan_urgensi"], "")

    def test_database_endpoint_queries(self):
        """Memastikan fungsi pembaca data DB yang dipakai FastAPI web endpoints berjalan tanpa error."""
        if not DEFAULT_DB_PATH.exists():
            self.skipTest("Database state.db belum ada")

        # 1. Beranda
        data_beranda = ambil_data_terbaru_per_kategori(hari=7)
        self.assertIn("berita", data_beranda)
        self.assertIsInstance(data_beranda["berita"], list)

        # 2. Arsip
        data_arsip = ambil_riwayat_dikelompokkan_per_hari(hari=7)
        self.assertIsInstance(data_arsip, dict)

        # 3. Prediksi tren
        pred = ambil_prediksi_tren_terakhir()
        # Jika belum ada, pred boleh None
        if pred:
            self.assertIn("prediksi_berita", pred)
            self.assertIn("tanggal_dihitung", pred)

        # 4. Statistik publik
        stat = ambil_statistik_publik()
        self.assertEqual(stat.get("status"), "ok")
        self.assertIn("kpi_insights", stat)
        self.assertIn("top_sektor", stat)


if __name__ == "__main__":
    unittest.main()
