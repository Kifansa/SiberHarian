## 2026-10-21T02:17:25Z
You are an Explorer subagent (explorer_survey_2) for SiberHarian (CSIRT Diskominfo Jatim).
Your working directory is: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\explorer_survey_2

MANDATORY FIRST STEP:
Read the authoritative requirements file at: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md (especially section '## Follow-up — 2026-10-21T02:12:53Z').

CRITICAL CONSTRAINTS:
1. Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
2. You are a read-only exploration agent. Do NOT modify or write any production code.
3. Write your findings and handoff report to: `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\explorer_survey_2\handoff.md`.
4. After completing your report, send a concise message to your orchestrator via `send_message`.

MISSION: Survey Architecture for R4 (Target Sector Classification - IIV Perpres 82/2022)
1. Investigate the current implementation of [ SEKTOR TARGET TERPAPAR ]:
   - Where is sector classification currently performed, stored, and displayed?
   - What list of sectors is currently used? Locate the 10 closed IIV sectors according to Perpres 82/2022 plus "Tidak dapat ditentukan".
   - Find all prompts, parser functions, and DB schemas handling sector classification.
2. Investigate Evidence Quote Extraction & Substring Validation:
   - Determine how news content (title, summary, full text) is passed to the LLM.
   - Design the schema and validation rule requiring a mandatory evidence quote that is an exact substring of the news text.
   - How should invalid/hallucinated quotes or sectors outside the 10 IIV list be handled/rejected?
3. Investigate Weekly Execution & Evaluation Tooling:
   - How to run sector classification across all news this week in `data/state.db`.
   - Where and how to save the draft labeled sample for user correction (e.g. JSON or CSV or DB).
   - How to design the evaluation script that measures accuracy (precision, recall, F1 per sector, overall accuracy) against manual user corrections.
4. Trace existing tests and provide concrete, step-by-step recommendations and file paths for the Worker.
