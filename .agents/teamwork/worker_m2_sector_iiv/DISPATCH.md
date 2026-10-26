# DISPATCH

## 2026-10-21T02:50:06Z
You are a Worker subagent (worker_m2_sector_iiv) for SiberHarian (CSIRT Diskominfo Jatim).
Your working directory is: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m2_sector_iiv

MANDATORY FIRST STEP:
Read the authoritative requirements file at: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md (especially section '## Follow-up — 2026-10-21T02:12:53Z').

CRITICAL CONSTRAINTS:
1. Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
2. MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
3. Exclusively owned files for this subtask:
   - `src/cti/preparer.py` (sector taxonomy constants)
   - `src/storage/db.py` (schema migration for intelijen_berita_tervalidasi)
   - `src/cti/analyzer.py` (sector classification & substring validation guard)
   - `src/cti/evaluator.py` (sector evaluation metrics & draft dataset generation)
   - `scripts/classify_weekly_sectors.py` (weekly batch runner)
   - `scripts/generate_evaluation_draft.py`
   - `scripts/evaluate_pipeline.py`
   - `tests/test_cti_sector_classification.py`

TASK SPECIFICATION (R4 - Sektor Target Terpapar 10 IIV Perpres 82/2022):
1. `src/cti/preparer.py`:
   - Define canonical 10 IIV sectors (Perpres 82/2022 Pasal 4):
     1. Administrasi Pemerintahan
     2. Energi & Sumber Daya Mineral
     3. Transportasi
     4. Keuangan & Perbankan
     5. Kesehatan
     6. Teknologi Informasi & Komunikasi (TIK)
     7. Pertahanan & Keamanan
     8. Pangan
     9. Pendidikan
     10. Layanan Publik & Pengguna Digital
     11. Tidak dapat ditentukan (mandatory fallback)
   - Export `CLOSED_10_IIV_SECTORS` and `IIV_SECTOR_DISPLAY_NAMES`.

2. `src/storage/db.py`:
   - In `init_db()`, non-destructively add columns to `intelijen_berita_tervalidasi` if not present:
     `sektor_target TEXT`, `confidence_sektor REAL`, `kutipan_bukti_sektor TEXT`, `alasan_sektor TEXT`, `koreksi_admin_sektor TEXT`.
   - Update `simpan_intelijen_berita()` and `ambil_intelijen_berita()` to store and load these fields.
   - Add `simpan_koreksi_admin_sektor(article_identifier, sektor, alasan)`.

3. `src/cti/analyzer.py`:
   - Implement `guard_sector_and_quote(sektor: str, kutipan_bukti: str, teks_berita: str) -> Tuple[str, str, float, bool]`:
     * Strict rule: If `sektor` is not in `CLOSED_10_IIV_SECTORS` or if `kutipan_bukti` is NOT an exact substring (case-insensitive, normalized whitespace) of `teks_berita`, REJECT hard and fallback to `"Tidak dapat ditentukan"` with quote `""` and confidence `0.0`.
     * If `sektor == "Tidak dapat ditentukan"`, quote is `""` and is valid.
   - Implement `classify_sector(article: Dict[str, Any]) -> Dict[str, Any]`:
     * Uses LLM with structured prompt when online.
     * Offline/deterministic fallback: matches keywords against canonical sector rules and extracts the exact containing sentence as `kutipan_bukti` (guaranteed exact substring!).
     * Runs through `guard_sector_and_quote`.
   - In `analyze_news()`, call sector classification and attach `sektor_target`, `confidence_sektor`, `kutipan_bukti_sektor`, `alasan_sektor` to the intelligence record.

4. `scripts/classify_weekly_sectors.py`:
   - Create script that loads all news from the past 7 days from `data/state.db`, classifies their victim sector, validates evidence quotes, and stores results into `intelijen_berita_tervalidasi`.

5. `src/cti/evaluator.py`, `scripts/generate_evaluation_draft.py`, and `scripts/evaluate_pipeline.py`:
   - Update `generate_draft_dataset()`: add `prediksi_sektor`, `confidence_sektor`, `kutipan_bukti_sektor`, `verified_sektor` (empty for user correction), `status_label` ("DRAFT_PENDING_USER_REVIEW").
   - Update `calculate_evaluation_metrics()`: when `verified_sektor` is filled, calculate Precision, Recall, F1 per sector, overall sector accuracy, and evidence quote validity rate.

6. `tests/test_cti_sector_classification.py`:
   - Unit tests covering:
     * Closed 10 IIV + fallback constraint.
     * Exact substring validation guard (valid substring accepted; altered/hallucinated quote rejected).
     * Out-of-list sector rejection.
     * Weekly batch classification execution.
     * Evaluation metric calculations (Precision, Recall, F1).
   - Run: `python -m pytest tests/test_cti_sector_classification.py`.
