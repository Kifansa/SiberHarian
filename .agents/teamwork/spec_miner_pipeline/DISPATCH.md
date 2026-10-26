# Dispatch: Spec Miner Pipeline

## Mission
Analyze requirements and specify technical design for data preparation, relational/vector stores, per-news classification/enrichment pipeline, periodic update pipeline, and evaluation framework.

## Working Directory
`D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_pipeline`

## Mandatory Reading
Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md` before starting.

## CRITICAL CONSTRAINTS
- Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
- Produce your comprehensive report in `handoff.md` in your working directory.

## Investigation Scope
1. Tahap 1 & 2 Data Preparation & Storage Architecture:
   - Staging directory structure (`data/raw/<sumber>/<tanggal>/`), version metadata schema, SHA-256 verification.
   - STIX flattening schema: id (T-number), name, tactic, description, platform, revoked/deprecated filter.
   - Taxonomy document schema: name, definition, news examples.
   - D3FEND relational table schema: ATT&CK ID -> D3FEND technique list (id, name, definition, tactic). Confirm SQLite relational table design for deterministic mitigation lookup.
   - NIST document schema: control/subcat id, title, statement, family/function.
   - Mandatory document metadata schema: source, source_version, original_id, ingest_date.
2. Tahap 3 RAG Vector Indexing:
   - Separate vector collections: (a) ATT&CK, (b) taxonomy, (c) NIST.
   - Technical justification for `gemini-embedding-001` handling Indonesian-English multilingual text.
   - Strategy for storing original vs translated news text and performing retrieval on translated text.
3. Tahap 4 News Processing Pipeline:
   - Structured JSON output schema for incident classification (primary label, confidence 0-1, news evidence quote, brief rationale, handling of "tidak dapat ditentukan").
   - Conditional ATT&CK extraction (only if news describes attack flow), top-k retrieval, stop at tactic or return "tidak ditentukan" if evidence is weak.
   - Active ATT&CK technique validation guard: reject hallucinated/inactive IDs.
   - Deterministic D3FEND lookup: strictly enforce no LLM additions.
   - Provenance storage schema: record versions used (ATT&CK, D3FEND, NIST, taxonomy) and manual correction columns.
4. Tahap 5 Periodic Update Specification:
   - Version checking mechanism per source (git commit/tag, D3FEND /api/version.json).
   - Staging validation (drop detection, empty staging rejection).
   - Diff report generator (new, modified, revoked techniques).
   - Incremental re-embedding and atomic index switch (with rollback support).
   - Revoked technique audit flagger: flag historical incidents without silent deletion.
   - Cron/systemd and proxy/internal mirror configuration support.
5. Tahap 6 Evaluation Framework Specification:
   - Schema and format for draft labeled dataset from `data/state.db`.
   - Metrics calculation: precision, recall, F1 per category, ATT&CK technique accuracy.
   - Re-run capability when prompt, model, embedding, or data version changes.

Deliver your findings in `handoff.md` in your working directory and notify the orchestrator when complete.


## 2026-10-20T15:27:10Z
Read D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md and D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_pipeline\DISPATCH.md. Your working directory is D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_pipeline. CRITICAL: Do NOT touch and do NOT read Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx and the folder LAPORAN DASHBOARD ADMIN/. Detail technical design specifications for Tahap 1-6 and Requirements R0-R4. Produce handoff.md in your working directory and notify the orchestrator when finished.
