import { ambilTren } from './api.js';
import { animateNumber, tampilkanToast, formatWaktuSekarang, formatTanggalSingkat, formatTanggalIndonesia } from './utils.js';

let sudahDimuat = false;

// Global chart instances untuk cleanup
let chartKataKunci = null;
let chartVendorCve = null;
let chartHarian = null;
let chartCvss = null;
let chartSumber = null;
let chartNasIntl = null;
let chartJenis = null;
let chartHarianSumber = null;
let chartRadarVektor = null;
let chartSektorTarget = null;

// Expose tab switcher pada window SEGERA agar tombol selalu bisa dipencet!
window.tampilAiTab = function (tab) {
  const btnBerita = document.getElementById('tab-ai-berita-btn');
  const btnCve = document.getElementById('tab-ai-cve-btn');
  const boxBerita = document.getElementById('ai-tab-berita');
  const boxCve = document.getElementById('ai-tab-cve');

  if (!btnBerita || !btnCve || !boxBerita || !boxCve) return;

  if (tab === 'berita') {
    boxBerita.classList.remove('hidden');
    boxCve.classList.add('hidden');
    btnBerita.className = 'px-3 py-1 rounded-md text-xs font-semibold transition-all bg-primary text-white shadow-xs cursor-pointer';
    btnCve.className = 'px-3 py-1 rounded-md text-xs font-semibold transition-all text-slate-600 hover:text-slate-900 cursor-pointer';
  } else {
    boxBerita.classList.add('hidden');
    boxCve.classList.remove('hidden');
    btnCve.className = 'px-3 py-1 rounded-md text-xs font-semibold transition-all bg-google-red text-white shadow-xs cursor-pointer';
    btnBerita.className = 'px-3 py-1 rounded-md text-xs font-semibold transition-all text-slate-600 hover:text-slate-900 cursor-pointer';
  }
};

