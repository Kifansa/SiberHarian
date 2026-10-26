# Handoff Report: Codebase Survey & Architectural Analysis

**Agent**: explorer_survey_codebase  
**Date**: 2026-10-20  
**Target Milestone**: Discovery & Architectural Exploration  
**Status**: Complete  

---

## 1. Observation

### 1.1 Codebase Architecture & File Layout
The repository `D:\penting\magang\kominfo\NOTIFIKASI-BERITA` is an automated CTI (Cyber Threat Intelligence) monitoring, summarization, and reporting portal built for CSIRT Diskominfo Jawa Timur.

- **Directory Layout**:
  - `config/`: System configuration (`config.yaml`), classification and entity rules (`rules/` containing `publik_statistik.yaml`, `sektor_rules.yaml`, `keywords_jawa_timur.yaml`, etc.), and modular LLM prompts (`prompts/`).
  - `data/`: Core SQLite database (`data/state.db`), database backup (`data/state.db.bak`), sample dump (`data/pipeline_output_dump.json`), and encyclopedia folder (`data/encyclopedia/`). Note: An empty 0-byte file `state.db` exists in the repository root, but `src/storage/db.py:19` explicitly binds to `data/state.db` (`DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "state.db"`).
  - `src/`:
    - `src/pipeline_harian.py`: Entry point for batch news scraping, filtering, classification, and deduplication.
    - `src/scraper/`: RSS ingestion (international & domestic), Google News scraper, and `robots.txt` compliance validator (`pipeline.py`, `sources.py`, `extractor.py`, `robots_checker.py`).
    - `src/classifier/`: Relevance classifier (`relevance_classifier.py`) categorizing articles into `insiden_spesifik`, `analisis_relevan`, or `tidak_relevan` using Gemini API batch calls.
    - `src/dedup/`: Hybrid deduplication combining token similarity via RapidFuzz and batch semantic vector cosine similarity (`deduplicator.py`).
    - `src/summarizer/`: Modular news article summarizer in Indonesian using Gemini API (`llm_summarizer.py`).
    - `src/analytics/`:
      - `cti_agents.py`: Generates the 5-module SITREP CTI report (`### 1. INSIDEN MELONJAK DRASTIS`, `### 2. TREN INSIDEN MINGGUAN`, `### 3. VEKTOR SERANGAN TREN INSIDEN MINGGUAN`, `### 4. REKOMENDASI AKSI`, `### 5. PREDIKSI TREN ANCAMAN SIBER`).
      - `rag_engine.py`: Semantic retrieval of news context, organic threat extraction, and hybrid MITRE semantic mapping with cosine similarity and RapidFuzz fallback.
      - `trend_analyzer.py`: Analytical statistical aggregations (`susun_ringkasan_statistik_tren`, `susun_statistik_dashboard`, `hitung_distribusi_taktik_mitre`, `ekstrak_radar_cve_watchlist`).
      - `trend_predictor.py`: Orchestrates multi-agent trend prediction (`proses_prediksi_tren`) and regional 3-column analysis.
      - `pasca_proses.py`: Post-summarization pipeline writing records to `riwayat_tren`, managing the 14-day rolling retention window, and updating dashboard cache.
      - `encyclopedia_lookup.py`: Local JSON dictionary search across 12 frameworks.
    - `src/storage/`: SQLite access layer (`db.py`) managing tables, migrations, and transactional helper contexts.
    - `src/utils/`: LLM adapter (`llm_adapter.py`), embedding adapter (`embedding_adapter.py`), settings manager (`settings_manager.py`), logging, HTTP retry client.
    - `src/web/`: FastAPI web server (`app.py`), Jinja2 templates (`templates/admin.html`, `templates/index.html`, `templates/partials/_tren.html`), and modular client JS (`static/js/tren.js`, `static/js/tren/tren-kpi.js`, `static/js/tren/tren-ai-cards.js`, etc.).
  - `tests/`: 9 test files containing 36 automated unit and integration tests.
  - Runtime environment: Python 3.12.10, FastAPI 0.115.6, google-generativeai >= 0.8.0, rapidfuzz 3.10.1, pandas 2.2.3, pytest 9.1.1.

