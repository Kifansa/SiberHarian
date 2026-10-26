# HANDOFF REPORT: DYNAMIC MULTI-DATASET ACCEPTANCE TESTING (M4)

**Worker**: worker_m4_dynamic_tests  
**Role**: implementer, qa, specialist  
**Working Directory**: `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m4_dynamic_tests`  
**Parent Agent**: Project Orchestrator (`e7dc208b-024f-412d-993f-55ea0f0598d7`)  
**Status**: COMPLETED & VERIFIED  

---

## 1. Observation

1. **Direct Dispatch Objectives**:
   - Create automated test suite `tests/test_dynamic_multi_dataset.py` proving on two distinct datasets (Dataset A vs Dataset B) that:
     - `[ POLA ANCAMAN ]` shifts dynamically between datasets (based on dominant closed 11 eCSIRT category).
     - `[ SINYAL ANCAMAN BARU ]` shifts dynamically based on novelty > volume, strictly requiring >= 2 cases (1 case must be rejected as false alarm, returning 'Kondisi Stabil').
     - `[ SEKTOR TARGET TERPAPAR ]` shifts dynamically between datasets across the 10 closed IIV sectors (Perpres 82/2022) + 'Tidak dapat ditentukan', with mandatory exact substring quote validation (verified with `assert quote in news_text` or whitespace-normalized equivalent). Out-of-list sectors and invalid quotes must be rejected.
   - Run `python -m pytest tests/test_dynamic_multi_dataset.py -v` and ensure all tests pass cleanly.

2. **Codebase Inspection**:
   - `src/analytics/rag_engine.py`:
     - Line 578: `def hitung_prediksi_pola_serangan(self) -> Dict[str, Any]` computes dominant closed eCSIRT category across `CLOSED_11_TAXONOMY_CATEGORIES`.
     - Line 653: `def hitung_prediksi_ancaman_baru(self) -> str` and line 861 `def ambil_berita_ancaman_baru(self) -> Dict[str, Any]` implement the novelty > volume heuristic with mandatory threshold $\ge 2$ cases in current period (`cnt_cur >= 2`), returning `"Kondisi Stabil"` if `cnt_cur < 2`.
     - Lines 292-296: In `RAGEngine.__init__`, if `kategori_relevansi` is present in columns, it filters for `kategori_relevansi == 'insiden_spesifik'`.
   - `src/cti/preparer.py`:
     - Lines 32-44: `CLOSED_11_TAXONOMY_CATEGORIES` (11 closed categories).
     - Lines 177-189: `CLOSED_10_IIV_SECTORS` (10 IIV sectors Perpres 82/2022 Pasal 4 + "Tidak dapat ditentukan").
   - `src/cti/analyzer.py`:
     - Lines 111-170: `guard_sector_and_quote` validates that sector belongs to `CLOSED_10_IIV_SECTORS`, quote is non-empty for active sectors, and quote is an exact case-insensitive whitespace-normalized substring of `teks_berita`. Rejects out-of-list sectors and hallucinated quotes, defaulting to `("Tidak dapat ditentukan", "", 0.0, False)`.
     - Line 677: `def classify_sector(self, article)` extracts victim sector and exact quote.
   - `src/analytics/trend_analyzer.py`:
     - Line 404: `def hitung_tren_sektor_target(df_riwayat)` aggregates victim sector exposure across articles.
     - Lines 70-114: `_dedup_ringan_lintas_hari` deduplicates headlines with token similarity $\ge 85\%$.

