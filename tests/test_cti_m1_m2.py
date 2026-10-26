"""
Unit & Integration Test Suite for SiberHarian CTI Milestones 1 & 2.
Mencakup pengujian:
- Downloader resilience (retry exponential backoff, timeout, mirror)
- Metadata schema & SHA-256 verification
- STIX 2.1 flattener (filtering revoked & deprecated)
- Taxonomy corpus generator (11 closed categories & eCSIRT parents)
- D3FEND relational SQLite storage & deterministic SQL lookup
- NIST OSCAL catalog flattener (SP 800-53 Rev 5 & CSF 2.0)
"""

import os
import json
import sqlite3
import tempfile
import hashlib
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.cti.downloader import (
    CTIDownloader,
    DownloadError,
    DEFAULT_TIMEOUT,
)
from src.cti.preparer import (
    CTIPreparer,
    flatten_attack_stix,
    generate_taxonomy_documents,
    prepare_d3fend_storage,
    flatten_nist_oscal,
    CLOSED_11_TAXONOMY_CATEGORIES,
    TAXONOMY_DISPLAY_NAMES,
    ECSIRT_PARENT_MAPPINGS,
)
from src.storage.db import (
    init_db,
    simpan_d3fend_techniques,
    simpan_d3fend_attack_mappings,
    ambil_d3fend_mitigasi_by_attack_id,
    ambil_semua_d3fend_techniques,
    ambil_semua_d3fend_mappings,
)


