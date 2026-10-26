---
name: SiberHarian
description: Cyber Threat Intelligence & Incident Analytics Platform (CSIRT Diskominfo Jawa Timur) - Cyber-HUD / Tactical Dark Terminal Edition
colors:
  # The Cyber-HUD Reference Palette Colors:
  bg-primary: "#0a1628"      # 1. Dark Tactical Navy Canvas (Main background)
  bg-secondary: "#0d2137"    # 2. Elevated Dark Surface (Navbar, headers, toolbars, card tracks)
  bg-card: "rgba(17,34,64,0.7)" # 3. Glassmorphic HUD Surface (Blur 8px, border #1a3a5c)
  bg-terminal: "#070f1c"    # 4. Code & Log Terminal Body
  accent-cyan: "#00d4ff"     # 5. Primary Interactive Cyan (Buttons, borders, totals, active lines)
  accent-teal: "#00ff88"     # 6. Vibrant Teal (Progress gradients, success)
  accent-neon: "#00ff9d"     # 7. Neon Green (Status pulses, active tags [ ... ], live indicators)
  accent-red: "#ff3366"      # 8. Hazard Red (Critical threats, CVE watch, active date tabs < ... >)
  accent-amber: "#ffc107"    # 9. Warning Amber (Medium alerts, viewer badges)
  accent-orange: "#ff8800"   # 10. Education / Outreach Orange
  accent-purple: "#a78bfa"   # 11. Advisory Purple
  border-base: "#1a3a5c"     # 12. Tactical Grid & Border Line
  text-primary: "#e0f0ff"    # 13. High-Contrast White-Cyan (WCAG AAA)
  text-secondary: "#8892b0"  # 14. Monospace Slate Label (WCAG AA)
  text-muted: "#7d8ca6"      # 15. Meta Footers & Captions

  # Semantic Mappings:
  primary: "#00d4ff"
  primary-hover: "#33ddff"
  primary-light: "rgba(0, 212, 255, 0.12)"
  primary-accent: "#00ff88"
  surface: "rgba(17, 34, 64, 0.7)"
  surface-subtle: "#0d2137"
  surface-card: "rgba(17, 34, 64, 0.7)"
  background: "#0a1628"
  on-surface: "#e0f0ff"
  on-surface-variant: "#8892b0"
  outline: "#1a3a5c"
  outline-hover: "#00d4ff"
  outline-border: "#1a3a5c"
  critical: "#ff3366"
  warning: "#ffc107"
  success: "#00ff9d"
  shadow-dark: "rgba(0, 0, 0, 0.5)"
  shadow-glow: "rgba(0, 212, 255, 0.25)"
typography:
  display:
    fontFamily: "'Sora', sans-serif"
    fontSize: "clamp(1.875rem, 4vw, 2.75rem)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.025em"
  headline:
    fontFamily: "'Sora', sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: "-0.02em"
  title:
    fontFamily: "'Sora', sans-serif"
    fontSize: "1.125rem"
    fontWeight: 700
    lineHeight: 1.4
    letterSpacing: "-0.01em"
  body:
    fontFamily: "'Sora', sans-serif"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: "normal"
  label:
    fontFamily: "'Fragment Mono', 'Share Tech Mono', monospace"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: "0.05em"
  caption:
    fontFamily: "'Fragment Mono', 'Share Tech Mono', monospace"
    fontSize: "0.6875rem"
    fontWeight: 500
    lineHeight: 1.4
  mono:
    fontFamily: "'Fragment Mono', 'Share Tech Mono', monospace"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
  icon:
    fontFamily: "Material Symbols Outlined"
    fontSize: "1.25rem"
rounded:
  chamfer: "10px"
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
    backgroundColor: "rgba(0, 212, 255, 0.12)"
    borderColor: "#00d4ff"
    textColor: "#ffffff"
    shape: "clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)"
    fontFamily: "'Fragment Mono', monospace"
    padding: "10px 20px"
  button-secondary:
    backgroundColor: "rgba(255, 255, 255, 0.05)"
    borderColor: "#1a3a5c"
    textColor: "#e0f0ff"
    shape: "clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)"
    fontFamily: "'Fragment Mono', monospace"
    padding: "10px 18px"
  badge-critical:
    backgroundColor: "rgba(255, 51, 102, 0.15)"
    textColor: "#ff3366"
    borderColor: "rgba(255, 51, 102, 0.4)"
    rounded: "{rounded.sm}"
  badge-info:
    backgroundColor: "rgba(0, 212, 255, 0.12)"
    textColor: "#00d4ff"
    borderColor: "rgba(0, 212, 255, 0.3)"
    rounded: "{rounded.sm}"
  badge-success:
    backgroundColor: "rgba(0, 255, 157, 0.15)"
    textColor: "#00ff9d"
    borderColor: "rgba(0, 255, 157, 0.4)"
    rounded: "{rounded.sm}"
  card-default:
    backgroundColor: "rgba(17, 34, 64, 0.7)"
    borderColor: "#1a3a5c"
    textColor: "#e0f0ff"
    backdropFilter: "blur(8px)"
    rounded: "{rounded.xl}"
    padding: "24px"
