import { escapeHtml } from './tren-utils.js';

/**
 * Deprecated: Tab switcher Berita vs CVE telah dihapus.
 * SITREP CTI kini disajikan langsung terpadu tanpa tab terpisah.
 */
export function tampilAiTab() {
  // No-op for backwards compatibility
}

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

  // Dukung diawali dengan #, atau format nomor tebal (**1. JUDUL**), atau nomor urut (1. JUDUL)
  const isHashHeader = trimmed.startsWith('#');
  const isNumberedBoldHeader = /^\*\*\s*\d+[\.\)]\s+/i.test(trimmed);
  const isNumberedHeader = /^\d+[\.\)]\s+[A-Z]/i.test(trimmed);

  if (!isHashHeader && !isNumberedBoldHeader && !isNumberedHeader) {
    return { isHeader: false, cleanTitle: '' };
  }

  // Abaikan baris key-value inline yang memiliki konten setelah titik dua (kecuali untuk header bernomor)
  if (/:\s+\S+/.test(trimmed) && !isNumberedBoldHeader && !isNumberedHeader) {
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

  // Kata kunci penanda section laporan SITREP CTI
  const mainKeywords = [
    // Berita 0: Tren Insiden
    'TREN INSIDEN MINGGUAN', 'MAKRO',
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
    // Berita 6: Prediksi & Ancaman Masa Depan
    'PREDIKSI', 'ANCAMAN MASA DEPAN', 'EMERGING THREATS'
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
 * @returns {{ number: string, numClass: string, cardBorder: string }}
 */
export function getSectionMeta(title, index = 0, totalSections = 5) {
  const t = title.toLowerCase();

  // Berita Section 1: TREN INSIDEN
  if (t.includes('tren insiden') || t.includes('makro')) {
    return {
      number: '1',
      numClass: 'bg-[#FDF2F8] text-[#BE185D]', // Pink theme
      cardBorder: 'border-[#FBCFE8]'
    };
  }

  // Berita Section 2: LANSKAP
  if (t.includes('lanskap') || t.includes('pola') || t.includes('mikro')) {
    return {
      number: '2',
      numClass: 'bg-[#E0F2FE] text-[#0369A1]', // Blue theme
      cardBorder: 'border-[#E2EDF8]'
    };
  }

  // Berita Section 3: VEKTOR SERANGAN
  if (t.includes('vektor') || t.includes('sektor') || t.includes('ttp')) {
    return {
      number: '3',
      numClass: 'bg-[#EEF2FF] text-[#4338CA]', // Indigo theme
      cardBorder: 'border-[#E2EDF8]'
    };
  }

  // Berita Section 4: REKOMENDASI AKSI
  if (t.includes('rekomendasi') || t.includes('mitigasi') || t.includes('aksi')) {
    return {
      number: '4',
      numClass: 'bg-[#FFE4E6] text-[#BE123C]', // Rose theme
      cardBorder: 'border-[#E2EDF8]'
    };
  }

  // Berita Section 5: PREDIKSI & ANCAMAN BARU
  if (t.includes('prediksi') || t.includes('masa depan') || t.includes('emerging')) {
    return {
      number: '5',
      numClass: 'bg-[#059669] text-white', // Emerald theme
      cardBorder: 'border-emerald-300'
    };
  }

  // Fallback berdasarkan index
  const isLast = (index === totalSections - 1);
  return {
    number: String(index + 1),
    numClass: isLast ? 'bg-[#059669] text-white' : 'bg-[#EEF5FA] text-[#0A4174]',
    cardBorder: isLast ? 'border-emerald-300' : 'border-[#E2EDF8]'
  };
}

/**
 * Mem-parsing teks mentah Markdown laporan AI menjadi kartu-kartu HTML terstruktur
 * @param {HTMLElement} container Elemen DOM kontainer kartu
 * @param {string} rawText Teks Markdown dari LLM
 */
export function renderLaporanCards(container, rawText) {
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
    const fallbackTitle = 'SITREP Analisis Lanskap & Rekomendasi';
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
          html += '<div class="overflow-x-auto my-3 rounded-lg border border-[#E2EDF8]"><table class="w-full text-xs text-left border-collapse"><tbody class="divide-y divide-[#E2EDF8]">';
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
        html += `<div class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-[#0A4174] text-white shadow-2xs mt-4 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">shield</span> ${badgeText}</div>`;
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
        html += `<div class="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-[#4E8EA2] text-white shadow-2xs mt-4 mb-2 w-fit"><span class="material-symbols-outlined text-[14px]">tune</span> ${badgeText}</div>`;
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
    // Jika section ganjil dan ini elemen terakhir, buat span penuh agar rapi
    const isOddLast = (sections.length % 2 !== 0 && idx === sections.length - 1);
    const spanClass = isOddLast ? 'col-span-full' : '';

    return `
      <div class="bg-white ${meta.cardBorder} rounded-lg p-5 sm:p-6 shadow-xs flex flex-col justify-between transition-all ${spanClass}">
        <div>
          <div class="flex items-center gap-2.5 mb-3.5">
            <span class="w-7 h-7 rounded-md ${meta.numClass} flex items-center justify-center font-bold text-xs shrink-0 shadow-2xs font-mono">${meta.number}</span>
            <h4 class="text-xs sm:text-sm font-bold text-[#001D39] tracking-tight uppercase">${escapeHtml(sec.title)}</h4>
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
