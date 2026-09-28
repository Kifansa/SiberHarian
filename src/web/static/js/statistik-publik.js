/**
 * Modul Frontend untuk Statistik & Edukasi Publik (SiberHarian - CSIRT Jatim)
 * Menyajikan:
 * 1. Insightful KPI Cards (Wawasan bermakna berbasis data riil)
 * 2. Word Cloud Kasus Insiden Spesifik (Interaktif, filter berita langsung)
 * 3. Grafik Fakta Siber (Top Ancaman & Software Populer Terpapar)
 * 4. Daftar Intisari Artikel Edukasi Nyata dari Database
 */

import { simpanItemModal } from './modal.js';
import { escapeHtml } from './utils.js';

let chartAncaman = null;
let chartVendor = null;
let chartTimeline = null;
let chartSebaranMedia = null;
let kataTerpilih = null;


export async function muatTabStatistikPublik() {
  try {
    const res = await fetch("/api/statistik-publik");
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();

    if (data.status !== "ok") throw new Error("Gagal mengambil data statistik publik");

    // 1. Update Insightful KPI Cards (Fakta Murni dengan Deskripsi)
    if (data.kpi_insights && Array.isArray(data.kpi_insights)) {
      data.kpi_insights.forEach((kpi, idx) => {
        const elVal = document.getElementById(`pub-kpi-${idx + 1}-val`);
        const elDesc = document.getElementById(`pub-kpi-${idx + 1}-desc`);
        if (elVal && kpi.nilai) elVal.textContent = kpi.nilai;
        if (elDesc && kpi.insight) elDesc.textContent = kpi.insight;
      });
    }

    // 2. Render Word Cloud Kasus Insiden Spesifik (7 Hari Terkini)
    renderWordCloud(data.word_cloud || []);

    // 3. Render Chart Top Ancaman dan Software Terpapar (Fakta Praktis)
    renderChartAncaman(data.top_ancaman || []);
    renderChartVendor(data.top_vendor || []);

    // 4. Render Intisari Artikel Edukasi Nyata
    renderEdukasiList(data.edukasi_list || []);

  } catch (err) {
    console.error("Gagal memuat statistik publik:", err);
  }
}

/**
 * Palet warna organik terinspirasi visual referensi word cloud:
 * Harmoni eggplant, navy, amber/karamel, ocean teal, forest green, cobalt, dan wine.
 */
const PALET_WORDCLOUD_ORGANIK = [
  "#1E1B4B", // Midnight Indigo (seperti 'audience')
  "#4A154B", // Deep Eggplant / Violet (seperti 'together')
  "#92400E", // Warm Caramel / Amber (seperti 'discover')
  "#155E75", // Deep Ocean Cyan (seperti 'create')
  "#0F766E", // Pine Teal (seperti 'word')
  "#15803D", // Forest Green (seperti 'opinions')
  "#1D4ED8", // Royal Cobalt (seperti 'artwork')
  "#831843", // Deep Wine / Plum (seperti 'shared')
  "#9A3412", // Rust Ochre (seperti 'words')
  "#3730A3", // Indigo Slate (seperti 'feelings')
  "#047857", // Emerald Green (seperti 'cloud')
  "#701A75", // Magenta Plum (seperti 'poll')
  "#1E40AF", // Navy Blue (seperti 'complex')
  "#4D7C0F", // Olive Green (seperti 'question')
  "#991B1B", // Dark Crimson (seperti 'grow')
  "#0A4174", // CSIRT Dark Sapphire
];

/**
 * Susun kata kunci ke dalam struktur awan konsentris:
 * Mengumpulkan seluruh kata terbesar (inti topik) rapat di tengah canvas,
 * sementara kata-kata pendukung berbobot sedang/kecil mengitari di sisi luar.
 */