class TestCTIDownloader(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.staging_dir = Path(self.temp_dir.name) / "raw"
        self.downloader = CTIDownloader(
            base_staging_dir=self.staging_dir,
            timeout=5,
            max_retries=3,
            backoff_factor=1.1,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_downloader_retry_and_resilience_raises_download_error(self):
        """Downloader harus mencoba ulang hingga 3x dan melempar DownloadError saat gagal."""
        with patch.object(self.downloader.session, "get", side_effect=Exception("Connection refused")):
            dest_file = self.staging_dir / "test" / "file.json"
            with self.assertRaises(DownloadError) as ctx:
                self.downloader._download_stream_with_retry("https://example.com/fail.json", dest_file)
            self.assertIn("Gagal mengunduh", str(ctx.exception))
            self.assertIn("3 percobaan", str(ctx.exception))

    def test_downloader_local_mirror_support(self):
        """Downloader harus dapat mengambil payload dari mirror lokal jika tersedia."""
        mirror_dir = Path(self.temp_dir.name) / "mirror"
        mirror_dir.mkdir(parents=True, exist_ok=True)
        mirror_file = mirror_dir / "machinetag.json"
        dummy_content = b'{"namespace": "ecsirt", "version": "2", "predicates": []}'
        mirror_file.write_bytes(dummy_content)

        downloader_with_mirror = CTIDownloader(
            base_staging_dir=self.staging_dir,
            mirror_base_url=str(mirror_dir),
        )

        dest_file = self.staging_dir / "misp_taxonomies" / "2026-10-20" / "machinetag.json"
        sha256, size = downloader_with_mirror._download_stream_with_retry(
            "https://example.com/machinetag.json", dest_file
        )

        self.assertTrue(dest_file.exists())
        self.assertEqual(size, len(dummy_content))
        self.assertEqual(sha256, hashlib.sha256(dummy_content).hexdigest())

    def test_metadata_json_schema_completeness(self):
        """Metadata JSON staging harus memuat seluruh 8 atribut wajib."""
        dest_dir = self.staging_dir / "misp_taxonomies" / "2026-10-20"
        dest_dir.mkdir(parents=True, exist_ok=True)
        sample_json = dest_dir / "machinetag.json"
        content = json.dumps({"namespace": "ecsirt", "version": "2", "predicates": [{"values": [1, 2]}]}).encode("utf-8")
        sample_json.write_bytes(content)

        with patch.object(self.downloader, "_download_stream_with_retry", return_value=(hashlib.sha256(content).hexdigest(), len(content))):
            meta = self.downloader.download_misp_taxonomy("2026-10-20")

        required_keys = [
            "source_name", "source_url", "download_timestamp_utc",
            "version_identifier", "file_sha256", "file_size_bytes",
            "record_count_parsed", "download_status"
        ]
        for key in required_keys:
            self.assertIn(key, meta, f"Missing required metadata key: {key}")
        self.assertEqual(meta["download_status"], "SUCCESS")
        self.assertEqual(len(meta["file_sha256"]), 64)
        self.assertGreater(meta["file_size_bytes"], 0)


class TestCTIPreparer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_state.db"
        init_db(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_flatten_attack_stix_filters_revoked_and_deprecated(self):
        """STIX flattener wajib membuang teknik revoked dan deprecated, hanya menyisakan teknik aktif."""
        sample_bundle = {
            "type": "bundle",
            "id": "bundle--123",
            "objects": [
                {
                    "type": "x-mitre-collection",
                    "x_mitre_version": "20.0"
                },
                {
                    "type": "attack-pattern",
                    "id": "attack-pattern--active-1",
                    "name": "Phishing",
                    "description": "Adversaries may send phishing messages.",
                    "revoked": False,
                    "x_mitre_deprecated": False,
                    "x_mitre_platforms": ["Windows", "Linux"],
                    "kill_chain_phases": [{"kill_chain_name": "mitre-attack", "phase_name": "initial-access"}],
                    "external_references": [{"source_name": "mitre-attack", "external_id": "T1566"}],
                },
                {
                    "type": "attack-pattern",
                    "id": "attack-pattern--revoked-1",
                    "name": "PowerShell (Revoked)",
                    "description": "Old PowerShell technique.",
                    "revoked": True,
                    "external_references": [{"source_name": "mitre-attack", "external_id": "T1086"}],
                },
                {
                    "type": "attack-pattern",
                    "id": "attack-pattern--deprecated-1",
                    "name": "Graphical User Interface (Deprecated)",
                    "description": "Deprecated GUI technique.",
                    "x_mitre_deprecated": True,
                    "external_references": [{"source_name": "mitre-attack", "external_id": "T1061"}],
                },
                {
                    "type": "malware",
                    "id": "malware--1",
                    "name": "Non Attack Pattern",
                }
            ]
        }

        flattened = flatten_attack_stix(sample_bundle, source_version="v20.0")
        self.assertEqual(len(flattened), 1)
        tech = flattened[0]
        self.assertEqual(tech["technique_id"], "T1566")
        self.assertEqual(tech["name"], "Phishing")
        self.assertEqual(tech["tactics"], ["initial-access"])
        self.assertFalse(tech["revoked"])
        self.assertFalse(tech["deprecated"])
        self.assertEqual(tech["metadata"]["source"], "mitre-attack")
        self.assertEqual(tech["metadata"]["source_version"], "v20.0")

        # Test formatting for RAG
        rag_text = CTIPreparer.format_attack_document_text(tech)
        self.assertIn("[TEKNIK MITRE ATT&CK]", rag_text)
        self.assertIn("ID: T1566", rag_text)

    def test_generate_taxonomy_documents_closed_11_categories(self):
        """Taxonomy generator wajib menghasilkan tepat 11 kategori tertutup dengan pemetaan eCSIRT."""
        docs = generate_taxonomy_documents(source_version="2")
        self.assertEqual(len(docs), 11)

        cat_ids = [d["category_id"] for d in docs]
        for expected in CLOSED_11_TAXONOMY_CATEGORIES:
            self.assertIn(expected, cat_ids)

        for d in docs:
            cat_id = d["category_id"]
            self.assertEqual(d["name"], TAXONOMY_DISPLAY_NAMES[cat_id])
            self.assertEqual(d["ecsirt_parent"], ECSIRT_PARENT_MAPPINGS[cat_id])
            self.assertTrue(len(d["definition"]) > 20)
            self.assertTrue(len(d["representative_examples"]) >= 1)
            self.assertEqual(d["metadata"]["source"], "misp-taxonomies/ecsirt")

        # Termasuk kategori wajib "tidak_dapat_ditentukan"
        undetermined = next(d for d in docs if d["category_id"] == "tidak_dapat_ditentukan")
        self.assertEqual(undetermined["name"], "Tidak Dapat Ditentukan")
        self.assertEqual(undetermined["ecsirt_parent"], "other:unspecified")

    def test_d3fend_relational_storage_and_deterministic_lookup(self):
        """D3FEND wajib tersimpan dalam tabel relasional SQLite dan dapat di-lookup secara deterministik."""
        sample_techniques = {
            "@graph": [
                {
                    "@id": "d3f:Multi-factorAuthentication",
                    "d3f:d3fend-id": "D3-MFA",
                    "rdfs:label": "Multi-factor Authentication",
                    "d3f:synonym": "MFA, 2FA"
                },
                {
                    "@id": "d3f:WebApplicationFiltering",
                    "d3f:d3fend-id": "D3-WAF",
                    "rdfs:label": "Web Application Filtering",
                    "d3f:synonym": "WAF"
                }
            ]
        }

        sample_mappings = {
            "results": {
                "bindings": [
                    {
                        "off_tech_id": {"value": "T1566"},
                        "def_tech_label": {"value": "Multi-factor Authentication"},
                        "def_tactic_label": {"value": "Credential Access Defense"},
                        "def_tech": {"value": "http://d3fend.mitre.org/ontologies/d3fend.owl#Multi-factorAuthentication"}
                    },
                    {
                        "off_tech_id": {"value": "T1190"},
                        "def_tech_label": {"value": "Web Application Filtering"},
                        "def_tactic_label": {"value": "Application Hardening"},
                        "def_tech": {"value": "http://d3fend.mitre.org/ontologies/d3fend.owl#WebApplicationFiltering"}
                    }
                ]
            }
        }

        res = prepare_d3fend_storage(
            mappings_input=sample_mappings,
            techniques_input=sample_techniques,
            db_path=self.db_path,
            source_version="1.6.0"
        )

        self.assertGreaterEqual(res["techniques_stored"], 2)
        self.assertEqual(res["mappings_stored"], 2)

        # Lookup T1566 (Phishing)
        mitigations = ambil_d3fend_mitigasi_by_attack_id("T1566", db_path=self.db_path)
        self.assertEqual(len(mitigations), 1)
        self.assertEqual(mitigations[0]["technique_id"], "D3-MFA")
        self.assertEqual(mitigations[0]["name"], "Multi-factor Authentication")
        self.assertEqual(mitigations[0]["tactic"], "Credential Access Defense")

        # Lookup sub-technique T1566.001 -> harus fallback ke T1566 jika tidak ada spesifik
        sub_mitigations = ambil_d3fend_mitigasi_by_attack_id("T1566.001", db_path=self.db_path)
        self.assertEqual(len(sub_mitigations), 1)
        self.assertEqual(sub_mitigations[0]["technique_id"], "D3-MFA")

        # Lookup teknik yang tidak memiliki mapping -> harus return empty list (tanpa halusinasi)
        unmapped = ambil_d3fend_mitigasi_by_attack_id("T9999", db_path=self.db_path)
        self.assertEqual(unmapped, [])

    def test_flatten_nist_oscal_catalogs(self):
        """NIST flattener wajib meratakan SP 800-53 controls dan CSF 2.0 subcategories."""
        sample_sp800 = {
            "catalog": {
                "groups": [
                    {
                        "id": "ac",
                        "title": "Access Control",
                        "controls": [
                            {
                                "id": "ac-2",
                                "title": "Account Management",
                                "parts": [
                                    {"name": "statement", "prose": "Manage information system accounts."}
                                ]
                            }
                        ]
                    }
                ]
            }
        }

        sample_csf = {
            "catalog": {
                "groups": [
                    {
                        "id": "PR",
                        "title": "PROTECT",
                        "controls": [
                            {
                                "id": "PR.AA",
                                "title": "Identity Management and Access Control",
                                "controls": [
                                    {
                                        "id": "PR.AA-01",
                                        "title": "Identities Managed",
                                        "parts": [
                                            {"name": "statement", "prose": "Identities and credentials are managed."}
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }

        controls = flatten_nist_oscal(sample_sp800, sample_csf)
        self.assertEqual(len(controls), 2)

        ctrl_ids = [c["control_id"] for c in controls]
        self.assertIn("AC-2", ctrl_ids)
        self.assertIn("PR.AA-01", ctrl_ids)

        ac2 = next(c for c in controls if c["control_id"] == "AC-2")
        self.assertEqual(ac2["framework"], "NIST SP 800-53 Rev 5")
        self.assertEqual(ac2["statement"], "Manage information system accounts.")
        self.assertEqual(ac2["metadata"]["source"], "nist-oscal")

        rag_text = CTIPreparer.format_nist_document_text(ac2)
        self.assertIn("[KONTROL KEAMANAN SISTEM NIST]", rag_text)
        self.assertIn("ID Kontrol: AC-2", rag_text)


if __name__ == "__main__":
    unittest.main()
