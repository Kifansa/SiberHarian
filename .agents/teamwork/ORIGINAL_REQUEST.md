# Original User Request

## 2026-10-20T15:23:35Z

Upgrade project SiberHarian (CSIRT Diskominfo Jatim) yang sudah ada: tambahkan lapisan intelijen tervalidasi berbasis sumber resmi (taksonomi insiden MISP/ENISA, MITRE ATT&CK, MITRE D3FEND, NIST OSCAL) lengkap dengan pipeline download, persiapan data, indeks RAG, klasifikasi per berita, update berkala, dan evaluasi. Hasilnya **menambah** informasi tervalidasi ke dashboard admin yang sudah ada, bukan mengganti teks yang ada. Tujuan: produksi (dipakai tim CTI internal).

Working directory: D:\penting\magang\kominfo\NOTIFIKASI-BERITA (project yang sudah ada; pelajari kode, README, dan tes yang ada sebelum mengubah apa pun)
Integrity mode: development

Jangan sentuh dan jangan baca file `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` dan folder `LAPORAN DASHBOARD ADMIN/`.

## Spesifikasi dari User (verbatim, wajib diikuti)

```
# SUMBER DATA
1. Taksonomi insiden: repositori github.com/MISP/misp-taxonomies. Periksa isinya, pilih taksonomi klasifikasi insiden yang paling cocok (kandidat: taksonomi berbasis eCSIRT/ENISA, circl, common-taxonomy, veris). Sebagai alternatif, ENISA Reference Security Incident Taxonomy: github.com/enisaeu/Reference-Security-Incident-Taxonomy-Task-Force. Jelaskan alasan pilihanmu. Dari taksonomi itu buat daftar tertutup 8-12 kategori praktis untuk berita (mis. ransomware, data breach, DDoS, defacement, phishing/penipuan, malware, eksploitasi kerentanan, akses tidak sah, lainnya, tidak dapat ditentukan), dan petakan tiap kategori ke induknya di taksonomi sumber.
2. MITRE ATT&CK (Enterprise): repositori github.com/mitre-attack/attack-stix-data, JSON STIX 2.1. Verifikasi path file terbaru (kemungkinan enterprise-attack/enterprise-attack.json) dan cara repositori menandai versi.
3. MITRE D3FEND: API JSON di https://d3fend.mitre.org. Endpoint: /api/ontology/inference/d3fend-full-mappings.json (pemetaan serangan ke pertahanan), /api/technique/all.json, /api/offensive-technique/all.json, /api/version.json. Jangan pakai ontologi OWL/TTL.
4. NIST: katalog OSCAL JSON resmi (SP 800-53 Rev 5 dan CSF 2.0) dari github.com/usnistgov/oscal-content. Verifikasi path file yang tepat.
Catatan: URL dan path di atas berasal dari riset awal dan belum semuanya diuji. Verifikasi setiap URL sebelum dipakai, dan laporkan jika ada yang berubah. Jangan mengarang path.
Proyek sudah punya file lokal: mitre.json, d3fend.json, nist.json, bssn.json. Periksa struktur masing-masing dulu, dan putuskan apakah dipakai ulang atau dibuat ulang dari sumber resmi.

# TAHAP 1: DOWNLOAD
Tulis skrip download untuk tiap sumber ke folder staging (data/raw/<sumber>/<tanggal>/), dengan timeout, retry, dan log. Simpan metadata versi (tag rilis/commit hash/hasil version.json), URL, tanggal unduh, dan checksum SHA-256.

# TAHAP 2: PERSIAPAN DATA
- Jangan masukkan JSON STIX mentah ke RAG. Ratakan menjadi satu dokumen teks per teknik ATT&CK: id (T-number), nama, tactic, deskripsi, platform, dan flag revoked/deprecated (buang yang revoked/deprecated).
- Taksonomi insiden: satu dokumen per kategori (nama, definisi, contoh berita).
- D3FEND: tabel pemetaan (ATT&CK ID -> daftar teknik D3FEND dengan id, nama, definisi, tactic D3FEND). Simpan sebagai tabel/database relasional, BUKAN di vector store. Lookup mitigasi harus deterministik.
- NIST: satu dokumen per kontrol/subkategori (id, judul, pernyataan, family/fungsi). Dipakai hanya sebagai sumber informasi tambahan.
- Setiap dokumen wajib punya metadata: sumber, versi sumber, id asli, tanggal ingest.

# TAHAP 3: INDEKS RAG
- Buat koleksi vector terpisah: (a) ATT&CK, (b) taksonomi insiden, (c) NIST. D3FEND tidak masuk vector store.
- Pakai model embedding multibahasa (karena sebagian teks bisa campuran Indonesia-Inggris), dan jelaskan pilihanmu.
- Simpan teks berita asli dan hasil terjemahan; retrieval memakai teks terjemahan.

# TAHAP 4: ALUR PEMAKAIAN (per berita)
1. Klasifikasi insiden: retrieval dari koleksi taksonomi, lalu LLM memilih SATU label utama (opsional label tambahan) dari daftar tertutup. Output JSON terstruktur: label, confidence (0-1), kutipan bukti dari berita, dan alasan singkat. Label "tidak dapat ditentukan" wajib tersedia.
2. Teknik ATT&CK: jalankan HANYA jika berita menyebut alur/cara serangan. Ambil top-k kandidat (10-20) dari koleksi ATT&CK, LLM memilih teknik beserta kutipan bukti dan confidence. Jika bukti lemah, berhenti di tingkat tactic atau kembalikan "tidak ditentukan". Jangan menebak.
3. Validasi: setiap ID teknik yang dikeluarkan LLM harus ada di data ATT&CK yang aktif. Jika tidak, tolak dan catat.
4. Mitigasi: dari teknik ATT&CK yang valid, lakukan lookup deterministik di tabel pemetaan D3FEND. LLM tidak boleh menambah teknik D3FEND yang tidak ada di hasil lookup. Tampilkan sebagai "saran mitigasi umum untuk teknik terkait", bukan temuan spesifik insiden.
5. NIST: hanya jika admin meminta informasi lebih; ambil kontrol/subkategori relevan dari koleksi NIST dan tampilkan sebagai referensi tambahan beserta sumbernya.
6. Narasi LLM hanya boleh memakai fakta dari teks berita dan hasil tervalidasi di atas; sertakan link berita sumber; bedakan fakta dari inferensi.
7. Simpan hasil beserta versi ATT&CK/D3FEND/NIST/taksonomi yang dipakai, serta kolom koreksi manual admin.

# TAHAP 5: SKRIP UPDATE BERKALA (WAJIB)
Buat skrip update terpisah untuk ATT&CK, D3FEND, NIST, dan taksonomi MISP, dengan perilaku berikut:
- Cek versi dulu (commit/tag rilis GitHub, atau /api/version.json untuk D3FEND). Jika tidak berubah, berhenti dan catat "tidak ada pembaruan".
- Unduh ke staging, validasi skema dan jumlah record (tolak jika turun drastis atau kosong), bandingkan dengan versi sebelumnya, dan buat laporan diff (teknik baru, berubah, revoked).
- Hanya re-embed dokumen yang berubah.
- Update atomik: gunakan indeks baru lalu tukar; simpan versi lama untuk rollback.
- Jika ada ID teknik lama yang hilang/revoked, tandai insiden lama yang memakainya untuk ditinjau, jangan dihapus diam-diam.
- Logging, notifikasi kegagalan (email/webhook), dan idempoten (aman dijalankan ulang).
- Jadwal: contoh cron/systemd timer atau GitHub Actions (mis. mingguan untuk ATT&CK/D3FEND/MISP, bulanan untuk NIST). Dukung opsi proxy dan mirror internal karena jaringan pemerintah bisa membatasi akses keluar.

# TAHAP 6: EVALUASI
Sediakan skrip evaluasi: dari 200-500 berita berlabel manual, hitung precision, recall, dan F1 per kategori serta akurasi teknik ATT&CK. Jalankan ulang setiap kali prompt, model, embedding, atau versi data berubah.

# ATURAN
- Jangan mengarang URL, ID teknik, atau isi taksonomi. Jika tidak yakin, katakan dan minta verifikasi.
- Jawab dalam bahasa Indonesia, kode dan komentar boleh bahasa Inggris.
- Kerjakan bertahap dan tanyakan satu hal saja jika ada keputusan penting yang butuh input saya.
```

