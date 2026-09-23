# Panduan Kelanjutan Implementasi Audit CTI (SiberHarian)

Dokumen ini adalah *handover* untuk melanjutkan proses audit dan hardening SiberHarian, memastikan AI berikutnya (atau Anda) dapat melanjutkan tanpa ambiguitas.

## Status Pekerjaan Saat Ini

**✅ Fase 1: Foundation (SELESAI)**
- `src/utils/config_loader.py` telah dibuat sebagai singleton yang otomatis me-load semua konfigurasi.
- Hardcoded dictionaries telah diekstrak ke dalam 6 file YAML di `config/rules/` (`vektor_rules.yaml`, `sektor_rules.yaml` yang sudah dibersihkan, `kategori_ancaman.yaml`, dll).
- Semua System Prompts telah diekstrak ke 7 file TXT di `config/prompts/`.
- `config/config.yaml` telah diperbarui dengan block `cti_analysis` yang memuat seluruh parameter LLM, scoring RAG, threshold clustering, dan formula *threat posture*.

**✅ Fase 2: Critical Bug Fixes (SELESAI)**
- Fungsi `_buat_fallback_sitrep_deterministik()` yang menyebabkan *NameError* (saat mode `instant_rag`) telah diimplementasikan di `cti_agents.py`.
- Tiga fungsi deteksi NLP yang menyebabkan *ImportError* di `trend_predictor.py` (`_deteksi_sektor_spesifik`, dll) telah diimplementasikan di `cti_agents.py`.
- Bug `[OWASP]` pada prefix Cloud Security Alliance (CSA) di `encyclopedia_lookup.py` telah diperbaiki, SEKALIGUS file tersebut telah di-refactor secara menyeluruh (DRY Refactoring) sehingga copy-paste 12 block pencarian kini menjadi 1 loop dinamis yang rapi.

---

## Langkah Selanjutnya (Untuk Agent AI Berikutnya)

Berikan instruksi ini secara utuh (copy-paste) kepada AI berikutnya:

### 1. Eksekusi Fase 3: Hardcode Elimination (Refactoring Module)
Tugas utama Anda adalah mengganti semua referensi *hardcoded* di dalam kode agar mengambil data dari `ConfigLoader`. Gunakan pola ini: `from src.utils.config_loader import ConfigLoader`.

*   **File `src/analytics/trend_analyzer.py`:**
    *   Hapus deklarasi `VEKTOR_RULES`, `SEKTOR_RULES`, `_SUMBER_INTERNASIONAL`, `_KEYWORDS_JAWA_TIMUR`, dan `kategori_ancaman_definisi`.
    *   Ganti dengan pemanggilan `ConfigLoader.get_rules("vektor_rules")`, dll.
    *   Ganti magic numbers untuk *threat posture* (seperti `0.035`, `0.012`, `8.0`, `6.0`, dll) dengan membaca dari `ConfigLoader.get_config()["cti_analysis"]["threat_posture"]`.
*   **File `src/analytics/cti_agents.py` & `src/analytics/trend_predictor.py`:**
    *   Hapus semua variabel konstan `SYSTEM_PROMPT_*`.
    *   Ganti dengan pemanggilan `ConfigLoader.get_prompt("section_1_makro")`, dll.
    *   Ganti parameter LLM (model `llama3.2`, `temperature`, `num_predict`, batasan karakter string/truncation) menjadi bacaan dari `ConfigLoader.get_config()["cti_analysis"]["llm"]`.
*   **File `src/analytics/rag_engine.py`:**
    *   Ganti hardcode scoring RAG (judul +3, body +1, vector +1), *fuzzy threshold* (65), dan *top_n* (3) agar mengambil dari `ConfigLoader.get_config()["cti_analysis"]["rag"]`.
*   **File `src/storage/db.py` & `src/analytics/pasca_proses.py`:**
    *   Pastikan referensi kategori dan retensi (14 hari) membaca config baru.

### 2. Eksekusi Fase 4: Pembuatan Kasus Uji (Test Cases)
*   Modifikasi file `tests/test_25_case_studies.py` atau buat file test suite baru `tests/test_future_and_adversarial.py`.
*   Tambahkan **25 kasus uji berita masa depan** (contoh: Ransomware menyerang VPN RSUD, Deepfake suara pejabat, Supply chain attack via NPM SPBE).
*   Tambahkan **30 kasus uji adversarial (jebakan)** (contoh: Berita "pertahanan" sepak bola, virus biologis Covid-19, kata "hacker" di konteks hackathon/inovasi, kasus dengan aktor anonim).
*   Gunakan struktur data kasus uji yang dapat di-run melalui *unittest mock* Ollama (mirip dengan implementasi saat ini).

### 3. Eksekusi Fase 5: Validasi
*   Jalankan `python -m pytest tests/` (atau eksekutor tes yang relevan). Pastikan pipeline RAG dan CTI tetap berjalan mulus dengan refactoring ConfigLoader, dan uji ketahanan (*robustness*) pipeline terhadap 30 kasus jebakan. Lakukan iterasi perbaikan kode jika RAG masih tertipu oleh berita jebakan.
