import { ambilTren } from './api.js';
import { animateNumber, tampilkanToast, formatWaktuSekarang, formatTanggalSingkat, formatTanggalIndonesia } from './utils.js';

let sudahDimuat = false;
let sedangMemuat = false;
let lastTrenData = null;

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
    btnBerita.className = 'px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all bg-white text-blue-600 shadow-xs cursor-pointer focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none';
    btnCve.className = 'px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all text-slate-600 hover:text-slate-900 cursor-pointer focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none';
  } else {
    boxBerita.classList.add('hidden');
    boxCve.classList.remove('hidden');
    btnCve.className = 'px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all bg-white text-blue-600 shadow-xs cursor-pointer focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none';
    btnBerita.className = 'px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all text-slate-600 hover:text-slate-900 cursor-pointer focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none';
  }
};

export async function muatTabTren(isManualReload = false) {
  if (sedangMemuat) return;
  if (sudahDimuat && !isManualReload) return;

  const trenDesc = document.getElementById('tren-desc');
  const trenLoadingState = document.getElementById('tren-loading-state');
  const trenEmptyState = document.getElementById('tren-empty-state');
  const trenKontenContainer = document.getElementById('tren-konten-container');
  const btnRefresh = document.getElementById('btn-refresh-tren');
  const btnRefreshIcon = document.getElementById('btn-refresh-tren-icon');
  const btnRefreshText = document.getElementById('btn-refresh-tren-text');

  sedangMemuat = true;

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
  } else {
    // First load / pindah tab: tampilkan animasi & loading skeleton
    if (trenLoadingState) {
      trenLoadingState.classList.remove('hidden');
    }
    if (trenKontenContainer) {
      trenKontenContainer.classList.add('hidden');
    }
    if (trenEmptyState) {
      trenEmptyState.classList.add('hidden');
    }
    if (trenDesc) {
      trenDesc.textContent = 'Menganalisis data tren intelijen siber...';
    }
  }

  try {
    // Beri jeda minimal 450ms agar animasi radar dan shimmer progress bar terlihat mulus
    const [data] = await Promise.all([
      ambilTren(),
      new Promise(r => setTimeout(r, isManualReload ? 500 : 450))
    ]);
    if (!data || data.status !== 'ok') {
      sudahDimuat = false;
      if (trenLoadingState) trenLoadingState.classList.add('hidden');
      if (trenEmptyState) trenEmptyState.classList.remove('hidden');
      if (trenKontenContainer) {
        trenKontenContainer.classList.add('hidden');
        trenKontenContainer.classList.remove('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
      }
      if (trenDesc) {
        trenDesc.textContent = data && data.message ? `Gagal: ${data.message}` : 'Belum ada data tren.';
      }
      if (isManualReload) {
        tampilkanToast('Gagal memuat data tren siber', 'error');
      }
      return;
    }

    sudahDimuat = true;

    if (trenLoadingState) trenLoadingState.classList.add('hidden');
    if (trenEmptyState) trenEmptyState.classList.add('hidden');
    if (trenKontenContainer) {
      trenKontenContainer.classList.remove('hidden');
      // Kembalikan efek opacity dan skala kontainer
      trenKontenContainer.classList.remove('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
      trenKontenContainer.classList.add('opacity-100', 'scale-100');
    }

    lastTrenData = data;
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
    if (trenLoadingState) trenLoadingState.classList.add('hidden');
    if (trenEmptyState) trenEmptyState.classList.remove('hidden');
    if (trenKontenContainer) {
      trenKontenContainer.classList.add('hidden');
      trenKontenContainer.classList.remove('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
    }
    if (trenDesc) {
      trenDesc.textContent = 'Terjadi kesalahan saat memuat data tren.';
    }
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
    }
  } finally {
    sedangMemuat = false;
  }
}

export function muatUlangTabTren() {
  sudahDimuat = false;
  return muatTabTren(true);
}

// Expose fungsi ke window
window.muatTabTren = muatTabTren;
window.muatUlangTabTren = muatUlangTabTren;

// Helper escape HTML
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>"']/g, match => {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return map[match];
  });
}

