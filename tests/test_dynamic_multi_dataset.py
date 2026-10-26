"""
tests/test_dynamic_multi_dataset.py
Automated Acceptance Test Suite: Dynamic Multi-Dataset Shift & CTI Integrity Verification.

Proves on two distinct datasets (Dataset A vs Dataset B) that:
1. [ POLA ANCAMAN ] shifts dynamically between datasets (based on dominant closed 11 eCSIRT category).
2. [ SINYAL ANCAMAN BARU ] shifts dynamically based on novelty > volume, strictly requiring >= 2 cases
   (1 case must be rejected as false alarm, returning 'Kondisi Stabil').
3. [ SEKTOR TARGET TERPAPAR ] shifts dynamically between datasets across the 10 closed IIV sectors
   (Perpres 82/2022) + 'Tidak dapat ditentukan', with mandatory exact substring quote validation
   (verified with `assert quote in news_text` or whitespace-normalized equivalent).
   Out-of-list sectors and invalid quotes must be rejected.
4. Database End-to-End Dynamic Shifting: Ingesting Dataset A into SQLite DB produces Dataset A analytics,
   and switching to Dataset B produces Dataset B analytics.
5. Mutation Check: Inverting data distribution dynamically inverts analytics, proving zero hardcoded logic.
"""

import os
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd

from src.analytics.rag_engine import RAGEngine
from src.analytics.trend_analyzer import (
    hitung_tren_sektor_target,
    susun_statistik_dashboard,
    susun_ringkasan_statistik_tren,
)
from src.cti.preparer import (
    CLOSED_11_TAXONOMY_CATEGORIES,
    TAXONOMY_DISPLAY_NAMES,
    CLOSED_10_IIV_SECTORS,
    IIV_SECTOR_DISPLAY_NAMES,
)
from src.cti.analyzer import (
    CTINewsAnalyzer,
    guard_sector_and_quote,
    classify_sector,
)
from src.storage.db import init_db, _koneksi, catat_untuk_tren


