# Laporan Handoff Spesifikasi Teknis: Pipeline Intelijen Siber Terintegrasi (Tahap 1–6 & R0–R4)

**Penyusun**: SPECIFICATION MINER (`spec_miner_pipeline`)  
**Penerima**: Orchestrator (`d326f96e-59d9-4542-b4b8-e1006667c5bf`)  
**Lokasi Berkas**: `D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\spec_miner_pipeline\handoff.md`  
**Waktu Penyelesaian**: 2026-10-20T15:45:00Z  

---

## 1. Observation

Berdasarkan pemeriksaan langsung pada berkas repositori `D:\penting\magang\kominfo\NOTIFIKASI-BERITA`, eksekusi perintah verifikasi, serta pemeriksaan API/web sumber resmi, diamati fakta-fakta konkret berikut:

1. **Integritas Test Suite Awal**:
   Perintah `python -m pytest tests/` dijalankan secara live dan menghasilkan:
   ```text
   36 passed, 5 warnings in 13.91s (Python 3.12.10, pytest-9.1.1)
   ```
   Seluruh 36 tes unit & integrasi yang ada lulus tanpa error.

2. **Kondisi Sumber & Ensiklopedia Lokal Saat Ini**:
   - `data/encyclopedia/mitre.json`: 212 baris, hanya memuat ~25 entri teknik kurasi manual dengan kata kunci bahasa Indonesia, tanpa deskripsi lengkap dan tanpa pemetaan STIX 2.1 standar.
   - `data/encyclopedia/d3fend.json`: 149 baris, hanya memuat ~10 entri mitigasi generik (`D3-MFA`, `D3-DBR`, `D3-WAF`, dll.), tanpa relasi pemetaan ke teknik ATT&CK.
   - `data/encyclopedia/nist.json`: 98 baris, memuat 10 ringkasan fungsi NIST CSF (`GV.SC`, `ID.AM`, `PR.AA`, dll.) dengan mitigasi statis bahasa Indonesia.
   - `data/encyclopedia/bssn.json`: 45 baris, memuat 7 regulasi/standar BSSN (Peraturan BSSN 1/2024, UU PDP, Perpres SPBE, dll.).
   - Sesuai arahan R0: `mitre.json`, `d3fend.json`, dan `nist.json` adalah data dummy yang harus diganti dari sumber resmi. Berkas seperti `bssn.json`, `cis_controls.json`, `iso27001.json`, `owasp.json`, `cwe.json`, `csa_ccm.json`, `cisa_cpg.json`, `indeks_kami.json`, dan `csirt_framework.json` dipertahankan dahulu dan diajukan ke user sebelum dihapus/diubah.

3. **Status Database Persisten (`data/state.db`)**:
   Pemeriksaan skema dan isi `data/state.db` menghasilkan:
   - Tabel aktif: `konten_terkirim`, `riwayat_tren`, `prediksi_tren_terakhir`, `metadata_sistem`, `pengaturan`, `admin_users`.
   - Jumlah baris berita aktif di `riwayat_tren`: 169 baris berita lengkap dengan kolom `id`, `kategori`, `identifier`, `judul`, `sumber`, `kata_kunci`, `kategori_relevansi`, `tanggal_publish`, `ringkasan_atau_narasi`, `link`. Data ini siap dipakai sebagai basis sampling dataset evaluasi Tahap 6 (200-500 artikel).

4. **Verifikasi Sumber Eksternal & Endpoint Resmi (Live Checked)**:
   - **MISP Taxonomies**: Repositori `github.com/MISP/misp-taxonomies`. Berkas `ecsirt/machinetag.json` terverifikasi berisi taksonomi insiden standar CSIRT (`abusive-content`, `malicious-code`, `information-gathering`, `intrusion-attempts`, `intrusions`, `availability`, `information-content-security`, `fraud`, `other`).
   - **MITRE ATT&CK STIX 2.1**: Repositori `github.com/mitre-attack/attack-stix-data`, branch `master`, berkas `enterprise-attack/enterprise-attack.json`. Versi ditandai melalui Git release tags (mis. `v16.1`, `v17.0`) dan properti bundle STIX.
   - **MITRE D3FEND API**: Endpoint `https://d3fend.mitre.org/api/version.json` berhasil diakses live:
     ```json
     {
       "version": "1.6.0",
       "ontology_version": "1.6.0",
       "release_date": "2026-08-31T00:12:00Z",
       "ontology_hash_sha256": "744a9fdabf6a04db645d56db8d7cd286205e8f9c294e92a4cd1e823dec756804"
     }
     ```
     Endpoint pemetaan relasional: `/api/ontology/inference/d3fend-full-mappings.json` dan metadata teknik: `/api/technique/all.json`.
   - **NIST OSCAL**: Repositori `github.com/usnistgov/oscal-content`, branch `master`. Jalur berkas:
     - SP 800-53 Rev 5: `nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json` (Terverifikasi live via HTTP GET).
     - CSF 2.0: `nist.gov/CSF/2.0/json/` (katalog OSCAL CSF 2.0).

5. **Titik Tampilan Dashboard Admin Saat Ini (`src/web/templates/partials/_tren.html` & `src/analytics/cti_agents.py`)**:
   - Titik 1: KPI `[ POLA ANCAMAN ]` pada baris 140 `_tren.html` yang dirender oleh `tren-kpi.js` melalui `stat.prediksi_pola_serangan`.
   - Titik 2: Section 1 `INSIDEN MELONJAK DRASTIS` pada baris 176 `cti_agents.py`.
   - Titik 3: Section 2 `TREN INSIDEN MINGGUAN` pada baris 177 `cti_agents.py`.
   - Titik 4: Section 3 `VEKTOR SERANGAN TREN INSIDEN MINGGUAN` pada baris 178 `cti_agents.py`.
   - Titik 5: Section 4 `REKOMENDASI AKSI` pada baris 179 `cti_agents.py`.

---

## 2. Logic Chain & Technical Design Specifications

### 2.1. Keputusan Pemilihan Taksonomi Insiden & Daftar Tertutup
- **Evaluasi Kandidat Taksonomi**:
  1. *ENISA Threat Taxonomy (`enisa/machinetag.json`)*: Berisi ancaman makro dan bencana fisik (gempa, banjir, kebakaran, radiasi, terorisme fisik). Kurang spesifik untuk operasional triage insiden siber harian.
  2. *VERIS (`veris/machinetag.json`)*: Matriks 4A (Actors, Actions, Assets, Attributes) sangat komprehensif untuk analisis pasca-insiden metrik asuransi/risiko, tetapi terlalu berat dan kompleks untuk klasifikasi cepat satu label per berita siber.
  3. *CIRCL Taxonomy (`circl/machinetag.json`)*: Terikat pada prosedur operasional internal CIRCL Luksemburg.
  4. *eCSIRT.net Taxonomy (`ecsirt/machinetag.json`)*: **PILIHAN TERBAIK**. Dibangun khusus oleh TF-CSIRT/eCSIRT untuk klasifikasi insiden tim tanggap darurat siber (CSIRT). Selaras langsung dengan tupoksi CSIRT Diskominfo Jawa Timur, memiliki predikat aksi serangan yang jelas, serta kompatibel dengan MISP machine-tag.