3. **Execution Commands and Results**:
   - `python -m pytest tests/test_dynamic_multi_dataset.py -v`:
     ```
     ============================= test session starts =============================
     collected 13 items

     tests/test_dynamic_multi_dataset.py::TestDynamicDatasetShift::test_pola_ancaman_shifts_dynamically PASSED [  7%]
     tests/test_dynamic_multi_dataset.py::TestDynamicDatasetShift::test_sektor_target_terpapar_shifts_dynamically PASSED [ 15%]
     tests/test_dynamic_multi_dataset.py::TestDynamicDatasetShift::test_sinyal_ancaman_baru_shifts_dynamically PASSED [ 23%]
     tests/test_dynamic_multi_dataset.py::TestNoveltyVsVolumeRules::test_adding_second_case_immediately_activates_threat_signal PASSED [ 30%]
     tests/test_dynamic_multi_dataset.py::TestNoveltyVsVolumeRules::test_novelty_takes_precedence_over_high_volume_established_category PASSED [ 38%]
     tests/test_dynamic_multi_dataset.py::TestNoveltyVsVolumeRules::test_single_case_novelty_rejected_as_false_alarm PASSED [ 46%]
     tests/test_dynamic_multi_dataset.py::TestExactSubstringSectorVerification::test_all_10_closed_iiv_sectors_with_exact_substring_verification PASSED [ 53%]
     tests/test_dynamic_multi_dataset.py::TestExactSubstringSectorVerification::test_empty_quote_for_active_sector_rejected_by_guard PASSED [ 61%]
     tests/test_dynamic_multi_dataset.py::TestExactSubstringSectorVerification::test_hallucinated_or_mutated_quote_rejected_by_guard PASSED [ 69%]
     tests/test_dynamic_multi_dataset.py::TestExactSubstringSectorVerification::test_out_of_list_sector_rejected_by_guard PASSED [ 76%]
     tests/test_dynamic_multi_dataset.py::TestExactSubstringSectorVerification::test_undetermined_sector_must_have_empty_quote PASSED [ 84%]
     tests/test_dynamic_multi_dataset.py::TestDatabasePipelineDynamicDatasetShift::test_database_level_dynamic_shift PASSED [ 92%]
     tests/test_dynamic_multi_dataset.py::TestIntegrityMutationCheck::test_swapped_categories_inverts_pola_and_sinyal_output PASSED [100%]

     ============= 13 passed, 2 warnings, 15 subtests passed in 6.62s ==============
     ```
   - Regression test across entire repository `python -m pytest tests/ -v`:
     `283 passed, 5 warnings, 15 subtests passed in 265.47s (0:04:25)`. Zero test regressions.

---

## 2. Logic Chain

1. **Step 1: Dataset Construction for Dynamic Shifting (Observation 1 & 2)**:
   - Built two completely distinct datasets with genuine Indonesian CTI news articles:
     - **Dataset A**:
       - 4 baseline articles (`2026-09-20`) on banking phishing (`phishing_penipuan`) targeting "Keuangan & Perbankan".
       - 4 current articles (`2026-09-28`) on banking phishing (`phishing_penipuan`) targeting "Keuangan & Perbankan".
       - 2 emerging articles (`2026-09-28`) on novel ransomware (`ransomware`) with novelty keywords ("baru", "varian baru", "tebusan").
     - **Dataset B**:
       - 4 baseline articles (`2026-09-20`) on hospital zero-day exploits (`eksploitasi_kerentanan`) targeting "Kesehatan".
       - 4 current articles (`2026-09-28`) on hospital zero-day exploits (`eksploitasi_kerentanan`) targeting "Kesehatan".
       - 2 emerging articles (`2026-09-28`) on novel malware infostealers (`malware`) with novelty keywords ("malware", "varian baru", "trojan").

2. **Step 2: Proving Dynamic Shift (Observation 3)**:
   - `TestDynamicDatasetShift.test_pola_ancaman_shifts_dynamically`:
     - Dataset A dominant: `Phishing / Penipuan Siber`
     - Dataset B dominant: `Eksploitasi Kerentanan (Exploit / Zero-Day)`
     - Verified `assert pola_a != pola_b`.
   - `TestDynamicDatasetShift.test_sinyal_ancaman_baru_shifts_dynamically`:
     - Dataset A novel signal: `Ransomware`
     - Dataset B novel signal: `Malware / Infostealer`
     - Verified `assert sinyal_a != sinyal_b`.
   - `TestDynamicDatasetShift.test_sektor_target_terpapar_shifts_dynamically`:
     - Dataset A top sector: `Keuangan & Perbankan`
     - Dataset B top sector: `Kesehatan`
     - Verified `assert top_sektor_a != top_sektor_b`.
     - Verified per-article sector classification on Dataset A articles yields `Keuangan & Perbankan` with exact substring quote in news text.
     - Verified per-article sector classification on Dataset B articles yields `Kesehatan` with exact substring quote in news text.

3. **Step 3: Proving Novelty vs Volume Rules (Observation 3)**:
   - `test_novelty_takes_precedence_over_high_volume_established_category`:
     - Established category has 10 total cases (5 baseline, 5 current, 0% growth).
     - Novel category has 0 in baseline and 2 cases in current with novelty signal.
     - Dominant pattern remains established category (high volume), while Sinyal Ancaman Baru is the novel category (`Ransomware`), proving novelty > volume.
   - `test_single_case_novelty_rejected_as_false_alarm`:
     - When novel category has only 1 case in current period, system strictly rejects it as a potential false alarm and returns `"Kondisi Stabil"`.
   - `test_adding_second_case_immediately_activates_threat_signal`:
     - Adding a second case immediately elevates the novel category to the active threat signal.