function susunAwanOrganik(wordList) {
  if (!wordList || wordList.length <= 4) return wordList;

  // Urutkan dari bobot terbesar ke terkecil
  const sorted = [...wordList].sort((a, b) => b.bobot - a.bobot);

  // Ambil kata-kata inti terbesar (Top 6-8 kata terbesar)
  const giantCount = Math.min(8, Math.max(4, Math.floor(sorted.length * 0.28)));
  const giants = sorted.slice(0, giantCount);
  const remaining = sorted.slice(giantCount);

  // Kata terbesar (giants) dikelompokkan rapat bersama-sama di tengah:
  // Susun giants secara berselang-seling dari pusat (spiral concentric core)
  const centerCore = [];
  giants.forEach((item, idx) => {
    if (idx % 2 === 0) {
      centerCore.push(item);
    } else {
      centerCore.unshift(item);
    }
  });

  // Kata-kata sisanya (medium & kecil) dibagi rata ke sisi luar (kiri/atas dan kanan/bawah)
  const outerLeft = [];
  const outerRight = [];
  remaining.forEach((item, idx) => {
    if (idx % 2 === 0) {
      outerLeft.push(item);
    } else {
      outerRight.push(item);
    }
  });

  // Gabungkan: Outer kiri -> INTI KATA TERBESAR DI TENGAH -> Outer kanan
  return [...outerLeft, ...centerCore, ...outerRight];
}

/**
 * Render Word Cloud Kasus Insiden Spesifik
 * Tipografi organik murni tanpa angka dan tanpa border sesuai referensi visual
 */
function renderWordCloud(wordList) {
  const container = document.getElementById("pub-wordcloud-box");
  if (!container) return;

  if (!wordList || wordList.length === 0) {
    container.innerHTML = `<div class="text-xs text-[#49769F]">Belum ada kata kunci insiden yang tercatat.</div>`;
    return;
  }

  const maxBobot = Math.max(...wordList.map((w) => w.bobot), 1);
  const minBobot = Math.min(...wordList.map((w) => w.bobot), 1);

  // Susun awan secara organik agar kata terbesar berada di tengah
  const clusteredWords = susunAwanOrganik(wordList);

  container.innerHTML = clusteredWords
    .map((item, idx) => {
      // Skala ukuran font & ketebalan dinamis
      // Min: 13px (medium), Max: 46px (black)
      const rasio = (item.bobot - minBobot) / (maxBobot - minBobot || 1);
      const fontSize = Math.round(13 + rasio * 33);
      
      let fontWeight = 500;
      let letterSpacing = "-0.01em";
      if (item.bobot >= 40) {
        fontWeight = 900;
        letterSpacing = "-0.035em";
      } else if (item.bobot >= 25) {
        fontWeight = 800;
        letterSpacing = "-0.025em";
      } else if (item.bobot >= 15) {
        fontWeight = 700;
        letterSpacing = "-0.015em";
      } else if (item.bobot >= 8) {
        fontWeight = 600;
      }

      // Pilih warna organik tematik
      const color = PALET_WORDCLOUD_ORGANIK[idx % PALET_WORDCLOUD_ORGANIK.length];
      const isAktif = kataTerpilih === item.kata.toLowerCase();

      // Desain murni tipografi: TANPA border, TANPA angka, TANPA background kotak
      const safeKata = escapeHtml(item.kata);
      return `
        <button type="button"
          data-kata-raw="${safeKata}"
          onclick="window.pilihWordCloud(this.getAttribute('data-kata-raw'))"
          data-kata="${safeKata.toLowerCase()}"
          style="font-size: clamp(${Math.round(fontSize * 0.72)}px, ${fontSize * 0.08}vw + 12px, ${fontSize}px); color: ${color}; font-weight: ${fontWeight}; letter-spacing: ${letterSpacing}; ${isAktif ? 'background-color: #EEF5FA; outline: 2px solid #0A4174; border-radius: 8px; padding: 2px 8px; transform: scale(1.15); opacity: 1;' : ''}"
          class="wordcloud-item inline-block font-sans cursor-pointer transition-all duration-200 hover:scale-110 hover:bg-[#EEF5FA]/80 px-2 py-1 leading-none whitespace-nowrap select-none focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none rounded-lg"
          title="Saring kasus: ${safeKata}">
          ${safeKata}
        </button>
      `;
    })
    .join("");

  // Sesuaikan opasitas jika sudah ada kata yang terpilih
  if (kataTerpilih) {
    sorotKataAktif(kataTerpilih);
  }
}

