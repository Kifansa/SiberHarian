# Referensi Desain — CSIRT Provinsi Jawa Timur (csirt.jatimprov.go.id)

> **Gaya desain:** *Cyber-HUD / Tactical Dark Terminal* — latar navy gelap, aksen neon cyan & hijau, label monospace berkurung `[ ... ]`, sudut tombol/tab yang "terpotong" (chamfer), kartu semi-transparan, dan glow cyan tipis pada state aktif.
>
> **Revisi 3** — token desain kini bersumber dari **CSS asli situs** (`:root` di `cyber-theme.css?v=61`), bukan lagi tebakan piksel.

---

## 0. Sumber Data & Tingkat Kepercayaan

Website tidak bisa diakses langsung dari lingkungan saya, jadi data berasal dari: 4 screenshot tampilan, 1 screenshot Computed `<body>`, 1 screenshot Computed sebuah item navigasi, dan 3 screenshot panel Styles `:root`.

| Label | Arti |
|---|---|
| 🟢 **CSS asli** | Dibaca langsung dari DevTools situs. **Nilai pasti.** |
| ✅ **Terukur** | Diukur dari piksel screenshot dan **sudah cocok** dengan token CSS asli. |
| 🔵 **Estimasi** | Perkiraan visual (ukuran heading, chamfer, jaguar, dll). Skala screenshot tidak diketahui, jadi selisih ±6–14% terhadap CSS px sangat mungkin (contoh: `--nav-height` asli 70px tampak ±66px di screenshot). |

### Stack teknologi (🟢 disimpulkan dari panel Styles)

- **Bootstrap 5.3** (SCSS, terlihat dari `_root.scss:9` dan variabel `--bs-*`) sebagai dasar.
- **`cyber-theme.css?v=61`** sebagai lapisan tema kustom yang menimpa Bootstrap (`--bg-*`, `--accent-*`, `--text-*`, dst).
- Bootstrap mendefinisikan `--bs-body-color: #212529`, `--bs-body-bg: #fff`, `--bs-body-line-height: 1.5`, tetapi `<body>` **menimpanya** (lihat bagian 4).
- Konsekuensi praktis: container 1320px di layar ≥1400px, breakpoint 576/768/992/1200/1400, utilitas `d-flex`, `gap-*`, dsb. kemungkinan besar tersedia.

### Belum terlihat (mohon ambil jika ingin 100% akurat)

1. Di blok `:root` pertama masih ada **"Show all properties (61 more)"** (sesudah `--sev-kritis`). Klik tombol itu; isinya kemungkinan warna severity lain (`--sev-tinggi`, dst) dan token komponen.
2. **Mode terang:** aturan pengganti variabel (biasanya `[data-theme="light"] { ... }` atau `.light-theme`).
3. Warna **Jaguar** (bagian 2.6) — tidak ada token yang cocok di daftar yang terlihat.
4. Ukuran/berat `h1`, judul kartu, dan teks tombol.

---

## 1. Filosofi & Karakter Visual

| Aspek | Karakter |
|---|---|
| Mood | Siaga, teknis, "command center", tetapi tetap resmi (instansi pemerintah) |
| Tema default | **Dark**; ada toggle tema ☀ di navbar (mode terang belum terdokumentasi) |
| Bahasa visual | HUD/terminal: kurung siku, `//`, uppercase monospace, garis tipis bercahaya |
| Kepadatan | Lega; banyak ruang negatif, kartu dengan padding besar |
| Kontras | Tinggi pada teks utama; teks sekunder sengaja lebih redup |
| Kedalaman | Kartu **semi-transparan** (`rgba` 0.7) + glow cyan, hampir tanpa shadow gelap |
| Bahasa konten | Bahasa Indonesia, kalimat pendek, pola *Blind Spot → Solution* |

**Pola microcopy khas (pertahankan agar konsisten):**
- Navigasi & label: `[ BERANDA ]`, `[ EKOSISTEM ]`
- Judul seksi: `[ ARTIKEL // 03 ]` (penomoran dengan `//`)
- CTA: `[PROFIL LENGKAP →]`, `[🛡 LAPOR INSIDEN]`, `LIHAT DETAIL LAYANAN →`
- Nomor kartu dua digit: `03`, `04`, `05`
- Status: titik hijau + `Terakhir disinkronkan 6 hours ago`
- Tab data: `< DOKUMEN >`, `< CVE >`

---

## 2. Palet Warna (token asli 🟢)

### 2.1 Latar & Permukaan

| Token asli | Nilai | Dipakai untuk |
|---|---|---|
| `--bg-primary` | `#0a1628` | Background `<body>`, halaman, navbar |
| `--bg-secondary` | `#0d2137` | Track bar chart, permukaan sekunder, aksen tab aktif |
| `--bg-card` | `rgba(17, 34, 64, 0.7)` | Kartu (layanan, artikel, statistik, panel chart). Di atas `#0a1628` menghasilkan **`#0F1E39`** ✅ (terukur `#0F1F39`) |
| `--article-surface-hover` | `rgba(19, 39, 70, 0.82)` | Latar kartu artikel saat hover (≈ `#112441`) |

> Karena `--bg-card` transparan, kartu **terlihat sedikit berbeda tergantung latar di belakangnya** (mis. di atas grid/partikel). Tirulah dengan `background: var(--bg-card)`, jangan hex solid, dan opsional tambahkan `backdrop-filter: blur(8px)` 🔵.