### 1.2 Baseline Test Suite Verification
Command executed: `python -m pytest tests/ -v`  
Result: **36 passed, 5 warnings in 14.09s** (Exit code 0).

The 36 tests and their respective modules:
1. `tests/test_25_case_studies.py`:
   - `test_evaluasi_80_studi_kasus_cti` (Evaluates 25 mock CTI edge cases against AI hallucinations, date leaks, 4-dimensional analysis, and encyclopedia tags).
2. `tests/test_embedding_and_rag.py`:
   - `TestEmbeddingFallbackAndRAG::test_config_yaml_embedding_fallback`
   - `TestEmbeddingFallbackAndRAG::test_embed_documents_fallback`
   - `TestEmbeddingFallbackAndRAG::test_embed_text_all_models_fail`
   - `TestEmbeddingFallbackAndRAG::test_embed_text_empty_input`
   - `TestEmbeddingFallbackAndRAG::test_embed_text_fallback_to_second_model`
   - `TestEmbeddingFallbackAndRAG::test_embed_text_primary_success`
   - `TestEmbeddingFallbackAndRAG::test_get_embedding_chain`
   - `TestEmbeddingFallbackAndRAG::test_legacy_strings_eradicated`
   - `TestEmbeddingFallbackAndRAG::test_rag_engine_double_loop_removed`
   - `TestEmbeddingFallbackAndRAG::test_settings_manager_embedding_config`
3. `tests/test_end_to_end_flow.py`:
   - `TestEndToEndFlow::test_dedup_and_relevance_flow` (End-to-end flow with mocks for embeddings, classifier, and summarizer).
4. `tests/test_fitur_baru_cve_mitre.py`:
   - `TestFiturBaruCveMitre::test_distribusi_taktik_mitre`
   - `TestFiturBaruCveMitre::test_ekstrak_radar_cve_watchlist`
   - `TestFiturBaruCveMitre::test_integrasi_statistik_tren_dan_dashboard`
5. `tests/test_gemini_rate_limiter.py`:
   - `TestAPIKeyPool::test_key_parsing`
   - `TestAPIKeyPool::test_rate_limited_rotation`
   - `TestGeminiRateLimiter::test_pacing_calculation`
   - `TestGeminiRateLimiter::test_rpm_limit_classification`
   - `TestBatchClassifier::test_batch_classification_fallback_on_empty`
   - `TestBatchClassifier::test_json_extraction_fallback_regex`
   - `TestBatchClassifier::test_json_extraction_valid`
6. `tests/test_kpi_dashboard_tren.py`:
   - `TestKpiDashboardTren::test_ancaman_baru_bukan_kata_acak_judul`
   - `TestKpiDashboardTren::test_ekstraksi_malware_spesifik_organik`
   - `TestKpiDashboardTren::test_hitung_tren_sektor_target_memiliki_growth_dan_persen`
   - `TestKpiDashboardTren::test_mitre_mapping_semantic_grounding`
   - `TestKpiDashboardTren::test_pola_serangan_tidak_terpotong_paksa`
   - `TestKpiDashboardTren::test_susun_statistik_dashboard_kpi_cards`
   - `TestKpiDashboardTren::test_top3_insiden_memiliki_mitre_mapping`
7. `tests/test_pipeline_e2e_integration.py`:
   - `TestPipelineE2EIntegration::test_database_endpoint_queries`
   - `TestPipelineE2EIntegration::test_normalisasi_poin_cti_edge_cases`
   - `TestPipelineE2EIntegration::test_proses_prediksi_tren_structure`
8. `tests/test_statistik_publik.py`:
   - `TestStatistikPublik::test_struktur_statistik_publik`
