# Technical Remediation Strategy: Rewiring `tests/test_cti_e2e_suite.py` to Production Code

**Author**: Explorer Agent (`explorer_remediate_tests`)  
**Target File**: `tests/test_cti_e2e_suite.py`  
**Working Directory**: `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\explorer_remediate_tests`  
**Reference Report**: Forensic Audit Report (`.agents/teamwork/auditor_test_suite/handoff.md`)  
**Status**: Ready for Implementation  

---

## 1. Observation

### 1.1 Test Suite Status and Audit Findings
1. Inspection of `tests/test_cti_e2e_suite.py` (2,046 lines) reveals that between line 1 and line 2046, there are **zero imports** from `src/` (token `src` appears 0 times).
2. Execution of the test runner tracking loaded modules confirms that running all 150 tests loads **zero production modules**:
   ```
   Ran 150 tests in 0.043s
   Loaded src modules during test run: []
   ```
3. The test file creates two embedded fake constructs:
   - `CTIAuthoritativeSpecs` (lines 36–135): in-file duplicates of taxonomy lists, ATT&CK dictionaries, D3FEND mappings, and NIST controls.
   - `CTIReferenceHarness` (lines 152–380): in-file duplicates of SHA-256 validation, STIX flattening, in-memory SQLite table creation, and metric calculation.
4. Out of 150 test cases:
   - 46 tests (30.7%) assert properties against `CTIReferenceHarness`.
   - 9 tests (6.0%) assert against `CTIAuthoritativeSpecs`.
   - 18 tests (12.0%) execute raw SQL queries against an isolated in-memory SQLite database (`sqlite3.connect(":memory:")`).
   - 77 tests (51.3%) test inline tautologies (e.g. lines 458–459: `default_timeout = 45; self.assertEqual(default_timeout, 45)`, line 788: `dummy_vector = [0.1] * 768; self.assertEqual(len(dummy_vector), 768)`).
5. All 7 acceptance criteria tests in `test_cti_e2e_suite.py` have a **0.0% mutation kill rate** (100% survive when production code in `src/` is mutated or missing).

### 1.2 Existing Genuine Production Modules in `src/`
Inspection of the codebase confirms that substantial production implementations are already available in `src/`:
1. **`src/cti/downloader.py`** (480 lines):
   - Classes & functions: `CTIDownloader`, `DownloadError`, `DEFAULT_TIMEOUT` (45s), `DEFAULT_RAW_DIR`, `OFFICIAL_URLS`.
   - Methods: `_download_stream_with_retry`, `_resolve_url`, `_get_system_proxies`, `download_misp_taxonomy`, `download_mitre_attack`, `download_mitre_d3fend`, `download_nist_oscal`, `download_all`.
   - Writes genuine staging payloads into `data/raw/<source>/<YYYY-MM-DD>/` and writes `metadata.json` with SHA-256 and 8 required attributes.
2. **`src/cti/preparer.py`** (754 lines):
   - Classes & functions: `CTIPreparer`, `flatten_attack_stix`, `generate_taxonomy_documents`, `prepare_d3fend_storage`, `flatten_nist_oscal`.
   - Constants: `CLOSED_11_TAXONOMY_CATEGORIES`, `TAXONOMY_DISPLAY_NAMES`, `ECSIRT_PARENT_MAPPINGS`, `TAXONOMY_DEFINITIONS`.
   - Truly filters out revoked (`revoked: True`) and deprecated (`x_mitre_deprecated: True`) techniques from STIX 2.1 bundles.
3. **`src/cti/vector_store.py`** (583 lines):
   - Classes & functions: `CTIVectorStore`, `compute_deterministic_embedding`, `cosine_similarity`, `VECTOR_DIMENSION` (768).
   - Manages 3 strictly isolated collection namespaces: `collection_attack`, `collection_taxonomy`, `collection_nist`.
   - Maintains independent persistent directories: `dir_attack`, `dir_taxonomy`, `dir_nist`.
4. **`src/storage/db.py`** (1,018 lines):
   - SQLite tables: `d3fend_techniques`, `d3fend_attack_mappings`, `intelijen_berita_tervalidasi`.
   - Genuine functions: `init_db`, `simpan_d3fend_techniques`, `simpan_d3fend_attack_mappings`, `ambil_d3fend_mitigasi_by_attack_id`, `ambil_semua_d3fend_techniques`, `ambil_semua_d3fend_mappings`, `simpan_intelijen_berita`, `ambil_intelijen_berita`, `ambil_semua_intelijen_berita`, `simpan_koreksi_admin_intelijen`, `tandai_flag_tinjauan_intelijen`.
