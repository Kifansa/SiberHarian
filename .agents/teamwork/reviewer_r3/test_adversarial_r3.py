import concurrent.futures
import json
import logging
import os
import shutil
import tempfile
import unittest
from pathlib import Path

import tests.conftest
from fastapi.testclient import TestClient

from src.scraper.sources import FilterKataKunci, bangun_daftar_feed_rss
from src.utils.llm_adapter import (
    APIKeyPool,
    DEFAULT_MODEL_CHAIN,
    GeminiLLMAdapter,
    GeminiRateLimiter,
)
from src.utils.settings_manager import (
    DEFAULT_PROACTIVE_THRESHOLDS,
    DEFAULT_RATE_LIMITS,
    OBSOLETE_MODELS,
    OFFICIAL_NARRATIVE_MODELS,
    SettingsManager,
)
from src.web.app import app, buat_token_sesi


class TestAdversarialR3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.admin_token = buat_token_sesi("admin")

    def setUp(self):
        self._temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self._temp_db.close()
        shutil.copy2("data/state.db", self._temp_db.name)
        SettingsManager.set_db_path(self._temp_db.name)
        self.client.cookies.set("cti_session", self.admin_token)

    def tearDown(self):
        SettingsManager.reset_db_path()
        try:
            os.remove(self._temp_db.name)
        except Exception:
            pass

    def test_concurrent_multithread_rate_limiter_proactive_thresholds(self):
        """Simulasi 20 threads paralel menguji transisi ambang proaktif seluruh 7 model narasi & 2 embedding."""
        limiter = GeminiRateLimiter()
        pool = APIKeyPool()
        pool.set_keys(["AIzaSyKey1ParallelTest", "AIzaSyKey2ParallelTest"])

        # Matriks model narasi resmi (quota, proactive_threshold)
        expected_thresholds = {
            "gemini-2.5-flash": 4,
            "gemini-2.5-flash-lite": 9,
            "gemini-3-flash": 4,
            "gemini-3.1-flash-lite": 14,
            "gemini-3.6-flash": 4,
            "gemini-3.5-flash-lite": 14,
            "gemini-3.8-flash": 4,
            "gemini-embedding-001": 90,
            "gemini-embedding-exp-03-07": 90,
        }

        # Verifikasi batas ambang statis & dinamis
        for model, expected_thresh in expected_thresholds.items():
            self.assertEqual(
                limiter.get_proactive_threshold(model),
                expected_thresh,
                f"Model {model} harus memiliki proactive threshold {expected_thresh}",
            )

        # Uji konkurensi: 20 worker threads merekam pemanggilan secara simultan
        def worker_task(model_name: str, count: int, key: str):
            for _ in range(count):
                limiter.record_call(model_name, key)

        active_key = pool.get_active_key()
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = []
            # Isi model gemini-2.5-flash sampai 4 calls (ambang tercapai)
            futures.append(executor.submit(worker_task, "gemini-2.5-flash", 4, active_key))
            # Isi model gemini-2.5-flash-lite sampai 8 calls (1 call di bawah ambang 9)
            futures.append(executor.submit(worker_task, "gemini-2.5-flash-lite", 8, active_key))
            concurrent.futures.wait(futures)

        # flash (4 calls) wajib terdeteksi near limit
        self.assertTrue(limiter.is_model_near_limit("gemini-2.5-flash", active_key))
        # flash-lite (8 calls) belum mencapai batas 9
        self.assertFalse(limiter.is_model_near_limit("gemini-2.5-flash-lite", active_key))

        # Pilihan slot otomatis berpindah ke model kedua (flash-lite) tanpa jeda
        candidate_models = ["gemini-2.5-flash", "gemini-2.5-flash-lite", "gemini-3-flash"]
        sel_key, sel_model, wait_sec = limiter.select_available_slot(candidate_models, pool)
        self.assertEqual(sel_key, active_key)
        self.assertEqual(sel_model, "gemini-2.5-flash-lite")
        self.assertEqual(wait_sec, 0.0)

    def test_tab1_api_keys_and_model_chain_top_level_and_edge_cases(self):
        """Tab 1: Input API Key dan Model Chain di-sanitize, obsolete dibuang, dan top-level api_key didukung."""
        # Test input top-level api_key dengan newline dan koma
        raw_keys = "AIzaSyKeyA\r\nAIzaSyKeyB,  AIzaSyKeyA  \nAIzaSyKeyC"
        payload = {
            "api_key": raw_keys,
            "model_chain": "gemini-2.5-flash, gemini-2.0-flash, gemini-3-flash, gemini-1.5-flash, gemini-2.5-flash",
        }
        res = self.client.post("/api/settings", json=payload)
        self.assertEqual(res.status_code, 200)

        # Verifikasi API Key tersimpan bersih & terdeduplikasi
        saved_keys = SettingsManager.get("gemini.api_key")
        self.assertEqual(saved_keys, ["AIzaSyKeyA", "AIzaSyKeyB", "AIzaSyKeyC"])

        # Verifikasi Model Chain membersihkan model usang dan deduplikasi
        saved_chain = SettingsManager.get("gemini.model_chain")
        self.assertEqual(saved_chain, ["gemini-2.5-flash", "gemini-3-flash"])
        for obs in OBSOLETE_MODELS:
            self.assertNotIn(obs, saved_chain)

    def test_tab1_rate_limits_and_thresholds_purge_obsolete_on_write(self):
        """Tab 1: Menyimpan rate_limits dan proactive_thresholds membuang model usang saat ditulis ke database."""
        payload = {
            "rate_limits": {
                "gemini-2.5-flash": 5,
                "gemini-2.0-flash": 99,
                "gemini-1.5-pro": 88,
                "gemini-embedding-001": 100,
            },
            "proactive_thresholds": {
                "gemini-2.5-flash": 4,
                "gemini-3.5-flash": 99,
                "embedding-001": 88,
                "gemini-embedding-001": 90,
            },
        }
        res = self.client.post("/api/settings", json=payload)
        self.assertEqual(res.status_code, 200)

        rl = SettingsManager.get("gemini.rate_limits")
        self.assertNotIn("gemini-2.0-flash", rl)
        self.assertNotIn("gemini-1.5-pro", rl)
        self.assertEqual(rl["gemini-2.5-flash"], 5.0)

        pt = SettingsManager.get("gemini.proactive_thresholds")
        self.assertNotIn("gemini-3.5-flash", pt)
        self.assertNotIn("embedding-001", pt)
        self.assertEqual(pt["gemini-2.5-flash"], 4)

    def test_tab2_keywords_database_roundtrip_and_relevance_filter(self):
        """Tab 2: Filter Kata Kunci Scraping tersinkron ke 3 kategori dan mempengaruhi FilterKataKunci."""
        payload = {
            "keywords": {
                "indonesia_mandiri": ["  Ransomware  ", "PERETASAN", "ransomware", "  "],
                "objek_data_sensitif": ["ktp", "  NIK  ", "npwp"],
                "objek_aset_digital": ["SERVER", "database", "server"],
            }
        }
        res = self.client.post("/api/settings", json=payload)
        self.assertEqual(res.status_code, 200)

        kw_mandiri = SettingsManager.get("keywords.indonesia_mandiri")
        self.assertEqual(kw_mandiri, ["ransomware", "peretasan"])

        # FilterKataKunci wajib mengenali keyword baru dari DB
        fk = FilterKataKunci({})
        self.assertTrue(fk.relevan("Insiden peretasan sistem perbankan nasional"))
        self.assertTrue(fk.relevan("Serangan ransomware mengunci berkas sensitif"))
        self.assertFalse(fk.relevan("Rapat koordinasi pengembangan wilayah"))

    def test_tab3_prompts_preservation_and_configloader_fallback(self):
        """Tab 3: Prompt template mempertahankan format multi-baris dan memiliki fallback saat DB kosong."""
        multi_prompt = "Instruksi Analis CTI:\n1. Identifikasi TTP\n2. Petakan ke MITRE Enterprise\n3. Berikan rekomendasi teknis."
        res = self.client.post("/api/settings/prompts", json={"section_3_vektor": multi_prompt})
        self.assertEqual(res.status_code, 200)

        # GET via API endpoint
        get_res = self.client.get("/api/settings/prompts/section_3_vektor")
        self.assertEqual(get_res.status_code, 200)
        self.assertEqual(get_res.json()["isi"], multi_prompt)

        # Fallback test: jika prompt di DB dikosongkan, get_prompt mundur secara anggun
        SettingsManager.set("prompt.section_3_vektor", "")
        fallback_prompt = SettingsManager.get_prompt("section_3_vektor")
        self.assertIsInstance(fallback_prompt, str)

    def test_tab4_rss_sources_roundtrip_and_builder(self):
        """Tab 4: Manajemen sumber feed RSS disinkronkan ke DB dan dibaca oleh bangun_daftar_feed_rss."""
        payload = {
            "rss_sources_international": [
                {
                    "nama": "The Hacker News",
                    "feeds": ["https://thehackernews.com/rss.xml", "https://thehackernews.com/rss.xml"],
                    "active": True,
                },
                {
                    "nama": "Dark Reading Inactive",
                    "feeds": ["https://darkreading.com/rss.xml"],
                    "active": False,
                },
            ],
            "rss_sources_indonesia": [
                {
                    "nama": "Cyberthreat.id",
                    "feeds": ["https://cyberthreat.id/feed"],
                    "active": True,
                }
            ],
        }
        res = self.client.post("/api/settings", json=payload)
        self.assertEqual(res.status_code, 200)

        # Verifikasi sumber aktif dan tidak aktif pada bangun_daftar_feed_rss
        feeds = bangun_daftar_feed_rss({})
        feed_urls = [f[0] for f in feeds]
        feed_names = [f[1] for f in feeds]

        self.assertIn("https://thehackernews.com/rss.xml", feed_urls)
        self.assertIn("The Hacker News", feed_names)
        self.assertIn("https://cyberthreat.id/feed", feed_urls)
        # Sumber nonaktif tidak boleh dimasukkan ke pipeline crawling
        self.assertNotIn("https://darkreading.com/rss.xml", feed_urls)

    def test_tab5_references_info_and_ndjson_streaming(self):
        """Tab 5: Info 4 framework CTI dan streaming progress pembaruan referensi."""
        res = self.client.get("/api/settings/references-info")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(len(data["references"]), 4)

        # Test streaming progress
        stream_res = self.client.post("/api/settings/update-references")
        self.assertEqual(stream_res.status_code, 200)
        events = [json.loads(line) for line in stream_res.text.splitlines() if line.strip()]
        self.assertGreaterEqual(len(events), 4)
        self.assertEqual(events[-1]["status"], "completed")
        self.assertEqual(events[-1]["percent"], 100)

    def test_frontend_settings_html_contains_zero_literal_slash_n_bugs(self):
        """Memverifikasi partials/_settings.html bebas dari bug regex literal /\\\\n/g dan split('\\\\n')."""
        html_path = Path("src/web/templates/partials/_settings.html")
        content = html_path.read_text(encoding="utf-8")

        # Tidak boleh ada split('\\n') atau replace(/\\n/g)
        self.assertNotIn("buffer.split('\\\\n')", content, "HTML template tidak boleh memuat buffer.split('\\\\n')")
        self.assertNotIn(".replace(/\\\\n/g", content, "HTML template tidak boleh memuat .replace(/\\\\n/g")

        # Harus memuat split('\n') dan replace(/\r?\n/g
        self.assertIn("buffer.split('\\n')", content, "HTML template harus memuat buffer.split('\\n')")
        self.assertIn(".replace(/\\r?\\n/g", content, "HTML template harus memuat .replace(/\\r?\\n/g")


if __name__ == "__main__":
    unittest.main()
