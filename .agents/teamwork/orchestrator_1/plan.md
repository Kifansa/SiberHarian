# SiberHarian CTI Intelligence Layer Upgrade — Master Plan

## Overview
Upgrade the existing SiberHarian CSIRT Diskominfo Jatim notification system to integrate an authoritative CTI (Cyber Threat Intelligence) layer based on MISP/ENISA taxonomies, MITRE ATT&CK Enterprise, MITRE D3FEND, and NIST OSCAL. Preserves all 36 existing tests and integrates into the existing admin dashboard in a strictly additive manner.

## Special User Constraints & Handling (R0)
1. **9 Unspecified Encyclopedia Files**:
   - `bssn.json`, `owasp.json`, `cwe.json`, `cis_controls.json`, `iso27001.json`, `csa_ccm.json`, `cisa_cpg.json`, `indeks_kami.json`, `csirt_framework.json`.
   - **Constraint**: DO NOT replace or delete before user confirmation.
   - **Action**: Prepare proposal containing:
     - Proposed authoritative source for each file.
     - Option to retain as legacy fallback vs replace from official source vs deprecate.
     - Route proposal to Sentinel for user decision.
2. **Feature Overlap Management**:
   - *Overlap 1: Modul 4 Rekomendasi Aksi*: Currently uses keyword search on `data/encyclopedia/*.json`. Proposal: Maintain existing recommendation output intact; append a distinct block titled **"Saran Mitigasi Terverifikasi MITRE D3FEND"** and **"Referensi Standar NIST Tambahan"**.
   - *Overlap 2: KPI Pola Ancaman*: Currently uses regex/organic threat extraction. Proposal: Keep current organic text and percentage growth intact; add a badge/sub-line titled **"Taksonomi Resmi: [ Kategori ] (Keyakinan: X%)"**.
   - **Constraint**: Propose design to Sentinel/User before altering any behavior.

## Key Phases & Milestones

### Phase 0: Comprehensive Survey & Specification Mining [COMPLETED]
- Survey completed by Codebase Explorer, CTI Sources Spec Miner, and Pipeline Spec Miner.
- `PROJECT.md` and `TEST_INFRA.md` published at project root.

### Phase 1: Dual Track Launch
- **Track A (E2E Testing)**: Dispatch `teamwork_preview_test_writer` to build 4-tier opaque-box test suite in `tests/test_cti_e2e_suite.py` and publish `TEST_READY.md`.
- **Track B (User Consultation)**: Submit proposal on 9 encyclopedia files and 2 overlap points to Sentinel.

### Phase 2: Implementation Track (Sequential Milestones)
- **Milestone 1**: CTI Download & Staging Pipeline (Tahap 1, R1)
  - Staging scripts for MISP, ATT&CK, D3FEND, NIST with timeouts, retries, SHA-256 checksums, and proxy/mirror support.
- **Milestone 2**: Data Prep & Relational/Doc Stores (Tahap 2, R1)
  - STIX flattener (filtering revoked/deprecated), eCSIRT 11 closed category docs, D3FEND SQLite relational mapping table (deterministic lookup, strictly non-vector), NIST OSCAL control docs.
- **Milestone 3**: Multilingual RAG Vector Indexing (Tahap 3, R1)
  - 3 separate collections (`collection_attack`, `collection_taxonomy`, `collection_nist`), `gemini-embedding-001` adapter with fallbacks, translated text retrieval.
- **Milestone 4**: Per-News CTI Analysis Pipeline & Guardrails (Tahap 4, R2)
  - Incident classifier with structured JSON, conditional ATT&CK extraction (only if attack flow exists), active ATT&CK ID validation guard, deterministic D3FEND lookup, provenance table `intelijen_berita_tervalidasi`.
- **Milestone 5**: Additive Admin Dashboard Integration (Tahap 4 & R3)
  - Strictly additive display at the 5 specified points.
- **Milestone 6**: Periodic Update Pipeline & Safety (Tahap 5, R4)
  - Idempotent version check, staging drop guard (>30% drop rejected), diff reporting, incremental re-embedding, atomic swap with rollback, revoked technique historical audit flagger.
- **Milestone 7**: Evaluation Framework & Draft Dataset (Tahap 6, R4)
  - Draft dataset extraction from `riwayat_tren` (`data/state.db`) with `DRAFT_PENDING_USER_REVIEW`, evaluation calculator for Precision, Recall, F1, and ATT&CK accuracy.

### Phase 3: Final Acceptance, Verification & Hardening
- Verification that all 36 original tests pass.
- Verification that 100% of E2E test suite passes.
- Tier 5 Adversarial Coverage Hardening (Challenger loop).
- Forensic Integrity Audit (`teamwork_preview_auditor`) with ZERO TOLERANCE.
- Final completion report to Sentinel.
