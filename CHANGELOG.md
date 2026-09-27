# Changelog SiberHarian

Semua perubahan penting pada proyek **SiberHarian (CSIRT Dinas Komunikasi dan Informatika Provinsi Jawa Timur)** didokumentasikan di berkas ini. Format penulisan mengacu pada [Keep a Changelog](https://keepachangelog.com/id/1.0.0/).

---

## [2.3.0] - 2026-09-25

### Ditambahkan
- **Semantic Vector Embeddings (text-embedding-004):** Engine RAG kini mendukung pencarian semantik vektor dengan embedding model Gemini untuk menemukan korelasi ancaman kontekstual, lengkap dengan fallback mulus ke pencarian leksikal.
- **Indeks Postur Ancaman Komparatif (Threat Posture):** Banner indikator skor komposit 1.0 sampai 10.0 di halaman Admin Tren yang menormalisasi frekuensi insiden, volume CVE, dan rata-rata skor CVSS secara statistik seimbang (Min-Max scaling).
- **Matriks Tindakan Ancaman Aktif:** Tabel taktis SOC untuk memetakan kategori ancaman, tingkat urgensi (KRITIS/TINGGI/SEDANG/MONITOR), fokus kerentanan website instansi, dan tindakan taktis langsung.
- **Grafik Dinamika Deret Waktu 7 Hari:** Line chart perbandingan fluktuasi harian berita insiden versus penemuan CVE kritis pada tab admin.
- **Donut Chart Sebaran Media Publik:** Visualisasi proporsi peliputan media nasional vs media global / CTI pada tab statistik publik.
- **Deteksi Anomali Lonjakan:** Penanda otomatis (*spike highlight*) pada grafik timeline harian ketika volume insiden melampaui ambang batas abnormal.

### Diubah
- **Prompt CVE Section 3 Diperbarui:** Prompt `cve_sec3_kripto` diubah menjadi ulasan *Eksploitabilitas & Weaponization (PoC)* untuk memberikan intelijen yang lebih actionable bagi analis SOC.
- **Prompt Sinyal Ancaman Baru Diperkuat:** Menambahkan arahan wajib proyeksi replikasi risiko ke domain instansi publik dan rekomendasi kewaspadaan spesifik pada `section_5_emerging.txt`.
- **Sintesis Wilayah BLUF:** Peningkatan micro-prompt regional dengan pendekatan *Bottom Line Up Front* dan analisis dampak domino lintas sektor.
- **Statistik Publik 100% Dinamis:** Memperbaiki bug variabel lokal tidak ter-return pada database, mengganti seluruh nilai KPI statis di HTML dengan kalkulasi SQL agregat riil.

---

## [2.2.0] - 2026-09-24

### Ditambahkan
- **Kepatuhan Scraping & Robots.txt:** Modul `robots_checker.py` untuk memvalidasi izin perayapan web sebelum scraping artikel lengkap.
- **User-Agent Resmi Transparan:** Identitas User-Agent terstandarisasi mencantumkan kontak dan alamat resmi CSIRT Jatim.
- **Atribusi Hak Cipta Publik:** Penambahan disclaimer perlindungan hak cipta dan kepatuhan UU No. 28 Tahun 2014 Pasal 43 huruf c pada footer portal.
- **Ekstraksi Nama Media Asli:** Menampilkan penerbit media berita asli (misal: Kompas, Antara, Detik) untuk feed Google News RSS.

### Dihapus
- Pembersihan *dead code* dan fungsi usang yang tidak terpakai pada frontend JS (`cards.js`, `beranda.js`, `tren-charts.js`, dll.).

---

## [2.1.0] - 2026-09-23

### Ditambahkan
- **Manajemen Pengaturan Dinamis Berbasis Database:** Tabel `pengaturan` untuk memodifikasi sumber RSS, kata kunci filter, dan prompt LLM secara langsung via UI admin tanpa menyentuh kode.
- **Role-Based Access Control (RBAC):** Pemisahan 2 tipe admin (Superadmin dan Viewer) dengan pengamanan kata sandi menggunakan hashing `bcrypt`.
- **Panel Pengaturan Admin (_settings.html):** Antarmuka terpadu untuk mengelola konfigurasi sistem.

---

## [2.0.0] - 2026-09-22

### Diubah
- **Migrasi Arsitektur Inferensi AI:** Beralih sepenuhnya dari Ollama lokal ke Google Gemini API dengan rantai fallback otomatis (Gemini 3.1 Flash Lite sampai 3.7 Flash) guna menjamin keandalan uptime dan kecepatan inferensi.
- **Arsitektur SIMP (Sequential Isolated Micro-Prompts):** Restrukturisasi pembuatan laporan SITREP CTI menjadi modul-modul independen yang stabil tanpa kerapuhan format JSON.
- **Ensiklopedia Standar Keamanan Siber:** Integrasi 12 framework keamanan siber (165 entitas) untuk rekomendasi mitigasi deterministik bebas halusinasi.

---

## [1.0.0] - 2026-08-15

### Rilis Awal
- Versi perdana SiberHarian dengan pemantauan RSS siber internasional dan nasional.
- Penyimpanan SQLite lokal di `data/state.db`.
- Dashboard publik berbasis Tailwind CSS dan konsol monitor terminal SSE.
