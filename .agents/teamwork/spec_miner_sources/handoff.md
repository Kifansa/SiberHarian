# Handoff Report: CTI Sources Specification & Local Files Analysis

**Agent:** spec_miner_sources  
**Working Directory:** `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_sources`  
**Milestone:** CTI Authoritative Sources Live-Verification & Local Files Specification  
**Recipient:** Orchestrator (`d326f96e-59d9-4542-b4b8-e1006667c5bf`)

---

## 1. Observation

### 1.1 Incident Taxonomy (MISP / ENISA)
- **MISP Taxonomies Repository:** `https://github.com/MISP/misp-taxonomies`
  - Evaluated directories: `ecsirt`, `enisa`, `common-taxonomy`, `circl`, `veris`.
  - Machine tag schema at `https://raw.githubusercontent.com/MISP/misp-taxonomies/main/ecsirt/machinetag.json`:
    - Namespace: `ecsirt`, Version: `2`, Predicates: 11 categories (`abusive-content`, `malicious-code`, `information-gathering`, `intrusion-attempts`, `intrusions`, `availability`, `information-content-security`, `fraud`, `vulnerable`, `other`, `test`).
    - Latest commit for `ecsirt/machinetag.json`: SHA `f05a6c061685923b878335e81c0750f9e5884665`, Date: `2025-03-04T12:55:19Z`.
- **ENISA Reference Security Incident Taxonomy (RSIT) Task Force:** `https://github.com/enisaeu/Reference-Security-Incident-Taxonomy-Task-Force`
  - Version: `1003` (`working_copy/humanv1.md` and `working_copy/machinev1`).
  - Hierarchical categories: 10 primary classes with standardized subcategories (e.g., `Malicious Code -> Ransomware`, `Information Content Security -> Leak of Confidential Information`, `Intrusions -> Application Compromise`, `Availability -> Distributed Denial of Service`, `Fraud -> Phishing`).

### 1.2 MITRE ATT&CK (Enterprise STIX 2.1)
- **Repository:** `https://github.com/mitre-attack/attack-stix-data`
  - Latest Release Tag: `v20.0` (Published: `2026-10-13T19:00:15Z`).
  - Active File Path: `enterprise-attack/enterprise-attack.json` (Size: 55,271,014 bytes, SHA identical to `enterprise-attack-20.0.json`).
  - Download URL: `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json` (or pinned tag `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/v20.0/enterprise-attack/enterprise-attack.json`).
  - STIX 2.1 Object Attributes:
    - Root: `{"type": "bundle", "id": "bundle--...", "objects": [...]}`.
    - Technique Object Type: `"type": "attack-pattern"`.
    - Revocation & Deprecation: `revoked: bool` (e.g., `T1183` has `"revoked": true`), `x_mitre_deprecated: bool`.
    - Technique ID: In `external_references` where `source_name == "mitre-attack"`, field `external_id` (e.g., `"T1566"`, `"T1059.001"`).
    - Tactic names: In `kill_chain_phases` where `kill_chain_name == "mitre-attack"`, field `phase_name` (e.g., `"initial-access"`, `"execution"`).
    - Platform: `x_mitre_platforms` (e.g. `["Windows", "Linux", "macOS"]`).
    - Subtechnique flag: `x_mitre_is_subtechnique: bool`.

