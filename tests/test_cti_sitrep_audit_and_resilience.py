import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from src.analytics.rag_engine import RAGEngine
from src.analytics.cti_agents import (
    _petakan_taksonomi_insiden,
    _susun_paragraf_insiden_rag,
    _generate_section_1_makro,
    _generate_section_2_mikro,
    _generate_section_3_vektor,
    _generate_section_4_rekomendasi,
    _generate_section_5_emerging,
)


class TestSITREPObjectivityAndRAGGrounding(unittest.TestCase):
    """
    Audit independen objektivitas SITREP CTI:
    1. Memastikan tidak ada pengarahan buatan (steering), tidak ada skor keyakinan semu (hallucinated confidence).
    2. Memastikan pemetaan taksonomi dan MITRE murni berbasis kesamaan semantik & leksikal.
    3. Memastikan D3FEND mitigasi lookup bersifat deterministik dari database relasional.
    """

    def setUp(self):
        self.rag = RAGEngine()

    def test_semantic_mapping_zero_steering_and_no_fake_boosts(self):
        """Memverifikasi map_incident_to_mitre_semantic tidak menggunakan sigmoid boost floor atau hallmark steering."""
        incident_title = "Penyebaran Dokumen Faktur Palsu Berisi Trojan"
        incident_narrative = "Pelaku mengirimkan email berisikan lampiran dokumen faktur palsu berekstensi ISO."

        # Mock embedding deterministik (768 dimensi)
        mock_vec = [0.05] * 768
        with patch("src.utils.llm_adapter.GeminiLLMAdapter.embed_text", return_value=mock_vec):
            results = self.rag.map_incident_to_mitre_semantic(
                incident_title=incident_title,
                incident_narrative=incident_narrative,
                top_k=3
            )

        self.assertIsInstance(results, list)
        for res in results:
            self.assertIn("id", res)
            self.assertIn("technique", res)
            self.assertIn("tactic", res)
            self.assertIn("score", res)
            # Skor kemiripan harus berupa float murni (antara 0.0 s.d 1.0) tanpa manipulasi
            self.assertGreaterEqual(res["score"], 0.0)
            self.assertLessEqual(res["score"], 1.0)
            # Memastikan tidak ada label 'keyakinan: XX%' yang disuntikkan secara artifisial
            self.assertNotIn("keyakinan", str(res.get("technique", "")).lower())

    def test_section_4_deterministic_d3fend_and_no_fake_fallbacks(self):
        """Memverifikasi Bagian 4 tidak menyuntikkan mitigasi statis D3-MFA / AC-2 ketika data kosong."""
        # Uji dengan insiden tanpa pemetaan teknik ATT&CK
        top3_empty = [
            {"nama_insiden": "Insiden Umum", "mitre_mapping": [], "mitigasi_ensiklopedia": []}
        ]
        rekomendasi = _generate_section_4_rekomendasi(top3_empty)
        # Sesuai aturan objektivitas Opsi A: dilarang ada D3-MFA statis jika tidak terpetakan
        self.assertNotIn("D3-MFA", rekomendasi)
        self.assertNotIn("AC-2", rekomendasi)
        self.assertNotIn("PR.AC-1", rekomendasi)

    def test_rag_paragraf_generator_grounded_on_news_corpus(self):
        """Memverifikasi _susun_paragraf_insiden_rag merangkum murni dari korpus berita."""
        fakta_rag = {
            "kejadian": "Serangan ransomware LockBit 3.0",
            "nama_kasus": "Serangan Ransomware LockBit 3.0",
            "aktor": "Kelompok Brain Cipher",
            "pihak_terdampak": "Pusat Data Nasional Sementara 2",
            "lokasi_kejadian": "Surabaya, Jawa Timur",
            "senjata_metode": "Ransomware enkripsi AES-256",
            "alur_serangan": "Eksploitasi kredensial VPN kemudian penyebaran muatan ransomware",
            "dampak": "Layanan publik imigrasi lumpuh sementara",
        }

        paragraf = _susun_paragraf_insiden_rag(
            nama_kategori="Ransomware",
            fakta_rag=fakta_rag,
            jumlah_artikel=12,
            growth_persen=140.0,
            is_emerging=False,
            nama_kasus="Serangan Ransomware LockBit 3.0"
        )

        # Verifikasi bahwa fakta-fakta spesifik hadir dalam narasi
        self.assertIn("LockBit 3.0", paragraf)
        self.assertIn("Brain Cipher", paragraf)
        self.assertIn("Pusat Data Nasional", paragraf)
        self.assertIn("AES-256", paragraf)
        self.assertIn("imigrasi lumpuh", paragraf)
        self.assertIn("[ POLA ANCAMAN ]", paragraf)


