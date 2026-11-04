/**
 * Modul Frontend untuk Statistik & Edukasi Publik (SiberHarian)
 * Menyajikan:
 * 1. Insightful KPI Cards (Wawasan bermakna berbasis data riil)
 * 2. Word Cloud Kasus Insiden Spesifik (Interaktif, filter berita langsung)
 * 3. Grafik Fakta Siber (Top Ancaman Horizontal Pill Bar Chart)
 * 4. Daftar Intisari Artikel Edukasi Nyata dari Database
 */

import { simpanItemModal } from './modal.js';
import { escapeHtml } from './utils.js';

let chartAncaman = null;
let chartTimeline = null;
let chartSebaranMedia = null;
let kataTerpilih = null;

export async function muatTabStatistikPublik() {
  try {
    const res = await fetch("/api/statistik-publik");
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();

    if (data.status !== "ok") throw new Error("Gagal mengambil data statistik publik");

    // 1. Update Highlight KPI Publik (Modus Paling Mengintai)
    if (data.kpi_insights && Array.isArray(data.kpi_insights) && data.kpi_insights.length > 0) {
      const kpi = data.kpi_insights[0];
      const elVal = document.getElementById("pub-kpi-1-val");
      const elDesc = document.getElementById("pub-kpi-1-desc");
      if (elVal && kpi.nilai) elVal.textContent = kpi.nilai;
      if (elDesc && kpi.insight) elDesc.textContent = kpi.insight;

      // Update growth badge (P0 Rekomendasi Publik)
      const elGrowth = document.getElementById("pub-kpi-1-growth");
      const elGrowthIcon = document.getElementById("pub-kpi-1-growth-icon");
      const elGrowthText = document.getElementById("pub-kpi-1-growth-text");
      if (elGrowth && kpi.growth_persen !== undefined) {
        const gw = kpi.growth_persen;
        const isUp = gw >= 0;
        const iconName = isUp ? 'trending_up' : 'trending_down';
        const colorClass = isUp ? 'text-[#00ff88]' : 'text-[#8892b0]';
        elGrowth.className = `inline-flex items-center gap-1 text-xs font-bold font-mono ${colorClass} whitespace-nowrap shrink-0`;
        if (elGrowthIcon) elGrowthIcon.textContent = iconName;
        if (elGrowthText) elGrowthText.textContent = `${isUp ? '+' : ''}${gw}% vs pekan lalu`;
      }
    }

    // 2. Render Word Cloud Kasus Insiden Spesifik (7 Hari Terkini)
    renderWordCloud(data.word_cloud || []);

    // 3. Render Chart Top Ancaman (Fakta Praktis 1 Kolom Penuh - Horizontal Pill Bar)
    renderChartAncaman(data.top_ancaman || []);

    // 4. Render Intisari Artikel Edukasi Nyata
    renderEdukasiList(data.edukasi_list || []);

  } catch (err) {
    console.error("Gagal memuat statistik publik:", err);
  }
}

/**
 * Palet warna cerah taktis neon cyber untuk latar belakang dark Cyber-HUD:
 * Cyan, Teal, Neon Green, Sky Blue, Soft Purple, Emerald, Amber, Pink, dan White.
 */
const PALET_WORDCLOUD_CYBER = [
  "#00d4ff", // Neon Cyan
  "#00ff88", // Tactical Teal
  "#00ff9d", // Cyber Neon Green
  "#7bbde8", // Sapphire Ice
  "#a78bfa", // Soft Purple Neon
  "#38bdf8", // Light Sky Blue
  "#34d399", // Emerald Light
  "#fbbf24", // Amber Glow
  "#f472b6", // Rose Neon
  "#e0f0ff", // Crisp Cyber White
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

  // Kata terbesar (giants) dikelompokkan rapat bersama-sama di tengah
  const centerCore = [];
  giants.forEach((item, idx) => {
    if (idx % 2 === 0) {
      centerCore.push(item);
    } else {
      centerCore.unshift(item);
    }
  });

  // Kata-kata sisanya (medium & kecil) dibagi rata ke sisi luar
  const outerLeft = [];
  const outerRight = [];
  remaining.forEach((item, idx) => {
    if (idx % 2 === 0) {
      outerLeft.push(item);
    } else {
      outerRight.push(item);
    }
  });

  return [...outerLeft, ...centerCore, ...outerRight];
}

