# Dispatch: Worker M1 & M2 (CTI Ingestion & Preparation)

## Mission
Implement Milestone 1 (Download & Staging Pipeline) and Milestone 2 (Data Preparation & Relational/Document Storage) for the SiberHarian CTI Layer.

## Working Directory
`D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m1_m2`

## Mandatory Reading
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md` (mandatory).
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\PROJECT.md`
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_pipeline\handoff.md`
- Read `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_sources\handoff.md`

## CRITICAL CONSTRAINTS & WARNINGS
- Do NOT touch and do NOT read `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and the folder `LAPORAN DASHBOARD ADMIN/`.
- All 36 existing tests in `python -m pytest tests/` MUST remain passing without regressions.
- MANDATORY INTEGRITY WARNING:
  DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
- Do NOT touch the 9 unverified encyclopedia files (`bssn.json`, `owasp.json`, etc.) in `data/encyclopedia/`.

## Exclusive Write Ownership
You exclusively own and may create/edit:
- `src/cti/__init__.py`
- `src/cti/downloader.py`
- `src/cti/preparer.py`
- `src/storage/db.py` (ONLY add helper methods/DDL for `d3fend_techniques` and `d3fend_attack_mappings`; do NOT break existing functions)
- `data/raw/` directories and staging payloads.
Do NOT write to `tests/test_cti_e2e_suite.py` (owned by test_writer).

## Implementation Requirements

### Milestone 1: Download & Staging Pipeline (Tahap 1, R1)
1. In `src/cti/downloader.py`:
   - Implement downloaders for:
     a. MISP eCSIRT Taxonomy: `https://raw.githubusercontent.com/MISP/misp-taxonomies/main/ecsirt/machinetag.json`
     b. MITRE ATT&CK STIX 2.1 Enterprise: `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json` (or latest release tag)
     c. MITRE D3FEND: Query `https://d3fend.mitre.org/api/version.json` for version string, then fetch `https://d3fend.mitre.org/ontologies/d3fend/{version}/d3fend-full-mappings.json` (Note: `/api/ontology/inference/d3fend-full-mappings.json` is a 404, use versioned URL!), plus `/api/technique/all.json`.
     d. NIST OSCAL Catalogs: `https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json` and `https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json`.
   - Staging path format: `data/raw/<sumber>/<YYYY-MM-DD>/`.
   - Accompany each download with `metadata.json` recording: `source_name`, `source_url`, `download_timestamp_utc`, `version_identifier`, `file_sha256`, `file_size_bytes`, `record_count_parsed`, `download_status`.
   - Resilience: timeout (45s), exponential backoff retry (3x), logging, proxy support (`HTTP_PROXY`, `HTTPS_PROXY`), mirror base URL option.

### Milestone 2: Data Preparation & Storage (Tahap 2, R1)
2. In `src/cti/preparer.py`:
   - ATT&CK STIX 2.1 Flattener:
     - Filter strictly for `type == "attack-pattern"`. Discard if `revoked: true` or `x_mitre_deprecated: true`.
     - Output flattened documents: `technique_id` (T-number from external_references), `name`, `tactics` (from kill_chain_phases), `description`, `platforms` (`x_mitre_platforms`), `is_subtechnique`.
     - Metadata: `source: "mitre-attack"`, `source_version`, `original_id`, `ingest_date`.
   - Incident Taxonomy Document Generator:
     - Generate 11 closed category documents (Ransomware, Data Breach, DDoS, Defacement, Phishing/Penipuan, Malware, Eksploitasi Kerentanan, Akses Tidak Sah, Pelecehan/Konten Berbahaya, Lainnya, Tidak Dapat Ditentukan).
     - Each document includes: name, eCSIRT parent predicate/value, definition, representative news examples.
   - D3FEND Relational Storage (SQLite):
     - D3FEND MUST NOT be placed into vector store. Must be stored in relational SQLite table for deterministic lookup.
     - Tables in `data/state.db`:
       `d3fend_techniques (technique_id PRIMARY KEY, name, tactic, definition, source_version, updated_at)`
       `d3fend_attack_mappings (id INTEGER PK AUTOINCREMENT, attack_technique_id, d3fend_technique_id, relationship_type, source_version)`
     - Populated from D3FEND mappings and technique definitions.
   - NIST OSCAL Control Flattener:
     - Parse SP 800-53 Rev 5 controls and CSF 2.0 subcategories into documents: `control_id`, `title`, `statement`, `family_or_function`, `framework`.
     - Metadata: `source: "nist-oscal"`, `source_version`, `original_id`, `ingest_date`.

3. Verification:
   - Run existing tests: `python -m pytest tests/` and verify all 36 tests pass.
   - Run smoke tests on your downloader and preparer to ensure files, metadata, and SQLite tables are generated properly.
   - Document commands and results in `handoff.md`.


## 2026-10-20T15:43:04Z
Read D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\ORIGINAL_REQUEST.md and D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m1_m2\DISPATCH.md. Your working directory is D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\worker_m1_m2. CRITICAL CONSTRAINTS: Do NOT touch and do NOT read Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx and the folder LAPORAN DASHBOARD ADMIN/. All 36 existing tests in tests/ must remain passing. MANDATORY INTEGRITY WARNING: DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A teamwork_preview_auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected. Implement Milestone 1 & 2 per DISPATCH.md in src/cti/downloader.py and src/cti/preparer.py, run tests, and report in handoff.md.


## 2026-10-20T15:45:01Z
**Context**: Keputusan Resmi User (R0 & R3) untuk Implementasi CTI

**Content**: User telah mengeluarkan keputusan resmi:
1. 9 File Ensiklopedia Non-Spesifikasi (bssn, indeks_kami, csirt_framework, owasp, cwe, cis_controls, iso27001, csa_ccm, cisa_cpg) resmi DIHAPUS. Sistem HANYA memakai ATT&CK, D3FEND, NIST, dan taksonomi insiden (eCSIRT/ENISA).
2. mitre.json, d3fend.json, nist.json dummy lama diganti penuh dengan data resmi hasil download.
3. Seluruh pemanggil ensiklopedia di masa mendatang akan mengarah ke 4 pilar ini.

**Action**: Tetap fokus pada penyiapan data resmi ATT&CK, D3FEND, NIST, dan taksonomi eCSIRT di `src/cti/downloader.py` dan `src/cti/preparer.py`.


## 2026-10-20T15:58:10Z
**Context**: Status check M1 & M2

**Content**: Bagaimana status implementasi downloader dan preparer Anda? Apakah pengujian dan pembuatan handoff.md sudah siap?

**Action**: Mohon selesaikan dan kirimkan handoff report jika sudah tuntas.