---

# Design System: Cyber-HUD / Tactical Dark Terminal Edition (CSIRT Jatim)

## Overview

**Creative North Star: "Cyber-HUD / Tactical Dark Terminal - Unified Official Visual Experience with CSIRT Provinsi Jawa Timur (`https://csirt.jatimprov.go.id/`)"**

SiberHarian menghadirkan antarmuka analitik intelijen ancaman siber (CTI) sekaligus portal informasi publik resmi CSIRT Provinsi Jawa Timur. Menggunakan tema **Cyber-HUD / Tactical Dark Terminal** dengan kanvas taktis gelap (`#0a1628`), permukaan sekunder `#0d2137`, kartu kaca semi-transparan `rgba(17,34,64,0.7)` dengan `backdrop-filter: blur(8px)`, aksen pendar neon (`#00d4ff`, `#00ff88`, `#00ff9d`, `#ff3366`), tipografi terstandarisasi (`Sora` dan `Fragment Mono`), serta sudut pemotongan diagonal 10px (*chamfered clip-path*).

Desain ini melayani **Dua Persona Pengguna (Dual-User Experience)**:
1. **Mode Publik (Masyarakat Umum & Pengelola OPD)**: Antarmuka komando siber yang bersih, informatif, dan edukatif dengan visualisasi data ramah publik tanpa tombol operasional backend.
2. **Mode Admin CTI (Tim CSIRT Diskominfo Jatim)**: Konsol operasional SOC lengkap dengan monitor terminal pipeline real-time, 4 scorecards KPI bercahaya, 3 kolom kasus wilayah, radar CVE, dan analisis intelijen strategis.

---

## Key Design Pillars

1. **Tactical Dark Canvas (`#0a1628`) & Ambient Cyber Grid**: Latar belakang dark navy pekat dengan grid ambient 40px `.cyber-grid-ambient` yang menciptakan kedalaman visual command center modern.
2. **High-Contrast Reading Typography (`#e0f0ff` on `#0a1628`)**: Rasio kontras tinggi (**15.6 : 1**) melampaui standar WCAG AAA, menjamin keterbacaan artikel dan data teknis dalam sesi analisis panjang.
3. **Chamfer Cut 10px Interactive Elements**: Seluruh tombol utama dan tab aksi mengadopsi sudut potong diagonal chamfered:
   `clip-path: polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)`.
4. **Brackets & Monospace Notation (`Fragment Mono`)**: Penggunaan kurung siku `[ ... ]` untuk label modul dan `< ... >` untuk filter navigasi tanggal arsip, mempertegas estetika instrumen telemetri siber profesional.
5. **Horizontal Pill Progress Bars (`Chart.js`)**: Visualisasi frekuensi serangan dan sektor vital menggunakan horizontal pill bars (`indexAxis: 'y'`) dengan gradasi neon cyan-ke-teal (`#00d4ff` &rarr; `#00ff88`) di atas track gelap `#0d2137`.

---

## Dual-Role Navigation Architecture

### Header Navigation Bar
- **Sticky Navbar (70px)**: Background `#0a1628`/95 dengan `backdrop-filter: blur(12px)` dan border bawah tipis `#1a3a5c`.
- **Identitas Logo CSIRT**: Logo perisai Pemprov Jatim berlatar glow cyan `#00d4ff`, dengan teks judul `SiberHarian` dan sub-label `[ CSIRT PROVINSI JAWA TIMUR ]`.
- **Mode Publik**: Tab `[ BERANDA // STATISTIK ]` dan `[ ARSIP RIWAYAT ]`.
- **Mode Admin CTI**: Tab `[ TREN SIBER // CTI ]`, `[ ARSIP RIWAYAT ]`, dan `[ PENGATURAN ]`.