function isMainSectionHeader(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.length > 85) return { isHeader: false, cleanTitle: '' };

  // Abaikan bullet points (*, -, •, +)
  if (/^[\*\-•\+]\s+/.test(trimmed)) return { isHeader: false, cleanTitle: '' };

  // Abaikan baris key-value inline yang memiliki konten setelah titik dua
  // e.g. 'Sektor/vertikal target teratas: Pengguna...' atau 'Catatan: Perlu diingat...'
  if (/:\s+\S+/.test(trimmed) && !trimmed.startsWith('**') && !trimmed.startsWith('#')) {
    return { isHeader: false, cleanTitle: '' };
  }

  // Bersihkan format markdown, nomor urut, emoji (dengan flag unicode u), dan tanda baca di ujung
  let clean = trimmed;
  clean = clean.replace(/^#+\s*/, '');
  clean = clean.replace(/^\*+|\*+$/g, '').replace(/^_+|_+$/g, '');
  clean = clean.replace(/^\d+[\.\)\-]\s*/, '');
  clean = clean.replace(/^[\p{Extended_Pictographic}\uFE0F\u200D\s]+/u, '');
  clean = clean.replace(/[:.]+$/, '');
  clean = clean.replace(/^\*+|\*+$/g, '').replace(/^_+|_+$/g, '').trim();

  if (!clean) return { isHeader: false, cleanTitle: '' };

  // Abaikan sub-header mitigasi internal atau catatan tambahan
  if (/^(prioritas|mitigasi\s*sementara|workaround|tindak\s*lanjut|catatan)\b/i.test(clean)) {
    return { isHeader: false, cleanTitle: '' };
  }

  const upper = clean.toUpperCase();

  // Kata kunci penanda 4 section berita dan 3 section CVE
  const mainKeywords = [
    // Berita 1: Lanskap
    'LANSKAP', 'POLA ANCAMAN',
    // Berita 2: Vektor Serangan & Sektor Terpapar
    'VEKTOR SERANGAN', 'SEKTOR TERPAPAR', 'TTPS',
    // Berita 3: Korelasi Kerentanan & Ancaman
    'HUBUNGAN KERENTANAN', 'KERENTANAN & ANCAMAN', 'KORELASI KERENTANAN', 'HUBUNGAN ANCAMAN', 'HUBUNGAN', 'KORELASI',
    // Berita 4: Rekomendasi Mitigasi
    'REKOMENDASI MITIGASI', 'MITIGASI BERTINGKAT', 'MATRIKS MITIGASI', 'REKOMENDASI ANTISIPASI',
    // CVE 1: Vendor & Produk Prioritas
    'VENDOR & PRODUK', 'PRODUK PRIORITAS', 'VENDOR PRIORITAS', 'VENDOR',
    // CVE 2: Analisis Vektor Eksploitasi
    'ANALISIS VEKTOR', 'VEKTOR EKSPLOITASI', 'EKSPLOITASI & DAMPAK',
    // CVE 3: Panduan Patching
    'PANDUAN PATCHING', 'PRIORITAS PATCHING & MITIGASI', 'PATCHING & MITIGASI'
  ];

  for (const kw of mainKeywords) {
    if (upper.includes(kw)) {
      return { isHeader: true, cleanTitle: clean };
    }
  }

  return { isHeader: false, cleanTitle: '' };
}

function getSectionMeta(title) {
  const t = title.toLowerCase();
  if (t.includes('lanskap') || t.includes('pola')) {
    return { icon: 'public', border: 'border-slate-200', badgeBg: 'bg-blue-600 text-white shadow-sm' };
  }
  if (t.includes('eksploitasi') || (t.includes('vektor') && (t.includes('dampak') || t.includes('analisis')))) {
    return { icon: 'bolt', border: 'border-slate-200', badgeBg: 'bg-amber-500 text-white shadow-sm' };
  }
  if (t.includes('vektor') || t.includes('sektor') || t.includes('ttp')) {
    return { icon: 'track_changes', border: 'border-slate-200', badgeBg: 'bg-amber-500 text-white shadow-sm' };
  }
  if (t.includes('korelasi') || t.includes('hubungan') || t.includes('kerentanan & ancaman')) {
    return { icon: 'hub', border: 'border-slate-200', badgeBg: 'bg-indigo-600 text-white shadow-sm' };
  }
  if (t.includes('vendor') || t.includes('produk')) {
    return { icon: 'verified_user', border: 'border-slate-200', badgeBg: 'bg-red-600 text-white shadow-sm' };
  }
  if (t.includes('patching') || t.includes('panduan')) {
    return { icon: 'build_circle', border: 'border-slate-200', badgeBg: 'bg-emerald-600 text-white shadow-sm' };
  }
  if (t.includes('mitigasi') || t.includes('rekomendasi') || t.includes('matriks') || t.includes('antisipasi')) {
    return { icon: 'security', border: 'border-slate-200', badgeBg: 'bg-emerald-600 text-white shadow-sm' };
  }
  return { icon: 'article', border: 'border-slate-200', badgeBg: 'bg-slate-700 text-white shadow-sm' };
}

