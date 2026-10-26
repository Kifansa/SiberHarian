# DISPATCH: worker_m4_dynamic_tests

## Context
You are the Dynamic Multi-Dataset Acceptance Test Worker for SiberHarian (CSIRT Diskominfo Jatim).
Working Directory: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m4_dynamic_tests

## Authoritative Instructions
Read:
- D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md (specifically '## Follow-up — 2026-10-21T02:12:53Z' and '## Follow-up — 2026-10-21T02:48:39Z')
- D:\penting\magang\kominfo\NOTIFIKASI-BERITA\PROJECT.md
- D:\penting\magang\kominfo\NOTIFIKASI-BERITA\AUDIT_HARDCODE_DAN_LOGIKA_TERARAH.md

## MANDATORY INTEGRITY WARNING
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

## Objective
Create a dedicated automated test suite: `tests/test_dynamic_multi_dataset.py`.
Prove that changing/adding news dynamically updates:
1. `[ POLA ANCAMAN ]` (dominant closed eCSIRT taxonomy category)
2. `[ SINYAL ANCAMAN BARU ]` (rising taxonomy category, novelty > volume, >= 2 cases required, 1 case rejected)
3. `[ SEKTOR TARGET TERPAPAR ]` (10 closed IIV sectors Perpres 82/2022 + "Tidak dapat ditentukan", mandatory exact substring quote)

## Key Test Requirements to Cover
1. **Dynamic Shift across Two Distinct Datasets**:
   - Dataset A:
     - Baseline / dominant articles produce POLA ANCAMAN = Category X (e.g. "Phishing & Penipuan Online").
     - Emerging articles with >= 2 cases produce SINYAL ANCAMAN BARU = Category Y (e.g. "Ransomware").
     - Victim sector articles produce SEKTOR TARGET TERPAPAR = Sector 1 (e.g. "Keuangan & Perbankan") with exact substring evidence quote.
   - Dataset B:
     - Baseline / dominant articles produce POLA ANCAMAN = Category Z (e.g. "Eksploitasi Kerentanan (Exploit / Zero-Day)").
     - Emerging articles with >= 2 cases produce SINYAL ANCAMAN BARU = Category W (e.g. "Malware / Infostealer").
     - Victim sector articles produce SEKTOR TARGET TERPAPAR = Sector 2 (e.g. "Kesehatan" or "Administrasi Pemerintahan") with exact substring quote.
   - Assert `pola_A != pola_B`, `sinyal_A != sinyal_B`, `sektor_A != sektor_B`.
2. **Novelty vs Volume Rules**:
   - When Category A has high volume (e.g. 5 cases in baseline and 5 in current) but 0% growth, and Category B has 0 in baseline and 2 cases in current, SINYAL ANCAMAN BARU must be Category B (novelty > volume).
   - When a new category has only 1 case in current period, it must NOT trigger an alarm (returns "Kondisi Stabil").
3. **Exact Substring Evidence Verification**:
   - Every classified sector must have an evidence quote that is an exact substring of the article text (`assert quote in news_text`).
   - If sector is "Tidak dapat ditentukan", quote must be empty string `""`.
4. **Run Pytest & Verify**:
   - Run `python -m pytest tests/test_dynamic_multi_dataset.py -v`
   - Document results in `handoff.md` and send message to orchestrator (`e7dc208b-024f-412d-993f-55ea0f0598d7`).

## 2026-10-21T03:18:47Z
[Message] timestamp=2026-10-21T03:18:47Z sender=e7dc208b-024f-412d-993f-55ea0f0598d7 priority=MESSAGE_PRIORITY_HIGH
Create the dedicated automated test suite tests/test_dynamic_multi_dataset.py proving on two distinct datasets (Dataset A vs Dataset B) that:
1. [ POLA ANCAMAN ] shifts dynamically between datasets (based on dominant closed 11 eCSIRT category).
2. [ SINYAL ANCAMAN BARU ] shifts dynamically based on novelty > volume, strictly requiring >= 2 cases (1 case must be rejected as false alarm, returning 'Kondisi Stabil').
3. [ SEKTOR TARGET TERPAPAR ] shifts dynamically between datasets across the 10 closed IIV sectors (Perpres 82/2022) + 'Tidak dapat ditentukan', with mandatory exact substring quote validation (verified with assert quote in news_text or whitespace-normalized equivalent). Out-of-list sectors and invalid quotes must be rejected.
4. Execute python -m pytest tests/test_dynamic_multi_dataset.py -v and ensure all tests pass cleanly.
5. Write your complete handoff report to D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m4_dynamic_tests\handoff.md and send a message back with your findings.