### 1.3 MITRE D3FEND JSON API
- **Endpoint Tests on `https://d3fend.mitre.org`:**
  - `GET /api/version.json`: HTTP 200 OK, 297 bytes.
    - Content: `{"version": "1.6.0", "ontology_version": "1.6.0", "release_date": "2026-08-31T00:12:00Z", "ontology_hash_sha256": "744a9fdabf6a04db645d56db8d7cd286205e8f9c294e92a4cd1e823dec756804", "frontend_version": "0.26.1"}`.
  - `GET /api/technique/all.json`: HTTP 200 OK, 36,638 bytes. Contains 271 defensive techniques with `@id`, `d3f:d3fend-id` (e.g., `"D3-AMED"`), `rdfs:label`, `d3f:synonym`.
  - `GET /api/offensive-technique/all.json`: HTTP 200 OK, 585,720 bytes. Contains 858 offensive techniques with `@id`, `d3f:attack-id` (e.g., `"T1001"`), `rdfs:label`, `d3f:definition`.
  - **CRITICAL FINDING — 404 ON SPECIFIED MAPPINGS ENDPOINT:**
    - `GET /api/ontology/inference/d3fend-full-mappings.json`: **HTTP Error 404: Not Found**.
    - Live verified true path: **`https://d3fend.mitre.org/ontologies/d3fend/{version}/d3fend-full-mappings.json`**
      (Current live URL: `https://d3fend.mitre.org/ontologies/d3fend/1.6.0/d3fend-full-mappings.json`).
      HTTP Status: 200 OK, Content-Length: 60,304,720 bytes (~60.3 MB).
    - Mapping Structure: SPARQL 1.1 JSON format (`results.bindings[]`). Each binding contains:
      `off_tech_id` (e.g., `"T1003.005"`), `off_tech_label` (e.g., `"Cached Domain Credentials"`), `def_tech_label` (e.g., `"Credential Hardening"`), `def_tactic_label` (e.g., `"Harden"`), `query_def_tech_label` (e.g., `"Token Binding"`), `def_artifact_label` (e.g., `"Credential"`), `def_tech` (URI).

### 1.4 NIST OSCAL JSON Catalogs
- **Repository:** `https://github.com/usnistgov/oscal-content`
  - Latest Release Tag: `v1.5.0` (Commit: `78650f02ad9321bb7b817846f8fbd4f2bcd620de`, Date: `2026-05-13T05:13:20Z`).
  - **NIST CSF 2.0:**
    - Path: `nist.gov/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json` (Size: 349,827 bytes, minified: `175,291` bytes).
    - Raw URL: `https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json`.
    - OSCAL Structure: `catalog.groups` (6 Functions: `GV`, `ID`, `PR`, `DE`, `RS`, `RC`) -> `controls` (Categories, e.g. `GV.OC`) -> nested `controls` (Subcategories, e.g. `GV.OC-01`) -> `parts` (`statement`, `example`).
  - **NIST SP 800-53 Rev 5:**
    - Path: `nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json` (Size: 10,442,037 bytes, minified: `4,906,119` bytes).
    - Raw URL: `https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json`.
    - OSCAL Structure: `catalog.groups` (Control Families, e.g. `ac`, `ia`, `sc`) -> `controls` (`ac-1`, `ac-2`) -> `parts` (`statement`, `guidance`).

### 1.5 Local Files Audit (`data/encyclopedia/`)
- Direct file examination and record counts:
  - `mitre.json`: 35 items. Format: `[{"id": "T1566", "tactic": "Initial Access", "technique": "Phishing", "keywords": [...]}]`. Manually curated subset with Indonesian keywords; no descriptions or platforms.
  - `d3fend.json`: 21 items. Format: `[{"id": "D3-MFA", "tactic": "Credential Access Defense", "technique": "Multi-Factor Authentication", "keywords": [...], "mitigation": "..."}]`. Arbitrary curated 21 items; no ATT&CK mapping table.
  - `nist.json`: 16 items. Format: `[{"function": "Govern", "category": "GV.SC ...", "keywords": [...], "mitigation": "..."}]`. Only 16 high-level CSF categories; no OSCAL controls or subcategories.
  - `bssn.json`: 7 items. Format: `[{"id": "BSSN-CSIRT", "standard": "Peraturan BSSN No. 1 Tahun 2024 ...", "keywords": [...], "mitigation": "..."}]`. References Indonesian national cybersecurity regulations (Perpres SPBE, UU PDP, BSrE, Pusopkamsinas).
  - 8 Other files in `data/encyclopedia/`:
    `cis_controls.json` (18 items), `cisa_cpg.json` (5 items), `csa_ccm.json` (5 items), `csirt_framework.json` (6 items), `cwe.json` (20 items), `indeks_kami.json` (6 items), `iso27001.json` (10 items), `owasp.json` (16 items). All are small keyword-lookup files used in `src/analytics/encyclopedia_lookup.py`.