5. **Existing Baseline Tests**:
   - `python -m pytest tests/test_cti_m1_m2.py`: 7 tests passed (5.32s) executing genuine code.
   - `python -m pytest --ignore=tests/test_cti_e2e_suite.py --ignore=tests/test_cti_m1_m2.py`: 36 baseline tests passed (15.05s).

---

## 2. Logic Chain

1. **Step 1 (Root Cause Identification)**:
   The auditor correctly identified that `tests/test_cti_e2e_suite.py` was created as an isolated contract mock rather than a real test runner. Because `CTIReferenceHarness` and `CTIAuthoritativeSpecs` encapsulate their own logic and data structures, testing them does not verify any part of `src/`.
2. **Step 2 (Availability of Production Targets)**:
   Observations 1.2.1 through 1.2.4 demonstrate that production targets for M1, M2, and core components of M3, M4, and M6 already exist in `src/cti/downloader.py`, `src/cti/preparer.py`, `src/cti/vector_store.py`, and `src/storage/db.py`. Therefore, all tests covering M1 and M2 can be immediately and completely rewired to execute these genuine production classes.
3. **Step 3 (Milestone Gating Policy for Incomplete Modules)**:
   For features belonging to incomplete milestones (M4 analyzer pipeline, M5 dashboard additive integration, M6 periodic updater orchestration, M7 evaluation benchmark runner):
   - A self-certifying pass via an inline tautology is strictly prohibited.
   - An honest testing architecture defines the required module interface contract in the test imports. If the module or function is not yet implemented, tests MUST either fail honestly against the contract or be marked with `@unittest.skip(reason="Pending Milestone MX implementation of src.cti.XYZ")`.
   - This ensures that reported test results reflect true milestone completion status (e.g. 70 passed, 80 skipped), with a 0% facade rate.
4. **Step 4 (Mutation Sensitivity)**:
   By asserting directly against the outputs of `flatten_attack_stix`, `ambil_d3fend_mitigasi_by_attack_id`, `CTIDownloader._download_stream_with_retry`, and `tandai_flag_tinjauan_intelijen`, any defect introduced into production code will trigger test failures (100% mutation kill rate on covered features).

---

## 3. Caveats

1. **Pending Production Modules**:
   `src/cti/analyzer.py`, `src/cti/updater.py`, and `src/cti/evaluator.py` have not yet been implemented as dedicated files in `src/cti/`. However, their database backing functions (`simpan_intelijen_berita`, `ambil_intelijen_berita`, `tandai_flag_tinjauan_intelijen`) already exist in `src/storage/db.py`.
2. **FastAPI Web Route Testing**:
   For M5 dashboard additive integration, testing against `src.web.app` requires `starlette.testclient.TestClient`. Tests can assert the presence of legacy content and verify whether the additive CTI blocks are appended once implemented.
3. **External Network Calls During Testing**:
   Tests for `CTIDownloader` must never depend on live upstream internet connections. They should use `unittest.mock.patch` on `requests.Session.get` or use local temporary filesystem mirrors (`mirror_base_url`), verifying genuine retry handling, timeout configuration, and SHA-256 calculation.

---

## 4. Conclusion & Technical Remediation Plan

`tests/test_cti_e2e_suite.py` must be refactored into a genuine production-executing E2E suite. Below is the actionable implementation blueprint.

### 4.1 Structural Changes to `tests/test_cti_e2e_suite.py`

#### A. Eradicate Fake Harness and Specifications
1. **Delete lines 36–135**: completely remove `class CTIAuthoritativeSpecs`.
2. **Delete lines 152–380**: completely remove `class CTIReferenceHarness`.
3. **Delete redundant exception declarations**: remove `class DownloadError` and `class DropDetectionError` from test file; import them from production modules.

