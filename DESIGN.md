---
name: SiberHarian
description: Cyber Threat Intelligence & Vulnerability Analytics Platform (Diskominfo Jawa Timur)
colors:
  primary: "#2563eb"
  primary-hover: "#1d4ed8"
  primary-light: "rgba(37, 99, 235, 0.12)"
  surface: "#ffffff"
  surface-card: "#ffffff"
  background: "#f8fafc"
  on-surface: "#0f172a"
  on-surface-variant: "#64748b"
  outline: "#e2e8f0"
  outline-hover: "#cbd5e1"
  critical: "#dc2626"
  warning: "#d97706"
  success: "#059669"
  shadow-dark: "rgba(0, 0, 0, 0.08)"
  shadow-light: "rgba(0, 0, 0, 0.04)"
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
    fontSize: "0.875rem"
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
    backgroundColor: "#2563eb"
    textColor: "#ffffff"
    rounded: "{rounded.md}"
    padding: "10px 20px"
  button-secondary:
    backgroundColor: "#1e293b"
    textColor: "#e2e8f0"
    rounded: "{rounded.md}"
    padding: "10px 18px"
  badge-critical:
    backgroundColor: "rgba(239, 68, 68, 0.1)"
    textColor: "#f87171"
    borderColor: "rgba(239, 68, 68, 0.2)"
    rounded: "{rounded.sm}"
  badge-info:
    backgroundColor: "rgba(37, 99, 235, 0.1)"
    textColor: "#60a5fa"
    borderColor: "rgba(37, 99, 235, 0.2)"
    rounded: "{rounded.sm}"
  badge-warning:
    backgroundColor: "rgba(245, 158, 11, 0.1)"
    textColor: "#fbbf24"
    borderColor: "rgba(245, 158, 11, 0.2)"
    rounded: "{rounded.sm}"
  card-default:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.outline}"
    textColor: "{colors.on-surface}"
    rounded: "{rounded.lg}"
    padding: "24px"
---

# Design System: Diskominfo Sentinel Enterprise

## Overview

**Creative North Star: "Clean Enterprise Cyber Threat Intelligence & Vulnerability Analytics"**

SiberHarian menghadirkan antarmuka platform analitik intelijen ancaman siber (CTI) yang bersih, profesional, elegan, dan berwibawa (*high-trust enterprise platform*), cocok untuk operasional CSIRT / Diskominfo Provinsi Jawa Timur tanpa ornamen robotik berlebihan.

**Key Design Pillars:**
- **Refined Dark Slate Canvas (`#0b0f19`)**: Latar belakang bernuansa deep charcoal slate yang nyaman di mata untuk pemantauan jangka panjang.
- **Clean Surface Hierarchy (`#111827` cards with `#1e293b` borders)**: Kartu analitik dengan batas kontur 1px halus dan rounded corners 16px.
- **Trustworthy Sapphire Blue Accent (`#2563eb` / `#3b82f6`)**: Aksen primer profesional untuk aksi utama, tab aktif, dan visual navigasi.
- **Natural Human Copywriting**: Seluruh label tombol dan status menggunakan teks bersih berbahasa Indonesia yang jelas tanpa tanda kurung siku robotik (`Jalankan Pipeline`, `Ekspor Laporan PDF`, `Selengkapnya →`).
- **Targeted Monospace Usage**: Font `JetBrains Mono` digunakan secara terarah hanya untuk data teknis (kode CVE ID, skor CVSS, timestamp, persentase data, dan log terminal), sedangkan semua heading dan teks konten menggunakan font `Inter`.

---

## Semantic Color Palette

### Base Surfaces
- **Canvas / Background**: `#0b0f19` (Deep Charcoal Slate)
- **Card Surfaces**: `#111827` (Slate 900)
- **Card Border**: `#1e293b` (Slate 800), hover `#334155` (Slate 700)
- **Text Heading**: `#ffffff` (Pure White)
- **Text Body**: `#94a3b8` / `#cbd5e1` (Slate 400 / Slate 300)
- **Text Muted**: `#64748b` (Slate 500)

### Severity Signals
- **Critical / Insiden Riil**: `bg-red-500/10 text-red-400 border border-red-500/20`
- **Edukasi / Evergreen / Info**: `bg-blue-500/10 text-blue-400 border border-blue-500/20`
- **Warning / High CVE**: `bg-amber-500/10 text-amber-400 border border-amber-500/20`
- **Live Feed Active**: `bg-slate-800 text-slate-300` dengan pulse `bg-emerald-500`

---

## Layout & Components

### Hero Section
- Header bersih dengan logo instansi Garuda / SiberHarian berwibawa.
- Telemetry pill: `Pemantauan Intelijen Ancaman Siber Aktif` dengan status dot hijau emerald.
- Action Bar: Tombol solid `Jalankan Pipeline` (`bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-sm`), tombol `Batalkan` (merah halus), dan toggle `Buka/Tutup Monitor`.

### Telemetry KPI Cards
- 4 kartu metrik utama di tab Tren (`Total Insiden Berita`, `Total Kerentanan CVE`, `Rata-Rata Skor CVSS`, `Topik & Vendor Utama`).
- Ikon fungsional dalam wadah membulat dengan aksen warna semantik.
- Nilai angka tegas dan bersih dengan badge pertumbuhan persentase.

### Threat Intelligence & CVE Feed Cards
- Kartu berita dan CVE berukuran 3 kolom responsif.
- Kategori badge di sudut kiri atas, sumber/vendor di kanan atas.
- Link aksi: `Selengkapnya →` untuk ringkasan lengkap dan `Baca sumber asli` / `Detail NVD` untuk tautan eksternal.

### Charts & Data Visualizations
- 7 grafik analitik interaktif berbasis Chart.js dengan garis kisi-kisi abu-abu halus (`rgba(148, 163, 184, 0.1)`), tooltip modern dark slate (`#0f172a`), dan palet warna analitik seimbang.
- Tabel Kata Kunci dan Vendor CVE dengan baris hover halus dan badge pertumbuhan data.
