import tests.conftest
import json
import logging
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from src.scraper.sources import FilterKataKunci, _kumpulkan_semua_kata_kunci
from src.utils.llm_adapter import DEFAULT_MODEL_CHAIN, GeminiLLMAdapter, GeminiRateLimiter
from src.utils.settings_manager import (
    DEFAULT_PROACTIVE_THRESHOLDS,
    DEFAULT_RATE_LIMITS,
    OFFICIAL_NARRATIVE_MODELS,
    OBSOLETE_MODELS,
    SettingsManager,
)
from src.web.app import app


class TestAdversarialR2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def setUp(self):
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

    def test_corrupted_database_graceful_fallback_and_warning(self):
        """SettingsManager wajib gracefully fallback ke default resmi dan mencatat warning saat DB rusak."""
        corrupt_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        corrupt_file.write(b"CORRUPT_DATABASE_HEADER_INVALID_SQLITE_DATA")
        corrupt_file.close()

        try:
            with self.assertLogs("src.utils.settings_manager", level="WARNING") as cm:
                SettingsManager.set_db_path(corrupt_file.name)
                # Model chain fallback
                chain = SettingsManager.get("gemini.model_chain")
                self.assertEqual(chain, OFFICIAL_NARRATIVE_MODELS)

                # Rate limits fallback
                rl = SettingsManager.get("gemini.rate_limits")
                self.assertIsInstance(rl, dict)
                for m in OFFICIAL_NARRATIVE_MODELS:
                    self.assertIn(m, rl)
                self.assertEqual(rl["gemini-2.5-flash"], 5.0)
                self.assertEqual(rl["gemini-3.1-flash-lite"], 15.0)
                self.assertEqual(rl["gemini-embedding-001"], 100.0)

                # Proactive thresholds fallback
                pt = SettingsManager.get("gemini.proactive_thresholds")
                self.assertIsInstance(pt, dict)
                for m in OFFICIAL_NARRATIVE_MODELS:
                    self.assertIn(m, pt)
                self.assertEqual(pt["gemini-2.5-flash"], 4)
                self.assertEqual(pt["gemini-3.1-flash-lite"], 14)
                self.assertEqual(pt["gemini-embedding-001"], 90)

            # Warning log must be present
            self.assertTrue(any("gagal membaca" in msg.lower() or "peringatan" in msg.lower() for msg in cm.output))
        finally:
            SettingsManager.reset_db_path()
            try:
                os.remove(corrupt_file.name)
            except Exception:
                pass

    def test_bom_stripping_on_prompts_and_strings(self):
        """SettingsManager wajib membersihkan karakter UTF-8 BOM (\ufeff) dari string prompt."""
        # Test direct get
        SettingsManager.set("prompt.test_bom", "\ufeffHalo, ini instruksi tanpa BOM.")
        isi = SettingsManager.get("prompt.test_bom")
        self.assertFalse(isi.startswith("\ufeff"))
        self.assertTrue(isi.startswith("Halo"))

        # Test pre-existing prompt in state.db
        p_klasifikasi = SettingsManager.get("prompt.klasifikasi")
        self.assertFalse(p_klasifikasi.startswith("\ufeff"))
        self.assertTrue(p_klasifikasi.startswith("Kamu adalah analis"))

    def test_partial_dict_in_rate_limits_and_thresholds_backfilled(self):
        """Jika rate_limits di DB hanya berisi sebagian model, 7 model narasi & embedding wajib di-backfill."""
        partial_rl = {"gemini-2.5-flash": 5.0, "gemini-2.0-flash": 99.0}
        SettingsManager.set("gemini.rate_limits", partial_rl)

        rl = SettingsManager.get("gemini.rate_limits")
        self.assertNotIn("gemini-2.0-flash", rl)
        for m in OFFICIAL_NARRATIVE_MODELS:
            self.assertIn(m, rl)
        self.assertIn("gemini-embedding-001", rl)
        self.assertIn("text-embedding-004", rl)

        partial_pt = {"gemini-2.5-flash": 4, "gemini-1.5-pro": 88}
        SettingsManager.set("gemini.proactive_thresholds", partial_pt)

        pt = SettingsManager.get("gemini.proactive_thresholds")
        self.assertNotIn("gemini-1.5-pro", pt)
        for m in OFFICIAL_NARRATIVE_MODELS:
            self.assertIn(m, pt)
        self.assertIn("gemini-embedding-001", pt)
        self.assertIn("text-embedding-004", pt)

    def test_api_settings_keywords_sanitization_and_deduplication(self):
        """Endpoint /api/settings wajib men-sanitize, lowercase, trim whitespace, dan deduplikasi kata kunci."""
        from src.web.app import buat_token_sesi
        token = buat_token_sesi("admin")
        self.client.cookies.set("cti_session", token)

        payload = {
            "keywords": {
                "indonesia_mandiri": ["  Bocor  ", "bocor", "KEBOCORAN DATA", "", "   ", "kebocoran data"],
                "objek_data_sensitif": "ktp, KTP,   nik,  paspor \n SIM",
            }
        }
        res = self.client.post("/api/settings", json=payload)
        self.assertEqual(res.status_code, 200)

        mandiri = SettingsManager.get("keywords.indonesia_mandiri")
        self.assertEqual(mandiri, ["bocor", "kebocoran data"])

        sensitif = SettingsManager.get("keywords.objek_data_sensitif")
        self.assertEqual(sensitif, ["ktp", "nik", "paspor", "sim"])

    def test_api_settings_model_chain_strips_obsolete_and_deduplicates(self):
        """Endpoint /api/settings wajib memfilter model usang dan mendeduplikasi input model chain."""
        from src.web.app import buat_token_sesi
        token = buat_token_sesi("admin")
        self.client.cookies.set("cti_session", token)

        payload = {
            "model_chain": [
                "gemini-2.5-flash",
                "gemini-2.0-flash",
                "gemini-2.5-flash-lite",
                "gemini-1.5-flash",
                "gemini-2.5-flash",
                "gemini-3-flash",
                "gemini-3.5-flash",
            ]
        }
        res = self.client.post("/api/settings", json=payload)
        self.assertEqual(res.status_code, 200)

        chain = SettingsManager.get("gemini.model_chain")
        self.assertEqual(chain, ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash"])
        for obs in OBSOLETE_MODELS:
            self.assertNotIn(obs, chain)

    def test_api_settings_prompts_preserves_newlines_and_strips_bom(self):
        """Endpoint /api/settings/prompts wajib mempertahankan newline dan membersihkan BOM."""
        from src.web.app import buat_token_sesi
        token = buat_token_sesi("admin")
        self.client.cookies.set("cti_session", token)

        multiline_prompt = "\ufeffBaris 1: Analisis insiden.\nBaris 2: Pemetaan TTP.\nBaris 3: Rekomendasi."
        res = self.client.post("/api/settings/prompts", json={"section_1_makro": multiline_prompt})
        self.assertEqual(res.status_code, 200)

        saved = SettingsManager.get_prompt("section_1_makro")
        self.assertFalse(saved.startswith("\ufeff"))
        self.assertIn("\nBaris 2:", saved)
        self.assertEqual(saved.count("\n"), 2)

    def test_api_settings_rss_sources_sanitization(self):
        """Endpoint /api/settings/rss wajib memvalidasi struktur, mendeduplikasi URLs, dan menolak entri kosong."""
        from src.web.app import buat_token_sesi
        token = buat_token_sesi("admin")
        self.client.cookies.set("cti_session", token)

        payload = {
            "international": [
                {"nama": "Bleeping Computer", "feeds": ["https://example.com/feed", "https://example.com/feed"], "active": True},
                {"nama": "   ", "feeds": ["https://invalid.com/feed"]},
            ]
        }
        res = self.client.post("/api/settings/rss", json=payload)
        self.assertEqual(res.status_code, 200)

        sources = SettingsManager.get_rss_sources("international")
        self.assertEqual(len(sources), 1)
        self.assertEqual(sources[0]["nama"], "Bleeping Computer")
        self.assertEqual(sources[0]["feeds"], ["https://example.com/feed"])

    def test_scraper_keywords_priority_and_fallback(self):
        """Filter scraping memprioritaskan database, namun mundur ke config.yaml jika DB kosong."""
        dummy_config = {
            "keywords": {
                "english": ["cyberattack_fallback"],
                "indonesia_mandiri": ["peretasan_fallback"],
                "objek_data_sensitif": ["rekam_medis_fallback"],
                "objek_aset_digital": ["server_fallback"],
                "indikator_insiden": ["terbobol_fallback"],
                "ambigu_butuh_konteks": ["judi_fallback"],
            }
        }

        # 1. Saat DB terisi (kondisi default): DB diutamakan
        kw = _kumpulkan_semua_kata_kunci(dummy_config)
        self.assertIn("kebocoran data", kw["mandiri"])

        # 2. Saat DB dikosongkan: fallback ke config.yaml aktif
        SettingsManager.set("keywords.indonesia_mandiri", [])
        kw_after_empty = _kumpulkan_semua_kata_kunci(dummy_config)
        self.assertIn("peretasan_fallback", kw_after_empty["mandiri"])

    def test_embedding_chain_strictly_two_models_quota_100_threshold_90(self):
        """Memverifikasi embedding chain persis 2 model dengan kuota 100 RPM & threshold proaktif 90."""
        SettingsManager.set("gemini.embedding_model", "gemini-embedding-001")
        SettingsManager.set("gemini.embedding_model_fallback", ["gemini-embedding-exp-03-07"])

        chain = GeminiLLMAdapter._get_embedding_chain()
        self.assertEqual(chain, ["gemini-embedding-001", "gemini-embedding-exp-03-07"])
        self.assertEqual(len(chain), 2)

        limiter = GeminiRateLimiter()
        for model in chain:
            self.assertEqual(limiter.get_quota_rpm(model), 100.0)
            self.assertEqual(limiter.get_proactive_threshold(model), 90)


if __name__ == "__main__":
    unittest.main()
