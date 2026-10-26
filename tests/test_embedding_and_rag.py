import os
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
import yaml

from src.utils.llm_adapter import GeminiLLMAdapter, DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_FALLBACK_MODELS
from src.utils.settings_manager import SettingsManager
from src.analytics.rag_engine import RAGEngine
import src.analytics.cti_agents as cti_agents


class TestEmbeddingFallbackAndRAG(unittest.TestCase):
    def setUp(self):
        from src.utils.llm_adapter import _rate_limiter, _key_pool
        with _rate_limiter._lock:
            _rate_limiter._history.clear()
            _rate_limiter._last_call.clear()
        with _key_pool._lock:
            _key_pool._cooldowns.clear()

    def tearDown(self):
        from src.utils.llm_adapter import _rate_limiter, _key_pool
        with _rate_limiter._lock:
            _rate_limiter._history.clear()
            _rate_limiter._last_call.clear()
        with _key_pool._lock:
            _key_pool._cooldowns.clear()

    def test_legacy_strings_eradicated(self):
        """Pastikan tidak ada teks 'Llama 3.2' tersisa di cti_agents.py dan config.yaml."""
        # 1. Cek file cti_agents.py
        with open("src/analytics/cti_agents.py", "r", encoding="utf-8") as f:
            cti_content = f.read()
        self.assertNotIn("Llama 3.2", cti_content)
        self.assertIn("Google Gemini Modular LLM", cti_content)

        # 2. Cek config.yaml
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            cfg_content = f.read()
        self.assertNotIn("Llama 3.2", cfg_content)
        self.assertIn("Google Gemini Modular LLM", cfg_content)

    def test_config_yaml_embedding_fallback(self):
        """Pastikan config.yaml memuat embedding_model dan embedding_model_fallback."""
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        gemini_cfg = cfg.get("gemini", {})
        self.assertEqual(gemini_cfg.get("embedding_model"), "gemini-embedding-001")
        self.assertIn("embedding_model_fallback", gemini_cfg)
        fallbacks = gemini_cfg.get("embedding_model_fallback")
        self.assertIsInstance(fallbacks, list)
        self.assertIn("text-embedding-004", fallbacks)

    def test_settings_manager_embedding_config(self):
        """Pastikan SettingsManager mengembalikan embedding_model dan fallback dengan benar."""
        cfg = SettingsManager.get_gemini_config()
        self.assertEqual(cfg.get("embedding_model"), "gemini-embedding-001")
        self.assertIn("embedding_model_fallback", cfg)
        self.assertTrue(len(cfg.get("embedding_model_fallback")) >= 1)

    def test_get_embedding_chain(self):
        """Pastikan rantai model embedding terbentuk secara berurutan dan terdeduplikasi."""
        chain = GeminiLLMAdapter._get_embedding_chain()
        self.assertEqual(chain[0], "gemini-embedding-001")
        self.assertIn("gemini-embedding-exp-03-07", chain)
        self.assertIn("text-embedding-004", chain)

        # Custom requested model should be at index 0
        custom_chain = GeminiLLMAdapter._get_embedding_chain("custom-model-01")
        self.assertEqual(custom_chain[0], "custom-model-01")
        self.assertIn("gemini-embedding-001", custom_chain)

    @patch("src.utils.llm_adapter.genai.embed_content")
    def test_embed_text_primary_success(self, mock_embed):
        """Test embed_text sukses menggunakan model utama."""
        mock_embed.return_value = {"embedding": [0.1, 0.2, 0.3]}
        res = GeminiLLMAdapter.embed_text("test cyber news")
        self.assertEqual(res, [0.1, 0.2, 0.3])
        # Pastikan dipanggil dengan model utama
        self.assertEqual(mock_embed.call_args[1]["model"], "models/gemini-embedding-001")

    @patch("src.utils.llm_adapter.genai.embed_content")
    def test_embed_text_fallback_to_second_model(self, mock_embed):
        """Test embed_text fallback ke model kedua jika model utama error."""
        call_models = []

        def side_effect(*args, **kwargs):
            m = kwargs.get("model", "")
            call_models.append(m)
            if "gemini-embedding-001" in m:
                raise RuntimeError("Primary model quota / unsupported error")
            return {"embedding": [0.4, 0.5, 0.6]}

        mock_embed.side_effect = side_effect
        res = GeminiLLMAdapter.embed_text("sample incident")
        self.assertEqual(res, [0.4, 0.5, 0.6])
        self.assertTrue(any("gemini-embedding-001" in m for m in call_models))
        self.assertTrue(any("gemini-embedding-exp-03-07" in m or "text-embedding-004" in m for m in call_models))

    @patch("src.utils.llm_adapter.genai.embed_content")
    def test_embed_text_all_models_fail(self, mock_embed):
        """Test embed_text jika seluruh model dalam rantai gagal."""
        mock_embed.side_effect = RuntimeError("All models down")
        res = GeminiLLMAdapter.embed_text("critical breach")
        self.assertEqual(res, [])

    def test_embed_text_empty_input(self):
        """Test embed_text dengan input kosong langsung return []."""
        self.assertEqual(GeminiLLMAdapter.embed_text(""), [])
        self.assertEqual(GeminiLLMAdapter.embed_text("   "), [])
        self.assertEqual(GeminiLLMAdapter.embed_text(None), [])

    @patch("src.utils.llm_adapter.genai.embed_content")
    def test_embed_documents_fallback(self, mock_embed):
        """Test embed_documents fallback ke model berikutnya jika model utama gagal."""
        call_models = []

        def side_effect(*args, **kwargs):
            m = kwargs.get("model", "")
            call_models.append(m)
            if "gemini-embedding-001" in m:
                raise RuntimeError("Batch primary failed")
            return {"embedding": [[0.1, 0.2], [0.3, 0.4]]}

        mock_embed.side_effect = side_effect
        docs = ["artikel satu", "artikel dua"]
        res = GeminiLLMAdapter.embed_documents(docs, batch_size=2)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0], [0.1, 0.2])
        self.assertEqual(res[1], [0.3, 0.4])

    def test_rag_engine_double_loop_removed(self):
        """
        Pastikan perhitungan skor pada retrieve_berita_context tidak lagi memiliki loop ganda.
        Sebelumnya vector_set dicek 2x:
          score += w_vector
          score += 1
        Sekarang hanya dihitung 1x:
          score += w_vector
        """
        sample_df = pd.DataFrame([{
            "id": 1,
            "kategori": "berita",
            "kategori_relevansi": "insiden_spesifik",
            "sumber": "CNN",
            "judul": "Insiden kebocoran data di instansi",
            "ringkasan_atau_narasi": "Pelaku ransomware lockbit mencuri data rahasia",
            "kata_kunci": "ransomware, kebocoran",
            "tanggal_publikasi": "2026-10-20 10:00:00",
            "status_relevansi": "relevan_insiden",
        }])

        rag = RAGEngine(df_riwayat=sample_df)

        # Keyword match saja
        ctx_kw = rag.retrieve_berita_context(
            top_keywords=["ransomware"],
            top_vectors=[],
            limit=5
        )
        self.assertIn("Insiden kebocoran data", ctx_kw)

        # Vector term match saja
        ctx_vec = rag.retrieve_berita_context(
            top_keywords=[],
            top_vectors=["lockbit"],
            limit=5
        )
        self.assertIn("Insiden kebocoran data", ctx_vec)


if __name__ == "__main__":
    unittest.main()