- **Daftar Tertutup 11 Kategori Praktis untuk Berita**:
  | # | Kategori Praktis (Label Utama) | Induk eCSIRT (`predicate:value`) | Definisi Singkat |
  |---|--------------------------------|----------------------------------|------------------|
  | 1 | `Ransomware` | `malicious-code:ransomware` | Penyusupan kode berbahaya yang mengenkripsi file/sistem dan meminta tebusan |
  | 2 | `Data Breach / Kebocoran Data` | `information-content-security:unauthorized-information-access` & `data-loss` | Akses, eksfiltrasi, publikasi, atau penjualan data rahasia/pribadi tanpa hak |
  | 3 | `DDoS / Gangguan Ketersediaan` | `availability:ddos` & `dos` | Serangan saturasi trafik/sumber daya yang melumpuhkan layanan atau server publik |
  | 4 | `Web Defacement` | `intrusions:defacement` | Perubahan visual atau konten situs web tanpa izin (mis. slot judi, klaim peretasan) |
  | 5 | `Phishing / Penipuan Siber` | `fraud:phishing` & `masquerade` | Rekayasa sosial digital (email, tautan, APK palsu) untuk mencuri kredensial/dana |
  | 6 | `Malware / Infostealer` | `malicious-code:malware` (`trojan`, `spyware`, `botnet-drone`) | Infeksi perangkat oleh software jahat untuk mencuri data, spyware, atau remote access |
  | 7 | `Eksploitasi Kerentanan (Exploit / Zero-Day)` | `intrusion-attempts:ids-alert` | Pemanfaatan celah keamanan software/hardware teridentifikasi (CVE atau 0-day) |
  | 8 | `Akses Tidak Sah / Pembobolan Akun` | `intrusions:account-compromise` & `root-compromise` | Penggunaan kredensial curian, brute force, atau bypass otentikasi ke sistem internal |
  | 9 | `Pelecehan / Konten Berbahaya` | `abusive-content:spam` & `harmful-speech` | Penyebaran spam massal, ancaman, konten disinformasi terkoordinasi |
  | 10| `Lainnya` | `other` | Insiden siber nyata yang tidak tercakup dalam 9 kategori spesifik di atas |
  | 11| `Tidak Dapat Ditentukan` | `other:unspecified` | Berita tidak memuat informasi/bukti faktual yang memadai untuk diklasifikasikan |

---

### 2.2. Keputusan Terhadap Berkas Lokal yang Ada
1. `data/encyclopedia/mitre.json`: **BUAT ULANG** dari sumber resmi `github.com/mitre-attack/attack-stix-data` (JSON STIX 2.1). Berkas lokal lama dibuang dari korpus utama karena tidak lengkap dan tidak memiliki taktik/sub-teknik resmi.
2. `data/encyclopedia/d3fend.json`: **BUAT ULANG** dari API resmi MITRE D3FEND (`/api/ontology/inference/d3fend-full-mappings.json` dan `/api/technique/all.json`). Disimpan dalam tabel SQLite relasional deterministik, bukan berkas JSON parsial.
3. `data/encyclopedia/nist.json`: **BUAT ULANG** dari katalog resmi OSCAL JSON NIST SP 800-53 Rev 5 dan CSF 2.0. Berkas lokal lama digantikan oleh koleksi dokumen kontrol terindeks.
4. `data/encyclopedia/bssn.json`: **PERTAHANKAN SEMENTARA & AJUKAN KE USER** sesuai aturan R0. Karena sumber resmi regulasi BSSN dalam format terstruktur belum didefinisikan dalam spesifikasi, berkas ini tetap disimpan sebagai fallback referensi nasional sampai ada konfirmasi eksplisit dari user.

---

### 2.3. Spesifikasi Arsitektur Tahap 1: Download & Staging
- **Struktur Direktori Staging**:
  ```text
  data/
  └── raw/
      ├── misp_taxonomies/
      │   └── <YYYY-MM-DD>/
      │       ├── machinetag.json
      │       └── metadata.json
      ├── mitre_attack/
      │   └── <YYYY-MM-DD>/
      │       ├── enterprise-attack.json
      │       └── metadata.json
      ├── mitre_d3fend/
      │   └── <YYYY-MM-DD>/
      │       ├── version.json
      │       ├── d3fend-full-mappings.json
      │       ├── technique-all.json
      │       └── metadata.json
      └── nist_oscal/
          └── <YYYY-MM-DD>/
              ├── NIST_SP-800-53_rev5_catalog.json
              ├── CSF_2.0_catalog.json
              └── metadata.json
  ```
- **Skema Metadata JSON (`metadata.json`)**:
  ```json
  {
    "source_name": "mitre_attack",
    "source_url": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
    "download_timestamp_utc": "2026-10-20T12:00:00Z",
    "version_identifier": "v16.1",
    "commit_hash": "a1b2c3d4e5f6...",
    "file_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "file_size_bytes": 48291042,
    "record_count_parsed": 834,
    "download_status": "SUCCESS"
  }
  ```
- **Resiliensi Jaringan**:
  - Timeout: 45 detik.
  - Retry: 3 kali dengan *exponential backoff* (delay: 2s, 4s, 8s).
  - Proxy Support: Membaca variabel sistem `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`.
  - Mirror Support: Mendukung parameter CLI `--mirror-base-url` untuk lingkungan intranet tertutup instansi pemerintah (Diskominfo Jatim).

---

### 2.4. Spesifikasi Arsitektur Tahap 2: Persiapan Data & Penyimpanan
1. **Perataan Dokumen STIX 2.1 MITRE ATT&CK**:
   - Filter ketat: Hanya objek dengan `type == "attack-pattern"`. Buang jika `revoked == True` atau `x_mitre_deprecated == True`.
   - Ekstraksi ID: Ambil dari `external_references` di mana `source_name == "mitre-attack"` (format `Txxxx` atau `Txxxx.yyy`).
   - Teks Dokumen per Teknik untuk RAG:
     ```text
     [TEKNIK MITRE ATT&CK]
     ID: T1566
     Nama: Phishing
     Taktik: Initial Access
     Platform: Linux, macOS, Windows, SaaS, Office 365
     Deskripsi: Adversaries may send phishing messages to gain access to victim systems. Phishing relies on user interaction...
     ```
   - Skema Metadata Dokumen:
     `{"source": "mitre-attack", "source_version": "v16.1", "original_id": "attack-pattern--...", "technique_id": "T1566", "ingest_date": "2026-10-20T12:00:00Z"}`

