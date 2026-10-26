"""
Unit and Integration Test Suite: CTI Victim Sector Classification (10 IIV Perpres 82/2022 Pasal 4).

Menguji:
1. Batasan 10 Sektor IIV Tertutup + Fallback 'Tidak dapat ditentukan'.
2. Guardrail Substring Eksak (Valid substring diterima, kutipan terhalusinasi/diubah ditolak keras).
3. Penolakan Sektor di Luar Daftar (Out-of-list rejection).
4. Klasifikasi Sektor Deterministik & LLM Guardrails.
5. Persistensi Basis Data & Koreksi Admin Sektor.
6. Eksekusi Batch Mingguan (Weekly Batch Runner).
7. Kalkulasi Metrik Evaluasi Sektor (Precision, Recall, F1, Akurasi Sektor, Validitas Kutipan).
"""

import os
import csv
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.cti.preparer import (
    CLOSED_10_IIV_SECTORS,
    IIV_SECTOR_DISPLAY_NAMES,
    InvalidSectorError,
)
from src.cti.analyzer import (
    CTINewsAnalyzer,
    guard_sector_and_quote,
    classify_sector,
)
from src.storage.db import (
    init_db,
    _koneksi,
    simpan_intelijen_berita,
    ambil_intelijen_berita,
    simpan_koreksi_admin_sektor,
)
from src.cti.evaluator import (
    CTIEvaluator,
    generate_draft_dataset,
    calculate_evaluation_metrics,
)
from scripts.classify_weekly_sectors import classify_weekly_news_sectors, load_weekly_news


class TestIIVSectorTaxonomyConstants(unittest.TestCase):
    """Pengujian konstanta taksonomi 10 Sektor IIV Perpres 82/2022."""

    def test_canonical_10_iiv_sectors_count_and_fallback(self):
        """Memastikan daftar tertutup memuat tepat 10 sektor resmi + 1 fallback wajib."""
        self.assertEqual(len(CLOSED_10_IIV_SECTORS), 11)
        self.assertIn("Tidak dapat ditentukan", CLOSED_10_IIV_SECTORS)

        expected_sectors = [
            "Administrasi Pemerintahan",
            "Energi & Sumber Daya Mineral",
            "Transportasi",
            "Keuangan & Perbankan",
            "Kesehatan",
            "Teknologi Informasi & Komunikasi (TIK)",
            "Pertahanan & Keamanan",
            "Pangan",
            "Pendidikan",
            "Layanan Publik & Pengguna Digital",
            "Tidak dapat ditentukan",
        ]
        self.assertEqual(CLOSED_10_IIV_SECTORS, expected_sectors)

    def test_iiv_sector_display_names_mapping(self):
        """Memastikan seluruh sektor terpetakan dalam display names."""
        for sec in CLOSED_10_IIV_SECTORS:
            self.assertIn(sec, IIV_SECTOR_DISPLAY_NAMES)
            self.assertTrue(len(IIV_SECTOR_DISPLAY_NAMES[sec]) > 0)