## Requirements

### R0. Arahan tambahan dari user
- Jika butuh akses internet untuk verifikasi URL/path, isi repositori, atau versi, gunakan fitur web search. Jika unduhan HTTP langsung dari mesin ini gagal, laporkan dengan jelas dan jangan memalsukan data.
- Ensiklopedia yang ada di `data/encyclopedia/` adalah data **dummy**: ganti semuanya dengan data dari sumber resmi. Untuk file yang sumber resminya tidak disebut dalam spesifikasi (mis. bssn, owasp, cwe, cis_controls, iso27001, csa_ccm, cisa_cpg, indeks_kami, csirt_framework), tanya user dulu sebelum memutuskan sumber penggantinya atau menghapusnya.
- Ini adalah **upgrade** untuk menambah informasi agar project valid, bukan perombakan menyeluruh. Jika ada yang tumpang tindih dengan fitur/logika yang sudah ada atau ambigu, berhenti dan tanya user dulu.

### R1. Pipeline data sumber resmi (Tahap 1–3)
Implementasikan Tahap 1–3 sesuai spesifikasi di atas. Untuk embedding: tetap memakai Gemini embedding yang sudah ada di project (`gemini-embedding-001` dengan rantai fallback yang sudah dikonfigurasi). Jelaskan mengapa model ini memenuhi syarat multibahasa. Laporkan hasil verifikasi setiap URL/path sumber (mana yang valid, mana yang berubah) dan keputusan pakai ulang/buat ulang untuk `mitre.json`, `d3fend.json`, `nist.json`, `bssn.json` beserta alasannya.