function renderLaporanCards(container, rawText, defaultType = 'berita') {
  if (!container) return;
  if (!rawText || !rawText.trim()) {
    container.innerHTML = '<div class="text-slate-500 text-sm italic col-span-full py-6 text-center">Belum ada data ringkasan yang tercatat.</div>';
    return;
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

  function formatBodyHtml(linesArr) {
    let html = '';
    let inList = false;
    let inTable = false;

    for (let i = 0; i < linesArr.length; i++) {
      const raw = linesArr[i];
      const trimmed = raw.trim();
      
      if (!trimmed) {
        if (inList) { html += '</ul>'; inList = false; }
        if (inTable) { html += '</tbody></table></div>'; inTable = false; }
        continue;
      }

      // --- Table Parsing ---
      if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
        if (inList) { html += '</ul>'; inList = false; }
        
        if (!inTable) {
            html += '<div class="overflow-x-auto mt-3 mb-4 rounded-xl border border-slate-200 shadow-xs"><table class="w-full text-left border-collapse text-xs">';
            inTable = true;
            
            const cells = trimmed.split('|').slice(1, -1).map(s => s.trim());
            html += '<thead><tr class="bg-slate-50 border-b border-slate-200">';
            for (const cell of cells) {
                html += `<th class="py-2.5 px-3.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">${cell}</th>`;
            }
            html += '</tr></thead><tbody class="divide-y divide-slate-100 text-slate-700">';
            continue;
        }
        
        if (/^[\|\-\s:]+$/.test(trimmed)) {
            continue;
        }
        
        const cells = trimmed.split('|').slice(1, -1).map(s => s.trim());
        html += '<tr class="hover:bg-slate-50/70 transition-colors">';
        for (const cell of cells) {
            const cellContent = cell.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>');
            html += `<td class="py-2.5 px-3.5 text-xs text-slate-700 align-top">${cellContent}</td>`;
        }
        html += '</tr>';
        continue;
      } else {
        if (inTable) {
            html += '</tbody></table></div>';
            inTable = false;
        }
      }
      // ----------------------

      if (/^[\-\*\•]?\s*\*?prioritas\s*patching/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
        const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
        const bodyText = parts.slice(1).join(':').trim();
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-red-600 text-white shadow-xs mt-3 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">bolt</span> ${badgeText}</div>`;
        if (bodyText) {
            html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>')}</p>`;
        }
        continue;
      }
      if (/^[\-\*\•]?\s*\*?(prioritas\s*2|tindak\s*lanjut\s*jangka\s*panjang)/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
        const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
        const bodyText = parts.slice(1).join(':').trim();
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-blue-600 text-white shadow-xs mt-4 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">shield</span> ${badgeText}</div>`;
        if (bodyText) {
            html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>')}</p>`;
        }
        continue;
      }
      if (/^[\-\*\•]?\s*\*?prioritas(?:\s*1|\b)/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
        const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
        const bodyText = parts.slice(1).join(':').trim();
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-red-600 text-white shadow-xs mt-3 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">local_fire_department</span> ${badgeText}</div>`;
        if (bodyText) {
            html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>')}</p>`;
        }
        continue;
      }
      if (/^[\-\*\•]?\s*\*?(mitigasi\s*sementara|workaround)/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
        const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
        const bodyText = parts.slice(1).join(':').trim();
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold bg-amber-500 text-white shadow-xs mt-4 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">tune</span> ${badgeText}</div>`;
        if (bodyText) {
            html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>')}</p>`;
        }
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
        html += `<li class="flex items-start gap-2 text-slate-700 text-sm leading-snug"><span class="text-blue-600 mt-1.5 w-1.5 h-1.5 rounded-full bg-blue-600 shrink-0"></span><span>${itemContent}</span></li>`;
      } else {
        if (inList) { html += '</ul>'; inList = false; }
        const pContent = trimmed.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-slate-900">$1</strong>');
        html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${pContent}</p>`;
      }
    }

    if (inList) { html += '</ul>'; }
    if (inTable) { html += '</tbody></table></div>'; }
    return html;
  }

  const cardsHtml = sections.map((sec) => {
    const meta = getSectionMeta(sec.title);
    const bodyHtml = formatBodyHtml(sec.lines);

    return `
      <div class="bg-white border ${meta.border} rounded-2xl p-6 shadow-xs flex flex-col justify-between">
        <div>
          <div class="flex items-center gap-2.5 mb-3.5 pb-2.5 border-b border-slate-100">
            <span class="w-8 h-8 rounded-xl ${meta.badgeBg} flex items-center justify-center shrink-0 shadow-sm">
              <span class="material-symbols-outlined text-lg" aria-hidden="true">${meta.icon}</span>
            </span>
            <h4 class="text-sm font-bold text-slate-900 tracking-tight">${escapeHtml(sec.title)}</h4>
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
    card.classList.add('ring-2', 'ring-primary/30', 'ring-offset-1');
    setTimeout(() => {
      card.classList.remove('ring-2', 'ring-primary/30', 'ring-offset-1');
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
  const kpiCveVendor = document.getElementById('kpi-cve-vendor');
  const totalCve = stat.total_cve ?? 0;
  if (kpiCve) {
    if (isAnimated) {
      animateNumber(kpiCve, totalCve, 450, 0);
    } else {
      kpiCve.textContent = totalCve;
    }
  }
  
  const vendorCount = stat.total_vendor_cve ?? 0;
  if (kpiCveVendor) kpiCveVendor.textContent = `${vendorCount} Vendor`;

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
      kpiCvssLevel.className = 'text-[11px] font-bold px-2 py-0.5 rounded-lg bg-red-600 text-white font-mono shadow-xs';
    } else if (avgScore >= 7.0) {
      kpiCvssLevel.textContent = 'HIGH';
      kpiCvssLevel.className = 'text-[11px] font-bold px-2 py-0.5 rounded-lg bg-amber-500 text-white font-mono shadow-xs';
    } else {
      kpiCvssLevel.textContent = 'MEDIUM';
      kpiCvssLevel.className = 'text-[11px] font-bold px-2 py-0.5 rounded-lg bg-blue-600 text-white font-mono shadow-xs';
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

  const lightGridColor = 'rgba(226, 232, 240, 0.8)';
  const lightTickColor = '#64748b';
  const tooltipStyle = {
    backgroundColor: '#ffffff',
    titleColor: '#0f172a',
    bodyColor: '#334155',
    borderColor: '#e2e8f0',
    borderWidth: 1,
    padding: 10,
    cornerRadius: 8,
    titleFont: { family: 'Inter, sans-serif', weight: 'bold' },
    bodyFont: { family: 'Inter, sans-serif' },
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
  };

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
            label: '7 Hari Terkini',
            data: dataTerkini,
            backgroundColor: '#2563eb',
            borderRadius: 6,
          },
          {
            label: '7 Hari Baseline',
            data: dataBaseline,
            backgroundColor: '#94a3b8',
            borderRadius: 6,
          }
        ]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom', labels: { boxWidth: 10, font: { family: 'Inter, sans-serif', size: 11 }, color: '#64748b' } },
          tooltip: tooltipStyle
        },
        scales: {
          x: { grid: { color: lightGridColor }, ticks: { color: lightTickColor, precision: 0 } },
          y: { grid: { display: false }, ticks: { color: '#1e293b', font: { family: 'Inter, sans-serif', weight: '600' } } }
        }
      }
    });
  }

  // 2. Chart Vendor CVE (Doughnut Chart)
  const elVendor = document.getElementById('chart-vendor-cve');
  if (elVendor) {
    const labels = (stat.vendor_naik || []).map(item => item.vendor);
    const counts = (stat.vendor_naik || []).map(item => item.jumlah_terkini);
    const colors = ['#2563eb', '#dc2626', '#d97706', '#059669', '#7c3aed', '#0284c7', '#ea580c', '#4f46e5'];

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
          legend: { position: 'right', labels: { boxWidth: 10, font: { family: 'Inter, sans-serif', size: 11 }, color: '#64748b' } },
          tooltip: {
            ...tooltipStyle,
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
            borderColor: '#2563eb',
            backgroundColor: 'rgba(37, 99, 235, 0.08)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#2563eb',
            pointHoverRadius: 6,
          },
          {
            label: 'CVE',
            data: dataCve,
            borderColor: '#dc2626',
            backgroundColor: 'rgba(220, 38, 38, 0.08)',
            fill: true,
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: '#dc2626',
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
            ...tooltipStyle,
            callbacks: {
              title: (items) => {
                const idx = items[0]?.dataIndex;
                return rawDates[idx] ? formatTanggalIndonesia(rawDates[idx]) : '';
              }
            }
          }
        },
        scales: {
          x: { grid: { color: lightGridColor }, ticks: { color: lightTickColor } },
          y: { grid: { color: lightGridColor }, beginAtZero: true, ticks: { color: lightTickColor, precision: 0 } }
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
            backgroundColor: '#059669',
            borderRadius: 4,
          },
          {
            label: 'Internasional',
            data: hsIntl,
            backgroundColor: '#2563eb',
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
            ...tooltipStyle,
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
          x: { stacked: true, grid: { color: lightGridColor }, ticks: { color: lightTickColor } },
          y: { stacked: true, grid: { color: lightGridColor }, beginAtZero: true, ticks: { color: lightTickColor, precision: 0 } }
        }
      }
    });
  }

  // 5. Chart Radar Vektor Serangan
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
          backgroundColor: 'rgba(37, 99, 235, 0.12)',
          borderColor: '#2563eb',
          borderWidth: 2,
          pointBackgroundColor: '#2563eb',
          pointBorderColor: '#ffffff',
          pointBorderWidth: 2,
          pointRadius: 4,
          pointHoverRadius: 6,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        layout: {
          padding: { top: 15, bottom: 15, left: 45, right: 45 }
        },
        plugins: {
          legend: { display: false },
          tooltip: {
            ...tooltipStyle,
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
              font: { family: 'Inter, sans-serif', size: 10 },
              backdropColor: 'transparent',
              color: '#64748b'
            },
            grid: { color: 'rgba(226, 232, 240, 0.9)' },
            angleLines: { color: 'rgba(226, 232, 240, 0.9)' },
            pointLabels: {
              font: { size: 11, weight: '600', family: 'Inter, sans-serif' },
              color: '#334155',
              padding: 10
            }
          }
        }
      }
    });
  }

  // 6. Chart Sektor & Vertikal Target Terpapar
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
          backgroundColor: '#0284c7',
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
            ...tooltipStyle,
            callbacks: {
              label: (ctx) => ` ${ctx.raw} insiden terpapar`
            }
          }
        },
        scales: {
          x: { grid: { color: lightGridColor }, ticks: { color: lightTickColor, precision: 0 } },
          y: { grid: { display: false }, ticks: { color: '#1e293b', font: { family: 'Inter, sans-serif', weight: '600' } } }
        }
      }
    });
  }

  // 7. Chart Distribusi Sumber Berita
  const elSumber = document.getElementById('chart-sumber');
  if (elSumber && stat.distribusi_sumber?.length) {
    const sumberLabels = stat.distribusi_sumber.map(d => d.sumber);
    const sumberData = stat.distribusi_sumber.map(d => d.jumlah);
    const sumberColors = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0284c7', '#ea580c', '#4f46e5', '#db2777', '#0d9488'];

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
            ...tooltipStyle,
            callbacks: {
              label: (ctx) => ` ${ctx.raw} artikel insiden`
            }
          }
        },
        scales: {
          x: { grid: { color: lightGridColor }, ticks: { color: lightTickColor, precision: 0 } },
          y: { grid: { display: false }, ticks: { color: '#1e293b', font: { family: 'Inter, sans-serif', weight: '600' } } }
        }
      }
    });
  }

  // 8. Chart Asal Media Berita: Nasional vs Internasional
  const elNasIntl = document.getElementById('chart-nasional-intl');
  if (elNasIntl && stat.nasional_vs_internasional) {
    const nasData = stat.nasional_vs_internasional;
    chartNasIntl = new Chart(elNasIntl, {
      type: 'doughnut',
      data: {
        labels: ['Nasional', 'Internasional'],
        datasets: [{
          data: [nasData.nasional, nasData.internasional],
          backgroundColor: ['#059669', '#2563eb'],
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
            ...tooltipStyle,
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

  // 9. Chart Klasifikasi Konten: Insiden vs Analisis
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
          backgroundColor: ['#dc2626', '#2563eb'],
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
            ...tooltipStyle,
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

  // 10. Chart Distribusi Skor CVSS
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
          backgroundColor: ['#dc2626', '#d97706', '#2563eb'],
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
            ...tooltipStyle,
            callbacks: {
              label: (ctx) => ` ${ctx.raw} kerentanan CVE`
            }
          }
        },
        scales: {
          x: { grid: { color: lightGridColor }, ticks: { color: lightTickColor, precision: 0 } },
          y: { grid: { display: false }, ticks: { color: '#1e293b', font: { family: 'Inter, sans-serif', weight: '600' } } }
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
      tbodyKk.innerHTML = '<tr><td colspan="3" class="py-6 text-center text-slate-500 text-sm">Tidak ada lonjakan kata kunci saat ini.</td></tr>';
    } else {
      items.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50/70 transition-colors';
        tr.innerHTML = `
          <td class="py-3.5 px-3.5 font-semibold text-slate-900">
            ${escapeHtml(item.kata_kunci)}
          </td>
          <td class="py-3.5 px-3.5 text-center font-mono">
            <span class="font-bold text-slate-900 text-sm">${item.jumlah_terkini}</span>
            <span class="block text-[10px] font-normal text-slate-500 font-sans">baseline: ${item.jumlah_baseline}</span>
          </td>
          <td class="py-3.5 px-3.5 text-right font-mono">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-600 text-white font-mono font-bold text-xs shadow-xs">
              <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">trending_up</span>
              <span>+${item.growth_persen}%</span>
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
      tbodyVendor.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-slate-500 text-sm">Tidak ada lonjakan vendor CVE saat ini.</td></tr>';
    } else {
      vendors.forEach(v => {
        const topProdukList = (v.top_produk || []).filter(p => p.produk && p.produk !== '-' && p.produk !== '(lihat deskripsi)' && p.produk !== 'Lainnya / Belum Teridentifikasi');
        const fallbackVendor = v.vendor ? v.vendor.split('/')[0].trim() : 'Lainnya';
        
        const topProdukHtml = topProdukList.length > 0
          ? `<div class="flex flex-wrap items-center gap-1.5 py-0.5">` +
              topProdukList.map(p => `
                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-slate-100 text-slate-700 text-xs font-medium border border-slate-200">
                  <span class="font-semibold text-slate-800">${escapeHtml(p.produk)}</span>
                  <span class="text-[10px] text-slate-500 font-mono font-bold">(${p.jumlah}x)</span>
                </span>
              `).join('') + `</div>`
          : `<span class="text-slate-600 text-xs sm:text-sm">${escapeHtml(fallbackVendor)}</span>`;

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50/70 transition-colors';
        tr.innerHTML = `
          <td class="py-3.5 px-3.5 font-semibold text-slate-900 align-middle">
            ${escapeHtml(v.vendor)}
          </td>
          <td class="py-3.5 px-3.5 text-center align-middle font-mono">
            <span class="font-bold text-slate-900 text-sm">${v.jumlah_terkini}</span>
            <span class="block text-[10px] font-normal text-slate-500 font-sans">baseline: ${v.jumlah_baseline}</span>
          </td>
          <td class="py-3.5 px-3.5 align-middle whitespace-normal break-words leading-relaxed max-w-[320px] sm:max-w-[400px]">
            ${topProdukHtml}
          </td>
          <td class="py-3.5 px-3.5 text-right align-middle font-mono">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-red-600 text-white font-mono font-bold text-xs shadow-xs">
              <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">arrow_upward</span>
              <span>+${v.growth_persen}%</span>
            </span>
          </td>
        `;
        tbodyVendor.appendChild(tr);
      });
    }
  }
}

function parseMarkdownToHtmlForPdf(raw) {
  if (!raw || !raw.trim()) {
    return '<div class="card-block"><p style="color:#64748b;font-style:italic;">Belum ada data analisis tercatat.</p></div>';
  }

  const lines = raw.split('\n');
  let html = '';
  let inList = false;
  let inSection = false;

  for (let rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      if (inList) { html += '</ul>'; inList = false; }
      continue;
    }

    // Heading baris baru: section header, ###, atau **Judul**
    const headerCheck = isMainSectionHeader(line);
    const isHeading = headerCheck.isHeader || line.startsWith('###') || (/^\*\*[^*]+\*\*$/.test(line) && line.length < 80);
    if (isHeading) {
      if (inList) { html += '</ul>'; inList = false; }
      if (inSection) { html += '</div>'; }
      const cleanTitle = headerCheck.isHeader ? headerCheck.cleanTitle : line.replace(/^###\s*/, '').replace(/^\*\*|\*\*$/g, '').trim();
      html += `<div class="card-block"><h4 class="card-heading">${escapeHtml(cleanTitle)}</h4>`;
      inSection = true;
      continue;
    }

    // Bullet point
    if (line.startsWith('- ') || line.startsWith('* ') || /^\d+[\.\)]\s+/.test(line)) {
      if (!inList) {
        if (!inSection) { html += '<div class="card-block">'; inSection = true; }
        html += '<ul class="bullet-list">';
        inList = true;
      }
      let content = line.replace(/^[-*]\s+|\d+[\.\)]\s+/, '').trim();
      
      // Formatting badge mitigasi
      content = content
        .replace(/^Prioritas\s*:\s*/i, '<span class="badge-prio">PRIORITAS</span> ')
        .replace(/^Prioritas\s*1\s*(\([^\)]*\))?\s*:\s*/i, '<span class="badge-prio">PRIORITAS</span> ')
        .replace(/^Prioritas\s*2\s*(\([^\)]*\))?\s*:\s*/i, '<span class="badge-menengah">MENENGAH</span> ')
        .replace(/^Prioritas\s*3\s*(\([^\)]*\))?\s*:\s*/i, '<span class="badge-jangka">JANGKA PANJANG</span> ')
        .replace(/^Prioritas\s*Kritis\s*:\s*/i, '<span class="badge-prio">PRIORITAS</span> ');

      // Bold text formatting
      content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      html += `<li>${content}</li>`;
      continue;
    }

    // Regular paragraph text
    if (inList) { html += '</ul>'; inList = false; }
    if (!inSection) { html += '<div class="card-block">'; inSection = true; }
    let pContent = line.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html += `<p class="card-text">${pContent}</p>`;
  }

  if (inList) html += '</ul>';
  if (inSection) html += '</div>';
  return html;
}

export function eksporLaporanTren() {
  if (!lastTrenData || !lastTrenData.statistik) {
    tampilkanToast('Data tren belum tersedia untuk diekspor ke PDF', 'warning');
    return;
  }

  const stat = lastTrenData.statistik;
  const postur = stat.threat_posture || {};
  const tglCetak = new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  const jamCetak = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });
  const isPosturTinggi = (postur.level || '').toUpperCase().includes('SIAGA') || (postur.level || '').toUpperCase().includes('KRITIS') || (postur.skor && postur.skor >= 7);

  const htmlContent = `<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <title>Laporan Eksekutif CTI - SiberHarian</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 12mm 15mm 15mm 15mm;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #0f172a;
      background: #ffffff;
      font-size: 9.5pt;
      line-height: 1.45;
      margin: 0;
      padding: 0;
    }
    .header-kop {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid #0f172a;
      padding-bottom: 10px;
      margin-bottom: 14px;
    }
    .header-kop .instansi {
      font-size: 8pt;
      font-weight: 700;
      color: #64748b;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 2px;
    }
    .header-kop h1 {
      font-size: 13pt;
      font-weight: 900;
      color: #1e40af;
      margin: 0 0 2px 0;
      letter-spacing: -0.01em;
    }
    .header-kop .subjudul {
      font-size: 8.5pt;
      color: #334155;
      margin: 0;
    }
    .badge-gov {
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      color: #1d4ed8;
      padding: 4px 9px;
      border-radius: 6px;
      font-size: 7.5pt;
      font-weight: 800;
      text-align: right;
    }
    .posture-banner {
      background: ${isPosturTinggi ? '#fef2f2' : '#f0fdf4'};
      border: 1px solid ${isPosturTinggi ? '#fecaca' : '#bbf7d0'};
      border-left: 4.5px solid ${isPosturTinggi ? '#dc2626' : '#16a34a'};
      padding: 9px 12px;
      border-radius: 6px;
      margin-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .posture-banner .posture-title {
      font-size: 9.5pt;
      font-weight: 800;
      color: ${isPosturTinggi ? '#991b1b' : '#166534'};
      margin: 0;
    }
    .posture-banner .posture-meta {
      font-size: 8pt;
      color: #475569;
      margin-top: 1px;
    }
    .posture-badge {
      background: ${isPosturTinggi ? '#dc2626' : '#16a34a'};
      color: #ffffff;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 800;
      font-size: 8.5pt;
      letter-spacing: 0.05em;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-bottom: 14px;
    }
    .kpi-box {
      border: 1px solid #e2e8f0;
      background: #f8fafc;
      border-radius: 6px;
      padding: 8px 10px;
    }
    .kpi-box .label {
      font-size: 7pt;
      text-transform: uppercase;
      font-weight: 700;
      color: #64748b;
      margin-bottom: 2px;
    }
    .kpi-box .val {
      font-size: 13pt;
      font-weight: 800;
      color: #0f172a;
      font-family: monospace;
    }
    .kpi-box .sub {
      font-size: 7pt;
      color: #64748b;
      margin-top: 1px;
    }
    .section-title {
      font-size: 10pt;
      font-weight: 800;
      color: #0f172a;
      border-bottom: 1.5px solid #cbd5e1;
      padding-bottom: 3px;
      margin: 14px 0 8px 0;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      page-break-after: avoid;
    }
    .card-block {
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 9px 12px;
      margin-bottom: 8px;
      background: #ffffff;
      page-break-inside: avoid;
    }
    .card-heading {
      margin: 0 0 4px 0;
      font-size: 9.5pt;
      font-weight: 800;
      color: #1e40af;
    }
    .card-text {
      margin: 0 0 4px 0;
      font-size: 8.5pt;
      color: #334155;
    }
    .bullet-list {
      margin: 3px 0 0 0;
      padding-left: 16px;
      font-size: 8.5pt;
      color: #334155;
    }
    .bullet-list li {
      margin-bottom: 4px;
      line-height: 1.4;
    }
    .badge-prio {
      display: inline-block;
      background: #fee2e2;
      color: #991b1b;
      font-weight: 800;
      font-size: 7pt;
      padding: 1.5px 5px;
      border-radius: 3px;
      margin-right: 4px;
      font-family: monospace;
    }
    .badge-menengah {
      display: inline-block;
      background: #fef3c7;
      color: #92400e;
      font-weight: 800;
      font-size: 7pt;
      padding: 1.5px 5px;
      border-radius: 3px;
      margin-right: 4px;
      font-family: monospace;
    }
    .badge-jangka {
      display: inline-block;
      background: #dbeafe;
      color: #1e40af;
      font-weight: 800;
      font-size: 7pt;
      padding: 1.5px 5px;
      border-radius: 3px;
      margin-right: 4px;
      font-family: monospace;
    }
    table.data-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 6px;
      font-size: 8pt;
      page-break-inside: avoid;
    }
    table.data-table th {
      background: #f1f5f9;
      border: 1px solid #cbd5e1;
      padding: 5px 8px;
      text-align: left;
      font-weight: 700;
      color: #334155;
      text-transform: uppercase;
      font-size: 7.5pt;
    }
    table.data-table td {
      border: 1px solid #e2e8f0;
      padding: 5px 8px;
      color: #1e293b;
    }
    .footer-meta {
      margin-top: 20px;
      border-top: 1px solid #cbd5e1;
      padding-top: 6px;
      display: flex;
      justify-content: space-between;
      font-size: 7pt;
      color: #64748b;
      page-break-inside: avoid;
    }
  </style>
</head>
<body>
  <div class="header-kop">
    <div>
      <div class="instansi">Pemerintah Provinsi Jawa Timur &bull; Diskominfo</div>
      <h1>Laporan Eksekutif Cyber Threat Intelligence</h1>
      <div class="subjudul">Ringkasan Analisis Tren &amp; Rekomendasi Mitigasi Insiden Siber (SiberHarian)</div>
    </div>
    <div class="badge-gov">
      <div>DISPOSAL: TLP:AMBER</div>
      <div style="font-weight:normal;color:#475569;margin-top:2px;">${tglCetak}</div>
    </div>
  </div>

  <div class="posture-banner">
    <div>
      <div class="posture-title">Status Postur Ancaman: ${postur.level || 'SIAGA'} (${postur.skor ? postur.skor + '/10' : '-'})</div>
      <div class="posture-meta">Fokus Utama: <strong>${escapeHtml(stat.top_focus || 'Keamanan Infrastruktur & Web OPD')}</strong> &bull; Cakupan Analisis 7 Hari Agregat</div>
    </div>
    <div class="posture-badge">${postur.level || 'SIAGA'}</div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-box">
      <div class="label">Total Insiden Berita</div>
      <div class="val">${stat.total_berita || 0}</div>
      <div class="sub">Growth 7H: +${stat.berita_growth || 0}%</div>
    </div>
    <div class="kpi-box">
      <div class="label">Total Kerentanan CVE</div>
      <div class="val">${stat.total_cve || 0}</div>
      <div class="sub">${stat.total_cve_critical || 0} Level Critical</div>
    </div>
    <div class="kpi-box">
      <div class="label">Rata-Rata CVSS Score</div>
      <div class="val">${stat.avg_cvss || '-'}</div>
      <div class="sub">Tingkat: High / Critical</div>
    </div>
    <div class="kpi-box">
      <div class="label">Top Vendor Terdampak</div>
      <div class="val" style="font-size:10.5pt;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(stat.top_focus || '-')}</div>
      <div class="sub">Prioritas Pengamanan</div>
    </div>
  </div>

  <div class="section-title">1. Ringkasan Intelijen Ancaman &amp; Rekomendasi Mitigasi Berita</div>
  ${parseMarkdownToHtmlForPdf(lastTrenData.prediksi_berita)}

  <div class="section-title">2. Rekomendasi Prioritas Kerentanan &amp; Patching CVE</div>
  ${parseMarkdownToHtmlForPdf(lastTrenData.prediksi_cve)}

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;page-break-inside:avoid;">
    <div>
      <div class="section-title" style="margin-top:0;">3. Kata Kunci Lonjakan Tertinggi</div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Kata Kunci</th>
            <th style="text-align:center;">Kemunculan (7H)</th>
            <th style="text-align:right;">Growth</th>
          </tr>
        </thead>
        <tbody>
          ${(stat.kata_kunci_naik || []).slice(0, 6).map(k => `
            <tr>
              <td><strong>${escapeHtml(k.kata_kunci)}</strong></td>
              <td style="text-align:center;font-weight:600;">${k.jumlah_terkini}</td>
              <td style="text-align:right;"><span style="display:inline-block;background:#059669;color:#ffffff;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:10.5px;">+${k.growth_persen}%</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div>
      <div class="section-title" style="margin-top:0;">4. Vendor Kerentanan Prioritas</div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Vendor</th>
            <th style="text-align:center;">Total CVE</th>
            <th style="text-align:right;">Growth</th>
          </tr>
        </thead>
        <tbody>
          ${(stat.vendor_naik || []).slice(0, 6).map(v => `
            <tr>
              <td><strong>${escapeHtml(v.vendor)}</strong></td>
              <td style="text-align:center;font-weight:600;">${v.jumlah_terkini}</td>
              <td style="text-align:right;"><span style="display:inline-block;background:#dc2626;color:#ffffff;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:10.5px;">+${v.growth_persen}%</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  </div>

  <div class="footer-meta">
    <div>SiberHarian v1.2.0 &bull; Diskominfo Provinsi Jawa Timur &bull; Analisis AI Lokal On-Premise (Ollama)</div>
    <div>Dicetak pada: ${tglCetak} pukul ${jamCetak} WIB</div>
  </div>
</body>
</html>`;

  // Render ke iframe tersembunyi untuk memicu dialog cetak / Simpan sebagai PDF native browser
  const printIframe = document.createElement('iframe');
  printIframe.style.position = 'fixed';
  printIframe.style.right = '0';
  printIframe.style.bottom = '0';
  printIframe.style.width = '0';
  printIframe.style.height = '0';
  printIframe.style.border = 'none';
  document.body.appendChild(printIframe);

  const doc = printIframe.contentWindow.document;
  doc.open();
  doc.write(htmlContent);
  doc.close();

  tampilkanToast('Membuka dialog Simpan sebagai PDF...', 'info');

  printIframe.contentWindow.focus();
  setTimeout(() => {
    try {
      printIframe.contentWindow.print();
    } catch (e) {
      console.error('Print iframe error:', e);
      // Fallback: buka popup window
      const win = window.open('', '_blank');
      if (win) {
        win.document.write(htmlContent);
        win.document.close();
        win.focus();
        win.print();
      }
    }
    setTimeout(() => {
      if (document.body.contains(printIframe)) {
        document.body.removeChild(printIframe);
      }
    }, 2000);
  }, 350);
}