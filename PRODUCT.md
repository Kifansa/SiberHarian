# Product

<!-- impeccable:product-schema 1 -->

## Platform

Web (Fitur Terintegrasi pada Portal Resmi CSIRT Provinsi Jawa Timur: `https://csirt.jatimprov.go.id/`)

## Users

1. **Admin Tim CTI & Analis Keamanan CSIRT Diskominfo Jawa Timur (Internal)**:
   - Tim teknis operasional Security Operations Center (SOC) yang bertugas memantau insiden siber harian, mengeksekusi pipeline pengumpulan data & LLM summarization, menganalisis insiden siber kritis, memetakan lonjakan tren ancaman mingguan berbasis kerangka MITRE ATT&CK, serta mengekspor Laporan Intelijen Ancaman Siber Mingguan Resmi (PDF) untuk briefing pimpinan.
2. **Pengunjung Portal CSIRT Jatim & Publik Umum (Eksternal)**:
   - Masyarakat umum, pengelola website Organisasi Perangkat Daerah (OPD)/BUMD Jawa Timur, praktisi IT, dan akademisi yang membutuhkan akses transparan terhadap berita insiden siber terkini, arsip insiden, serta **Statistik Berita & Intelijen Publik** berbasis data fakta nyata untuk meningkatkan literasi dan kewaspadaan keamanan digital (*cyber awareness*).

## Product Purpose

SiberHarian adalah modul intelijen ancaman siber (*Cyber Threat Intelligence*) dan portal edukasi keamanan terpadu yang diintegrasikan ke dalam ekosistem portal resmi CSIRT Provinsi Jawa Timur. Platform ini menjalankan fungsi ganda:
1. Memberikan instrumen CTI operasional dan analisis prediktif terakselerasi AI bagi Tim CSIRT Diskominfo Jatim guna memitigasi serangan sebelum mengeksploitasi aset pemerintah daerah.
2. Menyajikan pusat informasi dan statistik fakta siber yang ramah publik guna mengedukasi masyarakat mengenai tren penipuan digital (phishing, malware, kebocoran data) dan modus kejahatan siber yang perlu diwaspadai.

## Positioning

Solusi intelijen dan edukasi keamanan siber terpadu berbasis *Cloud-Accelerated Intelligence with Google Gemini API*: mengombinasikan agregasi berita siber harian (nasional & global) dengan inferensi AI berbasis Google Gemini API dengan fallback chain otomatis dan Semantic Vector RAG (`gemini-embedding-001` dengan fallback otomatis ke model Gemini Embedding 2). Menyediakan dua lapis pengalaman pengguna: *Operational CTI Cockpit* untuk analis internal dan *Public Cyber Radar* berbasis data empiris murni untuk masyarakat luas.

## Operating Context

- **Mode Publik (2 Tab Saja)**: Pengunjung portal mengakses tab **Beranda & Statistik** (gabungan wawasan KPI dinamis berbasis fakta, Word Cloud interaktif kasus insiden spesifik, grafik fakta siber, sebaran sumber media pelapor, intisari artikel edukasi asli dari database, serta feed berita insiden & edukasi hari terakhir) dan tab **Arsip** (penelusuran riwayat dan filter tanggal). Pengalaman publik bersih dari tombol operasional backend maupun konsol teknis.
- **Mode Admin Tim CTI (3 Tab + Settings)**: Analis mengakses tab **Beranda Admin** (dilengkapi konsol terminal real-time SSE untuk menjalankan atau membatalkan pipeline scraping & summarization), tab **Arsip**, tab **Tren Siber CTI** (indeks postur ancaman komparatif, matriks tindakan taktis, dinamika deret waktu 7 hari, klastering insiden wilayah, dan pemetaan TTPs MITRE ATT&CK), serta tab **Pengaturan** (manajemen sumber RSS, keyword, dan prompt bagi Superadmin).

## Capabilities and Constraints

