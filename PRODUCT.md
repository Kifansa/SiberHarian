# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users

- **Analis Keamanan Siber & Tim CSIRT Diskominfo Jawa Timur**: Tim teknis yang bertugas memantau insiden siber harian, menganalisis kerentanan, dan mengambil tindakan mitigasi/pencegahan dini untuk melindungi website dan infrastruktur digital pemerintah provinsi Jawa Timur.
- **Pengelola & Tim Keamanan Informasi**: Tim yang membutuhkan rangkuman eksekutif, evaluasi postur ancaman siber mingguan, serta bukti kepatuhan keamanan.

## Product Purpose

SiberHarian adalah platform intelijen ancaman siber (Cyber Threat Intelligence) terpadu yang memantau, mengagregasi, meringkas, dan menganalisis tren berita insiden siber (nasional & internasional) serta data kerentanan CVE kritis secara otomatis setiap hari. Tujuannya adalah memberikan pemahaman situasional cepat dan rekomendasi mitigasi preventif bagi tim Diskominfo Jawa Timur sebelum ancaman mengeksploitasi aset lokal.

## Positioning

Intelijen keamanan siber lokal dan mandiri tanpa dependensi cloud pihak ketiga: mengombinasikan agregasi berita siber harian + NVD CVE NIST dengan inferensi LLM lokal (Ollama / Qwen) secara on-premise, dilengkapi analitik lonjakan 7 hari, arsip interaktif, dan prediksi ancaman bertingkat yang kontekstual terhadap proteksi website instansi pemerintah.

## Operating Context

- **Rutinitas Pemantauan Harian**: Pipeline otomatis dijalankan setiap hari untuk mengambil berita siber terbaru, mengunduh data CVE HIGH/CRITICAL dari NVD NIST, melakukan klasifikasi relevansi, deduplikasi, dan peringkasan berbasis AI lokal.
- **Lingkungan Kerja**: Tim keamanan memantau dashboard web (tab Beranda, Tren, Arsip) melalui browser desktop, serta menerima alert notifikasi harian melalui Bot Telegram.
- **Tindakan Lanjut Operasional**: Analis membaca rekomendasi mitigasi teknis dan jangka panjang, memeriksa korelasi vendor yang terdampak, lalu melakukan hardening atau koordinasi patching pada infrastruktur website OPD di Jawa Timur.

## Capabilities and Constraints

- **Agregasi Multi-Sumber**: Mengambil berita keamanan siber dari berbagai RSS/feed media nasional & internasional, serta API NVD NIST untuk CVE skor 9.0–10.0.
- **LLM Lokal On-Premise**: Inferensi AI menggunakan Ollama (model Qwen2.5-Coder / Qwen2.5:7b) untuk memastikan privasi data dan kedaulatan informasi tanpa ketergantungan API cloud eksternal.
- **Analitik & Deteksi Tren 14 Hari**: Menghitung lonjakan kata kunci ancaman (growth %) dan sebaran vendor CVE terdampak, membandingkan 7 hari terkini vs 7 hari baseline.
- **Prediksi Intelijen & Mitigasi**: LLM memetakan TTPs penyerang, sektor terpapar, korelasi ancaman, serta rekomendasi mitigasi bertingkat (Prioritas teknis & Tindak lanjut jangka panjang).
- **Arsip & Pencarian Riwayat**: Penyimpanan SQLite terstruktur (`data/state.db`) dengan kemampuan filter tanggal 14 hari ke belakang, filter kategori (Insiden Spesifik vs Edukasi/Evergreen), dan pencarian instan.
- **Distribusi Notifikasi**: Pengiriman otomatis format intelijen ringkas ke kanal Telegram dan visualisasi interaktif di dashboard Web Flask.

## Brand Commitments

- **Nama**: SiberHarian (NOTIFIKASI-BERITA)
- **Identitas Visual**: Bersih, presisi, bernuansa intelijen profesional (palet biru Google `#2563eb`, latar slate terang `#f8fafc`, kartu putih bersih dengan batas halus, serta kode warna tingkat risiko terstandar).
- **Gaya Bahasa**: Bahasa Indonesia profesional Cyber Threat Intelligence, lugas, padat, obyektif, dan berorientasi tindakan mitigasi.

## Evidence on Hand

- Database SQLite aktif di `data/state.db` menyimpan riwayat artikel berita, skor keparahan, CVE, kata kunci tren, dan ringkasan harian.
- Log pemrosesan harian di direktori `logs/`.
- File dataset perbandingan kualitas ringkasan dan klasifikasi relevansi di direktori `data/`.
- Frontend dashboard web aktif di `src/web/` dengan template Flask Jinja2, Tailwind CSS, Alpine.js, dan Chart.js.

## Product Principles

1. **Aksi Preventif di Atas Reaktif**: Seluruh analisis dan prediksi difokuskan untuk memberikan langkah mitigasi sebelum ancaman mengeksploitasi website atau sistem instansi.
2. **Kedaulatan & Keamanan Data (Local First)**: Pemrosesan AI dan penyimpanan data berjalan lokal di server tanpa kebocoran data intelijen ke layanan eksternal.
3. **Fakta & Data Akurat**: Narasi analisis dan rekomendasi hanya bertumpu pada data kejadian nyata dan statistik terverifikasi tanpa halusinasi atau asumsi berlebihan.
4. **Cepat & Terstruktur**: Informasi disajikan dalam hirarki visual yang jelas, ringkas, dan mudah dipahami dalam hitungan detik oleh analis maupun pimpinan.

## Accessibility & Inclusion

- Dukungan kontras teks tinggi dan tipografi jelas (Inter & JetBrains Mono) untuk kenyamanan pemantauan jangka panjang di Security Operations Center (SOC).
- Desain responsif ramah layar lebar (desktop/monitor SOC) maupun tablet dan smartphone.