2. **Dokumen Taksonomi Insiden**:
   - Satu dokumen per kategori (11 kategori).
   - Teks Dokumen:
     ```text
     [TAKSONOMI INSIDEN SIBER]
     Kategori: Ransomware
     Induk eCSIRT: malicious-code:ransomware
     Definisi: Serangan perangkat lunak pemeras yang mengenkripsi berkas, basis data, atau sistem operasi korban dan menuntut tebusan uang/kripto untuk kunci dekripsi.
     Contoh Kasus: LockBit melumpuhkan PDNS, Brain Cipher mengenkripsi server rumah sakit, penyebaran ransomware via phishing email.
     ```
   - Metadata Dokumen:
     `{"source": "misp-taxonomies/ecsirt", "source_version": "2026-10-20", "original_id": "8311fd86-7ef4-5534-8179-06720dc0278e", "ingest_date": "2026-10-20T12:00:00Z"}`

3. **Tabel Relasional Deterministik MITRE D3FEND (SQLite)**:
   - D3FEND **DILARANG** dimasukkan ke vector store RAG. Wajib disimpan dalam tabel relasional SQLite untuk lookup deterministik.
   - Skema DDL SQLite di `data/state.db`:
     ```sql
     CREATE TABLE IF NOT EXISTS d3fend_techniques (
         technique_id TEXT PRIMARY KEY,
         name TEXT NOT NULL,
         tactic TEXT NOT NULL,
         definition TEXT,
         source_version TEXT NOT NULL,
         updated_at TEXT NOT NULL
     );

     CREATE TABLE IF NOT EXISTS d3fend_attack_mappings (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         attack_technique_id TEXT NOT NULL,
         d3fend_technique_id TEXT NOT NULL,
         relationship_type TEXT DEFAULT 'mitigates',
         source_version TEXT NOT NULL,
         FOREIGN KEY (d3fend_technique_id) REFERENCES d3fend_techniques(technique_id)
     );

     CREATE INDEX IF NOT EXISTS idx_d3fend_attack_lookup 
     ON d3fend_attack_mappings(attack_technique_id);
     ```

4. **Perataan Dokumen Kontrol NIST OSCAL**:
   - Satu dokumen per kontrol SP 800-53 Rev 5 dan per subkategori CSF 2.0.
   - Teks Dokumen:
     ```text
     [KONTROL KEAMANAN SISTEM NIST]
     Framework: SP 800-53 Rev 5
     ID Kontrol: AC-2
     Judul: Account Management
     Keluarga/Fungsi: Access Control
     Pernyataan: The organization manages information system accounts, including establishing, activating, modifying, reviewing, disabling, and removing accounts in accordance with organizational procedures...
     ```
   - Metadata Dokumen:
     `{"source": "nist-oscal", "source_version": "SP800-53-Rev5", "original_id": "ac-2", "ingest_date": "2026-10-20T12:00:00Z"}`

---

### 2.5. Spesifikasi Arsitektur Tahap 3: Indeks RAG & Multilingual Embedding
1. **Pemisahan Koleksi Vektor**:
   - Menggunakan 3 koleksi vektor terpisah secara fisik/namespace:
     - `collection_taxonomy`: Korpus 11 kategori insiden eCSIRT.
     - `collection_attack`: Korpus seluruh teknik ATT&CK aktif (~600-800 dokumen teknik).
     - `collection_nist`: Korpus kontrol keamanan NIST SP 800-53 & CSF 2.0 (~1.200 dokumen).
2. **Justifikasi Teknis `gemini-embedding-001` untuk Teks Multibahasa**:
   - Model `gemini-embedding-001` (dengan dimensi 768) dilatih secara natif pada korpus multibahasa lebih dari 100 bahasa, mencakup Bahasa Indonesia dan Bahasa Inggris.
   - Domain CTI Indonesia memiliki karakteristik campuran (*code-mixing*): berita berbahasa Indonesia kerap menggunakan istilah teknis bahasa Inggris ("eksploitasi vulnerability via reverse shell dan bypass firewall").
   - Kemampuan *cross-lingual semantic alignment* pada `gemini-embedding-001` memungkinkan kueri dalam bahasa Indonesia diproyeksikan ke ruang vektor bersama yang berdekatan dengan dokumen teknik MITRE ATT&CK dan NIST yang berbahasa Inggris standar.
   - Repositori telah memiliki rantai fallback otomatis di `src/utils/llm_adapter.py` (`gemini-embedding-exp-03-07`, `text-embedding-004`).
3. **Strategi Penyimpanan Teks Asli & Hasil Terjemahan**:
   - Setiap artikel yang di-scrape disimpan dalam dua representasi di memori/database:
     - `teks_asli`: Teks berita asli berbahasa Indonesia dari media/portal.
     - `teks_terjemahan`: Ringkasan fakta teknis dalam bahasa Inggris terstandarisasi CTI.
   - **Aturan Eksekusi Retrieval**:
     - Retrieval Taksonomi: Menggunakan `teks_asli` dan `teks_terjemahan` karena dokumen taksonomi memuat contoh dwibahasa.
     - Retrieval MITRE ATT&CK & NIST: **WAJIB** menggunakan `teks_terjemahan` (vektor kueri dihitung dari fakta teknis bahasa Inggris). Hal ini memaksimalkan *semantic matching score* terhadap terminologi resmi ATT&CK dan NIST.

---

### 2.6. Spesifikasi Arsitektur Tahap 4: Alur Pemrosesan Berita (Per Berita)
1. **Klasifikasi Insiden**:
   - LLM mengambil top-3 kandidat dari `collection_taxonomy`.
   - LLM memilih SATU label utama dari daftar tertutup 11 kategori.
   - Skema JSON Output Terstruktur:
     ```json
     {
       "kategori_utama": "Ransomware",
       "kategori_tambahan": null,
       "confidence": 0.94,
       "kutipan_bukti": "Pelaku mengunci file database rumah sakit dan menuntut uang tebusan 10 Bitcoin.",
       "alasan": "Teks secara eksplisit mendeskripsikan enkripsi file dan tuntutan uang tebusan.",
       "id_taksonomi_induk": "malicious-code:ransomware"
     }
     ```
   - Aturan: Jika tidak ada bukti yang relevan, LLM **wajib** mengeluarkan `kategori_utama: "Tidak Dapat Ditentukan"`.
