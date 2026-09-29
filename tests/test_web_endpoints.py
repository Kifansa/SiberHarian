import unittest
from fastapi.testclient import TestClient

from src.web.app import app


class TestWebEndpoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_endpoint_statistik_publik(self):
        """Memvalidasi respons API statistik publik untuk warga dan OPD."""
        response = self.client.get("/api/statistik-publik")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("kpi_insights", data)
        self.assertGreaterEqual(len(data["kpi_insights"]), 3)
        self.assertIn("insight", data["kpi_insights"][0])
        self.assertIn("takeaway_chart", data)
        self.assertIn("word_cloud", data)

        # Memastikan tidak ada placeholder dan field kontekstual terisi
        self.assertIsInstance(data["takeaway_chart"], str)
        self.assertGreater(len(data["takeaway_chart"]), 10)

        if data["word_cloud"]:
            first_kw = data["word_cloud"][0]
            self.assertIn("kata", first_kw)
            self.assertIn("bobot", first_kw)
            self.assertIn("contoh_judul", first_kw)
            self.assertIn("sumber", first_kw)

    def test_endpoint_api_tren(self):
        """Memvalidasi respons API tren untuk Admin SOC Diskominfo Jatim."""
        response = self.client.get("/api/tren")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("status", data)

        if data.get("status") == "ok":
            stat = data.get("statistik", {})
            self.assertIsInstance(stat, dict)

            # Memastikan fitur baru hadir
            self.assertIn("taktik_mitre", stat)
            self.assertIn("cve_watchlist", stat)
            self.assertIn("vektor_serangan", stat)
            self.assertIn("sektor_target", stat)

            # Memastikan sisa-sisa fitur lama yang dihapus tidak muncul di respons
            self.assertNotIn("threat_posture", stat)
            self.assertNotIn("matriks_tindakan", stat)
            self.assertNotIn("skor_threat_posture", stat)

    def test_endpoint_ensiklopedia(self):
        """Memvalidasi endpoint referensi ensiklopedia siber."""
        response = self.client.get("/api/ensiklopedia")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("frameworks", data)


if __name__ == "__main__":
    unittest.main()