### 2.2 Aksen

| Token asli | Hex | Peran |
|---|---|---|
| `--accent-cyan` | `#00d4ff` | Aksen primer: link/nav aktif, border kartu aktif, awal gradient chart, tombol "Lihat Semua", angka total, scroll-top |
| `--accent-teal` | `#00ff88` | Ujung gradient chart, ikon aktif hijau, status sukses |
| `--accent-neon-green` | `#00ff9d` | Judul seksi `[ ARTIKEL // 03 ]`, titik status hijau |
| `--accent-neon-yellow` | `#ccff00` | Aksen kuning-lime (cadangan/highlight khusus) |
| `--accent-purple` | `#7b2fff` | Node partikel hero, aksen sekunder |
| `--accent-red` | `#ff3366` | Tab aktif CVE, tombol Lapor Insiden, alert |
| `--accent-orange` | `#ff8800` | Beruang / tahap Edukasi (lihat 2.6) |

### 2.3 Teks

| Token asli | Hex | Dipakai untuk |
|---|---|---|
| `--text-primary` | `#e0f0ff` | Warna teks dasar `<body>`, judul, angka bar |
| `--text-secondary` | `#8892b0` | Nav idle, label statistik, tab idle, label bulan |
| `--text-muted` | `#7d8ca6` | `BLIND SPOT`, nomor kartu, meta/tanggal, paragraf kartu redup |
| `--text-secondary-filter` | `invert(70%) sepia(11%) saturate(543%) hue-rotate(189deg) brightness(96%) contrast(87%)` | **Filter CSS** untuk mewarnai ikon/gambar hitam agar menjadi warna `--text-secondary` (dipakai ikon idle: Panda, Elang, Serigala) |

### 2.4 Border, Glow & Shadow

| Token asli | Nilai | Dipakai untuk |
|---|---|---|
| `--border` | `#1a3a5c` | Border standar semua kartu/panel/track/divider |
| `--border-glow` | `rgba(0, 212, 255, 0.4)` | Border state aktif/hover |
| `--glow` | `rgba(0, 212, 255, 0.3)` | Warna glow dasar |
| `--glow-strong` | `rgba(0, 212, 255, 0.6)` | Glow kuat (fokus, elemen utama) |
| `--shadow` | `0 4px 30px rgba(0, 0, 0, 0.4)` | Shadow gelap (dropdown/modal) |
| `--shadow-glow` | `0 0 25px rgba(0, 212, 255, 0.25)` | Kartu layanan aktif |
| `--article-border-hover` | `rgba(0, 212, 255, 0.48)` | Border kartu artikel saat hover |
| `--article-shadow-hover` | `0 10px 24px rgba(0, 0, 0, 0.22)` | Shadow kartu artikel saat hover |

### 2.5 Warna Data & Severity

Kartu statistik memakai **variabel Bootstrap 5.3** (🟢 terverifikasi di `_root.scss`) dan aksen tema:

| Data (screenshot) | Angka | Token | Hex |
|---|---|---|---|
| Dokumen IOC | 17 | `--accent-cyan` | `#00d4ff` |
| CVE | 66,178 | `--accent-cyan` | `#00d4ff` |
| Critical/High | 33,457 | `--bs-danger` | `#dc3545` |
| Malware | 1,572 | `--bs-warning` | `#ffc107` |
| Phishing | 53,938 | `--bs-info` | `#0dcaf0` |
| IP Feeds | 3,788 | `--bs-primary` | `#0d6efd` |
| Severity Kritis | — | `--sev-kritis` | `#f45b69` |

Warna Bootstrap lain yang tersedia: `--bs-success #198754`, `--bs-teal #20c997`, `--bs-orange #fd7e14`, `--bs-purple #6f42c1`, `--bs-indigo #6610f2`, `--bs-pink #d63384`, `--bs-gray #6c757d`.

### 2.6 Aksen Ekosistem (per "hewan")

| Tahap | Hewan | Warna aktif | Status |
|---|---|---|---|
| Edukasi | Beruang | `#ff8800` (`--accent-orange`) pada opasitas ≈ 0.85 | ✅ ikon terukur `#DA7805`; `#ff8800` @0.85 di atas kartu = `#DB7809` |
| Patroli | Jaguar | ≈ `#FF6F16` (oranye-kemerahan, lebih merah dari Beruang) | 🔵 terukur `#E1641C` (puncak) — tidak ada token yang cocok; mungkin di 61 properti tersembunyi atau inline |
| Proteksi, Deteksi, Diseminasi | Panda, Elang, Serigala | idle: `--text-secondary` via `--text-secondary-filter` | 🟢 mekanisme; hasil terukur `#8090A8` |

### 2.7 Token Animasi Hero

| Token asli | Nilai | Makna |
|---|---|---|
| `--hero-animation-cyan` | `#00d4ff` | Node/garis jaringan cyan |
| `--hero-animation-shield` | `#42c3e6` | Warna perisai/logo animasi |
| `--hero-animation-teal` | `#00ff88` | Node hijau |
| `--hero-animation-purple` | `#7b2fff` | Node ungu |
| `--hero-animation-red` | `#ff3366` | Node/garis merah (ancaman) |
| `--hero-animation-glow` | `rgba(0, 212, 255, 0.3)` | Halo node |
| `--hero-animation-trail` | `rgba(10, 22, 40, 0.2)` | Warna jejak: kanvas menimpa frame lama dengan `bg` 20% → efek *motion trail* |
| `--hero-animation-fade` | `rgba(0, 0, 0, 1)` | Warna pemudaran tepi |
| `--hero-animation-line-alpha` | `0.2` | Opasitas garis antar node |