2. **Ekstraksi MITRE ATT&CK Kondisional**:
   - Gate Kondisi: Evaluasi apakah teks berita memuat deskripsi cara atau alur serangan (*attack flow*).
   - Jika **TIDAK ADA** alur serangan: Ekstraksi dilewati, mengembalikan `{"status": "tidak_ditentukan", "tactic": null, "technique_id": null}`. Dilarang menebak.
   - Jika **ADA** alur serangan: Retrieval top-15 kandidat dari `collection_attack`.
   - Pemilihan oleh LLM: LLM memilih ID teknik yang paling cocok disertai kutipan bukti.
   - Aturan Bukti Lemah: Jika berita hanya menyebutkan indikasi umum tanpa bukti alur spesifik, LLM berhenti pada tingkat Tactic (mis. `Initial Access`) dan mengisi `technique_id: "tidak_ditentukan"`.
3. **Guard Validasi Teknik ATT&CK Aktif**:
   - Sebelum hasil LLM diterima, ID teknik diverifikasi terhadap set ID ATT&CK aktif yang valid:
     ```python
     if technique_id not in ACTIVE_ATTACK_IDS:
         logger.warning(f"ID Teknik {technique_id} dari LLM ditolak: Tidak ada di dataset ATT&CK aktif.")
         # Tolak dan catat ke log audit penolakan
         technique_id = "tidak_ditentukan"
     ```
4. **Lookup Deterministik Mitigasi D3FEND**:
   - Berdasarkan `technique_id` ATT&CK yang telah divalidasi, sistem melakukan kueri SQL ke `d3fend_attack_mappings`.
   - Mengambil daftar teknik D3FEND resmi (ID, nama, taktik pertahanan, definisi).
   - **STRICT GUARD**: LLM DILARANG menambah atau memodifikasi mitigasi D3FEND. Output yang ditampilkan ke admin murni hasil dari tabel relasional dengan penanda: *"Saran mitigasi umum untuk teknik terkait, bukan temuan forensik spesifik insiden"*.
5. **Referensi NIST On-Demand**:
   - Jika admin meminta eksplorasi kontrol kepatuhan, sistem mengambil kontrol relevan dari `collection_nist` dan menampilkannya sebagai referensi tambahan terpisah.
6. **Integritas Fakta Narasi LLM**:
   - Narasi LLM hanya boleh menggunakan fakta dari teks berita asli dan data tervalidasi di atas.
   - Tautan URL sumber berita asli wajib dicantumkan.
   - Fakta yang dilaporkan berita harus dibedakan secara tegas dari inferensi analisis AI.
7. **Skema Penyimpanan Provenance & Koreksi Manual**:
   - Tabel `intelijen_berita_tervalidasi` di `data/state.db`:
     ```sql
     CREATE TABLE IF NOT EXISTS intelijen_berita_tervalidasi (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         article_identifier TEXT NOT NULL UNIQUE,
         kategori_insiden TEXT NOT NULL,
         confidence_kategori REAL NOT NULL,
         kutipan_bukti_kategori TEXT,
         mitre_tactic TEXT,
         mitre_technique_id TEXT,
         mitre_technique_name TEXT,
         confidence_mitre REAL,
         kutipan_bukti_mitre TEXT,
         d3fend_mitigasi_json TEXT,
         nist_referensi_json TEXT,
         version_taxonomy TEXT NOT NULL,
         version_attack TEXT NOT NULL,
         version_d3fend TEXT NOT NULL,
         version_nist TEXT NOT NULL,
         dibuat_pada TEXT NOT NULL,
         koreksi_admin_kategori TEXT DEFAULT NULL,
         koreksi_admin_technique_id TEXT DEFAULT NULL,
         koreksi_admin_catatan TEXT DEFAULT NULL,
         koreksi_admin_oleh TEXT DEFAULT NULL,
         koreksi_admin_pada TEXT DEFAULT NULL
     );
     ```

---

### 2.7. Spesifikasi Arsitektur Tahap 5: Skrip Update Berkala
1. **Mekanisme Pengecekan Versi Independen**:
   - Empat skrip update modular:
     - `update_attack.py`: Cek Git commit hash / release tag via GitHub API `mitre-attack/attack-stix-data`.
     - `update_d3fend.py`: Cek `ontology_hash_sha256` dan `version` dari `https://d3fend.mitre.org/api/version.json`.
     - `update_nist.py`: Cek Git commit hash pada `usnistgov/oscal-content`.
     - `update_taxonomy.py`: Cek Git commit hash pada `MISP/misp-taxonomies`.
   - **Idempoten**: Jika hash/versi sama dengan versi yang sedang aktif di `metadata_sistem`, proses berhenti langsung dan mencatat log: `"Tidak ada pembaruan untuk <sumber> (versi aktif: <versi>)"`.
2. **Validasi Staging & Pencegahan Drop Katastropik**:
   - Unduh payload ke `data/raw/<sumber>/<tanggal>/`.
   - Validasi sintaks JSON dan kelengkapan skema.
   - Deteksi drop jumlah record:
     ```python
     if new_count == 0 or new_count < (old_count * 0.70):
         raise UpdateValidationError(
             f"Pembaruan ditolak: Terdeteksi penurunan record drastis pada {source} (lama: {old_count}, baru: {new_count})."
         )
     ```
3. **Laporan Diff (Diff Report)**:
   - Menghitung selisih record antara versi lama dan baru:
     - `added`: Daftar ID baru.
     - `modified`: Daftar ID yang mengalami perubahan nama/definisi.
     - `revoked`: Daftar ID yang di-revoke atau dihapus.
   - Disimpan sebagai `data/reports/diff_<sumber>_<timestamp>.json`.
4. **Re-embedding Inkremental & Penggantian Indeks Atomik (Atomic Swap)**:
   - Sistem **HANYA** melakukan embedding terhadap dokumen dalam set `added` dan `modified`. Dokumen yang tidak berubah menggunakan vektor dari cache lama.
   - Buat koleksi vektor baru: `<koleksi>_vNext`.
   - Lakukan pengujian *smoke test* pada `<koleksi>_vNext`.
   - Swap atomik: Arahkan pointer aktif `<koleksi>_active` ke `<koleksi>_vNext`.
   - Rollback: Indeks lama `<koleksi>_vPrev` disimpan di disk. Jika terjadi kegagalan sistem dalam 24 jam pertama, pointer dapat langsung dialihkan kembali ke `vPrev`.