class TestExactSubstringValidationGuard(unittest.TestCase):
    """Pengujian ketat guardrail validasi kutipan bukti (exact substring)."""

    def setUp(self):
        self.news_text = (
            "Dinas Kominfo Provinsi Jawa Timur mendeteksi adanya upaya peretasan "
            "terhadap server aplikasi perizinan terpadu pada hari Selasa kemarin. "
            "Tim CSIRT Diskominfo Jatim segera melakukan isolasi jaringan."
        )

    def test_valid_exact_substring_accepted(self):
        """Kutipan yang persis sama dengan teks berita harus diterima."""
        quote = "Dinas Kominfo Provinsi Jawa Timur mendeteksi adanya upaya peretasan"
        sektor, val_quote, conf, is_valid = guard_sector_and_quote(
            "Administrasi Pemerintahan", quote, self.news_text, confidence=0.90
        )
        self.assertTrue(is_valid)
        self.assertEqual(sektor, "Administrasi Pemerintahan")
        self.assertEqual(val_quote, quote)
        self.assertEqual(conf, 0.90)

    def test_case_insensitive_and_whitespace_normalization(self):
        """Kutipan dengan perbedaan huruf kapital atau spasi ganda tetap cocok."""
        quote = "dinas  kominfo provinsi jawa   timur mendeteksi"
        sektor, val_quote, conf, is_valid = guard_sector_and_quote(
            "Administrasi Pemerintahan", quote, self.news_text, confidence=0.85
        )
        self.assertTrue(is_valid)
        self.assertEqual(sektor, "Administrasi Pemerintahan")

    def test_altered_or_hallucinated_quote_rejected(self):
        """Kutipan yang diubah kata-katanya (halusinasi LLM) wajib ditolak keras."""
        hallucinated_quote = "Kementerian Kominfo Pusat mendeteksi serangan malware ganas"
        sektor, val_quote, conf, is_valid = guard_sector_and_quote(
            "Administrasi Pemerintahan", hallucinated_quote, self.news_text, confidence=0.90
        )
        self.assertFalse(is_valid)
        self.assertEqual(sektor, "Tidak dapat ditentukan")
        self.assertEqual(val_quote, "")
        self.assertEqual(conf, 0.0)

    def test_empty_quote_for_active_sector_rejected(self):
        """Kutipan kosong untuk sektor aktif wajib ditolak keras."""
        sektor, val_quote, conf, is_valid = guard_sector_and_quote(
            "Kesehatan", "", self.news_text
        )
        self.assertFalse(is_valid)
        self.assertEqual(sektor, "Tidak dapat ditentukan")
        self.assertEqual(val_quote, "")
        self.assertEqual(conf, 0.0)

    def test_fallback_sector_accepted_with_empty_quote(self):
        """Sektor 'Tidak dapat ditentukan' sah dengan kutipan kosong."""
        sektor, val_quote, conf, is_valid = guard_sector_and_quote(
            "Tidak dapat ditentukan", "", self.news_text
        )
        self.assertTrue(is_valid)
        self.assertEqual(sektor, "Tidak dapat ditentukan")
        self.assertEqual(val_quote, "")
        self.assertEqual(conf, 0.0)


class TestOutOfListSectorRejection(unittest.TestCase):
    """Pengujian penolakan sektor di luar daftar 10 IIV."""

    def test_out_of_list_sector_rejected_hard(self):
        """Label sektor liar yang bukan anggota CLOSED_10_IIV_SECTORS harus ditolak."""
        bogus_sectors = [
            "Sektor Swasta Murni",
            "Pariwisata & Hiburan",
            "Kripto Desentralisasi",
            "Otomotif",
            "Perdagangan Bebas",
        ]
        text = "Sektor pariwisata Jawa Timur mengalami peningkatan kunjungan wisatawan."
        for bogus in bogus_sectors:
            sektor, quote, conf, is_valid = guard_sector_and_quote(
                bogus, "Sektor pariwisata", text
            )
            self.assertFalse(is_valid)
            self.assertEqual(sektor, "Tidak dapat ditentukan")
            self.assertEqual(quote, "")
            self.assertEqual(conf, 0.0)