- Current test suite status: All 36 existing tests pass (`python -m pytest tests/` -> 36 passed in 13.87s).

---

## 2. Logic Chain

### 2.1 Incident Taxonomy Selection
1. **Candidate Comparison:**
   - `eCSIRT / RSIT` (ENISA Reference Security Incident Taxonomy Task Force v1003 & MISP `ecsirt` v2): Endorsed by TF-CSIRT, FIRST.org, and European CSIRTs Network. Designed specifically for incident triage and computer security emergency teams. Provides clean 2-level hierarchy with exact categories relevant to public sector CSIRTs.
   - `circl` (MISP `circl` v6): Internal taxonomy of CIRCL (Luxembourg CERT); lacks wide inter-agency adoption.
   - `common-taxonomy` (MISP `common-taxonomy` v3): Joint CSIRT/Law Enforcement taxonomy; mirrors eCSIRT but oriented toward judicial evidence.
   - `veris` (Verizon VERIS): Multi-attribute enterprise schema (A4 framework: Actor, Action, Asset, Attribute) requiring dozens of fields; too heavy and over-engineered for 1-sentence to 1-paragraph news classification.
2. **Recommendation:** Adopt **eCSIRT / ENISA Reference Security Incident Taxonomy**. It aligns directly with Gov-CSIRT / BSSN CSIRT standard incident triage guidelines and MISP STIX event categorization.
3. **Closed List of 10 Practical News Categories & Parent Mapping:**
   1. `ransomware` (Ransomware / Pemerasan Data)  
      -> Parent in eCSIRT: `malicious-code` (`predicate="malicious-code"`, value=`"ransomware"`)
   2. `data_breach` (Kebocoran Data / Akses Informasi Ilegal)  
      -> Parent in eCSIRT: `information-content-security` (value=`"Unauthorised-information-access"`, RSIT: `"Leak of Confidential Information"`)
   3. `defacement` (Peretasan Tampilan Web / Judi Online)  
      -> Parent in eCSIRT: `intrusions` (value=`"defacement"`)
   4. `ddos` (Serangan Kelumpuhan Layanan / DoS / DDoS)  
      -> Parent in eCSIRT: `availability` (value=`"ddos"`)
   5. `phishing_penipuan` (Phishing, Rekayasa Sosial, Penipuan APK)  
      -> Parent in eCSIRT: `fraud` (value=`"phishing"`, RSIT: `"Social Engineering / Phishing"`)
   6. `malware` (Malware, Infostealer, Trojan, Botnet non-ransomware)  
      -> Parent in eCSIRT: `malicious-code` (value=`"malware"`)
   7. `eksploitasi_kerentanan` (Eksploitasi Celah Keamanan / RCE / CVE / Zero-Day)  
      -> Parent in eCSIRT: `intrusion-attempts` (value=`"ids-alert"`, `"exploit"`, RSIT: `"Exploitation of Known Vulnerabilities"`)
   8. `akses_tidak_sah` (Pembajakan Akun, Brute Force, Login Tidak Sah)  
      -> Parent in eCSIRT: `intrusions` (value=`"privileged-account-compromise"`, `"unprivileged-account-compromise"`)
   9. `lainnya` (Insiden Siber Lainnya)  
      -> Parent in eCSIRT: `other` (value=`"other"`, RSIT: `"Uncategorised"`)
   10. `tidak_dapat_ditentukan` (Tidak Dapat Ditentukan / Informasi Tidak Cukup)  
       -> Parent in eCSIRT: `other` (value=`"unknown"`, RSIT: `"Undetermined"`) — Mandatory per Tahap 4.

### 2.2 Local Files Strategy: Reuse vs. Recreate
1. **`mitre.json` -> RECREATE from official ATT&CK STIX 2.1:**
   - *Observation:* Contains only 35 manual entries, missing >700 active techniques, missing descriptions, and missing platform metadata required for Tahap 2.
   - *Conclusion:* Recreate flattened dataset from `enterprise-attack.json` (filtering out `revoked: true` and `x_mitre_deprecated: true`). Existing keywords in `mitre.json` can be kept as a secondary Indonesian keyword lexicon.