#### B. Replace Header with Authoritative Production Imports
```python
import os
import sys
import json
import sqlite3
import hashlib
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
from unittest.mock import patch, MagicMock

# Project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =====================================================================
# PRODUCTION MODULE IMPORTS (M1, M2, M3, STORAGE)
# =====================================================================
from src.cti.downloader import (
    CTIDownloader,
    DownloadError,
    DEFAULT_TIMEOUT,
    DEFAULT_RAW_DIR,
    OFFICIAL_URLS,
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
    TAXONOMY_DEFINITIONS,
)
from src.storage.db import (
    init_db,
    DEFAULT_DB_PATH,
    simpan_d3fend_techniques,
    simpan_d3fend_attack_mappings,
    ambil_d3fend_mitigasi_by_attack_id,
    ambil_semua_d3fend_techniques,
    ambil_semua_d3fend_mappings,
    simpan_intelijen_berita,
    ambil_intelijen_berita,
    ambil_semua_intelijen_berita,
    simpan_koreksi_admin_intelijen,
    tandai_flag_tinjauan_intelijen,
)
from src.cti.vector_store import (
    CTIVectorStore,
    compute_deterministic_embedding,
    cosine_similarity,
    VECTOR_DIMENSION,
)

# =====================================================================
# PENDING MODULE IMPORTS WITH HONEST SKIP CAPABILITY (M4, M5, M6, M7)
# =====================================================================
try:
    from src.cti.analyzer import (
        classify_incident_news,
        extract_attack_technique_conditional,
        validate_active_attack_id,
        lookup_d3fend_mitigations,
        simpan_intelijen_tervalidasi,
    )
except ImportError:
    classify_incident_news = None
    extract_attack_technique_conditional = None
    validate_active_attack_id = None
    lookup_d3fend_mitigations = None
    simpan_intelijen_tervalidasi = None

try:
    from src.cti.updater import (
        check_upstream_versions,
        detect_catastrophic_drop,
        compute_source_diff,
        swap_vector_index_atomic,
        rollback_vector_index,
        audit_and_flag_revoked_incidents,
        DropDetectionError,
    )
except ImportError:
    check_upstream_versions = None
    detect_catastrophic_drop = None
    compute_source_diff = None
    swap_vector_index_atomic = None
    rollback_vector_index = None
    audit_and_flag_revoked_incidents = None
    class DropDetectionError(Exception): pass

try:
    from src.cti.evaluator import (
        generate_draft_evaluation_dataset,
        calculate_cti_metrics,
    )
except ImportError:
    generate_draft_evaluation_dataset = None
    calculate_cti_metrics = None

try:
    from fastapi.testclient import TestClient
    from src.web.app import app
except ImportError:
    TestClient = None
    app = None
```

---

### 4.2 Class-by-Class Rewiring Blueprint (10 Classes, 150 Tests)

#### Class 1: `TestTier1Tahap1DownloadStaging` (10 tests)
- **Target**: `src.cti.downloader.CTIDownloader`
- **Fixtures**: `tempfile.TemporaryDirectory()`, `staging_dir = Path(temp_dir) / "raw"`, `downloader = CTIDownloader(base_staging_dir=staging_dir, timeout=DEFAULT_TIMEOUT)`.
- **Rewiring**:
  - `test_t1_f1_staging_directory_hierarchy`: Call `downloader.download_misp_taxonomy("2026-10-20")` with mocked network; verify `(staging_dir / "misp_taxonomies" / "2026-10-20")` is created by `CTIDownloader`.
  - `test_t1_f1_sha256_calculation_and_verification`: Execute `downloader._download_stream_with_retry` on mock stream; assert returned `sha256` exactly matches `hashlib.sha256(payload).hexdigest()`.
  - `test_t1_f1_sha256_mismatch_detection`: Corrupt file on disk, recompute hash; assert mismatch detected.
  - `test_t1_f1_metadata_json_schema_completeness`: Run `downloader.download_misp_taxonomy`; read real `metadata.json` written to staging directory; assert all 8 required keys exist and are non-empty.
  - `test_t1_f1_zero_byte_payload_rejection`: Mock stream returning 0 bytes; assert `CTIDownloader` raises `DownloadError`.
  - `test_t1_f2_network_retry_exponential_backoff`: Mock session with 3 failures; verify retry count is 3 and exponential backoff is applied before raising `DownloadError`.
  - `test_t1_f2_timeout_handling`: Assert `downloader.timeout == DEFAULT_TIMEOUT == 45` and passes to `session.get(..., timeout=self.timeout)`.
  - `test_t1_f2_proxy_configuration_parsing`: Patch `os.environ` with proxies; call `CTIDownloader._get_system_proxies()`; verify session proxies updated.
  - `test_t1_f2_internal_mirror_url_override`: Call `downloader._resolve_url(...)` with `mirror_base_url` set; assert URL redirected to internal mirror.
  - `test_t1_f2_network_failure_does_not_forge_data`: Mock permanent network failure; assert `DownloadError` raised and zero fake records created.

