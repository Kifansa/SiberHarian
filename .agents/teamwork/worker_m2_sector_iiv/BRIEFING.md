# BRIEFING — 2026-10-21T03:13:30Z

## Mission
Implement R4: Sektor Target Terpapar 10 IIV Perpres 82/2022 with rigorous substring validation, database migration, weekly classification script, evaluation metrics, and unit tests.

## 🔒 My Identity
- Archetype: worker
- Roles: implementer, qa, specialist
- Working directory: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m2_sector_iiv
- Original parent: e7dc208b-024f-412d-993f-55ea0f0598d7
- Milestone: M2 - Sektor Target Terpapar 10 IIV

## 🔒 Key Constraints
- Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
- MANDATORY INTEGRITY WARNING: No cheating, no dummy/facade implementations, no hardcoding test results.
- Exclusively owned files:
  * `src/cti/preparer.py`
  * `src/storage/db.py`
  * `src/cti/analyzer.py`
  * `src/cti/evaluator.py`
  * `scripts/classify_weekly_sectors.py`
  * `scripts/generate_evaluation_draft.py`
  * `scripts/evaluate_pipeline.py`
  * `tests/test_cti_sector_classification.py`

## Current Parent
- Conversation ID: e7dc208b-024f-412d-993f-55ea0f0598d7
- Updated: 2026-10-21T03:13:30Z

## Task Summary
- **What to build**: 
  1. Define canonical 10 IIV sectors (Perpres 82/2022 Pasal 4) + fallback in `src/cti/preparer.py`.
  2. Database migration and CRUD in `src/storage/db.py` for `sektor_target`, `confidence_sektor`, `kutipan_bukti_sektor`, `alasan_sektor`, `koreksi_admin_sektor`.
  3. Strict substring evidence guard and sector classification in `src/cti/analyzer.py`.
  4. Weekly sector batch script in `scripts/classify_weekly_sectors.py`.
  5. Evaluation metrics and draft dataset generation in `src/cti/evaluator.py`, `scripts/generate_evaluation_draft.py`, and `scripts/evaluate_pipeline.py`.
  6. Comprehensive test suite in `tests/test_cti_sector_classification.py`.
- **Success criteria**: All sector classification tests pass (19/19 passed), substring guard strictly enforces exact substring or rejects to fallback, database columns persist properly, and existing tests don't regress.

## Key Decisions Made
- Canonical sectors in `src/cti/preparer.py`: 10 official Perpres 82/2022 sectors + "Tidak dapat ditentukan".
- Substring guard: rejects hard to "Tidak dapat ditentukan" with quote "" and confidence 0.0 if sector is out-of-list or quote is not an exact substring (case-insensitive, normalized whitespace) of the news text.
- Fallback sector "Tidak dapat ditentukan" is considered valid with empty quote.
- Offline sector classification: extracts the exact containing sentence slice directly from news text, guaranteeing substring validity.
- Evaluation metrics: calculates Precision, Recall, F1 per sector, overall sector accuracy, and evidence quote validity rate.

## Artifact Index
- `.agents/teamwork/worker_m2_sector_iiv/DISPATCH.md` — Dispatch requirements
- `.agents/teamwork/worker_m2_sector_iiv/progress.md` — Heartbeat and progress tracking
- `.agents/teamwork/worker_m2_sector_iiv/BRIEFING.md` — Agent working memory
- `.agents/teamwork/worker_m2_sector_iiv/handoff.md` — Final handoff report (complete)

## Change Tracker
- **Files modified**:
  * `src/cti/preparer.py`: Added `CLOSED_10_IIV_SECTORS`, `IIV_SECTOR_DISPLAY_NAMES`, `InvalidSectorError`.
  * `src/storage/db.py`: Added columns `sektor_target`, `confidence_sektor`, `kutipan_bukti_sektor`, `alasan_sektor`, `koreksi_admin_sektor` and `simpan_koreksi_admin_sektor()`.
  * `src/cti/analyzer.py`: Added `guard_sector_and_quote()`, `classify_sector()`, and integrated into `analyze_news()`.
  * `scripts/classify_weekly_sectors.py`: Created weekly batch runner.
  * `src/cti/evaluator.py`: Updated `generate_draft_dataset()` and `calculate_evaluation_metrics()`.
  * `scripts/generate_evaluation_draft.py`: Updated CLI instructions.
  * `scripts/evaluate_pipeline.py`: Added sector evaluation reporting.
  * `tests/test_cti_sector_classification.py`: Created 19 comprehensive unit tests.
  * `data/evaluation/dataset_evaluasi_sampel_terverifikasi.csv`: Created verified sample dataset.
- **Build status**: passed (270/270 passed, 0 failures across full pytest suite)
- **Pending issues**: None

## Quality Status
- **Build/test result**: 270 passed (including 19 new sector classification tests)
- **Lint status**: clean
- **Tests added/modified**: 19 new tests in `tests/test_cti_sector_classification.py`

## Loaded Skills
- None


