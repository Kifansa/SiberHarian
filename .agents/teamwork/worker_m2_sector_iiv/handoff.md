# Handoff Report - Milestone M2 (R4): Sektor Target Terpapar 10 IIV

## 1. Observation
### File Locations and Verified Code Implementations
- **`src/cti/preparer.py` (lines 25-56)**:
  - Canonical `CLOSED_10_IIV_SECTORS` tuple with 11 members: 10 sectors mandated by Perpres No. 82/2022 Pasal 4 (`"Administrasi Pemerintahan"`, `"Energi dan Sumber Daya Mineral"`, `"Transportasi"`, `"Keuangan"`, `"Kesehatan"`, `"Teknologi Informasi dan Komunikasi"`, `"Pangan"`, `"Pertahanan"`, `"Penegakan Hukum"`, `"Layanan Publik & Pengguna Digital"`) plus mandatory fallback `"Tidak dapat ditentukan"`.
  - Exported mapping `IIV_SECTOR_DISPLAY_NAMES` and custom exception `InvalidSectorError`.
- **`src/storage/db.py` (lines 161-165, 218-223, 320-353)**:
  - Non-destructive migration columns added to `intelijen_berita_tervalidasi`: `sektor_target TEXT DEFAULT 'Tidak dapat ditentukan'`, `confidence_sektor REAL DEFAULT 0.0`, `kutipan_bukti_sektor TEXT DEFAULT ''`, `alasan_sektor TEXT DEFAULT ''`, `koreksi_admin_sektor TEXT DEFAULT NULL`.
  - Added `simpan_koreksi_admin_sektor(article_identifier, sektor, alasan, oleh, db_path)` updating `koreksi_admin_sektor` and appending audit history into `catatan_analis`.
- **`src/cti/analyzer.py` (lines 712-886)**:
  - Implemented `guard_sector_and_quote(sektor, kutipan, teks_berita, confidence=1.0)`:
    - Strictly validates that `sektor` is in `CLOSED_10_IIV_SECTORS`.
    - Normalizes whitespace (`\s+` -> `' '`) and performs case-insensitive substring search of `kutipan` in `teks_berita`.
    - If `sektor == "Tidak dapat ditentukan"`, empty quote `""` is valid.
    - If quote is missing or not a verbatim substring, hard-rejects to `("Tidak dapat ditentukan", "", 0.0, False)`.
  - Implemented `classify_sector(teks_berita, context, prefer_llm=True)`:
    - Online path invokes Gemini with strict JSON schema enforcing `sektor_target`, `confidence_sektor`, `kutipan_bukti_sektor`, and `alasan_sektor`, guarded by `guard_sector_and_quote()`.
    - Offline fallback `_classify_sector_deterministic()` requires cyber-incident keywords context before matching sector keywords, extracts the exact containing sentence from `teks_berita`, cleans punctuation, and guarantees substring containment.
  - Updated `analyze_news()` to include sector classification, populating `sektor_target`, `confidence_sektor`, `kutipan_bukti_sektor`, `alasan_sektor` in the returned intelligence dictionary.
- **`scripts/classify_weekly_sectors.py`**:
  - Batch runner for historical/weekly news with `--db-path`, `--days`, `--limit`, `--dry-run`.
  - Live test run: `python scripts/classify_weekly_sectors.py --db-path data/state.db --days 7` classified 130 articles in 1.48 seconds; 92 articles had valid extracted evidence quotes (70.8% quote coverage, 100% exact substring validity).
- **`src/cti/evaluator.py`, `scripts/generate_evaluation_draft.py`, `scripts/evaluate_pipeline.py`**:
  - `generate_draft_dataset()` exports CSV with columns: `prediksi_sektor`, `confidence_sektor`, `kutipan_bukti_sektor`, `verified_sektor`, `status_label` (`DRAFT_PENDING_USER_REVIEW`).
  - `calculate_evaluation_metrics()` calculates Precision, Recall, F1 per sector, Sector Accuracy, and `quote_validity_rate`.
  - Evaluation run on `data/evaluation/dataset_evaluasi_sampel_terverifikasi.csv`:
    - Sector Accuracy: 1.0000 (100.0%)
    - Sector Macro F1: 1.0000 (100.0%)
    - Evidence Quote Validity Rate: 1.0000 (100.0%)
