"""
tests/test_adversarial_challenger_1.py
Adversarial Stress Test Suite — Challenger 1 (Gate Certification).

Adversarial stress-testing of SiberHarian CTI Dynamic Upgrade:
1. Adversarial Sector & Evidence Quote:
   - Tricky mutated quotes (insertions, deletions, transpositions, Levenshtein mutations)
   - Whitespace and formatting variations (tabs, mixed newlines, non-breaking spaces)
   - Cross-article quotes and hallucinations
   - Out-of-list sectors, prompt injections, and partial sector matches
   - Valid acceptance of 'Tidak dapat ditentukan' with empty quote
2. Novelty vs Volume Edge Cases:
   - Exactly 1 article for a brand new novel category (must return 'Kondisi Stabil')
   - Exactly 2 articles of novel category vs 50 articles of established category (novelty > volume)
   - Zero articles in dataset (graceful handling, zero crashes)
   - Rapid category surges (growth >= 200%, cnt_cur >= 2)
3. Option A SITREP Zero-Fallback Stress-Test:
   - Zero-technique situation in cti_agents.py (assert T1190, D3-MFA, AC-2 never appear)
   - Unmapped or unknown technique IDs (T9999) produce zero static fallback mitigations
   - Empty DB eCSIRT distribution produces zero fabricated taxonomy distributions
   - Full pipeline execution across instant_rag and modular_llm fallback modes
"""

import os
import re
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from typing import Dict, List, Any

from src.cti.preparer import (
    CLOSED_10_IIV_SECTORS,
    IIV_SECTOR_DISPLAY_NAMES,
    CLOSED_11_TAXONOMY_CATEGORIES,
    TAXONOMY_DISPLAY_NAMES,
)
from src.cti.analyzer import (
    guard_sector_and_quote,
    _normalize_whitespace,
)
from src.analytics.rag_engine import (
    RAGEngine,
    resolve_article_taxonomy_category,
)
from src.analytics.cti_agents import (
    _format_distribusi_ecsirt,
    _format_rujukan_mitre,
    _format_mitigasi_d3fend_nist,
    _deteksi_sektor_spesifik,
    _deteksi_senjata_spesifik,
    _deteksi_dampak_spesifik,
    _generate_section_1_makro,
    _generate_section_2_mikro,
    _generate_section_3_vektor,
    _generate_section_4_rekomendasi,
    _generate_section_5_emerging,
    _buat_fallback_sitrep_deterministik,
    jalankan_pipeline_multi_agent,
)


