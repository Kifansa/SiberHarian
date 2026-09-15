import { escapeHtml } from './tren-utils.js';

/**
 * Pengganti tab switcher Berita vs CVE pada kartu rekomendasi AI
 * @param {'berita' | 'cve'} tab 
 */
export function tampilAiTab(tab) {
  const btnBerita = document.getElementById('tab-ai-berita-btn');
  const btnCve = document.getElementById('tab-ai-cve-btn');
  const boxBerita = document.getElementById('ai-tab-berita');
  const boxCve = document.getElementById('ai-tab-cve');

  if (!btnBerita || !btnCve || !boxBerita || !boxCve) return;

  if (tab === 'berita') {
    boxBerita.classList.remove('hidden');
    boxCve.classList.add('hidden');
    btnBerita.className = 'px-5 py-1.5 rounded-full text-xs font-bold transition-all bg-[#7BBDE8] text-white shadow-2xs cursor-pointer focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none';
    btnCve.className = 'px-5 py-1.5 rounded-full text-xs font-semibold transition-all text-[#49769F] hover:text-[#001D39] cursor-pointer focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none';
  } else {
    boxBerita.classList.add('hidden');
    boxCve.classList.remove('hidden');
    btnCve.className = 'px-5 py-1.5 rounded-full text-xs font-bold transition-all bg-[#7BBDE8] text-white shadow-2xs cursor-pointer focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none';
    btnBerita.className = 'px-5 py-1.5 rounded-full text-xs font-semibold transition-all text-[#49769F] hover:text-[#001D39] cursor-pointer focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none';
  }
}

// Pasang langsung ke window agar interaksi tombol di HTML selalu responsif
if (typeof window !== 'undefined') {
  window.tampilAiTab = tampilAiTab;
}

/**
 * Mendeteksi apakah baris teks merupakan judul section utama laporan
 * @param {string} line 
 * @returns {{ isHeader: boolean, cleanTitle: string }}
 */
export function isMainSectionHeader(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.length > 85) return { isHeader: false, cleanTitle: '' };

  // Abaikan bullet points (*, -, •, +)
  if (/^[\*\-•\+]\s+/.test(trimmed)) return { isHeader: false, cleanTitle: '' };

  // Abaikan baris key-value inline yang memiliki konten setelah titik dua
  if (/:\s+\S+/.test(trimmed) && !trimmed.startsWith('**') && !trimmed.startsWith('#')) {
    return { isHeader: false, cleanTitle: '' };
  }

  // Bersihkan format markdown, nomor urut, emoji, dan tanda baca
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

  // Kata kunci penanda 5 section berita dan 4 section CVE
  const mainKeywords = [
    // Berita 1: Lanskap
    'LANSKAP', 'POLA ANCAMAN',
    // Berita 2: Vektor Serangan & Sektor Terpapar
    'VEKTOR SERANGAN', 'SEKTOR TERPAPAR', 'TTPS',
    // Berita 3: Implikasi Persandian & Kriptografi
    'IMPLIKASI PERSANDIAN', 'PERSANDIAN & KRIPTOGRAFI', 'PERSANDIAN', 'KRIPTOGRAFI',
    // Berita 4: Korelasi Kerentanan & Ancaman
    'HUBUNGAN KERENTANAN', 'KERENTANAN & ANCAMAN', 'KORELASI KERENTANAN', 'HUBUNGAN ANCAMAN', 'HUBUNGAN', 'KORELASI',
    // Berita 5: Rekomendasi Mitigasi
    'REKOMENDASI MITIGASI', 'MITIGASI BERTINGKAT', 'MATRIKS MITIGASI', 'REKOMENDASI ANTISIPASI', 'REKOMENDASI AKSI', 'REKOMENDASI',
    // CVE 1: Vendor & Produk Prioritas
    'VENDOR & PRODUK', 'PRODUK PRIORITAS', 'VENDOR PRIORITAS', 'VENDOR',
    // CVE 2: Analisis Vektor Eksploitasi
    'ANALISIS VEKTOR', 'VEKTOR EKSPLOITASI', 'EKSPLOITASI & DAMPAK',
    // CVE 3: Implikasi Kriptografi & Integritas Sistem
    'IMPLIKASI KRIPTOGRAFI', 'KRIPTOGRAFI & INTEGRITAS', 'INTEGRITAS SISTEM',
    // CVE 4: Panduan Patching
    'PANDUAN PATCHING', 'PRIORITAS PATCHING & MITIGASI', 'PATCHING & MITIGASI'
  ];

  for (const kw of mainKeywords) {
    if (upper.includes(kw)) {
      return { isHeader: true, cleanTitle: clean };
    }
  }

  return { isHeader: false, cleanTitle: '' };
}

