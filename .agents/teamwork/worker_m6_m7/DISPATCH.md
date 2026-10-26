# Dispatch: Worker M6 & M7 (Periodic Updater & Evaluation Framework)

## Mission
Implement Milestone 6 (Periodic Update Scripts & Resiliency - Tahap 5, R4) and Milestone 7 (Evaluation Framework & Labeled Dataset - Tahap 6, R4).

## Working Directory
`D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m6_m7`

## Mandatory Reading
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md` (mandatory).
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\PROJECT.md`
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_pipeline\handoff.md` (Tahap 5 & 6 specs).
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m1_m2\handoff.md`.
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m3_m4\handoff.md`.

## CRITICAL CONSTRAINTS & WARNINGS
- Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
- All baseline tests in `python -m pytest tests/` MUST remain passing without regressions.
- MANDATORY INTEGRITY WARNING:
  DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Exclusive Write Ownership
You exclusively own and may edit:
- `src/cti/updater.py`
- `src/cti/evaluator.py`
- `scripts/update_attack.py`
- `scripts/update_d3fend.py`
- `scripts/update_nist.py`
- `scripts/update_taxonomy.py`
- `scripts/generate_evaluation_draft.py`
- `scripts/evaluate_pipeline.py`
- `data/evaluation/` (dataset directory)
- `tests/test_cti_m6_m7.py`
Do NOT edit `tests/test_cti_e2e_suite.py` or `src/web/`.

## Implementation Requirements

### Milestone 6: Periodic Update Scripts (Tahap 5, R4)
1. In `src/cti/updater.py`:
   - Implement `CTISourceUpdater`:
     - **Idempotent Version Checking**:
       - `check_version(source)`: Compares remote commit/tag/version.json against active version stored in `data/raw/<source>/latest` or `metadata_sistem`.
       - If unchanged, logs `"tidak ada pembaruan untuk <source> (versi aktif: <version>)"` and exits cleanly (exit code 0).
     - **Staging & Catastrophic Drop Guard**:
       - Downloads payload to `data/raw/<source>/<today>/`.
       - Validates schema and record count.
       - If `new_count == 0` or `new_count < (old_count * 0.70)` (>30% drop), raises `DropDetectionError`, aborts the update, and keeps the active index/database intact.
     - **Diff Reporting**:
       - Computes `added`, `modified`, `revoked` ID sets.
       - Emits report JSON to `data/reports/diff_<source>_<timestamp>.json`.
     - **Incremental Re-embedding & Atomic Swap**:
       - Only re-embeds documents in `added` and `modified`.
       - Creates `<collection>_vNext`, runs smoke test, swaps active pointer, retains `<collection>_vPrev` for rollback.
     - **Revoked Technique Historical Auditor**:
       - If ATT&CK technique is revoked, queries `intelijen_berita_tervalidasi` in `data/state.db`.
       - Calls `src.storage.db.tandai_flag_tinjauan_intelijen` with `"TEKNIK_REVOKED_PERLU_REVIEW"`.
       - **NEVER** deletes historical records.
     - **CLI Scripts**: `scripts/update_attack.py`, `scripts/update_d3fend.py`, `scripts/update_nist.py`, `scripts/update_taxonomy.py`.
     - Support proxy (`HTTP_PROXY`) and internal mirror (`--mirror-base-url`).

### Milestone 7: Evaluation Framework & Dataset (Tahap 6, R4)
2. In `src/cti/evaluator.py`:
   - **Dataset Draft Generator**:
     - `generate_draft_dataset(db_path, output_csv_path, sample_size=200)`:
       - Extracts news articles from `riwayat_tren` in `data/state.db`.
       - Analyzes using `CTINewsAnalyzer`.
       - Emits CSV/JSON marked clearly with `status_label = "DRAFT_PENDING_USER_REVIEW"`.
       - Leaves `verified_kategori` and `verified_mitre_id` columns empty for easy human correction.
     - CLI: `scripts/generate_evaluation_draft.py`.
   - **Evaluation Metric Calculator**:
     - `calculate_evaluation_metrics(csv_path)`:
       - Reads verified rows (where `verified_kategori` is non-empty).
       - Computes Precision, Recall, F1 per category, and Macro-F1.
       - Computes ATT&CK technique accuracy (`predicted_id == verified_id`).
       - Formats and displays tabular summary.
       - Re-runnable directly after human user corrects labels.
     - CLI: `scripts/evaluate_pipeline.py`.

3. Verification:
   - Run tests: ensure all existing tests pass (`python -m pytest tests/`).
   - Write comprehensive tests in `tests/test_cti_m6_m7.py`.
   - Document commands and outputs in `handoff.md`.


## 2026-10-20T16:23:14Z
Read D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md and D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m6_m7\DISPATCH.md. Your working directory is D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m6_m7. CRITICAL CONSTRAINTS: Do NOT touch and do NOT read Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx and the folder LAPORAN DASHBOARD ADMIN/. All baseline tests in tests/ must remain passing. MANDATORY INTEGRITY WARNING: DO NOT CHEAT. Implement Milestone 6: Periodic Update Engine (src/cti/updater.py with idempotent version checks, drop guard, diff reports, atomic swap, revoked technique flagger) and Milestone 7: Evaluation Framework (src/cti/evaluator.py with draft dataset generator from state.db and metric calculator). Run tests, and report in handoff.md.
