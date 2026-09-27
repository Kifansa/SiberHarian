import unittest
from unittest.mock import patch
import pandas as pd

from src.dedup.deduplicator import deteksi_duplikat_hybrid
from src.classifier.relevance_classifier import filter_artikel_relevan
from src.summarizer.llm_summarizer import ringkas_semua_berita


class TestEndToEndFlow(unittest.TestCase):
    def test_dedup_and_relevance_flow(self):
        df = pd.DataFrame([
            {
                "judul": "Serangan Ransomware Terdeteksi di Instansi X",
                "teks_asli": "Terjadi kebocoran data akibat serangan ransomware di server instansi X.",
                "sumber": "CNN",
            },
            {
                "judul": "Serangan Ransomware Terdeteksi di Instansi X",
                "teks_asli": "Ransomware melumpuhkan server instansi X.",
                "sumber": "Detik",
            },
            {
                "judul": "Tips Memilih Smartphone Terbaik Tahun 2026",
                "teks_asli": "Berikut panduan memilih smartphone untuk kebutuhan harian.",
                "sumber": "Tempo",
            },
        ])

        with patch("src.utils.embedding_adapter.GeminiEmbeddingAdapter.embed_batch") as mock_emb:
            mock_emb.return_value = [[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]]
            dedup_df = deteksi_duplikat_hybrid(df)
            self.assertEqual(len(dedup_df), 2)
            mock_emb.assert_called_once()

        with patch("src.classifier.relevance_classifier.GeminiLLMAdapter.chat") as mock_chat:
            mock_chat.return_value = (
                '[{"id": "ART-1", "kategori": "insiden_spesifik"}, '
                '{"id": "ART-2", "kategori": "tidak_relevan"}]'
            )
            rel_df = filter_artikel_relevan(dedup_df)
            self.assertEqual(len(rel_df), 1)
            self.assertEqual(rel_df.iloc[0]["kategori_relevansi"], "insiden_spesifik")

        with patch("src.summarizer.llm_summarizer.GeminiLLMAdapter.chat") as mock_sum_chat:
            mock_sum_chat.return_value = "Server instansi X mengalami serangan ransomware yang menyebabkan kebocoran data."
            res_df = ringkas_semua_berita(rel_df)
            self.assertIn("ringkasan", res_df.columns)
            self.assertTrue(len(res_df.iloc[0]["ringkasan"]) > 10)


if __name__ == "__main__":
    unittest.main()
