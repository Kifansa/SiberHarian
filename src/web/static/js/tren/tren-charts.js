import { escapeHtml } from './tren-utils.js';

/**
 * Modul visualisasi analitik untuk Tab Tren (CSIRT Jatim Cyber-HUD Style)
 */

let chartRadarVektor = null;
let chartSektorTarget = null;
let chartKomposisiAdmin = null;

export function destroyCharts() {
  if (chartRadarVektor && typeof chartRadarVektor.destroy === 'function') {
    chartRadarVektor.destroy();
    chartRadarVektor = null;
  }
  if (chartSektorTarget && typeof chartSektorTarget.destroy === 'function') {
    chartSektorTarget.destroy();
    chartSektorTarget = null;
  }
  if (chartKomposisiAdmin && typeof chartKomposisiAdmin.destroy === 'function') {
    chartKomposisiAdmin.destroy();
    chartKomposisiAdmin = null;
  }
}

/**
 * Merender analitik visual: Vektor Serangan Siber (TTPs), Sektor Vital Terpapar (IIV), dan Komposisi Cakupan Media
 * @param {Object} stat Objek data statistik tren
 */
export function renderCharts(stat) {
  if (!stat) return;

  // Bersihkan grafik sebelumnya
  destroyCharts();

  // 1. Distribusi Vektor Serangan Siber (TTPs) - Horizontal Progress Bar ala Desain CSIRT Jatim
  const elRadar = document.getElementById('chart-radar-vektor') || document.getElementById('chart-vektor-serangan');
  if (elRadar) {
    let containerRadar = elRadar;
    if (containerRadar.tagName === 'CANVAS') {
      const div = document.createElement('div');
      div.id = containerRadar.id;
      div.className = 'space-y-4 pt-1';
      containerRadar.parentNode.replaceChild(div, containerRadar);
      containerRadar = div;
    }

    const vektorList = stat.vektor_serangan || [];
    let displayList = vektorList.filter(d => d.jumlah > 0);
    if (displayList.length === 0) {
      displayList = vektorList.slice(0, 6);
    } else {
      displayList = displayList.slice(0, 6);
    }

    if (!displayList.length) {
      containerRadar.innerHTML = `<div class="text-[#7d8ca6] text-xs py-8 text-center font-mono">Belum ada data vektor serangan untuk rentang waktu ini.</div>`;
    } else {
      const maxJumlah = Math.max(...displayList.map(d => d.jumlah), 1);

      const totalVektor = displayList.reduce((acc, curr) => acc + curr.jumlah, 0) || 1;
      const topVektor = displayList[0];
      const pctVektor = Math.round((topVektor.jumlah / totalVektor) * 100);

      const barsHtml = displayList.map((item) => {
        const widthPct = item.jumlah > 0 ? Math.max(Math.min(Math.round((item.jumlah / maxJumlah) * 100), 100), 3) : 0;

        return `
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs font-mono gap-2">
              <div class="min-w-0 flex-1">
                <span class="text-[#e0f0ff] font-['Sora'] font-medium block truncate" title="${escapeHtml(item.vektor)}">${escapeHtml(item.vektor)}</span>
              </div>
              <div class="shrink-0 font-bold text-[#00d4ff] whitespace-nowrap">
                ${item.jumlah} artikel
              </div>
            </div>
            <div class="w-full bg-[#0d2137] rounded-full h-3 overflow-hidden border border-[#1a3a5c]">
              <div class="h-full rounded-full transition-all duration-700 ease-out shadow-[0_0_8px_rgba(0,212,255,0.4)]" style="width: ${widthPct}%; background: linear-gradient(90deg, #00d4ff 0%, #00ff88 100%);"></div>
            </div>
          </div>
        `;
      }).join('');

      const insightHtml = `
        <div class="mt-4 pt-3 border-t border-[#1a3a5c]/60 flex items-start gap-2 text-[11px] font-mono text-[#8892b0]">
          <span class="material-symbols-outlined text-sm text-[#00d4ff] shrink-0 mt-0.5">tips_and_updates</span>
          <span><strong class="text-[#00d4ff]">${escapeHtml(topVektor.vektor)}</strong> mendominasi ${pctVektor}% dari seluruh indikasi vektor serangan aktif.</span>
        </div>
      `;

      containerRadar.innerHTML = barsHtml + insightHtml;
    }
  }

  // 2. Sektor Industri Target Terpapar - Horizontal Progress Bar ala Desain CSIRT Jatim
  const elSektor = document.getElementById('chart-sektor-target');
  if (elSektor) {
    let containerSektor = elSektor;
    if (containerSektor.tagName === 'CANVAS') {
      const div = document.createElement('div');
      div.id = containerSektor.id;
      div.className = 'space-y-4 pt-1';
      containerSektor.parentNode.replaceChild(div, containerSektor);
      containerSektor = div;
    }

    const sektorList = stat.sektor_target || [];
    let displayList = sektorList.filter(d => d.jumlah > 0);
    if (displayList.length === 0) {
      displayList = sektorList.slice(0, 5);
    } else {
      displayList = displayList.slice(0, 5);
    }

    if (!displayList.length) {
      containerSektor.innerHTML = `<div class="text-[#7d8ca6] text-xs py-8 text-center font-mono">Belum ada data sektor industri untuk rentang waktu ini.</div>`;
    } else {
      const maxSektor = Math.max(...displayList.map(d => d.jumlah), 1);
      const totalInsiden = stat.total_berita || displayList.reduce((acc, curr) => acc + curr.jumlah, 0) || 1;
      const topSektor = displayList[0];
      const pctTopSektor = Math.round((topSektor.jumlah / totalInsiden) * 100);

      const barsHtml = displayList.map((item) => {
        const widthPct = item.jumlah > 0 ? Math.max(Math.min(Math.round((item.jumlah / maxSektor) * 100), 100), 3) : 0;
        const pctInsiden = Math.round((item.jumlah / totalInsiden) * 100);

        return `
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs font-mono gap-2">
              <div class="min-w-0 flex-1">
                <span class="text-[#e0f0ff] font-['Sora'] font-medium block truncate" title="${escapeHtml(item.sektor)}">${escapeHtml(item.sektor)}</span>
              </div>
              <div class="shrink-0 font-bold text-[#00ff88] whitespace-nowrap">
                ${item.jumlah} insiden <span class="font-normal text-[11px] text-[#7d8ca6]">(${pctInsiden}%)</span>
              </div>
            </div>
            <div class="w-full bg-[#0d2137] rounded-full h-3 overflow-hidden border border-[#1a3a5c]">
              <div class="h-full rounded-full transition-all duration-700 ease-out shadow-[0_0_8px_rgba(0,255,136,0.4)]" style="width: ${widthPct}%; background: linear-gradient(90deg, #00ff88 0%, #00d4ff 100%);"></div>
            </div>
          </div>
        `;
      }).join('');

      const insightHtml = `
        <div class="mt-4 pt-3 border-t border-[#1a3a5c]/60 flex items-start gap-2 text-[11px] font-mono text-[#8892b0]">
          <span class="material-symbols-outlined text-sm text-[#00ff88] shrink-0 mt-0.5">shield</span>
          <span><strong class="text-[#00ff88]">${escapeHtml(topSektor.sektor)}</strong> mencatat konsentrasi paparan tertinggi (${topSektor.jumlah} insiden, ${pctTopSektor}%).</span>
        </div>
      `;

      containerSektor.innerHTML = barsHtml + insightHtml;
    }
  }

  // 3. Cakupan Media Pelapor Admin (P0 Admin)
  if (stat.nasional_vs_internasional) {
    renderChartKomposisiAdmin(stat.nasional_vs_internasional, stat.total_berita);
  }
}