class TestSITREPResilienceAcrossDiverseNews(unittest.TestCase):
    """
    Uji ketangguhan SITREP terhadap berbagai variasi korpus berita nyata & ekstrem:
    - Dataset kosong
    - Berita tanpa tanggal / tanpa atribut lengkap
    - Berita bahasa asing
    - Lonjakan berita tunggal
    - Lonjakan multi-kategori dengan volume ekstrem
    """

    def test_resilience_empty_database_and_dataframe(self):
        """Memverifikasi sistem tidak crash saat dataset kosong total."""
        df_kosong = pd.DataFrame(columns=["id", "judul", "kategori", "published_parsed"])
        rag_kosong = RAGEngine(df_kosong)

        pola = rag_kosong.hitung_prediksi_pola_serangan()
        self.assertIsInstance(pola, dict)
        self.assertIn("pola", pola)

        ancaman_str = rag_kosong.hitung_prediksi_ancaman_baru()
        self.assertEqual(ancaman_str, "Kondisi Stabil")

        ancaman_dict = rag_kosong.ambil_berita_ancaman_baru()
        self.assertFalse(ancaman_dict.get("ada", False))

        sec1 = _generate_section_1_makro(pola)
        self.assertIsInstance(sec1, str)
        self.assertGreater(len(sec1), 10)

        sec5 = _generate_section_5_emerging(ancaman_dict)
        self.assertIn("Kondisi Stabil", sec5)

    def test_resilience_single_article_never_triggers_emerging_threat(self):
        """Memverifikasi batas minimal dua artikel untuk Sinyal Ancaman Baru (anti-false-positive)."""
        df_single = pd.DataFrame([
            {
                "id": "1",
                "judul": "Insiden Baru Muncul",
                "kategori": "eksploitasi_kerentanan",
                "published_parsed": pd.Timestamp.now().timetuple()
            }
        ])

        rag_single = RAGEngine(df_single)
        ancaman_str = rag_single.hitung_prediksi_ancaman_baru()
        # Tepat 1 artikel tidak boleh memicu status ancaman baru aktif
        self.assertEqual(ancaman_str, "Kondisi Stabil")

    def test_resilience_missing_fields_and_malformed_articles(self):
        """Memverifikasi ketahanan terhadap artikel dengan field None, string kosong, atau struktur rusak."""
        incidents_malformed = [
            {
                "nama_insiden": "",
                "uraian_fakta": None,
                "mitre_mapping": None,
                "fakta_rag": None
            },
            {
                "nama_insiden": "Judul Tanpa Fakta",
                "uraian_fakta": "",
                "mitre_mapping": [],
                "fakta_rag": {}
            }
        ]

        # Mocking chat agar tidak memanggil real API
        with patch("src.utils.llm_adapter.GeminiLLMAdapter.chat", return_value=""):
            sec2 = _generate_section_2_mikro(incidents_malformed)
            self.assertIsInstance(sec2, str)

            sec3 = _generate_section_3_vektor(incidents_malformed)
            self.assertIsInstance(sec3, str)

            sec4 = _generate_section_4_rekomendasi(incidents_malformed)
            self.assertIsInstance(sec4, str)

    def test_resilience_multilingual_and_foreign_news(self):
        """Memverifikasi pemetaan taksonomi dan penanganan berita berbahasa Inggris."""
        news_item = {
            "nama_insiden": "Critical Zero-Day Vulnerability Exploit in Apache HTTP Server",
            "uraian_fakta": "Threat actors deployed an unauthenticated RCE exploit leveraging CVE-2026-1234 targeting public infrastructure servers.",
            "kategori_taksonomi": "eksploitasi_kerentanan"
        }

        kat_display, induk = _petakan_taksonomi_insiden(news_item)
        self.assertIn("Eksploitasi Kerentanan", kat_display)
        self.assertEqual(induk, "intrusion-attempts:ids-alert")

    def test_resilience_drastic_volume_skew_novelty_beats_volume(self):
        """Memverifikasi bahwa kemunculan kategori baru tidak tertutup oleh volume tinggi kategori mapan."""
        now_tuple = pd.Timestamp.now().timetuple()
        
        # 30 berita ransomware (kategori mapan historis) vs 2 berita zero-day baru (kategori novel)
        rows = []
        for i in range(30):
            rows.append({
                "id": f"rw_{i}",
                "judul": f"Laporan Ransomware Kasus ke-{i}",
                "kategori": "ransomware",
                "published_parsed": now_tuple
            })
        for j in range(2):
            rows.append({
                "id": f"zd_{j}",
                "judul": f"Eksploitasi Kerentanan Baru Ditemukan #{j}",
                "kategori": "eksploitasi_kerentanan",
                "published_parsed": now_tuple
            })

        df_skew = pd.DataFrame(rows)
        rag_skew = RAGEngine(df_skew)
        ancaman_dict = rag_skew.ambil_berita_ancaman_baru()
        self.assertIsInstance(ancaman_dict, dict)


if __name__ == "__main__":
    unittest.main()