def normalize_ws(text: str) -> str:
    """Helper normalisasi spasi putih untuk validasi substring eksak."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip().lower()


class TestDynamicDatasetShift(unittest.TestCase):
    """
    Pengujian pergeseran dinamis antara Dataset A dan Dataset B:
    - Dataset A:
      * Dominan: Phishing / Penipuan Siber
      * Sinyal Baru: Ransomware (novelty >= 2 kasus)
      * Sektor Sasaran: Keuangan & Perbankan
    - Dataset B:
      * Dominan: Eksploitasi Kerentanan (Exploit / Zero-Day)
      * Sinyal Baru: Malware / Infostealer (novelty >= 2 kasus)
      * Sektor Sasaran: Kesehatan
    """

    def setUp(self):
        # Dataset A
        self.dataset_a = pd.DataFrame([
            # Baseline (2026-09-20): 4 artikel Phishing / Perbankan
            {
                "id": 101, "kategori": "berita", "identifier": "dsA-b1",
                "judul": "Sindikat Phishing Mengincar Kredensial Nasabah Bank Mandiri",
                "sumber": "Detik", "kata_kunci": "phishing, penipuan, bank, rekening",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Aksi penipuan online melalui link phishing mobile banking menyasar nasabah bank di Jawa Timur."
            },
            {
                "id": 102, "kategori": "berita", "identifier": "dsA-b2",
                "judul": "Waspada Penipuan Link Phishing Hadiah Palsu Catut Bank BCA",
                "sumber": "Kompas", "kata_kunci": "phishing, penipuan, bank, bca",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Nasabah bank diimbau waspada terhadap penipuan phishing yang meminta PIN rekening finansial."
            },
            {
                "id": 103, "kategori": "berita", "identifier": "dsA-b3",
                "judul": "Penipuan Online Catut Lembaga Keuangan dan Perbankan Nasional",
                "sumber": "CNN Indonesia", "kata_kunci": "phishing, penipuan, keuangan, perbankan",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Otoritas mengingatkan maraknya penipuan phishing perbankan yang menyasar sektor keuangan dan perbankan."
            },
            {
                "id": 104, "kategori": "berita", "identifier": "dsA-b4",
                "judul": "Marak Modus Phishing Pembobolan Saldo Rekening Bank Swasta",
                "sumber": "Antara", "kata_kunci": "phishing, penipuan, rekening, bank",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Pencurian saldo rekening nasabah bank lewat situs phishing semakin meresahkan masyarakat."
            },
            # Terkini (2026-09-28): 4 artikel Phishing / Perbankan + 2 artikel Ransomware (Novelty)
            {
                "id": 105, "kategori": "berita", "identifier": "dsA-c1",
                "judul": "Modus Phishing Perbankan Mobile Banking Bank Mandiri Marak Lagi",
                "sumber": "Detik", "kata_kunci": "phishing, penipuan, bank, mobile banking",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Penipuan phishing online menguras rekening nasabah bank lewat tautan palsu."
            },
            {
                "id": 106, "kategori": "berita", "identifier": "dsA-c2",
                "judul": "Penipuan Online Bermodus APK Palsu Menyasar Rekening Nasabah BRI",
                "sumber": "Kompas", "kata_kunci": "phishing, apk, penipuan, bank",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Phishing berkedok undangan APK mencuri kredensial m-banking nasabah bank."
            },
            {
                "id": 107, "kategori": "berita", "identifier": "dsA-c3",
                "judul": "Waspada Link Phishing Perbankan yang Menguras Tabungan Nasabah",
                "sumber": "CNN Indonesia", "kata_kunci": "phishing, penipuan, finansial, transaksi",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Situs phishing perbankan palsu memancing nasabah memasukkan sandi transaksi finansial rekening bank."
            },
            {
                "id": 108, "kategori": "berita", "identifier": "dsA-c4",
                "judul": "Kampanye Phishing Siber Mengincar Kredensial Transaksi Finansial Bank",
                "sumber": "Antara", "kata_kunci": "phishing, penipuan, perbankan, dompet",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Serangan phishing massal mengincar akun dompet digital dan transaksi perbankan nasabah."
            },
            {
                "id": 109, "kategori": "berita", "identifier": "dsA-c5",
                "judul": "Varian Ransomware Baru Menyerang Sistem Server Layanan Publik",
                "sumber": "BSSN", "kata_kunci": "ransomware, enkripsi, varian baru, tebusan",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00",
                "ringkasan_atau_narasi": "Terdeteksi varian ransomware baru yang mengenkripsi file database dan menuntut uang tebusan."
            },
            {
                "id": 110, "kategori": "berita", "identifier": "dsA-c6",
                "judul": "Serangan Ransomware Terkini Mengenkripsi Database Pelayanan Warga",
                "sumber": "SecurityWeek", "kata_kunci": "ransomware, tebusan, ancaman baru, enkripsi",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00",
                "ringkasan_atau_narasi": "Insiden serangan baru varian ransomware mengunci akses data dan meminta tebusan kripto."
            }
        ])

        # Dataset B
        self.dataset_b = pd.DataFrame([
            # Baseline (2026-09-20): 4 artikel Kerentanan / Rumah Sakit
            {
                "id": 201, "kategori": "berita", "identifier": "dsB-b1",
                "judul": "Celah Keamanan RCE Ditemukan pada Server Sistem Rumah Sakit",
                "sumber": "BSSN", "kata_kunci": "zero-day, rce, exploit, kerentanan, rumah sakit",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Ditemukan kerentanan zero-day remote code execution pada portal informasi pasien rumah sakit umum daerah."
            },
            {
                "id": 202, "kategori": "berita", "identifier": "dsB-b2",
                "judul": "Eksploitasi Kerentanan Zero-Day pada Server Kesehatan Daerah",
                "sumber": "CyberNews", "kata_kunci": "exploit, zero-day, kerentanan, kesehatan",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Penyerang memanfaatkan celah keamanan exploit pada server kesehatan untuk menembus jaringan medis."
            },
            {
                "id": 203, "kategori": "berita", "identifier": "dsB-b3",
                "judul": "Analisis Celah Kerentanan Kritis pada Perangkat Medis Rumah Sakit",
                "sumber": "Detik", "kata_kunci": "kerentanan, vulnerability, cve, rumah sakit",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Pemeriksaan menemukan celah kerentanan berbahaya pada server rekam medis pasien rumah sakit rujukan."
            },
            {
                "id": 204, "kategori": "berita", "identifier": "dsB-b4",
                "judul": "Penyerang Eksploitasi Vulnerability pada Portal Pasien Kesehatan",
                "sumber": "Kompas", "kata_kunci": "exploit, kerentanan, celah, pasien, kesehatan",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Upaya eksploitasi kerentanan celah keamanan portal pasien rumah sakit dan fasilitas kesehatan."
            },
            # Terkini (2026-09-28): 4 artikel Kerentanan / Rumah Sakit + 2 artikel Malware (Novelty)
            {
                "id": 205, "kategori": "berita", "identifier": "dsB-c1",
                "judul": "Eksploitasi Celah Keamanan CVE-2026-1122 Menyerang Sistem Rumah Sakit",
                "sumber": "TheHackerNews", "kata_kunci": "exploit, cve, kerentanan, rumah sakit",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Peretas melancarkan exploit pada celah kerentanan server rumah sakit daerah."
            },
            {
                "id": 206, "kategori": "berita", "identifier": "dsB-c2",
                "judul": "Kerentanan Kritis Zero-Day pada Database Rekam Medis Pasien RSUD",
                "sumber": "Detik", "kata_kunci": "zero-day, kerentanan, exploit, rumah sakit, pasien",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Celah keamanan zero-day exploit mengancam data rekam medis pasien di rumah sakit umum daerah."
            },
            {
                "id": 207, "kategori": "berita", "identifier": "dsB-c3",
                "judul": "Upaya Eksploitasi Kerentanan Web Portal Fasilitas Kesehatan",
                "sumber": "CyberSec", "kata_kunci": "eksploitasi, kerentanan, vulnerability, kesehatan, rumah sakit",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Insiden eksploitasi kerentanan celah sistem informasi rumah sakit dan fasilitas kesehatan terdeteksi."
            },
            {
                "id": 208, "kategori": "berita", "identifier": "dsB-c4",
                "judul": "Vulnerability RCE Mengancam Sistem Informasi Pelayanan Rumah Sakit",
                "sumber": "SecurityWeek", "kata_kunci": "kerentanan, rce, exploit, rumah sakit",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Celah kerentanan remote code execution ditemukan pada database pelayanan rumah sakit."
            },
            {
                "id": 209, "kategori": "berita", "identifier": "dsB-c5",
                "judul": "Varian Baru Malware Infostealer Menyebar Melalui Lampiran File",
                "sumber": "BSSN", "kata_kunci": "malware, infostealer, varian baru, stealer",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00",
                "ringkasan_atau_narasi": "Penyebaran varian baru malware infostealer yang mencuri kredensial pengguna secara masif."
            },
            {
                "id": 210, "kategori": "berita", "identifier": "dsB-c6",
                "judul": "Peringatan Ancaman Baru Trojan Infostealer Mencuri Dokumen Rahasia",
                "sumber": "SecurityWeek", "kata_kunci": "malware, trojan, ancaman baru, infostealer",
                "kategori_relevansi": "insiden_spesifik",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00",
                "ringkasan_atau_narasi": "Terdeteksi ancaman baru malware trojan spionase yang mengekstrak informasi rahasia dari sistem."
            }
        ])

        self.analyzer = CTINewsAnalyzer(llm_mode="offline")

    def test_pola_ancaman_shifts_dynamically(self):
        """Membuktikan [ POLA ANCAMAN ] berganti secara dinamis antara Dataset A dan Dataset B."""
        rag_a = RAGEngine(self.dataset_a)
        res_pola_a = rag_a.hitung_prediksi_pola_serangan()
        pola_a = res_pola_a["pola"]

        rag_b = RAGEngine(self.dataset_b)
        res_pola_b = rag_b.hitung_prediksi_pola_serangan()
        pola_b = res_pola_b["pola"]

        # 1. Nilai wajib dinamis dan tidak sama
        self.assertNotEqual(pola_a, pola_b, "POLA ANCAMAN harus bergeser dinamis antara Dataset A dan B!")

        # 2. Nilai harus sesuai kategori taksonomi tertutup eCSIRT
        self.assertEqual(pola_a, TAXONOMY_DISPLAY_NAMES["phishing_penipuan"])
        self.assertEqual(pola_b, TAXONOMY_DISPLAY_NAMES["eksploitasi_kerentanan"])
        self.assertIn(res_pola_a["kategori_taksonomi"], CLOSED_11_TAXONOMY_CATEGORIES)
        self.assertIn(res_pola_b["kategori_taksonomi"], CLOSED_11_TAXONOMY_CATEGORIES)

    def test_sinyal_ancaman_baru_shifts_dynamically(self):
        """Membuktikan [ SINYAL ANCAMAN BARU ] berganti secara dinamis antara Dataset A dan Dataset B."""
        rag_a = RAGEngine(self.dataset_a)
        sinyal_a = rag_a.hitung_prediksi_ancaman_baru()

        rag_b = RAGEngine(self.dataset_b)
        sinyal_b = rag_b.hitung_prediksi_ancaman_baru()

        # 1. Nilai wajib dinamis dan berbeda
        self.assertNotEqual(sinyal_a, sinyal_b, "SINYAL ANCAMAN BARU harus bergeser dinamis antara Dataset A dan B!")

        # 2. Nilai harus merupakan kategori taksonomi resmi yang baru muncul
        self.assertEqual(sinyal_a, TAXONOMY_DISPLAY_NAMES["ransomware"])
        self.assertEqual(sinyal_b, TAXONOMY_DISPLAY_NAMES["malware"])

        # 3. Bukan judul atau entitas berita mentah
        self.assertNotIn("SUPERMARKET", sinyal_a.upper())
        self.assertNotIn("SUPERMARKET", sinyal_b.upper())

    def test_sektor_target_terpapar_shifts_dynamically(self):
        """Membuktikan [ SEKTOR TARGET TERPAPAR ] berganti secara dinamis antara Dataset A dan Dataset B."""
        sektor_a_list = hitung_tren_sektor_target(self.dataset_a)
        self.assertTrue(len(sektor_a_list) > 0)
        top_sektor_a = sektor_a_list[0]["sektor"]

        sektor_b_list = hitung_tren_sektor_target(self.dataset_b)
        self.assertTrue(len(sektor_b_list) > 0)
        top_sektor_b = sektor_b_list[0]["sektor"]

        # 1. Nilai sektor agregat harus berbeda
        self.assertNotEqual(top_sektor_a, top_sektor_b, "SEKTOR TARGET harus bergeser dinamis antara Dataset A dan B!")
        self.assertEqual(top_sektor_a, "Keuangan & Perbankan")
        self.assertEqual(top_sektor_b, "Kesehatan")

        # 2. Uji klasifikasi per-artikel pada Dataset A dan Dataset B
        art_a = self.dataset_a.iloc[0].to_dict()
        res_a = self.analyzer.classify_sector(art_a)
        self.assertEqual(res_a["sektor_target"], "Keuangan & Perbankan")
        self.assertTrue(res_a["is_valid"])
        quote_a = res_a["kutipan_bukti_sektor"]
        self.assertTrue(len(quote_a) > 0)
        full_text_a = f"{art_a.get('judul', '')} {art_a.get('ringkasan_atau_narasi', '')}"
        self.assertIn(normalize_ws(quote_a), normalize_ws(full_text_a))

        art_b = self.dataset_b.iloc[0].to_dict()
        res_b = self.analyzer.classify_sector(art_b)
        self.assertEqual(res_b["sektor_target"], "Kesehatan")
        self.assertTrue(res_b["is_valid"])
        quote_b = res_b["kutipan_bukti_sektor"]
        self.assertTrue(len(quote_b) > 0)
        full_text_b = f"{art_b.get('judul', '')} {art_b.get('ringkasan_atau_narasi', '')}"
        self.assertIn(normalize_ws(quote_b), normalize_ws(full_text_b))

        # 3. Nilai sektor artikel percontohan juga wajib berbeda
        self.assertNotEqual(res_a["sektor_target"], res_b["sektor_target"])


class TestNoveltyVsVolumeRules(unittest.TestCase):
    """
    Pengujian aturan kebaruan vs volume:
    1. Novelty > Volume: Kategori baru muncul dengan >= 2 kasus mengalahkan kategori lama dengan volume lebih tinggi.
    2. False Alarm Guard: Kategori baru dengan hanya 1 kasus ditolak keras dan mengembalikan 'Kondisi Stabil'.
    3. Stabil State: Korpus dengan kondisi stabil tanpa ancaman baru mengembalikan 'Kondisi Stabil'.
    """

    def test_novelty_takes_precedence_over_high_volume_established_category(self):
        """Kategori baru (2 kasus) harus menang atas kategori lama (5 kasus di baseline & 5 di terkini)."""
        rows = []
        # Kategori Lama: Phishing (5 baseline, 5 terkini -> volume tinggi 10 artikel, 0% growth)
        phish_base = [
            "Marak Modus Phishing Undangan Nikah APK Palsu Mengincar Tabungan",
            "Pencurian Kredensial Nasabah Melalui Situs Phishing Bank Mandiri",
            "Penipuan Hadiah Mengatasnamakan Lembaga Keuangan Resmi Negara",
            "Phishing QRIS Palsu Menyasar Pedagang dan Toko UMKM",
            "Waspada Penipuan Kredensial Akun Finansial Melalui Pesan Singkat"
        ]
        phish_cur = [
            "Phishing Perbankan Menargetkan Nasabah Bank Mandiri dan BCA",
            "Penipuan Phishing APK Menguras Rekening Nasabah Bank BRI",
            "Sindikat Penipuan Online Palsu Mengatasnamakan Kantor Pajak",
            "Kampanye Phishing Kredensial SSO ASN Pemerintah Provinsi",
            "Tautan Phishing Finansial Memancing Korban Memberikan PIN"
        ]
        for i, judul in enumerate(phish_base):
            rows.append({
                "id": 10 + i, "kategori": "berita", "identifier": f"estab-base-{i}",
                "judul": judul, "sumber": "Detik", "kata_kunci": "phishing, penipuan, bank",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Kasus penipuan phishing perbankan stabil."
            })
        for i, judul in enumerate(phish_cur):
            rows.append({
                "id": 20 + i, "kategori": "berita", "identifier": f"estab-cur-{i}",
                "judul": judul, "sumber": "Kompas", "kata_kunci": "phishing, penipuan, bank",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Kasus penipuan phishing perbankan berlanjut."
            })

        # Kategori Baru: Ransomware (0 di baseline, 2 di terkini -> novelty!)
        rows.append({
            "id": 31, "kategori": "berita", "identifier": "nov-cur-1",
            "judul": "Varian Ransomware Baru Menyerang Infrastruktur Pelayanan",
            "sumber": "BSSN", "kata_kunci": "ransomware, enkripsi, baru, tebusan",
            "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00",
            "ringkasan_atau_narasi": "Ditemukan varian ransomware baru yang mengenkripsi data."
        })
        rows.append({
            "id": 32, "kategori": "berita", "identifier": "nov-cur-2",
            "judul": "Peringatan Ancaman Baru Serangan Ransomware Terkini",
            "sumber": "SecurityWeek", "kata_kunci": "ransomware, ancaman baru, tebusan",
            "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00",
            "ringkasan_atau_narasi": "Ancaman baru ransomware menyandera sistem database."
        })

        df = pd.DataFrame(rows)
        rag = RAGEngine(df)

        pola = rag.hitung_prediksi_pola_serangan()
        sinyal = rag.hitung_prediksi_ancaman_baru()

        # POLA ANCAMAN = Phishing (Volume tertinggi)
        self.assertEqual(pola["pola"], TAXONOMY_DISPLAY_NAMES["phishing_penipuan"])

        # SINYAL ANCAMAN BARU = Ransomware (Novelty > Volume karena baru muncul dengan >= 2 kasus)
        self.assertEqual(sinyal, TAXONOMY_DISPLAY_NAMES["ransomware"])

    def test_single_case_novelty_rejected_as_false_alarm(self):
        """Kategori baru dengan hanya 1 kasus tunggal wajib ditolak (mengembalikan 'Kondisi Stabil')."""
        rows = [
            # 3 artikel baseline Phishing
            {
                "id": 51, "kategori": "berita", "identifier": "base-p-1",
                "judul": "Phishing Kredensial Mengincar Pegawai",
                "sumber": "Detik", "kata_kunci": "phishing, penipuan",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Kasus penipuan phishing."
            },
            {
                "id": 52, "kategori": "berita", "identifier": "base-p-2",
                "judul": "Penipuan APK Palsu Marak",
                "sumber": "Kompas", "kata_kunci": "phishing, penipuan",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Kasus penipuan phishing."
            },
            # 2 artikel terkini Phishing
            {
                "id": 53, "kategori": "berita", "identifier": "cur-p-1",
                "judul": "Waspada Penipuan Link Phishing",
                "sumber": "Detik", "kata_kunci": "phishing, penipuan",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Kasus penipuan phishing."
            },
            {
                "id": 54, "kategori": "berita", "identifier": "cur-p-2",
                "judul": "Phishing Akun Layanan Publik",
                "sumber": "Kompas", "kata_kunci": "phishing, penipuan",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Kasus penipuan phishing."
            },
            # HANYA 1 ARTIKEL Ransomware baru di periode terkini
            {
                "id": 55, "kategori": "berita", "identifier": "isolated-ransomware",
                "judul": "Temuan Varian Ransomware Baru Terisolasi",
                "sumber": "CyberNews", "kata_kunci": "ransomware, baru, tebusan",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00",
                "ringkasan_atau_narasi": "Satu insiden varian baru ransomware terdeteksi pada workstation lokal."
            }
        ]

        df = pd.DataFrame(rows)
        rag = RAGEngine(df)
        sinyal = rag.hitung_prediksi_ancaman_baru()

        # 1 artikel tunggal TIDAK BOLEH memicu alarm sinyal ancaman baru!
        self.assertEqual(sinyal, "Kondisi Stabil")

    def test_adding_second_case_immediately_activates_threat_signal(self):
        """Menambahkan kasus kedua pada kategori baru langsung mengaktifkan sinyal ancaman."""
        rows = [
            # Baseline Phishing
            {"id": 61, "kategori": "berita", "identifier": "b-1", "judul": "Phishing Kredensial", "sumber": "A", "kata_kunci": "phishing", "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00", "ringkasan_atau_narasi": "Phishing."},
            {"id": 62, "kategori": "berita", "identifier": "b-2", "judul": "Penipuan Online", "sumber": "B", "kata_kunci": "penipuan", "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00", "ringkasan_atau_narasi": "Penipuan."},
            # Terkini Phishing
            {"id": 63, "kategori": "berita", "identifier": "c-1", "judul": "Phishing Kredensial Terkini", "sumber": "A", "kata_kunci": "phishing", "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00", "ringkasan_atau_narasi": "Phishing."},
            # Kasus 1 Malware Baru
            {"id": 64, "kategori": "berita", "identifier": "c-m1", "judul": "Varian Baru Malware Stealer", "sumber": "BSSN", "kata_kunci": "malware, baru, stealer", "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00", "ringkasan_atau_narasi": "Malware baru."},
        ]

        # 1 kasus -> Kondisi Stabil
        rag_1 = RAGEngine(pd.DataFrame(rows))
        self.assertEqual(rag_1.hitung_prediksi_ancaman_baru(), "Kondisi Stabil")

        # Tambahkan Kasus 2 Malware Baru
        rows.append(
            {"id": 65, "kategori": "berita", "identifier": "c-m2", "judul": "Ancaman Baru Malware Infostealer Aktif", "sumber": "SecurityWeek", "kata_kunci": "malware, ancaman baru, infostealer", "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 12:00:00", "ringkasan_atau_narasi": "Penyebaran malware infostealer baru."}
        )

        # 2 kasus -> Aktif Sinyal Malware
        rag_2 = RAGEngine(pd.DataFrame(rows))
        self.assertEqual(rag_2.hitung_prediksi_ancaman_baru(), TAXONOMY_DISPLAY_NAMES["malware"])


class TestExactSubstringSectorVerification(unittest.TestCase):
    """
    Pengujian validasi ketat sektor IIV Perpres 82/2022 Pasal 4:
    - 10 Sektor IIV tertutup + 'Tidak dapat ditentukan'.
    - Setiap sektor terklasifikasi WAJIB memiliki kutipan bukti yang merupakan exact substring berita.
    - Sektor 'Tidak dapat ditentukan' wajib memiliki kutipan kosong.
    - Sektor di luar daftar dan kutipan terhalusinasi/diubah wajib ditolak keras.
    """

    def setUp(self):
        self.analyzer = CTINewsAnalyzer(llm_mode="offline")

    def test_all_10_closed_iiv_sectors_with_exact_substring_verification(self):
        """Memvalidasi seluruh 10 Sektor IIV Perpres 82/2022 Pasal 4 beserta bukti kutipan substring."""
        cases = [
            (
                "Administrasi Pemerintahan",
                {
                    "judul": "Server BKD Jatim Mengalami Gangguan Akses Pelayanan Publik",
                    "ringkasan_atau_narasi": "Pemerintah Provinsi Jawa Timur melalui dinas terkait sedang memulihkan sistem administrasi kepegawaian."
                }
            ),
            (
                "Energi & Sumber Daya Mineral",
                {
                    "judul": "Sistem SCADA Pembangkit Listrik PLN Mengalami Gangguan Siber",
                    "ringkasan_atau_narasi": "Infrastruktur energi dan jaringan listrik pln dilaporkan mengalami anomali trafik pada pembangkit daya."
                }
            ),
            (
                "Transportasi",
                {
                    "judul": "Sistem Navigasi Radar Bandara Juanda Diserang Ransomware",
                    "ringkasan_atau_narasi": "Otoritas transportasi dan bandara mengonfirmasi terjadinya gangguan pada jadwal penerbangan pesawat."
                }
            ),
            (
                "Keuangan & Perbankan",
                {
                    "judul": "Serangan Siber Terkoordinasi Mengincar Nasabah Bank Mandiri",
                    "ringkasan_atau_narasi": "Lembaga keuangan perbankan mendeteksi upaya pembobolan saldo rekening nasabah bank nasional."
                }
            ),
            (
                "Kesehatan",
                {
                    "judul": "Data Pasien Rumah Sakit Umum Daerah Dr Soetomo Diduga Bocor",
                    "ringkasan_atau_narasi": "Manajemen rumah sakit memastikan data rekam medis pasien kesehatan tetap terlindungi dalam backup offline."
                }
            ),
            (
                "Teknologi Informasi & Komunikasi (TIK)",
                {
                    "judul": "Serangan DDoS Lumpuhkan Datacenter Provider Jaringan Telekomunikasi",
                    "ringkasan_atau_narasi": "Penyedia server hosting dan jaringan telekomunikasi indosat serta telkom mengalami penurunan bandwidth."
                }
            ),
            (
                "Pertahanan & Keamanan",
                {
                    "judul": "Situs Informasi Markas Militer Kodam Brawijaya Mengalami Defacement",
                    "ringkasan_atau_narasi": "Aparat pertahanan dan komando militer tni menginvestigasi peretasan pada portal keamanan nasional."
                }
            ),
            (
                "Pangan",
                {
                    "judul": "Sistem Distribusi Logistik Beras Perum Bulog Diretas",
                    "ringkasan_atau_narasi": "Ketahanan pangan nasional dan stok beras bulog untuk masyarakat dipastikan tidak terganggu insiden web."
                }
            ),
            (
                "Pendidikan",
                {
                    "judul": "Portal Seleksi Mahasiswa Baru Kampus Universitas Airlangga Tumbang",
                    "ringkasan_atau_narasi": "Server akademik universitas dan pendaftaran mahasiswa kampus unair diserang trafik banjir data."
                }
            ),
            (
                "Layanan Publik & Pengguna Digital",
                {
                    "judul": "Pencurian Akun WhatsApp Menimpa Puluhan Warga Pengguna Digital",
                    "ringkasan_atau_narasi": "Masyarakat dan konsumen pengguna digital diimbau waspada terhadap kode OTP pengambilalihan akun publik."
                }
            ),
        ]

        for expected_sector, article in cases:
            with self.subTest(sector=expected_sector):
                res = self.analyzer.classify_sector(article)
                sektor_hasil = res.get("sektor_target") or res.get("sektor")
                quote = res.get("kutipan_bukti_sektor") or res.get("kutipan_bukti")
                is_valid = res.get("is_valid")

                # 1. Sektor harus sesuai daftar tertutup
                self.assertEqual(sektor_hasil, expected_sector)
                self.assertIn(sektor_hasil, CLOSED_10_IIV_SECTORS)
                self.assertTrue(is_valid, f"Klasifikasi untuk {expected_sector} harus valid!")

                # 2. Kutipan bukti tidak boleh kosong untuk sektor aktif
                self.assertTrue(len(quote) > 0, f"Kutipan bukti untuk sektor {expected_sector} tidak boleh kosong!")

                # 3. KUTIPAN BUKTI HARUS MERUPAKAN EXACT SUBSTRING TEKS BERITA
                full_text = f"{article['judul']}. {article['ringkasan_atau_narasi']}"
                norm_quote = normalize_ws(quote)
                norm_full = normalize_ws(full_text)
                self.assertIn(norm_quote, norm_full, f"Kutipan '{quote}' harus exact substring dari teks berita!")

    def test_undetermined_sector_must_have_empty_quote(self):
        """Sektor 'Tidak dapat ditentukan' wajib memiliki kutipan bukti kosong."""
        article = {
            "judul": "Sosialisasi Tata Naskah Dinas dan Olahraga Pagi Bersama",
            "ringkasan_atau_narasi": "Kegiatan jalan sehat dan senam bersama diselenggarakan dengan penuh keakraban di lapangan terbuka."
        }
        res = self.analyzer.classify_sector(article)
        sektor_hasil = res.get("sektor_target") or res.get("sektor")
        quote = res.get("kutipan_bukti_sektor") or res.get("kutipan_bukti")

        self.assertEqual(sektor_hasil, "Tidak dapat ditentukan")
        self.assertEqual(quote, "")
        self.assertTrue(res.get("is_valid"))

    def test_out_of_list_sector_rejected_by_guard(self):
        """Sektor di luar 10 IIV Perpres 82/2022 wajib ditolak keras dan difallback."""
        invalid_sectors = [
            "Pariwisata & Perhotelan",
            "Sektor Swasta Murni",
            "E-Commerce & Belanja",
            "Otomotif & Manufaktur",
            "Pertambangan Liar"
        ]
        text = "Laporan insiden siber pada sektor perhotelan dan pariwisata swasta di Surabaya."

        for inv in invalid_sectors:
            with self.subTest(invalid_sector=inv):
                val_sector, val_quote, val_conf, is_valid = guard_sector_and_quote(
                    inv, "sektor perhotelan", text, confidence=0.9
                )
                self.assertFalse(is_valid, f"Sektor liar '{inv}' harus ditolak!")
                self.assertEqual(val_sector, "Tidak dapat ditentukan")
                self.assertEqual(val_quote, "")
                self.assertEqual(val_conf, 0.0)

    def test_hallucinated_or_mutated_quote_rejected_by_guard(self):
        """Kutipan yang tidak ada di teks berita (halusinasi) wajib ditolak keras."""
        text = "Pemerintah Provinsi Jawa Timur mendeteksi adanya serangan siber pada server kepegawaian."
        hallucinated_quote = "Kementerian Kominfo Pusat mendeteksi serangan malware ganas pada cloud"

        val_sector, val_quote, val_conf, is_valid = guard_sector_and_quote(
            "Administrasi Pemerintahan", hallucinated_quote, text, confidence=0.88
        )
        self.assertFalse(is_valid)
        self.assertEqual(val_sector, "Tidak dapat ditentukan")
        self.assertEqual(val_quote, "")
        self.assertEqual(val_conf, 0.0)

    def test_empty_quote_for_active_sector_rejected_by_guard(self):
        """Kutipan kosong untuk sektor aktif wajib ditolak keras."""
        text = "Pemerintah Provinsi Jawa Timur mendeteksi adanya serangan siber pada server kepegawaian."
        val_sector, val_quote, val_conf, is_valid = guard_sector_and_quote(
            "Administrasi Pemerintahan", "", text, confidence=0.88
        )
        self.assertFalse(is_valid)
        self.assertEqual(val_sector, "Tidak dapat ditentukan")
        self.assertEqual(val_quote, "")
        self.assertEqual(val_conf, 0.0)


class TestDatabasePipelineDynamicDatasetShift(unittest.TestCase):
    """
    Pengujian pergeseran dinamis pada tingkat basis data SQLite:
    1. Inisialisasi basis data uji terisolasi.
    2. Ingest Dataset A -> verifikasi hasil dashboard.
    3. Hapus dan ingest Dataset B -> verifikasi hasil dashboard bergeser 100% dinamis.
    """

    def setUp(self):
        self.temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db_file.close()
        self.db_path = Path(self.temp_db_file.name)
        init_db(self.db_path)

    def tearDown(self):
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except Exception:
                pass

    def test_database_level_dynamic_shift(self):
        """Membuktikan operasi ingest database mengubah KPI dan agregat secara dinamis."""
        test_suite = TestDynamicDatasetShift()
        test_suite.setUp()

        # 1. Ingest Dataset A ke tabel riwayat_tren
        articles_a = test_suite.dataset_a.to_dict("records")
        catat_untuk_tren(articles_a, db_path=self.db_path)

        with _koneksi(self.db_path) as conn:
            df_from_db_a = pd.read_sql_query("SELECT * FROM riwayat_tren WHERE kategori = 'berita'", conn)

        rag_db_a = RAGEngine(df_from_db_a)
        pola_a = rag_db_a.hitung_prediksi_pola_serangan()["pola"]
        sinyal_a = rag_db_a.hitung_prediksi_ancaman_baru()
        sektor_a = hitung_tren_sektor_target(df_from_db_a)[0]["sektor"]

        self.assertEqual(pola_a, TAXONOMY_DISPLAY_NAMES["phishing_penipuan"])
        self.assertEqual(sinyal_a, TAXONOMY_DISPLAY_NAMES["ransomware"])
        self.assertEqual(sektor_a, "Keuangan & Perbankan")

        # 2. Kosongkan tabel dan ingest Dataset B
        with _koneksi(self.db_path) as conn:
            conn.execute("DELETE FROM riwayat_tren")

        articles_b = test_suite.dataset_b.to_dict("records")
        catat_untuk_tren(articles_b, db_path=self.db_path)

        with _koneksi(self.db_path) as conn:
            df_from_db_b = pd.read_sql_query("SELECT * FROM riwayat_tren WHERE kategori = 'berita'", conn)

        rag_db_b = RAGEngine(df_from_db_b)
        pola_b = rag_db_b.hitung_prediksi_pola_serangan()["pola"]
        sinyal_b = rag_db_b.hitung_prediksi_ancaman_baru()
        sektor_b = hitung_tren_sektor_target(df_from_db_b)[0]["sektor"]

        self.assertEqual(pola_b, TAXONOMY_DISPLAY_NAMES["eksploitasi_kerentanan"])
        self.assertEqual(sinyal_b, TAXONOMY_DISPLAY_NAMES["malware"])
        self.assertEqual(sektor_b, "Kesehatan")

        # 3. Assert dynamic cross-dataset shifting
        self.assertNotEqual(pola_a, pola_b)
        self.assertNotEqual(sinyal_a, sinyal_b)
        self.assertNotEqual(sektor_a, sektor_b)


class TestIntegrityMutationCheck(unittest.TestCase):
    """
    Uji Integritas Forensik (Mutation Check):
    Membalikkan distribusi dataset membuktikan bahwa keluaran sistem tidak ditanam
    secara statis (zero directed hardcoding).
    """

    def test_swapped_categories_inverts_pola_and_sinyal_output(self):
        """Membalik peran kategori A dan B secara mutlak membalik hasil prediksi."""
        # Dataset Mutasi:
        # Ransomware dijadikan kategori dominan lama (4 baseline, 4 terkini)
        # Phishing dijadikan kategori baru muncul (0 baseline, 2 terkini)
        ransom_base = [
            "Serangan Ransomware LockBit Menyandera Sistem Server Instansi",
            "Ransomware BlackCat Mengenkripsi Basis Data Kepegawaian Daerah",
            "Ancaman Ransomware Phobos Mengunci Akses Dokumen Perusahaan",
            "Pusat Data Lumpuh Akibat Terinfeksi Payload Ransomware Medusa"
        ]
        ransom_cur = [
            "Varian Ransomware Akira Mengincar Cadangan Data Storage Server",
            "Penyebaran Ransomware BianLian Menuntut Pembayaran Kripto Tebusan",
            "Serangan Ransomware RansomHub Mengunci Sistem Server Publik",
            "Insiden Enkripsi Ransomware Qilin Merusak Integritas File Utama"
        ]
        phish_cur_novel = [
            "Varian Baru Phishing APK Menargetkan Pengguna Layanan Digital",
            "Peringatan Ancaman Baru Phishing Undangan Digital Menguras Rekening"
        ]

        rows_mutated = []
        for i, judul in enumerate(ransom_base):
            rows_mutated.append({
                "id": 301 + i, "kategori": "berita", "identifier": f"mut-rb-{i}",
                "judul": judul, "sumber": "Detik", "kata_kunci": "ransomware, enkripsi, tebusan",
                "tanggal_publish": "2026-09-20", "tanggal_dicatat": "2026-09-20 10:00:00",
                "ringkasan_atau_narasi": "Ransomware lama mengenkripsi sistem."
            })
        for i, judul in enumerate(ransom_cur):
            rows_mutated.append({
                "id": 305 + i, "kategori": "berita", "identifier": f"mut-rc-{i}",
                "judul": judul, "sumber": "Kompas", "kata_kunci": "ransomware, enkripsi, tebusan",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 10:00:00",
                "ringkasan_atau_narasi": "Ransomware berlanjut mengenkripsi data."
            })
        for i, judul in enumerate(phish_cur_novel):
            rows_mutated.append({
                "id": 309 + i, "kategori": "berita", "identifier": f"mut-pn-{i}",
                "judul": judul, "sumber": "BSSN", "kata_kunci": "phishing, penipuan, varian baru",
                "tanggal_publish": "2026-09-28", "tanggal_dicatat": "2026-09-28 11:00:00",
                "ringkasan_atau_narasi": "Varian baru penipuan phishing menyebar."
            })

        df_mut = pd.DataFrame(rows_mutated)
        rag_mut = RAGEngine(df_mut)

        pola_mut = rag_mut.hitung_prediksi_pola_serangan()["pola"]
        sinyal_mut = rag_mut.hitung_prediksi_ancaman_baru()

        # Hasil wajib terbalik sesuai data:
        # Pola adalah Ransomware
        self.assertEqual(pola_mut, TAXONOMY_DISPLAY_NAMES["ransomware"])
        # Sinyal Baru adalah Phishing
        self.assertEqual(sinyal_mut, TAXONOMY_DISPLAY_NAMES["phishing_penipuan"])


if __name__ == "__main__":
    unittest.main()
