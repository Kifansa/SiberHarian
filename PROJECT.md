# Project: SiberHarian CTI Intelligence Layer Upgrade

## Architecture
The SiberHarian CTI intelligence layer upgrade augments the existing CSIRT Diskominfo Jawa Timur news monitoring portal with an authoritative threat intelligence layer.
- **Authoritative Data Sources**:
  Per official user decision (R0), the 9 synthetic encyclopedia files (`bssn`, `indeks_kami`, `csirt_framework`, `owasp`, `cwe`, `cis_controls`, `iso27001`, `csa_ccm`, `cisa_cpg`) are officially removed. The system strictly standardizes on 4 authoritative pillars:
  1. **MISP / ENISA eCSIRT Incident Taxonomy** (`ecsirt/machinetag.json`)
  2. **MITRE ATT&CK Enterprise STIX 2.1** (`enterprise-attack.json`)
  3. **MITRE D3FEND JSON API** (`/api/version.json` & `/ontologies/d3fend/{version}/d3fend-full-mappings.json`)
  4. **NIST OSCAL Catalogs** (SP 800-53 Rev 5 & CSF 2.0)

- **Data Flow**:
  1. **Download & Staging (Tahap 1)**: Ingests raw payloads from official sources into `data/raw/<source>/<date>/` with metadata JSON (version, URL, timestamp, SHA-256).
  2. **Data Preparation & Storage (Tahap 2)**:
     - ATT&CK STIX 2.1: Flattened into text documents (T-number, name, tactic, description, platform), filtering out revoked/deprecated.
     - Incident Taxonomy: 11 closed categories derived from MISP/ENISA eCSIRT taxonomy.
     - MITRE D3FEND: Ingested into SQLite relational tables (`d3fend_techniques`, `d3fend_attack_mappings`) for deterministic SQL lookups (strictly non-vector).
     - NIST OSCAL: Flattened into control documents (SP 800-53 Rev 5 & CSF 2.0).
  3. **RAG Multilingual Vector Indexing (Tahap 3)**:
     - 3 separate vector collections: `collection_attack`, `collection_taxonomy`, `collection_nist`.
     - Multilingual embedding via `gemini-embedding-001` (with fallbacks `gemini-embedding-exp-03-07`, `text-embedding-004`).
     - Dual-text strategy: news articles retain Indonesian text; technical English translation is generated for retrieval against ATT&CK and NIST.
  4. **Per-News Analysis Pipeline & Guardrails (Tahap 4)**:
     - Incident Classification: Structured JSON output against closed 11 categories (including "Tidak Dapat Ditentukan").
     - Conditional ATT&CK Extraction: Triggered ONLY if attack flow is described in news.
     - Active ATT&CK Validation Guard: Enforces that any technique ID emitted by LLM belongs to active enterprise ATT&CK set.
     - Deterministic D3FEND Mitigation Lookup: Exact SQL query join from validated ATT&CK ID to D3FEND techniques; zero LLM additions.
     - Provenance & Manual Correction: Stored in `intelijen_berita_tervalidasi` table.
  5. **Additive Admin Dashboard Integration (R3)**:
     - Enriches 5 display points without deleting or modifying any existing text:
       1. KPI `[ POLA ANCAMAN ]`: Appends badge `Taksonomi Resmi: [label]` (without confidence percentage, per user decision).
       2. Section 1 `INSIDEN MELONJAK DRASTIS`: Appends verified eCSIRT distribution summary.
       3. Section 2 `TREN INSIDEN MINGGUAN`: Appends verified incident taxonomy tags to the 3 weekly micro-incidents.
       4. Section 3 `VEKTOR SERANGAN TREN INSIDEN MINGGUAN`: Appends verified MITRE ATT&CK Enterprise techniques with evidence.
       5. Section 4 `REKOMENDASI AKSI`: Appends deterministic D3FEND mitigations and NIST control references.
  6. **Periodic Update Engine (Tahap 5)**:
     - Idempotent version check per source, catastrophic drop detection (>30% drop rejected), diff reporting, incremental re-embedding, atomic swap with rollback retention, and historical revoked technique audit flagging.
  7. **Evaluation Framework (Tahap 6)**:
     - Automated generation of draft labeled dataset from `data/state.db` marked `DRAFT_PENDING_USER_REVIEW`.
     - Evaluation runner computing Precision, Recall, F1 per category, and ATT&CK accuracy.