function sorotKataAktif(kata) {
  const items = document.querySelectorAll("#pub-wordcloud-box .wordcloud-item");
  items.forEach((item) => {
    const itemKata = item.getAttribute("data-kata") || "";
    if (itemKata.toLowerCase() === kata.toLowerCase()) {
      item.style.opacity = "1";
      item.style.transform = "scale(1.15)";
      item.style.backgroundColor = "#EEF5FA";
      item.style.outline = "2px solid #0A4174";
      item.style.borderRadius = "8px";
      item.style.padding = "2px 8px";
      item.classList.add("z-10", "shadow-xs");
    } else {
      item.style.opacity = "0.35";
      item.style.transform = "scale(0.96)";
      item.style.backgroundColor = "transparent";
      item.style.outline = "none";
      item.style.padding = "2px 4px";
      item.classList.remove("z-10", "shadow-xs");
    }
  });
}

// Interaktivitas: Memfilter berita di halaman Beranda berdasarkan kata kunci Word Cloud
window.pilihWordCloud = function (kata) {
  const kataLower = (kata || "").trim().toLowerCase();

  // Jika kata yang sama diklik lagi, batalkan saringan (toggle)
  if (kataTerpilih === kataLower) {
    window.resetFilterWordCloud();
    return;
  }

  kataTerpilih = kataLower;
  const btnReset = document.getElementById("pub-wordcloud-reset");
  if (btnReset) btnReset.classList.remove("hidden");

  const labelActive = document.getElementById("pub-wordcloud-active-label");
  if (labelActive) {
    labelActive.textContent = `Menyaring kasus: "${kata}"`;
    labelActive.classList.remove("hidden");
  }

  // Sinkronkan ke input search feed beranda
  const berandaInput = document.getElementById("beranda-search-input");
  if (berandaInput) {
    berandaInput.value = kata;
  }

  // Update visual item awan kata
  sorotKataAktif(kataLower);

  // Filter kartu berita di tab beranda
  if (window.filterBerandaCards) {
    window.filterBerandaCards(kataLower);
  }

  // Scroll halus ke area kartu berita
  const feedAnchor = document.getElementById("feed-beranda-anchor") || document.getElementById("card-container");
  if (feedAnchor) {
    feedAnchor.scrollIntoView({ behavior: "smooth", block: "start" });
  }
};

window.resetFilterWordCloud = function () {
  kataTerpilih = null;
  const btnReset = document.getElementById("pub-wordcloud-reset");
  if (btnReset) btnReset.classList.add("hidden");

  const labelActive = document.getElementById("pub-wordcloud-active-label");
  if (labelActive) labelActive.classList.add("hidden");

  const berandaInput = document.getElementById("beranda-search-input");
  if (berandaInput && berandaInput.value) {
    berandaInput.value = "";
  }

  // Pulihkan seluruh kata ke kondisi normal
  const items = document.querySelectorAll("#pub-wordcloud-box .wordcloud-item");
  items.forEach((item) => {
    item.style.opacity = "1";
    item.style.transform = "scale(1)";
    item.style.backgroundColor = "transparent";
    item.style.outline = "none";
    item.style.padding = "2px 4px";
    item.classList.remove("z-10", "shadow-xs");
  });

  if (window.filterBerandaCards) {
    window.filterBerandaCards("");
  }
};

/**
 * Render Daftar Judul Edukasi Keamanan Siber (Title-Only, Scrollable, Detail saat Diklik)
 */