### R2. Alur pemakaian per berita (Tahap 4)
Implementasikan Tahap 4 sesuai spesifikasi dan sambungkan ke pipeline yang sudah ada.

### R3. Integrasi dashboard admin (hanya menambah)
- Hasil klasifikasi insiden tampil di KPI **"[ POLA ANCAMAN ]"**.
- Klasifikasi tampil sebagai penjelasan tambahan di section **"ANALISIS BERITA SIBER & REKOMENDASI MITIGASI"**, bagian **"INSIDEN MELONJAK DRASTIS"** dan **"TREN INSIDEN MINGGUAN"**.
- Rujukan MITRE ATT&CK tampil di bagian **"VEKTOR SERANGAN TREN INSIDEN MINGGUAN"**.
- Rekomendasi aksi memakai MITRE D3FEND dan NIST.
- Update ini hanya menambah informasi agar valid. Teks dan konten yang sudah ada tidak boleh dihapus atau diganti. Jika ragu apakah suatu perubahan menggantikan teks yang ada, berhenti dan tanya user dulu.

### R4. Update berkala dan evaluasi (Tahap 5–6)
Implementasikan Tahap 5 dan 6 sesuai spesifikasi. Belum ada dataset berlabel manual: buat draf label otomatis dari berita di `data/state.db` (ditandai jelas sebagai draf yang menunggu tinjauan user, bukan ground truth), dengan format yang mudah dikoreksi user. Skrip evaluasi harus bisa langsung dijalankan ulang setelah user mengoreksi label.

## Acceptance Criteria

### Integritas sumber
- [ ] Ada laporan verifikasi URL/path: tiap sumber dicek live, perubahan dari spesifikasi dilaporkan, tanpa path karangan.
- [ ] Setiap dokumen ter-ingest punya metadata sumber, versi sumber, id asli, dan tanggal ingest (dicek dengan skrip/tes).
- [ ] Koleksi ATT&CK tidak memuat teknik revoked/deprecated (dicek dengan tes).
- [ ] Folder staging berisi metadata versi + SHA-256 yang cocok dengan file yang diunduh.