class TestSectorClassificationEngine(unittest.TestCase):
    """Pengujian modul analisis dan klasifikasi sektor (offline & mocked LLM)."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = Path(self.temp_db.name)
        init_db(self.db_path)
        self.analyzer = CTINewsAnalyzer(db_path=self.db_path, llm_mode="offline")

    def tearDown(self):
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except Exception:
                pass

    def test_offline_classification_government(self):
        """Artikel pemerintah daerah terklasifikasi sebagai Administrasi Pemerintahan."""
        article = {
            "judul": "Server BKD Jatim Mengalami Gangguan Akses Layanan",
            "ringkasan_atau_narasi": "Pemerintah Provinsi Jawa Timur melalui dinas terkait sedang memulihkan sistem.",
        }
        res = self.analyzer.classify_sector(article)
        self.assertEqual(res["sektor_target"], "Administrasi Pemerintahan")
        self.assertTrue(res["is_valid"])
        self.assertIn(res["kutipan_bukti_sektor"].lower(), f"{article['judul']} {article['ringkasan_atau_narasi']}".lower())

    def test_offline_classification_healthcare(self):
        """Artikel rumah sakit terklasifikasi sebagai Kesehatan."""
        article = {
            "judul": "Data Pasien RSUD Dr Soetomo Surabaya Diduga Bocor",
            "ringkasan_atau_narasi": "Pihak rumah sakit menegaskan data rekam medis pasien tetap aman dan terenkripsi.",
        }
        res = self.analyzer.classify_sector(article)
        self.assertEqual(res["sektor_target"], "Kesehatan")
        self.assertTrue(res["is_valid"])
        self.assertTrue(len(res["kutipan_bukti_sektor"]) > 0)

    def test_offline_classification_banking(self):
        """Artikel perbankan terklasifikasi sebagai Keuangan & Perbankan."""
        article = {
            "judul": "Nasabah Keluhkan Gangguan Aplikasi M-Banking Bank Daerah",
            "ringkasan_atau_narasi": "Transaksi finansial dan transfer rekening dilaporkan sempat tertunda.",
        }
        res = self.analyzer.classify_sector(article)
        self.assertEqual(res["sektor_target"], "Keuangan & Perbankan")
        self.assertTrue(res["is_valid"])

    def test_offline_classification_non_incident_fallback(self):
        """Artikel seremonial tanpa korban IIV fallback ke 'Tidak dapat ditentukan'."""
        article = {
            "judul": "Gowes Sehat Pagi Hari Bersama Warga di Taman Kota",
            "ringkasan_atau_narasi": "Kegiatan rutin akhir pekan berlangsung meriah di alun-alun.",
        }
        res = self.analyzer.classify_sector(article)
        self.assertEqual(res["sektor_target"], "Tidak dapat ditentukan")
        self.assertEqual(res["kutipan_bukti_sektor"], "")
        self.assertEqual(res["confidence_sektor"], 0.0)

    def test_analyze_news_integrates_sector_fields(self):
        """analyze_news harus menyimpan dan menyertakan field sektor target."""
        article = {
            "identifier": "news-test-sec-001",
            "judul": "Serangan Siber Menargetkan Gardu Induk Listrik PLN",
            "ringkasan_atau_narasi": "Sistem pasokan daya listrik energi nasional berhasil diisolasi oleh tim tanggap darurat.",
        }
        record = self.analyzer.analyze_news(article, persist=True)
        self.assertEqual(record["sektor_target"], "Energi & Sumber Daya Mineral")
        self.assertIn("sektor_target", record)
        self.assertIn("confidence_sektor", record)
        self.assertIn("kutipan_bukti_sektor", record)
        self.assertIn("alasan_sektor", record)

        saved = ambil_intelijen_berita("news-test-sec-001", db_path=self.db_path)
        self.assertIsNotNone(saved)
        self.assertEqual(saved["sektor_target"], "Energi & Sumber Daya Mineral")


    def test_llm_mode_with_mock_and_guard(self):
        """Simulasi respons LLM: jika LLM memprediksi valid, diterima oleh guard."""
        analyzer_llm = CTINewsAnalyzer(db_path=self.db_path, llm_mode="gemini")
        article = {
            "judul": "Kampus Universitas Airlangga Luncurkan Sistem Keamanan Baru",
            "ringkasan_atau_narasi": "Langkah ini untuk mengamankan data mahasiswa dan dosen universitas.",
        }
        fake_llm_response = json.dumps({
            "sektor": "Pendidikan",
            "kutipan_bukti": "Langkah ini untuk mengamankan data mahasiswa dan dosen universitas.",
            "confidence": 0.92,
            "alasan": "Menyebut data mahasiswa dan dosen universitas",
        })

        with patch("src.utils.llm_adapter.GeminiLLMAdapter.chat", return_value=fake_llm_response):
            res = analyzer_llm.classify_sector(article)
            self.assertEqual(res["sektor_target"], "Pendidikan")
            self.assertEqual(res["confidence_sektor"], 0.92)
            self.assertTrue(res["is_valid"])


class TestDatabasePersistenceAndAdminCorrection(unittest.TestCase):
    """Pengujian schema migrasi dan koreksi manual admin pada sektor."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = Path(self.temp_db.name)
        init_db(self.db_path)

    def tearDown(self):
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except Exception:
                pass

    def test_schema_columns_exist(self):
        """Memastikan kolom sektor ada di tabel intelijen_berita_tervalidasi."""
        with _koneksi(self.db_path) as conn:
            cur = conn.execute("PRAGMA table_info(intelijen_berita_tervalidasi)")
            cols = [r[1] for r in cur.fetchall()]
            for expected_col in [
                "sektor_target",
                "confidence_sektor",
                "kutipan_bukti_sektor",
                "alasan_sektor",
                "koreksi_admin_sektor",
            ]:
                self.assertIn(expected_col, cols)

    def test_simpan_dan_ambil_koreksi_admin_sektor(self):
        """Admin dapat mengoreksi sektor sasaran berita secara persisten."""
        art_id = "news-sec-corr-001"
        rec = {
            "article_identifier": art_id,
            "kategori_insiden": "ransomware",
            "confidence_kategori": 0.9,
            "sektor_target": "Tidak dapat ditentukan",
            "confidence_sektor": 0.0,
            "kutipan_bukti_sektor": "",
            "alasan_sektor": "Awalnya tidak terdeteksi",
        }
        simpan_intelijen_berita(rec, db_path=self.db_path)

        success = simpan_koreksi_admin_sektor(
            article_identifier=art_id,
            sektor="Administrasi Pemerintahan",
            alasan="Instansi korban adalah Badan Kepegawaian Daerah",
            oleh="analis_csirt",
            db_path=self.db_path,
        )
        self.assertTrue(success)

        loaded = ambil_intelijen_berita(art_id, db_path=self.db_path)
        self.assertEqual(loaded["koreksi_admin_sektor"], "Administrasi Pemerintahan")
        self.assertEqual(loaded["alasan_sektor"], "Instansi korban adalah Badan Kepegawaian Daerah")