function renderEdukasiList(edukasiList) {
  const container = document.getElementById("pub-edukasi-grid");
  if (!container) return;

  const countBadge = document.getElementById("pub-edukasi-count");
  if (countBadge) {
    countBadge.textContent = `${edukasiList ? edukasiList.length : 0} Panduan`;
  }

  if (!edukasiList || edukasiList.length === 0) {
    container.innerHTML = `<div class="col-span-full py-8 text-center text-xs text-[#49769F]">Belum ada artikel edukasi dalam 7 hari terakhir.</div>`;
    return;
  }

  container.innerHTML = edukasiList
    .map((item) => {
      const tanggalFormat = item.tanggal ? item.tanggal.slice(0, 10) : "Terkini";
      const sumberLengkap = item.sumber
        ? `${item.sumber} • ${tanggalFormat}`
        : `CSIRT Jatim • ${tanggalFormat}`;

      // Simpan seluruh data lengkap (rangkuman & metadata) ke registry modal
      const idx = simpanItemModal({
        judul: item.judul,
        sumber: sumberLengkap,
        link: item.link || '',
        teksLengkap: item.ringkasan || "Tidak ada rangkuman detail tersedia.",
        pillClass: 'bg-emerald-50 text-[#15803d] border border-emerald-200',
        pillLabel: 'Edukasi Keamanan Siber'
      });

      // Hanya tampilkan judul saja, rangkuman dan info lainnya muncul setelah diklik (modal)
      return `
        <button type="button" 
          onclick="window.bukaModal ? window.bukaModal(${idx}) : bukaModal(${idx})"
          class="w-full text-left bg-white hover:bg-[#EEF5FA] border border-[#E2EDF8] hover:border-[#BDD8E9] p-3 sm:p-3.5 rounded-xl transition-all flex items-center justify-between gap-3 group cursor-pointer shadow-2xs hover:shadow-xs active:scale-[0.99] focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none"
          title="Klik untuk membaca rangkuman dan informasi lengkap">
          <div class="flex items-center gap-2.5 sm:gap-3 min-w-0">
            <span class="w-7 h-7 sm:w-8 sm:h-8 rounded-lg bg-emerald-50 text-[#15803d] flex items-center justify-center shrink-0 group-hover:bg-emerald-100 group-hover:scale-105 transition-all">
              <span class="material-symbols-outlined text-base sm:text-lg" aria-hidden="true">menu_book</span>
            </span>
            <span class="font-bold text-xs sm:text-sm text-[#001D39] group-hover:text-[#0A4174] transition-colors line-clamp-2 leading-snug">
              ${escapeHtml(item.judul)}
            </span>
          </div>
          <span class="material-symbols-outlined text-slate-400 group-hover:text-[#0A4174] text-base sm:text-lg shrink-0 transition-transform group-hover:translate-x-0.5" aria-hidden="true">
            arrow_forward
          </span>
        </button>
      `;
    })
    .join("");
}

function renderChartAncaman(topAncaman) {
  const ctx = document.getElementById("chart-ancaman-publik");
  if (!ctx) return;

  if (chartAncaman) chartAncaman.destroy();

  const labels = topAncaman.map((a) => a.kategori);
  const values = topAncaman.map((a) => a.jumlah);
  const totalKasus = values.reduce((a, b) => a + b, 0) || 1;

  const colors = ["#0A4174", "#49769F", "#4E8EA2", "#6EA2B3", "#7BBDE8", "#BDD8E9"];

  chartAncaman = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Jumlah Laporan",
          data: values,
          backgroundColor: colors.slice(0, values.length),
          borderRadius: 6,
          borderWidth: 1,
          borderColor: "#E2EDF8",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#001D39",
          titleFont: { family: "Inter", size: 12, weight: "bold" },
          bodyFont: { family: "Inter", size: 12 },
          padding: 8,
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed.y;
              const pct = Math.round((val / totalKasus) * 100);
              return ` ${val} Kasus Terlaporkan (${pct}% dari total)`;
            },
          },
        },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: "Inter", size: 10, weight: "600" },
            color: "#001D39",
          },
        },
        y: {
          beginAtZero: true,
          grid: { color: "#E2EDF8" },
          ticks: {
            font: { family: "JetBrains Mono", size: 10 },
            color: "#49769F",
            precision: 0,
          },
        },
      },
    },
  });
}

function renderChartVendor(topVendor) {
  const ctx = document.getElementById("chart-vendor-publik");
  if (!ctx) return;

  if (chartVendor) chartVendor.destroy();

  const labels = topVendor.map((v) => v.vendor);
  const values = topVendor.map((v) => v.total_cve);

  chartVendor = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          axis: "y",
          label: "Total CVE Kritis",
          data: values,
          backgroundColor: "#0A4174",
          borderRadius: 4,
        },
      ],
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#001D39",
          titleFont: { family: "Inter", size: 12, weight: "bold" },
          bodyFont: { family: "Inter", size: 11 },
          padding: 8,
          callbacks: {
            label: (ctx) => ` ${ctx.parsed.x} Celah Kerentanan Kritis (CVSS ≥ 9.0)`,
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: "#E2EDF8" },
          ticks: {
            font: { family: "JetBrains Mono", size: 10 },
            color: "#49769F",
            precision: 0,
          },
        },
        y: {
          grid: { display: false },
          ticks: {
            font: { family: "Inter", size: 10, weight: "600" },
            color: "#001D39",
          },
        },
      },
    },
  });
}