5. **Auditor Teknik ATT&CK yang Dicabut (Revoked Audit Flagger)**:
   - Jika ada teknik ATT&CK lama yang berstatus `revoked` atau hilang:
     - Sistem **DILARANG** menghapus berita atau insiden historis secara diam-diam.
     - Query seluruh catatan di `riwayat_tren` dan `intelijen_berita_tervalidasi` yang merujuk ID tersebut.
     - Tambahkan bendera audit: `flag_tinjauan = "TEKNIK_REVOKED_PERLU_REVIEW"` beserta catatan versi ATT&CK baru.
6. **Penjadwalan & Konfigurasi Proxy**:
   - Jadwal Cron: Mingguan (`0 2 * * 1`) untuk ATT&CK, D3FEND, dan MISP Taxonomy; Bulanan (`0 3 1 * *`) untuk NIST OSCAL.
   - Dukungan Systemd Timer dan GitHub Actions workflow file.
   - Notifikasi kegagalan terintegrasi ke webhook/log admin.

---

### 2.8. Spesifikasi Arsitektur Tahap 6: Kerangka Kerja Evaluasi (Evaluation Framework)
1. **Pembuatan Draf Dataset Berlabel dari `data/state.db`**:
   - Skrip: `scripts/generate_evaluation_draft.py`.
   - Mengambil 200–500 artikel berita acak/terdistribusi dari 169+ baris di tabel `riwayat_tren`.
   - Menjalankan pipeline klasifikasi dan ekstraksi teknik secara otomatis.
   - Menyimpan ke berkas CSV/JSON: `data/evaluation/dataset_evaluasi_draf.csv`.
   - **Tanda Keabsahan Jelas**: Setiap entri ditandai eksplisit:
     ```csv
     id_berita,judul,ringkasan,prediksi_kategori,confidence_kategori,verified_kategori,prediksi_mitre_id,verified_mitre_id,status_label
     2749,"Social Engineering...","...",Phishing / Penipuan Siber,0.92,,T1566,,DRAFT_PENDING_USER_REVIEW
     ```
     Kolom `verified_kategori` dan `verified_mitre_id` dibiarkan kosong agar mudah diisi/dikoreksi manual oleh user/analis CSIRT.
2. **Kalkulasi Metrik Evaluasi**:
   - Skrip: `scripts/evaluate_pipeline.py`.
   - Input: Berkas yang telah dikoreksi user (di mana `verified_kategori` tidak kosong).
   - Metrik per Kategori Insiden:
     - Precision: $P = \frac{TP}{TP + FP}$
     - Recall: $R = \frac{TP}{TP + FN}$
     - F1-Score: $F1 = 2 \times \frac{P \times R}{P + R}$
     - Macro-F1 dan Weighted-F1 rata-rata.
     - Tabel Confusion Matrix antarkategori.
   - Metrik MITRE ATT&CK:
     - Akurasi Teknik Presisi: Persentase `prediksi_mitre_id == verified_mitre_id`.
     - Akurasi Taktik: Persentase kecocokan level taktik.
     - Tingkat Halusinasi ID: Persentase teknik yang tidak terdaftar di ATT&CK aktif (Target: 0.0%).
     - Akurasi Abstensi: Ketepatan sistem menghasilkan "tidak_ditentukan" pada artikel tanpa bukti alur serangan.
3. **Kemampuan Re-run Fleksibel**:
   - Perintah dapat dijalankan ulang setiap kali prompt, konfigurasi model, embedding, atau versi data diperbarui:
     ```bash
     python scripts/evaluate_pipeline.py --dataset data/evaluation/dataset_evaluasi_verified.csv --model gemini-3.5-flash
     ```

---

### 2.9. Spesifikasi Integrasi Dashboard Admin (Requirement R3 - 5 Titik Tampilan)
Prinsip dasar R3: **HANYA MENAMBAH INFORMASI TERVALIDASI, TIDAK BOLEH MENGHAPUS ATAU MENGGANTI TEKS LAMA**.

1. **Titik 1: KPI `[ POLA ANCAMAN ]`** (`src/web/templates/partials/_tren.html:140` & `tren-kpi.js:116`):
   - Status Saat Ini: Menampilkan pola ancaman organik (mis. "Peretasan Web", "Ransomware") dan persentase growth.
   - Penambahan Tervalidasi: Di bawah teks pola lama, tambahkan badge taksonomi resmi:
     ```html
     <!-- Konten Lama Tetap Ada -->
     <div id="kpi-pola-serangan">...</div>
     <!-- Penambahan Tervalidasi Baru -->
     <div class="mt-1 flex items-center gap-1.5 text-[11px] font-mono text-[#00d4ff] bg-[#00d4ff]/10 px-2 py-0.5 rounded border border-[#00d4ff]/20">
       <span>Taksonomi Resmi:</span>
       <strong id="kpi-taksonomi-resmi">[ Ransomware ] (Keyakinan: 94%)</strong>
     </div>
     ```
2. **Titik 2: Section "ANALISIS BERITA SIBER & REKOMENDASI MITIGASI" -> Bagian 1 "INSIDEN MELONJAK DRASTIS"** (`src/analytics/cti_agents.py:176`):
   - Status Saat Ini: Narasi makro 1 paragraf tren lonjakan insiden.
   - Penambahan Tervalidasi: Di akhir paragraf narasi asli, ditambahkan blok rujukan taksonomi eCSIRT tervalidasi:
     ```markdown
     [Narasi Asli Paragraf 1 Tetap Utuh]

     **Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:
     - Kategori Dominan: **Ransomware** (`malicious-code:ransomware`) — 65% dari insiden melonjak.
     - Status Verifikasi: Tervalidasi otomatis terhadap taksonomi eCSIRT.net v2026.
     ```
3. **Titik 3: Section "ANALISIS BERITA SIBER & REKOMENDASI MITIGASI" -> Bagian 2 "TREN INSIDEN MINGGUAN"** (`src/analytics/cti_agents.py:177`):
   - Status Saat Ini: Narasi 3 insiden mikro mingguan aktif.
   - Penambahan Tervalidasi: Pada masing-masing dari 3 insiden, disisipkan metadata klasifikasi resmi:
     ```markdown
     [Uraian Fakta Insiden Asli Tetap Utuh]
     - *Klasifikasi Resmi*: **[Ransomware]** (Keyakinan: 92% | Bukti: "enkripsi sistem server PDNS")
     ```