## Feature Inventory
| # | Feature | Description | Milestone | Source |
|---|---------|-------------|-----------|--------|
| 1 | Raw Data Downloaders & Staging | Ingestion scripts for MISP, ATT&CK, D3FEND, NIST with retry, timeout, SHA-256 and metadata logs | M1 | Tahap 1, R1 |
| 2 | Network Resilience & Mirrors | Support for proxy (HTTP/HTTPS) and internal government mirror URLs | M1 | R0, Tahap 1 |
| 3 | MITRE ATT&CK STIX 2.1 Flattener | Parses STIX 2.1 bundle, filters revoked/deprecated, flattens to active technique documents | M2 | Tahap 2, R1 |
| 4 | eCSIRT Incident Taxonomy Corpus | Generates 11 closed category documents mapped to eCSIRT parents | M2 | Tahap 2, R1 |
| 5 | D3FEND Relational Store | SQLite tables (`d3fend_techniques`, `d3fend_attack_mappings`) for deterministic SQL lookups | M2 | Tahap 2, R1 |
| 6 | NIST OSCAL Control Flattener | Flattens NIST SP 800-53 Rev 5 and CSF 2.0 catalogs into searchable control documents | M2 | Tahap 2, R1 |
| 7 | Multi-Collection Vector Engine | 3 isolated collections (`collection_attack`, `collection_taxonomy`, `collection_nist`) with metadata | M3 | Tahap 3, R1 |
| 8 | Multilingual Embedding & Dual-Text | `gemini-embedding-001` integration with translated query retrieval for ATT&CK/NIST | M3 | Tahap 3, R1 |
| 9 | Structured JSON Incident Classifier | LLM classification into closed 11 categories with confidence, quote, and mandatory undetermined option | M4 | Tahap 4, R2 |
| 10 | Conditional ATT&CK Extractor | Extracts technique only when attack flow is present; stops at tactic or undetermined if weak | M4 | Tahap 4, R2 |
| 11 | Active ATT&CK Validation Guard | Validates technique IDs against active set; rejects and logs hallucinated/inactive IDs | M4 | Tahap 4, R2 |
| 12 | Deterministic D3FEND Lookup | SQL-only mitigation lookup based on validated ATT&CK ID; zero LLM additions | M4 | Tahap 4, R2 |
| 13 | Provenance & Manual Correction Store | Schema and persistence in `intelijen_berita_tervalidasi` recording source versions and admin edits | M4 | Tahap 4, R2 |
| 14 | Additive KPI `[ POLA ANCAMAN ]` | Appends validated taxonomy badge `Taksonomi Resmi: [label]` to KPI card without altering existing text | M5 | R3 |
| 15 | Additive Section 1 Lonjakan Insiden | Appends validated eCSIRT distribution summary to macro incident section | M5 | R3 |
| 16 | Additive Section 2 Tren Mingguan | Appends validated incident taxonomy tags to the 3 weekly micro-incidents | M5 | R3 |
| 17 | Additive Section 3 Vektor Serangan | Appends verified MITRE ATT&CK Enterprise techniques with evidence to attack vector section | M5 | R3 |
| 18 | Additive Section 4 Rekomendasi Aksi | Appends deterministic D3FEND mitigations and NIST control references to action section | M5 | R3 |
| 19 | Periodic Source Update Scripts | Modular update scripts for ATT&CK, D3FEND, NIST, MISP with idempotent version checks | M6 | Tahap 5, R4 |
| 20 | Staging Validation & Drop Guard | Detects empty or >30% record drop, aborts update, keeps current index intact | M6 | Tahap 5, R4 |
| 21 | Diff Reporter & Incremental Embed | Computes added/modified/revoked diff and re-embeds only modified/added records | M6 | Tahap 5, R4 |
| 22 | Atomic Index Swap & Rollback | Generates `vNext` index, runs smoke test, swaps pointer, retains `vPrev` for 24h rollback | M6 | Tahap 5, R4 |
| 23 | Revoked Technique Audit Flagger | Flags historical incidents referencing revoked techniques without deleting records | M6 | Tahap 5, R4 |
| 24 | Evaluation Dataset Generator | Extracts 200-500 draft cases from `riwayat_tren` marked `DRAFT_PENDING_USER_REVIEW` | M7 | Tahap 6, R4 |
| 25 | CTI Evaluation Metric Calculator | Computes Precision, Recall, F1 per category, and ATT&CK accuracy on verified dataset | M7 | Tahap 6, R4 |
| 26 | Comprehensive E2E Test Suite | 4-tier opaque-box test suite verifying all CTI features and backward compatibility | M_E2E | Acceptance Criteria |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M_E2E | E2E Testing Suite Track | Design and implement 4-tier comprehensive opaque-box test harness (Tiers 1-4) | none | DONE |
| M1-M7 | Core CTI Intelligence Layer | Tahap 1 to Tahap 6 implementation (Downloader, Preparer, Vector, Analyzer, Dashboard, Updater, Evaluator) | none | DONE |
| M_UPGRADE_M3 | R3 SITREP Option A Remediation | Remove all hardcoded fallbacks (T1190, D3-MFA, AC-2, fake distributions) across all 5 SITREP points. Publish AUDIT_HARDCODE_DAN_LOGIKA_TERARAH.md | none | DONE |
| M_UPGRADE_M1 | R1 & R2 KPI Backend & UI | Closed 11 eCSIRT category for Pola Ancaman; remove redundant badge; Sinyal Ancaman Baru novelty > volume with >= 2 cases | none | DONE |
| M_UPGRADE_M2 | R4 IIV Sector Classification | 10 IIV sectors Perpres 82/2022 + 'Tidak dapat ditentukan', exact substring quote guard, batch runner, evaluator | none | DONE |
| M_UPGRADE_M4 | Dynamic Multi-Dataset Acceptance | Automated test verifying dynamic shift across 2 distinct datasets for Pola, Sinyal, and Sektor | M_UPGRADE_M1, M_UPGRADE_M2 | DONE |
| M_GATE | Gate Certification & Forensic Audit | Reviewer (2x), Challenger (2x), and Forensic Auditor (1x) verification with zero hardcode tolerance | M_UPGRADE_M4 | IN_PROGRESS |