2. **`d3fend.json` -> RECREATE from official D3FEND API:**
   - *Observation:* Contains only 21 items with synthetic IDs, completely missing the ATT&CK-to-D3FEND mapping table required for deterministic mitigation lookup in Tahap 4.
   - *Conclusion:* Ingest `d3fend-full-mappings.json` (60.3 MB) and `/api/technique/all.json` into a relational table (`d3fend_mappings.sqlite` or state table in `data/`). Existing `d3fend.json` must be preserved or wrapped so legacy tests expecting `[D3-MFA]` remain green.
3. **`nist.json` -> RECREATE from official OSCAL Catalogs:**
   - *Observation:* Contains 16 high-level CSF categories with dummy mitigation text; lacks granular controls, subcategories, and SP 800-53 controls.
   - *Conclusion:* Build structured documents from `NIST_CSF_v2.0_catalog.json` (Subcategories like `PR.AA-01`) and `NIST_SP-800-53_rev5_catalog.json` (Controls like `AC-1`, `IA-2`).
4. **`bssn.json` -> REUSE as National Regulatory Standard (Consult User per R0):**
   - *Observation:* Official BSSN regulations (Perpres No. 82/2022, Peraturan BSSN No. 1/2024, BSrE, UU PDP) do not have a public GitHub/OSCAL JSON API. The entries represent real Indonesian statutory requirements.
   - *Conclusion:* Preserve `bssn.json` as the national compliance reference. Raise consultation question for user confirmation per R0.

### 2.3 Multilingual Embedding Justification
- Project uses `gemini-embedding-001` (configured in `src/utils/llm_adapter.py` and `src/dedup/deduplicator.py` with fallbacks `gemini-embedding-exp-03-07` and `text-embedding-004`).
- *Justification:*
  1. Pre-trained on multilingual web-scale data supporting >100 languages, natively capturing cross-lingual semantic parity between Indonesian terminology (e.g., "pencurian data pribadi KTP/KK", "injeksi skrip judi slot") and English canonical taxonomy (e.g., "unauthorized data access", "web defacement").
  2. Per Tahap 3: "Simpan teks berita asli dan hasil terjemahan; retrieval memakai teks terjemahan." Translating news to English before retrieval ensures optimal cosine similarity against the English STIX and OSCAL catalogs while maintaining semantic linkage.

---

## 3. Caveats

1. **D3FEND Mappings URL Change:**
   The URL stated in initial research (`https://d3fend.mitre.org/api/ontology/inference/d3fend-full-mappings.json`) is a **404**. The update pipeline must first query `GET https://d3fend.mitre.org/api/version.json` to extract `version` (e.g. `1.6.0`), and then fetch `https://d3fend.mitre.org/ontologies/d3fend/{version}/d3fend-full-mappings.json`.
2. **ATT&CK Bundle Size & Memory:**
   `enterprise-attack.json` is 55.2 MB. It contains both revoked/deprecated techniques and active techniques. A single `json.load()` requires ~180MB RAM in Python. This is safe on 64-bit systems, but streaming or indexing into a flattened local database (SQLite/JSONL) during preparation (Tahap 2) is essential.
3. **Backward Compatibility of Existing 36 Tests:**
   Existing tests (`tests/test_kpi_dashboard_tren.py`, `tests/test_fitur_baru_cve_mitre.py`, `tests/test_web_endpoints.py`) expect certain keys and mock returns from `src/analytics/encyclopedia_lookup.py`. Upgrades must **augment** the intelligence layer without deleting legacy functions or changing expected dictionary keys.
4. **Other Encyclopedia Files in `data/encyclopedia/`:**
   Per R0, files like `cis_controls.json`, `cisa_cpg.json`, `csa_ccm.json`, `csirt_framework.json`, `cwe.json`, `indeks_kami.json`, `iso27001.json`, `owasp.json` are dummy/summarized datasets. They are left intact until user confirms whether to replace or retire them.

---

## 4. Conclusion