class TestAdversarialSectorAndQuote(unittest.TestCase):
    """
    Adversarial attacks against guard_sector_and_quote to verify 100% strict rejection
    of invalid sectors, hallucinated quotes, and mutated substrings.
    """

    def setUp(self):
        self.sample_text = (
            "Dinas Komunikasi dan Informatika Provinsi Jawa Timur mendeteksi adanya "
            "upaya serangan siber yang menargetkan server Administrasi Pemerintahan. "
            "Pihak Bank Jatim juga mengonfirmasi adanya serangan phishing perbankan "
            "yang menyasar nasabah layanan keuangan digital."
        )

    # -------------------------------------------------------------------------
    # 1. Mutated Quote Attacks (Must be REJECTED)
    # -------------------------------------------------------------------------
    def test_quote_with_inserted_character_rejected(self):
        """Quote dengan penambahan 1 karakter di awal/tengah/akhir harus DITOLAK KERAS."""
        mutations = [
            "XDinas Komunikasi dan Informatika",  # insert at start
            "Dinas Komunikasi X dan Informatika",  # insert in middle
            "Dinas Komunikasi dan InformatikaX",  # insert at end
            "Dinas Komunikasi dan Informastika",  # single typo insertion
        ]
        for mutated_quote in mutations:
            sektor, quote, conf, is_valid = guard_sector_and_quote(
                sektor="Administrasi Pemerintahan",
                kutipan_bukti=mutated_quote,
                teks_berita=self.sample_text,
            )
            self.assertFalse(
                is_valid,
                f"Kutipan termutasi '{mutated_quote}' seharusnya ditolak, tapi lolos!"
            )
            self.assertEqual(sektor, "Tidak dapat ditentukan")
            self.assertEqual(quote, "")
            self.assertEqual(conf, 0.0)

    def test_quote_with_deleted_character_rejected(self):
        """Quote dengan typo penghapusan huruf internal (bukan substring eksak) harus DITOLAK KERAS."""
        mutations = [
            "Dinas Komunikas dan Informatika",   # 'i' deleted from Komunikasi
            "Dins Komunikasi dan Informatika",   # 'a' deleted from Dinas
            "server Administrasi Pemerintahn",   # 'a' deleted from Pemerintahan
            "Pihak Bak Jatim",                   # 'n' deleted from Bank
            "layanan keuagan digital",           # 'n' deleted from keuangan
        ]
        for mutated_quote in mutations:
            sektor, quote, conf, is_valid = guard_sector_and_quote(
                sektor="Administrasi Pemerintahan",
                kutipan_bukti=mutated_quote,
                teks_berita=self.sample_text,
            )
            self.assertFalse(is_valid, f"Kutipan hilang huruf '{mutated_quote}' lolos validasi!")
            self.assertEqual(sektor, "Tidak dapat ditentukan")
            self.assertEqual(quote, "")

    def test_quote_with_transposed_characters_rejected(self):
        """Quote dengan pertukaran 2 huruf bersebelahan (transposition) harus DITOLAK KERAS."""
        mutations = [
            "Dinas Komuniksai dan Informatika",  # sa -> as
            "server Admnistrasi Pemerintahan",  # mi -> im
            "Pihak Bnak Jatim",                  # an -> na
        ]
        for mutated_quote in mutations:
            sektor, quote, conf, is_valid = guard_sector_and_quote(
                sektor="Administrasi Pemerintahan",
                kutipan_bukti=mutated_quote,
                teks_berita=self.sample_text,
            )
            self.assertFalse(is_valid, f"Kutipan transposisi '{mutated_quote}' lolos validasi!")
            self.assertEqual(sektor, "Tidak dapat ditentukan")

    def test_quote_with_homoglyph_or_substitution_rejected(self):
        """Quote dengan substitusi huruf mirip (e.g. angka '0' utk 'O', '1' utk 'l') harus DITOLAK."""
        mutations = [
            "Dinas K0munikasi dan Informatika",  # '0' for 'o'
            "Dinas Komunikasi dan lnformatika",  # 'l' for 'I'
            "Pihak Bank Jat1m",                  # '1' for 'i'
        ]
        for mutated_quote in mutations:
            sektor, quote, conf, is_valid = guard_sector_and_quote(
                sektor="Administrasi Pemerintahan",
                kutipan_bukti=mutated_quote,
                teks_berita=self.sample_text,
            )
            self.assertFalse(is_valid, f"Kutipan substitusi '{mutated_quote}' lolos validasi!")

    # -------------------------------------------------------------------------
    # 2. Whitespace and Normalization Boundary Tests
    # -------------------------------------------------------------------------
    def test_quote_with_tabs_and_newlines_normalized_properly(self):
        """
        Quote yang memuat tab atau newline di antara kata-kata yang valid
        harus dinormalisasi spasi putihnya dan DITERIMA jika urutan kata persis.
        """
        # Exact matching words with differing whitespace/newlines
        quote_tab_newline = "Dinas\tKomunikasi\n\ndan\r\nInformatika"
        sektor, quote, conf, is_valid = guard_sector_and_quote(
            sektor="Administrasi Pemerintahan",
            kutipan_bukti=quote_tab_newline,
            teks_berita=self.sample_text,
        )
        self.assertTrue(is_valid, "Whitespace-normalized quote harusnya valid!")
        self.assertEqual(sektor, "Administrasi Pemerintahan")
        self.assertEqual(conf, 0.85)

    def test_quote_only_whitespace_or_newlines_rejected_for_active_sector(self):
        """Quote yang hanya berisi spasi, tab, newline, atau string kosong harus DITOLAK untuk sektor aktif."""
        blank_quotes = [
            "",
            "   ",
            "\t\t",
            "\n\r\n",
            "   \t  \n  ",
        ]
        for bq in blank_quotes:
            sektor, quote, conf, is_valid = guard_sector_and_quote(
                sektor="Administrasi Pemerintahan",
                kutipan_bukti=bq,
                teks_berita=self.sample_text,
            )
            self.assertFalse(is_valid, f"Whitespace-only quote '{repr(bq)}' lolos untuk sektor aktif!")
            self.assertEqual(sektor, "Tidak dapat ditentukan")
            self.assertEqual(quote, "")

    # -------------------------------------------------------------------------
    # 3. Cross-Article & Hallucination Attacks
    # -------------------------------------------------------------------------
    def test_quote_from_different_article_rejected(self):
        """Kutipan yang berasal dari artikel lain (tidak ada di teks saat ini) harus DITOLAK."""
        external_quote = "Rumah Sakit Umum Daerah Dr Soetomo mengalami kelumpuhan sistem"
        sektor, quote, conf, is_valid = guard_sector_and_quote(
            sektor="Kesehatan",
            kutipan_bukti=external_quote,
            teks_berita=self.sample_text,
        )
        self.assertFalse(is_valid, "Kutipan dari artikel lain lolos validasi!")
        self.assertEqual(sektor, "Tidak dapat ditentukan")
        self.assertEqual(quote, "")

    def test_empty_or_none_news_text_rejected(self):
        """Teks berita kosong atau None harus menolak kutipan apapun untuk sektor aktif."""
        sektor, quote, conf, is_valid = guard_sector_and_quote(
            sektor="Administrasi Pemerintahan",
            kutipan_bukti="Dinas Komunikasi",
            teks_berita="",
        )
        self.assertFalse(is_valid)
        self.assertEqual(sektor, "Tidak dapat ditentukan")

        sektor2, quote2, conf2, is_valid2 = guard_sector_and_quote(
            sektor="Administrasi Pemerintahan",
            kutipan_bukti="Dinas Komunikasi",
            teks_berita=None,
        )
        self.assertFalse(is_valid2)
        self.assertEqual(sektor2, "Tidak dapat ditentukan")

    # -------------------------------------------------------------------------
    # 4. Out-of-List & Prompt Injection Sectors
    # -------------------------------------------------------------------------
    def test_out_of_list_and_injection_sectors_rejected(self):
        """Sektor yang tidak terdaftar dalam CLOSED_10_IIV_SECTORS harus DITOLAK 100%."""
        illegal_sectors = [
            "Komersial Swasta",
            "Sektor BUMN",
            "Pendidikan Tinggi",  # Substring/superset
            "Administrasi",       # Partial name
            "Keuangan",           # Partial name
            "Administrasi Pemerintahan; DROP TABLE intelijen_berita_tervalidasi;--",
            "<script>alert(1)</script>",
            "12345",
            "E-Commerce & Startup",
            "Militer Asing",
        ]
        valid_quote = "Dinas Komunikasi dan Informatika"
        for ill_sec in illegal_sectors:
            sektor, quote, conf, is_valid = guard_sector_and_quote(
                sektor=ill_sec,
                kutipan_bukti=valid_quote,
                teks_berita=self.sample_text,
            )
            self.assertFalse(is_valid, f"Sektor terlarang '{ill_sec}' lolos validasi!")
            self.assertEqual(sektor, "Tidak dapat ditentukan")
            self.assertEqual(quote, "")

    def test_canonical_sector_case_insensitivity(self):
        """Sektor yang valid meskipun huruf besar semua atau ada spasi di ujung harus dinormalisasi ke kanonikal."""
        valid_quote = "Dinas Komunikasi dan Informatika"
        sektor, quote, conf, is_valid = guard_sector_and_quote(
            sektor="  ADMINISTRASI PEMERINTAHAN  ",
            kutipan_bukti=valid_quote,
            teks_berita=self.sample_text,
        )
        self.assertTrue(is_valid)
        self.assertEqual(sektor, "Administrasi Pemerintahan")
        self.assertEqual(quote, valid_quote)

    # -------------------------------------------------------------------------
    # 5. Fallback Acceptance ('Tidak dapat ditentukan')
    # -------------------------------------------------------------------------
    def test_fallback_sector_accepted_with_empty_or_non_empty_quote(self):
        """
        Label fallback 'Tidak dapat ditentukan' HARUS diterima:
        - Jika quote kosong -> diterima, quote tetap '', conf 0.0, is_valid=True.
        - Jika quote non-kosong -> diterima, tapi quote dipaksa '', conf 0.0, is_valid=True.
        """
        fallbacks = [
            "Tidak dapat ditentukan",
            "tidak dapat ditentukan",
            "tidak_dapat_ditentukan",
            "tidak ditentukan",
            "none",
            "-",
            "",
            None,
        ]
        for fb in fallbacks:
            # Subtest 1: quote kosong
            sektor, quote, conf, is_valid = guard_sector_and_quote(
                sektor=fb,
                kutipan_bukti="",
                teks_berita=self.sample_text,
            )
            self.assertTrue(is_valid, f"Fallback '{fb}' dengan quote kosong ditolak!")
            self.assertEqual(sektor, "Tidak dapat ditentukan")
            self.assertEqual(quote, "")
            self.assertEqual(conf, 0.0)

            # Subtest 2: quote berisi teks (harus dipaksa kosong demi integritas)
            sektor2, quote2, conf2, is_valid2 = guard_sector_and_quote(
                sektor=fb,
                kutipan_bukti="Kutipan apapun di sini",
                teks_berita=self.sample_text,
            )
            self.assertTrue(is_valid2, f"Fallback '{fb}' dengan quote teks ditolak!")
            self.assertEqual(sektor2, "Tidak dapat ditentukan")
            self.assertEqual(quote2, "", "Quote fallback seharusnya dipaksa kosong!")
            self.assertEqual(conf2, 0.0)


