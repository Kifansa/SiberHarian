# Handoff Report: Survey for R3 (Whole-Project Hardcode Audit), Dynamic Multi-Dataset Proof, & Regression Baseline

**Agent**: `explorer_survey_3`  
**Date**: 2026-10-21  
**Working Directory**: `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\explorer_survey_3`  
**Mission**: Whole-Project Hardcode & Directed Results Audit (R3), Dynamic Multi-Dataset Acceptance Testing Architecture, and Existing Test Suite Regression Baseline.

---

## 1. Observation

### 1.1 Existing Test Suite Baseline (pytest)
Execution command: `python -m pytest tests/`
Direct execution result:
- **Total Tests Collected**: 241 items
- **Result**: `241 passed, 5 warnings in 320.10s` (Exit code 0).
- **Test File Distribution**:
  1. `tests/test_25_case_studies.py`: 1 passed (parameterized 25 case studies)
  2. `tests/test_cti_e2e_suite.py`: 150 passed
  3. `tests/test_cti_m1_m2.py`: 7 passed
  4. `tests/test_cti_m3_m4.py`: 22 passed
  5. `tests/test_cti_m5.py`: 14 passed
  6. `tests/test_cti_m6_m7.py`: 12 passed
  7. `tests/test_embedding_and_rag.py`: 10 passed
  8. `tests/test_end_to_end_flow.py`: 1 passed
  9. `tests/test_fitur_baru_cve_mitre.py`: 3 passed
  10. `tests/test_gemini_rate_limiter.py`: 7 passed
  11. `tests/test_kpi_dashboard_tren.py`: 7 passed
  12. `tests/test_pipeline_e2e_integration.py`: 3 passed
  13. `tests/test_statistik_publik.py`: 1 passed
  14. `tests/test_web_endpoints.py`: 3 passed

---

### 1.2 Whole-Project Audit Findings: Hardcoded Values, Fallbacks, & Directed Logic

#### A. KPI Values, Fallbacks, and Empty-State Defaults
1. **`src/analytics/trend_analyzer.py:891-893`**:
   ```python
   except Exception as err:
       logger.warning(f"Gagal menghitung prediksi pola serangan/ancaman: {err}")
       pola_serangan = {"pola": "RCE", "growth_persen": 0.0, "subteks": "Stabil"}
       ancaman_baru = "Menunggu Sinyal"
   ```
   - *Observation*: `"pola": "RCE"` is hardcoded as an exception fallback. If the RAG engine throws an error or fails, the dashboard displays `"RCE"` as the attack pattern.

2. **`src/analytics/rag_engine.py:457-465, 494-514`**:
   ```python
   fallback = {
       "pola": "Insiden Dominan",
       "pola_lengkap": "Insiden Dominan",
       "growth_persen": 0.0,
       "jumlah_terkini": 0,
       "tingkat_risiko": "SEDANG",
       "subteks": "vs minggu lalu",
       "taksonomi_resmi": "Akses Tidak Sah / Pembobolan Akun"
   }
   ...
   if not taksonomi_resmi:
       ...
       else:
           taksonomi_resmi = "Akses Tidak Sah / Pembobolan Akun"
   ```
   - *Observation*: Hardcoded taxonomy category `"Akses Tidak Sah / Pembobolan Akun"` is returned whenever `self.df_berita.empty` or when regex keyword heuristics match nothing.

3. **`src/analytics/rag_engine.py:484-490`**:
   ```python
   for _, r in df_terkini.iterrows():
       ident = r.get("identifier")
       if ident:
           rec = ambil_intelijen_berita(ident)
           if rec and rec.get("kategori_insiden") and rec.get("kategori_insiden") != "Tidak Dapat Ditentukan":
               taksonomi_resmi = rec.get("kategori_insiden")
               break
   ```
   - *Observation*: Directed logic: Instead of aggregating across all weekly news items, it takes the taxonomy category of the *first* article found and immediately breaks the loop.

4. **`src/analytics/rag_engine.py:739-745, 775-801`**:
   ```python
   if self.df_berita.empty:
       return {
           "ada": False,
           "nama": "Menunggu Sinyal",
           "jenis_serangan": "Kondisi Stabil",
           "uraian": "(Tidak ada ancaman baru)",
           "sumber": "-"
       }
   ...
   row_first = df_terkini.iloc[0]
   ent = extract_threat_entity_organic(row_first.get("judul", ""), ...)
   ```
   - *Observation*: [ SINYAL ANCAMAN BARU ] currently relies on `extract_threat_entity_organic` from a single article (`df_terkini.iloc[0]`), returning arbitrary extracted strings like `"Ratusan Supermarket Prancis"` instead of a rising taxonomy threat category.

