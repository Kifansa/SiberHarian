# Dispatch: Spec Miner Sources

## Mission
Investigate and live-verify authoritative CTI sources, exact repository paths, JSON endpoints, versioning schemes, and analyze existing local CTI files.

## Working Directory
`D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_sources`

## Mandatory Reading
Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md` before starting.

## CRITICAL CONSTRAINTS
- Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
- Do NOT fabricate or hallucinate URLs, file paths, or taxonomy contents. Verify them live using web search or reading available documentation.
- Produce your comprehensive report in `handoff.md` in your working directory.

## Investigation Scope
1. Incident Taxonomy:
   - Investigate github.com/MISP/misp-taxonomies and github.com/enisaeu/Reference-Security-Incident-Taxonomy-Task-Force.
   - Compare candidates (eCSIRT/ENISA, circl, common-taxonomy, veris, etc.).
   - Recommend the best taxonomy for CSIRT Diskominfo Jatim news classification with rationale.
   - Define a closed list of 8-12 practical categories for news (e.g., ransomware, data breach, DDoS, defacement, phishing/penipuan, malware, eksploitasi kerentanan, akses tidak sah, lainnya, tidak dapat ditentukan) and map each to its parent in the source taxonomy.
2. MITRE ATT&CK (Enterprise):
   - Investigate github.com/mitre-attack/attack-stix-data.
   - Verify the exact current path for Enterprise STIX 2.1 JSON (e.g. `enterprise-attack/enterprise-attack.json`) and release tagging / version scheme.
3. MITRE D3FEND JSON API:
   - Investigate https://d3fend.mitre.org endpoints:
     - `/api/ontology/inference/d3fend-full-mappings.json` (offensive to defensive mappings)
     - `/api/technique/all.json`
     - `/api/offensive-technique/all.json`
     - `/api/version.json`
   - Verify schema and structure of mappings (ATT&CK ID -> D3FEND technique list).
4. NIST OSCAL JSON Catalogs:
   - Investigate github.com/usnistgov/oscal-content.
   - Verify exact JSON paths for SP 800-53 Rev 5 and NIST CSF 2.0.
5. Local Files Analysis:
   - Inspect existing local files: `mitre.json`, `d3fend.json`, `nist.json`, `bssn.json` in the project.
   - Determine whether each should be reused or recreated from the official live sources, with clear justifications.
   - For other encyclopedia files in `data/encyclopedia/` (bssn, owasp, cwe, cis_controls, etc.), document what exists and note questions for user consultation per R0.

Deliver your findings in `handoff.md` in your working directory and notify the orchestrator when complete.


## 2026-10-20T15:27:10Z
From: d326f96e-59d9-4542-b4b8-e1006667c5bf (orchestrator)
Content: Read D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md and D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_sources\DISPATCH.md. Your working directory is D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_sources. CRITICAL: Do NOT touch and do NOT read Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx and the folder LAPORAN DASHBOARD ADMIN/. Live-verify official CTI sources (MISP/ENISA taxonomy, MITRE ATT&CK STIX, MITRE D3FEND API, NIST OSCAL content) and analyze local files (mitre.json, d3fend.json, nist.json, bssn.json). Produce handoff.md in your working directory and notify the orchestrator when finished.
