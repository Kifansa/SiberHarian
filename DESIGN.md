---
name: SiberHarian
description: Cyber Threat Intelligence & Vulnerability Analytics Platform (CSIRT Diskominfo Jawa Timur) - Sapphire Oceanic Edition
colors:
  # The 7 Reference Palette Colors:
  ref-navy: "#001D39"      # 1. Midnight Navy (Headings, primary hero dark card, primary chart bars)
  ref-sapphire: "#0A4174"  # 2. Dark Sapphire / Royal Navy (Primary action buttons, hero gradient end)
  ref-slate: "#49769F"     # 3. Slate Blue / Denim (Subheadings, inactive states, borders)
  ref-teal: "#4E8EA2"      # 4. Ocean Teal (Line curves, radar strokes, active highlights)
  ref-seafoam: "#6EA2B3"   # 5. Soft Cyan / Seafoam (Secondary chart bars, accents)
  ref-sky: "#7BBDE8"       # 6. Sky Blue (Active navigation pills, glowing chart peaks, primary highlights)
  ref-ice: "#BDD8E9"       # 7. Ice Blue (Badge surfaces, subtle borders, soft pills, light tints)

  # Semantic Mappings:
  primary: "#0A4174"
  primary-hover: "#001D39"
  primary-light: "#EEF5FA"
  primary-accent: "#7BBDE8"
  surface: "#ffffff"
  surface-subtle: "#EEF5FA"
  surface-card: "#ffffff"
  background: "#EEF4F8"
  on-surface: "#001D39"
  on-surface-variant: "#49769F"
  outline: "#E2EDF8"
  outline-hover: "#BDD8E9"
  outline-border: "#BDD8E9"
  critical: "#b91c1c"
  warning: "#b45309"
  success: "#15803d"
  shadow-dark: "rgba(0, 29, 57, 0.06)"
  shadow-light: "rgba(0, 29, 57, 0.02)"
typography:
  display:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "clamp(1.875rem, 4vw, 2.75rem)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "-0.01em"
  body:
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, sans-serif"
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "normal"
  label:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.01em"
  caption:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.6875rem"
    fontWeight: 600
    lineHeight: 1.4
  mono:
    fontFamily: "JetBrains Mono, monospace"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
  icon:
    fontFamily: "Material Symbols Outlined"
    fontSize: "1.25rem"
rounded:
  xs: "2px"
  sm: "4px"
  md: "6px"
  lg: "8px"
  xl: "12px"
  2xl: "16px"
  full: "9999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
  gutter: "24px"
components:
  button-primary:
    backgroundColor: "#0A4174"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 20px"
  button-secondary:
    backgroundColor: "#ffffff"
    textColor: "#001D39"
    borderColor: "#BDD8E9"
    rounded: "{rounded.md}"
    padding: "10px 18px"
  badge-critical:
    backgroundColor: "#fee2e2"
    textColor: "#b91c1c"
    borderColor: "#fecaca"
    rounded: "{rounded.sm}"
  badge-info:
    backgroundColor: "#EEF5FA"
    textColor: "#0A4174"
    borderColor: "#BDD8E9"
    rounded: "{rounded.sm}"
  badge-warning:
    backgroundColor: "#fef3c7"
    textColor: "#b45309"
    borderColor: "#fde68a"
    rounded: "{rounded.sm}"
  card-default:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.outline}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "24px"
---

# Design System: Sapphire Oceanic Edition (SiberHarian - CSIRT Jatim)

## Overview

**Creative North Star: "Sapphire Oceanic - High-Trust, Dignified Government Cyber Threat Intelligence & Public Cyber Awareness"**

SiberHarian menghadirkan antarmuka analitik intelijen ancaman siber (CTI) sekaligus portal informasi publik resmi CSIRT Provinsi Jawa Timur (`https://csirt.jatimprov.go.id/`). Menggunakan palet **Sapphire Oceanic** (`#0A4174`), kanvas sejuk (`#EEF4F8`), kartu putih bersih, dan aksen 7 warna referensi (`#001D39`, `#0A4174`, `#49769F`, `#4E8EA2`, `#6EA2B3`, `#7BBDE8`, `#BDD8E9`).