4. **Step 4: Proving Exact Substring Sector Validation (Observation 2 & 3)**:
   - `test_all_10_closed_iiv_sectors_with_exact_substring_verification`:
     - Evaluated all 10 closed IIV sectors under Perpres 82/2022 Pasal 4:
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
     - Every single sector classification produced `is_valid == True` and a non-empty `kutipan_bukti_sektor` that is an exact substring of the article text (`assert normalize_ws(quote) in normalize_ws(full_text)`).
   - `test_undetermined_sector_must_have_empty_quote`:
     - Non-incident context produces sector `"Tidak dapat ditentukan"` with quote `""`.
   - `test_out_of_list_sector_rejected_by_guard`:
     - Rejects out-of-list sectors (e.g., "Pariwisata & Perhotelan", "Sektor Swasta Murni", "Otomotif") and coerces to `"Tidak dapat ditentukan"` with empty quote `""`.
   - `test_hallucinated_or_mutated_quote_rejected_by_guard`:
     - Rejects quotes not found in article text, coercing to `"Tidak dapat ditentukan"`.
   - `test_empty_quote_for_active_sector_rejected_by_guard`:
     - Rejects empty quotes for active sectors, coercing to `"Tidak dapat ditentukan"`.

5. **Step 5: Proving Database-Level Dynamic Pipeline & Anti-Hardcode Mutation (Observation 3)**:
   - `test_database_level_dynamic_shift`:
     - Ingests Dataset A into SQLite `riwayat_tren` table -> computes Dataset A analytics (`Phishing`, `Ransomware`, `Keuangan & Perbankan`).
     - Empties table and ingests Dataset B into `riwayat_tren` -> computes Dataset B analytics (`Eksploitasi Kerentanan`, `Malware`, `Kesehatan`).
     - Proves end-to-end database pipeline dynamic switching.
   - `test_swapped_categories_inverts_pola_and_sinyal_output`:
     - Forensic mutation test: Inverted data distribution (making Ransomware dominant and Phishing novel) completely inverts the output (`pola = Ransomware`, `sinyal = Phishing`), proving 0% directed hardcoding.

---

## 3. Caveats

- In `RAGEngine.__init__`, if `kategori_relevansi` is present in the DataFrame/database columns, the engine specifically filters for `kategori_relevansi == 'insiden_spesifik'`. The test dataset explicitly includes this column, matching the production schema and `tests/test_kpi_dashboard_tren.py`.
- No files outside `.agents/teamwork/worker_m4_dynamic_tests/` and `tests/test_dynamic_multi_dataset.py` were modified. `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and folder `LAPORAN DASHBOARD ADMIN/` were left completely untouched per user mandate.

---

## 4. Conclusion

The dedicated automated test suite `tests/test_dynamic_multi_dataset.py` is fully implemented and passes cleanly (13 passed, 15 subtests passed in 6.62s). All requirements from `DISPATCH.md`, `ORIGINAL_REQUEST.md`, and `AUDIT_HARDCODE_DAN_LOGIKA_TERARAH.md` are completely satisfied:
1. `[ POLA ANCAMAN ]` shifts dynamically between Dataset A and Dataset B across the closed 11 eCSIRT categories.
2. `[ SINYAL ANCAMAN BARU ]` shifts dynamically between datasets, enforcing novelty > volume, strictly requiring $\ge 2$ cases, and rejecting 1-case incidents as `"Kondisi Stabil"`.
3. `[ SEKTOR TARGET TERPAPAR ]` shifts dynamically across all 10 IIV sectors (Perpres 82/2022) + `"Tidak dapat ditentukan"`, with mandatory exact substring quote validation (`assert quote in news_text`).
4. Out-of-list sectors and hallucinated/invalid quotes are strictly rejected.
5. Zero regressions across the entire repository test suite (283 passed in `tests/`).

---

## 5. Verification Method

To independently verify the test suite and its results, execute:

```powershell
# 1. Run the dedicated dynamic multi-dataset test suite
python -m pytest tests/test_dynamic_multi_dataset.py -v

# 2. Run the sector classification and KPI dashboard tests
python -m pytest tests/test_cti_sector_classification.py tests/test_kpi_dashboard_tren.py -v

# 3. Run the full test suite across the repository
python -m pytest tests/ -v
```

Invalidation conditions:
- Any test in `tests/test_dynamic_multi_dataset.py` fails.
- `pola_a == pola_b`, `sinyal_a == sinyal_b`, or `sektor_a == sektor_b` when testing distinct datasets.
- A single-case novel category triggers an alarm instead of returning `"Kondisi Stabil"`.
- An active sector is classified without an exact substring evidence quote present in the news text.