/**
 * Render Word Cloud Kasus Insiden Spesifik
 * Mengadopsi tactical HUD chip styling ber-border tipis dengan pendaran neon saat hover
 */
function renderWordCloud(wordList) {
  const container = document.getElementById("pub-wordcloud-box");
  if (!container) return;

  if (!wordList || wordList.length === 0) {
    container.innerHTML = `<div class="text-xs font-mono text-[#7d8ca6]">Belum ada kata kunci insiden yang tercatat.</div>`;
    return;
  }

  const maxBobot = Math.max(...wordList.map((w) => w.bobot), 1);
  const minBobot = Math.min(...wordList.map((w) => w.bobot), 1);

  // Susun awan secara konsentris agar kata terbesar berada di tengah
  const clusteredWords = susunAwanOrganik(wordList);

  container.innerHTML = clusteredWords
    .map((item, idx) => {
      // Skala ukuran font & ketebalan dinamis
      const rasio = (item.bobot - minBobot) / (maxBobot - minBobot || 1);
      const fontSize = Math.round(12 + rasio * 22);
      
      let fontWeight = 600;
      let letterSpacing = "0.02em";
      if (item.bobot >= 40) {
        fontWeight = 800;
        letterSpacing = "0.04em";
      } else if (item.bobot >= 25) {
        fontWeight = 700;
      }

      const color = PALET_WORDCLOUD_CYBER[idx % PALET_WORDCLOUD_CYBER.length];
      const isAktif = kataTerpilih === item.kata.toLowerCase();

      const safeKata = escapeHtml(item.kata);
      const safeContoh = escapeHtml(item.contoh_judul || '');
      const safeSumber = escapeHtml(item.sumber || '');
      return `
        <button type="button"
          data-kata-raw="${safeKata}"
          data-contoh-judul="${safeContoh}"
          data-sumber="${safeSumber}"
          onclick="window.pilihWordCloud(this.getAttribute('data-kata-raw'), this)"
          data-kata="${safeKata.toLowerCase()}"
          style="font-size: clamp(${Math.round(fontSize * 0.75)}px, ${fontSize * 0.08}vw + 11px, ${fontSize}px); color: ${color}; font-weight: ${fontWeight}; letter-spacing: ${letterSpacing}; ${isAktif ? 'background-color: rgba(255, 51, 102, 0.18); border-color: #ff3366; box-shadow: 0 0 16px rgba(255,51,102,0.4); transform: scale(1.12); opacity: 1;' : ''}"
          class="wordcloud-item inline-block font-mono cursor-pointer transition-all duration-200 hover:scale-105 px-3 py-1 sm:py-1.5 leading-snug whitespace-nowrap select-none rounded-lg bg-[#0d2137]/80 border border-[#1a3a5c] hover:border-[#00d4ff] hover:shadow-[0_0_12px_rgba(0,212,255,0.3)] focus-visible:ring-2 focus-visible:ring-[#00d4ff] focus-visible:outline-none"
          title="Saring kasus: ${safeKata}">
          ${safeKata}
        </button>
      `;
    })
    .join("");

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
      item.style.transform = "scale(1.12)";
      item.style.backgroundColor = "rgba(255, 51, 102, 0.18)";
      item.style.borderColor = "#ff3366";
      item.style.boxShadow = "0 0 16px rgba(255, 51, 102, 0.4)";
      item.classList.add("z-10");
    } else {
      item.style.opacity = "0.35";
      item.style.transform = "scale(0.96)";
      item.style.backgroundColor = "rgba(13, 33, 55, 0.4)";
      item.style.borderColor = "#1a3a5c";
      item.style.boxShadow = "none";
      item.classList.remove("z-10");
    }
  });
}