function renderChartTimeline(timelineData) {
  const ctx = document.getElementById("chart-timeline-publik");
  if (!ctx || !timelineData || !timelineData.label || timelineData.label.length === 0) return;

  if (chartTimeline) chartTimeline.destroy();

  const formattedLabels = timelineData.label.map((tgl) => {
    const parts = tgl.split("-");
    return parts.length === 3 ? `${parts[2]}/${parts[1]}` : tgl;
  });

  const beritaVals = timelineData.berita || [];
  const avgBerita = beritaVals.length ? (beritaVals.reduce((a, b) => a + b, 0) / beritaVals.length) : 0;

  chartTimeline = new Chart(ctx, {
    type: "line",
    data: {
      labels: formattedLabels,
      datasets: [
        {
          label: "Berita Insiden",
          data: beritaVals,
          borderColor: "#0A4174",
          backgroundColor: "rgba(10, 65, 116, 0.08)",
          fill: true,
          tension: 0.35,
          pointBackgroundColor: (ctx) => {
            const val = ctx.raw;
            return (val >= avgBerita * 1.8 && val > 2) ? "#b91c1c" : "#0A4174";
          },
          pointRadius: (ctx) => {
            const val = ctx.raw;
            return (val >= avgBerita * 1.8 && val > 2) ? 6 : 4;
          },
          pointHoverRadius: 7,
          borderWidth: 2.5,
        },
        {
          label: "CVE Kritis",
          data: timelineData.cve || [],
          borderColor: "#d97706",
          backgroundColor: "rgba(217, 119, 6, 0.06)",
          fill: true,
          tension: 0.35,
          pointBackgroundColor: "#d97706",
          pointRadius: 4,
          pointHoverRadius: 6,
          borderWidth: 2.5,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: "index",
        intersect: false,
      },
      plugins: {
        legend: {
          display: true,
          position: "top",
          align: "end",
          labels: {
            boxWidth: 12,
            boxHeight: 12,
            usePointStyle: true,
            font: { family: "Inter", size: 11, weight: "600" },
            color: "#001D39",
          },
        },
        tooltip: {
          backgroundColor: "#001D39",
          titleFont: { family: "Inter", size: 12, weight: "bold" },
          bodyFont: { family: "Inter", size: 11 },
          padding: 10,
          boxPadding: 4,
        },
      },
      scales: {
        x: {
          grid: { color: "#F0F4F8" },
          ticks: {
            font: { family: "Inter", size: 10, weight: "500" },
            color: "#49769F",
          },
        },
        y: {
          beginAtZero: true,
          grid: { color: "#E2EDF8" },
          ticks: {
            font: { family: "JetBrains Mono", size: 10 },
            color: "#49769F",
            precision: 0,
          },
        },
      },
    },
  });
}

function renderSebaranMedia(sebaranMedia) {
  const ctx = document.getElementById("chart-sebaran-media-publik");
  if (!ctx || !sebaranMedia) return;

  if (chartSebaranMedia) chartSebaranMedia.destroy();

  const nas = sebaranMedia["Media Nasional"] || 0;
  const intl = sebaranMedia["Media Global & CTI"] || 0;
  const total = nas + intl || 1;
  const pctNas = Math.round((nas / total) * 100);
  const pctIntl = 100 - pctNas;

  const elNas = document.getElementById("sebaran-media-nasional-val");
  const elGlobal = document.getElementById("sebaran-media-global-val");
  if (elNas) elNas.textContent = `${nas} berita (${pctNas}%)`;
  if (elGlobal) elGlobal.textContent = `${intl} berita (${pctIntl}%)`;

  chartSebaranMedia = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Media Nasional", "Media Global & CTI"],
      datasets: [
        {
          data: [nas, intl],
          backgroundColor: ["#0A4174", "#4E8EA2"],
          borderWidth: 2,
          borderColor: "#ffffff",
          hoverOffset: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "68%",
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#001D39",
          titleFont: { family: "Inter", size: 12, weight: "bold" },
          bodyFont: { family: "Inter", size: 11 },
          padding: 8,
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed;
              const pct = Math.round((val / total) * 100);
              return ` ${ctx.label}: ${val} artikel (${pct}%)`;
            },
          },
        },
      },
    },
  });
}

window.muatTabStatistikPublik = muatTabStatistikPublik;