9. `tests/test_web_endpoints.py`:
   - `TestWebEndpoints::test_endpoint_api_tren`
   - `TestWebEndpoints::test_endpoint_ensiklopedia`
   - `TestWebEndpoints::test_endpoint_statistik_publik`

### 1.3 Database & State Survey (`data/state.db`)
Database inspection script executed on `data/state.db` confirmed:
- Tables:
  1. `konten_terkirim`: 2,821 records.
     - Columns: `identifier (TEXT PRIMARY KEY)`, `kategori (TEXT)`, `judul (TEXT)`, `sumber (TEXT)`, `tanggal_kirim (TEXT)`.
     - Purpose: Tracking previously processed articles to prevent duplicate scraping.
  2. `riwayat_tren`: 169 records.
     - Columns: `id (INTEGER PK AUTOINCREMENT)`, `kategori (TEXT)`, `identifier (TEXT)`, `judul (TEXT)`, `sumber (TEXT)`, `kata_kunci (TEXT)`, `kategori_relevansi (TEXT)`, `severity (TEXT)`, `vendor (TEXT)`, `tanggal_publish (TEXT)`, `tanggal_dicatat (TEXT)`, `ringkasan_atau_narasi (TEXT)`, `link (TEXT)`, `skor_cvss (REAL)`, `produk (TEXT)`.
     - Distribution: All 169 records have `kategori = 'berita'`. Within `kategori_relevansi`: 98 `insiden_spesifik`, 71 `analisis_relevan`.
     - Rolling retention: 14 days based on `tanggal_publish` (`bersihkan_riwayat_tren_lama` in `src/storage/db.py:200-208`).
  3. `prediksi_tren_terakhir`: 1 record (`id = 1`).
     - Columns: `id (INTEGER PK)`, `prediksi_berita (TEXT)`, `prediksi_cve (TEXT)`, `tanggal_dihitung (TEXT)`, `kasus_wilayah_ai (TEXT)`, `statistik_json (TEXT)`.
     - Size: `prediksi_berita` ~5,240 chars (the 5-section markdown), `kasus_wilayah_ai` ~4,160 chars, `statistik_json` ~20,251 chars.
  4. `metadata_sistem`: 1 record.
     - `waktu_terakhir_scraping` = `'2026-10-20 09:38:41'`.
  5. `pengaturan`: 20 records.
     - Key-value configuration for prompts, models, API keys, RSS feeds, and keywords.
  6. `admin_users`: 2 records (hashed passwords with bcrypt; default `superadmin` and `viewer`).
  7. `sqlite_sequence`: 2 records.
- Note: Root `state.db` was checked and found to be an empty 0-byte file without tables.

### 1.4 Existing Encyclopedia & Local CTI Files
Located in `data/encyclopedia/` (12 JSON files):
1. `mitre.json` (8,468 bytes, 212 lines):
   - Format: Array of objects with keys `{"id": "T1566", "tactic": "Initial Access", "technique": "Phishing", "keywords": [...]}`.
   - Coverage: Contains only ~25 hand-curated techniques with Indonesian keywords.
   - Missing: Descriptions, sub-techniques, platforms, revoked/deprecated flags, version metadata.
2. `d3fend.json` (8,753 bytes, 149 lines):
   - Format: Array of objects with keys `{"id": "D3-MFA", "tactic": "Credential Access Defense", "technique": "Multi-Factor Authentication", "keywords": [...], "mitigation": "..."}`.
   - Characteristics: Uses synthetic abbreviations (`D3-MFA`, `D3-DBR`, `D3-WAF`) rather than official D3FEND ontology IDs (`d3f:MultiFactorAuthentication` or technique IDs).
3. `nist.json` (6,183 bytes, 98 lines):
   - Format: Array of objects with keys `{"function": "Govern", "category": "GV.SC...", "keywords": [...], "mitigation": "..."}`.
   - Characteristics: A small curated selection of NIST CSF 2.0 categories with hardcoded Indonesian mitigation text.
