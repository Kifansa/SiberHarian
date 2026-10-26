import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import tests.conftest  # Apply Windows sandbox IOCP pipe patch and GenAI mock

from src.utils.llm_adapter import (
    APIKeyPool,
    DEFAULT_MODEL_CHAIN,
    GeminiLLMAdapter,
    GeminiRateLimiter,
)
from src.utils.settings_manager import SettingsManager


class TestAdversarialReviewerVerification(unittest.TestCase):
    def setUp(self):
        # Database isolation using temporary database
        self._temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._temp_db.close()
        shutil.copy2("data/state.db", self._temp_db.name)
        SettingsManager.set_db_path(self._temp_db.name)

    def tearDown(self):
        SettingsManager.reset_db_path()
        try:
            os.remove(self._temp_db.name)
        except Exception:
            pass

    def test_r1_official_7_models_chain_and_order(self):
        """Memverifikasi rantai 7 model narasi resmi terdaftar dalam urutan presisi."""
        cfg = SettingsManager.get_gemini_config()
        chain = cfg.get("model_chain")
        expected = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-3-flash",
            "gemini-3.1-flash-lite",
            "gemini-3.6-flash",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
        ]
        self.assertEqual(chain, expected)
        self.assertEqual(len(chain), 7)

    def test_r1_obsolete_models_completely_purged(self):
        """Memverifikasi seluruh model usang tidak ada dalam rantai narasi atau kamus limit."""
        obsolete_models = [
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-3.5-flash",
            "embedding-001",
        ]
        cfg = SettingsManager.get_gemini_config()
        chain = cfg.get("model_chain")
        for obs in obsolete_models:
            self.assertNotIn(obs, chain)
            self.assertNotIn(obs, cfg.get("rate_limits", {}))
            self.assertNotIn(obs, cfg.get("proactive_thresholds", {}))

    def test_r1_rate_limits_and_proactive_thresholds_values(self):
        """Memverifikasi batas RPM dan ambang proaktif seluruh 7 model narasi (5->4, 10->9, 15->14)."""
        limiter = GeminiRateLimiter()
        expected_quotas = {
            "gemini-2.5-flash": (5.0, 4),
            "gemini-2.5-flash-lite": (10.0, 9),
            "gemini-3-flash": (5.0, 4),
            "gemini-3.1-flash-lite": (15.0, 14),
            "gemini-3.6-flash": (5.0, 4),
            "gemini-3.5-flash-lite": (15.0, 14),
            "gemini-3.8-flash": (5.0, 4),
        }
        for model, (exp_rpm, exp_thresh) in expected_quotas.items():
            self.assertEqual(limiter.get_quota_rpm(model), exp_rpm, f"RPM mismatch for {model}")
            self.assertEqual(limiter.get_proactive_threshold(model), exp_thresh, f"Threshold mismatch for {model}")

    def test_r2_embedding_models_and_thresholds(self):
        """Memverifikasi 2 model embedding resmi berkuota 100 RPM dengan ambang proaktif 90."""
        limiter = GeminiRateLimiter()
        for emb_model in ["gemini-embedding-001", "gemini-embedding-exp-03-07"]:
            self.assertEqual(limiter.get_quota_rpm(emb_model), 100.0)
            self.assertEqual(limiter.get_proactive_threshold(emb_model), 90)

    def test_r2_embedding_chain_strictly_from_db(self):
        """Memverifikasi _get_embedding_chain tidak menyisipkan model hardcoded tambahan jika diset via DB."""
        SettingsManager.set("gemini.embedding_model", "gemini-embedding-001")
        SettingsManager.set("gemini.embedding_model_fallback", ["gemini-embedding-exp-03-07"])
        chain = GeminiLLMAdapter._get_embedding_chain()
        self.assertEqual(chain, ["gemini-embedding-001", "gemini-embedding-exp-03-07"])
        self.assertNotIn("text-embedding-004", chain)
        self.assertNotIn("embedding-001", chain)

    def test_r1_dynamic_rate_limit_update(self):
        """Memverifikasi perubahan batas kuota via DB langsung terbaca tanpa restart."""
        limiter = GeminiRateLimiter()
        SettingsManager.set("gemini.rate_limits", {"gemini-2.5-flash": 12.0})
        SettingsManager.set("gemini.proactive_thresholds", {"gemini-2.5-flash": 11})

        self.assertEqual(limiter.get_quota_rpm("gemini-2.5-flash"), 12.0)
        self.assertEqual(limiter.get_proactive_threshold("gemini-2.5-flash"), 11)

    def test_r3_tab1_llm_settings(self):
        """Memvalidasi Tab 1 (Umum & LLM): Kunci API, rantai model, model embedding."""
        cfg = SettingsManager.get_gemini_config()
        self.assertIn("api_key", cfg)
        self.assertIn("model_chain", cfg)
        self.assertIn("embedding_model", cfg)
        self.assertIn("embedding_model_fallback", cfg)
        self.assertEqual(cfg["temperature"], 0.1)

    def test_r3_tab2_keywords_subtabs_in_db(self):
        """Memvalidasi Tab 2 (Filter Kata Kunci Scraping): 3 sub-tab kategori terikat langsung ke state.db."""
        kw = SettingsManager.get_keywords()
        self.assertIn("indonesia_mandiri", kw)
        self.assertIn("objek_data_sensitif", kw)
        self.assertIn("objek_aset_digital", kw)
        self.assertIsInstance(kw["indonesia_mandiri"], list)
        self.assertIsInstance(kw["objek_data_sensitif"], list)
        self.assertIsInstance(kw["objek_aset_digital"], list)
        self.assertGreater(len(kw["indonesia_mandiri"]), 0)
        self.assertGreater(len(kw["objek_data_sensitif"]), 0)
        self.assertGreater(len(kw["objek_aset_digital"]), 0)

    def test_r3_tab3_prompts_in_db(self):
        """Memvalidasi Tab 3 (Template Prompt LLM): Seluruh 6 prompt aktif bersumber dari state.db."""
        prompts = SettingsManager.get_all_prompts_info()
        self.assertEqual(len(prompts), 6)
        prompt_ids = [p["id"] for p in prompts]
        expected_ids = [
            "klasifikasi",
            "ringkas_berita",
            "section_1_makro",
            "section_2_mikro",
            "section_3_vektor",
            "section_5_emerging",
        ]
        for pid in expected_ids:
            self.assertIn(pid, prompt_ids)
            content = SettingsManager.get_prompt(pid)
            self.assertIsInstance(content, str)
            self.assertGreater(len(content.strip()), 10, f"Prompt {pid} is empty")

    def test_r3_tab4_rss_sources_in_db(self):
        """Memvalidasi Tab 4 (Sumber RSS): Membaca sumber feed internasional dan nasional dari state.db."""
        intl = SettingsManager.get_rss_sources("international")
        indo = SettingsManager.get_rss_sources("indonesia")
        self.assertIsInstance(intl, list)
        self.assertIsInstance(indo, list)
        self.assertGreater(len(intl), 0)
        self.assertGreater(len(indo), 0)
        for s in intl + indo:
            self.assertIn("nama", s)
            self.assertIn("feeds", s)
            self.assertGreater(len(s["feeds"]), 0)

    def test_r3_tab5_references_info(self):
        """Memvalidasi Tab 5 (Sumber Referensi CTI): Endpoint info referensi mengembalikan 4 framework."""
        from fastapi.testclient import TestClient
        from src.web.app import app, buat_token_sesi

        client = TestClient(app)
        token = buat_token_sesi("admin")
        client.cookies.set("cti_session", token)

        resp = client.get("/api/settings/references-info")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "ok")
        refs = data.get("references", [])
        self.assertEqual(len(refs), 4)
        ref_ids = [r["id"] for r in refs]
        for expected in ["ecsirt", "mitre_attack", "mitre_d3fend", "nist_controls"]:
            self.assertIn(expected, ref_ids)


if __name__ == "__main__":
    unittest.main()