Desain ini melayani **Dua Persona Pengguna (Dual-User Experience)**:
1. **Mode Publik (Masyarakat Umum & Pengelola OPD)**: Antarmuka bersih, informatif, dan edukatif tanpa tombol teknis backend.
2. **Mode Admin CTI (Tim CSIRT Diskominfo Jatim)**: Konsol operasional SOC lengkap dengan monitor terminal pipeline real-time dan analisis intelijen strategis.

---

## Key Design Pillars

1. **Clean Oceanic Canvas (`#EEF4F8`)**: Latar belakang sejuk, tenang, dan profesional yang nyaman untuk penjelajahan publik maupun pemantauan intensif di SOC.
2. **Deep Midnight Navy Text (`#001D39`)**: Tipografi tajam berkontras tinggi (rasio kontras > 14:1) dengan warna teks navy gelap alami, bebas dari efek lelah mata.
3. **Sapphire Primary Action (`#0A4174`, hover `#001D39`)**: Aksen biru berwibawa khas identitas Pemprov Jawa Timur untuk tombol aksi utama dan status terpilih.
4. **Natural Human Copywriting**: Seluruh teks, label, dan grafik menggunakan bahasa Indonesia baku, jelas, dan lugas. Menghilangkan seluruh AI-slop buzzwords (*unlock, elevate, revolutionize, seamless*).
5. **Targeted Monospace Usage**: Font `JetBrains Mono` digunakan secara disiplin hanya untuk data teknis numerik (kode CVE ID, skor CVSS, persentase, tanggal teknis, dan terminal log). Teks judul dan narasi menggunakan font `Inter`.

---

## Dual-Role Navigation Architecture

### Header Role Switcher
Terletak di sisi kanan header portal, memberikan toggle halus dan jelas:
- **Mode Publik (2 Tab Saja)**: Menampilkan tab **Berita & Statistik** (gabungan wawasan KPI, Word Cloud, grafik fakta, intisari edukasi asli, dan feed berita) serta **Arsip**.
- **Mode Admin CTI (3 Tab)**: Menampilkan tab **Dashboard** (operasional + floating console terminal SSE), **Arsip**, dan **Tren CTI**. Badge identitas `"Tim CTI CSIRT"` ditampilkan di samping logo.

### Desktop & Mobile Navigation
- **Desktop**: Segmented navigation pill control (`#EEF4F8` container dengan border `#BDD8E9`). Tab aktif disorot dengan warna `#7BBDE8` (Sky Blue) dengan teks putih tegas.
- **Mobile**: Fixed bottom navigation bar (`bg-white` dengan border-t `#BDD8E9`) yang dinamis menyesuaikan 2 tab untuk Publik dan 3 tab untuk Admin CTI.

---

## Surface Specifications

### 1. Tab Beranda & Statistik (Sisi Publik)
Menggabungkan wawasan intelijen dan berita hari terakhir dalam satu alur yang kohesif:
- **Insightful KPI Cards**: 4 kartu wawasan fakta bermakna (*Modus Paling Mengintai: Akun & Phishing 54%*, *Status Risiko Software: Kritis Ekstrem 9.5/10*, *Software Terbanyak Celah: Microsoft & Web CMS*, *Fokus Wilayah: 60% Isu Nasional*).
- **Word Cloud Kasus Insiden Spesifik (Interaktif)**: Diekstrak eksklusif dari berita `insiden_spesifik`. Ukuran font dinamis (12px–26px) dengan palet Sapphire Oceanic. Mengklik kata kunci akan langsung memfilter kartu berita kejadian terkait di bawahnya.
- **Grafik Fakta Empiris**: Bar chart sebaran modus ancaman dan horizontal bar chart software populer terpapar celah kritis.
- **Intisari Artikel Edukasi Asli**: Daftar himbauan pencegahan yang disarikan langsung dari artikel edukasi siber terverifikasi di database (`kategori_relevansi == 'analisis_relevan'`) lengkap dengan link ke sumber berita asli.
- **Feed Berita & CVE Hari Terakhir**: Kartu berita dan CVE terkini dengan modal pop-up pembaca ringkasan lengkap.

