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





    def test_endpoint_references_info(self):

        """Memvalidasi endpoint info 4 sumber referensi CTI (eCSIRT, ATT&CK, D3FEND, NIST)."""

        from src.web.app import buat_token_sesi

        token = buat_token_sesi("admin")

        self.client.cookies.set("cti_session", token)



        response = self.client.get("/api/settings/references-info")

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data.get("status"), "ok")

        self.assertIn("references", data)

        self.assertEqual(len(data["references"]), 4)



        ref_ids = [r["id"] for r in data["references"]]

        self.assertIn("ecsirt", ref_ids)

        self.assertIn("mitre_attack", ref_ids)

        self.assertIn("mitre_d3fend", ref_ids)

        self.assertIn("nist_controls", ref_ids)



        for ref in data["references"]:

            self.assertGreater(ref["record_count"], 0)

            self.assertEqual(ref["status"], "AKTIF")

            self.assertTrue(ref["url"].startswith("http"))



    def test_endpoint_update_references_streaming(self):

        """Memvalidasi endpoint streaming pembaruan 4 referensi CTI dengan progress 0-100%."""

        from src.web.app import buat_token_sesi

        import json

        token = buat_token_sesi("admin")

        self.client.cookies.set("cti_session", token)



        response = self.client.post("/api/settings/update-references")

        self.assertEqual(response.status_code, 200)



        events = []

        for line in response.text.splitlines():

            line = line.strip()

            if line:

                try:

                    events.append(json.loads(line))

                except Exception:

                    pass



        self.assertGreaterEqual(len(events), 4)

        self.assertLessEqual(events[0]["percent"], 20)

        self.assertEqual(events[-1]["percent"], 100)

        self.assertEqual(events[-1]["status"], "completed")

        self.assertIn("selesai", events[-1]["message"].lower())





if __name__ == "__main__":

    unittest.main()