5. **`src/web/static/js/tren/tren-kpi.js:151-166` & `src/web/templates/partials/_tren.html:153`**:
   ```javascript
   if (kpiPolaTaxonomy) {
     let labelTaxonomy = polaData.taksonomi_resmi || polaData.kategori_taksonomi;
     if (!labelTaxonomy) {
       const npl = namaPola.toLowerCase();
       ...
       else labelTaxonomy = 'Akses Tidak Sah / Pembobolan Akun';
     }
     kpiPolaTaxonomy.textContent = `Taksonomi Resmi: [${labelTaxonomy}]`;
   }
   ```
   - *Observation*: Frontend hardcodes fallback to `'Akses Tidak Sah / Pembobolan Akun'` and formats badge `Taksonomi Resmi: [label]` into `<span id="kpi-pola-taxonomy-badge">` in `_tren.html:153`.

---

#### B. Charts and Tables Data Generation
6. **`src/analytics/trend_analyzer.py:303-305`**:
   ```python
   if not taktik_counter:
       taktik_counter["Initial Access"] = max(1, len(df_terkini))
   ```
   - *Observation*: Directed / fabricated chart data. If no MITRE tactics match the news corpus, it artificially sets `"Initial Access"` with a frequency count equal to `len(df_terkini)`, forcing the tactics chart to show 100% "Initial Access".

7. **`src/analytics/trend_analyzer.py:421-429` & `config/rules/sektor_rules.yaml`**:
   ```python
   for _, row in df_sub.iterrows():
       teks = (str(row.get("judul", "")) + " " + str(row.get("ringkasan_atau_narasi", "")) + " " + str(row.get("kata_kunci", ""))).lower()
       for s_nama, s_words in SEKTOR_RULES.items():
           if any(w in teks for w in s_words):
               counts[s_nama] += 1
   ```
   - *Observation*: Sektor Target Terpapar uses crude substring regex matching on non-IIV keywords ("developer", "rust", "wordpress", "whatsapp", "warga", "konsumen") rather than LLM classification with verbatim evidence quotes from the article.

8. **`src/storage/db.py:590-591`**:
   ```python
   if not top_sektor:
       top_sektor = [{"sektor": s, "jumlah": 0, "growth_persen": 0.0} for s in list(sektor_rules.keys())[:5]]
   ```
   - *Observation*: When no news matches sectors, it synthesizes 5 dummy sectors with 0 count to populate public statistics.

---

#### C. SITREP 5 Parts in "ANALISIS BERITA SIBER & REKOMENDASI MITIGASI"
*(Constraint: Do NOT modify SITREP findings before user chooses options per finding!)*

9. **`src/analytics/cti_agents.py:124-129` (Section 1: INSIDEN MELONJAK DRASTIS)**:
   ```python
   if not found_from_db:
       pola = (data_makro or {}).get("nama_pola", "Akses Tidak Sah")
       lines.append("- **Akses Tidak Sah / Pembobolan Akun** (eCSIRT: intrusions:account-compromise): Dominan pada perimeter portal publik")
       lines.append(f"- **Eksploitasi Kerentanan (Exploit / Zero-Day)** (eCSIRT: intrusion-attempts:ids-alert): Pola ancaman melonjak ({pola})")
       lines.append("- **Malware / Infostealer** (eCSIRT: malicious-code:malware): Terdeteksi penyebaran payload aktif")
   ```
   - *Observation*: Hardcoded fake analysis bullets when SQLite table `intelijen_berita_tervalidasi` is empty. Claims specific threats ("Dominan pada perimeter portal publik", "Terdeteksi penyebaran payload aktif") without data.

10. **`src/analytics/cti_agents.py:148-151` (Section 3: VEKTOR SERANGAN TREN INSIDEN MINGGUAN)**:
    ```python
    else:
        tid = "T1190"
        tname = "Exploit Public-Facing Application"
        ttactic = "Initial Access"
    ```
    - *Observation*: Hardcoded MITRE ATT&CK fallback technique `T1190: Exploit Public-Facing Application` with tactic `Initial Access` when no mapping exists.

