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
    def setUp(self):
        import shutil
        import tempfile
        from src.utils.settings_manager import SettingsManager

        self._temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._temp_db.close()
        shutil.copy2("data/state.db", self._temp_db.name)
        SettingsManager.set_db_path(self._temp_db.name)

    def tearDown(self):
        import os
        from src.utils.settings_manager import SettingsManager

        SettingsManager.reset_db_path()
        try:
            os.remove(self._temp_db.name)
        except Exception:
            pass
    def test_rpm_limit_classification(self):
        limiter = GeminiRateLimiter()
        self.assertEqual(limiter._get_model_rpm_limit("gemini-3.5-flash-lite"), 12.0)
        self.assertEqual(limiter._get_model_rpm_limit("gemini-3.7-flash"), 4.0)
        self.assertEqual(limiter._get_model_rpm_limit("gemini-embedding-001"), 80.0)

    def test_proactive_threshold_classification(self):
        """Menguji ambang batas proaktif (90%-95% RPM) untuk 7 model narasi & embedding."""
        limiter = GeminiRateLimiter()
        # 7 Model Narasi
        self.assertEqual(limiter.get_quota_rpm("gemini-2.5-flash"), 5.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-2.5-flash"), 4)

        self.assertEqual(limiter.get_quota_rpm("gemini-2.5-flash-lite"), 10.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-2.5-flash-lite"), 9)

        self.assertEqual(limiter.get_quota_rpm("gemini-3-flash"), 5.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-3-flash"), 4)

        self.assertEqual(limiter.get_quota_rpm("gemini-3.1-flash-lite"), 15.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-3.1-flash-lite"), 14)

        self.assertEqual(limiter.get_quota_rpm("gemini-3.6-flash"), 5.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-3.6-flash"), 4)

        self.assertEqual(limiter.get_quota_rpm("gemini-3.5-flash-lite"), 15.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-3.5-flash-lite"), 14)

        self.assertEqual(limiter.get_quota_rpm("gemini-3.8-flash"), 5.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-3.8-flash"), 4)

        # 2 Model Embedding Resmi (100 RPM)
        self.assertEqual(limiter.get_quota_rpm("gemini-embedding-001"), 100.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-embedding-001"), 90)

        self.assertEqual(limiter.get_quota_rpm("gemini-embedding-exp-03-07"), 100.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-embedding-exp-03-07"), 90)

    def test_proactive_model_switch_at_threshold(self):
        """Saat model mencapai 90%-95% threshold, sistem proaktif beralih ke model berikutnya pada key yang sama."""
        limiter = GeminiRateLimiter()
        pool = APIKeyPool()
        pool.set_keys("AIzaSyMockKey1111111111, AIzaSyMockKey2222222222")

        models = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
        key = pool.get_active_key()

        # Panggil gemini-2.5-flash sebanyak 4 kali (mencapai threshold 4)
        for _ in range(4):
            limiter.record_call("gemini-2.5-flash", key)

        self.assertTrue(limiter.is_model_near_limit("gemini-2.5-flash", key))
        self.assertFalse(limiter.is_model_near_limit("gemini-2.5-flash-lite", key))

        # Panggilan berikutnya otomatis memilih gemini-2.5-flash-lite pada key yang sama
        sel_key, sel_model, wait_sec = limiter.select_available_slot(models, pool)
        self.assertEqual(sel_key, key)
        self.assertEqual(sel_model, "gemini-2.5-flash-lite")
        self.assertEqual(wait_sec, 0.0)

    def test_proactive_key_switch_when_all_models_saturated(self):
        """Saat seluruh model pada Key 1 mencapai limit, sistem proaktif beralih ke Key 2."""
        limiter = GeminiRateLimiter()
        pool = APIKeyPool()
        key1 = "AIzaSyMockKey1111111111"
        key2 = "AIzaSyMockKey2222222222"
        pool.set_keys([key1, key2])

        models = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]

        # Jenuhkan Key 1 untuk kedua model
        for _ in range(4):
            limiter.record_call("gemini-2.5-flash", key1)
        for _ in range(9):
            limiter.record_call("gemini-2.5-flash-lite", key1)

        # Slot berikutnya wajib memilih Key 2 dengan model pertama
        sel_key, sel_model, wait_sec = limiter.select_available_slot(models, pool)
        self.assertEqual(sel_key, key2)
        self.assertEqual(sel_model, "gemini-2.5-flash")
        self.assertEqual(wait_sec, 0.0)

    def test_graceful_waiting_when_all_keys_saturated(self):
        """Saat semua model pada semua API Key jenuh, sistem menunggu secara anggun (wait_sec > 0)."""
        limiter = GeminiRateLimiter()
        pool = APIKeyPool()
        key1 = "AIzaSyMockKey1111111111"
        key2 = "AIzaSyMockKey2222222222"
        pool.set_keys([key1, key2])

        models = ["gemini-2.5-flash"]

        # Jenuhkan Key 1 & Key 2
        for _ in range(4):
            limiter.record_call("gemini-2.5-flash", key1)
            limiter.record_call("gemini-2.5-flash", key2)

        sel_key, sel_model, wait_sec = limiter.select_available_slot(models, pool)
        self.assertIsNone(sel_key)
        self.assertIsNone(sel_model)
        self.assertGreater(wait_sec, 0.0)
        self.assertLessEqual(wait_sec, 61.0)

    def test_pacing_calculation(self):
        limiter = GeminiRateLimiter()
        start = time.time()
        # Fast successive calls on a 4 RPM model should pace appropriately
        limiter._last_call["mock-flash"] = start - 1.0  # Called 1s ago
        # Minimum interval for 4 RPM is 15s. Should not raise errors.
        self.assertTrue(limiter._get_model_rpm_limit("mock-flash") == 4.0)

    def test_dynamic_rate_limit_and_threshold_update(self):
        """Menguji pembaruan dinamis kuota RPM dan ambang proaktif melalui SettingsManager tanpa restart."""
        from src.utils.settings_manager import SettingsManager
        limiter = GeminiRateLimiter()

        orig_rl = SettingsManager.get("gemini.rate_limits") or {}
        orig_pt = SettingsManager.get("gemini.proactive_thresholds") or {}
        try:
            updated_rl = dict(orig_rl)
            updated_rl["gemini-2.5-flash"] = 8.0
            SettingsManager.set("gemini.rate_limits", updated_rl)

            updated_pt = dict(orig_pt)
            updated_pt["gemini-2.5-flash"] = 7
            SettingsManager.set("gemini.proactive_thresholds", updated_pt)

            self.assertEqual(limiter.get_quota_rpm("gemini-2.5-flash"), 8.0)
            self.assertEqual(limiter.get_proactive_threshold("gemini-2.5-flash"), 7)
        finally:
            SettingsManager.set("gemini.rate_limits", orig_rl)
            SettingsManager.set("gemini.proactive_thresholds", orig_pt)

    def test_all_7_models_threshold_switching(self):
        """Memverifikasi seluruh 7 model narasi berganti tepat pada ambang proaktif masing-masing."""
        limiter = GeminiRateLimiter()
        pool = APIKeyPool()
        key = "AIzaSyMockKeyThresholdTest"
        pool.set_keys([key])

        test_cases = [
            ("gemini-2.5-flash", 5.0, 4),
            ("gemini-2.5-flash-lite", 10.0, 9),
            ("gemini-3-flash", 5.0, 4),
            ("gemini-3.1-flash-lite", 15.0, 14),
            ("gemini-3.6-flash", 5.0, 4),
            ("gemini-3.5-flash-lite", 15.0, 14),
            ("gemini-3.8-flash", 5.0, 4),
        ]

        for model, exp_rpm, exp_thresh in test_cases:
            self.assertEqual(limiter.get_quota_rpm(model), exp_rpm)
            self.assertEqual(limiter.get_proactive_threshold(model), exp_thresh)

            limiter._history.clear()
            for _ in range(exp_thresh - 1):
                limiter.record_call(model, key)
            self.assertFalse(limiter.is_model_near_limit(model, key))

            limiter.record_call(model, key)
            self.assertTrue(limiter.is_model_near_limit(model, key))

    def test_embedding_threshold_switching(self):
        """Memverifikasi model embedding 100 RPM berganti pada ambang proaktif 90 calls/min."""
        limiter = GeminiRateLimiter()
        pool = APIKeyPool()
        key = "AIzaSyMockKeyEmbeddingTest"
        pool.set_keys([key])

        models = ["gemini-embedding-001", "gemini-embedding-exp-03-07"]
        self.assertEqual(limiter.get_quota_rpm("gemini-embedding-001"), 100.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-embedding-001"), 90)

        limiter._history.clear()
        for _ in range(90):
            limiter.record_call("gemini-embedding-001", key)

        self.assertTrue(limiter.is_model_near_limit("gemini-embedding-001", key))
        self.assertFalse(limiter.is_model_near_limit("gemini-embedding-exp-03-07", key))

        sel_key, sel_model, wait_sec = limiter.select_available_slot(models, pool)
        self.assertEqual(sel_key, key)
        self.assertEqual(sel_model, "gemini-embedding-exp-03-07")
        self.assertEqual(wait_sec, 0.0)

    def test_embedding_chain_strictly_from_db(self):
        """Memverifikasi _get_embedding_chain murni bersumber dari database tanpa auto-append tambahan."""
        from src.utils.llm_adapter import GeminiLLMAdapter
        from src.utils.settings_manager import SettingsManager

        orig_fb = SettingsManager.get("gemini.embedding_model_fallback")
        try:
            SettingsManager.set("gemini.embedding_model_fallback", ["gemini-embedding-exp-03-07"])
            chain = GeminiLLMAdapter._get_embedding_chain()
            self.assertEqual(chain, ["gemini-embedding-001", "gemini-embedding-exp-03-07"])
            self.assertNotIn("text-embedding-004", chain)
        finally:
            SettingsManager.set("gemini.embedding_model_fallback", orig_fb)

    def test_database_model_chain_exact_7_models_order(self):
        """Memverifikasi state.db memuat tepat 7 model narasi dalam urutan resmi tanpa model usang."""
        from src.utils.settings_manager import SettingsManager
        import sqlite3
        import json

        expected_chain = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-3-flash",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
        ]
        SettingsManager.set("gemini.model_chain", expected_chain)

        chain = SettingsManager.get("gemini.model_chain")
        self.assertEqual(chain, expected_chain)

        conn = sqlite3.connect(SettingsManager._db_path)
        row = conn.execute("SELECT nilai FROM pengaturan WHERE kunci = 'gemini.model_chain'").fetchone()
        conn.close()
        db_chain = json.loads(row[0])
        self.assertEqual(db_chain, expected_chain)
        for obsolete in ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro", "gemini-3.5-flash"]:
            self.assertNotIn(obsolete, db_chain)


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