### 2.8 Rasio Kontras (WCAG, dihitung)

| Pasangan | Rasio | Status |
|---|---|---|
| `#e0f0ff` di atas `#0a1628` | **15.6 : 1** | AAA |
| `#8892b0` di atas `#0F1E39` (kartu) | **5.4 : 1** | AA |
| `#7d8ca6` di atas `#0F1E39` (kartu) | **4.9 : 1** | AA (teks normal) ✅ |
| `#00d4ff` di atas `#0a1628` | **10.2 : 1** | AAA |
| `#00ff88` / `#00ff9d` di atas `#0a1628` | **13.5 / 13.6 : 1** | AAA |
| `#ff3366` di atas `#0a1628` | **5.1 : 1** | AA |
| `#ff8800` di atas kartu | **6.9 : 1** | AA |
| `#f45b69` di atas kartu | **5.2 : 1** | AA |
| `#ffc107` di atas kartu | **10.1 : 1** | AAA |
| `#dc3545` / `#0d6efd` di atas kartu | **3.6 : 1** | ⚠️ hanya untuk angka besar (≥ 24px bold) |
| `#7b2fff` di atas kartu | **2.9 : 1** | ⚠️ dekoratif saja (node/garis), jangan untuk teks |

> Koreksi dari revisi sebelumnya: `--text-muted` sebelumnya saya tebak `#64748B` (3.5 : 1, gagal AA). Nilai asli `#7d8ca6` lolos AA.

---

## 3. Gradient

Blok `:root` yang terlihat **tidak** mendefinisikan variabel gradient; gradient bar chart dibentuk dari dua token aksen. Nilai di bawah ini **diukur dari piksel** (✅) dan titik ujungnya cocok persis dengan token.

### 3.1 Gradient Bar Chart Utama (✅)

Interpolasi **linear** kiri → kanan, dan **setiap bar punya gradient sendiri** (bukan satu gradient sepanjang track), jadi bar pendek pun berakhir hijau penuh.

```
Start : #00d4ff = var(--accent-cyan)    0%
Mid   : ≈ #00E9C4 (hasil interpolasi)  50%
End   : #00ff88 = var(--accent-teal)  100%
```

```css
--grad-bar: linear-gradient(90deg, var(--accent-cyan) 0%, var(--accent-teal) 100%);
```

Terukur di bar Agustus: `#00D5FF → #00DBED → #00E2D8 → #00EAC3 → #00F2AE → #00F999 → #00FF89`.

### 3.2 Gradient Bulan Berjalan / Data Belum Final (✅)

Bar September memudar dari cyan ke abu-slate (bukan ke hijau) sebagai sinyal "belum lengkap".

```
Start : #00d4ff = var(--accent-cyan)   0%
Mid   : ≈ #38A5C2                     50%
End   : #6E7A87 (slate)              100%
```

```css
--grad-bar-partial: linear-gradient(90deg, var(--accent-cyan) 0%, #6E7A87 100%);
```

Label bulan aktif memakai `--accent-cyan`; bulan lain `--text-secondary`.

### 3.3 Garis Bawah Tab Aktif (🔵)

```css
--grad-tab-underline: linear-gradient(90deg, transparent, rgba(0,212,255,.5), transparent);
```

### 3.4 Latar Tab Aktif (✅)

```css
--grad-tab-active: linear-gradient(180deg, #092438 0%, #0A1A2D 100%);
```

### 3.5 Progress Line Carousel (✅)

Garis 3px di atas carousel: isi `#14CCED` (≈ cyan), track `#101F33`.

### 3.6 Gradient Tambahan untuk Grafik Anda (⭐ turunan)

Bukan hasil ukur; disusun dari token asli agar grafik baru satu keluarga dengan situs.

| Kebutuhan | Gradient / Palet |
|---|---|
| **Area/line chart (fill)** | `linear-gradient(180deg, rgba(0,212,255,.35), rgba(0,212,255,0))` + garis `--accent-cyan` 2px |
| **Line chart tren positif** | garis `linear-gradient(90deg, var(--accent-cyan), var(--accent-teal))` |
| **Bar vertikal** | `linear-gradient(180deg, var(--accent-teal), var(--accent-cyan))` (hijau di puncak) |
| **Bar bahaya** | `linear-gradient(90deg, var(--accent-red), var(--bs-danger))` |
| **Bar peringatan** | `linear-gradient(90deg, #ffc107, var(--accent-orange))` |
| **Bar kritis (severity)** | `linear-gradient(90deg, var(--sev-kritis), var(--accent-red))` |
| **Donut/pie (6 seri)** | `#00d4ff · #00ff88 · #0d6efd · #ffc107 · #dc3545 · #8892b0` |
| **Palet seri tambahan** | `#7b2fff` (ungu), `#ff8800` (oranye), `#ccff00` (lime) |
| **Heatmap severity** | `#0F1E39 → #0d6efd → #00d4ff → #ffc107 → #dc3545` |
| **Glow bar** | `box-shadow: 0 0 12px var(--glow)` |
| **Grid & sumbu** | garis `--border`, label `--text-secondary` 11–12px mono |
| **Tooltip** | bg `--bg-card`, border `--border`, teks `--text-primary`, radius `--radius` |