#### Class 2: `TestTier1Tahap2DataPreparation` (20 tests)
- **Target**: `src.cti.preparer` & `src.storage.db`
- **Fixtures**: `tempfile.TemporaryDirectory()`, `db_path = Path(temp_dir) / "state.db"`, `init_db(db_path)`.
- **Rewiring**:
  - `test_t1_f3_stix_*` (5 tests): Execute real `flatten_attack_stix(bundle, source_version="v20.0")`. Verify filtering of `revoked: True` and `x_mitre_deprecated: True`, extraction of `technique_id` from external_references, and RAG document formatting via `CTIPreparer.format_attack_document_text()`.
  - `test_t1_f4_ecsirt_*` (5 tests): Execute real `generate_taxonomy_documents(source_version="2")`. Verify exactly 11 closed categories in `CLOSED_11_TAXONOMY_CATEGORIES`, valid `ECSIRT_PARENT_MAPPINGS`, and mandatory inclusion of `tidak_dapat_ditentukan` mapped to `other:unspecified`.
  - `test_t1_f5_d3fend_*` (5 tests): Call real `prepare_d3fend_storage(mappings, techniques, db_path=self.db_path)`. Verify tables `d3fend_techniques` and `d3fend_attack_mappings` in SQLite, foreign key enforcement, lookup index `idx_d3fend_attack_lookup`, and deterministic query via `ambil_d3fend_mitigasi_by_attack_id()`.
  - `test_t1_f6_nist_*` (5 tests): Call real `flatten_nist_oscal(sample_sp800, sample_csf)`. Verify extraction of SP 800-53 controls (e.g. `AC-2`) and CSF 2.0 subcategories (`PR.AA-01`), document formatting via `CTIPreparer.format_nist_document_text()`, and metadata schema.

#### Class 3: `TestTier1Tahap3VectorAndEmbedding` (10 tests)
- **Target**: `src.cti.vector_store.CTIVectorStore`
- **Fixtures**: `tempfile.TemporaryDirectory()`, `vector_dir = Path(temp_dir) / "vectors"`, `store = CTIVectorStore(vector_dir=vector_dir, auto_load=False, embedding_mode="offline")`.
- **Rewiring**:
  - `test_t1_f7_three_separate_collections_isolation`: Verify `store.ALLOWED_COLLECTIONS == {"collection_attack", "collection_taxonomy", "collection_nist"}` and lists are isolated.
  - `test_t1_f7_collection_query_scoping`: Verify `search_attack`, `search_taxonomy`, `search_nist` execute only within their respective collections.
  - `test_t1_f7_collection_metadata_tags`: Assert documents stored in collection have correct collection tag.
  - `test_t1_f7_collection_persistence_directory`: Assert `store.dir_attack`, `store.dir_taxonomy`, `store.dir_nist` exist on filesystem.
  - `test_t1_f7_collection_graceful_partial_failure`: Verify independent health tracking in `store.status`.
  - `test_t1_f8_multilingual_embedding_gemini_config`: Verify `DEFAULT_EMBEDDING_MODEL == "gemini-embedding-001"`.
  - `test_t1_f8_multilingual_dimension_768`: Call `compute_deterministic_embedding("ransomware")`; assert vector length is 768 and L2 norm is 1.0.
  - `test_t1_f8_embedding_fallback_chain`: Check fallback model list from configuration.
  - `test_t1_f8_dual_text_storage_strategy`: Verify dual-text fields (`teks_asli` and `teks_terjemahan`) handling.
  - `test_t1_f8_translation_used_for_attack_and_nist_retrieval`: Verify cosine similarity retrieval using English query terms.

