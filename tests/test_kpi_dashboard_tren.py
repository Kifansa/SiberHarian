import unittest
import pandas as pd
from src.analytics.rag_engine import RAGEngine
from src.analytics.trend_analyzer import hitung_tren_sektor_target, susun_statistik_dashboard

from src.cti.preparer import CLOSED_11_TAXONOMY_CATEGORIES, TAXONOMY_DISPLAY_NAMES

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

    def test_ancaman_baru_1_kasus_returns_kondisi_stabil(self):
        # sample_df hanya memuat 1 kasus zero-day di periode terkini -> wajib ditolak (Kondisi Stabil)
        rag = RAGEngine(self.sample_df)
        ancaman_kpi = rag.hitung_prediksi_ancaman_baru()
        self.assertEqual(ancaman_kpi, "Kondisi Stabil")

    def test_ancaman_baru_2_kasus_returns_kategori_taksonomi(self):
        # Tambah 1 artikel zero-day lagi sehingga menjadi 2 kasus di periode terkini
        df_dua_kasus = pd.concat([
            self.sample_df,
            pd.DataFrame([{
                "id": 4,
                "kategori": "berita",
                "identifier": "art-4",
                "judul": "Eksploitasi Zero-Day RCE Baru Menyerang Infrastruktur Cloud",
                "sumber": "BSSN",
                "kata_kunci": "zero-day, rce, exploit, baru",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "CRITICAL",
                "tanggal_publish": "2026-09-28",
                "tanggal_dicatat": "2026-09-28 12:00:00",
                "ringkasan_atau_narasi": "Celah zero-day baru dimanfaatkan peretas untuk mengeksekusi kode berbahaya."
            }])
        ], ignore_index=True)

        rag = RAGEngine(df_dua_kasus)
        ancaman_kpi = rag.hitung_prediksi_ancaman_baru()
        self.assertEqual(ancaman_kpi, TAXONOMY_DISPLAY_NAMES["eksploitasi_kerentanan"])
        self.assertNotIn("JADI KORBAN", ancaman_kpi.upper())

    def test_ekstraksi_malware_taksonomi_dan_threshold_kasus(self):
        # 1 kasus malware -> harus Kondisi Stabil
        df_malware_1 = pd.DataFrame([
            {
                "id": 10,
                "kategori": "berita",
                "identifier": "art-malware-1",
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
        rag_1 = RAGEngine(df_malware_1)
        self.assertEqual(rag_1.hitung_prediksi_ancaman_baru(), "Kondisi Stabil")

        # 2 kasus malware -> harus mengembalikan kategori taksonomi resmi Malware / Infostealer
        df_malware_2 = pd.concat([
            df_malware_1,
            pd.DataFrame([{
                "id": 11,
                "kategori": "berita",
                "identifier": "art-malware-2",
                "judul": "Varian Baru Infostealer Menargetkan Kredensial Pengguna",
                "sumber": "SecurityWeek",
                "kata_kunci": "malware, infostealer, stealer, baru",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "HIGH",
                "tanggal_publish": "2026-09-28",
                "tanggal_dicatat": "2026-09-28 13:00:00",
                "ringkasan_atau_narasi": "Ditemukan varian baru infostealer yang mencuri data browser."
            }])
        ], ignore_index=True)
        rag_2 = RAGEngine(df_malware_2)
        self.assertEqual(rag_2.hitung_prediksi_ancaman_baru(), TAXONOMY_DISPLAY_NAMES["malware"])

    def test_pola_serangan_tidak_terpotong_paksa(self):
        rag = RAGEngine(self.sample_df)
        pola = rag.hitung_prediksi_pola_serangan()
        
        self.assertIn("pola", pola)
        self.assertIn("growth_persen", pola)
        self.assertIn("subteks", pola)
        self.assertEqual(pola["subteks"], "vs minggu lalu")
        # Nilai utama pola adalah kategori taksonomi tertutup
        self.assertIn(pola["pola"], list(TAXONOMY_DISPLAY_NAMES.values()))

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

    def test_novelty_precedence_over_volume(self):
        # Kategori A (Phishing) tren lama: 4 artikel di baseline (2026-09-20) dan 4 di terkini (2026-09-28)
        # Kategori B (Ransomware) baru muncul: 0 di baseline, 2 di terkini (2026-09-28)
        phish_base_titles = [
            "Marak Modus Phishing Undangan Nikah APK Palsu",
            "Pencurian Kredensial Nasabah Melalui Situs Phishing Bank",
            "Penipuan Hadiah Mengatasnamakan Lembaga Resmi",
            "Phishing QRIS Palsu Menyasar Pedagang UMKM"
        ]
        phish_cur_titles = [
            "Phishing Perbankan Menargetkan Nasabah Bank Mandiri",
            "Penipuan Phishing APK Menguras Rekening Nasabah BCA",
            "Sindikat Penipuan Online Palsu Mengatasnamakan Pajak",
            "Kampanye Phishing Kredensial SSO ASN Pemerintah"
        ]
        ransom_cur_titles = [
            "Serangan Ransomware LockBit Mengenkripsi Pusat Data Nasional",
            "Varian Ransomware Baru BlackCat Menyandera Sistem Rumah Sakit"
        ]

        rows = []
        for i, judul in enumerate(phish_base_titles):
            rows.append({
                "id": 100 + i,
                "kategori": "berita",
                "identifier": f"base-phish-{i}",
                "judul": judul,
                "kata_kunci": "phishing, penipuan",
                "tanggal_publish": "2026-09-20",
                "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Kasus penipuan online."
            })
        for i, judul in enumerate(phish_cur_titles):
            rows.append({
                "id": 200 + i,
                "kategori": "berita",
                "identifier": f"cur-phish-{i}",
                "judul": judul,
                "kata_kunci": "phishing, penipuan",
                "tanggal_publish": "2026-09-28",
                "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Kasus penipuan online."
            })
        for i, judul in enumerate(ransom_cur_titles):
            rows.append({
                "id": 300 + i,
                "kategori": "berita",
                "identifier": f"cur-ransom-{i}",
                "judul": judul,
                "kata_kunci": "ransomware, enkripsi, baru",
                "tanggal_publish": "2026-09-28",
                "tanggal_dicatat": "2026-09-28 11:00:00",
                "ringkasan_atau_narasi": "Ransomware baru mengenkripsi database dan meminta tebusan."
            })

        df_ab = pd.DataFrame(rows)
        rag = RAGEngine(df_ab)
        pola = rag.hitung_prediksi_pola_serangan()
        ancaman = rag.hitung_prediksi_ancaman_baru()

        # POLA ANCAMAN = Kategori A (Phishing - volume tertinggi)
        self.assertEqual(pola["pola"], TAXONOMY_DISPLAY_NAMES["phishing_penipuan"])
        # SINYAL ANCAMAN BARU = Kategori B (Ransomware - kebaruan > volume dengan >= 2 kasus)
        self.assertEqual(ancaman, TAXONOMY_DISPLAY_NAMES["ransomware"])


if __name__ == "__main__":
    unittest.main()