### Mobile Navigation HUD
- Bottom bar mengambang dengan latar `#0d2137`/95, border `#1a3a5c`, dan ikon navigasi ramah jempol.

---

## Surface Specifications

### 1. Tab Beranda & Statistik (Sisi Publik)
- **Hero Command Center**: Header taktis dengan status aktif `● [ CSIRT PROVINSI JAWA TIMUR ]` berdenyut, headline display, dan 2 tombol chamfered.
- **Kartu KPI Paling Mengintai**: Kartu sorotan visual dengan status `[ WASPADA ]` neon amber dan metrik persentase tajam.
- **Word Cloud Kasus Insiden Interaktif**: Kumpulan kata kunci berbasis frekuensi dengan pendar neon cyan, teal, dan purple yang langsung menyaring feed berita saat diklik.
- **Infografis 3 Langkah Anatomi Serangan**: Kartu edukasi visual langkah mitigasi dengan nomor langkah chamfered.
- **Horizontal Pill Bar Chart**: Visualisasi sebaran modus ancaman dan sektor vital IIV.
- **Feed Berita Intelijen**: Kartu berita glassmorphic dengan tag wilayah (`[ JAWA TIMUR ]`, `[ NASIONAL ]`, `[ GLOBAL ]`), ringkasan terstruktur, dan pop-up modal detail.

### 2. Tab Arsip (Publik & Admin)
- **Header Modul**: `[ ARSIP // 02 ]` dengan deskripsi riwayat data intelijen.
- **Tab Tanggal Cepat HUD**: Format `< HARI INI >`, `< 7 HARI >`, `< 14 HARI >`, `< 30 HARI >` dengan border merah `#ff3366` saat aktif.
- **Toolbar Taktis Terpadu**: Select dropdown kategori dan live search bar monospace dark `#0d2137`.

### 3. Tab Tren Siber CTI (Admin Tim CTI)
- **Executive KPI Scorecards (4 Kartu)**: Indeks Postur Risiko, Total Insiden Terpantau, Sektor Vital Terdampak, dan Rasio Isu Wilayah dengan metrik glowing `Fragment Mono`.
- **Kasus Wilayah 3-Level**: Kolom Internasional, Nasional, dan Jawa Timur berlatar dark cyber dengan tombol aksi modal `[ DETAIL ANALISIS → ]`.
- **AI SITREP Executive Digest**: Kartu ringkasan intelijen mingguan dengan rekomendasi aksi preskriptif dan ekspor PDF resmi.
- **3 Chart Horizontal Pill**: Sebaran TTPs Serangan, 10 Sektor Vital IIV (Perpres No. 82/2022), dan Pemetaan 12 Taktik MITRE ATT&CK.
- **Radar CVE Watchlist & Matriks Tindakan Taktis**: Tabel dark cyber dengan CVE ID tautan NVD dan checklist mitigasi SOC.

### 4. Modul Login & Pengaturan
- **Otentikasi Petugas Tim CTI (`login.html`)**: Halaman taktis dengan kartu semi-transparan `rgba(17,34,64,0.85)`, border neon atas, dan tombol chamfer `[ MASUK KE SISTEM CTI → ]`.
- **Panel Pengaturan (`_settings.html`)**: 4 tab konfigurasi (`[ UMUM & LLM ]`, `[ TEMPLATE PROMPT LLM ]`, `[ SUMBER RSS ]`, `[ KEAMANAN AKUN ]`) dengan editor prompt terminal `#070f1c` dan tabel manajemen RSS.

---

## Semantic Color Tokens (WCAG AA/AAA Verified)

- **Canvas Background**: `#0a1628`
- **Secondary Surface / Track**: `#0d2137`
- **Card Surface**: `rgba(17, 34, 64, 0.7)` (Blur 8px)
- **Terminal Surface**: `#070f1c`
- **Border**: `#1a3a5c`
- **Primary Text**: `#e0f0ff` (Kontras 15.6:1 - WCAG AAA)
- **Secondary Text**: `#8892b0` (Kontras 5.4:1 - WCAG AA)
- **Cyan Interactive**: `#00d4ff` (Kontras 10.2:1 - WCAG AAA)
- **Teal Progress**: `#00ff88` (Kontras 13.5:1 - WCAG AAA)
- **Neon Status**: `#00ff9d` (Kontras 13.8:1 - WCAG AAA)
- **Hazard Red**: `#ff3366` (Kontras 5.1:1 - WCAG AA)
- **Warning Amber**: `#ffc107` (Kontras 11.2:1 - WCAG AAA)