/**
 * Mendapatkan penomoran, warna badge, border, dan styling berdasarkan judul section
 * Sesuai desain referensi CTI Diskominfo Jatim
 * @param {string} title 
 * @param {number} index 
 * @param {number} totalSections 
 * @returns {{ number: string, numClass: string, cardBorder: string, badgePrioritas: string | null }}
 */
export function getSectionMeta(title, index = 0, totalSections = 5) {
  const t = title.toLowerCase();

  // Berita Section 1: LANSKAP & POLA ANCAMAN
  if (t.includes('lanskap') || t.includes('pola')) {
    return {
      number: '1',
      numClass: 'bg-[#E0F2FE] text-[#0369A1]',
      cardBorder: 'border-[#E2EDF8]',
      badgePrioritas: null
    };
  }

  // Berita Section 2: VEKTOR SERANGAN & SEKTOR
  if (t.includes('vektor') || t.includes('sektor') || t.includes('ttp')) {
    return {
      number: '2',
      numClass: 'bg-[#EEF2FF] text-[#4338CA]',
      cardBorder: 'border-[#E2EDF8]',
      badgePrioritas: null
    };
  }

  // Berita Section 3: IMPLIKASI PERSANDIAN & KRIPTOGRAFI
  if (t.includes('persandian') || (t.includes('implikasi') && t.includes('kripto') && !t.includes('integritas'))) {
    return {
      number: '3',
      numClass: 'bg-[#EEF5FA] text-[#0A4174]',
      cardBorder: 'border-[#BDD8E9]',
      badgePrioritas: '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#EEF5FA] text-[#0A4174] uppercase tracking-wider shrink-0 border border-[#BDD8E9]">PERSANDIAN</span>'
    };
  }

  // Berita Section 4: KORELASI KERENTANAN CVE
  if (t.includes('korelasi') || t.includes('hubungan') || t.includes('kerentanan')) {
    return {
      number: '4',
      numClass: 'bg-[#FFE4E6] text-[#BE123C]',
      cardBorder: 'border-[#E2EDF8]',
      badgePrioritas: null
    };
  }

  // Berita Section 5 / CVE Section Terakhir: REKOMENDASI AKSI
  if (t.includes('rekomendasi') || t.includes('mitigasi') || t.includes('aksi')) {
    return {
      number: String(totalSections || 5),
      numClass: 'bg-[#059669] text-white',
      cardBorder: 'border-emerald-300',
      badgePrioritas: '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FEE2E2] text-[#991B1B] uppercase tracking-wider shrink-0">PRIORITAS 1</span>'
    };
  }

  // CVE Section 1: VENDOR & PRODUK PRIORITAS
  if (t.includes('vendor') || t.includes('produk')) {
    return {
      number: '1',
      numClass: 'bg-[#E0F2FE] text-[#0369A1]',
      cardBorder: 'border-[#E2EDF8]',
      badgePrioritas: null
    };
  }

  // CVE Section 2: ANALISIS VEKTOR EKSPLOITASI
  if (t.includes('eksploitasi') || (t.includes('vektor') && (t.includes('dampak') || t.includes('analisis')))) {
    return {
      number: '2',
      numClass: 'bg-[#EEF2FF] text-[#4338CA]',
      cardBorder: 'border-[#E2EDF8]',
      badgePrioritas: null
    };
  }

  // CVE Section 3: IMPLIKASI KRIPTOGRAFI & INTEGRITAS SISTEM
  if (t.includes('integritas') || (t.includes('implikasi') && t.includes('kripto'))) {
    return {
      number: '3',
      numClass: 'bg-[#EEF5FA] text-[#0A4174]',
      cardBorder: 'border-[#BDD8E9]',
      badgePrioritas: '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#EEF5FA] text-[#0A4174] uppercase tracking-wider shrink-0 border border-[#BDD8E9]">KRIPTOGRAFI</span>'
    };
  }

  // CVE Section 4: PANDUAN PATCHING & MITIGASI
  if (t.includes('patching') || t.includes('panduan')) {
    return {
      number: String(totalSections || 4),
      numClass: 'bg-[#059669] text-white',
      cardBorder: 'border-emerald-300',
      badgePrioritas: '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FEE2E2] text-[#991B1B] uppercase tracking-wider shrink-0">PRIORITAS 1</span>'
    };
  }

  // Fallback berdasarkan index
  const isLast = (index === totalSections - 1);
  return {
    number: String(index + 1),
    numClass: isLast ? 'bg-[#059669] text-white' : 'bg-[#EEF5FA] text-[#0A4174]',
    cardBorder: isLast ? 'border-emerald-300' : 'border-[#E2EDF8]',
    badgePrioritas: isLast ? '<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FEE2E2] text-[#991B1B] uppercase tracking-wider shrink-0">PRIORITAS 1</span>' : null
  };
}