- **Agregasi Multi-Sumber & Kepatuhan Legal**: Memantau feed berita siber internasional dan media nasional Indonesia dengan User-Agent transparan, validasi `robots.txt` otomatis, dan kepatuhan UU Hak Cipta No. 28/2014.
- **LLM Cloud-Accelerated & Semantic RAG**: Menggunakan Google Gemini API dengan sistem fallback otomatis (Gemini 3.1 Flash Lite sampai 3.7 Flash) dan Semantic Vector Search menggunakan model `gemini-embedding-001` (Gemini Embedding 1) dengan fallback ke model Gemini Embedding 2 (`gemini-embedding-exp-03-07` / `text-embedding-004`) untuk relevansi kontekstual tinggi.
- **Arsitektur Pemrosesan CTI Modular (SIMP)**: Menggunakan *Sequential Isolated Micro-Prompts* (SIMP) yang mengeksekusi analisis bagian demi bagian secara terisolasi (< 450 token per inferensi), menjamin kestabilan LLM tanpa bottleneck memori dan bebas ketergantungan format JSON rapuh.
- **Taksonomi Sektor IIV & MITRE ATT&CK**: Standardisasi 10 sektor target berdasarkan **Perpres No. 82 Tahun 2022 tentang Infrastruktur Informasi Vital (IIV)** serta 12 taktik **MITRE ATT&CK Enterprise Matrix** untuk analisis vektor serangan yang akurat.
- **Guardrail Semantic Role Separation**: Memisahkan peran entitas secara ketat sehingga vendor/peneliti keamanan (Zimperium, Mandiant, Kaspersky, BSSN, Google Security) tidak pernah keliru dilabeli sebagai aktor penyerang.
- **Ensiklopedia Standar Keamanan Siber Komprehensif**: Mengintegrasikan 12 kerangka kerja global dan nasional (165 entitas standar) meliputi MITRE ATT&CK, MITRE D3FEND, NIST CSF 2.0, OWASP Top 10, CWE, BSSN CSIRT Framework, CIS Controls, Indeks KAMI BSSN, CISA CPG, ISO/IEC 27001, CSA CCM, dan CSIRT Framework Indonesia.
- **Statistik Publik Berbasis Fakta Nyata**: Visualisasi interaktif (Chart.js) murni bersumber dari database empiris (frekuensi kata kunci ancaman, sektor vital sasaran IIV, timeline harian, sebaran media pelapor) tanpa kesimpulan spekulatif AI.
- **Analisis Strategis CTI Internal**: Postur risiko ancaman komparatif ternormalisasi, matriks tindakan taktis siap eksekusi, dan agen CTI multi-dimensi dengan RAG ensiklopedia siber untuk membedah pola serangan dan menyusun rekomendasi mitigasi bertingkat.
- **Penyimpanan Terpusat SQLite (`data/state.db`)**: Tracking riwayat konten terkirim (anti-duplikasi), metadata artikel & insiden, konfigurasi dinamis, dan cache statistik instan (< 5 ms).
- **Ekspor Dokumen PDF Resmi**: Generator laporan berkas intelijen mingguan siap cetak langsung dari browser.

## Brand Commitments

- **Identitas Terintegrasi**: SiberHarian - Fitur Berita & Intelijen Siber CSIRT Provinsi Jawa Timur.
- **Identitas Visual**: Tema *Cyber-HUD / Tactical Dark Terminal Edition* resmi selaras dengan portal CSIRT Provinsi Jawa Timur (`https://csirt.jatimprov.go.id/`) (Dark Navy `#0a1628`, Elevated Surface `#0d2137`, Glassmorphic Card `rgba(17,34,64,0.7)`, Cyber Cyan `#00d4ff`, Teal `#00ff88`, Neon Green `#00ff9d`, Hazard Red `#ff3366`, dan sudut potong chamfer 10px).
- **Gaya Bahasa**:
  - *Mode Publik*: Bahasa Indonesia yang komunikatif, lugas, mudah dipahami warga non-teknis, tanpa jargon membingungkan, dan berorientasi pada pencegahan praktis.
  - *Mode Admin CTI*: Bahasa Indonesia teknis CTI profesional, presisi, padat, berdasar bukti empiris, dan berorientasi tindakan mitigasi terukur.

## Evidence on Hand

- Database SQLite aktif di `data/state.db` dengan riwayat artikel dan laporan insiden siber riil.
- Endpoint backend FastAPI di `src/web/app.py` yang melayani API data harian, arsip, SSE streaming, dan agregat statistik.
- Desain antarmuka responsif di `src/web/templates/` dan komponen modular di `src/web/static/js/`.

## Product Principles

1. **Integritas Fakta di Atas Spekulasi**: Statistik untuk publik disajikan 100% dari data empiris tanpa fabrikasi atau generalisasi berlebih.
2. **Kedaulatan & Keamanan Data (Local First)**: Penyimpanan informasi berjalan sepenuhnya di infrastruktur lokal, dipadukan dengan akselerasi LLM Gemini Diskominfo Jawa Timur.
3. **Pemisahan Peran yang Tegas**: Akses operasional teknis (terminal scraping, eksekusi pipeline) terisolasi untuk Tim CTI, sementara publik mendapatkan pengalaman membaca yang nyaman dan mendidik.
4. **Desain Berorientasi Aksi**: Baik analis maupun masyarakat umum mendapatkan nilai nyata: analis memperoleh rekomendasi mitigasi teknis, sementara masyarakat mendapatkan pemahaman risiko dan tips proteksi diri di ruang digital.

## Accessibility & Inclusion

- Rasio kontras teks sangat tinggi (15.6 : 1 untuk teks utama `#e0f0ff` terhadap `#0a1628`) memenuhi standar WCAG AAA.
- Tipografi terstandar: `Sora` untuk seluruh teks narasi dan headline; `Fragment Mono` / `Share Tech Mono` khusus untuk data teknis, metrik, skor postur risiko, tombol chamfered, dan notasi HUD brackets.
- Dukungan responsif penuh untuk monitor desktop SOC command center (1440px+), tablet inspeksi, dan smartphone masyarakat umum.