### Kebenaran pipeline (tes otomatis)
- [ ] ID teknik ATT&CK yang tidak ada/tidak aktif dari LLM ditolak dan dicatat.
- [ ] Mitigasi D3FEND yang ditampilkan identik dengan hasil lookup tabel; LLM tidak bisa menambah teknik D3FEND.
- [ ] Berita tanpa bukti alur serangan tidak menghasilkan teknik (berhenti di tactic atau "tidak ditentukan").
- [ ] Output klasifikasi selalu valid terhadap skema JSON dan daftar label tertutup, termasuk "tidak dapat ditentukan".
- [ ] Hasil tersimpan memuat versi ATT&CK/D3FEND/NIST/taksonomi dan kolom koreksi manual admin.

### Update berkala
- [ ] Skrip update dijalankan dua kali berturut-turut: run kedua mencatat "tidak ada pembaruan" dan tidak mengubah apa pun.
- [ ] Tes: staging kosong atau jumlah record turun drastis ditolak, indeks aktif tidak berubah, dan rollback berfungsi.
- [ ] Tes: ID teknik yang hilang/revoked menandai insiden lama untuk ditinjau, tanpa menghapusnya.
- [ ] Ada laporan diff (baru/berubah/revoked) dan hanya dokumen yang berubah yang di-embed ulang.

### Dashboard dan regresi
- [ ] Kelima titik tampilan di R3 menampilkan data baru; perbandingan sebelum/sesudah menunjukkan teks lama tetap ada.
- [ ] Seluruh 36 tes yang sudah ada (`python -m pytest tests/`) tetap lulus, ditambah tes baru.

### Evaluasi
- [ ] Skrip evaluasi berjalan pada draf dataset berlabel dan mengeluarkan precision/recall/F1 per kategori serta akurasi teknik ATT&CK.

## Follow-up — 2026-10-20T15:40:57Z

Pengingat dari user (R0): untuk 9 file ensiklopedia yang sumber resminya tidak ada di spesifikasi (bssn, owasp, cwe, cis_controls, iso27001, csa_ccm, cisa_cpg, indeks_kami, csirt_framework), JANGAN ganti atau hapus sebelum bertanya ke user. Kirim pertanyaannya ke saya (usulan sumber resmi pengganti per file + opsi hapus/pertahankan), lalu saya teruskan ke user. Perlakukan hal yang sama untuk setiap tumpang tindih dengan fitur yang sudah ada (mis. Modul 4 rekomendasi yang memakai ensiklopedia, KPI Pola Ancaman yang saat ini berbasis regex): tanyakan dulu sebelum mengubah perilaku yang ada.

## Follow-up — 2026-10-20T15:44:14Z

Keputusan user atas konsultasi R0:

1. 9 file ensiklopedia (bssn, indeks_kami, csirt_framework, owasp, cwe, cis_controls, iso27001, csa_ccm, cisa_cpg): HAPUS. Sistem hanya memakai ATT&CK, D3FEND, NIST, dan taksonomi insiden (eCSIRT/ENISA). File mitre.json, d3fend.json, nist.json lama juga dummy, jadi ganti dari sumber resmi. Sesuaikan semua kode yang membaca file-file itu (mis. encyclopedia_lookup.py, rag_engine.search_encyclopedia_per_incident, Modul 4, endpoint /api/ensiklopedia, UI yang menampilkannya) agar tidak rusak. Tes lama yang secara spesifik menguji keberadaan 9 file itu boleh disesuaikan, tapi laporkan setiap tes yang diubah beserta alasannya; jangan hapus tes untuk menyembunyikan kegagalan. Jika penghapusan memaksa perubahan teks/fitur yang terlihat user di luar sumber ensiklopedia itu sendiri, tanya dulu.

2. Desain 2 titik tumpang tindih: DISETUJUI dengan satu perubahan. Modul 4: teks lama tetap utuh, tambahkan blok "Saran Mitigasi Terverifikasi MITRE D3FEND" dan "Referensi Standar NIST Tambahan" di bawahnya (catatan: karena 9 file dihapus, bagian teks lama yang bersumber dari file-file itu otomatis hilang; itu diizinkan). KPI Pola Ancaman: teks lama tetap utuh, tambahkan badge "Taksonomi Resmi: [label]" TANPA persentase keyakinan.

## Follow-up — 2026-10-20T15:56:56Z

