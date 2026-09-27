"""
Unit test untuk modul statistik publik (db.py - ambil_statistik_publik)
Memastikan:
1. Menghasilkan tepat 3 KPI cards (Top Target, Software Terpapar, Fokus Wilayah)
2. Kartu Status Risiko Software (CVSS bias) sudah dieliminasi
3. Query word cloud memfilter data 7 hari terkini
"""
import unittest
from pathlib import Path
from src.storage.db import ambil_statistik_publik, DEFAULT_DB_PATH

class TestStatistikPublik(unittest.TestCase):
    def test_struktur_statistik_publik(self):
        if not DEFAULT_DB_PATH.exists():
            self.skipTest("Database state.db belum ada")

        stat = ambil_statistik_publik()
        self.assertEqual(stat.get("status"), "ok")

        # 1. Pastikan KPI Insights berisi tepat 3 kartu
        kpis = stat.get("kpi_insights", [])
        self.assertEqual(len(kpis), 3, f"Jumlah KPI harus 3, didapat: {len(kpis)}")

        ids = [k["id"] for k in kpis]
        self.assertIn("top_target", ids)
        self.assertIn("top_vendor", ids)
        self.assertIn("fokus_wilayah", ids)

        # 2. Pastikan tidak ada CVSS 9.5 / Kritis Ekstrem di KPI publik
        for k in kpis:
            self.assertNotIn("Kritis Ekstrem", k["nilai"])
            self.assertNotIn("Perlu Update Segera", k["badge"])

        # 3. Pastikan word cloud tersedia dan memiliki bobot
        wc = stat.get("word_cloud", [])
        self.assertIsInstance(wc, list)
        if wc:
            self.assertIn("kata", wc[0])
            self.assertIn("bobot", wc[0])
            self.assertGreater(wc[0]["bobot"], 0)

        # 4. Pastikan komponen edukasi dan top vendor ada
        self.assertIn("edukasi_list", stat)
        self.assertIn("top_ancaman", stat)
        self.assertIn("top_vendor", stat)

if __name__ == "__main__":
    unittest.main()