4. **Titik 4: Bagian 3 "VEKTOR SERANGAN TREN INSIDEN MINGGUAN"** (`src/analytics/cti_agents.py:178`):
   - Status Saat Ini: Narasi alur serangan dengan rujukan MITRE ATT&CK umum.
   - Penambahan Tervalidasi: Menampilkan taktik dan teknik MITRE ATT&CK enterprise STIX 2.1 tervalidasi aktif lengkap dengan tautan resmi MITRE:
     ```markdown
     [Narasi Vektor Serangan Asli Tetap Utuh]
     - **Rujukan Terverifikasi MITRE ATT&CK Enterprise (v16.1)**:
       • Kampanye 1: Taktik **Initial Access** via **[T1190 Exploit Public-Facing Application]** (Skor Keyakinan: 88%)
       • Bukti Teknis: "Eksploitasi celah RCE pada modul upload aplikasi web..."
     ```
5. **Titik 5: Bagian 4 "REKOMENDASI AKSI"** (`src/analytics/cti_agents.py:179`):
   - Status Saat Ini: Menampilkan rekomendasi mitigasi gabungan.
   - Penambahan Tervalidasi: Menyajikan mitigasi deterministik dari MITRE D3FEND dan kontrol referensi NIST:
     ```markdown
     [Rekomendasi Aksi Asli Tetap Utuh]

     **Saran Mitigasi Terverifikasi MITRE D3FEND (Lookup Deterministik untuk T1190)**:
     - [D3-WAF] Web Application Filtering: Terapkan aturan virtual patching WAF untuk memblokir pola eksploitasi payload web.
     - [D3-SU] Software Update: Terapkan pembaruan keamanan vendor untuk menutup celah CVE yang dieksploitasi.
     *(Catatan: Rekomendasi di atas adalah saran mitigasi umum dari basis pengetahuan MITRE D3FEND untuk teknik serangan terkait).*

     **Referensi Standar NIST Tambahan**:
     - [NIST SP 800-53 Rev 5] SI-2 (Flaw Remediation): Identifikasi, laporkan, dan perbaiki kelemahan perangkat lunak.
     - [NIST CSF 2.0] PR.PS-02: Perangkat lunak dipelihara, diperbarui, dan ditambal secara berkala.
     ```

---

## 3. Features Discovered & Probe Results