Catatan verifikasi dari user/parent: 150 tes E2E baru dilaporkan LULUS 100% padahal Tahap 2–4 (flattening, tabel D3FEND, indeks RAG, klasifikasi per berita, validasi ID, integrasi dashboard) belum selesai diimplementasikan. Itu tanda tes terlalu lemah, banyak di-skip/mock, atau menguji placeholder. Wajib audit: (1) berapa tes yang benar-benar menjalankan kode produksi vs mock/skip/xfail, (2) pastikan tes acceptance criteria utama (penolakan ID ATT&CK palsu, D3FEND identik dengan lookup, tidak ada teknik tanpa bukti alur serangan, update idempoten, rollback, penandaan insiden revoked, 5 titik dashboard tetap berisi teks lama) GAGAL bila implementasinya dihapus/dirusak (mutation check). Laporkan hasil audit ini secara transparan.



## Follow-up — 2026-10-21T02:12:53Z

Lanjutan upgrade SiberHarian (CSIRT Diskominfo Jatim): KPI dashboard admin diubah agar memakai taksonomi jenis serangan, seluruh project diaudit untuk menemukan hasil yang hardcoded atau sengaja diarahkan agar terlihat benar, dan klasifikasi sektor target dibuat realistis. Semua hasil harus dinamis mengikuti berita yang berubah-ubah, bukan teks/hasil yang ditanam di kode.

Working directory: D:\penting\magang\kominfo\NOTIFIKASI-BERITA (project yang sudah ada; upgrade sebelumnya sudah menambah `src/cti/`, taksonomi eCSIRT 11 kategori, ATT&CK, D3FEND, NIST)
Integrity mode: development

Jangan sentuh dan jangan baca `Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx` dan folder `LAPORAN DASHBOARD ADMIN/`. Jika ada keputusan penting atau ambigu, berhenti dan tanya user (satu pertanyaan, dalam bahasa Indonesia).

## Requirements

### R1. KPI [ POLA ANCAMAN ] berbasis taksonomi
Nilai utama KPI adalah kategori taksonomi jenis serangan (taksonomi insiden tertutup yang sudah ada di project) yang dominan minggu ini, dihitung dari hasil klasifikasi berita, beserta angka dan pertumbuhannya. Badge tambahan "Taksonomi Resmi: [...]" dihapus karena nilai utamanya sudah taksonomi.

### R2. KPI [ SINYAL ANCAMAN BARU ] berbasis taksonomi
Entitas seperti "Ratusan Supermarket Prancis" diganti menjadi kategori taksonomi ancaman. Definisi dari user: KPI ini menampilkan insiden **baru** yang sedang naik. Jika berita menyebut ada insiden baru dan ada beberapa kasus, kategori itu harus naik ke KPI ini meskipun jumlahnya lebih sedikit dari kategori yang sedang tren di [ POLA ANCAMAN ]. Kebaruan lebih penting daripada volume; satu berita tunggal tidak cukup.

### R3. Audit hardcoded / hasil yang diarahkan (seluruh project)
Audit seluruh project (KPI, grafik, tabel, SITREP 5 bagian di ANALISIS BERITA SIBER & REKOMENDASI MITIGASI, kasus wilayah, statistik publik): temukan teks/nilai/ID yang ditanam di kode, fallback statis yang tampil seolah hasil analisis, default yang menutupi data kosong, atau logika yang dibuat agar tes/hasil terlihat benar. Untuk section ANALISIS BERITA SIBER & REKOMENDASI MITIGASI, berikan opsi ke user per temuan (perbaiki dengan cara X, atau tetap seperti sekarang beserta risikonya). **Jangan ubah temuan audit sebelum user memilih opsi**, kecuali yang sudah jelas diminta di R1, R2, R4.

### R4. [ SEKTOR TARGET TERPAPAR ]
Klasifikasi sektor per berita memakai LLM dengan daftar sektor tertutup (10 sektor IIV Perpres 82/2022), wajib menyertakan kutipan bukti dari teks berita, dan wajib punya label "Tidak dapat ditentukan" bila bukti tidak ada. Jalankan untuk seluruh berita minggu ini. Hasil harus seperti kasus nyata (sektor korban yang benar-benar disebut di berita), bukan sektor tebakan/generik. Sediakan sampel berlabel draf agar user bisa mengoreksi, dan skrip untuk mengukur akurasinya terhadap koreksi user.