#### Class 4: `TestTier1Tahap4PerNewsPipeline` (25 tests)
- **Target**: `src.storage.db` and `src.cti.analyzer` (M4)
- **Fixtures**: Isolated SQLite database initialized with `init_db(self.db_path)`.
- **Rewiring**:
  - D3FEND lookup tests (5 tests): Call real `ambil_d3fend_mitigasi_by_attack_id` on real SQLite database populated with `prepare_d3fend_storage`. Verify fallback for sub-techniques (e.g. `T1566.001` -> `T1566`), unmapped returning `[]`, and zero LLM hallucinated additions.
  - Provenance storage tests (5 tests): Call real `simpan_intelijen_berita`, `ambil_intelijen_berita`, `simpan_koreksi_admin_intelijen` on real SQLite database. Verify unique constraint on `article_identifier`, version retention (`version_taxonomy`, `version_attack`, `version_d3fend`, `version_nist`), and manual correction columns.
  - LLM Analyzer tests (15 tests covering classification, conditional extraction, active ID guard):
    - If `src.cti.analyzer` is implemented: call real functions `classify_incident_news()`, `extract_attack_technique_conditional()`, `validate_active_attack_id()`.
    - If `src.cti.analyzer` is pending: mark tests with `@unittest.skipIf(classify_incident_news is None, "Pending M4 src.cti.analyzer implementation")`.

#### Class 5: `TestTier1Tahap5PeriodicUpdateEngine` (25 tests)
- **Target**: `src.storage.db` and `src.cti.updater` (M6)
- **Rewiring**:
  - Revocation audit tests (Features 23, 5 tests): Execute real `tandai_flag_tinjauan_intelijen(mitre_technique_id, flag, db_path=self.db_path)`.
    - Assert `flag_tinjauan` is set to `"TEKNIK_REVOKED_PERLU_REVIEW"`.
    - Assert total record count in `intelijen_berita_tervalidasi` is **identical before and after** (zero records deleted!).
    - Assert unaffected techniques remain `flag_tinjauan IS NULL`.
    - Assert repeated execution is idempotent.
  - Drop guard & atomic swap tests (Features 19–22, 20 tests):
    - Rewire to call `detect_catastrophic_drop`, `compute_source_diff`, `swap_vector_index_atomic` from `src.cti.updater`.
    - If `src.cti.updater` is pending: mark with `@unittest.skipIf(detect_catastrophic_drop is None, "Pending M6 src.cti.updater implementation")`.

#### Class 6: `TestTier1Tahap6EvaluationFramework` (10 tests)
- **Target**: `src.cti.evaluator` (M7)
- **Rewiring**:
  - Rewire `test_t1_f24_*` to `generate_draft_evaluation_dataset(db_path=self.db_path)`.
  - Rewire `test_t1_f25_*` to `calculate_cti_metrics(ground_truth, predictions)`.
  - If `src.cti.evaluator` is pending: mark with `@unittest.skipIf(calculate_cti_metrics is None, "Pending M7 src.cti.evaluator implementation")`.

#### Class 7: `TestTier1R3DashboardAdditiveIntegration` (10 tests)
- **Target**: `src.web.app` (FastAPI TestClient)
- **Rewiring**:
  - Use `client = TestClient(app)`.
  - Make real requests: `client.get("/tren")` and `client.get("/api/tren")`.
  - Assert that original baseline text is preserved:
    - KPI card contains original text and percentage.
    - Section 1, 2, 3, 4 preserve baseline narrative.
  - When M5 is complete: assert presence of additive badge `Taksonomi Resmi: [label]` and verified CTI blocks.
  - Until M5 is complete: mark with `@unittest.skip("Pending M5 dashboard additive integration")`.

#### Class 8: `TestTier2BoundaryCases` (10 tests)
- **Target**: Real boundary conditions across `downloader.py`, `preparer.py`, `vector_store.py`, and `db.py`.
- **Rewiring**:
  - Replace simulated functions with real production calls:
    - STIX missing external_id -> call `flatten_attack_stix(bundle_with_missing_id)` -> verify skipped cleanly without error.
    - Empty D3FEND lookup -> call `ambil_d3fend_mitigasi_by_attack_id("T9999", db_path=self.db_path)` -> verify returns `[]`.
    - Duplicate article identifier -> call `simpan_intelijen_berita(record, db_path=self.db_path)` twice -> verify database handles collision cleanly.
    - Network timeout -> instantiate `CTIDownloader(timeout=0.001)` -> verify `DownloadError` raised.