4. `bssn.json` (3,053 bytes, 45 lines):
   - Format: Array of 7 objects (`BSSN-CSIRT`, `BSSN-PDP`, `BSSN-SPBE`, `BSSN-IIV`, `BSSN-TTE`, `BSSN-DEFACE`, `BSSN-RANSOM`) with regulatory citations.
5. Other files: `cis_controls.json`, `cisa_cpg.json`, `csa_ccm.json`, `csirt_framework.json`, `cwe.json`, `indeks_kami.json`, `iso27001.json`, `owasp.json`.
- Lookup Implementation (`src/analytics/encyclopedia_lookup.py`):
  - Searches by keyword matching: `_cocok_kata_kunci(e.get("keywords", []), terms_to_check)`.
  - Layered recommendations in `search_encyclopedia_per_incident()`: `taktis` (d3fend, cis_controls), `standar` (nist, iso27001, cisa_cpg), `nasional` (bssn, indeks_kami, csirt_framework), `aplikasi` (owasp, csa_ccm).

### 1.5 Admin Dashboard Architecture & The 5 Points from R3
Template: `src/web/templates/partials/_tren.html`  
Controller: `src/web/static/js/tren.js`  
Submodules: `src/web/static/js/tren/tren-kpi.js`, `src/web/static/js/tren/tren-ai-cards.js`  
API Provider: `GET /api/tren` in `src/web/app.py:315-390`

Mapping the 5 R3 Requirements:
1. **KPI `[ POLA ANCAMAN ]`**:
   - Template: `src/web/templates/partials/_tren.html:138-155`.
   - Elements: `<h4 class="...">[ POLA ANCAMAN ]</h4>`, value `<div id="kpi-pola-serangan">-</div>`, badge `<div id="kpi-pola-badge"><span id="kpi-pola-growth">+0%</span></div>`, subtext `<span id="kpi-pola-subtext">vs minggu lalu</span>`.
   - Client JS: `src/web/static/js/tren/tren-kpi.js:115-149`.
   - Data Source: `stat.prediksi_pola_serangan` (`pola` and `growth_persen`), computed by `RAGEngine.hitung_prediksi_pola_serangan()` (`src/analytics/rag_engine.py:165-218`).
   - Insertion strategy: The primary text shows the category/pattern; classification details and taxonomy labels can be displayed in an added badge, subtext, or tooltip without erasing the current string.
2. **"ANALISIS BERITA SIBER & REKOMENDASI MITIGASI" -> "INSIDEN MELONJAK DRASTIS"**:
   - Template: `src/web/templates/partials/_tren.html:204-220` with container `<div id="prediksi-berita-cards">`.
   - Backend Generator: `src/analytics/cti_agents.py:35-50` (`_generate_section_1_makro`), emitting markdown heading `### 1. INSIDEN MELONJAK DRASTIS`.
   - Client JS: Parsed and rendered as Card 1 by `renderLaporanCards()` in `src/web/static/js/tren/tren-ai-cards.js:109-116` & `284-303`.
   - Insertion strategy: Append taxonomy classification metadata (e.g. `[Taksonomi: Kategori - Subkategori]`) directly as an additional paragraph or badge in Section 1.
3. **"ANALISIS BERITA SIBER & REKOMENDASI MITIGASI" -> "TREN INSIDEN MINGGUAN"**:
   - Backend Generator: `src/analytics/cti_agents.py:51-70` (`_generate_section_2_mikro`), emitting markdown heading `### 2. TREN INSIDEN MINGGUAN`.
   - Client JS: Parsed and rendered as Card 2 by `src/web/static/js/tren/tren-ai-cards.js:118-125`.
   - Insertion strategy: In each bullet item of the 3 micro-incidents, append the verified incident taxonomy category alongside the incident narrative.
