# DISPATCH Log

## 2026-10-21T02:15:08Z
Sender: 17a27691-0874-48b4-96b7-a9105a1699a4
Message:
You are the Project Orchestrator (orchestrator_2) for SiberHarian (CSIRT Diskominfo Jatim).
Your working directory is: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\orchestrator_2
Your authoritative requirements are in: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md (specifically the latest section: '## Follow-up — 2026-10-21T02:12:53Z').

Key Constraints & Instructions:
1. Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
2. If there is an ambiguous or critical decision needed, stop and ask the user (one question, in Indonesian).
3. R1: KPI [ POLA ANCAMAN ] must use attack taxonomy category (closed taxonomy) as primary value, along with counts and growth. Remove the redundant "Taksonomi Resmi: [...]" badge.
4. R2: KPI [ SINYAL ANCAMAN BARU ] must use taxonomy category instead of entities. Must represent NEW rising incidents (novelty > volume; >=2 cases required, 1 case is not enough).
5. R3: Audit entire project for hardcoded/directed results (KPI, charts, tables, SITREP 5 parts in ANALISIS BERITA SIBER & REKOMENDASI MITIGASI, regional cases, public statistics). For ANALISIS BERITA SIBER & REKOMENDASI MITIGASI, provide options to user per finding (fix with X vs keep as is with risks). Do NOT change audit findings before user selects options, except R1, R2, R4. Write audit report to a markdown file in repo.
6. R4: [ SEKTOR TARGET TERPAPAR ] - LLM sector classification with 10 closed IIV sectors (Perpres 82/2022) + "Tidak dapat ditentukan". Mandatory evidence quote that is an exact substring of the news text. Run for all news this week. Provide draft labeled sample for user correction and script to measure accuracy against corrections.
7. Dynamic Acceptance Criteria: Prove via automated tests on two different datasets that changing/adding news dynamically updates [ POLA ANCAMAN ], [ SINYAL ANCAMAN BARU ], and [ SEKTOR TARGET TERPAPAR ].
8. Regression: All existing tests (`python -m pytest tests/`) must pass; any adapted tests must be documented.
9. Decompose into specialized subagents, maintain `plan.md`, `progress.md`, and `BRIEFING.md` in your working directory. Report completion when done.