## Interface Contracts

### CTI Downloader ↔ Data Staging
- Downloader outputs files into `data/raw/<source_name>/<YYYY-MM-DD>/`.
- Accompanying `metadata.json`:
  ```json
  {
    "source_name": "mitre_attack",
    "source_url": "...",
    "download_timestamp_utc": "ISO8601",
    "version_identifier": "string",
    "file_sha256": "string",
    "file_size_bytes": 12345,
    "record_count_parsed": 834,
    "download_status": "SUCCESS"
  }
  ```

### Data Preparation ↔ Vector & Relational Storage
- ATT&CK flattened record: `{"technique_id": "T1566", "name": "Phishing", "tactics": ["Initial Access"], "description": "...", "platforms": ["Windows", "Linux"], "source_version": "v20.0"}`
- D3FEND relational table schema in `data/state.db`:
  - `d3fend_techniques`: `(technique_id PRIMARY KEY, name, tactic, definition, source_version, updated_at)`
  - `d3fend_attack_mappings`: `(id INTEGER PK AUTOINCREMENT, attack_technique_id, d3fend_technique_id, relationship_type, source_version)`
- Incident Taxonomy closed categories (11 categories):
  - `ransomware`, `data_breach`, `defacement`, `ddos`, `phishing_penipuan`, `malware`, `eksploitasi_kerentanan`, `akses_tidak_sah`, `pelecehan_konten`, `lainnya`, `tidak_dapat_ditentukan`

### Pipeline Analyzer ↔ Dashboard Generator
- Analyzed news intel record schema:
  ```json
  {
    "kategori_utama": "Ransomware",
    "kategori_tambahan": null,
    "confidence_kategori": 0.94,
    "kutipan_bukti_kategori": "...",
    "mitre_tactic": "Initial Access",
    "mitre_technique_id": "T1566",
    "mitre_technique_name": "Phishing",
    "confidence_mitre": 0.88,
    "kutipan_bukti_mitre": "...",
    "d3fend_mitigasi": [
      {"id": "D3-MFA", "name": "Multi-Factor Authentication", "tactic": "Credential Access Defense", "definition": "..."}
    ],
    "nist_referensi": [
      {"id": "AC-2", "title": "Account Management", "framework": "SP 800-53 Rev 5", "statement": "..."}
    ],
    "version_info": {
      "taxonomy": "ecsirt-2026",
      "attack": "v20.0",
      "d3fend": "1.6.0",
      "nist": "SP800-53-Rev5"
    }
  }
  ```

## Code Layout
- `src/cti/`: Dedicated module for CTI intelligence layer:
  - `downloader.py`: Downloader and staging engine for MISP, ATT&CK, D3FEND, NIST.
  - `preparer.py`: Parsers for STIX 2.1, OSCAL, D3FEND mappings, and taxonomy.
  - `vector_store.py`: Multi-collection vector store management.
  - `analyzer.py`: News CTI enrichment, validation guards, and deterministic lookups.
  - `updater.py`: Periodic update workflows, drop guards, diff reports, atomic swap.
  - `evaluator.py`: Evaluation metrics, dataset generator, and benchmark runner.
- `src/storage/db.py`: Migration additions for CTI tables (`d3fend_techniques`, `d3fend_attack_mappings`, `intelijen_berita_tervalidasi`).
- `src/analytics/cti_agents.py`: Additive markdown enrichment for Sections 1, 2, 3, 4.
- `src/analytics/rag_engine.py`: Additive integration for KPI `[ POLA ANCAMAN ]`.
- `tests/test_cti_*.py`: Modular test suites for CTI intelligence layer.
- `tests_e2e/`: Opaque-box E2E test suite (Tiers 1-4).