**Contoh Chart.js:**

```js
const cs = getComputedStyle(document.documentElement);
const cyan = cs.getPropertyValue('--accent-cyan').trim();   // #00d4ff
const teal = cs.getPropertyValue('--accent-teal').trim();   // #00ff88

const ctx = canvas.getContext('2d');
const g = ctx.createLinearGradient(0, 0, canvas.width, 0);
g.addColorStop(0, cyan);
g.addColorStop(1, teal);

new Chart(ctx, {
  type: 'bar',
  data: { labels: ['Jun','Jul','Agu','Sep'], datasets: [{
    data: [7958, 9919, 10626, 8588],
    backgroundColor: g, borderRadius: 999, barThickness: 14
  }]},
  options: {
    indexAxis: 'y',
    plugins: { legend: { display: false } },
    scales: {
      x: { grid: { color: '#1a3a5c' }, ticks: { color: '#8892b0', font: { family: "'Fragment Mono', monospace" } } },
      y: { grid: { display: false }, ticks: { color: '#8892b0' } }
    }
  }
});
```

---

## 4. Tipografi (🟢 terverifikasi)

| Token asli | Nilai |
|---|---|
| `--font-heading` | `'Sora', 'Play', sans-serif` |
| `--font-mono` | `'Fragment Mono', 'Share Tech Mono', 'Play', monospace` |
| `<body>` `font-family` | `Sora, sans-serif` |

| Peran | Font | Catatan |
|---|---|---|
| Body & heading | **Sora** | Geometris lebar; heading 700–800 🔵 |
| Label, nav, tombol, tab, angka data, meta | **Fragment Mono** (fallback Share Tech Mono → Play → monospace) | ⚠️ Fragment Mono hanya punya **berat 400**; teks mono "tebal" di situs (tombol, angka besar) kemungkinan **faux-bold** dari browser. Tirulah dengan `font-weight: 700` bila ingin tampilan identik, atau pakai `Share Tech Mono` bila ingin tampilan bersih. |

