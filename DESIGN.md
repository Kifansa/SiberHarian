---
name: SiberHarian
description: Cyber Threat Intelligence & Vulnerability Analytics Platform (Diskominfo Jawa Timur) - Sapphire Oceanic Edition
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
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "20px"
  2xl: "24px"
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

# Design System: Sapphire Oceanic Edition (SiberHarian)

## Overview

**Creative North Star: "Sapphire Oceanic - High-Trust, Dignified Government Cyber Threat Intelligence"**

SiberHarian menghadirkan antarmuka analitik intelijen ancaman siber (CTI) dengan palet **Sapphire Oceanic** (`#0A4174`) yang berwibawa, dipadukan dengan latar belakang kanvas sejuk (`#EEF4F8`), kartu putih bersih, dan sistem aksen 7 warna referensi (`#001D39`, `#0A4174`, `#49769F`, `#4E8EA2`, `#6EA2B3`, `#7BBDE8`, `#BDD8E9`). Palet ini menghapus seluruh nuansa kecokelatan/kopi (coffee tone) dan tetap bebas dari glare dingin maupun neon elektrik yang menyilaukan.

**Key Design Pillars:**
- **Clean Oceanic Canvas (`#EEF4F8`)**: Latar belakang sejuk dan bersih yang nyaman di mata untuk pemantauan harian.
- **Deep Midnight Navy Text (`#001D39`)**: Tipografi tajam berkontras tinggi (rasio kontras > 14:1) dengan warna teks navy gelap alami.
- **Subheadings & Borders Slate Blue (`#49769F` & `#BDD8E9`)**: Hirarki teks pendukung dan garis batas kartu yang terstruktur rapi.
- **Sapphire Primary Action (`#0A4174`, hover `#001D39`)**: Tombol eksekusi utama, status terpilih, dan aksen visual berwibawa.
- **Deep Midnight Navy Console (`#001D39`, border `#0A4174`)**: Area log terminal pipeline dengan latar belakang midnight navy pekat dan teks kode tajam.
- **Grounded Semantic Accents**:
  - *Brick Red (`#b91c1c`)*: Insiden kritis, tombol pembatalan, dan lonjakan vendor CVE.
  - *Honey Amber / Ochre (`#b45309`)*: Skor CVSS tinggi dan peringatan mitigasi taktis.
  - *Warm Forest / Green (`#15803d`)*: Validasi sukses, status radar aktif, dan pertumbuhan insiden.
  - *Ocean Teal / Sky (`#4E8EA2` / `#7BBDE8`)*: Garis tren grafik, indikator aktif, dan aksen data.
- **Natural Human Copywriting**: Seluruh label tombol dan status menggunakan teks bersih berbahasa Indonesia yang jelas (`Jalankan Pipeline`, `Ekspor Laporan PDF Resmi`, `Selengkapnya →`).
- **Targeted Monospace Usage**: Font `JetBrains Mono` digunakan secara terarah hanya untuk data teknis (kode CVE ID, skor CVSS, timestamp, persentase data, dan log terminal), sedangkan semua heading dan teks konten menggunakan font `Inter`.

---

## Semantic Color Palette

### Base Surfaces
- **Canvas / Background**: `#EEF4F8` (Clean Oceanic Light Gray-Blue)
- **Subtle Surface**: `#EEF5FA` (Subtle Ice Blue Tint)
- **Card Surfaces**: `#ffffff` (Pure White Card)
- **Card Border**: `#E2EDF8` (Subtle Outline Border), hover `#BDD8E9` (Ice Blue Border)
- **Text Heading**: `#001D39` (Deep Midnight Navy)
- **Text Body**: `#334155` / `#475569` (Slate 700 / Slate 600)
- **Text Muted / Subtitle**: `#49769F` (Slate Blue / Denim)

### Severity Signals
- **Critical / Insiden Riil**: `bg-red-50 text-[#b91c1c] border border-red-200`
- **Edukasi / Evergreen / Info**: `bg-[#EEF5FA] text-[#0A4174] border border-[#BDD8E9]`
- **Warning / High CVE**: `bg-amber-50 text-[#b45309] border border-amber-200`
- **Live Feed Active**: `bg-[#EEF5FA] text-[#0A4174] border border-[#BDD8E9]` dengan pulse `bg-[#15803d]`

---

## Layout & Components

### Hero Section
- Header bersih dengan logo instansi Diskominfo Jatim / SiberHarian berwibawa.
- Action Bar: Tombol solid `Jalankan Pipeline` (`bg-[#0A4174] hover:bg-[#001D39] text-white font-bold rounded-full shadow-md shadow-[#0A4174]/20`), tombol `Batalkan` (`bg-[#b91c1c] hover:bg-[#991b1b] text-white rounded-full font-bold`), dan toggle `Buka/Tutup Monitor` (`bg-white hover:bg-[#EEF5FA] text-[#0A4174] border border-[#BDD8E9] rounded-full`).

### Telemetry KPI Cards
- Kartu metrik utama di tab Tren (`Fokus Ancaman Teratas`, `Total Berita Insiden`, `Total Kerentanan CVE`).
- Ikon fungsional dalam wadah membulat dengan aksen warna semantik hangat (`#0A4174`, `#4E8EA2`, `#b91c1c`, `#b45309`).
- Nilai angka tegas dan bersih dengan badge pertumbuhan persentase.

### Threat Intelligence & CVE Feed Cards
- Kartu berita dan CVE berukuran 3 kolom responsif dengan border bersih (`#E2EDF8`) dan hover border (`#7BBDE8`/60).
- Kategori badge di sudut kiri atas, sumber/vendor di kanan atas.
- Link aksi: `Selengkapnya →` dengan warna `#0A4174` untuk ringkasan modal lengkap dan `Baca sumber asli` / `Detail NVD` untuk tautan eksternal.

### Regional Cyber Incident Highlights (7 Hari Terakhir)
- Visualisasi 3 kolom responsif memetakan kasus insiden siber teramai: **Internasional**, **Nasional**, dan **Jawa Timur**.
- Jawa Timur dilengkapi pendeteksian otomatis kabupaten/kota serta instansi Pemprov/BUMD. Jika tidak ada insiden dalam 7 hari terakhir, menampilkan tanda **`-`** (Kondisi Kondusif / Nihil Kasus) secara tegas dan rapi.
- Perhitungan berbasis klastering frekuensi liputan media (RapidFuzz token matching) tanpa LLM/Ollama untuk latensi sub-10ms dan akurasi 100% bebas halusinasi.

### Charts & Data Visualizations
- Grafik analitik interaktif berbasis Chart.js dengan garis kisi-kisi abu-abu halus (`#E2EDF8`), tick abu-abu slate (`#49769F`), tooltip midnight navy pekat (`#001D39`), dan palet warna solid analitik seimbang tanpa efek kaca/transparansi berlebihan.
- Tabel Kata Kunci dan Vendor CVE dengan baris hover halus (`hover:bg-[#EEF5FA]/60`) dan badge pertumbuhan data.