class TestWeeklyBatchClassification(unittest.TestCase):
    """Pengujian batch runner skrip klasifikasi sektor berita mingguan."""

    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.db_path = Path(self.temp_db.name)
        init_db(self.db_path)

        # Seed data riwayat_tren 7 hari terakhir
        with _koneksi(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO riwayat_tren (kategori, identifier, judul, sumber, ringkasan_atau_narasi, tanggal_publish, tanggal_dicatat)
                VALUES 
                ('berita', 'batch-sec-1', 'Dinas Kesehatan Jatim Gelar Audit SPBE Medis', 'Diskominfo', 'Sistem rekam medis dan data pasien rumah sakit diaudit.', '2026-10-20', '2026-10-20'),
                ('berita', 'batch-sec-2', 'Bank Jatim Tingkatkan Keamanan Transaksi Digital', 'Diskominfo', 'Penguatan proteksi rekening dan aplikasi m-banking.', '2026-10-19', '2026-10-19'),
                ('berita', 'batch-sec-3', 'Sosialisasi Literasi Budaya Daerah', 'Humas', 'Rapat kerja pelestarian kebudayaan lokal.', '2026-10-18', '2026-10-18')
                """
            )

    def tearDown(self):
        if self.db_path.exists():
            try:
                self.db_path.unlink()
            except Exception:
                pass

    def test_weekly_batch_runner_execution(self):
        """Skrip batch mingguan berhasil memproses berita dan menyimpan hasil ke database."""
        result = classify_weekly_news_sectors(db_path=self.db_path, days=7)
        self.assertEqual(result["status"], "SUCCESS")
        self.assertEqual(result["total_processed"], 3)
        self.assertTrue(result["valid_quotes_count"] >= 2)
        self.assertTrue(result["quote_validity_rate"] > 0.5)

        # Cek database terisi sektor
        intel1 = ambil_intelijen_berita("batch-sec-1", db_path=self.db_path)
        self.assertIsNotNone(intel1)
        self.assertEqual(intel1["sektor_target"], "Kesehatan")

        intel2 = ambil_intelijen_berita("batch-sec-2", db_path=self.db_path)
        self.assertIsNotNone(intel2)
        self.assertEqual(intel2["sektor_target"], "Keuangan & Perbankan")


class TestEvaluationMetricCalculations(unittest.TestCase):
    """Pengujian pembentukan dataset evaluasi draf dan kalkulasi metrik sektor (Precision, Recall, F1)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.dir_path = Path(self.temp_dir.name)
        self.db_path = self.dir_path / "test_eval.db"
        init_db(self.db_path)

        with _koneksi(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO riwayat_tren (kategori, identifier, judul, sumber, ringkasan_atau_narasi, tanggal_publish, tanggal_dicatat)
                VALUES 
                ('berita', 'eval-1', 'RSUD Soetomo Surabaya Terkena Ransomware', 'Radar', 'Sistem rumah sakit dan data rekam medis pasien terganggu.', '2026-10-20', '2026-10-20'),
                ('berita', 'eval-2', 'Bank Daerah Jatim Perkuat Firewall M-Banking', 'Tempo', 'Proteksi transaksi nasabah dan rekening ditingkatkan.', '2026-10-20', '2026-10-20')
                """
            )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_draft_dataset_includes_sector_columns(self):
        """Dataset draf yang dibangkitkan wajib memiliki kolom sektor target."""
        csv_out = self.dir_path / "draft.csv"
        generate_draft_dataset(db_path=self.db_path, output_csv_path=csv_out, sample_size=10)
        self.assertTrue(csv_out.exists())

        with open(csv_out, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            self.assertIn("prediksi_sektor", fieldnames)
            self.assertIn("confidence_sektor", fieldnames)
            self.assertIn("kutipan_bukti_sektor", fieldnames)
            self.assertIn("verified_sektor", fieldnames)
            self.assertIn("status_label", fieldnames)

            rows = list(reader)
            self.assertEqual(len(rows), 2)
            for r in rows:
                self.assertEqual(r["status_label"], "DRAFT_PENDING_USER_REVIEW")
                self.assertEqual(r["verified_sektor"], "")  # Dibiarkan kosong untuk verifikasi user
                self.assertTrue(len(r["prediksi_sektor"]) > 0)

    def test_calculate_evaluation_metrics_precision_recall_f1(self):
        """Kalkulasi Precision, Recall, F1, Akurasi Sektor, dan Validitas Kutipan."""
        csv_file = self.dir_path / "verified_sector_dataset.csv"
        rows = [
            {
                "id_berita": "1",
                "judul": "Data RSUD Jatim Diretas",
                "ringkasan": "Data pasien rumah sakit bocor.",
                "prediksi_sektor": "Kesehatan",
                "confidence_sektor": "0.90",
                "kutipan_bukti_sektor": "Data pasien rumah sakit bocor.",
                "verified_sektor": "Kesehatan",
                "status_label": "VERIFIED",
            },
            {
                "id_berita": "2",
                "judul": "Bank Nasional Alami Serangan DDoS",
                "ringkasan": "Layanan transaksi rekening perbankan offline.",
                "prediksi_sektor": "Keuangan & Perbankan",
                "confidence_sektor": "0.85",
                "kutipan_bukti_sektor": "Layanan transaksi rekening perbankan offline.",
                "verified_sektor": "Keuangan & Perbankan",
                "status_label": "VERIFIED",
            },
            {
                "id_berita": "3",
                "judul": "Portal Dinas Pendidikan Diretas",
                "ringkasan": "Situs sekolah dan pendaftaran siswa dibobol.",
                "prediksi_sektor": "Pendidikan",
                "confidence_sektor": "0.88",
                "kutipan_bukti_sektor": "Situs sekolah dan pendaftaran siswa dibobol.",
                "verified_sektor": "Administrasi Pemerintahan",  # Koreksi analis: sebenarnya admin pemda
                "status_label": "VERIFIED",
            },
        ]
        fieldnames = list(rows[0].keys())
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fieldnames)
            w.writeheader()
            w.writerows(rows)

        metrics = calculate_evaluation_metrics(csv_file)
        self.assertEqual(metrics["status"], "SUCCESS")
        self.assertEqual(metrics["sector_samples"], 3)
        self.assertIn("sectors", metrics)
        self.assertIn("sector_accuracy", metrics)
        self.assertIn("quote_validity_rate", metrics)

        # 2 dari 3 prediksi cocok dengan koreksi (Kesehatan dan Keuangan cocok, Pendidikan != Administrasi)
        expected_accuracy = round(2 / 3, 4)
        self.assertEqual(metrics["sector_accuracy"], expected_accuracy)

        # Seluruh 3 kutipan bukti adalah substring valid dari teks berita
        self.assertEqual(metrics["quote_validity_rate"], 1.0)

        # Cek F1 Kesehatan = 1.0 (TP=1, FP=0, FN=0)
        self.assertEqual(metrics["sectors"]["Kesehatan"]["f1_score"], 1.0)
        self.assertEqual(metrics["sectors"]["Kesehatan"]["precision"], 1.0)
        self.assertEqual(metrics["sectors"]["Kesehatan"]["recall"], 1.0)


if __name__ == "__main__":
    unittest.main()