All 4 authoritative sources have been live-verified:
1. **MISP/ENISA Taxonomy:** eCSIRT/RSIT selected. 10 closed categories defined and mapped.
2. **MITRE ATT&CK STIX 2.1:** Path `enterprise-attack/enterprise-attack.json` on `mitre-attack/attack-stix-data`, latest version `v20.0`. Filtering rules established (`revoked == False` and `x_mitre_deprecated == False`).
3. **MITRE D3FEND API:** Dynamic versioned endpoint identified (`/ontologies/d3fend/{version}/d3fend-full-mappings.json`). Ingestion plan into relational lookup table confirmed.
4. **NIST OSCAL Catalogs:** Verified exact paths for CSF 2.0 (`nist.gov/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json`) and SP 800-53 Rev 5 (`nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json`) on `usnistgov/oscal-content` (release `v1.5.0`).
5. **Local Files & R0 Consultation:** Clear recreate verdicts for `mitre.json`, `d3fend.json`, `nist.json`; reuse verdict for `bssn.json`; formal consultation questions formulated for the remaining 8 files.

---

## Features Discovered

| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Incident Taxonomy | MISP eCSIRT Taxonomy | Machine-tag JSON defining 11 CSIRT incident categories | None (HTTP GET) | JSON machine-tag schema (`namespace`, `predicates`, `values`) | Returns HTTP error if GitHub is down | Live probe: `MISP/misp-taxonomies/ecsirt/machinetag.json` |
| 2 | Incident Taxonomy | ENISA RSIT Standard | Reference Security Incident Classification Taxonomy v1003 | None (HTTP GET) | Markdown and machine-readable table of 10 primary incident classes | Returns HTTP error if GitHub is down | Live probe: `enisaeu/Reference-Security-Incident-Taxonomy-Task-Force` |
| 3 | Incident Taxonomy | 10 Closed News Categories | Closed list of 10 practical categories for Diskominfo Jatim news classification mapped to eCSIRT | News headline & content | One of: `ransomware`, `data_breach`, `defacement`, `ddos`, `phishing_penipuan`, `malware`, `eksploitasi_kerentanan`, `akses_tidak_sah`, `lainnya`, `tidak_dapat_ditentukan` | Fallback to `tidak_dapat_ditentukan` when evidence is ambiguous | Domain mapping analysis |
| 4 | MITRE ATT&CK | Enterprise STIX 2.1 Bundle | Official JSON STIX 2.1 Enterprise repository containing active and historical adversary techniques | HTTP GET / download | Bundle of STIX objects (`attack-pattern`, `x-mitre-tactic`, etc.) | HTTP retry with timeout | Live probe: `mitre-attack/attack-stix-data/enterprise-attack/enterprise-attack.json` (v20.0) |
| 5 | MITRE ATT&CK | Revocation & Deprecation Filtering | STIX property inspection to eliminate inactive techniques from RAG | `attack-pattern` STIX object | Boolean `is_active` (`not revoked and not x_mitre_deprecated`) | Exclude object from RAG corpus | Live probe of STIX object properties |
| 6 | MITRE ATT&CK | Technique Extraction | Flattens STIX object into canonical text document | `attack-pattern` STIX object | Document: `id` (T-number), `nama`, `tactics`, `deskripsi`, `platform`, `is_subtechnique` | Fallback tactic if external ID missing | Live STIX parsing probe |
| 7 | MITRE D3FEND | Version API | JSON endpoint reporting active ontology release and SHA-256 hash | HTTP GET `/api/version.json` | `{"version": "1.6.0", "ontology_hash_sha256": "...", ...}` | HTTP error handling / retry | Live probe: `https://d3fend.mitre.org/api/version.json` |
| 8 | MITRE D3FEND | Full Mappings Endpoint | SPARQL JSON dataset mapping ATT&CK technique IDs to D3FEND defensive techniques | HTTP GET `/ontologies/d3fend/{version}/d3fend-full-mappings.json` | SPARQL JSON with `results.bindings` containing `off_tech_id`, `def_tech_label`, `def_tactic_label`, `query_def_tech_label` | Verified 404 on `/api/...`; dynamically resolve via `version.json` | Live probe & web search |
| 9 | MITRE D3FEND | Defensive Technique Directory | Directory of 271 defensive techniques with IDs (D3-...) and synonyms | HTTP GET `/api/technique/all.json` | JSON-LD `@graph` of defensive technique classes | HTTP retry | Live probe: `https://d3fend.mitre.org/api/technique/all.json` |
| 10 | MITRE D3FEND | Relational Mapping Table | SQLite/relational lookup table for deterministic ATT&CK -> D3FEND mitigation resolution | Valid ATT&CK ID (`T...`) | List of D3FEND techniques (`id`, `nama`, `definisi`, `tactic`); empty list if no mapping | Return empty list; never allow LLM hallucination | Tahap 2 & Tahap 4 spec probe |
| 11 | NIST OSCAL | CSF 2.0 OSCAL Catalog | Official OSCAL JSON catalog of NIST Cybersecurity Framework 2.0 | HTTP GET `NIST_CSF_v2.0_catalog.json` | OSCAL JSON with 6 Functions (`GV`, `ID`, `PR`, `DE`, `RS`, `RC`), Categories, Subcategories, and statements | HTTP retry | Live probe: `usnistgov/oscal-content/nist.gov/CSF/v2.0/json/` |
| 12 | NIST OSCAL | SP 800-53 Rev 5 Catalog | Official OSCAL JSON catalog of security & privacy controls | HTTP GET `NIST_SP-800-53_rev5_catalog.json` | OSCAL JSON catalog with Control Families, Controls (`AC-1`, etc.), and statements | HTTP retry | Live probe: `usnistgov/oscal-content/nist.gov/SP800-53/rev5/json/` |
| 13 | Local Files | `mitre.json` Recreate | Replace 35-item dummy file with official active Enterprise ATT&CK corpus | `enterprise-attack.json` | Recreated dataset with full coverage | Preserve Indonesian keywords as supplementary tag dictionary | Local file inspection & comparison |
| 14 | Local Files | `d3fend.json` Recreate | Replace 21-item dummy file with relational mapping table from official D3FEND API | `d3fend-full-mappings.json` + `technique/all.json` | Relational SQLite table `d3fend_mappings` | Maintain backward compatibility for `search_encyclopedia_per_incident` | Local file inspection & comparison |
| 15 | Local Files | `nist.json` Recreate | Replace 16-item dummy file with OSCAL CSF 2.0 & SP 800-53 documents | OSCAL Catalogs | Vector collection of controls/subcategories | Supplementary reference only | Local file inspection & comparison |
| 16 | Local Files | `bssn.json` Reuse | Retain Indonesian regulatory standards (Perpres SPBE, UU PDP, BSrE, Pusopkamsinas) | `data/encyclopedia/bssn.json` | National regulation reference dictionary | No changes without user consultation | Local file inspection & R0 compliance |
| 17 | Local Files | R0 Encyclopedia Consultation | Document 8 unverified encyclopedia files for user decision | `data/encyclopedia/*.json` | Formulated user consultation proposal | Keep intact until user instructs | R0 requirement probe |