// Interaktivitas: Memfilter berita di halaman Beranda berdasarkan kata kunci Word Cloud
window.pilihWordCloud = function (kata, btnEl = null) {
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
    labelActive.textContent = `[ MENYARING: "${kata.toUpperCase()}" ]`;
    labelActive.classList.remove("hidden");
  }

  // Sinkronkan ke input search feed beranda
  const berandaInput = document.getElementById("beranda-search-input");
  if (berandaInput) {
    berandaInput.value = kata;
  }

  // Update visual item awan kata
  sorotKataAktif(kataLower);

  // Filter kartu berita di tab beranda (mencakup berita lama dari seluruh pool 7 hari)
  if (window.filterBerandaCards) {
    window.filterBerandaCards(kataLower);
  }

  // Animasi gulir halus ke bawah menuju "Keamanan Siber Terbaru" + efek pendaran neon penanda
  setTimeout(() => {
    const anchor = document.getElementById("feed-beranda-anchor");
    const section = document.getElementById("feed-beranda-section");
    const targetEl = anchor || section;

    if (targetEl) {
      const headerOffset = 80;
      const targetPos = targetEl.getBoundingClientRect().top + window.pageYOffset - headerOffset;
      window.scrollTo({
        top: Math.max(0, targetPos),
        behavior: "smooth"
      });
    }

    if (section) {
      section.classList.remove("animate-target-highlight");
      void section.offsetWidth; // Force reflow
      section.classList.add("animate-target-highlight");
    }

    const cardsGrid = document.getElementById("beranda-cards-grid");
    if (cardsGrid) {
      cardsGrid.classList.remove("animate-target-highlight");
      void cardsGrid.offsetWidth; // Force reflow
      cardsGrid.classList.add("animate-target-highlight");
    }
  }, 120);
};

window.tutupWordCloudCallout = function () {
  const elCallout = document.getElementById("pub-wordcloud-callout");
  if (elCallout) elCallout.classList.add("hidden");
};