11. **`src/analytics/cti_agents.py:186-191` (Section 4: REKOMENDASI AKSI - D3FEND)**:
    ```python
    else:
        fallback_id = "D3-MFA"
        if fallback_id not in seen_d3:
            seen_d3.add(fallback_id)
            d3_lines.append(f"- **[D3-MFA] Multi-Factor Authentication** (Taktik: Credential Access Defense) untuk mitigasi {tid}: Wajibkan MFA berbasis token fisik atau aplikasi authenticator.")
    ```
    - *Observation*: Hardcoded D3FEND fallback ID `[D3-MFA]`. If D3FEND SQL lookup returns no record for the technique, code invents `[D3-MFA]` rather than adhering to strictly deterministic lookup.

12. **`src/analytics/cti_agents.py:209-211, 336` (Section 4: REKOMENDASI AKSI - NIST)**:
    ```python
    nist_lines.append("- **[AC-2] Account Management** (NIST SP 800-53 Rev 5): Pengelolaan kredensial dan hak akses terpusat.")
    nist_lines.append("- **[PR.AC-1] Identities and Credentials** (NIST CSF 2.0): Autentikasi dan identitas pengguna terlindungi.")
    ...
    mit_items = "\n".join(...) if mitigasi_valid else "- [D3-MFA] Wajibkan autentikasi multifaktor berbasis token pada seluruh akses administratif.\n- [NIST PR.AC] Terapkan segmentasi jaringan dan prinsip hak akses minimal."
    ```
    - *Observation*: Hardcoded NIST controls `[AC-2]` and `[PR.AC-1]` when file reading fails or no controls match.

13. **`src/analytics/cti_agents.py:398-420, 434-446` (_buat_fallback_sitrep_deterministik)**:
    ```python
    def _deteksi_sektor_spesifik(teks: str) -> str: ... return 'Layanan Publik Daerah'
    def _deteksi_senjata_spesifik(teks: str) -> str: ... return 'Akses Ilegal & Eksploitasi Web'
    def _deteksi_dampak_spesifik(teks: str) -> str: ... return 'Gangguan Integritas Sistem'
    ...
    laporan[1] += f'\n- **Target {sektor}**: Menggunakan metode {senjata} pada kasus {nama}.'
    laporan[2] += f'\n- **Alur Serangan {nama}**: Terpetakan pada taktik Initial Access via eksploitasi celah web. Dampak: {fakta[:120]}...'
    ```
    - *Observation*: Heuristic fallback sentences assembled from fixed string templates when in instant RAG mode or LLM failure.

---

#### D. Regional Cases (Kasus Wilayah / Jawa Timur / Kab/Kota)
14. **`src/analytics/trend_predictor.py:206-219, 236-247`**:
    ```python
    fallback_kosong = {
        "internasional": {
            "ada_kejadian": False, "isu_utama": "Kondisi Kondusif", "nama_kejadian": "-", "ringkasan_kasus": "", "kategori": "-",
            "lokasi": "Global",
            "alasan_urgensi": "- **Nihil Insiden Kritis**: Nihil anomali berkategori tinggi dalam 7 hari terakhir.",
            "potensi_ancaman": "- **Kesiapsiagaan**: Fokus pada audit celah sistem dan mitigasi vektor serangan aktif.", ...
        },
        ...
        "jawa_timur": {
            "ada_kejadian": False, "isu_utama": "Kondisi Kondusif", "nama_kejadian": "-", "ringkasan_kasus": "", "kategori": "-",
            "lokasi": "Jawa Timur",
            "alasan_urgensi": "- **Nihil Anomali**: Nihil anomali insiden siber yang menargetkan portal OPD di Jawa Timur dalam 7 hari terakhir.",
            "potensi_ancaman": "- **Kesiapsiagaan Preventif**: Pengetatan autentikasi multifaktor dan literasi keamanan siber ASN.", ...
        }
    }
    ```
    - *Observation*: Fixed multi-bullet strings presented as strategic regional CTI assessments when 0 incidents occurred.