export async function muatTabTren(isManualReload = false) {
  if (sudahDimuat && !isManualReload) return;

  const trenDesc = document.getElementById('tren-desc');
  const trenEmptyState = document.getElementById('tren-empty-state');
  const trenKontenContainer = document.getElementById('tren-konten-container');
  const btnRefresh = document.getElementById('btn-refresh-tren');
  const btnRefreshIcon = document.getElementById('btn-refresh-tren-icon');
  const btnRefreshText = document.getElementById('btn-refresh-tren-text');

  // Set visual feedback saat reload manual
  if (isManualReload) {
    if (btnRefresh) {
      btnRefresh.disabled = true;
      btnRefresh.classList.add('opacity-70', 'cursor-not-allowed');
    }
    if (btnRefreshIcon) {
      btnRefreshIcon.classList.add('animate-spin');
    }
    if (btnRefreshText) {
      btnRefreshText.textContent = 'Memperbarui...';
    }
    if (trenKontenContainer && !trenKontenContainer.classList.contains('hidden')) {
      trenKontenContainer.classList.add('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
    }
    if (trenDesc) {
      trenDesc.textContent = 'Memperbarui data tren siber...';
    }
  }

  try {
    // Beri jeda minimal 500ms saat reload manual agar animasi spin & transisi terlihat jelas
    const [data] = await Promise.all([
      ambilTren(),
      isManualReload ? new Promise(r => setTimeout(r, 500)) : Promise.resolve()
    ]);
    sudahDimuat = true;

    if (!data || data.status !== 'ok') {
      if (trenEmptyState) trenEmptyState.classList.remove('hidden');
      if (trenKontenContainer) trenKontenContainer.classList.add('hidden');
      return;
    }

    if (trenEmptyState) trenEmptyState.classList.add('hidden');
    if (trenKontenContainer) {
      trenKontenContainer.classList.remove('hidden');
      // Kembalikan efek opacity dan skala kontainer
      trenKontenContainer.classList.remove('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
      trenKontenContainer.classList.add('opacity-100', 'scale-100');
    }

    if (trenDesc) {
      trenDesc.textContent = `Diperbarui pada ${formatWaktuSekarang()}`;
    }

    // 1. Render Prediksi Tren Cards (Executive Summary)
    const containerBerita = document.getElementById('prediksi-berita-cards');
    const containerCve = document.getElementById('prediksi-cve-cards');
    if (containerBerita) {
      renderLaporanCards(containerBerita, data.prediksi_berita, 'berita');
    }
    if (containerCve) {
      renderLaporanCards(containerCve, data.prediksi_cve, 'cve');
    }

    // Attach event listeners ke tombol tab secara langsung
    const btnBerita = document.getElementById('tab-ai-berita-btn');
    const btnCve = document.getElementById('tab-ai-cve-btn');
    if (btnBerita) btnBerita.onclick = () => window.tampilAiTab('berita');
    if (btnCve) btnCve.onclick = () => window.tampilAiTab('cve');

    // 2. Render KPI Scorecards & Tables
    const stat = data.statistik;
    if (stat) {
      renderKpiCards(stat, isManualReload);
      renderTables(stat);
      
      // 3. Render Chart.js secara terisolasi
      setTimeout(() => {
        try {
          renderCharts(stat);
        } catch (errChart) {
          console.error('Gagal merender chart tren:', errChart);
        }
      }, 50);

      // Flash highlight pada kartu dashboard
      if (isManualReload) {
        flashUpdatedCards();
      }
    }

    // Selesai reload: beri feedback sukses
    if (isManualReload) {
      if (btnRefreshIcon) {
        btnRefreshIcon.classList.remove('animate-spin');
        btnRefreshIcon.textContent = 'check_circle';
        btnRefreshIcon.classList.add('text-google-green');
      }
      if (btnRefreshText) {
        btnRefreshText.textContent = 'Data Terkini!';
        btnRefreshText.classList.add('text-google-green');
      }
      tampilkanToast('Data tren keamanan siber berhasil diperbarui');

      setTimeout(() => {
        if (btnRefreshIcon) {
          btnRefreshIcon.textContent = 'refresh';
          btnRefreshIcon.classList.remove('text-google-green');
        }
        if (btnRefreshText) {
          btnRefreshText.textContent = 'Muat Ulang Data';
          btnRefreshText.classList.remove('text-google-green');
        }
        if (btnRefresh) {
          btnRefresh.disabled = false;
          btnRefresh.classList.remove('opacity-70', 'cursor-not-allowed');
        }
      }, 1500);
    }
  } catch (err) {
    console.error('Error saat memuat tab tren:', err);
    sudahDimuat = false;
    if (isManualReload) {
      tampilkanToast('Gagal memperbarui data tren siber', 'error');
      if (btnRefreshIcon) {
        btnRefreshIcon.classList.remove('animate-spin');
        btnRefreshIcon.textContent = 'refresh';
      }
      if (btnRefreshText) {
        btnRefreshText.textContent = 'Muat Ulang Data';
      }
      if (btnRefresh) {
        btnRefresh.disabled = false;
        btnRefresh.classList.remove('opacity-70', 'cursor-not-allowed');
      }
      if (trenKontenContainer) {
        trenKontenContainer.classList.remove('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
      }
    }
  }
}

export function muatUlangTabTren() {
  sudahDimuat = false;
  return muatTabTren(true);
}

// Expose fungsi ke window
window.muatTabTren = muatTabTren;
window.muatUlangTabTren = muatUlangTabTren;

function renderLaporanCards(container, rawText, defaultType = 'berita') {
  if (!container) return;
  if (!rawText || !rawText.trim()) {
    container.innerHTML = '<div class="text-slate-500 text-sm italic col-span-full py-6 text-center">Belum ada data ringkasan yang tercatat.</div>';
    return;
  }

  function isMainSectionHeader(line) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.length > 75) return { isHeader: false, cleanTitle: '' };
    if (trimmed.endsWith(':') || trimmed.endsWith('.')) return { isHeader: false, cleanTitle: '' };

    const isMarked = (trimmed.startsWith('**') && trimmed.endsWith('**')) ||
                     trimmed.startsWith('#') ||
                     /^\d+[\.\)]\s+/.test(trimmed) ||
                     (trimmed.length > 4 && trimmed === trimmed.toUpperCase() && !trimmed.startsWith('*'));
    if (!isMarked) return { isHeader: false, cleanTitle: '' };

    const clean = trimmed
      .replace(/^(?:\d+[\.\)]\s*)?([🌐🎯🔗🛡️⚡📋🚨📊🔴]\s*)?/, '')
      .replace(/^\*+|\*+$/g, '')
      .replace(/^#+/, '')
      .trim();

    if (/^prioritas\s*(?:1|2|patching)/i.test(clean) || /^mitigasi\s*sementara/i.test(clean) || /^workaround/i.test(clean)) {
      return { isHeader: false, cleanTitle: '' };
    }

    const mainKeywords = [
      'LANSKAP', 'POLA ANCAMAN', 'VEKTOR SERANGAN', 'SEKTOR TERPAPAR',
      'KORELASI', 'MATRIKS MITIGASI', 'REKOMENDASI ANTISIPASI',
      'VENDOR & PRODUK', 'VENDOR', 'ANALISIS VEKTOR', 'EKSPLOITASI & DAMPAK',
      'PANDUAN PATCHING', 'PRIORITAS PATCHING & MITIGASI'
    ];

    for (const kw of mainKeywords) {
      if (clean.toUpperCase().includes(kw)) {
        return { isHeader: true, cleanTitle: clean };
      }
    }

    return { isHeader: false, cleanTitle: '' };
  }

  const lines = rawText.trim().split('\n');
  const sections = [];
  let currentTitle = '';
  let currentLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const { isHeader, cleanTitle } = isMainSectionHeader(line);

    if (isHeader) {
      if (currentTitle || currentLines.length > 0) {
        sections.push({ title: currentTitle || 'Ringkasan', lines: currentLines });
      }
      currentTitle = cleanTitle;
      currentLines = [];
    } else {
      currentLines.push(line);
    }
  }

  if (currentTitle || currentLines.length > 0) {
    sections.push({ title: currentTitle || 'Ringkasan', lines: currentLines });
  }

  if (sections.length === 0) {
    sections.push({ title: defaultType === 'berita' ? 'Ringkasan Intelijen Berita' : 'Prioritas Kerentanan CVE', lines: lines });
  }

  function getSectionMeta(title) {
    const t = title.toLowerCase();
    if (t.includes('lanskap') || t.includes('pola')) {
      return { icon: 'public', border: 'border-blue-200', badgeBg: 'bg-blue-100 text-blue-800' };
    }
    if (t.includes('vektor') || t.includes('sektor') || t.includes('ttp')) {
      return { icon: 'track_changes', border: 'border-amber-200', badgeBg: 'bg-amber-100 text-amber-900' };
    }
    if (t.includes('korelasi')) {
      return { icon: 'hub', border: 'border-indigo-200', badgeBg: 'bg-indigo-100 text-indigo-900' };
    }
    if (t.includes('mitigasi') || t.includes('rekomendasi') || t.includes('matriks')) {
      return { icon: 'security', border: 'border-emerald-200', badgeBg: 'bg-emerald-100 text-emerald-900' };
    }
    if (t.includes('vendor') || t.includes('produk')) {
      return { icon: 'verified_user', border: 'border-red-200', badgeBg: 'bg-red-100 text-google-red' };
    }
    if (t.includes('eksploitasi') || t.includes('dampak')) {
      return { icon: 'bolt', border: 'border-amber-200', badgeBg: 'bg-amber-100 text-amber-900' };
    }
    if (t.includes('patching') || t.includes('panduan')) {
      return { icon: 'build_circle', border: 'border-emerald-200', badgeBg: 'bg-emerald-100 text-emerald-900' };
    }
    return { icon: 'article', border: 'border-slate-200', badgeBg: 'bg-slate-100 text-slate-800' };
  }

  function formatBodyHtml(linesArr) {
    let html = '';
    let inList = false;

    for (let i = 0; i < linesArr.length; i++) {
      const raw = linesArr[i];
      const trimmed = raw.trim();
      if (!trimmed) {
        if (inList) { html += '</ul>'; inList = false; }
        continue;
      }

      if (/^prioritas\s*1/i.test(trimmed) || /^\*\s*prioritas\s*1/i.test(trimmed) || /^\*\*prioritas\s*1/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const cleanP = trimmed.replace(/^[\*\s\-]+|[\*\s\-]+$/g, '').replace(/:$/, '');
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-red-50 text-google-red border border-red-200 mt-3 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">local_fire_department</span> ${cleanP}</div>`;
        continue;
      }
      if (/^prioritas\s*2/i.test(trimmed) || /^\*\s*prioritas\s*2/i.test(trimmed) || /^\*\*prioritas\s*2/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const cleanP = trimmed.replace(/^[\*\s\-]+|[\*\s\-]+$/g, '').replace(/:$/, '');
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-blue-50 text-primary border border-blue-200 mt-4 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">shield</span> ${cleanP}</div>`;
        continue;
      }
      if (/prioritas\s*patching/i.test(trimmed) && !trimmed.includes(':')) {
        if (inList) { html += '</ul>'; inList = false; }
        const cleanP = trimmed.replace(/^[\*\s\-]+|[\*\s\-]+$/g, '');
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-red-50 text-google-red border border-red-200 mt-3 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">bolt</span> ${cleanP}</div>`;
        continue;
      }
      if (/mitigasi\s*sementara/i.test(trimmed) || /workaround/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const cleanP = trimmed.replace(/^[\*\s\-]+|[\*\s\-]+$/g, '');
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-bold bg-amber-50 text-amber-800 border border-amber-200 mt-4 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">tune</span> ${cleanP}</div>`;
        continue;
      }

      if (/^[A-Z][a-zA-Z\s\/&()]+:$/.test(trimmed) || (trimmed.startsWith('**') && trimmed.endsWith(':**'))) {
        if (inList) { html += '</ul>'; inList = false; }
        const sub = trimmed.replace(/^\*+|\*+$/g, '');
        html += `<p class="text-xs font-bold text-slate-800 mt-3 mb-1.5 uppercase tracking-wider">${sub}</p>`;
        continue;
      }

      if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ') || /^\+\s+/.test(trimmed)) {
        if (!inList) {
          html += '<ul class="space-y-1.5 my-1.5 text-slate-700 text-sm">';
          inList = true;
        }
        const itemContent = trimmed.replace(/^[\*\-•\+]\s+/, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>');
        html += `<li class="flex items-start gap-2 text-slate-700 text-sm leading-snug"><span class="text-slate-400 mt-1.5 w-1.5 h-1.5 rounded-full bg-slate-400 shrink-0"></span><span>${itemContent}</span></li>`;
      } else {
        if (inList) { html += '</ul>'; inList = false; }
        const pContent = trimmed.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>');
        html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${pContent}</p>`;
      }
    }

    if (inList) { html += '</ul>'; }
    return html;
  }

  const cardsHtml = sections.map((sec) => {
    const meta = getSectionMeta(sec.title);
    const bodyHtml = formatBodyHtml(sec.lines);

    return `
      <div class="bg-white border ${meta.border} rounded-xl p-5 shadow-xs hover:shadow-sm transition-all flex flex-col justify-between">
        <div>
          <div class="flex items-center gap-2 mb-3.5 pb-2.5 border-b border-slate-100">
            <span class="p-1.5 rounded-lg ${meta.badgeBg} flex items-center justify-center">
              <span class="material-symbols-outlined text-[18px]">${meta.icon}</span>
            </span>
            <h4 class="text-sm font-bold text-slate-900 tracking-tight">${sec.title}</h4>
          </div>
          <div class="space-y-1">
            ${bodyHtml}
          </div>
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = cardsHtml;
}

function flashUpdatedCards() {
  const cards = document.querySelectorAll('.kpi-card, .chart-card');
  cards.forEach(card => {
    card.classList.add('ring-2', 'ring-blue-400/40', 'ring-offset-1');
    setTimeout(() => {
      card.classList.remove('ring-2', 'ring-blue-400/40', 'ring-offset-1');
    }, 800);
  });
}

function renderKpiCards(stat, isAnimated = false) {
  // KPI 1: Insiden Berita
  const kpiBerita = document.getElementById('kpi-total-berita');
  const kpiBeritaGrowth = document.getElementById('kpi-berita-growth');
  const totalBerita = stat.total_berita ?? 0;
  if (kpiBerita) {
    if (isAnimated) {
      animateNumber(kpiBerita, totalBerita, 450, 0);
    } else {
      kpiBerita.textContent = totalBerita;
    }
  }

  const insidenGrowth = stat.tren_kategori?.insiden_spesifik?.growth_persen ?? 0;
  if (kpiBeritaGrowth) {
    kpiBeritaGrowth.textContent = `${insidenGrowth >= 0 ? '+' : ''}${insidenGrowth}%`;
  }

  // KPI 2: Total CVE
  const kpiCve = document.getElementById('kpi-total-cve');
  const kpiCveCrit = document.getElementById('kpi-cve-critical');
  const totalCve = stat.total_cve ?? 0;
  if (kpiCve) {
    if (isAnimated) {
      animateNumber(kpiCve, totalCve, 450, 0);
    } else {
      kpiCve.textContent = totalCve;
    }
  }
  
  const critCount = stat.severity_breakdown?.CRITICAL ?? 0;
  if (kpiCveCrit) kpiCveCrit.textContent = `${critCount} Critical`;

  // KPI 3: CVSS Score
  const kpiCvss = document.getElementById('kpi-avg-cvss');
  const kpiCvssLevel = document.getElementById('kpi-cvss-level');
  const avgScore = stat.avg_cvss || 0;
  if (kpiCvss) {
    if (isAnimated) {
      animateNumber(kpiCvss, avgScore, 450, 1);
    } else {
      kpiCvss.textContent = avgScore > 0 ? avgScore.toFixed(1) : '0.0';
    }
  }
  if (kpiCvssLevel) {
    if (avgScore >= 9.0) {
      kpiCvssLevel.textContent = 'CRITICAL';
      kpiCvssLevel.className = 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-red-50 text-google-red border border-red-200';
    } else if (avgScore >= 7.0) {
      kpiCvssLevel.textContent = 'HIGH';
      kpiCvssLevel.className = 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-amber-50 text-amber-800 border border-amber-200';
    } else {
      kpiCvssLevel.textContent = 'MEDIUM';
      kpiCvssLevel.className = 'text-[11px] font-bold px-2 py-0.5 rounded-full bg-blue-50 text-primary border border-blue-200';
    }
  }

  // KPI 4: Top Focus
  const kpiFocus = document.getElementById('kpi-top-focus');
  const kpiDetail = document.getElementById('kpi-top-detail');
  const topVendor = stat.vendor_naik?.[0]?.vendor || '-';
  const topKk = stat.kata_kunci_naik?.[0]?.kata_kunci || '-';
  if (kpiFocus) kpiFocus.textContent = `${topVendor} / ${topKk}`;
  if (kpiDetail) {
    const vCount = stat.vendor_naik?.[0]?.jumlah_terkini || 0;
    const kCount = stat.kata_kunci_naik?.[0]?.jumlah_terkini || 0;
    kpiDetail.textContent = `${vCount} CVE (${topVendor}) • ${kCount} Berita (${topKk})`;
  }

  // Badges CVSS Distribution
  const badgePerfect = document.getElementById('badge-cvss-perfect');
  const badgeHigh = document.getElementById('badge-cvss-high');
  const badgeMid = document.getElementById('badge-cvss-mid');
  if (stat.distribusi_cvss?.length >= 3) {
    const vals = stat.distribusi_cvss;
    if (badgePerfect) {
      if (isAnimated) animateNumber(badgePerfect, vals[0].jumlah, 400, 0);
      else badgePerfect.textContent = vals[0].jumlah;
    }
    if (badgeHigh) {
      if (isAnimated) animateNumber(badgeHigh, vals[1].jumlah, 400, 0);
      else badgeHigh.textContent = vals[1].jumlah;
    }
    if (badgeMid) {
      if (isAnimated) animateNumber(badgeMid, vals[2].jumlah, 400, 0);
      else badgeMid.textContent = vals[2].jumlah;
    }
  }

  // Badges Nasional vs Internasional
  const badgeNas = document.getElementById('badge-nasional');
  const badgeIntl = document.getElementById('badge-internasional');
  if (stat.nasional_vs_internasional) {
    const nasVal = stat.nasional_vs_internasional.nasional || 0;
    const intlVal = stat.nasional_vs_internasional.internasional || 0;
    if (badgeNas) {
      if (isAnimated) animateNumber(badgeNas, nasVal, 400, 0);
      else badgeNas.textContent = nasVal;
    }
    if (badgeIntl) {
      if (isAnimated) animateNumber(badgeIntl, intlVal, 400, 0);
      else badgeIntl.textContent = intlVal;
    }
  }

  // Badges Insiden vs Analisis
  const badgeInsiden = document.getElementById('badge-insiden');
  const badgeAnalisis = document.getElementById('badge-analisis');
  if (stat.komposisi_jenis) {
    const insidenVal = stat.komposisi_jenis.insiden_spesifik || 0;
    const analisisVal = stat.komposisi_jenis.analisis_relevan || 0;
    if (badgeInsiden) {
      if (isAnimated) animateNumber(badgeInsiden, insidenVal, 400, 0);
      else badgeInsiden.textContent = insidenVal;
    }
    if (badgeAnalisis) {
      if (isAnimated) animateNumber(badgeAnalisis, analisisVal, 400, 0);
      else badgeAnalisis.textContent = analisisVal;
    }
  }
}

function renderCharts(stat) {
  if (typeof Chart === 'undefined') return;

  // Cleanup chart sebelumnya jika ada
  if (chartKataKunci) { chartKataKunci.destroy(); chartKataKunci = null; }
  if (chartVendorCve) { chartVendorCve.destroy(); chartVendorCve = null; }
  if (chartHarian) { chartHarian.destroy(); chartHarian = null; }
  if (chartCvss) { chartCvss.destroy(); chartCvss = null; }
  if (chartSumber) { chartSumber.destroy(); chartSumber = null; }
  if (chartNasIntl) { chartNasIntl.destroy(); chartNasIntl = null; }
  if (chartJenis) { chartJenis.destroy(); chartJenis = null; }
  if (chartHarianSumber) { chartHarianSumber.destroy(); chartHarianSumber = null; }
  if (chartRadarVektor) { chartRadarVektor.destroy(); chartRadarVektor = null; }
  if (chartSektorTarget) { chartSektorTarget.destroy(); chartSektorTarget = null; }

  // 1. Chart Kata Kunci (Bar Chart)
  const elKataKunci = document.getElementById('chart-kata-kunci');
  if (elKataKunci) {
    const labels = (stat.kata_kunci_naik || []).map(item => item.kata_kunci);
    const dataTerkini = (stat.kata_kunci_naik || []).map(item => item.jumlah_terkini);
    const dataBaseline = (stat.kata_kunci_naik || []).map(item => item.jumlah_baseline);

    chartKataKunci = new Chart(elKataKunci, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Terkini (3H)',
            data: dataTerkini,
            backgroundColor: '#1a73e8',
            borderRadius: 4,
          },
          {
            label: 'Baseline (4H)',
            data: dataBaseline,
            backgroundColor: '#e8eaed',
            borderRadius: 4,
          }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 11 } } },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
          }
        },
        scales: {
          x: { grid: { color: '#f1f3f4' }, ticks: { precision: 0 } },
          y: { grid: { display: false } }
        }
      }
    });
  }

  // 2. Chart Vendor CVE (Doughnut Chart)
  const elVendor = document.getElementById('chart-vendor-cve');
  if (elVendor) {
    const labels = (stat.vendor_naik || []).map(item => item.vendor);
    const counts = (stat.vendor_naik || []).map(item => item.jumlah_terkini);
    const colors = ['#1a73e8', '#d93025', '#f9ab00', '#1e8e3e', '#8430ce', '#129eaf', '#e8710a', '#174ea6'];

    chartVendorCve = new Chart(elVendor, {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: counts,
          backgroundColor: colors.slice(0, labels.length),
          borderWidth: 2,
          borderColor: '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '62%',
        plugins: {
          legend: { position: 'right', labels: { boxWidth: 10, font: { size: 11 } } },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` ${ctx.label}: ${ctx.raw} CVE`
            }
          }
        }
      }
    });
  }

  // 3. Chart Harian Berita vs CVE (Line Chart)
  const elHarian = document.getElementById('chart-harian');
  if (elHarian) {
    const rawDates = (stat.harian || []).map(item => item.tanggal);
    const labels = rawDates.map(d => formatTanggalSingkat(d));
    const dataBerita = (stat.harian || []).map(item => item.berita);
    const dataCve = (stat.harian || []).map(item => item.cve);

    chartHarian = new Chart(elHarian, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Berita',
            data: dataBerita,
            borderColor: '#1a73e8',
            backgroundColor: 'rgba(26, 115, 232, 0.08)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
          },
          {
            label: 'CVE',
            data: dataCve,
            borderColor: '#d93025',
            backgroundColor: 'rgba(217, 48, 37, 0.08)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointHoverRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              title: (items) => {
                const idx = items[0]?.dataIndex;
                return rawDates[idx] ? formatTanggalIndonesia(rawDates[idx]) : '';
              }
            }
          }
        },
        scales: {
          x: { grid: { color: '#f8fafc' } },
          y: { grid: { color: '#f1f3f4' }, beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

  // 4. Chart Harian Sumber: Nasional vs Internasional (Stacked Bar)
  const elHarianSumber = document.getElementById('chart-harian-sumber');
  if (elHarianSumber && stat.harian_sumber?.length) {
    const hsRawDates = stat.harian_sumber.map(d => d.tanggal);
    const hsLabels = hsRawDates.map(d => formatTanggalSingkat(d));
    const hsNas = stat.harian_sumber.map(d => d.nasional);
    const hsIntl = stat.harian_sumber.map(d => d.internasional);

    chartHarianSumber = new Chart(elHarianSumber, {
      type: 'bar',
      data: {
        labels: hsLabels,
        datasets: [
          {
            label: 'Nasional',
            data: hsNas,
            backgroundColor: '#1e8e3e',
            borderRadius: 4,
          },
          {
            label: 'Internasional',
            data: hsIntl,
            backgroundColor: '#1a73e8',
            borderRadius: 4,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              title: (items) => {
                const idx = items[0]?.dataIndex;
                return hsRawDates[idx] ? formatTanggalIndonesia(hsRawDates[idx]) : '';
              },
              label: (ctx) => ` ${ctx.dataset.label}: ${ctx.raw} berita`
            }
          }
        },
        scales: {
          x: { stacked: true, grid: { color: '#f8fafc' } },
          y: { stacked: true, grid: { color: '#f1f3f4' }, beginAtZero: true, ticks: { precision: 0 } }
        }
      }
    });
  }

  // 5. Chart Radar Vektor Serangan (Dengan Margin/Padding Luas Agar Tidak Terpotong)
  const elRadar = document.getElementById('chart-radar-vektor');
  if (elRadar && stat.vektor_serangan?.length) {
    const radarLabels = stat.vektor_serangan.map(d => d.vektor);
    const radarData = stat.vektor_serangan.map(d => d.jumlah);

    chartRadarVektor = new Chart(elRadar, {
      type: 'radar',
      data: {
        labels: radarLabels,
        datasets: [{
          label: 'Jumlah Insiden',
          data: radarData,
          backgroundColor: 'rgba(26, 115, 232, 0.12)',
          borderColor: '#1a73e8',
          borderWidth: 2.5,
          pointBackgroundColor: '#1a73e8',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4.5,
          pointHoverRadius: 7,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: {
            top: 15,
            bottom: 15,
            left: 45,
            right: 45
          }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#202124',
            titleFont: { size: 12, weight: 'bold' },
            bodyFont: { size: 12 },
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` ${ctx.raw} artikel insiden`
            }
          }
        },
        scales: {
          r: {
            beginAtZero: true,
            ticks: {
              precision: 0,
              font: { size: 10 },
              backdropColor: 'transparent',
              color: '#5f6368'
            },
            grid: { color: '#e8eaed' },
            angleLines: { color: '#e8eaed' },
            pointLabels: {
              font: { size: 12, weight: 'bold', family: 'Inter, system-ui, sans-serif' },
              color: '#202124',
              padding: 12
            }
          }
        }
      }
    });
  }

  // 5. Chart Sektor & Vertikal Target Terpapar (Horizontal Bar)
  const elSektor = document.getElementById('chart-sektor-target');
  if (elSektor && stat.sektor_target?.length) {
    const sektorLabels = stat.sektor_target.map(d => d.sektor);
    const sektorData = stat.sektor_target.map(d => d.jumlah);

    chartSektorTarget = new Chart(elSektor, {
      type: 'bar',
      data: {
        labels: sektorLabels,
        datasets: [{
          label: 'Insiden Terpapar',
          data: sektorData,
          backgroundColor: '#1a73e8',
          borderRadius: 4,
          barThickness: 16,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` ${ctx.raw} insiden terpapar`
            }
          }
        },
        scales: {
          x: { grid: { color: '#f1f3f4' }, ticks: { precision: 0 } },
          y: { grid: { display: false }, ticks: { font: { weight: '600' } } }
        }
      }
    });
  }

  // 6. Chart Distribusi Sumber Berita (Horizontal Bar)
  const elSumber = document.getElementById('chart-sumber');
  if (elSumber && stat.distribusi_sumber?.length) {
    const sumberLabels = stat.distribusi_sumber.map(d => d.sumber);
    const sumberData = stat.distribusi_sumber.map(d => d.jumlah);
    const sumberColors = ['#1a73e8', '#1e8e3e', '#f9ab00', '#d93025', '#8430ce', '#129eaf', '#e8710a', '#174ea6', '#c5221f', '#137333'];

    chartSumber = new Chart(elSumber, {
      type: 'bar',
      data: {
        labels: sumberLabels,
        datasets: [{
          label: 'Jumlah Berita',
          data: sumberData,
          backgroundColor: sumberColors.slice(0, sumberLabels.length),
          borderRadius: 4,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` ${ctx.raw} artikel insiden`
            }
          }
        },
        scales: {
          x: { grid: { color: '#f1f3f4' }, ticks: { precision: 0 } },
          y: { grid: { display: false }, ticks: { font: { weight: '600' } } }
        }
      }
    });
  }

  // 7. Chart Asal Media Berita: Nasional vs Internasional (Doughnut)
  const elNasIntl = document.getElementById('chart-nasional-intl');
  if (elNasIntl && stat.nasional_vs_internasional) {
    const nasData = stat.nasional_vs_internasional;
    chartNasIntl = new Chart(elNasIntl, {
      type: 'doughnut',
      data: {
        labels: ['Nasional', 'Internasional'],
        datasets: [{
          data: [nasData.nasional, nasData.internasional],
          backgroundColor: ['#1e8e3e', '#1a73e8'],
          borderWidth: 2,
          borderColor: '#ffffff',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const val = ctx.raw;
                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                return ` ${ctx.label}: ${val} artikel (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  // 8. Chart Klasifikasi Konten: Insiden vs Analisis (Doughnut)
  const elJenis = document.getElementById('chart-jenis-berita');
  if (elJenis && stat.komposisi_jenis) {
    const insiden = stat.komposisi_jenis.insiden_spesifik || 0;
    const analisis = stat.komposisi_jenis.analisis_relevan || 0;

    chartJenis = new Chart(elJenis, {
      type: 'doughnut',
      data: {
        labels: ['Insiden Riil', 'Edukasi / Evergreen'],
        datasets: [{
          data: [insiden, analisis],
          backgroundColor: ['#d93025', '#1a73e8'],
          borderWidth: 2,
          borderColor: '#ffffff',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '60%',
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => {
                const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                const val = ctx.raw;
                const pct = total > 0 ? Math.round((val / total) * 100) : 0;
                return ` ${ctx.label}: ${val} artikel (${pct}%)`;
              }
            }
          }
        }
      }
    });
  }

  // 9. Chart Distribusi Skor CVSS (Horizontal Bar)
  const elCvss = document.getElementById('chart-cvss');
  if (elCvss && stat.distribusi_cvss?.length) {
    const cvssLabels = stat.distribusi_cvss.map(d => d.label);
    const cvssData = stat.distribusi_cvss.map(d => d.jumlah);

    chartCvss = new Chart(elCvss, {
      type: 'bar',
      data: {
        labels: cvssLabels,
        datasets: [{
          data: cvssData,
          backgroundColor: ['#d93025', '#f9ab00', '#1a73e8'],
          borderRadius: 4,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#202124',
            padding: 10,
            cornerRadius: 8,
            callbacks: {
              label: (ctx) => ` ${ctx.raw} kerentanan CVE`
            }
          }
        },
        scales: {
          x: { grid: { color: '#f1f3f4' }, ticks: { precision: 0 } },
          y: { grid: { display: false }, ticks: { font: { weight: '600' } } }
        }
      }
    });
  }
}

function renderTables(stat) {
  // 1. Table Kata Kunci
  const tbodyKk = document.getElementById('tabel-kata-kunci-body');
  if (tbodyKk) {
    tbodyKk.innerHTML = '';
    const items = stat.kata_kunci_naik || [];
    if (items.length === 0) {
      tbodyKk.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-slate-400 text-sm">Tidak ada kata kunci naik.</td></tr>';
    } else {
      items.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50/80 transition-colors';
        tr.innerHTML = `
          <td class="py-3 px-3.5 font-bold text-slate-900 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-primary"></span> ${escapeHtml(item.kata_kunci)}
          </td>
          <td class="py-3 px-3.5 text-center font-extrabold text-slate-900">${item.jumlah_terkini}</td>
          <td class="py-3 px-3.5 text-center text-slate-500 font-medium">${item.jumlah_baseline}</td>
          <td class="py-3 px-3.5 text-right">
            <span class="px-2.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 font-mono font-bold text-xs">
              +${item.growth_persen}%
            </span>
          </td>
        `;
        tbodyKk.appendChild(tr);
      });
    }
  }

  // 2. Table Vendor
  const tbodyVendor = document.getElementById('tabel-vendor-body');
  if (tbodyVendor) {
    tbodyVendor.innerHTML = '';
    const vendors = stat.vendor_naik || [];
    if (vendors.length === 0) {
      tbodyVendor.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-slate-400 text-sm">Tidak ada vendor naik.</td></tr>';
    } else {
      vendors.forEach(v => {
        const topProdukList = v.top_produk || [];
        const topProdukText = topProdukList.length > 0 
          ? topProdukList.map(p => `${escapeHtml(p.produk)} (${p.jumlah}x)`).join(', ')
          : 'Lainnya / Tidak Teridentifikasi';

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50/80 transition-colors';
        tr.innerHTML = `
          <td class="py-3 px-3.5 font-bold text-slate-900 flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-google-red"></span> ${escapeHtml(v.vendor)}
          </td>
          <td class="py-3 px-3.5 text-center font-extrabold text-slate-900">${v.jumlah_terkini}</td>
          <td class="py-3 px-3.5 text-slate-600 max-w-[220px] truncate font-medium text-xs sm:text-sm" title="${topProdukText}">${topProdukText}</td>
          <td class="py-3 px-3.5 text-right">
            <span class="px-2.5 py-0.5 rounded bg-red-50 text-google-red border border-red-200 font-mono font-bold text-xs">
              +${v.growth_persen}%
            </span>
          </td>
        `;
        tbodyVendor.appendChild(tr);
      });
    }
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, match => {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return map[match];
  });
}