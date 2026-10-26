"""
Empirical Stress Test Harness & Adversarial Oracles
for SiberHarian CTI Intelligence Layer Upgrade.

Executed by Final Adversarial Challenger.
"""

import os
import sys
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch, Mock
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path("D:/penting/magang/kominfo/NOTIFIKASI-BERITA").resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.storage.db import (
    DEFAULT_DB_PATH,
    init_db,
    _koneksi,
    simpan_d3fend_techniques,
    simpan_d3fend_attack_mappings,
    ambil_d3fend_mitigasi_by_attack_id,
    simpan_metadata,
    ambil_metadata,
    simpan_intelijen_berita,
    ambil_intelijen_berita,
)
from src.cti.preparer import (
    CLOSED_11_TAXONOMY_CATEGORIES,
    TAXONOMY_DISPLAY_NAMES,
    ECSIRT_PARENT_MAPPINGS,
)
from src.cti.analyzer import CTINewsAnalyzer
from src.cti.updater import (
    CTISourceUpdater,
    DropDetectionError,
    detect_catastrophic_drop,
    check_upstream_versions,
)
from src.analytics.cti_agents import (
    _generate_section_1_makro,
    _generate_section_2_mikro,
    _generate_section_3_vektor,
    _generate_section_4_rekomendasi,
    _petakan_taksonomi_insiden,
)


