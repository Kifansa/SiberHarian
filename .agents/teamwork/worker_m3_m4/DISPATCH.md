# Dispatch: Worker M3 & M4 (Vector Indexing & News Analysis Pipeline)

## Mission
Implement Milestone 3 (RAG Multilingual Vector Indexing) and Milestone 4 (Per-News Processing Pipeline & Guardrails) for the SiberHarian CTI Layer.

## Working Directory
`D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m3_m4`

## Mandatory Reading
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md` (mandatory).
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\PROJECT.md`
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_pipeline\handoff.md`
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m1_m2\handoff.md`

## CRITICAL CONSTRAINTS & WARNINGS
- Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
- All existing tests in `python -m pytest tests/` MUST remain passing without regressions.
- MANDATORY INTEGRITY WARNING:
  DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
- D3FEND MUST NOT be placed into vector store. Lookups must be deterministic via `src.storage.db.ambil_d3fend_mitigasi_by_attack_id`.
- The 9 non-specified encyclopedia files (`bssn`, `owasp`, etc.) are officially removed per user decision; do NOT depend on them.

## Exclusive Write Ownership
You exclusively own and may create/edit:
- `src/cti/vector_store.py`
- `src/cti/analyzer.py`
- `src/storage/db.py` (add `intelijen_berita_tervalidasi` DDL and helper methods; do NOT break existing functions)
- `tests/test_cti_m3_m4.py`
Do NOT edit `tests/test_cti_e2e_suite.py` or `src/cti/downloader.py` or `src/cti/preparer.py`.

## Implementation Requirements

### Milestone 3: RAG Multilingual Vector Indexing (Tahap 3, R1)
1. In `src/cti/vector_store.py`:
   - Create `CTIVectorStore` managing 3 separate collections:
     - `collection_attack`: indexes 706 active techniques from `data/prepared/attack_techniques.json`.
     - `collection_taxonomy`: indexes 11 closed category docs from `data/prepared/taxonomy_categories.json`.
     - `collection_nist`: indexes 1,381 control docs from `data/prepared/nist_controls.json`.
   - Embeddings: Integrate with `src.utils.llm_adapter.GeminiLLMAdapter` (model `gemini-embedding-001`, dimension 768, fallback chain) and support cosine similarity ranking with persistent local vector caching in `data/vector_stores/`. Include a fast offline/local fallback embedding for deterministic unit testing and environments without Gemini API key.
   - Dual-text translation strategy:
     - Articles store both original Indonesian text and English technical translation.
     - Taxonomic retrieval can query both; ATT&CK and NIST retrieval strictly query the English translation for semantic alignment.

### Milestone 4: Per-News Processing Pipeline & Guardrails (Tahap 4, R2)
2. In `src/cti/analyzer.py`:
   - Implement `CTINewsAnalyzer`:
     a. **Incident Classification**: Retrieves top candidates from `collection_taxonomy`, prompts LLM to choose SATU label utama from the 11 closed categories. Output structured JSON: `kategori_utama`, `confidence`, `kutipan_bukti`, `alasan`, `id_taksonomi_induk`. Mandatory fallback to `"Tidak Dapat Ditentukan"` when evidence is absent/weak.
     b. **Conditional ATT&CK Extraction**:
        - Checks if news describes attack flow (*cara/alur serangan*).
        - If NO attack flow: abstains, returns `{"status": "tidak_ditentukan", "tactic": null, "technique_id": null}`. Dilarang menebak!
        - If attack flow present: retrieves top-15 from `collection_attack`, LLM selects technique with evidence quote. If evidence is weak, stops at tactic level.
     c. **Active ATT&CK Validation Guardrail**:
        - Validates technique ID against active 706 techniques.
        - If ID is missing, fake (e.g. T9999), or revoked (e.g. T1183), REJECTS the ID, logs audit warning, and sets `technique_id = "tidak_ditentukan"`.
     d. **Deterministic D3FEND Mitigation Lookup**:
        - For validated technique ID, calls `ambil_d3fend_mitigasi_by_attack_id(technique_id)` from `src.storage.db`.
        - ZERO LLM additions! Output displayed as general mitigation advice for the related technique.
     e. **NIST Reference Lookup**: On-demand retrieval of SP 800-53 and CSF 2.0 controls.
     f. **Provenance Storage**:
        - Creates and writes to table `intelijen_berita_tervalidasi` in `data/state.db`:
          `article_identifier`, `kategori_insiden`, `confidence_kategori`, `kutipan_bukti_kategori`, `mitre_tactic`, `mitre_technique_id`, `mitre_technique_name`, `confidence_mitre`, `kutipan_bukti_mitre`, `d3fend_mitigasi_json`, `nist_referensi_json`, `version_taxonomy`, `version_attack`, `version_d3fend`, `version_nist`, `dibuat_pada`, `koreksi_admin_kategori`, `koreksi_admin_technique_id`, `koreksi_admin_catatan`, `koreksi_admin_oleh`, `koreksi_admin_pada`.

3. Verification:
   - Run tests: ensure all existing tests pass (`python -m pytest tests/`).
   - Write comprehensive unit tests in `tests/test_cti_m3_m4.py`.
   - Document commands and results in `handoff.md`.


## 2026-10-20T16:00:13Z
Read D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md and D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m3_m4\DISPATCH.md. Your working directory is D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m3_m4. CRITICAL CONSTRAINTS: Do NOT touch and do NOT read Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx and the folder LAPORAN DASHBOARD ADMIN/. All existing tests in tests/ must remain passing. MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected. D3FEND must NOT be in vector store (deterministic SQL lookup only). Implement Milestone 3 (src/cti/vector_store.py) and Milestone 4 (src/cti/analyzer.py) per DISPATCH.md, run tests, and report in handoff.md.
