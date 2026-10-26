# Dispatch: Worker M5 (Additive Dashboard Integration & Legacy Adaptation)

## Mission
Implement Milestone 5: Additive Admin Dashboard Integration (Requirement R3) and adapt legacy encyclopedia callers to gracefully handle the removal of the 9 unverified encyclopedia files per the user's official decision.

## Working Directory
`D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m5`

## Mandatory Reading
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md` (mandatory).
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\PROJECT.md`
- Read User Decisions in `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\orchestrator_1\DISPATCH.md` (sections 15:44:37Z and R3).
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\explorer_survey_codebase\handoff.md` (contains exact line numbers for the 5 dashboard points).

## CRITICAL CONSTRAINTS & WARNINGS
- Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
- All baseline tests in `python -m pytest tests/` MUST remain passing without regressions.
- MANDATORY INTEGRITY WARNING:
  DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
- **Prinsip Mutlak R3**: HANYA MENAMBAH INFORMASI TERVALIDASI, TIDAK BOLEH MENGHAPUS ATAU MENGGANTI TEKS/NARASI LAMA.

## Exclusive Write Ownership
You exclusively own and may edit:
- `src/analytics/cti_agents.py`
- `src/analytics/encyclopedia_lookup.py`
- `src/analytics/rag_engine.py` (if needed for KPI integration)
- `src/web/templates/partials/_tren.html`
- `src/web/static/js/tren/tren-kpi.js`
- `src/web/static/js/tren/tren-ai-cards.js`
- `src/web/app.py` (for graceful `/api/ensiklopedia` adaptation)
- `tests/test_cti_m5.py`
Do NOT touch `tests/test_cti_e2e_suite.py` or files in `src/cti/`.

## Implementation Requirements

### 1. The 5 Dashboard Points (Requirement R3 - Strictly Additive)
1. **Titik 1: KPI `[ POLA ANCAMAN ]`**:
   - Files: `src/web/templates/partials/_tren.html:140` and `src/web/static/js/tren/tren-kpi.js:116`.
   - Current text and growth percentage must remain intact.
   - User Decision: Append badge `Taksonomi Resmi: [label]` **WITHOUT confidence percentage**.
2. **Titik 2: Section "ANALISIS BERITA SIBER & REKOMENDASI MITIGASI" -> Bagian 1 "INSIDEN MELONJAK DRASTIS"**:
   - File: `src/analytics/cti_agents.py` (`_generate_section_1_makro`).
   - Original macro narrative paragraph remains 100% intact.
   - Append block: `**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**` summarizing validated eCSIRT category distribution.
3. **Titik 3: Section "ANALISIS BERITA SIBER & REKOMENDASI MITIGASI" -> Bagian 2 "TREN INSIDEN MINGGUAN"**:
   - File: `src/analytics/cti_agents.py` (`_generate_section_2_mikro`).
   - Original 3 micro-incident narratives remain 100% intact.
   - Append validated incident taxonomy tags to each of the 3 weekly incidents:
     `- *Klasifikasi Resmi*: **[<Kategori>]** (eCSIRT: <induk_ecsirt>)`.
4. **Titik 4: Bagian 3 "VEKTOR SERANGAN TREN INSIDEN MINGGUAN"**:
   - File: `src/analytics/cti_agents.py` (`_generate_section_3_vektor`).
   - Original attack vector narrative remains 100% intact.
   - Append verified MITRE ATT&CK Enterprise techniques:
     `**Rujukan Terverifikasi MITRE ATT&CK Enterprise**:` listing active technique ID, name, tactic, and link.
5. **Titik 5: Bagian 4 "REKOMENDASI AKSI"**:
   - File: `src/analytics/cti_agents.py` (`_generate_section_4_rekomendasi`).
   - Original action recommendation text remains intact.
   - Append:
     `**Saran Mitigasi Terverifikasi MITRE D3FEND (Lookup Deterministik)**:` listing D3FEND techniques retrieved from SQLite via `src.storage.db.ambil_d3fend_mitigasi_by_attack_id`.
     `**Referensi Standar NIST Tambahan**:` listing NIST SP 800-53 / CSF 2.0 controls.

### 2. Graceful Adaptation for 9 Deleted Encyclopedia Files
- Per user decision, 9 files (`bssn`, `indeks_kami`, `csirt_framework`, `owasp`, `cwe`, `cis_controls`, `iso27001`, `csa_ccm`, `cisa_cpg`) are retired.
- In `src/analytics/encyclopedia_lookup.py` and `/api/ensiklopedia` (`src/web/app.py`), ensure code gracefully handles missing files (returns empty list or fallback to ATT&CK/D3FEND/NIST/eCSIRT without crashing).
- Existing unit tests in `tests/test_web_endpoints.py` must continue to pass!

### 3. Verification
- Run full test suite: `python -m pytest tests/` and verify all tests pass.
- Write unit tests in `tests/test_cti_m5.py` asserting that old text is preserved and new CTI blocks are present.
- Document in `handoff.md`.
