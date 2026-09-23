/**
 * Modul Frontend untuk Statistik & Edukasi Publik (SiberHarian - CSIRT Jatim)
 * Menyajikan:
 * 1. Insightful KPI Cards (Wawasan bermakna berbasis data riil)
 * 2. Word Cloud Kasus Insiden Spesifik (Interaktif, filter berita langsung)
 * 3. Grafik Fakta Siber (Top Ancaman & Software Populer Terpapar)
 * 4. Daftar Intisari Artikel Edukasi Nyata dari Database
 */

import { simpanItemModal } from './modal.js';

let chartAncaman = null;
let chartVendor = null;
let kataTerpilih = null;


export async function muatTabStatistikPublik() {
  try {
    const res = await fetch("/api/statistik-publik");
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();

    if (data.status !== "ok") throw new Error("Gagal mengambil data statistik publik");

    // 1. Update 4 Insightful KPI Cards
    if (data.kpi_insights && data.kpi_insights.length >= 4) {
      const kpis = data.kpi_insights;
      
      const elVal1 = document.getElementById("pub-kpi-1-val");
      const elDesc1 = document.getElementById("pub-kpi-1-desc");
      if (elVal1) elVal1.textContent = kpis[0].nilai;
      if (elDesc1) elDesc1.textContent = kpis[0].insight;

      const elVal2 = document.getElementById("pub-kpi-2-val");
      const elDesc2 = document.getElementById("pub-kpi-2-desc");
      if (elVal2) elVal2.textContent = kpis[1].nilai;
      if (elDesc2) elDesc2.textContent = kpis[1].insight;

      const elVal3 = document.getElementById("pub-kpi-3-val");
      const elDesc3 = document.getElementById("pub-kpi-3-desc");
      if (elVal3) elVal3.textContent = kpis[2].nilai;
      if (elDesc3) elDesc3.textContent = kpis[2].insight;

      const elVal4 = document.getElementById("pub-kpi-4-val");
      const elDesc4 = document.getElementById("pub-kpi-4-desc");
      if (elVal4) elVal4.textContent = kpis[3].nilai;
      if (elDesc4) elDesc4.textContent = kpis[3].insight;
    }

    // 2. Render Word Cloud Kasus Insiden Spesifik
    renderWordCloud(data.word_cloud || []);

    // 3. Render Chart Top Ancaman & Software Terpapar
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
 * Susun kata kunci ke dalam struktur awan organik (Archimedean clustering):
 * Menempatkan kata raksasa di zona tengah berdampingan dengan kata sedang/kecil,
 * serta kata-kata sedang dan kecil membingkai bagian atas dan bawah awan.
 */
function susunAwanOrganik(wordList) {
  if (!wordList || wordList.length <= 4) return wordList;

  const sorted = [...wordList].sort((a, b) => b.bobot - a.bobot);

  const giant = sorted.slice(0, 5);      // Top 5 kata terbesar (centerpiece)
  const large = sorted.slice(5, 12);     // Kata-kata besar penyeimbang
  const medium = sorted.slice(12, 21);   // Kata-kata menengah
  const small = sorted.slice(21);        // Kata-kata kecil pengisi rongga

  const topCluster = [];
  const centerCluster = [];
  const bottomCluster = [];

  // Frame atas awan
  while (topCluster.length < 7 && (small.length > 0 || medium.length > 0)) {
    if (small.length > 0) topCluster.push(small.pop());
    if (medium.length > 0) topCluster.push(medium.shift());
  }

  // Jantung awan (kata raksasa bersanding dengan kata sedang & kecil)
  while (giant.length > 0) {
    if (large.length > 0) centerCluster.push(large.shift());
    centerCluster.push(giant.shift());
    if (small.length > 0) centerCluster.push(small.shift());
    if (giant.length > 0) centerCluster.push(giant.shift());
    if (large.length > 0) centerCluster.push(large.shift());
  }

  // Frame bawah awan
  while (large.length > 0 || medium.length > 0 || small.length > 0) {
    if (medium.length > 0) bottomCluster.push(medium.shift());
    if (large.length > 0) bottomCluster.push(large.shift());
    if (small.length > 0) bottomCluster.push(small.pop());
  }

  return [...topCluster, ...centerCluster, ...bottomCluster].filter(Boolean);
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
      return `
        <button type="button"
          onclick="window.pilihWordCloud('${item.kata}')"
          data-kata="${item.kata.toLowerCase()}"
          style="font-size: clamp(${Math.round(fontSize * 0.72)}px, ${fontSize * 0.08}vw + 12px, ${fontSize}px); color: ${color}; font-weight: ${fontWeight}; letter-spacing: ${letterSpacing}; ${isAktif ? 'text-decoration: underline; text-underline-offset: 6px; text-decoration-thickness: 3px; transform: scale(1.2); opacity: 1;' : ''}"
          class="wordcloud-item inline-block font-sans cursor-pointer transition-all duration-200 hover:scale-115 p-1 leading-none whitespace-nowrap select-none focus-visible:outline-none"
          title="Kasus: ${item.kata}">
          ${item.kata}
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
      item.style.transform = "scale(1.2)";
      item.style.textDecoration = "underline";
      item.style.textUnderlineOffset = "6px";
      item.style.textDecorationThickness = "3px";
      item.classList.add("z-10");
    } else {
      item.style.opacity = "0.32";
      item.style.transform = "scale(0.95)";
      item.style.textDecoration = "none";
      item.classList.remove("z-10");
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

  // Update visual item awan kata
  sorotKataAktif(kataLower);

  // Filter kartu berita di tab beranda
  if (window.filterBerandaCards) {
    window.filterBerandaCards(kataLower);
  }

  // Scroll halus ke area kartu berita
  const feedContainer = document.getElementById("card-container");
  if (feedContainer) {
    feedContainer.scrollIntoView({ behavior: "smooth", block: "start" });
  }
};

window.resetFilterWordCloud = function () {
  kataTerpilih = null;
  const btnReset = document.getElementById("pub-wordcloud-reset");
  if (btnReset) btnReset.classList.add("hidden");

  const labelActive = document.getElementById("pub-wordcloud-active-label");
  if (labelActive) labelActive.classList.add("hidden");

  // Pulihkan seluruh kata ke kondisi normal
  const items = document.querySelectorAll("#pub-wordcloud-box .wordcloud-item");
  items.forEach((item) => {
    item.style.opacity = "1";
    item.style.transform = "scale(1)";
    item.style.textDecoration = "none";
    item.classList.remove("z-10");
  });

  if (window.filterBerandaCards) {
    window.filterBerandaCards("");
  }
};

/**
 * Render Intisari Artikel Edukasi Nyata dari Database
 */
function renderEdukasiList(edukasiList) {
  const container = document.getElementById("pub-edukasi-grid");
  if (!container) return;

  if (!edukasiList || edukasiList.length === 0) {
    container.innerHTML = `<div class="col-span-full py-8 text-center text-xs text-[#49769F]">Belum ada artikel edukasi terverifikasi.</div>`;
    return;
  }

  container.innerHTML = edukasiList
    .map((item) => {
      // Batasi ringkasan
      const shortDesc = item.ringkasan && item.ringkasan.length > 170
        ? item.ringkasan.slice(0, 170) + "..."
        : item.ringkasan || "Tidak ada ringkasan.";

      const tanggalFormat = item.tanggal ? item.tanggal.slice(0, 10) : "Terkini";
      const idx = simpanItemModal({
        judul: item.judul,
        sumber: item.sumber || "CSIRT Jatim",
        link: item.link || '',
        teksLengkap: item.ringkasan || shortDesc,
        pillClass: 'bg-[#EEF5FA] text-[#0A4174] border border-[#BDD8E9]',
        pillLabel: 'Edukasi'
      });

      return `
        <div class="bg-[#EEF5FA] rounded-lg border border-[#BDD8E9]/80 p-4 sm:p-5 flex flex-col justify-between shadow-2xs hover:shadow-xs transition-shadow">
          <div>
            <div class="flex items-center justify-between gap-2 mb-2 text-[11px] text-[#49769F]">
              <span class="font-semibold text-[#0A4174] truncate max-w-[180px]">${item.sumber || "CSIRT Jatim"}</span>
              <span class="font-mono">${tanggalFormat}</span>
            </div>
            <h4 class="font-bold text-sm text-[#001D39] leading-snug mb-2 hover:text-[#0A4174] transition-colors">
              ${item.judul}
            </h4>
            <p class="text-xs text-slate-600 leading-relaxed">
              ${shortDesc}
            </p>
          </div>

          <div class="mt-4 pt-3 border-t border-[#BDD8E9]/60 flex items-center justify-between">
            <button type="button" onclick="window.bukaModal ? window.bukaModal(${idx}) : bukaModal(${idx})"
              class="text-xs font-bold text-[#0A4174] hover:underline flex items-center gap-1 cursor-pointer">
              <span>Baca Intisari</span>
              <span class="material-symbols-outlined text-sm">arrow_forward</span>
            </button>
            ${
              item.link && item.link !== "#"
                ? `<a href="${item.link}" target="_blank" rel="noopener noreferrer" class="text-[11px] text-[#49769F] hover:text-[#001D39] flex items-center gap-0.5" title="Buka sumber media asli">
                    <span>Sumber Asli</span>
                    <span class="material-symbols-outlined text-xs">open_in_new</span>
                   </a>`
                : ""
            }
          </div>
        </div>
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
            label: (ctx) => ` ${ctx.parsed.y} Kasus Terlaporkan`,
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
            label: (ctx) => ` ${ctx.parsed.x} Celah Kerentanan Kritis`,
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

window.muatTabStatistikPublik = muatTabStatistikPublik;
