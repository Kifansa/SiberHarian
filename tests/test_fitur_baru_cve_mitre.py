import unittest
import pandas as pd
from datetime import datetime, timedelta

from src.analytics.trend_analyzer import (
    hitung_distribusi_taktik_mitre,
    ekstrak_radar_cve_watchlist,
    susun_ringkasan_statistik_tren,
    susun_statistik_dashboard,
)


class TestFiturBaruCveMitre(unittest.TestCase):
    def setUp(self):
        tgl_hari_ini = datetime.now().strftime("%Y-%m-%d")
        tgl_kemarin = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        self.df_insiden = pd.DataFrame([
            {
                "id": 1,
                "judul": "Celah Kritis Fortinet CVE-2024-21762 Dieksploitasi Peretas untuk Akses Jaringan",
                "ringkasan_atau_narasi": "Kerentanan RCE pada FortiOS SSL-VPN memungkinkan eksekusi perintah tanpa autentikasi.",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "sumber": "BleepingComputer",
                "tanggal_publish": tgl_hari_ini,
                "kata_kunci": "cve-2024-21762, rce, fortinet, exploit, initial access",
            },
            {
                "id": 2,
                "judul": "Eksploitasi Zero-Day Ivanti Connect Secure Menyasar Lembaga Publik",
                "ringkasan_atau_narasi": "Serangan bypass autentikasi dan command injection terpantau di gateway VPN Ivanti.",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "sumber": "The Hacker News",
                "tanggal_publish": tgl_kemarin,
                "kata_kunci": "ivanti, zero-day, vpn, command injection",
            },
            {
                "id": 3,
                "judul": "Kampanye Phishing Massal Menggunakan Trojan Infostealer Mencuri Kredensial",
                "ringkasan_atau_narasi": "Penyebaran file ISO palsu yang mengeksekusi malware pencuri token sesi dan password.",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "sumber": "Detik",
                "tanggal_publish": tgl_hari_ini,
                "kata_kunci": "phishing, infostealer, malware, credential access",
            },
        ])

    def test_distribusi_taktik_mitre(self):
        """Memastikan fungsi mengembalikan distribusi taktik MITRE ATT&CK yang valid."""
        hasil = hitung_distribusi_taktik_mitre(self.df_insiden)
        self.assertIsInstance(hasil, list)
        self.assertGreater(len(hasil), 0)

        taktik_names = [item["taktik"] for item in hasil]
        # Paling tidak Initial Access, Execution, atau Credential Access harus terdeteksi
        self.assertTrue(any(t in taktik_names for t in ["Initial Access", "Execution", "Credential Access"]))

        for item in hasil:
            self.assertIn("taktik", item)
            self.assertIn("jumlah", item)
            self.assertIn("persen", item)
            self.assertGreaterEqual(item["jumlah"], 1)
            self.assertGreaterEqual(item["persen"], 0.0)

    def test_ekstrak_radar_cve_watchlist(self):
        """Memastikan CVE eksplisit dan indikasi Zero-Day/RCE terekstrak dengan benar."""
        cve_list = ekstrak_radar_cve_watchlist(self.df_insiden)
        self.assertIsInstance(cve_list, list)
        self.assertGreaterEqual(len(cve_list), 2)

        cve_ids = [c["cve_id"] for c in cve_list]
        self.assertIn("CVE-2024-21762", cve_ids)

        item_fortinet = next(c for c in cve_list if c["cve_id"] == "CVE-2024-21762")
        self.assertEqual(item_fortinet["aplikasi_terdampak"], "Fortinet")
        self.assertEqual(item_fortinet["status_urgensi"], "Eksploitasi Aktif")
        self.assertIn("BleepingComputer", item_fortinet["sumber_terakhir"])

        # Memastikan deteksi non-CVE Zero-Day terpetakan
        self.assertTrue(any("Zero-Day" in c["cve_id"] or "RCE" in c["cve_id"] for c in cve_list))

    def test_integrasi_statistik_tren_dan_dashboard(self):
        """Memastikan taktik_mitre dan cve_watchlist hadir dalam payload statistik tren & dashboard."""
        ringkasan = susun_ringkasan_statistik_tren(self.df_insiden)
        self.assertIn("taktik_mitre", ringkasan)
        self.assertIn("cve_watchlist", ringkasan)

        stat_dashboard = susun_statistik_dashboard(self.df_insiden, ringkasan)
        self.assertIn("taktik_mitre", stat_dashboard)
        self.assertIn("cve_watchlist", stat_dashboard)

        # Memastikan atribut usang threat posture & matriks tindakan benar-benar tidak ada
        self.assertNotIn("threat_posture", stat_dashboard)
        self.assertNotIn("matriks_tindakan", stat_dashboard)


if __name__ == "__main__":
    unittest.main()
