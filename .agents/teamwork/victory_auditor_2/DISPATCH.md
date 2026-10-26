## 2026-10-24T16:35:04Z
[Message] timestamp=2026-10-24T16:35:04Z sender=a0178ffe-87b5-4784-8fa2-4eda7b176647 priority=MESSAGE_PRIORITY_HIGH content=You are teamwork_preview_victory_auditor. Conduct an independent post-victory audit (timeline audit, cheating/shortcut detection, and independent test execution) on the completed task.
Your working directory is: D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\victory_auditor_2
Please write your complete structured audit verdict to:
D:\penting\magang\kominfo\NOTIFIKASI-BERITA\.agents\teamwork\victory_auditor_2\report.md
and send your verdict and summary back to the orchestrator via send_message.

<original_task>
This is a single self-contained fix; keep it small and focused.
Pembersihan menyeluruh seluruh data *hardcoded* pada sistem dan sinkronisasi 100% seluruh komponen panel pengaturan admin (Umum & LLM, Filter Kata Kunci Scraping, Template Prompt CTI, Sumber RSS Feed, dan Referensi CTI) langsung dengan database SQLite (`data/state.db`). Mengonfigurasi secara presisi 7 model narasi Google Gemini beserta kuota RPM dan ambang batas proaktifnya, membatasi 2 model embedding resmi berkuota 100 RPM, serta menghapus total model usang dari seluruh basis kode dan database.

Working directory: `D:\penting\magang\kominfo\NOTIFIKASI-BERITA`
Integrity mode: development

Catatan Khusus Keamanan & Integritas:
- DILARANG memodifikasi atau membaca file `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` dan folder `LAPORAN DASHBOARD ADMIN/`.
- Seluruh 317+ unit test yang ada di `tests/` wajib tetap lulus 100% tanpa regresi.
- **ATURAN PENGUJIAN OFFLINE**: Seluruh pengujian otomatis, validasi sinkronisasi, dan unit test WAJIB berjalan secara 100% OFFLINE (Mocked / Fixture) dan DILARANG mengonsumsi kuota API Key riil pengguna.

## Requirements

### R1. Sinkronisasi Penuh Model Narasi & Database Tanpa Hardcoded Fallback
- Mengonfigurasi rantai model narasi di database `state.db` (tabel `pengaturan`, kunci `gemini.model_chain`) dan `config/config.yaml` agar hanya memuat 7 model narasi resmi yang ditetapkan:
  1. `gemini-2.5-flash`: 5 RPM (Ambang batas proaktif: 4)
  2. `gemini-2.5-flash-lite`: 10 RPM (Ambang batas proaktif: 9)
  3. `gemini-3-flash`: 5 RPM (Ambang batas proaktif: 4)
  4. `gemini-3.1-flash-lite`: 15 RPM (Ambang batas proaktif: 14)
  5. `gemini-3.6-flash`: 5 RPM (Ambang batas proaktif: 4)
  6. `gemini-3.5-flash-lite`: 15 RPM (Ambang batas proaktif: 14)
  7. `gemini-3.8-flash`: 5 RPM (Ambang batas proaktif: 4)
- Menghapus total model usang (`gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-3.5-flash`) dari `state.db`, `config.yaml`, `DEFAULT_MODEL_CHAIN`, fungsi `generate_text_with_chain`, dan kandidat `test-key` di `src/web/app.py`.
- **Dinamis Berbasis Database**: Ambang batas proaktif dan kuota RPM disimpan ke database (`gemini.rate_limits` dan `gemini.proactive_thresholds`) dan dibaca secara dinamis via `SettingsManager`, sehingga tidak ada kamus RPM statis yang membatasi perubahan pengguna.

### R2. Pembatasan Eksklusif 2 Model Embedding Google Gemini (100 RPM)
- Membatasi rantai embedding hanya pada 2 model embedding resmi Google Gemini yang terdaftar pada kuota pengguna (Primary & Fallback).
- Mengeliminasi kode penyisipan otomatis model embedding tambahan (`["text-embedding-004", "gemini-embedding-exp-03-07", "embedding-001"]`) di `_get_embedding_chain`, sehingga model yang digunakan murni bersumber dari `state.db` (`gemini.embedding_model` dan `gemini.embedding_model_fallback`).
- Ambang batas proaktif pergantian model embedding dikunci pada 90-95 RPM (kuota 100 RPM).

### R3. Audit dan Sinkronisasi Menyeluruh Seluruh Tab Pengaturan Admin
- **Tab 1 (Umum & LLM)**: Input textarea Kunci API dan Fallback Model Chain membaca dan menyimpan secara presisi ke tabel `pengaturan`. Nilai awal tidak lagi menampilkan model lama.
- **Tab 2 (Filter Kata Kunci Scraping)**: Ketiga sub-tab kategori (`mandiri`, `data`, `aset`) terikat langsung ke `keywords.indonesia_mandiri`, `keywords.objek_data_sensitif`, dan `keywords.objek_aset_digital` di database `state.db`. Filter scraping pada `src/scraper/sources.py` dan `relevance_classifier.py` secara konsisten menarik kata kunci dari database.
- **Tab 3 (Template Prompt LLM)**: Seluruh 6 prompt aktif (`klasifikasi`, `ringkas_berita`, `section_1_makro`, `section_2_mikro`, `section_3_vektor`, `section_5_emerging`) bersumber dan tersimpan di database `state.db`.
- **Tab 4 (Manajemen Sumber RSS)**: Sub-tab Internasional dan Nasional membaca serta menyimpan ke database `rss_sources_international` dan `rss_sources_indonesia`.
- **Tab 5 (Sumber Referensi CTI)**: Metadata 4 framework referensi intelijen siber (eCSIRT, ATT&CK, D3FEND, NIST) disinkronkan ke database / file prepared tanpa nilai statis yang terputus dari penyimpanan sistem.

## Acceptance Criteria

### Verifikasi Rantai Model & Quota Rate Limiter
- [ ] Database `data/state.db` pada kunci `gemini.model_chain` memuat tepat 7 model narasi tanpa sisa model lama (`gemini-2.0-flash`, `gemini-1.5-flash`, `gemini-1.5-pro`).
- [ ] Pengujian rate limiter membuktikan 7 model narasi mematuhi ambang batas proaktif masing-masing (5 RPM switch di 4, 10 RPM switch di 9, 15 RPM switch di 14).
- [ ] Model embedding terbukti hanya merotasi 2 model resmi dengan ambang batas proaktif 90 RPM (kuota 100 RPM).

### Verifikasi Eliminasi Hardcoded Data
- [ ] Tidak ada penambahan fallback model narasi usang secara hardcoded di dalam alur eksekusi `generate_text_with_chain` maupun uji koneksi API key.
- [ ] Seluruh pembacaan konfigurasi di pipeline scraping, klasifikasi, summarization, dan tren CTI memprioritaskan database `state.db` (via `SettingsManager`) sebelum file lokal.
- [ ] Seluruh unit test suite (`pytest tests/`) berjalan 100% OFFLINE tanpa error dan tanpa memicu panggilan jaringan eksternal.
</original_task>