/**
 * Mem-parsing teks mentah Markdown laporan AI menjadi kartu-kartu HTML terstruktur
 * @param {HTMLElement} container Elemen DOM kontainer kartu
 * @param {string} rawText Teks Markdown dari LLM
 * @param {'berita' | 'cve'} defaultType Tipe fallback
 */
export function renderLaporanCards(container, rawText, defaultType = 'berita') {
  if (!container) return;
  if (!rawText || !rawText.trim()) {
    container.innerHTML = '<div class="text-[#49769F] text-sm italic col-span-full py-6 text-center">Belum ada data ringkasan yang tercatat.</div>';
    return;
  }

  const lines = rawText.trim().split('\n');
  const sections = [];
  let currentTitle = '';
  let currentLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const headerCheck = isMainSectionHeader(line);

    if (headerCheck.isHeader) {
      if (currentTitle && currentLines.length) {
        sections.push({ title: currentTitle, lines: [...currentLines] });
      }
      currentTitle = headerCheck.cleanTitle;
      currentLines = [];
    } else {
      if (currentTitle) {
        currentLines.push(line);
      }
    }
  }

  if (currentTitle && currentLines.length) {
    sections.push({ title: currentTitle, lines: [...currentLines] });
  }

  // Fallback bila format tidak memiliki heading eksplisit
  if (sections.length === 0) {
    const fallbackTitle = defaultType === 'berita' ? 'Analisis Lanskap & Rekomendasi' : 'Prioritas Kerentanan & Mitigasi';
    sections.push({ title: fallbackTitle, lines });
  }

  function formatBodyHtml(bodyLines) {
    let html = '';
    let inList = false;
    let inTable = false;

    for (let j = 0; j < bodyLines.length; j++) {
      const rawLine = bodyLines[j];
      const trimmed = rawLine.trim();

      if (!trimmed) {
        if (inList) { html += '</ul>'; inList = false; }
        continue;
      }

      if (trimmed.includes('|') && trimmed.startsWith('|')) {
        if (inList) { html += '</ul>'; inList = false; }
        if (!inTable) {
          html += '<div class="overflow-x-auto my-3 rounded-2xl border border-[#E2EDF8]"><table class="w-full text-xs text-left border-collapse"><tbody class="divide-y divide-[#E2EDF8]">';
          inTable = true;
        }
        if (/^\|[\s\-:|]+\|$/.test(trimmed)) continue;
        const cells = trimmed.split('|').map(c => c.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
        html += '<tr class="hover:bg-[#EEF5FA]/60">' + cells.map(c => `<td class="py-1.5 px-2 text-slate-700 font-sans">${escapeHtml(c)}</td>`).join('') + '</tr>';
        continue;
      } else if (inTable) {
        html += '</tbody></table></div>';
        inTable = false;
      }

      if (/^[\-\*\•]?\s*\*?rekomendasi(?:\s*utama|\s*kunci)?\s*:/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
        const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
        const bodyText = parts.slice(1).join(':').trim();
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#0A4174] text-white shadow-2xs mt-4 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">shield</span> ${badgeText}</div>`;
        if (bodyText) {
            html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-[#001D39]">$1</strong>')}</p>`;
        }
        continue;
      }
      if (/^[\-\*\•]?\s*\*?prioritas(?:\s*1|\b)/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
        const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
        const bodyText = parts.slice(1).join(':').trim();
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#b91c1c] text-white shadow-2xs mt-3 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">local_fire_department</span> ${badgeText}</div>`;
        if (bodyText) {
            html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-[#001D39]">$1</strong>')}</p>`;
        }
        continue;
      }
      if (/^[\-\*\•]?\s*\*?(mitigasi\s*sementara|workaround)/i.test(trimmed)) {
        if (inList) { html += '</ul>'; inList = false; }
        const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
        const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
        const bodyText = parts.slice(1).join(':').trim();
        html += `<div class="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#4E8EA2] text-white shadow-2xs mt-4 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">tune</span> ${badgeText}</div>`;
        if (bodyText) {
            html += `<p class="text-slate-700 text-sm leading-relaxed mb-2">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold text-[#001D39]">$1</strong>')}</p>`;
        }
        continue;
      }

      if (/^[A-Z][a-zA-Z\s\/&()]+:$/.test(trimmed) || (trimmed.startsWith('**') && trimmed.endsWith(':**'))) {
        if (inList) { html += '</ul>'; inList = false; }
        const sub = trimmed.replace(/^\*+|\*+$/g, '');
        html += `<p class="text-xs font-bold text-[#001D39] mt-3 mb-1.5 uppercase tracking-wider">${sub}</p>`;
        continue;
      }

      if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ') || /^\+\s+/.test(trimmed)) {
        if (!inList) {
          html += '<ul class="space-y-2.5 my-2 text-slate-700 text-xs sm:text-[13px] leading-relaxed">';
          inList = true;
        }
        const liContent = trimmed.replace(/^[\*\-•\+]\s+/, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#001D39]">$1</strong>');
        html += `<li class="flex items-start gap-2.5"><span class="w-1.5 h-1.5 rounded-full bg-[#0A4174] mt-1.5 shrink-0 shadow-2xs"></span><span class="flex-1">${liContent}</span></li>`;
      } else {
        if (inList) { html += '</ul>'; inList = false; }
        const pContent = trimmed.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#001D39]">$1</strong>');
        html += `<p class="text-slate-600 text-xs sm:text-[13px] leading-relaxed mb-2">${pContent}</p>`;
      }
    }

    if (inList) { html += '</ul>'; }
    if (inTable) { html += '</tbody></table></div>'; }
    return html;
  }

  const cardsHtml = sections.map((sec, idx) => {
    const meta = getSectionMeta(sec.title, idx, sections.length);
    const bodyHtml = formatBodyHtml(sec.lines);
    // Jika jumlah card ganjil (misal 5 card), jadikan card terakhir membentang 2 kolom penuh
    const isFullWidth = (sections.length % 2 === 1 && idx === sections.length - 1);
    const spanClass = isFullWidth ? 'lg:col-span-2' : '';

    return `
      <div class="bg-white ${meta.cardBorder} rounded-2xl p-5 sm:p-6 shadow-xs flex flex-col justify-between transition-all ${spanClass}">
        <div>
          <div class="flex items-center justify-between gap-2 mb-3.5">
            <div class="flex items-center gap-2.5">
              <span class="w-7 h-7 rounded-lg ${meta.numClass} flex items-center justify-center font-bold text-xs shrink-0 shadow-2xs font-mono">${meta.number}</span>
              <h4 class="text-xs sm:text-sm font-bold text-[#001D39] tracking-tight uppercase">${escapeHtml(sec.title)}</h4>
            </div>
            ${meta.badgePrioritas ? meta.badgePrioritas : ''}
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