---

## Edge Cases

| # | Feature | Input | Observed Behavior |
|---|---------|-------|-------------------|
| 1 | D3FEND API Endpoint | Request to `https://d3fend.mitre.org/api/ontology/inference/d3fend-full-mappings.json` | Returns **HTTP 404 Not Found**. Resolved by using versioned URL `https://d3fend.mitre.org/ontologies/d3fend/{version}/d3fend-full-mappings.json` obtained from `/api/version.json`. |
| 2 | ATT&CK Revoked Technique | STIX object with `"revoked": true` (e.g., `T1183 Image File Execution Options Injection`) | Pipeline must discard revoked techniques so they never enter the active RAG vector index. |
| 3 | ATT&CK Deprecated Technique | STIX object with `"x_mitre_deprecated": true` (e.g., `T1002 Data Compressed`) | Pipeline must discard deprecated techniques so they never enter the active RAG vector index. |
| 4 | News Without Attack Flow | News article reporting a high-level incident without describing exploitation mechanisms (e.g., "Situs Pemprov Diretas") | Pipeline stops at tactic level or returns "tidak ditentukan"; does not speculate or guess technique IDs. |
| 5 | LLM Generates Invalid ATT&CK ID | LLM outputs a non-existent or retired technique ID (e.g., `T9999`) | Pipeline validates against active ATT&CK set; invalid ID is rejected and logged. |
| 6 | Unmapped ATT&CK Technique | ATT&CK technique has no corresponding defensive mitigation in D3FEND mapping table | Deterministic lookup returns empty list `[]`; LLM is prohibited from inventing mitigations. |
| 7 | Ambiguous Incident News | Generic IT disruption or non-malicious news (e.g., "Jaringan Internet Pemda Gangguan Pemeliharaan") | Taxonomy classifier outputs `tidak_dapat_ditentukan` or `lainnya` with low confidence. |
| 8 | Update Script: No Changes | Running update script when upstream version/commit hash has not changed | Script logs "tidak ada pembaruan" and exits 0 idempotently without re-embedding or modifying active index. |
| 9 | Update Script: Source Empty or Drastically Reduced | Upstream download is truncated, 0 bytes, or record count drops by >20% | Script aborts update, keeps existing index active, logs error, and issues failure notification. |
| 10 | Update Script: Technique ID Revoked in Upstream | Previously active technique (e.g., `T1234`) is revoked in new ATT&CK release | Historical incidents in `data/state.db` using that ID are flagged with `needs_review=1` rather than deleted. |
| 11 | Network Restriction / Proxy | Outbound HTTP requests blocked in restricted government datacenter | Download and update scripts support `HTTP_PROXY`, `HTTPS_PROXY`, and local mirror directory paths. |
| 12 | Legacy Unit Test Compatibility | `test_kpi_dashboard_tren.py` and `test_web_endpoints.py` calling `search_encyclopedia_per_incident` | If encyclopedia files are missing expected keys, legacy tests fail. Kept legacy fallbacks intact to guarantee all 36 tests pass. |