## Acceptance Criteria

### Dinamis
- [ ] Mengganti/menambah data berita uji (mis. memasukkan satu set berita berbeda ke DB uji) mengubah nilai [ POLA ANCAMAN ], [ SINYAL ANCAMAN BARU ], dan [ SEKTOR TARGET TERPAPAR ] sesuai isi berita baru (dibuktikan dengan tes otomatis pada dua dataset berbeda).
- [ ] Tidak ada teks hasil analisis, nama sektor, kategori, atau ID teknik yang ditampilkan sebagai hasil padahal berasal dari string tetap di kode (dibuktikan oleh laporan audit + tes).

### KPI
- [ ] [ POLA ANCAMAN ] menampilkan kategori taksonomi dari daftar tertutup; badge "Taksonomi Resmi" tidak ada lagi.
- [ ] [ SINYAL ANCAMAN BARU ] menampilkan kategori taksonomi, bukan nama entitas/judul berita.
- [ ] Tes: dataset di mana kategori A paling banyak (tren lama) dan kategori B baru muncul minggu ini dengan ≥2 kasus → POLA ANCAMAN = A, SINYAL ANCAMAN BARU = B.
- [ ] Tes: kategori baru dengan hanya 1 berita tidak muncul sebagai sinyal baru.

### Sektor
- [ ] Setiap hasil sektor punya kutipan bukti yang benar-benar ada di teks berita (dicek otomatis: kutipan adalah substring teks berita).
- [ ] Label di luar daftar 10 sektor IIV + "Tidak dapat ditentukan" ditolak.
- [ ] Ada draf sampel berlabel dan skrip akurasi yang bisa dijalankan ulang setelah koreksi user.

### Audit
- [ ] Laporan audit (file markdown di repo) berisi daftar temuan: lokasi file/baris, jenis masalah, dampak di UI, dan opsi perbaikan vs tetap. Untuk ANALISIS BERITA SIBER & REKOMENDASI MITIGASI, opsi diteruskan ke user sebelum diubah.

### Regresi
- [ ] Seluruh tes yang ada (`python -m pytest tests/`) tetap lulus; tes yang sengaja diubah karena perilaku baru dilaporkan beserta alasannya.
## Follow-up — 2026-10-21T02:48:39Z

Keputusan User atas 5 Temuan Audit R3:
User memilih: **Terapkan Opsi A untuk SEMUA ke-5 temuan** (Perbaiki semua ke-5 titik agar 100% jujur & dinamis sesuai data berita, tanpa fallback hardcoded T1190, D3-MFA, AC-2/PR.AC-1, distribusi eCSIRT fiktif, maupun tebakan senjata/sektor default).

Silakan langsung eksekusi penuh:
1. R1: KPI [ POLA ANCAMAN ] memakai kategori taksonomi jenis serangan yang dominan minggu ini beserta angka & growth; hapus badge tambahan "Taksonomi Resmi: [...]".
2. R2: KPI [ SINYAL ANCAMAN BARU ] memakai kategori taksonomi insiden baru yang sedang naik (kebaruan diutamakan dibanding volume, minimal >= 2 kasus berita agar bukan alarm palsu dari 1 berita tunggal; bukan lagi entitas seperti "Ratusan Supermarket Prancis").
3. R3: Terapkan Opsi A pada kelima titik di ANALISIS BERITA SIBER & REKOMENDASI MITIGASI serta bersihkan nilai hardcoded/terarah di seluruh project, dan tulis laporan audit lengkap (file markdown di repo).
4. R4: Klasifikasi [ SEKTOR TARGET TERPAPAR ] memakai LLM dengan 10 sektor IIV Perpres 82/2022 + "Tidak dapat ditentukan", wajib menyertakan kutipan bukti yang merupakan substring teks berita, dijalankan untuk berita minggu ini, disertai sampel berlabel draf dan skrip evaluasi akurasi.
5. Verifikasi dengan tes otomatis pada 2 dataset berita berbeda untuk membuktikan semua nilai berubah dinamis sesuai isi berita.


## Follow-up — 2026-10-24T11:31:58Z

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