15. **`src/web/static/js/tren/tren-wilayah.js:326-360`**:
    ```javascript
    const intlItem = aiData.internasional || (stat.kasus_wilayah?.internasional?.[0] ? {
      ada_kejadian: true,
      isu_utama: "Kebocoran Data",
      alasan_urgensi: "Insiden paling ramai dibicarakan media internasional dalam 7 hari terakhir.",
      potensi_ancaman: "Potensi eskalasi serangan siber global dan eksploitasi celah serupa.", ...
    } : null);
    ...
    const jatimItem = aiData.jawa_timur || (stat.kasus_wilayah?.jawa_timur?.[0] ? {
      ada_kejadian: true,
      isu_utama: "Pembajakan Akun",
      alasan_urgensi: "Insiden berdampak langsung pada entitas daerah di wilayah Jawa Timur.",
      potensi_ancaman: "Risiko peretasan web, kebocoran basis data, atau penyalahgunaan portal instansi.", ...
    } : null);
    ```
    - *Observation*: Frontend hardcoded fallbacks inject `"Kebocoran Data"` (Intl) and `"Pembajakan Akun"` (Jatim) if `aiData` is missing.

---

#### E. Public Statistics
16. **`src/storage/db.py:637, 650, 674-679`**:
    ```python
    sektor_utama = top_sektor[0]["sektor"] if top_sektor and top_sektor[0]["jumlah"] > 0 else "Infrastruktur Vital"
    ...
    "nilai": f"{top_cat['kategori']}" if top_cat["jumlah"] > 0 else "Kondisi Terkendali"
    ...
    takeaway_chart = ... if top_cat["jumlah"] > 0 else (
        "Aktivitas ancaman digital terpantau stabil tanpa anomali lonjakan masif pada periode pemantauan terkini."
    )
    ```
    - *Observation*: Masks empty DB with `"Kondisi Terkendali"` and `"Infrastruktur Vital"`.

---

### 1.3 Tests Directly Affected & Needing Documented Adaptation
Survey of existing 241 tests reveals the following specific tests that assert old behaviors:
1. `tests/test_cti_m5.py::test_titik_1_kpi_html_elements_preserved_and_taxonomy_badge_present`:
   - Line 184: `self.assertIn('id="kpi-pola-taxonomy-badge"', content)` and `self.assertIn('Taksonomi Resmi:', content)`.
   - *Conflict*: R1 explicitly removes the badge `Taksonomi Resmi: [...]` from the HTML and UI.
2. `tests/test_cti_m5.py::test_titik_1_kpi_js_no_confidence_percentage`:
   - Line 208: `self.assertIn('kpiPolaTaxonomy.textContent = \`Taksonomi Resmi: [\${labelTaxonomy}]\`', content)`.
   - *Conflict*: Badge text assignment removed under R1.
3. `tests/test_cti_e2e_suite.py::test_t1_f14_kpi_pola_ancaman_additive_badge`:
   - Line 1566: Asserts presence of `id="kpi-pola-taxonomy-badge"` in `_tren.html` and `Taksonomi Resmi: [${labelTaxonomy}]` in `tren-kpi.js`.
   - *Conflict*: Directly asserts the badge that R1 mandates to be removed.
4. `tests/test_kpi_dashboard_tren.py::test_ancaman_baru_bukan_kata_acak_judul`:
   - Line 58: `self.assertIn("ZERO-DAY", ancaman_kpi.upper())`.
   - *Conflict*: Asserts entity-level string ("ZERO-DAY") rather than a closed taxonomy category under R2.
5. `tests/test_kpi_dashboard_tren.py::test_ekstraksi_malware_spesifik_organik`:
   - Line 79: `self.assertIn("TASK#STOMP", ancaman.upper())`.
   - *Conflict*: Asserts organic entity extraction of malware name instead of taxonomy under R2.

---

## 2. Logic Chain

1. **Premise 1 (R1 & R2 Requirements)**:
   - R1 dictates: "[ POLA ANCAMAN ] primary value is the dominant taxonomy category this week (from closed taxonomy list eCSIRT 11 categories), along with its count and growth. Badge 'Taksonomi Resmi: [...]' is deleted."
   - R2 dictates: "[ SINYAL ANCAMAN BARU ] primary value is a rising taxonomy category with >= 2 cases this week that is new (novelty > volume; 1 single case is NOT enough). Entity strings like 'Ratusan Supermarket Prancis' must be replaced."
   - *Connection*: Observation 1.2 (items 1, 2, 3, 4, 5) shows that the existing codebase currently uses `extract_threat_entity_organic` and first-record break, while injecting `Taksonomi Resmi: [...]` as an auxiliary badge. The existing tests in Observation 1.3 test this old badge and old entity behavior. Thus, those specific assertions will fail once R1 and R2 are implemented unless adapted and documented.

