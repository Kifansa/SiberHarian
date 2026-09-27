import time
import unittest
from unittest.mock import MagicMock, patch

from src.classifier.relevance_classifier import _ekstrak_json_batch, klasifikasi_batch_5
from src.utils.llm_adapter import APIKeyPool, GeminiRateLimiter


class TestAPIKeyPool(unittest.TestCase):
    def test_key_parsing(self):
        pool = APIKeyPool()
        pool.set_keys("key1, key2,key3\nkey4")
        self.assertEqual(pool.total_keys(), 4)
        self.assertEqual(pool.get_active_key(), "key1")

    def test_rate_limited_rotation(self):
        pool = APIKeyPool()
        pool.set_keys("key_primary, key_secondary")
        self.assertEqual(pool.get_active_key(), "key_primary")

        # Mark primary key as rate-limited for 10 seconds
        next_key = pool.mark_rate_limited("key_primary", cooldown_seconds=10.0)
        self.assertEqual(next_key, "key_secondary")
        self.assertEqual(pool.get_active_key(), "key_secondary")


class TestGeminiRateLimiter(unittest.TestCase):
    def test_rpm_limit_classification(self):
        limiter = GeminiRateLimiter()
        self.assertEqual(limiter._get_model_rpm_limit("gemini-3.5-flash-lite"), 12.0)
        self.assertEqual(limiter._get_model_rpm_limit("gemini-3.7-flash"), 4.0)
        self.assertEqual(limiter._get_model_rpm_limit("gemini-embedding-001"), 80.0)

    def test_pacing_calculation(self):
        limiter = GeminiRateLimiter()
        start = time.time()
        # Fast successive calls on a 4 RPM model should pace appropriately
        limiter._last_call["mock-flash"] = start - 1.0  # Called 1s ago
        # Minimum interval for 4 RPM is 15s. Should not raise errors.
        self.assertTrue(limiter._get_model_rpm_limit("mock-flash") == 4.0)


class TestBatchClassifier(unittest.TestCase):
    def test_json_extraction_valid(self):
        sample_response = """
        Berikut hasil klasifikasi:
        ```json
        [
            {"id": "ART-1", "kategori": "insiden_spesifik"},
            {"id": "ART-2", "kategori": "tidak_relevan"},
            {"id": "ART-3", "kategori": "analisis_relevan"}
        ]
        ```
        """
        extracted = _ekstrak_json_batch(sample_response)
        self.assertIsNotNone(extracted)
        self.assertEqual(len(extracted), 3)
        self.assertEqual(extracted[0]["id"], "ART-1")
        self.assertEqual(extracted[0]["kategori"], "insiden_spesifik")

    def test_json_extraction_fallback_regex(self):
        sample_response = """
        ART-1: insiden_spesifik
        ART-2: tidak_relevan
        """
        extracted = _ekstrak_json_batch(sample_response)
        self.assertIsNotNone(extracted)
        self.assertEqual(len(extracted), 2)
        self.assertEqual(extracted[0]["kategori"], "insiden_spesifik")

    @patch("src.utils.llm_adapter.GeminiLLMAdapter.chat")
    def test_batch_classification_fallback_on_empty(self, mock_chat):
        # Respons rusak yang memicu fallback ke pemrosesan tunggal
        mock_chat.side_effect = [
            "Maaf saya tidak bisa menjawab format json.",  # respons batch rusak
            "kategori: insiden_spesifik",  # fallback artikel 1
            "kategori: tidak_relevan",  # fallback artikel 2
        ]
        docs = [
            {"judul": "Web Diretas", "teks_asli": "Insiden peretasan"},
            {"judul": "Ponsel Baru", "teks_asli": "Spesifikasi ponsel"},
        ]
        labels = klasifikasi_batch_5(docs)
        self.assertEqual(len(labels), 2)
        self.assertEqual(labels[0], "insiden_spesifik")
        self.assertEqual(labels[1], "tidak_relevan")


if __name__ == "__main__":
    unittest.main()