4. **Subsection "VEKTOR SERANGAN TREN INSIDEN MINGGUAN"**:
   - Backend Generator: `src/analytics/cti_agents.py:71-107` (`_generate_section_3_vektor`), emitting markdown heading `### 3. VEKTOR SERANGAN TREN INSIDEN MINGGUAN`.
   - Client JS: Parsed and rendered as Card 3 by `src/web/static/js/tren/tren-ai-cards.js:127-134`.
   - Data Source: Currently supplied via `inc.get("mitre_mapping", [])` computed by `RAGEngine.map_incident_to_mitre_semantic()`.
   - Insertion strategy: Enrich the MITRE ATT&CK reference with verified STIX metadata (Technique ID, Technique Name, Tactic) without altering the incident narrative structure.
5. **Mitigasi / Rekomendasi Aksi Section**:
   - Backend Generator: `src/analytics/cti_agents.py:121-134` (`_generate_section_4_rekomendasi`), emitting markdown heading `### 4. REKOMENDASI AKSI`.
   - Client JS: Parsed and rendered as Card 4 by `src/web/static/js/tren/tren-ai-cards.js:136-143`.
   - Data Source: Currently populated by `inc.get("mitigasi_ensiklopedia", [])` from `search_encyclopedia_per_incident()`.
   - Insertion strategy: Retain existing prescriptive format and substitute/augment with deterministic lookup mitigations mapped strictly via MITRE D3FEND table and NIST OSCAL catalog.

### 1.6 LLM & Embedding Pipeline Architecture
- Configured in `config/config.yaml` and dynamic database table `pengaturan`.
- Adapter: `src/utils/llm_adapter.py`.
- Primary embedding model: `gemini-embedding-001`.
- Embedding fallbacks: `gemini-embedding-exp-03-07`, `text-embedding-004`.
- Rate limiting (`GeminiRateLimiter`):
  - Embedding: 80 RPM.
  - Flash-Lite: 12 RPM.
  - Flash: 4 RPM.
- Quota management (`APIKeyPool`):
  - Parses comma/newline-separated API keys.
  - Auto-rotates to backup keys upon HTTP 429 quota errors with a 60-second cooldown timer.
- Batch embedding: `GeminiLLMAdapter.embed_documents()` processes in batches of 50 with automatic fallback to per-item embedding if batch fails.

---

## 2. Logic Chain

1. **Premise 1 (Codebase state)**: All 36 existing tests pass, and the application functions smoothly on FastAPI + SQLite + Google Gemini API.
2. **Premise 2 (Database state)**: `data/state.db` contains 169 historical news articles (`riwayat_tren`) and 2,821 logged identifiers. This database provides the historical corpus from which draft datasets and evaluation test cases can be sampled. Root `state.db` is an inert artifact and must remain untouched or safely ignored.
3. **Premise 3 (Encyclopedia state)**: The local JSON files in `data/encyclopedia/` (`mitre.json`, `d3fend.json`, `nist.json`, `bssn.json`) are lightweight synthetic/dummy files created for basic keyword matching. They lack STIX 2.1 schemas, revoked/deprecated flags, deterministic ATT&CK-to-D3FEND relational linkages, and OSCAL structures.
4. **Premise 4 (Decision on local files)**:
   - `mitre.json`: **Rebuild from official STIX 2.1**. The current file has only 25 techniques, no sub-techniques, no platform filters, and no revoked tracking. Rebuilding from `enterprise-attack.json` satisfies R1 and R2.
   - `d3fend.json`: **Rebuild from official D3FEND API**. Current file uses custom dummy keys (`D3-MFA`, `D3-DBR`) and keyword matching. Rebuilding as a deterministic relational mapping table (`ATT&CK ID -> D3FEND techniques`) ensures LLM cannot hallucinate defensive techniques.
   - `nist.json`: **Rebuild from official NIST OSCAL content**. Current file contains non-standard excerpts. Rebuilding one document per control/subcategory ensures official provenance.
   - `bssn.json`: **Keep as local policy reference, ask user before modifying or removing** (as required by R0: "Untuk file yang sumber resminya tidak disebut dalam spesifikasi... tanya user dulu").