2. **Premise 2 (R3 Whole-Project Hardcode Audit & User Decision Constraint)**:
   - R3 dictates: "Audit whole project: find hardcoded values, static fallbacks acting as fake analysis, defaults masking empty data. For section ANALISIS BERITA SIBER & REKOMENDASI MITIGASI, provide options to user per finding (Fix with X vs Keep as is with risks). Do NOT change findings before user decides, except R1, R2, R4."
   - *Connection*: Observations 1.2 items 9 through 13 catalogue exact file and line numbers of the SITREP 5 parts in `cti_agents.py`. These must be presented as structured options for user choice and NOT changed unilaterally during R1/R2/R4 work.

3. **Premise 3 (Dynamic Two-Dataset Acceptance Testing Proof)**:
   - Requirement: Prove via automated tests on two different datasets that changing/adding news dynamically updates [ POLA ANCAMAN ], [ SINYAL ANCAMAN BARU ], and [ SEKTOR TARGET TERPAPAR ].
   - *Connection*: Observations in `test_cti_m6_m7.py` and `test_cti_m3_m4.py` show that isolated SQLite test databases (`tmp_path / "test_state.db"`) with `init_db(db_path)` and `pd.DataFrame` feeds can be constructed with zero reliance on production data. By executing the calculation pipeline on Dataset A (Ransomware dominant, Keuangan target) vs Dataset B (Data Breach dominant, Eksploitasi Kerentanan new signal with 2 cases, Kesehatan target, 1 isolated Phishing case), we produce mathematical proof that all three values change dynamically without hardcoded strings.

---

## 3. Caveats

1. **Unmodified Production Files**: Per explorer role rules, no production code was modified during this survey.
2. **Untouched Constraints**: Files `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` and directory `LAPORAN DASHBOARD ADMIN/` were strictly NOT opened or touched.
3. **Execution Runtime**: Full test suite runs 241 tests in ~320 seconds on Windows because of crypto, hashing, and vector distance operations. Fast targeted test runs (e.g. `pytest tests/test_kpi_dashboard_tren.py`) should be used during implementation cycles.

---

## 4. Conclusion & Actionable Recommendations

### 4.1 Catalog of Options for User Decision (SITREP Section 1–5 in `ANALISIS BERITA SIBER & REKOMENDASI MITIGASI`)

| No | Location | Finding / Issue | UI Impact | Option A (Fix) | Option B (Keep As Is) |
|---|---|---|---|---|---|
| 1 | `src/analytics/cti_agents.py:124-129` | Hardcoded eCSIRT distribution when `intelijen_berita_tervalidasi` is empty | Section 1 displays 3 fixed bullet points ("Dominan pada perimeter portal publik", etc.) even with 0 news | Output: `"- (Belum ada data distribusi taksonomi tervalidasi pada periode ini)"` | Keep current fallback text. *Risk*: Falsely informs CSIRT of non-existent active malware/exploit surges. |
| 2 | `src/analytics/cti_agents.py:148-151` | Hardcoded MITRE ATT&CK technique fallback to `T1190: Exploit Public-Facing Application` | Section 3 displays T1190 with official URL for any incident lacking mapping | Display `"- Alur serangan tidak terpetakan pada teknik spesifik ATT&CK"` (stop at tactic level) | Keep T1190 fallback. *Risk*: Falsely attributes all unmapped attacks to web application exploits. |
| 3 | `src/analytics/cti_agents.py:186-191` | Hardcoded D3FEND fallback ID `[D3-MFA]` when D3FEND SQL lookup is empty | Section 4 fabricates `[D3-MFA]` when no technique mapping exists | If SQL lookup returns empty, display `"- Tidak ditemukan pemetaan mitigasi D3FEND spesifik untuk teknik ini"` | Keep `[D3-MFA]`. *Risk*: Violates deterministic lookup requirement. |
| 4 | `src/analytics/cti_agents.py:209-211, 336` | Hardcoded NIST controls `[AC-2]` and `[PR.AC-1]` when lookup fails | Section 4 always shows AC-2 and PR.AC-1 | Display `"- Referensi kontrol NIST tambahan tidak tersedia"` | Keep static AC-2 and PR.AC-1. *Risk*: Fakes NIST grounding without retrieval. |
| 5 | `src/analytics/cti_agents.py:398-420, 434-446` | Template heuristics with fallbacks (`'Layanan Publik Daerah'`, `'Akses Ilegal & Eksploitasi Web'`) | Section 2 & 3 in Instant RAG mode outputs synthetic guessed phrases | Only output facts explicitly present in article without guessing methods/dampaks | Keep heuristics. *Risk*: Hallucinates generic attacker methods. |