**Memuat font (Google Fonts):**

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700;800&family=Fragment+Mono&family=Share+Tech+Mono&family=Play:wght@400;700&display=swap" rel="stylesheet">
```

### Default terverifikasi

**`<body>`** (🟢 Computed):

```css
body {
  font-family: Sora, sans-serif;
  font-size: 16px;
  font-weight: 400;
  line-height: 1.6;                 /* 25.6px */
  color: var(--text-primary);       /* rgb(224, 240, 255) */
  background-color: var(--bg-primary); /* rgb(10, 22, 40) */
  overflow-x: hidden;
  position: relative;
  min-height: 100vh;
  transition: background 0.4s ease, color 0.4s ease;
}
```

**Item navigasi** (🟢 Computed pada elemen yang Anda inspeksi):

```css
.nav-link {
  display: flex; align-items: center;
  min-height: 44px; height: 44px;          /* target sentuh 44px */
  padding: 8px 10px;
  border: 1px solid transparent;           /* rgba(0,0,0,0) — border disiapkan untuk state aktif */
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 11.2px;                       /* 0.7rem */
  font-weight: 400;
  letter-spacing: 0.25px;
  line-height: 17.92px;                    /* 1.6 */
  color: var(--text-secondary);            /* rgb(136,146,176) */
  cursor: pointer; list-style: none;
  position: relative;
}
```

### Skala elemen lain (🔵 estimasi; skala screenshot tidak pasti)

| Elemen | Perkiraan | Berat | Catatan |
|---|---|---|---|
| Hero title | ~56–60px | 800 | Sora, putih, glow teks halus |
| Hero paragraf | ~17–18px / 1.7 | 400 | tengah, lebar ≈ 700px (sejalan `--content-measure: 70ch`) |
| Judul seksi `[ ARTIKEL // 03 ]` | ~26–28px | 700 | mono, `--accent-neon-green` |
| Judul kartu layanan | ~19–20px | 800 | Sora, UPPERCASE |
| Judul artikel | ~17–18px | 600 | Sora |
| Paragraf kartu | ~14px | 400 | Sora, `--text-muted` |
| Label mikro (`BLIND SPOT`, `SOLUTION`) | ~11–12px | 400 | mono, UPPERCASE, letter-spacing ≈ .1em |
| Teks tombol | ~12–13px | 700 (faux) | mono, UPPERCASE, letter-spacing ≈ .08em |
| Angka statistik | besar (~3× judul kartu) | 700 (faux) | mono, warna sesuai data |
| Meta (tanggal, penulis) | ~11–12px | 400 | mono, `--text-muted` |

**Aturan:** Sora untuk membaca (judul, paragraf); mono untuk semua yang berbau **data/status/aksi** (nav, tombol, label, angka, tanggal).

---

## 5. Bentuk (Shape Language)

### 5.1 Radius (🟢 token; sisanya 🔵)

| Elemen | Radius |
|---|---|
| Item navigasi | **4px** 🟢 |
| Kontrol/tombol umum | **`--radius` 8px** 🟢 |
| Kartu (layanan, artikel, panel chart, statistik) | **`--radius-card` 12px** 🟢 |
| Tab | ≈ 8–10px + chamfer 🔵 |
| Badge/tag artikel | ≈ 4px 🔵 |
| Tombol ikon (cari, tema, carousel) | lingkaran penuh 🔵 |
| Bar chart & track | pil penuh `999px` ✅ |

**Tinggi kontrol:** `--control-height: 40px` 🟢 (tombol CTA terukur ≈ 41px ✅).

### 5.2 Sudut Terpotong (*Chamfer*) — ciri khas

Tombol CTA dan tab memiliki sudut diagonal (terlihat jelas di kanan-bawah, dan kiri-atas pada tombol hero). Ukuran ±8–10px 🔵. (Tidak ada token untuk ini di daftar yang terlihat, kemungkinan `clip-path` langsung pada komponen.)

```css
.chamfer {
  --c: 10px;
  clip-path: polygon(var(--c) 0, 100% 0, 100% calc(100% - var(--c)),
                     calc(100% - var(--c)) 100%, 0 100%, 0 var(--c));
}
```

> ⚠️ `clip-path` memotong `border` dan `box-shadow`. Untuk border tetap terlihat di sudut diagonal, pakai dua lapis (wrapper warna border + inner inset 1px) atau `filter: drop-shadow()` untuk glow.

### 5.3 Border & Garis

- Border standar **1px `var(--border)`** (`#1a3a5c`) 🟢.
- State aktif/hover: 1px `var(--border-glow)` atau `--accent-cyan`; kartu layanan aktif + strip kiri 3px cyan ✅.
- Divider horizontal: 1px `var(--border)` versi redup.
- Garis putus-putus tipis menghubungkan tile ekosistem (motif "pipeline").
- Navbar: garis bawah 1px (`≈ #162539`).

### 5.4 Elevasi & Glow (🟢 token)

| State | Efek |
|---|---|
| Kartu layanan aktif | border cyan + `box-shadow: var(--shadow-glow)` + strip kiri 3px |
| Kartu artikel hover | `background: var(--article-surface-hover)`, `border-color: var(--article-border-hover)`, `box-shadow: var(--article-shadow-hover)` |
| Ikon lingkaran aktif | border `--accent-teal` + glow hijau (≈ `0 0 16px rgba(0,255,136,.45)` 🔵) |
| Tile ekosistem aktif | border & glow oranye |
| Elemen fokus/utama | `box-shadow: 0 0 0 1px var(--border-glow), 0 0 25px var(--glow-strong)` 🔵 |
| Dropdown/modal | `var(--shadow)` |
| Scroll-to-top | lingkaran `--accent-cyan` solid, panah gelap, cincin progres tipis |

---

## 6. Spesifikasi Komponen

### 6.1 Navbar
- Tinggi **`--nav-height: 70px`** 🟢, sticky, bg `--bg-primary` (sedikit transparan + blur 🔵), garis bawah 1px.
- Logo perisai (kiri), glow cyan (warna perisai animasi `#42c3e6`).
- Item `[ NAMA ]`: spesifikasi di bagian 4 (44px, 8×10 padding, radius 4, mono 11.2px). Dropdown ditandai chevron cyan kecil.
- **Item aktif:** teks `--accent-cyan`, border 1px ≈ `#163650`, bg ≈ `rgba(0,212,255,.06)` 🔵 (terukur `#0A2132`).
- Kanan: 2 tombol ikon bulat (cari, tema).
- Konten halaman dimulai di `--page-top` = `calc(var(--nav-height) + clamp(2rem, 5vw, 4rem))`.

### 6.2 Hero
- Latar `--bg-primary` + **animasi jaringan node** (kanvas; token di 2.7): node cyan/teal/ungu/merah, garis alpha 0.2, jejak fade `rgba(10,22,40,.2)`.
- Badge status: titik `--accent-neon-green` berkedip + `[ CSIRT PROVINSI JAWA TIMUR ]`, teks cyan mono, border cyan tipis.
- Judul putih 800 (Sora), paragraf `--text-primary`.
- Dua CTA sejajar (tinggi `--control-height` 40px):
  - **Primer:** bg ≈ `rgba(0,212,255,.08)` (terukur `#082B3F`), border 1px `--accent-cyan`, teks putih, chamfer.
  - **Bahaya:** bg ≈ `rgba(255,51,102,.13)` (terukur `#2C1F33`), border 1px `--accent-red`, ikon perisai-seru, chamfer.

### 6.3 Kartu Layanan (Carousel)
- Lebar ≈ 324px, tinggi ≈ 470px 🔵, gap ≈ 20px, padding ≈ 24px, radius **12px** 🟢.
- Struktur: nomor (`04`, mono, `--text-muted`) + ikon lingkaran di kanan-atas → judul UPPERCASE (Sora 800) → **BLIND SPOT** (label mono muted + kalimat) → divider → **SOLUTION** (label mono **cyan**) → tombol di dasar.
- **Idle:** bg `--bg-card`, border ≈ `#1F314D`.
- **Aktif:** bg ≈ `#0D2037`, strip kiri 3px cyan, border cyan ±40% (`--border-glow`), `--shadow-glow`, ikon jadi lingkaran hijau bercahaya.
- Tombol "LIHAT DETAIL LAYANAN →": tinggi 40px, lebar penuh, bg ≈ `#0D2D49`, border 1px cyan, teks putih mono, chamfer.
- Tepi kanan carousel di-*fade*. Prev/next: lingkaran ≈ 44px, bg ≈ `#003B55`, panah cyan.

### 6.4 Ekosistem (5 tile)
- Idle: ikon abu-biru (`--text-secondary-filter`) + nama mono UPPERCASE; bg `--bg-card`, border ≈ `#1B2E47`, radius 12px.
- Aktif melebar (tampil nama, subjudul, deskripsi terpotong `…`); warna berubah ke oranye (2.6).
- Label kategori di atas tile (`EDUKASI`, `PATROLI`, …): mono kecil, `--text-muted`.

### 6.5 Kartu Artikel
- Bg `--bg-card`, border 1px `--border`, radius 12px, padding ≈ 24px.
- Layout 2 kolom: satu kartu unggulan besar + kartu kecil bertumpuk (banner lebar).
- Hover: token `--article-*` (2.4), `transition: var(--transition)`.
- Badge kategori: bg gelap `≈ #061621`, border cyan, teks cyan mono, radius ≈ 4px.
- Meta: `15.09.2026 // Nama Penulis`, mono `--text-muted`.
- Ilustrasi bergaya 3D/AI neon biru-cyan.

### 6.6 Kartu Statistik (Dashboard)
- 6 kartu sejajar rata, bg `--bg-card`, border 1px `--border`, radius 12px (≈ 16px tampak di screenshot 🔵).
- Angka besar mono, warna sesuai 2.5, glow teks sewarna (≈ `0 0 20px <warna>66` 🔵); label UPPERCASE `--text-secondary`.
- Angka **dianimasikan count-up** ±0.8s (`--anim-duration-countup`) 🟢. Format ribuan koma: `66,178`.

### 6.7 Tab Kategori Data
- Bentuk `< DOKUMEN >`, `< CVE >`, … (tanda `< >` cyan gelap `#047894` saat idle).
- Idle: bg `≈ #0A1C2F`, border 1px `--border`, teks `--text-secondary`, chamfer.
- **Aktif:** border 1.5px `--accent-red`, teks & `< >` `--accent-red`, bg gradient 3.4, garis glow di bawah (3.3).
- Warna aktif **merah**, bukan cyan, agar terpisah dari aksen navigasi.

### 6.8 Panel Bar Chart
- Panel: bg `--bg-card`, border 1px `--border`, radius 12–16px, padding ≈ 30px.
- Header: judul kiri (`Tahun 2026`, 700, `--text-primary`) — total kanan (angka cyan mono + `TOTAL CVE` kecil).
- Sub-judul `RINCIAN 4 BULAN TERAKHIR (ROLLING)` UPPERCASE `--text-muted`.
- Baris: label bulan (kolom kiri ≈ 12%) — track — nilai (kanan, mono, `--text-primary`).
- Track: tinggi ≈ 14px, bg **`--bg-secondary`** (`#0d2137`) ✅, border 1px **`--border`** ✅, pil penuh. Fill: gradient 3.1.
- **Panjang bar** = `nilai / nilai_maks × 100%` ✅ (Juni 75.0% ↔ 74.9%).
- Bulan berjalan → gradient parsial (3.2) + label cyan.
- Footer: garis 1px `--border`, ikon ⓘ + catatan `--text-secondary`.
- Sinkron: titik `--accent-neon-green` + `Terakhir disinkronkan …`; tombol **"Lihat Semua"** solid `--accent-cyan`, teks gelap `≈ #081428`, radius ≈ 4px (satu-satunya tombol solid).

---

## 7. Layout, Spacing & Grid

- **Kontainer:** ≈ 1310px pada viewport 1456px → konsisten dengan **container Bootstrap xxl = 1320px** (🔵 disimpulkan dari stack Bootstrap).
- **Ukuran layout 🟢:** `--nav-height: 70px`, `--page-top: calc(var(--nav-height) + clamp(2rem, 5vw, 4rem))`, `--content-measure: 70ch` (lebar baca paragraf).
- **Skala spacing:** kelipatan 4/8px (utilitas Bootstrap `1–5` = .25/.5/1/1.5/3rem).
- **Jarak antar seksi:** ≈ 64–96px, dipisah garis 1px.
- **Alignment:** hero & judul pembuka seksi **center**; konten **left**.
- **Latar:** polos `--bg-primary`; grid samar (kotak ≈ 40px) tampak pada zoom 🔵:
  `background-image: linear-gradient(rgba(0,212,255,.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,.03) 1px, transparent 1px); background-size: 40px 40px;`

---

## 8. Ikonografi & Gambar

- **Ikon UI:** outline rounded, stroke ≈ 1.5–2px, gaya Lucide/Feather (cari, matahari, panah, perisai-seru, clipboard-check, radio-tower, ⓘ).
- **Ikon ekosistem:** 5 maskot hewan; aktif = warna aksen (2.6), idle = hitam yang diwarnai lewat `filter: var(--text-secondary-filter)`.
- **Logo:** perisai + ornamen, glow cyan (`#42c3e6`).
- **Ilustrasi:** komposisi gelap, neon cyan/biru; aksen merah untuk ancaman.

---

## 9. Motion (🟢 token asli)

| Token | Nilai | Pemakaian |
|---|---|---|
| `--transition` | `transform .3s, opacity .3s, color .3s` semuanya `cubic-bezier(.4, 0, .2, 1)` | transisi umum (kartu, link) |
| `--transition-fast` | `background-color/border-color/color/box-shadow 180ms ease-out, transform 140ms ease-out` | hover tombol, tab, kontrol |
| `--anim-duration-fast` | `0.25s` | mikro-interaksi |
| `--anim-duration-snappy` | `0.35s` | panel/dropdown |
| `--anim-duration-smooth` | `0.4s` | transisi tema, elemen besar |
| `--anim-duration-countup` | `0.8s` | animasi hitung angka statistik |
| `--anim-ease-out` | `cubic-bezier(.23, 1, .32, 1)` | masuk/entrance (deselerasi kuat) |
| `--anim-ease-in-out` | `cubic-bezier(.4, 0, .2, 1)` | perubahan state |
| `--anim-ease-move` | `cubic-bezier(.77, 0, .175, 1)` | pergerakan/slide (carousel) |
| `<body>` | `background, color 0.4s ease` | toggle tema |

**Rekomendasi penerapan (🔵):** bar chart tumbuh dari 0 ke nilai dengan `--anim-duration-smooth` + `--anim-ease-out`; titik status hijau *pulse* 2s; matikan animasi partikel & pulse pada `prefers-reduced-motion`.

---

## 10. Design Tokens Siap Pakai

### 10.1 Salinan token asli (🟢 dari `cyber-theme.css?v=61`)

```css
:root {
  /* Surface */
  --bg-primary: #0a1628;
  --bg-secondary: #0d2137;
  --bg-card: rgba(17, 34, 64, 0.7);

  /* Accent */
  --accent-cyan: #00d4ff;
  --accent-teal: #00ff88;
  --accent-neon-green: #00ff9d;
  --accent-neon-yellow: #ccff00;
  --accent-purple: #7b2fff;
  --accent-red: #ff3366;
  --accent-orange: #ff8800;

  /* Hero animation */
  --hero-animation-cyan: #00d4ff;
  --hero-animation-shield: #42c3e6;
  --hero-animation-teal: #00ff88;
  --hero-animation-purple: #7b2fff;
  --hero-animation-red: #ff3366;
  --hero-animation-glow: rgba(0, 212, 255, 0.3);
  --hero-animation-trail: rgba(10, 22, 40, 0.2);
  --hero-animation-fade: rgba(0, 0, 0, 1);
  --hero-animation-line-alpha: 0.2;

  /* Text */
  --text-primary: #e0f0ff;
  --text-secondary: #8892b0;
  --text-muted: #7d8ca6;
  --text-secondary-filter: invert(70%) sepia(11%) saturate(543%) hue-rotate(189deg) brightness(96%) contrast(87%);

  /* Border, glow, shadow */
  --border: #1a3a5c;
  --border-glow: rgba(0, 212, 255, 0.4);
  --glow: rgba(0, 212, 255, 0.3);
  --glow-strong: rgba(0, 212, 255, 0.6);
  --shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
  --shadow-glow: 0 0 25px rgba(0, 212, 255, 0.25);
  --article-surface-hover: rgba(19, 39, 70, 0.82);
  --article-border-hover: rgba(0, 212, 255, 0.48);
  --article-shadow-hover: 0 10px 24px rgba(0, 0, 0, 0.22);

  /* Motion */
  --transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1), color 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  --transition-fast: background-color 180ms ease-out, border-color 180ms ease-out, color 180ms ease-out, box-shadow 180ms ease-out, transform 140ms ease-out;
  --anim-duration-fast: 0.25s;
  --anim-duration-snappy: 0.35s;
  --anim-duration-smooth: 0.4s;
  --anim-duration-countup: 0.8s;
  --anim-ease-out: cubic-bezier(0.23, 1, 0.32, 1);
  --anim-ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  --anim-ease-move: cubic-bezier(0.77, 0, 0.175, 1);

  /* Type & shape & layout */
  --font-mono: 'Fragment Mono', 'Share Tech Mono', 'Play', monospace;
  --font-heading: 'Sora', 'Play', sans-serif;
  --radius: 8px;
  --radius-card: 12px;
  --control-height: 40px;
  --nav-height: 70px;
  --page-top: calc(var(--nav-height) + clamp(2rem, 5vw, 4rem));
  --content-measure: 70ch;
  --sev-kritis: #f45b69;
  /* + 61 properti lain belum terlihat */
}
```

### 10.2 Token turunan (⭐ tambahan saya — bukan dari situs)

```css
:root {
  /* Data (Bootstrap 5.3, 🟢 nilai asli --bs-*) */
  --data-danger:  #dc3545;   /* --bs-danger  */
  --data-warning: #ffc107;   /* --bs-warning */
  --data-info:    #0dcaf0;   /* --bs-info    */
  --data-primary: #0d6efd;   /* --bs-primary */

  /* Gradient (✅ terukur; ujung = token aksen) */
  --grad-bar:           linear-gradient(90deg, var(--accent-cyan) 0%, var(--accent-teal) 100%);
  --grad-bar-partial:   linear-gradient(90deg, var(--accent-cyan) 0%, #6E7A87 100%);
  --grad-tab-active:    linear-gradient(180deg, #092438 0%, #0A1A2D 100%);
  --grad-tab-underline: linear-gradient(90deg, transparent, rgba(0,212,255,.5), transparent);
  --grad-area-fill:     linear-gradient(180deg, rgba(0,212,255,.35) 0%, rgba(0,212,255,0) 100%);
  --grad-danger:        linear-gradient(90deg, var(--accent-red) 0%, #dc3545 100%);

  /* Bentuk */
  --chamfer: 10px;             /* 🔵 */
  --orange-jaguar: #ff6f16;    /* 🔵 estimasi */
}
```

### 10.3 Contoh komponen inti

```css
body {
  font-family: Sora, sans-serif; font-size: 16px; line-height: 1.6;
  color: var(--text-primary); background: var(--bg-primary);
  transition: background .4s ease, color .4s ease;
}

.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-card);
  transition: var(--transition-fast);
}
.card:hover {
  background: var(--article-surface-hover);
  border-color: var(--article-border-hover);
  box-shadow: var(--article-shadow-hover);
}

.bar-track { height: 14px; background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 999px; overflow: hidden; }
.bar-fill  { height: 100%; background: var(--grad-bar); border-radius: 999px; transition: width var(--anim-duration-smooth) var(--anim-ease-out); }
.bar-fill.is-partial { background: var(--grad-bar-partial); }

.btn-cta {
  height: var(--control-height); padding: 0 28px;
  font: 400 12.5px/1 var(--font-mono); font-weight: 700; letter-spacing: .08em; text-transform: uppercase;
  color: #fff; background: rgba(0,212,255,.08); border: 1px solid var(--accent-cyan);
  clip-path: polygon(10px 0,100% 0,100% calc(100% - 10px),calc(100% - 10px) 100%,0 100%,0 10px);
  transition: var(--transition-fast);
}
.btn-cta--danger { background: rgba(255,51,102,.13); border-color: var(--accent-red); }

.stat-num { font: 700 3.5rem/1 var(--font-mono); text-shadow: 0 0 20px currentColor; } /* count-up 0.8s via JS */
```

---

## 11. Do & Don't

| ✅ Do | ❌ Don't |
|---|---|
| Pakai variabel (`var(--bg-card)`) bukan hex, agar tema terang bisa menimpa | Hard-code hex di komponen |
| Kartu = `--bg-card` (semi-transparan) di atas `--bg-primary` | Kartu solid `#0F1F39` tanpa transparansi |
| Cyan = interaksi, teal = sukses/ujung gradient, merah = alert, oranye = ekosistem | Mencampur banyak neon dalam satu kartu |
| Gradient **per elemen** (bar mulai cyan, berakhir teal) | Satu gradient panjang untuk seluruh track |
| Gradient parsial abu untuk data belum final | Menampilkan bulan berjalan seolah lengkap |
| Mono untuk label/angka/CTA; Sora untuk paragraf | Mono untuk paragraf panjang |
| Chamfer hanya di tombol/tab | Chamfer di semua elemen |
| Glow (`--glow*`) hanya pada state aktif/hover | Glow permanen di semua kartu |
| Gunakan `--text-muted` (4.9 : 1) untuk teks kecil | Menurunkan kontras teks di bawah AA |
| Batasi seri chart ≤ 6 warna | Memakai `#7b2fff` untuk teks (2.9 : 1) |

---

## 12. Langkah Berikutnya

1. Klik **"Show all properties (61 more)"** pada blok `:root` pertama dan kirim screenshot-nya (kemungkinan `--sev-*` lain, token komponen, dan warna Jaguar).
2. Ambil **mode terang**: klik toggle ☀, lalu inspeksi `<html>`/`<body>` dan catat atribut (`data-theme`/class) serta blok override variabelnya.
3. Inspeksi **h1**, **judul kartu layanan**, **teks tombol CTA**, dan **angka statistik** (Computed → font-size, font-weight, letter-spacing) untuk mengganti seluruh baris 🔵 di bagian 4.
4. Inspeksi tombol CTA di tab *Styles* untuk melihat `clip-path` chamfer yang sebenarnya.
5. Tampilan **mobile** (nav hamburger, carousel, kartu statistik) — Bootstrap breakpoint sudah bisa diasumsikan, tetapi perilaku aslinya belum terlihat.

---

*Revisi 3. Sumber: 4 screenshot tampilan + 2 Computed (`<body>`, item navigasi) + 3 panel Styles `:root` (`cyber-theme.css?v=61` dan Bootstrap `_root.scss`). Halaman lain (Profil, Dokumen, Kontak, footer) belum terwakili.*

**Riwayat koreksi:** (R2) font body Sora; teks `#E0F0FF`. (R3) font mono ternyata **Fragment Mono** (bukan JetBrains Mono); `--text-muted` `#7d8ca6` (bukan `#64748B`); judul seksi `#00ff9d` (bukan `#00FF9C`); surface kartu = `rgba(17,34,64,.7)` transparan; oranye Beruang = `#ff8800` @ ±0.85; nav item radius 4px & 11.2px; navbar 70px; container mengikuti Bootstrap 5.3; ditambah token glow/shadow/hover artikel, animasi hero, motion, dan `--text-secondary-filter`.