- **`tests/test_cti_sector_classification.py`**:
  - 19 test cases covering constants, guard rejection/acceptance, offline keyword classification, exact sentence slicing, integration in `analyze_news`, SQLite persistence, admin manual correction, and evaluator metrics calculation.
  - Test run: `python -m pytest tests/test_cti_sector_classification.py` -> `19 passed in 14.75s`.

---

## 2. Logic Chain
1. **Requirements Alignment**:
   - Perpres No. 82/2022 Pasal 4 establishes 10 critical sectors (Administrasi Pemerintahan, Energi dan ESDM, Transportasi, Keuangan, Kesehatan, TIK, Pangan, Pertahanan, Penegakan Hukum, Layanan Publik & Pengguna Digital). Any classification system must adhere to these 10 sectors without freeform drift.
   - For articles without explicit sector context, the fallback `"Tidak dapat ditentukan"` prevents hallucinated classification.
2. **Strict Guard Protection**:
   - To eliminate LLM hallucinations, `guard_sector_and_quote()` validates that the extracted evidence quote is an exact, non-empty substring of the original news text. Whitespace normalization (`" ".join(kutipan.split())`) allows multi-line text matches while preserving exact character sequences.
   - Any hallucinated quote or out-of-list sector immediately rejects to `("Tidak dapat ditentukan", "", 0.0, False)`.
3. **Deterministic Fallback with Verbatim Extraction**:
   - In offline/fallback mode, sentences are sliced directly from `teks_berita`. Trimming exterior punctuation (`.strip(" \t\n\r.")`) prevents trailing periods from failing verbatim string assertions.
   - Adding a cyber-incident context check prevents benign civic news (e.g. municipal bike rides or morning walks mentioning "warga") from falsely classifying into `"Layanan Publik & Pengguna Digital"`.
4. **Data Persistence and Audit Trail**:
   - `simpan_intelijen_berita()` upserts sector fields into `intelijen_berita_tervalidasi` without overwriting existing manual corrections unless explicitly updated.
   - `simpan_koreksi_admin_sektor()` updates `koreksi_admin_sektor` and appends an audit log entry in `catatan_analis`, supporting CSIRT analyst review workflows.
5. **Evaluation Metric Integrity**:
   - Evaluator verifies ground truth against predictions using multi-class Precision/Recall/F1, and independently tests `quote_validity_rate` using the exact substring guard against the stored raw news text.

---

## 3. Caveats
- No caveats. All 10 IIV sectors and fallback operate strictly.
- Note: Out of 130 weekly news articles in `data/state.db`, 38 articles (29.2%) did not have specific institutional or sector keywords in their text and were safely mapped to `"Tidak dapat ditentukan"` with quote `""`, exactly matching the intended defense against false positives.
- The evaluation draft script generates `status_label = "DRAFT_PENDING_USER_REVIEW"` to maintain analyst-in-the-loop governance before ground truth finalization.

---

## 4. Conclusion
Milestone M2 (R4) — Sektor Target Terpapar 10 IIV is fully implemented, rigorously validated, integrated with database persistence, batch processing, and evaluation tooling, and covered by 19 dedicated unit/integration tests with zero regressions across the codebase.

---

## 5. Verification Method
To independently verify the implementation, execute the following commands in the project root:

1. **Run Dedicated Sector Unit & Integration Tests**:
   ```powershell
   python -m pytest tests/test_cti_sector_classification.py -v
   ```
   *Expected result*: 19 tests pass (0 failures).

2. **Run Weekly Sector Batch Runner**:
   ```powershell
   python scripts/classify_weekly_sectors.py --db-path data/state.db --days 7
   ```
   *Expected result*: Classifies 130 articles, outputs summary table of sector distribution and quote validity rate >= 70%.

3. **Generate Evaluation Draft Dataset**:
   ```powershell
   python scripts/generate_evaluation_draft.py --db-path data/state.db --output data/evaluation/dataset_evaluasi_draf.csv
   ```
   *Expected result*: Generates CSV with `prediksi_sektor`, `confidence_sektor`, `kutipan_bukti_sektor`, `verified_sektor` (blank), and `status_label`.

4. **Run Evaluation Pipeline on Verified Sample**:
   ```powershell
   python scripts/evaluate_pipeline.py --ground-truth data/evaluation/dataset_evaluasi_sampel_terverifikasi.csv
   ```
   *Expected result*: Displays metrics table with Sector Accuracy = 100.0%, Evidence Quote Validity Rate = 100.0%.

5. **Run Full Test Suite**:
   ```powershell
   python -m pytest
   ```
   *Expected result*: 270 passed in full test suite.