class TestEmpiricalAdversarialChallenger(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_db_path = Path(cls.temp_dir.name) / "test_adversarial.db"
        init_db(cls.test_db_path)
        cls.analyzer = CTINewsAnalyzer(db_path=cls.test_db_path, llm_mode="offline")

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    # =========================================================================
    # 1. ACTIVE ATT&CK GUARD STRESS
    # =========================================================================
    def test_guard_active_attack_id_hallucinations_and_invalids(self):
        """Stress-test Active ATT&CK Guard with malicious, hallucinated, and non-existent IDs."""
        hallucinated_ids = [
            "T9999",
            "T0000",
            "INVALID_TECHNIQUE",
            "T1059.999",
            "T9999.001",
            "T1234.567",
            "T-NONE",
            "SELECT * FROM users",
            "<script>alert(1)</script>",
            "T1086",  # Deprecated in modern ATT&CK (PowerShell superseded by T1059.001)
            "T1183",  # Deprecated/revoked in modern ATT&CK (IFEO persistence)
            None,
            "",
            "null",
            "none",
            "tidak_ditentukan",
        ]

        for bad_id in hallucinated_ids:
            with self.subTest(bad_id=bad_id):
                val_id, is_valid = self.analyzer.guard_active_attack_id(bad_id)
                self.assertFalse(
                    is_valid,
                    f"Active ATT&CK Guard failed to reject invalid/hallucinated ID: {bad_id}"
                )
                self.assertEqual(
                    val_id,
                    "tidak_ditentukan",
                    f"Active ATT&CK Guard did not normalize bad ID {bad_id} to 'tidak_ditentukan', got {val_id}"
                )

    def test_guard_active_attack_id_legitimate_ids(self):
        """Verify that genuine active ATT&CK Enterprise techniques pass the guard."""
        legit_ids = [
            "T1566",       # Phishing
            "T1566.001",   # Spearphishing Attachment
            "T1566.002",   # Spearphishing Link
            "T1190",       # Exploit Public-Facing Application
            "T1486",       # Data Encrypted for Impact
            "T1059.001",   # PowerShell
            "T1078",       # Valid Accounts
            "T1003",       # OS Credential Dumping
        ]

        for valid_id in legit_ids:
            with self.subTest(valid_id=valid_id):
                val_id, is_valid = self.analyzer.guard_active_attack_id(valid_id)
                self.assertTrue(
                    is_valid,
                    f"Active ATT&CK Guard incorrectly rejected valid ID: {valid_id}"
                )
                self.assertEqual(val_id, valid_id)

    def test_extract_attack_technique_no_attack_flow_abstains(self):
        """Verify that news without attack flow strictly returns 'tidak_ditentukan' and never guesses."""
        boring_news_samples = [
            "Dinas Komunikasi dan Informatika mengadakan rapat koordinasi SPBE bersama bupati dan jajaran kepala dinas di balai kota.",
            "Sosialisasi peraturan daerah mengenai tata kelola data pemerintahan berbasis elektronik berlangsung tertib.",
            "Workshop peningkatan kapasitas SDM digital untuk aparatur sipil negara diselenggarakan secara daring melalui Zoom.",
            "Kunjungan kerja komisi bidang komunikasi meninjau ruang server dan infrastruktur data center pemerintah daerah.",
        ]

        for text in boring_news_samples:
            with self.subTest(text=text[:40]):
                res = self.analyzer.extract_attack_technique(text)
                self.assertEqual(res["status"], "tidak_ditentukan")
                self.assertEqual(res["technique_id"], "tidak_ditentukan")
                self.assertEqual(res["confidence"], 0.0)

    def test_llm_hallucination_injection_neutralized_in_pipeline(self):
        """Adversarially inject LLM returning hallucinated ID T9999 and verify pipeline intercepts and strips it."""
        from src.utils.llm_adapter import GeminiLLMAdapter

        hallucinated_llm_response = json.dumps({
            "technique_id": "T9999",
            "tactic": "Initial Access",
            "technique_name": "Phantom Quantum Teleportation Attack",
            "confidence": 0.99,
            "kutipan_bukti": "Pelaku menyusup lewat sistem komputer."
        })

        with patch.object(GeminiLLMAdapter, "chat", return_value=hallucinated_llm_response):
            analyzer_llm = CTINewsAnalyzer(db_path=self.test_db_path, llm_mode="gemini")
            res = analyzer_llm.extract_attack_technique(
                teks_asli="Peretas melakukan eksploitasi celah keamanan server web pemerintah untuk menyusup.",
                teks_terjemahan="Hacker exploited web server vulnerability to compromise system."
            )
            # The hallucinated T9999 MUST NOT pass
            self.assertNotEqual(res["technique_id"], "T9999")
            self.assertEqual(res["technique_id"], "tidak_ditentukan")
            self.assertEqual(res["status"], "tactic_only")

    # =========================================================================
    # 2. CATASTROPHIC DROP GUARD STRESS
    # =========================================================================
    def test_catastrophic_drop_guard_thresholds(self):
        """Stress-test drop detection with drops > 30% and 0 records."""
        # 1. Total empty payload (0 records)
        with self.assertRaises(DropDetectionError):
            detect_catastrophic_drop("mitre_attack", new_count=0, old_count=100)

        with self.assertRaises(DropDetectionError):
            detect_catastrophic_drop("misp_taxonomies", new_count=0, old_count=11)

        with self.assertRaises(DropDetectionError):
            detect_catastrophic_drop("nist_oscal", new_count=0, old_count=1200)

        # 2. Drops strictly greater than 30%
        # 100 -> 69 (drop 31%)
        with self.assertRaises(DropDetectionError):
            detect_catastrophic_drop("mitre_attack", new_count=69, old_count=100)

        # 1000 -> 699 (drop 30.1%)
        with self.assertRaises(DropDetectionError):
            detect_catastrophic_drop("mitre_d3fend", new_count=699, old_count=1000)

        # 800 -> 100 (drop 87.5%)
        with self.assertRaises(DropDetectionError):
            detect_catastrophic_drop("mitre_attack", new_count=100, old_count=800)

        # 3. Drops <= 30% must be accepted without error
        try:
            # 100 -> 70 (drop exactly 30% - boundary case)
            detect_catastrophic_drop("mitre_attack", new_count=70, old_count=100)
            # 100 -> 75 (drop 25%)
            detect_catastrophic_drop("mitre_attack", new_count=75, old_count=100)
            # 100 -> 100 (drop 0%)
            detect_catastrophic_drop("mitre_attack", new_count=100, old_count=100)
            # 100 -> 150 (growth 50%)
            detect_catastrophic_drop("mitre_attack", new_count=150, old_count=100)
        except DropDetectionError as e:
            self.fail(f"Safe drop was incorrectly flagged as catastrophic: {e}")

    # =========================================================================
    # 3. IDEMPOTENT UPSTREAM UPDATE
    # =========================================================================
    def test_idempotent_version_check_identical_versions(self):
        """Verify CTISourceUpdater detects identical versions and logs 'tidak ada pembaruan'."""
        updater = CTISourceUpdater(db_path=self.test_db_path)
        
        # Seed active versions in database
        updater.set_active_version("mitre_attack", "v20.0")
        updater.set_active_version("mitre_d3fend", "1.6.0")

        # Mock remote version returning identical version
        updater.fetch_remote_version = lambda s: "v20.0" if s == "mitre_attack" else "1.6.0"

        # Check mitre_attack
        res_attack = updater.check_version("mitre_attack")
        self.assertFalse(res_attack["has_update"])
        self.assertEqual(res_attack["active_version"], "v20.0")
        self.assertEqual(res_attack["remote_version"], "v20.0")
        self.assertIn("tidak ada pembaruan", res_attack["message"].lower())
        self.assertEqual(res_attack["message"], "tidak ada pembaruan untuk mitre_attack (versi aktif: v20.0)")

        # Check mitre_d3fend
        res_d3 = updater.check_version("mitre_d3fend")
        self.assertFalse(res_d3["has_update"])
        self.assertIn("tidak ada pembaruan", res_d3["message"].lower())
        self.assertEqual(res_d3["message"], "tidak ada pembaruan untuk mitre_d3fend (versi aktif: 1.6.0)")

    # =========================================================================
    # 4. DETERMINISTIC D3FEND SQL LOOKUP
    # =========================================================================
    def test_d3fend_sql_deterministic_lookup(self):
        """Verify D3FEND lookup is 100% deterministic, relational SQL with zero hallucination."""
        # Seed test D3FEND data into test_db using standard helper
        techniques = [
            {
                "technique_id": "D3-MFA",
                "name": "Multi-Factor Authentication",
                "tactic": "Credential Access Defense",
                "definition": "Enforce MFA",
                "source_version": "1.6.0",
            },
            {
                "technique_id": "D3-NTA",
                "name": "Network Traffic Analysis",
                "tactic": "Network Defense",
                "definition": "Analyze packets",
                "source_version": "1.6.0",
            },
        ]
        simpan_d3fend_techniques(techniques, db_path=self.test_db_path)

        mappings = [
            {"attack_technique_id": "T1566", "d3fend_technique_id": "D3-MFA", "relationship_type": "mitigates"},
            {"attack_technique_id": "T1566.001", "d3fend_technique_id": "D3-MFA", "relationship_type": "mitigates"},
            {"attack_technique_id": "T1190", "d3fend_technique_id": "D3-NTA", "relationship_type": "mitigates"},
        ]
        simpan_d3fend_attack_mappings(mappings, db_path=self.test_db_path)

        # 1. Exact match
        res_t1566 = ambil_d3fend_mitigasi_by_attack_id("T1566", db_path=self.test_db_path)
        self.assertEqual(len(res_t1566), 1)
        self.assertEqual(res_t1566[0]["technique_id"], "D3-MFA")
        self.assertEqual(res_t1566[0]["name"], "Multi-Factor Authentication")

        # 2. Subtechnique match
        res_sub = ambil_d3fend_mitigasi_by_attack_id("T1566.001", db_path=self.test_db_path)
        self.assertEqual(len(res_sub), 1)
        self.assertEqual(res_sub[0]["technique_id"], "D3-MFA")

        # 3. Hierarchy fallback (sub-technique fallback to parent when sub-technique is unmapped)
        res_fallback = ambil_d3fend_mitigasi_by_attack_id("T1190.001", db_path=self.test_db_path)
        self.assertEqual(len(res_fallback), 1)
        self.assertEqual(res_fallback[0]["technique_id"], "D3-NTA")

        # 4. Unknown / Hallucinated ID returns strictly empty list
        res_fake = ambil_d3fend_mitigasi_by_attack_id("T9999", db_path=self.test_db_path)
        self.assertEqual(res_fake, [])

        res_fake_sub = ambil_d3fend_mitigasi_by_attack_id("T9999.999", db_path=self.test_db_path)
        self.assertEqual(res_fake_sub, [])

        # 5. SQL Injection Attack Resistance
        sqli_payload = "' OR '1'='1"
        res_sqli = ambil_d3fend_mitigasi_by_attack_id(sqli_payload, db_path=self.test_db_path)
        self.assertEqual(res_sqli, [])

        # Ensure database tables are completely intact
        with _koneksi(self.test_db_path) as conn:
            cur = conn.execute("SELECT COUNT(*) FROM d3fend_techniques")
            self.assertEqual(cur.fetchone()[0], 2)

    # =========================================================================
    # 5. ADDITIVE DASHBOARD VERIFICATION
    # =========================================================================
    def test_additive_dashboard_preserves_original_content(self):
        """Verify that all enriched sections preserve original baseline text and append verified CTI."""
        data_makro = {
            "nama_pola": "Ransomware & Exploit",
            "korpus_artikel": "Insiden ransomware meningkat di berbagai sektor layanan publik.",
        }
        top3_mikro = [
            {
                "nama_insiden": "Insiden 1: Serangan Ransomware Rumah Sakit",
                "uraian_fakta": "Enkripsi server rekam medis rumah sakit oleh kelompok ransomware.",
                "mitre_mapping": [{"id": "T1486", "technique": "Data Encrypted for Impact", "tactic": "Impact"}],
            },
            {
                "nama_insiden": "Insiden 2: Kebocoran Data Dukcapil",
                "uraian_fakta": "Pencurian jutaan data kependudukan dari server publik.",
                "mitre_mapping": [{"id": "T1190", "technique": "Exploit Public-Facing Application", "tactic": "Initial Access"}],
            },
            {
                "nama_insiden": "Insiden 3: Phishing Kepegawaian",
                "uraian_fakta": "Penyebaran email phishing lampiran pdf palsu kepada ASN.",
                "mitre_mapping": [{"id": "T1566.001", "technique": "Spearphishing Attachment", "tactic": "Initial Access"}],
            },
        ]

        # Section 1 Makro
        sec1 = _generate_section_1_makro(data_makro)
        # Must contain original narrative or header
        self.assertIn("Ransomware & Exploit", sec1)
        # Must strictly APPEND eCSIRT distribution block
        self.assertIn("**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:", sec1)

        # Section 2 Mikro
        sec2 = _generate_section_2_mikro(top3_mikro)
        # Must preserve all 3 micro incidents
        self.assertIn("Insiden 1", sec2)
        self.assertIn("Insiden 2", sec2)
        self.assertIn("Insiden 3", sec2)
        # Must append verified taxonomy tags
        self.assertIn("**Klasifikasi Resmi Taksonomi Insiden (eCSIRT)**:", sec2)
        self.assertIn("*Klasifikasi Resmi*:", sec2)

        # Section 3 Vektor
        sec3 = _generate_section_3_vektor(top3_mikro)
        # Must preserve attack vector narrative
        self.assertIn("T1486", sec3)
        self.assertIn("T1190", sec3)
        self.assertIn("T1566.001", sec3)
        # Must append verified MITRE ATT&CK reference with valid links
        self.assertIn("**Rujukan Terverifikasi MITRE ATT&CK Enterprise**:", sec3)
        self.assertIn("https://attack.mitre.org/techniques/T1486/", sec3)

        # Section 4 Rekomendasi
        sec4 = _generate_section_4_rekomendasi(top3_mikro)
        # Must preserve original actions
        self.assertIn("**Rekomendasi Aksi untuk ", sec4)
        # Must strictly append D3FEND mitigations and NIST references
        self.assertIn("**Saran Mitigasi Terverifikasi MITRE D3FEND (Lookup Deterministik)**:", sec4)
        self.assertIn("**Referensi Standar NIST Tambahan**:", sec4)


if __name__ == "__main__":
    unittest.main()