### 2. Tab Arsip (Publik & Admin)
- Penelusuran data 7-14 hari dengan dropdown tanggal, filter kategori (Insiden Spesifik, Edukasi, CVE), dan kotak pencarian instan (*live search*).

### 3. Tab Tren Siber CTI (Khusus Admin Tim CTI)
- **Komparatif Mingguan**: Analisis rolling 7 hari aktif vs 7 hari baseline untuk mengukur eskalasi ancaman siber secara matematis.
- **SITREP CTI 5-Bagian Terstruktur**: 
  1. Tren Insiden Mingguan (Makro)
  2. Lanskap & Entitas Ancaman (Mikro - klastering insiden multi-artikel dengan nama kampanye profesional dan mitigasi halusinasi peneliti)
  3. Vektor Serangan & Pemetaan MITRE ATT&CK (1-to-1)
  4. Rekomendasi Aksi Preskriptif (Injeksi deterministik dari Ensiklopedia Keamanan)
  5. Prediksi & Sinyal Ancaman Masa Depan (Emerging Threats)
- **Taksonomi Terstandarisasi**:
  - **10 Sektor Standar Nasional**: Mengacu pada Perpres No. 82 Tahun 2022 tentang Infrastruktur Informasi Vital (IIV) + Sektor Pendidikan & Pengguna Digital.
  - **12 Taktik MITRE ATT&CK Enterprise Matrix**: Initial Access, Execution, Persistence, Privilege Escalation, Defense Evasion, Credential Access, Discovery, Lateral Movement, Collection, Command & Control, Exfiltration, Impact.
- **Kasus Wilayah 3-Level (Internasional, Nasional, Jawa Timur)**: Visualisasi kartu insiden teramai dengan deteksi cerdas 29 kabupaten dan 9 kota di Jawa Timur.
- **Matriks Mitigasi Proteksi Web & Sistem**: Rekomendasi teknis langsung untuk pengamanan portal instansi publik.
- **Ekspor Dokumen PDF Resmi**: Cetak dokumen SITREP mingguan bertata letak standar Diskominfo Jatim langsung dari peramban.

### 4. Pusat Ensiklopedia Standar Keamanan Siber
- Database 12 kerangka kerja global dan nasional (165 entitas) tersimpan terstruktur dalam format JSON di `data/encyclopedia/`:
  - Standar Global: MITRE ATT&CK, MITRE D3FEND, NIST CSF 2.0, OWASP Top 10, CWE, CIS Controls, CISA CPG, ISO/IEC 27001, Cloud Security Alliance (CSA) CCM.
  - Standar Nasional: BSSN CSIRT Framework, Indeks KAMI (Keamanan Informasi BSSN), Panduan Operasional CSIRT Indonesia.
- Layanan API `/api/ensiklopedia` dengan filter kerangka kerja dan pencarian instan berbasis kata kunci.

---

## Semantic Color Tokens

- **Canvas Background**: `#EEF4F8`
- **Subtle Surface**: `#EEF5FA`
- **Card Surface**: `#ffffff`
- **Card Border**: `#E2EDF8`, hover: `#BDD8E9`
- **Navy Heading**: `#001D39`
- **Slate Text**: `#49769F`
- **Body Text**: `#334155`
- **Sapphire Primary**: `#0A4174`
- **Sky Active Pill**: `#7BBDE8`
- **Semantic Accents**:
  - *Critical / Darurat*: `#b91c1c` (Red 700)
  - *Warning / Perhatian*: `#b45309` (Amber 700)
  - *Success / Aman*: `#15803d` (Green 700)
  - *Teal Data Line*: `#4E8EA2`