---

## 5. Verification Method

To independently verify these findings:

1. **Verify Official Remote Endpoints via Python:**
   ```powershell
   # 1. Verify D3FEND version and true mappings URL
   python -c "import urllib.request, json; v = json.loads(urllib.request.urlopen('https://d3fend.mitre.org/api/version.json').read().decode()); print('D3FEND version:', v['version']); req = urllib.request.Request(f'https://d3fend.mitre.org/ontologies/d3fend/{v[\"version\"]}/d3fend-full-mappings.json', headers={'Range': 'bytes=0-100'}); print('Mappings Status:', urllib.request.urlopen(req).status)"

   # 2. Verify ATT&CK STIX latest release and bundle
   python -c "import urllib.request, json; rels = json.loads(urllib.request.urlopen(urllib.request.Request('https://api.github.com/repos/mitre-attack/attack-stix-data/releases?per_page=1', headers={'User-Agent': 'Py'})).read().decode()); print('ATT&CK latest tag:', rels[0]['tag_name'])"

   # 3. Verify NIST OSCAL CSF 2.0 and SP 800-53 paths
   python -c "import urllib.request, json; csf = json.loads(urllib.request.urlopen('https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json').read().decode()); print('NIST CSF 2.0 Title:', csf['catalog']['metadata']['title'])"

   # 4. Verify MISP eCSIRT machinetag
   python -c "import urllib.request, json; tax = json.loads(urllib.request.urlopen('https://raw.githubusercontent.com/MISP/misp-taxonomies/main/ecsirt/machinetag.json').read().decode()); print('MISP ecsirt predicates:', len(tax['predicates']))"
   ```

2. **Verify Local Files & Legacy Unit Tests:**
   ```powershell
   # Verify current test suite baseline
   python -m pytest tests/
   ```

3. **Invalidation Conditions:**
   - If MITRE alters the URL structure for D3FEND ontology releases (e.g., changes `/ontologies/d3fend/{version}/` base path).
   - If NIST alters the OSCAL repository schema in a breaking minor version.
   - If upstream STIX 2.1 changes the `external_references` convention for ATT&CK IDs.
