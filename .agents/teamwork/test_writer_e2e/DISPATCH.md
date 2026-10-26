# Dispatch: E2E Test Suite Writer

## Mission
Design and implement the comprehensive 4-tier opaque-box E2E test suite for the SiberHarian CTI Intelligence Layer Upgrade. The test suite must cover all 25 features and all Acceptance Criteria specified in `ORIGINAL_REQUEST.md`, `PROJECT.md`, and `TEST_INFRA.md`. Upon completion, publish `TEST_READY.md` at project root.

## Working Directory
`D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\test_writer_e2e`

## Mandatory Reading
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md` (mandatory).
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\PROJECT.md`
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\TEST_INFRA.md`
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_pipeline\handoff.md`
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_sources\handoff.md`

## CRITICAL CONSTRAINTS
- Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
- All 36 existing tests under `tests/` MUST remain passing without regressions.
- DO NOT CHEAT. All implementations and tests must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Write Ownership
- Exclusively owns: `tests/test_cti_e2e_suite.py` and `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\TEST_READY.md`.
- Do NOT modify existing test files in `tests/` (`test_25_case_studies.py`, `test_embedding_and_rag.py`, etc.).

## Test Scope & Requirements (Tiers 1-4)
Implement tests in `tests/test_cti_e2e_suite.py`:
1. **Tier 1 (Feature Coverage, >=5 tests per area)**:
   - Tahap 1: Staging directory structure (`data/raw/<source>/<date>/`), SHA-256 calculation & validation, metadata JSON schema verification, download retry logic, proxy/mirror parameter handling.
   - Tahap 2: STIX 2.1 flattening, revoked (`revoked: true`) and deprecated (`x_mitre_deprecated: true`) technique rejection, eCSIRT 11 closed categories mapping, D3FEND relational SQLite schema & foreign keys, NIST OSCAL control document formatting.
   - Tahap 3: Separate vector collections isolation (`collection_attack`, `collection_taxonomy`, `collection_nist`), multilingual embedding adapter with fallback chain, translated text retrieval query verification.
   - Tahap 4: Structured JSON classification schema (with mandatory "Tidak Dapat Ditentukan"), conditional ATT&CK extraction (no extraction without attack flow), active ATT&CK ID validation guard (rejects invalid/hallucinated IDs like T9999), deterministic D3FEND lookup (zero LLM additions), provenance table schema in `intelijen_berita_tervalidasi`.
   - Tahap 5: Periodic update idempotent version checking ("tidak ada pembaruan" when version unchanged), catastrophic drop detector (>30% drop rejected), diff reporting (added/modified/revoked), atomic index swap with rollback preservation, historical revoked technique audit flagging.
   - Tahap 6: Draft labeled dataset generator from `data/state.db` with `DRAFT_PENDING_USER_REVIEW`, evaluation metric calculator (Precision, Recall, F1 per category, and ATT&CK accuracy).
   - R3 Dashboard: Additive verification for the 5 points (KPI `[ POLA ANCAMAN ]`, Section 1, Section 2, Section 3, Section 4) verifying existing narrative is preserved.
2. **Tier 2 (Boundary & Corner Cases, >=5 per area)**:
   - Empty input text, news with zero attack details, corrupted JSON payload, network timeout simulation, missing external ID, empty mapping lookup, drop of 99% records.
3. **Tier 3 (Cross-Feature Combinations)**:
   - End-to-end integration: News input -> Classification -> Conditional ATT&CK -> Active Guard -> D3FEND Lookup -> Provenance Save -> Dashboard Additive Render.
   - Update cycle with revoked technique -> flag in `intelijen_berita_tervalidasi`.
4. **Tier 4 (Real-World Application Scenarios)**:
   - 5 comprehensive realistic scenarios per `TEST_INFRA.md` (Ransomware attack, mobile APK phishing, vague IT maintenance news, update cycle with revoked technique, catastrophic upstream drop).

When complete, write `TEST_READY.md` at project root with full summary and report in `handoff.md`.

## 2026-10-20T15:42:19Z
Read D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md and D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\test_writer_e2e\DISPATCH.md. Your working directory is D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\test_writer_e2e. CRITICAL CONSTRAINTS: Do NOT touch and do NOT read Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx and the folder LAPORAN DASHBOARD ADMIN/. Preserves all 36 existing tests in tests/. DO NOT CHEAT: all tests must be genuine and thorough. Write comprehensive 4-tier E2E test suite in tests/test_cti_e2e_suite.py covering all 25 features from PROJECT.md and TEST_INFRA.md. When complete, publish TEST_READY.md at project root and report back.

## 2026-10-20T15:44:56Z
Context: Keputusan Resmi User (R0 & R3) untuk E2E Test Suite
Content: User telah mengeluarkan keputusan resmi:
1. 9 File Ensiklopedia Non-Spesifikasi (bssn, indeks_kami, csirt_framework, owasp, cwe, cis_controls, iso27001, csa_ccm, cisa_cpg) resmi DIHAPUS. Sistem HANYA memakai ATT&CK, D3FEND, NIST, dan taksonomi insiden (eCSIRT/ENISA). Tes lama yang menguji keberadaan 9 file tersebut diizinkan disesuaikan.
2. KPI Pola Ancaman: Teks pola ancaman lama tetap utuh, tambahkan badge 'Taksonomi Resmi: [label]' TANPA persentase keyakinan.
3. Modul 4 Rekomendasi: Teks lama tetap utuh, tambahkan blok 'Saran Mitigasi Terverifikasi MITRE D3FEND' dan 'Referensi Standar NIST Tambahan' di bawahnya (bagian teks lama berbasis 9 ensiklopedia yang dihapus diizinkan hilang).
Action: Pastikan test suite E2E yang Anda buat di tests/test_cti_e2e_suite.py selaras dengan keputusan ini.