class TestAdversarialNoveltyVsVolume(unittest.TestCase):
    """
    Adversarial stress-testing of novelty vs volume trade-offs in KPI calculations:
    1. Exactly 1 article for a novel category MUST return 'Kondisi Stabil' (anti-false alarm).
    2. Exactly 2 articles of a brand new category vs 50 established articles:
       - Pola Ancaman MUST reflect the 50-article established category (volume dominance).
       - Sinyal Ancaman Baru MUST reflect the 2-article novel category (novelty > volume).
    3. Zero articles (empty DataFrame) MUST be handled gracefully without unhandled crashes.
    4. 1 article in entire dataset MUST NOT trigger threat signal.
    """

    def _create_mock_news_row(
        self,
        news_id: int,
        kategori_taksonomi: str,
        judul: str,
        ringkasan: str,
        tgl: str = "2026-09-28",
        kata_kunci: str = ""
    ) -> Dict[str, Any]:
        return {
            "id": news_id,
            "identifier": f"adv-{news_id}",
            "kategori": "berita",
            "kategori_relevansi": "insiden_spesifik",
            "judul": judul,
            "ringkasan_atau_narasi": ringkasan,
            "sumber": "Adversarial Stress Harness",
            "tanggal_publish": tgl,
            "tanggal_dicatat": f"{tgl} 10:00:00",
            "kata_kunci": kata_kunci,
            "kategori_insiden": kategori_taksonomi,
            "kategori_utama": kategori_taksonomi,
        }

    # -------------------------------------------------------------------------
    # 1. Exactly 1 Article of Novel Category (Must Reject as False Alarm)
    # -------------------------------------------------------------------------
    def test_single_article_novel_category_returns_kondisi_stabil(self):
        """
        1 artikel tunggal kategori baru (meskipun memuat kata kunci kebaruan kritis)
        HARUS menghasilkan 'Kondisi Stabil' pada hitung_prediksi_ancaman_baru.
        Ambang batas cnt_cur >= 2 tidak boleh dilanggar.
        """
        # Baseline dataset kosong (atau 0 kasus untuk ransomware)
        # Periode terkini: tepat 1 artikel ransomware dengan kata kunci sangat novel
        records = [
            self._create_mock_news_row(
                news_id=1,
                kategori_taksonomi="Ransomware",
                judul="Peringatan Kritis: Varian Baru Ransomware X Ditemukan Menyerang",
                ringkasan="Ditemukan ancaman baru malware ransomware zero-day yang sangat berbahaya dan aktif.",
                tgl="2026-09-28",
                kata_kunci="ransomware, baru, zero-day, novel, kritis",
            )
        ]
        df = pd.DataFrame(records)
        rag = RAGEngine(df_riwayat=df)

        sinyal_baru = rag.hitung_prediksi_ancaman_baru()
        self.assertEqual(
            sinyal_baru,
            "Kondisi Stabil",
            f"1 artikel tunggal seharusnya ditolak sebagai 'Kondisi Stabil', tapi menghasilkan: '{sinyal_baru}'"
        )

        ancaman_dict = rag.ambil_berita_ancaman_baru()
        self.assertFalse(ancaman_dict.get("ada"), "Field 'ada' harus bernilai False untuk 1 artikel!")
        self.assertEqual(ancaman_dict.get("nama"), "Kondisi Stabil")

    # -------------------------------------------------------------------------
    # 2. Exactly 2 Articles Novel vs 50 Established (Novelty > Volume Rule)
    # -------------------------------------------------------------------------
    def test_two_articles_novel_vs_fifty_established_articles(self):
        """
        Adversarial Stress Test:
        - 50 artikel Phishing / Penipuan di periode terkini dan 50 di baseline (growth 0%, high volume).
        - 2 artikel Ransomware di periode terkini, 0 di baseline (novel category, 100% new, cnt_cur = 2).
        Verifikasi:
        - [ POLA ANCAMAN ] = Phishing / Penipuan Siber (volume 50).
        - [ SINYAL ANCAMAN BARU ] = Ransomware (kebaruan menang atas volume 50!).
        """
        records = []
        news_id = 1

        # 50 artikel baseline Phishing dengan judul bervariasi agar tidak di-dedup
        for i in range(50):
            records.append(self._create_mock_news_row(
                news_id=news_id,
                kategori_taksonomi="Phishing / Penipuan Siber",
                judul=f"Laporan Penipuan Phishing Entitas {i+1} Perbankan Nasional",
                ringkasan=f"Modus penipuan phishing lawas nomor {i+1} mengincar akun finansial nasabah.",
                tgl="2026-09-20",  # Baseline period
                kata_kunci="phishing, penipuan, bank",
            ))
            news_id += 1

        # 50 artikel terkini Phishing (volume tetap tinggi)
        for i in range(50):
            records.append(self._create_mock_news_row(
                news_id=news_id,
                kategori_taksonomi="Phishing / Penipuan Siber",
                judul=f"Kasus Lanjutan Phishing Lembaga Finansial {i+1} Jawa Timur",
                ringkasan=f"Modus penipuan phishing berlanjut pada unit perbankan {i+1} minggu ini.",
                tgl="2026-09-28",  # Current period
                kata_kunci="phishing, penipuan, bank",
            ))
            news_id += 1

        # TEPAT 2 artikel terkini Ransomware (kategori baru muncul 0 di baseline)
        records.append(self._create_mock_news_row(
            news_id=news_id,
            kategori_taksonomi="Ransomware",
            judul="Peringatan Varian Baru Ransomware Kritis Muncul di Indonesia",
            ringkasan="Ditemukan modus baru serangan ransomware zero-day yang mengunci data.",
            tgl="2026-09-28",
            kata_kunci="ransomware, baru, novel, zero-day",
        ))
        news_id += 1
        records.append(self._create_mock_news_row(
            news_id=news_id,
            kategori_taksonomi="Ransomware",
            judul="Insiden Kedua Varian Baru Ransomware Terdeteksi di Sektor Finansial",
            ringkasan="Serangan baru ransomware mengonfirmasi tren baru ancaman pemerasan.",
            tgl="2026-09-28",
            kata_kunci="ransomware, baru, lonjakan, ancaman baru",
        ))

        df = pd.DataFrame(records)
        rag = RAGEngine(df_riwayat=df)

        # 1. Pola Ancaman harus dimenangkan oleh volume 50 Phishing
        pola_res = rag.hitung_prediksi_pola_serangan()
        self.assertEqual(
            pola_res["pola"],
            "Phishing / Penipuan Siber",
            f"Pola ancaman seharusnya Phishing / Penipuan Siber (volume 50), didapat: {pola_res['pola']}"
        )
        self.assertGreaterEqual(pola_res["jumlah_terkini"], 40)

        # 2. Sinyal Ancaman Baru HARUS dimenangkan oleh Ransomware (kebaruan > volume)
        sinyal_baru = rag.hitung_prediksi_ancaman_baru()
        self.assertEqual(
            sinyal_baru,
            "Ransomware",
            f"Sinyal ancaman baru seharusnya Ransomware (novelty menang atas volume 50), didapat: {sinyal_baru}"
        )

        ancaman_dict = rag.ambil_berita_ancaman_baru()
        self.assertTrue(ancaman_dict.get("ada"))
        self.assertEqual(ancaman_dict.get("nama"), "Ransomware")
        self.assertEqual(ancaman_dict.get("jumlah_kasus"), 2)

    # -------------------------------------------------------------------------
    # 3. Zero Articles (Empty DataFrame Stress-Test)
    # -------------------------------------------------------------------------
    def test_zero_articles_empty_dataframe_does_not_crash(self):
        """Dataset kosong melompong (0 berita) tidak boleh memicu unhandled crash/exception."""
        df_empty = pd.DataFrame()
        rag = RAGEngine(df_riwayat=df_empty)

        # Pola serangan
        pola_res = rag.hitung_prediksi_pola_serangan()
        self.assertIsInstance(pola_res, dict)
        self.assertEqual(pola_res["pola"], "Akses Tidak Sah / Pembobolan Akun")
        self.assertEqual(pola_res["jumlah_terkini"], 0)

        # Ancaman baru
        ancaman_res = rag.hitung_prediksi_ancaman_baru()
        self.assertEqual(ancaman_res, "Kondisi Stabil")

        ancaman_dict = rag.ambil_berita_ancaman_baru()
        self.assertFalse(ancaman_dict["ada"])
        self.assertEqual(ancaman_dict["nama"], "Kondisi Stabil")

        # Makro spiking
        makro_res = rag.ambil_data_tren_makro_spiking()
        self.assertIsInstance(makro_res, dict)
        self.assertEqual(makro_res["jumlah_artikel"], 0)

        # Top 3 mikro
        top3 = rag.ambil_top3_insiden_mikro()
        self.assertEqual(top3, [])

    # -------------------------------------------------------------------------
    # 4. Rapid Category Surge (Surge >= 200% with cnt_cur >= 2)
    # -------------------------------------------------------------------------
    def test_rapid_surge_growth_triggers_emerging_threat(self):
        """
        Kategori dengan baseline 1 kasus melonjak menjadi 4 kasus (growth 300% >= 200%)
        dengan kata kunci kebaruan harus memicu sinyal ancaman baru.
        """
        records = [
            # Baseline (2026-09-20): 1 kasus eksploitasi
            self._create_mock_news_row(
                news_id=1,
                kategori_taksonomi="Eksploitasi Kerentanan (Exploit / Zero-Day)",
                judul="Celah lama terdeteksi pada sistem internal",
                ringkasan="Uji celah keamanan pada sistem.",
                tgl="2026-09-20",
                kata_kunci="kerentanan, celah",
            ),
            # Baseline (2026-09-20): 10 kasus DDoS
            *[self._create_mock_news_row(
                news_id=10+i,
                kategori_taksonomi="Distributed Denial of Service (DDoS)",
                judul=f"Serangan DDoS sektor publik baseline {i+1}",
                ringkasan=f"Lalu lintas tinggi membanjiri server {i+1}.",
                tgl="2026-09-20",
                kata_kunci="ddos, lumpuh",
            ) for i in range(10)],
            # Terkini (2026-09-28): 10 kasus DDoS (growth 0%)
            *[self._create_mock_news_row(
                news_id=30+i,
                kategori_taksonomi="Distributed Denial of Service (DDoS)",
                judul=f"Serangan DDoS sektor publik lanjutan {i+1}",
                ringkasan=f"Lalu lintas tinggi berlanjut pada server {i+1}.",
                tgl="2026-09-28",
                kata_kunci="ddos, lumpuh",
            ) for i in range(10)],
            # Terkini (2026-09-28): 4 kasus eksploitasi (growth 300%!)
            *[self._create_mock_news_row(
                news_id=50+i,
                kategori_taksonomi="Eksploitasi Kerentanan (Exploit / Zero-Day)",
                judul=f"Lonjakan kritis eksploitasi zero-day baru {i+1}",
                ringkasan=f"Serangan baru mengeksploitasi kerentanan kritis 0-day secara masif pada server {i+1}.",
                tgl="2026-09-28",
                kata_kunci="zero-day, kritis, lonjakan, baru, exploit",
            ) for i in range(4)],
        ]

        df = pd.DataFrame(records)
        rag = RAGEngine(df_riwayat=df)

        sinyal_baru = rag.hitung_prediksi_ancaman_baru()
        self.assertEqual(
            sinyal_baru,
            "Eksploitasi Kerentanan (Exploit / Zero-Day)",
            f"Lonjakan 300% eksploitasi seharusnya menang sinyal baru, didapat: {sinyal_baru}"
        )