### Features Discovered Table
| # | Category | Feature | Description | Inputs | Outputs | Error Behavior | Discovered Via |
|---|----------|---------|-------------|--------|---------|----------------|----------------|
| 1 | Tahap 1: Staging | Staging Directory Hierarchy | Struktur direktori unduhan mentah per sumber dan per tanggal | Nama sumber (`misp_taxonomies`, `mitre_attack`, `mitre_d3fend`, `nist_oscal`), Tanggal (`YYYY-MM-DD`) | Path `data/raw/<sumber>/<tanggal>/` berisi raw payload + `metadata.json` | Buat folder otomatis jika belum ada; laporkan error izin file | ORIGINAL_REQUEST.md Tahap 1 & DISPATCH.md |
| 2 | Tahap 1: Staging | SHA-256 & Version Metadata Logger | Perekaman hash SHA-256 dan version identifier pada setiap payload mentah | File raw payload unduhan | Berkas `metadata.json` terstruktur | Jika hash tidak cocok atau file kosong, gagalkan staging | ORIGINAL_REQUEST.md Tahap 1 |
| 3 | Tahap 1: Resiliency | Network Resilience with Proxy & Mirror | Unduhan dengan timeout 45s, retry exponential backoff 3x, proxy HTTP/HTTPS dan opsi mirror internal | URL sumber, opsi proxy, opsi mirror URL | File payload mentah terunduh | Lemparkan `DownloadError` setelah 3 kali gagal, jangan buat data palsu | ORIGINAL_REQUEST.md R0 & Tahap 1 |
| 4 | Tahap 2: Flattening | MITRE ATT&CK STIX 2.1 Flattener | Perataan JSON STIX 2.1 menjadi dokumen teks per teknik aktif, membuang revoked/deprecated | `enterprise-attack.json` STIX 2.1 bundle | List of flattened technique documents (T-number, name, tactic, description, platform) | Tolak payload jika bukan bundle STIX yang valid | ORIGINAL_REQUEST.md Tahap 2 & STIX 2.1 Spec |
| 5 | Tahap 2: Taxonomy | eCSIRT Closed Taxonomy Document Generator | Pembuatan korpus 11 kategori insiden praktis dari eCSIRT machinetag | `ecsirt/machinetag.json` dari MISP | 11 dokumen taksonomi insiden dwibahasa dengan contoh berita | Jika file machinetag korup, fallback ke daftar 11 kategori default | ORIGINAL_REQUEST.md Sumber Data #1 |
| 6 | Tahap 2: Storage | D3FEND Relational Store (SQLite) | Tabel relasional untuk teknik D3FEND dan mapping ATT&CK -> D3FEND (non-vector) | `d3fend-full-mappings.json` & `technique-all.json` | Tabel `d3fend_techniques` dan `d3fend_attack_mappings` di `state.db` | Rollback transaksi jika terjadi pelanggaran foreign key | ORIGINAL_REQUEST.md Tahap 2 & DISPATCH.md |
| 7 | Tahap 2: Flattening | NIST OSCAL Control Flattener | Perataan katalog OSCAL JSON SP 800-53 Rev 5 & CSF 2.0 menjadi dokumen kontrol | OSCAL JSON catalog files | List of control documents (ID, title, statement, family/function) | Lewati kontrol tanpa ID/statement, catat peringatan | ORIGINAL_REQUEST.md Tahap 2 |
| 8 | Tahap 3: Vector | Multi-Collection Vector Engine | Engine RAG dengan 3 koleksi vektor terisolasi: (a) ATT&CK, (b) Taksonomi, (c) NIST | Korpus teks terstruktur dari Tahap 2 | 3 indeks vektor mandiri dengan metadata sumber lengkap | Jika satu koleksi gagal inisialisasi, koleksi lain tetap berfungsi | ORIGINAL_REQUEST.md Tahap 3 |
| 9 | Tahap 3: Multilingual | Multilingual Embedding Adapter | Justifikasi dan pemanfaatan `gemini-embedding-001` untuk teks campuran Indonesia-Inggris | String kueri atau batch teks | Vector embedding berdimensi 768 | Fallback otomatis ke `gemini-embedding-exp-03-07` atau `text-embedding-004` jika 429 | `src/utils/llm_adapter.py` & R1 |
| 10| Tahap 3: Retrieval | Dual-Text Translation Retrieval Strategy | Penyimpanan teks asli dan terjemahan bahasa Inggris; retrieval dilakukan pada teks terjemahan | Teks artikel asli berbahasa Indonesia | Teks terjemahan CTI; hasil retrieval vektor akurat | Jika terjemahan gagal, gunakan teks asli sebagai fallback retrieval | ORIGINAL_REQUEST.md Tahap 3 |
| 11| Tahap 4: Pipeline | Structured JSON Incident Classifier | Klasifikasi LLM ke SATU label utama dari 11 daftar tertutup dengan confidence dan bukti | Teks berita + top-k taksonomi retrieval | JSON: `kategori_utama`, `confidence`, `kutipan_bukti`, `alasan`, `id_taksonomi_induk` | Fallback wajib ke label "Tidak Dapat Ditentukan" jika ragu | ORIGINAL_REQUEST.md Tahap 4 #1 |
| 12| Tahap 4: Pipeline | Conditional ATT&CK Extractor | Ekstraksi teknik ATT&CK HANYA jika artikel mendeskripsikan alur/cara serangan | Teks berita + top-15 ATT&CK candidates | JSON teknik ATT&CK terpilih dengan bukti dan confidence | Jika bukti lemah, berhenti di taktik atau "tidak_ditentukan" | ORIGINAL_REQUEST.md Tahap 4 #2 |
| 13| Tahap 4: Guardrail | Active ATT&CK Validation Guard | Pemeriksaan keberadaan ID teknik LLM pada database teknik aktif | ID teknik yang dihasilkan LLM | Status valid / ditolak | Jika ID halusinasi atau revoked, tolak dan catat audit log | ORIGINAL_REQUEST.md Tahap 4 #3 |
| 14| Tahap 4: Guardrail | Deterministic D3FEND Lookup Enforcer | Penarikan mitigasi D3FEND murni dari tabel relasional tanpa intervensi penambahan oleh LLM | Validated ATT&CK ID | List of D3FEND mitigation records dari SQLite | Jika tidak ada mapping, kembalikan saran pengerasan umum | ORIGINAL_REQUEST.md Tahap 4 #4 |
| 15| Tahap 4: Provenance | Provenance & Manual Correction Storage | Penyimpanan hasil analisis lengkap dengan versi seluruh sumber data dan kolom koreksi admin | Hasil analisis berita + metadata versi sumber | Baris baru pada tabel `intelijen_berita_tervalidasi` | Rollback jika duplikat identifier | ORIGINAL_REQUEST.md Tahap 4 #7 |
| 16| Tahap 5: Update | Periodic Source Update Runner | Skrip modular update berkala untuk ATT&CK, D3FEND, NIST, dan MISP | Trigger cron/CLI/timer | Log eksekusi pembaruan, diff report, indeks terbarui | Hentikan jika versi tidak berubah ("tidak ada pembaruan") | ORIGINAL_REQUEST.md Tahap 5 |
| 17| Tahap 5: Safety | Catastrophic Drop Detector | Validasi jumlah record staging baru terhadap versi aktif sebelum proses ingest | Payload unduhan baru | Status lolos / batal update | Gagalkan update jika record 0 atau turun > 30% | ORIGINAL_REQUEST.md Tahap 5 |
| 18| Tahap 5: Safety | Incremental Re-embedding & Atomic Switch | Hanya re-embed dokumen yang berubah; swap indeks atomik dengan retensi versi rollback | Set diff (added, modified) | Indeks aktif baru dialihkan tanpa downtime | Jika verifikasi gagal, rollback otomatis ke `vPrev` | ORIGINAL_REQUEST.md Tahap 5 |
| 19| Tahap 5: Safety | Revoked Technique Historical Auditor | Penandaan insiden historis yang memakai teknik yang kini revoked tanpa menghapus record | Daftar ID ATT&CK yang revoked pada rilis baru | Catatan audit flagger pada insiden terkait | Jangan hapus data riwayat lama secara diam-diam | ORIGINAL_REQUEST.md Tahap 5 |
| 20| Tahap 6: Evaluation | Evaluation Dataset Generator from DB | Pembangkitan dataset sampling draf (200-500 artikel) dari `state.db` dengan tanda draf jelas | Tabel `riwayat_tren` dari `data/state.db` | File CSV `dataset_evaluasi_draf.csv` dengan kolom verifikasi kosong | Tandai status `DRAFT_PENDING_USER_REVIEW` | ORIGINAL_REQUEST.md Tahap 6 & R4 |
| 21| Tahap 6: Evaluation | CTI Evaluation Metric Calculator | Kalkulator Precision, Recall, F1 per kategori dan Akurasi ATT&CK dari dataset terverifikasi | File CSV dataset berlabel manual user | Laporan metrik tabular (P, R, F1, Macro-F1, ATT&CK Accuracy) | Beri pesan jika tidak ada baris yang telah diverifikasi | ORIGINAL_REQUEST.md Tahap 6 |
| 22| R3: UI Integration | Additive Dashboard Trend Integration | Penambahan penjelasan tervalidasi ke 5 titik tampilan dashboard admin tanpa menghapus teks lama | Hasil analisis tervalidasi per berita & mingguan | Tampilan UI dashboard ter-upgrade dengan badge tervalidasi | Jika data intelijen baru kosong, tampilkan konten lama saja | ORIGINAL_REQUEST.md R3 |

---