#### Class 9: `TestTier3CrossFeatureCombinations` (25 tests)
- **Target**: Pairwise integration between real production modules.
- **Rewiring**:
  - P01: `CTIDownloader` download stream writing to disk and verifying SHA-256.
  - P02: Output of `flatten_attack_stix()` feeding into `CTIVectorStore`.
  - P04: `CLOSED_11_TAXONOMY_CATEGORIES` resolving to `ECSIRT_PARENT_MAPPINGS`.
  - P07: Attack technique ID querying real SQLite `ambil_d3fend_mitigasi_by_attack_id`.
  - P09: Intelligence record written to real SQLite via `simpan_intelijen_berita`.
  - P19: Revoked technique updating real SQLite via `tandai_flag_tinjauan_intelijen`.
  - P23: T1486 ransomware querying real D3-DBR mitigation from SQLite.
  - P24: T1566 phishing querying real D3-MFA mitigation from SQLite.
  - P25: Manual admin correction updating real SQLite via `simpan_koreksi_admin_intelijen`.

#### Class 10: `TestTier4RealWorldScenarios` (5 tests)
- **Target**: Full end-to-end operational scenarios executing real production modules.
- **Rewiring**:
  - **Scenario 1 (LockBit Ransomware on Regional Hospital)**:
    1. Validate category against `CLOSED_11_TAXONOMY_CATEGORIES`.
    2. Query real SQLite for mitigations via `ambil_d3fend_mitigasi_by_attack_id("T1486", db_path=self.db_path)`.
    3. Assert `mitigations[0]["technique_id"] == "D3-DBR"`.
    4. Persist result via `simpan_intelijen_berita(record, db_path=self.db_path)`.
    5. Query persisted record via `ambil_intelijen_berita("RSUD-LOCKBIT", db_path=self.db_path)` and assert integrity.
  - **Scenario 2 (Phishing APK Banking Fraud)**:
    1. Query real SQLite for mitigations via `ambil_d3fend_mitigasi_by_attack_id("T1566", db_path=self.db_path)`.
    2. Assert `mitigations[0]["technique_id"] == "D3-MFA"`.
    3. Persist and retrieve via `simpan_intelijen_berita`.
  - **Scenario 3 (Vague News / Server Maintenance)**:
    1. Verify abstention handling.
    2. Call `ambil_d3fend_mitigasi_by_attack_id("tidak_ditentukan", db_path=self.db_path)`.
    3. Assert returned mitigations list is `[]` (zero hallucinated mitigations).
  - **Scenario 4 (Periodic Upstream Update Revoking T1086)**:
    1. Insert historical incident using `T1086` via `simpan_intelijen_berita`.
    2. Execute real `tandai_flag_tinjauan_intelijen("T1086", "TEKNIK_REVOKED_PERLU_REVIEW", db_path=self.db_path)`.
    3. Retrieve record: verify `flag_tinjauan == "TEKNIK_REVOKED_PERLU_REVIEW"`, `mitre_technique_id == "T1086"` intact.
    4. Verify total incident count is unchanged (zero records deleted).
  - **Scenario 5 (Corrupted Upstream Download Drop Guard)**:
    1. When `src.cti.updater` is present: execute `detect_catastrophic_drop(old_count=834, new_count=5)`.
    2. Verify `DropDetectionError` raised and database remains unmodified.

---

### 4.3 Mutation Check Defense Table

The table below demonstrates how the rewired tests will genuinely detect and fail upon real mutations in `src/`:

| Mutation Target in `src/` | Injected Defect / Mutation | Affected Rewired Tests | Resulting Test Failure | Mutation Killed? |
|---------------------------|----------------------------|------------------------|------------------------|:----------------:|
| `src/cti/preparer.py` (`flatten_attack_stix`) | Comment out `if obj.get("revoked", False): continue` | `test_t1_f3_stix_filtering_revoked_techniques` | `AssertionError: 1 != 0` (revoked technique included) | **YES (KILLED)** |
| `src/cti/preparer.py` (`flatten_attack_stix`) | Comment out `if obj.get("x_mitre_deprecated", False): continue` | `test_t1_f3_stix_filtering_deprecated_techniques` | `AssertionError: 1 != 0` (deprecated technique included) | **YES (KILLED)** |
| `src/cti/preparer.py` (`generate_taxonomy_documents`) | Remove `"tidak_dapat_ditentukan"` category | `test_t1_f4_ecsirt_undetermined_mandatory_category` | `AssertionError: 'tidak_dapat_ditentukan' not in docs` | **YES (KILLED)** |
| `src/storage/db.py` (`ambil_d3fend_mitigasi_by_attack_id`) | Remove sub-technique fallback (`parent_id = clean_id.split('.')[0]`) | `test_t1_f5_d3fend_relational_join_query`, `test_t4_scenario_1` | `AssertionError: len(mitigations) == 0 != 1` | **YES (KILLED)** |
| `src/storage/db.py` (`ambil_d3fend_mitigasi_by_attack_id`) | Return hardcoded dummy mitigations for unmapped IDs | `test_t1_f12_d3fend_fallback_when_mapping_missing`, `test_t4_scenario_3` | `AssertionError: [...] != []` | **YES (KILLED)** |
| `src/storage/db.py` (`tandai_flag_tinjauan_intelijen`) | Change `UPDATE` statement to `DELETE` statement | `test_t1_f23_revoked_technique_never_deletes_records`, `test_t4_scenario_4` | `AssertionError: 0 != 1` (record was deleted) | **YES (KILLED)** |
| `src/storage/db.py` (`simpan_intelijen_berita`) | Drop `UNIQUE` constraint or overwrite admin corrections | `test_t1_f13_provenance_manual_correction_columns`, `test_t3_p25` | `AssertionError: original value overwritten` | **YES (KILLED)** |
| `src/cti/downloader.py` (`_download_stream_with_retry`) | Fail to compute SHA-256 during chunk stream | `test_t1_f1_sha256_calculation_and_verification`, `test_t3_p01` | `AssertionError: actual_sha != expected_sha` | **YES (KILLED)** |
| `src/cti/downloader.py` (`_download_stream_with_retry`) | Accept zero-byte empty response without error | `test_t1_f1_zero_byte_payload_rejection` | `AssertionError: DownloadError not raised` | **YES (KILLED)** |
| `src/cti/vector_store.py` (`CTIVectorStore`) | Allow cross-collection bleeding (search in wrong folder) | `test_t1_f7_three_separate_collections_isolation`, `test_t1_f7_collection_query_scoping` | `AssertionError: cross-collection item found` | **YES (KILLED)** |

---

## 5. Verification Method

To verify the implementation of this remediation plan:

1. **Verify Eradication of Fake Harness**:
   ```powershell
   Get-Content tests/test_cti_e2e_suite.py | Select-String -Pattern "CTIReferenceHarness|CTIAuthoritativeSpecs"
   ```
   *Expected Output*: Empty (0 matches). Both fake classes are completely removed.

2. **Verify Real Production Imports**:
   ```powershell
   Get-Content tests/test_cti_e2e_suite.py | Select-String -Pattern "from src\.cti|from src\.storage"
   ```
   *Expected Output*: Multiple lines showing imports of `CTIDownloader`, `CTIPreparer`, `flatten_attack_stix`, `ambil_d3fend_mitigasi_by_attack_id`, `CTIVectorStore`, etc.

3. **Verify Runtime Module Loading**:
   ```powershell
   python -c "import sys, unittest; suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_cti_e2e_suite'); runner = unittest.TextTestRunner(verbosity=0); runner.run(suite); loaded = [m for m in sys.modules if m.startswith('src')]; print('Loaded src modules count:', len(loaded)); print('Loaded src modules:', loaded[:5])"
   ```
   *Expected Output*: `Loaded src modules count: > 0` (e.g. `['src', 'src.cti', 'src.cti.downloader', 'src.cti.preparer', 'src.storage.db', ...]`).

4. **Verify Realistic Test Execution Duration**:
   ```powershell
   python -m pytest tests/test_cti_e2e_suite.py
   ```
   *Expected Output*: Execution takes several seconds (not 43ms), executing genuine SQLite, SHA-256 hashing, and vector math.

5. **Verify Baseline Tests Integrity (Zero Regressions)**:
   ```powershell
   python -m pytest --ignore=tests/test_cti_e2e_suite.py
   ```
   *Expected Output*: `36 passed in ~15s` (all 36 baseline tests continue to pass without regressions).