class TestAdversarialSitrepOptionA(unittest.TestCase):
    """
    Adversarial Stress Test: Ensure 100% compliance with Option A in src/analytics/cti_agents.py.
    Assert that zero static fallbacks (T1190, D3-MFA, AC-2, PR.AC-1, fabricated eCSIRT distributions,
    or fabricated default sectors/weapons) are EVER produced under any adversarial or empty state.
    """

    # -------------------------------------------------------------------------
    # 1. Zero-Technique SITREP Stress-Test
    # -------------------------------------------------------------------------
    def test_zero_technique_produces_no_t1190_or_fake_mitre(self):
        """Top-3 insiden tanpa mitre_mapping sama sekali TIDAK boleh menghasilkan T1190."""
        incidents_empty = [
            {"nama_insiden": "Kampanye Tanpa Alur 1", "mitre_mapping": []},
            {"nama_insiden": "Kampanye Tanpa Alur 2", "mitre_mapping": []},
            {"nama_insiden": "Kampanye Tanpa Alur 3", "mitre_mapping": []},
        ]
        output_mitre = _format_rujukan_mitre(incidents_empty)
        self.assertNotIn("T1190", output_mitre)
        self.assertNotIn("Exploit Public-Facing Application", output_mitre)
        self.assertIn("Alur serangan tidak terpetakan pada teknik spesifik ATT&CK", output_mitre)

    def test_tactic_only_stops_at_tactic_without_t1190(self):
        """Top-3 insiden yang hanya memiliki taktik HARUS berhenti di taktik tanpa menyematkan T1190."""
        incidents_tactic = [
            {
                "nama_insiden": "Kampanye Akses Awal",
                "mitre_mapping": [{"tactic": "Initial Access", "id": None, "technique": None}],
            }
        ]
        output_mitre = _format_rujukan_mitre(incidents_tactic)
        self.assertNotIn("T1190", output_mitre)
        self.assertIn("Taktik ATT&CK: **Initial Access** (Teknik spesifik tidak ditentukan)", output_mitre)

    def test_unknown_or_unmapped_technique_produces_no_d3_mfa_fallback(self):
        """Teknik ATT&CK asing (T9999) yang tidak memiliki pemetaan D3FEND TIDAK boleh fallback ke D3-MFA."""
        incidents_unmapped_tech = [
            {
                "nama_insiden": "Kampanye Teknik Tidak Terpetakan",
                "mitre_mapping": [{"id": "T9999", "technique": "Unmapped Technique", "tactic": "Execution"}],
            }
        ]
        d3_out, nist_out = _format_mitigasi_d3fend_nist(incidents_unmapped_tech)
        self.assertNotIn("D3-MFA", d3_out)
        self.assertNotIn("Multi-Factor Authentication", d3_out)
        self.assertIn("Tidak ditemukan pemetaan mitigasi D3FEND spesifik untuk teknik ini", d3_out)

    def test_section_4_rekomendasi_produces_no_ac2_or_prac1_fallback(self):
        """Section 4 rekomendasi tanpa kontrol relevan TIDAK boleh menyuntikkan AC-2 atau PR.AC-1."""
        incidents_no_mitigasi = [
            {
                "nama_insiden": "Kampanye Nihil Mitigasi",
                "mitigasi_ensiklopedia": [],
                "mitre_mapping": [],
            }
        ]
        output_sec4 = _generate_section_4_rekomendasi(incidents_no_mitigasi)
        self.assertNotIn("AC-2", output_sec4)
        self.assertNotIn("PR.AC-1", output_sec4)
        self.assertNotIn("PR.AC", output_sec4)
        self.assertNotIn("D3-MFA", output_sec4)

    # -------------------------------------------------------------------------
    # 2. Empty Database Distribution Stress-Test
    # -------------------------------------------------------------------------
    def test_empty_database_produces_no_fabricated_ecsirt_distribution(self):
        """Database kosong TIDAK boleh memunculkan distribusi eCSIRT fiktif (Akses Tidak Sah / Eksploitasi / Malware)."""
        with patch("src.storage.db._koneksi") as mock_conn:
            mock_cursor = mock_conn.return_value.__enter__.return_value
            mock_cursor.execute.return_value.fetchall.return_value = []

            dist_out = _format_distribusi_ecsirt({})
            self.assertIn("(Belum ada data distribusi taksonomi tervalidasi pada periode ini)", dist_out)
            self.assertNotIn("Akses Tidak Sah / Pembobolan Akun (eCSIRT: intrusions:account-compromise)", dist_out)
            self.assertNotIn("Eksploitasi Kerentanan (Exploit / Zero-Day) (eCSIRT: intrusion-attempts:ids-alert)", dist_out)
            self.assertNotIn("Malware / Infostealer (eCSIRT: malicious-code:malware)", dist_out)

    # -------------------------------------------------------------------------
    # 3. Deterministic Fallback SITREP Stress-Test
    # -------------------------------------------------------------------------
    def test_deterministic_fallback_sitrep_produces_zero_hardcoded_tokens(self):
        """
        Fungsi _buat_fallback_sitrep_deterministik dan jalankan_pipeline_multi_agent (mode instant_rag)
        pada kondisi data kosong / tidak terpetakan TIDAK boleh memuat satupun token terlarang:
        - T1190
        - D3-MFA
        - AC-2
        - PR.AC-1
        - Target Layanan Publik Daerah (fabricated default)
        - Akses Ilegal & Eksploitasi Web (fabricated default)
        """
        sitrep_deterministik = _buat_fallback_sitrep_deterministik(
            data_makro={"nama_pola": "Insiden Siber Terkini", "growth_persen": 0},
            top3_mikro=[],
            ancaman_baru={"ada": False},
        )

        forbidden_tokens = [
            "T1190",
            "D3-MFA",
            "AC-2",
            "PR.AC-1",
            "PR.AC",
            "Target Layanan Publik Daerah",
            "Akses Ilegal & Eksploitasi Web",
            "Gangguan Integritas Sistem",
        ]

        for token in forbidden_tokens:
            self.assertNotIn(
                token,
                sitrep_deterministik,
                f"Token terlarang '{token}' ditemukan pada SITREP deterministik!"
            )

    # -------------------------------------------------------------------------
    # 4. End-to-End Pipeline Multi-Agent Empty State
    # -------------------------------------------------------------------------
    def test_pipeline_multi_agent_instant_rag_clean_of_fallbacks(self):
        """Pipeline multi-agent mode instant_rag 100% bebas dari token hardcode fallback."""
        laporan, meta = jalankan_pipeline_multi_agent(
            data_makro={"nama_pola": "Insiden Umum", "growth_persen": 0, "korpus_artikel": ""},
            top3_mikro=[],
            ancaman_baru={"ada": False},
            mode="instant_rag",
        )

        self.assertEqual(meta.get("mode"), "instant_rag")
        for token in ["T1190", "D3-MFA", "AC-2", "PR.AC-1"]:
            self.assertNotIn(
                token,
                laporan,
                f"Pipeline multi-agent menghasilkan token terlarang '{token}'!"
            )


if __name__ == "__main__":
    unittest.main()