### Edge Cases Table
| # | Feature | Input / Condition | Observed / Specified Behavior |
|---|---------|-------------------|--------------------------------|
| 1 | Klasifikasi Insiden | Berita hanya memberitakan regulasi umum tanpa insiden (mis. sosialisasi perda SPBE) | Model RAG mengembalikan label `"Tidak Dapat Ditentukan"` dengan confidence < 0.50 dan alasan ketiadaan fakta serangan. |
| 2 | Klasifikasi Insiden | Berita memuat multi-vektor (mis. Phishing yang berujung pada instalasi Ransomware) | Sistem memilih SATU label dampak paling parah sebagai `kategori_utama` (`Ransomware`) dan memasukkan `Phishing / Penipuan Siber` pada `kategori_tambahan`. |
| 3 | Ekstraksi ATT&CK | Berita hanya menyatakan "server dinas diretas hacker" tanpa penjelasan metode teknis | Gate kondisional mendeteksi ketiadaan alur serangan, ekstraksi teknik dilewati, status = `"tidak_ditentukan"`, LLM dilarang menebak. |
| 4 | Ekstraksi ATT&CK | Berita menyebutkan metode umum "menggunakan celah sistem" tanpa menyebut nama CVE/komponen | LLM berhenti pada Tactic level (`Initial Access`) dan mengisi `technique_id: "tidak_ditentukan"`. |
| 5 | Guard Validasi ATT&CK | LLM mengembalikan kode teknik fiktif seperti `T9999` atau teknik yang telah di-revoke pada versi aktif | Sistem mendeteksi `technique_id not in ACTIVE_ATTACK_IDS`, menolak hasil tersebut, mencatat peringatan audit, dan menetapkan ke `"tidak_ditentukan"`. |
| 6 | Lookup D3FEND | Teknik ATT&CK valid (`T1566`) tidak memiliki mitigasi spesifik di tabel relasional D3FEND | Sistem mengembalikan himpunan mitigasi pertahanan umum default (mis. MFA dan Least Privilege) dengan keterangan lookup tidak langsung. |
| 7 | Update Berkala | Jaringan intranet Diskominfo memblokir koneksi ke GitHub / D3FEND | Sistem mendeteksi timeout/koneksi gagal, membaca konfigurasi `HTTP_PROXY` atau `--mirror-base-url`, dan jika tetap gagal mencatat error tanpa merusak indeks aktif. |
| 8 | Update Berkala | Unduhan STIX dari MITRE mengalami korupsi data sehingga hanya berisi 5 teknik (turun 99%) | Detektor drop katastropik mendeteksi penurunan > 30%, membatalkan proses update, mempertahankan indeks aktif lama, dan mengirim peringatan audit. |
| 9 | Update Berkala | Skrip update dijalankan dua kali berturut-turut tanpa perubahan rilis di hulu | Run kedua mendeteksi kecocokan hash/commit, mencatat `"tidak ada pembaruan"`, dan keluar dengan kode 0 tanpa melakukan re-embedding atau modifikasi basis data. |
| 10| Update Berkala | Pembaruan ATT&CK baru mencabut teknik `T1086` (PowerShell, revoked diganti `T1059.001`) | Sistem tidak menghapus insiden lama yang merujuk `T1086`, melainkan menandai kolom `flag_tinjauan = "REVOKED_TECHNIQUE_REVIEW"` untuk ditinjau admin. |
| 11| Evaluasi | File evaluasi masih memuat seluruh baris dalam status draf tanpa ada verifikasi user | Skrip evaluasi menampilkan peringatan bahwa ground truth belum diisi, dan menolak menghitung metrik sampai minimal 1 entri diverifikasi. |
| 12| Integrasi UI Dashboard | API atau modul intelijen mengalami kegagalan/timeout pada salah satu section | Dashboard admin memanfaatkan prinsip *graceful degradation*: menampilkan teks asli yang sudah ada tanpa error blank page, dan badge intelijen baru berstatus *offline/pending*. |

---

## 4. Caveats & Assumptions

1. **Batasan Pemeriksaan Dokumen Rahasia**:
   Sesuai instruksi mutlak, berkas `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` dan folder `LAPORAN DASHBOARD ADMIN/` sama sekali **TIDAK DISENTUH DAN TIDAK DIBACA**. Seluruh rancangan disusun murni dari repositori aktif `src/`, `tests/`, `config/`, `data/state.db`, dan berkas `ORIGINAL_REQUEST.md` serta verifikasi live web/API.
2. **Kondisi Berkas Ensiklopedia Dummy yang Belum Terdaftar**:
   Berdasarkan aturan R0, berkas lokal `bssn.json`, `cis_controls.json`, `iso27001.json`, `owasp.json`, `cwe.json`, `csa_ccm.json`, `cisa_cpg.json`, `indeks_kami.json`, dan `csirt_framework.json` tidak dihapus. Implementasi nanti wajib meminta persetujuan user terlebih dahulu sebelum mengganti atau menghapus data-data ini.
3. **Kapasitas Sampling Dataset Evaluasi**:
   Saat ini tabel `riwayat_tren` di `data/state.db` memuat 169 artikel berita valid. Untuk mencapai target evaluasi 200–500 berita, sistem draf dapat menggunakan seluruh 169 berita yang ada ditambah hasil scraping pipeline harian berikutnya secara inkremental.

---

## 5. Conclusion

1. **Kelayakan Arsitektur**: Rancangan teknis untuk Tahap 1–6 dan Requirements R0–R4 telah terpetakan secara lengkap, presisi, dan dapat diimplementasikan tanpa merombak arsitektur inti SiberHarian yang sudah stabil (36 tes tetap lulus).
2. **Kesesuaian Sumber**:
   - Taksonomi Insiden: Terpilih `eCSIRT.net Taxonomy` dari repositori `MISP/misp-taxonomies` dengan pemetaan ke 11 kategori tertutup praktis.
   - MITRE ATT&CK: STIX 2.1 Enterprise aktif dari `mitre-attack/attack-stix-data`, diratakan per teknik tanpa entri revoked/deprecated.
   - MITRE D3FEND: Diambil dari endpoint JSON live `https://d3fend.mitre.org` dan disimpan dalam tabel relasional SQLite untuk lookup deterministik.
   - NIST OSCAL: Kontrol SP 800-53 Rev 5 dan CSF 2.0 dari `usnistgov/oscal-content` sebagai koleksi referensi tambahan.
3. **Kepatuhan Integrasi Dashboard**: Seluruh 5 titik tampilan pada R3 hanya menambahkan elemen tervalidasi ke dalam teks/tampilan yang sudah ada tanpa menghapus satu pun narasi asli.

---

## 6. Verification Method

Untuk memverifikasi spesifikasi ini secara independen:
1. **Verifikasi Test Suite Repositori**:
   ```bash
   python -m pytest tests/
   ```
   *Ekspektasi*: 36 passed.
2. **Verifikasi Skema Database & Data Sampling**:
   ```bash
   python -c "import sqlite3; conn = sqlite3.connect('data/state.db'); print('Riwayat count:', conn.execute('SELECT count(*) FROM riwayat_tren WHERE kategori=\'berita\'').fetchone()[0]); conn.close()"
   ```
   *Ekspektasi*: Output `Riwayat count: 169`.
3. **Verifikasi Aksesibilitas Live Endpoint Resmi**:
   - D3FEND Version API: Akses `https://d3fend.mitre.org/api/version.json` (memastikan status 200 OK dan versi `1.6.0`).
   - NIST OSCAL URL: Akses `https://raw.githubusercontent.com/usnistgov/oscal-content/master/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json` (memastikan status 200 OK).
   - ATT&CK STIX URL: Akses `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json` (memastikan status 200 OK).
   - MISP eCSIRT Taxonomy URL: Akses `https://raw.githubusercontent.com/MISP/misp-taxonomies/main/ecsirt/machinetag.json` (memastikan status 200 OK).