window.resetFilterWordCloud = function () {
  kataTerpilih = null;
  const btnReset = document.getElementById("pub-wordcloud-reset");
  if (btnReset) btnReset.classList.add("hidden");

  const labelActive = document.getElementById("pub-wordcloud-active-label");
  if (labelActive) labelActive.classList.add("hidden");

  window.tutupWordCloudCallout();

  const berandaInput = document.getElementById("beranda-search-input");
  if (berandaInput && berandaInput.value) {
    berandaInput.value = "";
  }

  // Pulihkan seluruh kata ke kondisi normal
  const items = document.querySelectorAll("#pub-wordcloud-box .wordcloud-item");
  items.forEach((item) => {
    item.style.opacity = "1";
    item.style.transform = "scale(1)";
    item.style.backgroundColor = "rgba(13, 33, 55, 0.8)";
    item.style.borderColor = "#1a3a5c";
    item.style.boxShadow = "none";
    item.classList.remove("z-10");
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
    countBadge.textContent = `[ ${edukasiList ? edukasiList.length : 0} Panduan ]`;
  }

  if (!edukasiList || edukasiList.length === 0) {
    container.innerHTML = `<div class="col-span-full py-8 text-center text-xs font-mono text-[#7d8ca6]">Belum ada artikel edukasi dalam 7 hari terakhir.</div>`;
    return;
  }

  container.innerHTML = edukasiList
    .map((item) => {
      const tanggalFormat = item.tanggal ? item.tanggal.slice(0, 10) : "Terkini";
      const sumberLengkap = item.sumber
        ? `${item.sumber} • ${tanggalFormat}`
        : tanggalFormat;

      // Simpan seluruh data lengkap (rangkuman & metadata) ke registry modal
      const idx = simpanItemModal({
        judul: item.judul,
        sumber: sumberLengkap,
        link: item.link || '',
        teksLengkap: item.ringkasan || "Tidak ada rangkuman detail tersedia.",
        pillClass: 'bg-[#0d2137] text-[#00ff88] border border-[#00ff88]/40 font-mono',
        pillLabel: '[ Edukasi Keamanan ]'
      });

      return `
        <button type="button" 
          onclick="window.bukaModal ? window.bukaModal(${idx}) : bukaModal(${idx})"
          class="w-full text-left bg-[#0d2137]/80 hover:bg-[#0d2137] border border-[#1a3a5c] hover:border-[#00d4ff]/50 p-3 sm:p-3.5 rounded-xl transition-all flex items-center justify-between gap-3 group cursor-pointer shadow-sm hover:shadow-[0_0_15px_rgba(0,212,255,0.2)] active:scale-[0.99] focus-visible:ring-2 focus-visible:ring-[#00d4ff] focus-visible:outline-none"
          title="Klik untuk membaca rangkuman dan informasi lengkap">
          <span class="font-semibold text-xs sm:text-sm text-[#e0f0ff] group-hover:text-[#00d4ff] transition-colors line-clamp-2 leading-snug min-w-0 pr-2 font-['Sora'] break-words overflow-hidden">
            ${escapeHtml(item.judul)}
          </span>
          <span class="material-symbols-outlined text-[#7d8ca6] group-hover:text-[#00d4ff] text-base sm:text-lg shrink-0 transition-transform group-hover:translate-x-0.5" aria-hidden="true">
            arrow_forward
          </span>
        </button>
      `;
    })
    .join("");
}

/**
 * Render Chart Top Ancaman (Horizontal Pill Bar Chart - Cyber-HUD Style)
 */
function renderChartAncaman(topAncaman) {
  const ctx = document.getElementById("chart-ancaman-publik");
  if (!ctx) return;

  if (chartAncaman) chartAncaman.destroy();

  const labels = topAncaman.map((a) => a.kategori);
  const values = topAncaman.map((a) => a.jumlah);
  const totalKasus = values.reduce((a, b) => a + b, 0) || 1;

  // Horizontal gradient: Cyan (#00d4ff) to Teal (#00ff88)
  const canvasCtx = ctx.getContext('2d');
  let barGradient = '#00d4ff';
  if (canvasCtx) {
    const g = canvasCtx.createLinearGradient(0, 0, 450, 0);
    g.addColorStop(0, '#00d4ff');
    g.addColorStop(1, '#00ff88');
    barGradient = g;
  }

  chartAncaman = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Jumlah Laporan",
          data: values,
          backgroundColor: barGradient,
          borderRadius: 9999, // Pill bar
          borderSkipped: false,
          barThickness: 16,
        },
      ],
    },
    options: {
      indexAxis: 'y', // Horizontal Pill Bar Chart
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "rgba(10, 22, 40, 0.95)",
          borderColor: "#1a3a5c",
          borderWidth: 1,
          titleColor: "#00d4ff",
          bodyColor: "#e0f0ff",
          titleFont: { family: "'Fragment Mono', 'Share Tech Mono', monospace", size: 12, weight: "bold" },
          bodyFont: { family: "'Sora', sans-serif", size: 11 },
          padding: 10,
          callbacks: {
            label: (ctx) => {
              const val = ctx.parsed.x;
              const pct = Math.round((val / totalKasus) * 100);
              return ` ${val} Kasus Terlaporkan (${pct}% dari total)`;
            },
          },
        },
      },
      scales: {
        x: {
          beginAtZero: true,
          grid: { color: "rgba(26, 58, 92, 0.4)" },
          ticks: {
            font: { family: "'Fragment Mono', 'Share Tech Mono', monospace", size: 10 },
            color: "#8892b0",
            precision: 0,
          },
        },
        y: {
          grid: { display: false },
          ticks: {
            font: { family: "'Sora', sans-serif", size: 11, weight: "600" },
            color: "#e0f0ff",
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
          borderColor: "#00d4ff",
          backgroundColor: "rgba(0, 212, 255, 0.12)",
          fill: true,
          tension: 0.35,
          pointBackgroundColor: (ctx) => {
            const val = ctx.raw;
            return (val >= avgBerita * 1.8 && val > 2) ? "#ff3366" : "#00d4ff";
          },
          pointRadius: (ctx) => {
            const val = ctx.raw;
            return (val >= avgBerita * 1.8 && val > 2) ? 6 : 4;
          },
          pointHoverRadius: 7,
          borderWidth: 2,
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
            font: { family: "'Fragment Mono', monospace", size: 11, weight: "600" },
            color: "#e0f0ff",
          },
        },
        tooltip: {
          backgroundColor: "rgba(10, 22, 40, 0.95)",
          borderColor: "#1a3a5c",
          borderWidth: 1,
          titleFont: { family: "'Fragment Mono', monospace", size: 12, weight: "bold" },
          bodyFont: { family: "'Sora', sans-serif", size: 11 },
          padding: 10,
          boxPadding: 4,
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(26, 58, 92, 0.4)" },
          ticks: {
            font: { family: "'Fragment Mono', monospace", size: 10 },
            color: "#8892b0",
          },
        },
        y: {
          beginAtZero: true,
          grid: { color: "rgba(26, 58, 92, 0.4)" },
          ticks: {
            font: { family: "'Fragment Mono', monospace", size: 10 },
            color: "#8892b0",
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
          backgroundColor: ["#00d4ff", "#00ff88"],
          borderWidth: 2,
          borderColor: "#0a1628",
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
          backgroundColor: "rgba(10, 22, 40, 0.95)",
          borderColor: "#1a3a5c",
          borderWidth: 1,
          titleFont: { family: "'Fragment Mono', monospace", size: 12, weight: "bold" },
          bodyFont: { family: "'Sora', sans-serif", size: 11 },
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
