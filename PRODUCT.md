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

- **Rutinitas Pemantauan & Analisis**: Pipeline dijalankan secara berkala untuk mengagregasi data berita dan CVE 7 hari terkini, membandingkannya dengan 7 hari baseline sebelumnya, serta menghasilkan analisis ancaman mingguan yang berorientasi tindakan proteksi website.
- **Lingkungan Kerja**: Tim keamanan memantau dashboard web (tab Beranda, Arsip, dan Tren Analisis Mingguan) melalui browser desktop, serta mengekspor Laporan PDF Resmi Mingguan untuk briefing pimpinan dan tim teknis.
- **Tindakan Lanjut Operasional**: Analis membaca rekomendasi mitigasi taktis, matriks tindakan ancaman mingguan, audit kerentanan aset web/CMS, serta checklist proteksi berkala guna mencegah serangan ke website instansi pemerintah.

## Capabilities and Constraints

- **Agregasi Multi-Sumber**: Mengambil berita keamanan siber dari berbagai RSS/feed media nasional & internasional, serta API publik NVD NIST (tanpa dependensi NVD API Key).
- **LLM Lokal On-Premise**: Inferensi AI menggunakan Ollama (model Qwen2.5-Coder / Qwen2.5:7b / Llama) untuk memastikan privasi data dan kedaulatan informasi tanpa ketergantungan API cloud eksternal.
- **Analisis Intelijen Mingguan (Rolling 7 Hari vs 7 Hari Baseline)**: Memetakan lonjakan ancaman, pergeseran postur risiko, vektor serangan TTPs, serta kerentanan software web server & CMS.
- **Matriks Tindakan & Mitigasi Proteksi Website**: Rekomendasi mitigasi bertingkat, matriks aksi mingguan (Ransomware, Defacement, Exploit, Phishing), dan checklist verifikasi keamanan interaktif bagi pengelola web.
- **Arsip & Pencarian Riwayat**: Penyimpanan SQLite terstruktur (`data/state.db`) dengan kemampuan filter tanggal, filter kategori, dan pencarian instan.
- **Distribusi Laporan**: Ekspor dokumen resmi PDF Laporan Intelijen Ancaman Siber Mingguan (Executive Advisory) siap cetak langsung dari dashboard web.

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
