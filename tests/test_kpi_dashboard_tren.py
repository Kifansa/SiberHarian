import unittest
import pandas as pd
from src.analytics.rag_engine import RAGEngine
from src.analytics.trend_analyzer import hitung_tren_sektor_target, susun_statistik_dashboard

class TestKpiDashboardTren(unittest.TestCase):
    def setUp(self):
        self.sample_df = pd.DataFrame([
            {
                "id": 1,
                "kategori": "berita",
                "identifier": "art-1",
                "judul": "Temuan Celah Kritis Zero-Day RCE pada Server Gateway Instansi Pemerintah",
                "sumber": "BSSN",
                "kata_kunci": "zero-day, rce, vulnerability, exploit, pemerintah",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "CRITICAL",
                "tanggal_publish": "2026-09-28",
                "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Ditemukan kerentanan zero-day remote code execution yang dieksploitasi penyerang pada jaringan pemerintah."
            },
            {
                "id": 2,
                "kategori": "berita",
                "identifier": "art-2",
                "judul": "Serangan Phishing dan Penipuan Online Bermodus APK Palsu Menyasar Nasabah Bank",
                "sumber": "Detik",
                "kata_kunci": "phishing, apk, perbankan, penipuan online",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "HIGH",
                "tanggal_publish": "2026-09-28",
                "tanggal_dicatat": "2026-09-28 11:00:00",
                "ringkasan_atau_narasi": "Nasabah bank ditargetkan menggunakan tautan phishing dan file APK berbahaya untuk mencuri kredensial."
            },
            {
                "id": 3,
                "kategori": "berita",
                "identifier": "art-3",
                "judul": "6.000 WNI Jadi Korban Sindikat Scam di Luar Negeri",
                "sumber": "Kompas",
                "kata_kunci": "scam, penipuan, online",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "MEDIUM",
                "tanggal_publish": "2026-09-20",
                "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Warga negara tertipu oleh sindikat penipuan online terorganisir."
            }
        ])

    def test_ancaman_baru_bukan_kata_acak_judul(self):
        rag = RAGEngine(self.sample_df)
        ancaman_kpi = rag.hitung_prediksi_ancaman_baru()
        
        # Harus berupa nama entitas ancaman organik, BUKAN kata acak seperti "JADI KORBAN"
        self.assertNotIn("JADI KORBAN", ancaman_kpi.upper())
        self.assertTrue(len(ancaman_kpi) > 0)
        # Menghasilkan nama entitas riil yang ditemukan dalam artikel (misal Celah Kritis Zero-Day)
        self.assertIn("ZERO-DAY", ancaman_kpi.upper())

    def test_ekstraksi_malware_spesifik_organik(self):
        df_malware = pd.DataFrame([
            {
                "id": 10,
                "kategori": "berita",
                "identifier": "art-malware",
                "judul": "Aktor Spionase Siber Menyebarkan Backdoor TASK#STOMP Lewat Lampiran Email",
                "sumber": "TheHackerNews",
                "kata_kunci": "malware, backdoor, task#stomp, spear-phishing",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "CRITICAL",
                "tanggal_publish": "2026-09-28",
                "tanggal_dicatat": "2026-09-28 12:00:00",
                "ringkasan_atau_narasi": "Grup APT terdeteksi menyebarkan varian baru backdoor TASK#STOMP."
            }
        ])
        rag = RAGEngine(df_malware)
        ancaman = rag.hitung_prediksi_ancaman_baru()
        # Harus menyebutkan malware secara spesifik tanpa klasifikasi statis
        self.assertIn("TASK#STOMP", ancaman.upper())

    def test_pola_serangan_tidak_terpotong_paksa(self):
        rag = RAGEngine(self.sample_df)
        pola = rag.hitung_prediksi_pola_serangan()
        
        self.assertIn("pola", pola)
        self.assertIn("growth_persen", pola)
        self.assertFalse(pola["pola"].endswith("Websi"))
        # Pastikan tidak ada pemotongan paksa [:20]
        self.assertTrue(len(pola["pola"]) > 0)

    def test_hitung_tren_sektor_target_memiliki_growth_dan_persen(self):
        hasil_sektor = hitung_tren_sektor_target(self.sample_df)
        self.assertTrue(len(hasil_sektor) > 0)
        
        top = hasil_sektor[0]
        self.assertIn("sektor", top)
        self.assertIn("jumlah", top)
        self.assertIn("growth_persen", top)
        self.assertIn("persen_total", top)

    def test_susun_statistik_dashboard_kpi_cards(self):
        stat = susun_statistik_dashboard(self.sample_df)
        self.assertIn("top_sektor", stat)
        self.assertIn("ancaman_baru", stat)
        self.assertIn("prediksi_pola_serangan", stat)
        self.assertTrue(len(stat["top_sektor"]) > 0)
        self.assertIsInstance(stat["ancaman_baru"], str)

    def test_mitre_mapping_semantic_grounding(self):
        rag = RAGEngine(self.sample_df)
        mitre_mapping = rag.map_incident_to_mitre_semantic(
            incident_title="Temuan Celah Kritis Zero-Day RCE pada Server Gateway Instansi Pemerintah",
            incident_narrative="Ditemukan kerentanan zero-day remote code execution yang dieksploitasi penyerang pada jaringan pemerintah.",
            keywords=["zero-day", "rce", "exploit"]
        )
        self.assertTrue(len(mitre_mapping) > 0)
        top_mitre = mitre_mapping[0]
        self.assertIn("id", top_mitre)
        self.assertIn("tactic", top_mitre)
        self.assertIn("technique", top_mitre)
        self.assertIn("score", top_mitre)
        # Kasus RCE/Zero-day harus terpetakan ke T1190 Exploit Public-Facing Application
        self.assertEqual(top_mitre["id"], "T1190")

    def test_top3_insiden_memiliki_mitre_mapping(self):
        rag = RAGEngine(self.sample_df)
        top3 = rag.ambil_top3_insiden_mikro()
        self.assertTrue(len(top3) > 0)
        for inc in top3:
            self.assertIn("mitre_mapping", inc)
            self.assertTrue(len(inc["mitre_mapping"]) > 0)

if __name__ == "__main__":
    unittest.main()