---

### 4.2 Two-Dataset Dynamic Proof Architecture (Acceptance Criteria)

Create `tests/test_dynamic_multi_dataset.py` with two explicit, isolated datasets:
- **Dataset 1**:
  - Baseline (7 days prior): 5 `Ransomware` articles (Sector: Keuangan).
  - Current (last 7 days): 8 `Ransomware` articles (Sector: Keuangan).
  - Expected:
    - `[ POLA ANCAMAN ]` = `"Ransomware"` (+60.0% growth, count 8)
    - `[ SINYAL ANCAMAN BARU ]` = `"Kondisi Stabil"` / `"Menunggu Sinyal"` (no emerging category)
    - `[ SEKTOR TARGET TERPAPAR ]` = `"Keuangan"` (top sector)
- **Dataset 2**:
  - Baseline: 8 `Ransomware` articles (Sector: Keuangan), 0 `Eksploitasi Kerentanan`, 0 `Phishing`.
  - Current: 4 `Ransomware` articles (Sector: Keuangan), 3 `Eksploitasi Kerentanan (Exploit / Zero-Day)` articles (Sector: Kesehatan), 1 `Phishing / Penipuan Siber` article (Sector: Administrasi Pemerintahan).
  - Expected:
    - `[ POLA ANCAMAN ]` = `"Ransomware"` (dominant volume, count 4)
    - `[ SINYAL ANCAMAN BARU ]` = `"Eksploitasi Kerentanan (Exploit / Zero-Day)"` (emerged this week with 3 cases >= 2, novelty > volume)
    - `Phishing` with 1 case is rejected as signal (proves the rule: 1 case is not enough)
    - `[ SEKTOR TARGET TERPAPAR ]` = `"Kesehatan"` (shifted to newly targeted sector with verified quote)
- Assertions comparing Dataset 1 and Dataset 2 outputs prove 100% dynamic behavior.

---

### 4.3 Regression & Test Adaptation Plan
When implementing R1, R2, and R4:
1. In `tests/test_cti_m5.py`:
   - Adapt `test_titik_1_kpi_html_elements_preserved_and_taxonomy_badge_present`: assert `kpi-pola-serangan` displays taxonomy; assert `kpi-pola-taxonomy-badge` is absent.
   - Adapt `test_titik_1_kpi_js_no_confidence_percentage`: assert `kpiPola.textContent = polaData.kategori_taksonomi || polaData.pola`.
2. In `tests/test_cti_e2e_suite.py`:
   - Adapt `test_t1_f14_kpi_pola_ancaman_additive_badge`: assert badge removal and primary taxonomy value.
3. In `tests/test_kpi_dashboard_tren.py`:
   - Adapt `test_ancaman_baru_bukan_kata_acak_judul` and `test_ekstraksi_malware_spesifik_organik` to assert taxonomy category rather than raw entity names.

---

## 5. Verification Method

1. **Verify Baseline Test Suite Execution**:
   ```powershell
   python -m pytest tests/
   ```
   *Expected*: 241 passed.

2. **Verify Code Locations Identified in this Report**:
   ```powershell
   python -c "from src.analytics.trend_analyzer import susun_statistik_dashboard; print('trend_analyzer importable')"
   python -c "from src.analytics.rag_engine import RAGEngine; print('rag_engine importable')"
   python -c "from src.analytics.cti_agents import _format_distribusi_ecsirt; print('cti_agents importable')"
   ```
   *Expected*: All modules import successfully.

3. **Invalidation Conditions**:
   - If `tests/test_kpi_dashboard_tren.py` or `tests/test_cti_m5.py` fail after implementation without documented test adaptations.
   - If changing test news datasets leaves `[ POLA ANCAMAN ]`, `[ SINYAL ANCAMAN BARU ]`, or `[ SEKTOR TARGET TERPAPAR ]` unchanged.