5. **Premise 5 (Multilingual justification for `gemini-embedding-001`)**: `gemini-embedding-001` and its fallback `text-embedding-004` are dense multilingual neural models trained on global corpora. In SiberHarian, cyber incidents frequently mix Indonesian terms ("kebocoran data", "peretasan portal pemda") with English technical terminology ("credential stuffing", "remote code execution", "phishing lure"). A unified multilingual embedding space ensures semantic alignment between Indonesian incident narratives and English ATT&CK/NIST standards without cross-lingual semantic drift.
6. **Premise 6 (Dashboard integration compliance)**: The 5 points required by R3 cleanly map to 1 KPI element (`kpi-pola-serangan`) and 4 markdown section generators (`_generate_section_1_makro`, `_generate_section_2_mikro`, `_generate_section_3_vektor`, `_generate_section_4_rekomendasi`). Adding validated taxonomy labels, ATT&CK T-numbers, and D3FEND/NIST recommendations strictly enriches existing text without removing existing headings or sentences.

---

## 3. Caveats

1. **Internet Fetch & Official Endpoints**: This exploration was performed locally without making outgoing external network calls to GitHub or D3FEND API. Live URL/path validation will be executed during the download/staging implementation phase.
2. **Deprecation Warnings**: 5 warnings were observed during pytest execution (google-auth PQC deprecation, google.generativeai deprecation recommendation to migrate to google.genai, FastAPI on_event deprecation, Starlette testclient httpx warning). None of these break existing tests, but they indicate future library upgrade considerations.
3. **Draft Evaluation Dataset**: There are 169 news articles currently in `data/state.db`. A draft manual labeling tool/script should be structured to allow administrative CTI review of these 169 articles (plus synthetic/expanded test cases) to reach the 200–500 evaluation benchmark required by Stage 6.

---

## 4. Conclusion

The codebase is healthy, well-tested (36/36 tests passing), cleanly modularized, and ready for the Layered Intelligence upgrade.

Key architectural recommendations for the implementer:
1. **Staging & Ingestion**: Store downloaded official data in `data/raw/<source>/<date>/` with metadata JSON (version, URL, download timestamp, SHA-256).
2. **CTI Data Storage**:
   - ATT&CK, Taxonomy, and NIST: Flatten into document structures with full provenance metadata (`source`, `source_version`, `original_id`, `ingest_date`) and index into separate vector collections.
   - D3FEND: Store as a SQLite relational mapping table (`mitre_attack_id` -> `d3fend_technique_id`, `d3fend_name`, `d3fend_tactic`, `definition`). Lookups MUST be deterministic SQL queries, not vector similarity.
3. **Pipeline Integration**:
   - In `src/classifier/` and `src/analytics/cti_agents.py`, preserve existing text while appending the structured validated taxonomy and technique tags.
   - Maintain strict backwards compatibility so that all existing 36 tests continue to pass.

---

## 5. Verification Method

To independently verify the observations and findings in this report:
1. Run the test suite:
   ```powershell
   python -m pytest tests/ -v
   ```
   *Expected result*: Exactly 36 tests pass.
2. Inspect the SQLite database tables and row counts:
   ```powershell
   python -c "import sqlite3; conn = sqlite3.connect('data/state.db'); print([(t[0], conn.execute(f'SELECT count(*) FROM {t[0]}').fetchone()[0]) for t in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()])"
   ```
   *Expected result*: Tables `konten_terkirim` (2,821), `riwayat_tren` (169), `prediksi_tren_terakhir` (1), `metadata_sistem` (1), `pengaturan` (20), `admin_users` (2).
3. Inspect the encyclopedia registry:
   Check `src/analytics/encyclopedia_lookup.py:10-23` and `data/encyclopedia/`.
4. Inspect the 5 dashboard points:
   - Check `src/web/templates/partials/_tren.html` lines 140, 207, 216.
   - Check `src/web/static/js/tren/tren-kpi.js` lines 116-149.
   - Check `src/web/static/js/tren/tren-ai-cards.js` lines 54-95, 109-152, 284-303.
   - Check `src/analytics/cti_agents.py` lines 35-185.