export function renderChartKomposisiAdmin(nasVsIntl, totalBerita) {
  const ctx = document.getElementById('chart-komposisi-admin');
  if (!ctx || !nasVsIntl) return;

  if (chartKomposisiAdmin && typeof chartKomposisiAdmin.destroy === 'function') {
    chartKomposisiAdmin.destroy();
  }

  const nas = nasVsIntl.nasional || 0;
  const intl = nasVsIntl.internasional || 0;
  const total = nas + intl || totalBerita || 1;
  const pctNas = Math.round((nas / total) * 100);
  const pctIntl = 100 - pctNas;

  const elNas = document.getElementById('admin-cakupan-nasional-val');
  const elGlobal = document.getElementById('admin-cakupan-global-val');
  if (elNas) elNas.textContent = `${nas} insiden (${pctNas}%)`;
  if (elGlobal) elGlobal.textContent = `${intl} insiden (${pctIntl}%)`;

  chartKomposisiAdmin = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Isu Nasional', 'Isu Global / CTI'],
      datasets: [
        {
          data: [nas, intl],
          backgroundColor: ['#00d4ff', '#00ff88'],
          borderWidth: 2,
          borderColor: '#0a1628',
          hoverOffset: 4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '68%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(10, 22, 40, 0.95)',
          borderColor: '#1a3a5c',
          borderWidth: 1,
          titleFont: { family: "'Fragment Mono', monospace", size: 12, weight: 'bold' },
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
