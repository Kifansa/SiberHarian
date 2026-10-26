## 2026-10-21T02:49:45Z
You are a Worker subagent (worker_m1_kpi_ui) for SiberHarian (CSIRT Diskominfo Jatim).
Your working directory is: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m1_kpi_ui

MANDATORY FIRST STEP:
Read the authoritative requirements file at: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md (especially section '## Follow-up — 2026-10-21T02:12:53Z').

CRITICAL CONSTRAINTS:
1. Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
2. MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
3. Exclusively owned files for this subtask:
   - `src/analytics/rag_engine.py`
   - `src/analytics/trend_analyzer.py` (only the exception fallback around line 892)
   - `src/web/templates/partials/_tren.html`
   - `src/web/static/js/tren/tren-kpi.js`
   - `tests/test_kpi_dashboard_tren.py`
   - `tests/test_cti_m5.py`
   - `tests/test_cti_e2e_suite.py`

TASK SPECIFICATION (R1 & R2):
1. `src/analytics/rag_engine.py`:
   - Implement `resolve_article_taxonomy_category(row_or_dict)` using closed 11 eCSIRT categories from `src.cti.preparer.CLOSED_11_TAXONOMY_CATEGORIES` and `TAXONOMY_DISPLAY_NAMES`.
   - Refactor `hitung_prediksi_pola_serangan(self)`:
     * Aggregate articles in `df_terkini` and `df_baseline` across the 11 categories.
     * Select dominant category. Set `pola = dominant_display_name` (e.g. "Ransomware").
     * Calculate `jumlah_terkini`, `growth_persen`, `subteks = "vs minggu lalu"`.
   - Refactor `hitung_prediksi_ancaman_baru(self)` & `ambil_berita_ancaman_baru(self)`:
     * Eliminate title regex entity fallback ("Ratusan Supermarket Prancis").
     * Enforce strict requirement: Kategori harus memiliki >= 2 kasus di periode terkini (`cnt_cur >= 2`). A single case (`cnt_cur == 1`) is REJECTED and cannot become a new threat signal.
     * Evaluate novelty score: new category (baseline == 0 or surging growth >= 200%) boosted by novelty keywords.
     * Novelty > volume: novel category with >= 2 cases takes precedence over higher-volume established categories.
     * If no category qualifies with >= 2 cases and novelty, return "Kondisi Stabil".
2. `src/analytics/trend_analyzer.py`:
   - Around line 892, update exception fallback: `pola = "Akses Tidak Sah / Pembobolan Akun"`, `ancaman_baru = "Kondisi Stabil"`.
3. `src/web/templates/partials/_tren.html`:
   - Cleanly remove line 153 (`<span ... id="kpi-pola-taxonomy-badge">...</span>`).
4. `src/web/static/js/tren/tren-kpi.js`:
   - Cleanly remove lines 150-166 (`kpiPolaTaxonomy` DOM manipulation).
5. Adapt Tests & Run:
   - `tests/test_kpi_dashboard_tren.py`: adapt assertions for closed taxonomy category and test that 1 case returns "Kondisi Stabil" while >= 2 cases returns taxonomy category.
   - `tests/test_cti_m5.py`: update `test_titik_1_*` to assert `kpi-pola-taxonomy-badge` is removed and `#kpi-pola-serangan` renders taxonomy.
   - `tests/test_cti_e2e_suite.py`: update `test_t1_f14_*` for taxonomy as primary value.
   - Run tests: `python -m pytest tests/test_kpi_dashboard_tren.py tests/test_cti_m5.py tests/test_cti_e2e_suite.py`.


## 2026-10-21T03:18:33Z
**Context**: Milestone M1 (R1 & R2) Implementation
**Content**: Please finalize and deliver your handoff report (write to your working directory's `handoff.md`) and report test results for `tests/test_kpi_dashboard_tren.py`, `tests/test_cti_m5.py`, and `tests/test_cti_e2e_suite.py`.
**Action**: Write handoff.md and reply with your completion message.
