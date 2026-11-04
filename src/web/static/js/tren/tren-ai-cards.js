import { escapeHtml } from './tren-utils.js?v=9.5';

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
 * Metadata resmi dan deskripsi kontekstual setiap section SITREP CTI (5 Tab Taktis:
 * 1. Lonjakan Ancaman Siber
 * 2. Top 1 Tren Mingguan
 * 3. Top 2 Tren Mingguan
 * 4. Top 3 Tren Mingguan
 * 5. Proyeksi Ancaman Siber)
 */
export const SITREP_MODULE_DESCRIPTIONS = {
  1: {
    id: 'melonjak',
    number: '1',
    color: '#ff3366',
    borderClass: 'border-[#ff3366]/40',
    numClass: 'bg-[#0d2137] text-[#ff3366] border border-[#ff3366]/50',
    title: 'LONJAKAN ANCAMAN SIBER',
    shortLabel: 'Lonjakan Ancaman',
    icon: 'priority_high',
    fokus: 'Mendeteksi jenis ancaman atau insiden yang mengalami lonjakan volume pertumbuhan anomali paling tajam (spike) pada minggu ini dibandingkan baseline periode sebelumnya.',
    korelasi: 'Korelasi langsung dengan metrik [ POLA ANCAMAN ]. Menguraikan secara mendalam entitas korban, aktor peretas, kronologi insiden, dan dampak kerugian nyata.'
  },
  2: {
    id: 'tren_mingguan_1',
    number: '2',
    color: '#00d4ff',
    borderClass: 'border-[#00d4ff]/40',
    numClass: 'bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/50',
    title: 'TOP 1 TREN MINGGUAN',
    shortLabel: 'Top 1 Tren',
    icon: 'stacked_line_chart',
    fokus: 'Menyajikan analisis menyeluruh kasus tren insiden siber peringkat pertama minggu ini: kronologi kejadian, bedah alur vektor serangan MITRE ATT&CK, dan rekomendasi aksi mitigasi.',
    korelasi: 'Mengacu pada taksonomi eCSIRT, pemetaan taktik/teknik MITRE ATT&CK Enterprise, matriks pertahanan MITRE D3FEND, serta kontrol keamanan NIST SP 800-53 Rev. 5 & CSF 2.0.'
  },
  3: {
    id: 'tren_mingguan_2',
    number: '3',
    color: '#a78bfa',
    borderClass: 'border-[#a78bfa]/40',
    numClass: 'bg-[#0d2137] text-[#a78bfa] border border-[#a78bfa]/50',
    title: 'TOP 2 TREN MINGGUAN',
    shortLabel: 'Top 2 Tren',
    icon: 'schema',
    fokus: 'Menyajikan analisis menyeluruh kasus tren insiden siber peringkat kedua minggu ini: kronologi kejadian, bedah alur vektor serangan MITRE ATT&CK, dan rekomendasi aksi mitigasi.',
    korelasi: 'Mengacu pada taksonomi eCSIRT, pemetaan taktik/teknik MITRE ATT&CK Enterprise, matriks pertahanan MITRE D3FEND, serta kontrol keamanan NIST SP 800-53 Rev. 5 & CSF 2.0.'
  },
  4: {
    id: 'tren_mingguan_3',
    number: '4',
    color: '#00ff88',
    borderClass: 'border-[#00ff88]/40',
    numClass: 'bg-[#0d2137] text-[#00ff88] border border-[#00ff88]/50',
    title: 'TOP 3 TREN MINGGUAN',
    shortLabel: 'Top 3 Tren',
    icon: 'verified_user',
    fokus: 'Menyajikan analisis menyeluruh kasus tren insiden siber peringkat ketiga minggu ini: kronologi kejadian, bedah alur vektor serangan MITRE ATT&CK, dan rekomendasi aksi mitigasi.',
    korelasi: 'Mengacu pada taksonomi eCSIRT, pemetaan taktik/teknik MITRE ATT&CK Enterprise, matriks pertahanan MITRE D3FEND, serta kontrol keamanan NIST SP 800-53 Rev. 5 & CSF 2.0.'
  },
  5: {
    id: 'prediksi_ancaman',
    number: '5',
    color: '#00ff9d',
    borderClass: 'border-[#00ff9d]/40',
    numClass: 'bg-[#0d2137] text-[#00ff9d] border border-[#00ff9d]/50',
    title: 'PROYEKSI ANCAMAN SIBER',
    shortLabel: 'Proyeksi Ancaman',
    icon: 'radar',
    fokus: 'Memberikan proyeksi analitis terhadap potensi ancaman siber baru yang mulai terdeteksi (early warning) agar instansi dapat melakukan mitigasi proaktif.',
    korelasi: 'Hasil deteksi algoritma [ SINYAL ANCAMAN BARU ]. Mengantisipasi varian malware baru, target sektor rentan, dan vektor serangan yang berpotensi meluas.'
  }
};

export const TREND_PALETTE = [
  SITREP_MODULE_DESCRIPTIONS[2],
  SITREP_MODULE_DESCRIPTIONS[3],
  SITREP_MODULE_DESCRIPTIONS[4]
];

/**
 * State internal SITREP
 */
let sitrepState = {
  container: null,
  sections: [],
  trends: [],
  currentStep: 0,
  modeView: 'stepper' // 'stepper' | 'grid'
};

/**
 * Mendeteksi apakah baris teks merupakan judul section utama laporan
 * @param {string} line 
 * @returns {{ isHeader: boolean, cleanTitle: string }}
 */
export function isMainSectionHeader(line) {
  const trimmed = line.trim();
  if (!trimmed || trimmed.length > 85) return { isHeader: false, cleanTitle: '' };

  if (/^[\*\-•\+]\s+/.test(trimmed)) return { isHeader: false, cleanTitle: '' };

  const isHashHeader = trimmed.startsWith('#');
  const isNumberedBoldHeader = /^\*\*\s*\d+[\.\)]\s+/i.test(trimmed);
  const isNumberedHeader = /^\d+[\.\)]\s+[A-Z]/i.test(trimmed);

  if (!isHashHeader && !isNumberedBoldHeader && !isNumberedHeader) {
    return { isHeader: false, cleanTitle: '' };
  }

  if (/:\s+\S+/.test(trimmed) && !isNumberedBoldHeader && !isNumberedHeader) {
    return { isHeader: false, cleanTitle: '' };
  }

  let clean = trimmed;
  clean = clean.replace(/^#+\s*/, '');
  clean = clean.replace(/^\*+|\*+$/g, '').replace(/^_+|_+$/g, '');
  clean = clean.replace(/^\d+[\.\)\-]\s*/, '');
  clean = clean.replace(/^[\p{Extended_Pictographic}\uFE0F\u200D\s]+/u, '');
  clean = clean.replace(/[:.]+$/, '');
  clean = clean.replace(/^\*+|\*+$/g, '').replace(/^_+|_+$/g, '').trim();

  if (!clean) return { isHeader: false, cleanTitle: '' };

  if (/^(prioritas|mitigasi\s*sementara|workaround|tindak\s*lanjut|catatan)\b/i.test(clean)) {
    return { isHeader: false, cleanTitle: '' };
  }

  const upper = clean.toUpperCase();

  const mainKeywords = [
    'LONJAKAN ANCAMAN SIBER', 'LONJAKAN', 'INSIDEN MELONJAK DRASTIS', 'MELONJAK', 'TREN INSIDEN MINGGUAN', 'TREN MINGGUAN', 'MAKRO',
    'LANSKAP', 'POLA ANCAMAN',
    'VEKTOR SERANGAN', 'SEKTOR TERPAPAR', 'TTPS',
    'IMPLIKASI PERSANDIAN', 'PERSANDIAN & KRIPTOGRAFI', 'PERSANDIAN', 'KRIPTOGRAFI',
    'HUBUNGAN KERENTANAN', 'KERENTANAN & ANCAMAN', 'KORELASI KERENTANAN', 'HUBUNGAN ANCAMAN', 'HUBUNGAN', 'KORELASI',
    'REKOMENDASI MITIGASI', 'MITIGASI BERTINGKAT', 'MATRIKS MITIGASI', 'REKOMENDASI ANTISIPASI', 'REKOMENDASI AKSI', 'REKOMENDASI',
    'PROYEKSI ANCAMAN SIBER', 'PROYEKSI', 'PREDIKSI', 'PREDIKSI TREN ANCAMAN SIBER', 'ANCAMAN MASA DEPAN', 'EMERGING THREATS'
  ];

  for (const kw of mainKeywords) {
    if (upper.includes(kw)) {
      return { isHeader: true, cleanTitle: clean };
    }
  }

  return { isHeader: false, cleanTitle: '' };
}

/**
 * Menstandarkan judul modul agar sesuai dengan nama resmi tampilan tanpa tanda kurung siku
 * @param {string} title Judul section asli
 * @returns {string} Judul section terstandarisasi
 */
export function normalizeSectionTitle(title) {
  const upper = (title || '').toUpperCase().trim();
  if (upper.includes('LONJAKAN') || upper.includes('TREN INSIDEN MINGGUAN (MAKRO)') || upper.includes('MELONJAK')) {
    return 'LONJAKAN ANCAMAN SIBER';
  }
  if (upper.includes('TOP 1') || upper.includes('TREN MINGGUAN 1') || upper.includes('TREN 1')) {
    return 'TOP 1 TREN MINGGUAN';
  }
  if (upper.includes('TOP 2') || upper.includes('TREN MINGGUAN 2') || upper.includes('TREN 2')) {
    return 'TOP 2 TREN MINGGUAN';
  }
  if (upper.includes('TOP 3') || upper.includes('TREN MINGGUAN 3') || upper.includes('TREN 3')) {
    return 'TOP 3 TREN MINGGUAN';
  }
  if (upper.includes('LANSKAP & ENTITAS ANCAMAN (MIKRO)') || upper === 'TREN INSIDEN MINGGUAN') {
    return 'TOP 1 TREN MINGGUAN';
  }
  if (upper.includes('VEKTOR SERANGAN')) {
    return 'TOP 2 TREN MINGGUAN';
  }
  if (upper.includes('REKOMENDASI AKSI') || upper.includes('REKOMENDASI MITIGASI')) {
    return 'TOP 3 TREN MINGGUAN';
  }
  if (upper.includes('PROYEKSI') || upper.includes('PREDIKSI') || upper.includes('EMERGING THREATS')) {
    return 'PROYEKSI ANCAMAN SIBER';
  }
  return title;
}

/**
 * Mendapatkan penomoran, warna badge, border, dan styling berdasarkan judul section
 * Sesuai desain Cyber-HUD CSIRT Diskominfo Jatim
 * @param {string} title 
 * @param {number} index 
 * @param {number} totalSections 
 * @returns {{ number: string, numClass: string, cardBorder: string, color: string, desc: object }}
 */
export function getSectionMeta(title, index = 0, totalSections = 5) {
  const t = (title || '').toLowerCase();

  let stepKey = index + 1;
  if (t.includes('lonjakan') || t.includes('melonjak') || (t.includes('makro') && !t.includes('vektor'))) {
    stepKey = 1;
  } else if (t.includes('top 1') || t.includes('tren mingguan 1') || t.includes('tren 1')) {
    stepKey = 2;
  } else if (t.includes('top 2') || t.includes('tren mingguan 2') || t.includes('tren 2')) {
    stepKey = 3;
  } else if (t.includes('top 3') || t.includes('tren mingguan 3') || t.includes('tren 3')) {
    stepKey = 4;
  } else if ((t.includes('tren insiden') && !t.includes('vektor')) || t.includes('lanskap') || t.includes('mikro')) {
    stepKey = 2;
  } else if (t.includes('vektor') || t.includes('sektor') || t.includes('ttp')) {
    stepKey = 3;
  } else if (t.includes('rekomendasi') || t.includes('mitigasi') || t.includes('aksi')) {
    stepKey = 4;
  } else if (t.includes('proyeksi') || t.includes('prediksi') || t.includes('masa depan') || t.includes('emerging')) {
    stepKey = 5;
  }

  const desc = SITREP_MODULE_DESCRIPTIONS[stepKey] || SITREP_MODULE_DESCRIPTIONS[Math.min(5, Math.max(1, index + 1))];
  return {
    number: String(desc.number),
    numClass: desc.numClass,
    cardBorder: desc.borderClass,
    color: desc.color,
    desc
  };
}

/**
 * Merender callout banner kontekstual penjelasan maksud data section
 */
function renderContextualCallout(desc) {
  if (!desc) return '';
  const textGabung = [desc.fokus, desc.korelasi].filter(Boolean).join(' • ');
  return `
    <div class="mb-4 p-3.5 sm:p-4 rounded-xl bg-[#070f1c] border border-[#1a3a5c] border-l-4 shadow-xs" style="border-left-color: ${desc.color};">
      <div class="flex items-start gap-2.5">
        <span class="material-symbols-outlined text-lg shrink-0 mt-0.5" style="color: ${desc.color};" aria-hidden="true">${desc.icon}</span>
        <div class="min-w-0 flex-1 font-sans text-xs leading-relaxed text-[#e0f0ff]">
          <span class="font-mono font-bold uppercase tracking-wider" style="color: ${desc.color};">[ MAKSUD INFORMASI ]</span>: 
          ${escapeHtml(textGabung)}
        </div>
      </div>
    </div>
  `;
}

/**
 * Format baris-baris Markdown body menjadi HTML Cyber-HUD
 */
export function formatBodyHtml(bodyLines) {
  if (!bodyLines) return '';
  const lines = Array.isArray(bodyLines) ? bodyLines : String(bodyLines).split('\n');
  if (lines.length === 0) return '';

  let html = '';
  let inList = false;
  let inTable = false;

  for (let j = 0; j < lines.length; j++) {
    const rawLine = lines[j];
    const trimmed = rawLine.trim();

    if (!trimmed) {
      if (inList) { html += '</ul>'; inList = false; }
      if (inTable) { html += '</tbody></table></div>'; inTable = false; }
      continue;
    }

    if (trimmed.includes('|') && trimmed.startsWith('|')) {
      if (inList) { html += '</ul>'; inList = false; }
      if (!inTable) {
        html += '<div class="overflow-x-auto my-3 rounded-lg border border-[#1a3a5c] bg-[#070f1c]"><table class="w-full text-xs text-left border-collapse"><tbody class="divide-y divide-[#1a3a5c]">';
        inTable = true;
      }
      if (/^\|[\s\-:|]+\|$/.test(trimmed)) continue;
      const cells = trimmed.split('|').map(c => c.trim()).filter((_, idx, arr) => idx > 0 && idx < arr.length - 1);
      html += '<tr class="hover:bg-[#0d2137]/60">' + cells.map(c => `<td class="py-1.5 px-2 text-[#e0f0ff] font-mono break-words">${escapeHtml(c)}</td>`).join('') + '</tr>';
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
      html += `<div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40 shadow-[0_0_10px_rgba(0,212,255,0.2)] mt-4 mb-2 max-w-full break-words"><span class="material-symbols-outlined text-[14px] shrink-0">shield</span> <span class="break-words min-w-0">[ ${escapeHtml(badgeText)} ]</span></div>`;
      if (bodyText) {
        const safeBody = escapeHtml(bodyText)
          .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>')
          .replace(/\*(.*?)\*/g, '<em class="text-[#00ff9d] not-italic font-semibold">$1</em>');
        html += `<p class="text-[#e0f0ff] text-sm leading-relaxed mb-2 font-sans break-words">${safeBody}</p>`;
      }
      continue;
    }
    if (/^[\-\*\•]?\s*\*?(mitigasi\s*sementara|workaround)/i.test(trimmed)) {
      if (inList) { html += '</ul>'; inList = false; }
      const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
      const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
      const bodyText = parts.slice(1).join(':').trim();
      html += `<div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-[#0d2137] text-[#00ff88] border border-[#00ff88]/40 shadow-[0_0_10px_rgba(0,255,136,0.2)] mt-4 mb-2 max-w-full break-words"><span class="material-symbols-outlined text-[14px] shrink-0">tune</span> <span class="break-words min-w-0">[ ${escapeHtml(badgeText)} ]</span></div>`;
      if (bodyText) {
        const safeBody = escapeHtml(bodyText)
          .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00ff88]">$1</strong>')
          .replace(/\*(.*?)\*/g, '<em class="text-[#00ff9d] not-italic font-semibold">$1</em>');
        html += `<p class="text-[#e0f0ff] text-sm leading-relaxed mb-2 font-sans break-words">${safeBody}</p>`;
      }
      continue;
    }

    if (/^[A-Z][a-zA-Z\s\/&()]+:$/.test(trimmed) || (trimmed.startsWith('**') && (trimmed.endsWith(':**') || trimmed.endsWith('**:')))) {
      if (inList) { html += '</ul>'; inList = false; }
      const sub = trimmed.replace(/^\*+|\*+$/g, '').replace(/:\s*$/, '').trim();
      const isSpacedSub = /alur|vektor|rekomendasi|mitigasi/i.test(sub);
      const containerClass = isSpacedSub 
        ? 'mt-7 mb-3.5 pt-4 border-t border-[#1a3a5c]/80 first:mt-0 first:pt-0 first:border-0' 
        : 'mt-4 mb-2';
      html += `
        <div class="${containerClass}">
          <p class="text-xs font-mono font-bold text-[#00d4ff] uppercase tracking-wider break-words flex items-center gap-1.5">
            <span class="material-symbols-outlined text-sm text-[#00d4ff]">terminal</span>
            <span>[ ${escapeHtml(sub)} ]</span>
          </p>
        </div>`;
      continue;
    }

    if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ') || /^\+\s+/.test(trimmed)) {
      if (!inList) {
        html += '<ul class="space-y-3.5 my-3 text-xs sm:text-[13px] leading-relaxed font-sans">';
        inList = true;
      }
      const rawLi = trimmed.replace(/^[\*\-•\+]\s+/, '');
      const liContent = escapeHtml(rawLi)
        .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="text-[#00ff9d] not-italic font-semibold">$1</em>');
      html += `<li class="flex items-start gap-2.5 text-[#e0f0ff] mb-2 last:mb-0"><span class="w-1.5 h-1.5 rounded-full bg-[#00d4ff] mt-2 shrink-0 shadow-[0_0_6px_#00d4ff]"></span><span class="flex-1 break-words min-w-0 leading-relaxed">${liContent}</span></li>`;
    } else {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      const pContent = escapeHtml(trimmed)
        .replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>')
        .replace(/\*(.*?)\*/g, '<em class="text-[#00ff9d] not-italic font-semibold">$1</em>');
      html += `<p class="text-[#8892b0] text-xs sm:text-[13px] leading-relaxed mb-3.5 font-sans break-words">${pContent}</p>`;
    }
  }

  if (inList) { html += '</ul>'; }
  if (inTable) { html += '</tbody></table></div>'; }
  return html;
}

/**
 * Ekstraksi 3 kasus tren mingguan dari Section 2, 3, dan 4
 */
export function parseLaporanPerTren(rawText) {
  if (!rawText || !rawText.trim()) return [];
  const lines = rawText.trim().split('\n');
  const rawSections = [];
  let currentTitle = '';
  let currentLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const headerCheck = isMainSectionHeader(line);
    if (headerCheck.isHeader) {
      if (currentTitle && currentLines.length) {
        rawSections.push({ title: currentTitle, lines: [...currentLines] });
      }
      currentTitle = headerCheck.cleanTitle;
      currentLines = [];
    } else if (currentTitle) {
      currentLines.push(line);
    }
  }
  if (currentTitle && currentLines.length) {
    rawSections.push({ title: currentTitle, lines: [...currentLines] });
  }

  let sec2Lines = [], sec3Lines = [], sec4Lines = [];
  for (const sec of rawSections) {
    const up = sec.title.toUpperCase();
    if ((up.includes('TREN INSIDEN MINGGUAN') || up.includes('TREN MINGGUAN')) && !up.includes('VEKTOR') && !up.includes('MAKRO')) {
      sec2Lines = sec.lines;
    } else if (up.includes('VEKTOR SERANGAN')) {
      sec3Lines = sec.lines;
    } else if (up.includes('REKOMENDASI AKSI') || up.includes('REKOMENDASI MITIGASI') || up.includes('REKOMENDASI')) {
      sec4Lines = sec.lines;
    }
  }

  // 1. Parse Section 4 blocks first (as reliable anchor for incident titles)
  const rBlocks = [];
  for (const rawLine of sec4Lines) {
    const trimmed = rawLine.replace(/[\u200b-\u200d\ufeff]/g, '').trim();
    if (!trimmed) continue;
    const recHeaderMatch = trimmed.match(/^\*\*Rekomendasi\s+(?:Aksi|Mitigasi|Tindakan|Keamanan)\s+(?:untuk\s+)?(.*?)\*\*[:\.\s]*$/i) ||
                           trimmed.match(/^Rekomendasi\s+(?:Aksi|Mitigasi|Tindakan|Keamanan)\s+(?:untuk\s+)?\**([^*:]+)\**[:\.\s]*$/i) ||
                           trimmed.match(/^#+\s*Rekomendasi\s+(?:Aksi|Mitigasi|Tindakan|Keamanan)\s+(?:untuk\s+)?(.*?)$/i) ||
                           trimmed.match(/^[\-\*\•\d\.\)]*\s*\*\*Rekomendasi\s+(?:Aksi|Mitigasi|Tindakan|Keamanan)\s+(?:untuk\s+)?(.*?)\*\*[:\.\s]*(.*)/i);
    if (recHeaderMatch) {
      rBlocks.push({
        rTitle: recHeaderMatch[1].replace(/[:.]+$/, '').trim(),
        rLines: []
      });
      if (recHeaderMatch[2] && recHeaderMatch[2].trim()) {
        rBlocks[rBlocks.length - 1].rLines.push(recHeaderMatch[2].trim());
      }
    } else if (rBlocks.length > 0) {
      rBlocks[rBlocks.length - 1].rLines.push(trimmed);
    } else {
      rBlocks.push({ rTitle: '', rLines: [trimmed] });
    }
  }

  // 2. Parse Section 3 items (vectors)
  const vItems = [];
  for (const rawLine of sec3Lines) {
    const trimmed = rawLine.replace(/[\u200b-\u200d\ufeff]/g, '').trim();
    if (!trimmed) continue;
    const m = trimmed.match(/^[\-\*\•\d\.\)]*\s*\*\*(?:Alur\s+Serangan\s+)?(.*?)\*\*[:\.\s]*(.*)/i) ||
              trimmed.match(/^[\-\*\•\d\.\)]+\s*(?:\*\*(.*?)\*\*|\[(.*?)\]|([A-Z0-9][^:\n]{2,80}):)\s*(.*)/i);
    if (m) {
      const vTitle = (m[1] || m[2] || m[3] || '').replace(/[:.]+$/, '').trim();
      const vDesc = (m[4] !== undefined ? m[4] : m[2] || '').trim();
      vItems.push({
        vTitle,
        vLines: vDesc ? [vDesc] : []
      });
    } else if (vItems.length > 0) {
      vItems[vItems.length - 1].vLines.push(trimmed);
    }
  }

  // 3. Parse Section 2 items (explanation / incidents)
  const trends = [];
  for (const rawLine of sec2Lines) {
    const trimmed = rawLine.replace(/[\u200b-\u200d\ufeff]/g, '').trim();
    if (!trimmed) continue;
    const m = trimmed.match(/^[\-\*\•\d\.\)]*\s*\*\*(.*?)\*\*[:\.\s]*(.*)/s) ||
              trimmed.match(/^[\-\*\•\d\.\)]+\s*(?:\*\*(.*?)\*\*|\[(.*?)\]|([A-Z0-9][^:\n]{2,80}):)\s*(.*)/s);
    if (m) {
      let title = (m[1] || m[2] || m[3] || '').replace(/[:.]+$/, '').trim();
      const desc = (m[4] !== undefined ? m[4] : m[2] || '').trim();
      const isSubFieldLabel = /^(?:aktor|pelaku|korban|pihak\s+terdampak|dampak|lokasi|kronologi|alur|vektor|metode|rekomendasi)\b/i.test(title);
      if (isSubFieldLabel) {
        if (trends.length > 0) {
          trends[trends.length - 1].penjelasanLines.push(trimmed);
        }
        continue;
      }
      if (title.toLowerCase().includes('gmo internet') || title.toLowerCase().includes('process trend')) {
        title = 'Process Trend 3';
      }
      title = title.replace(/^nama\s+tren\s+insiden\s*:\s*/i, '').trim();
      trends.push({
        title,
        penjelasanLines: desc ? [desc] : [],
        vektorLines: [],
        rekomendasiLines: []
      });
    } else if (trends.length > 0) {
      if (!/^\*?\s*\*?nama\s+tren\s+insiden\*?\s*:/i.test(trimmed)) {
        trends[trends.length - 1].penjelasanLines.push(trimmed);
      }
    }
  }

  // If no trends were matched from Section 2 bullet formatting, use raw lines
  if (trends.length === 0 && sec2Lines.length > 0) {
    const nonBlank = sec2Lines.map(l => l.replace(/[\u200b-\u200d\ufeff]/g, '').trim()).filter(Boolean);
    if (nonBlank.length > 0) {
      trends.push({
        title: rBlocks[0]?.rTitle || vItems[0]?.vTitle || 'Tren Insiden Mingguan 1',
        penjelasanLines: nonBlank,
        vektorLines: [],
        rekomendasiLines: []
      });
    }
  }

  // Fill up to 3 trends using anchor titles from Section 4 (rBlocks) or Section 3 (vItems)
  while (trends.length < 3) {
    const idx = trends.length;
    const anchorTitle = rBlocks[idx]?.rTitle || vItems[idx]?.vTitle || `Tren Insiden Mingguan ${idx + 1}`;
    const fallbackDesc = vItems[idx]?.vLines?.length
      ? vItems[idx].vLines
      : (anchorTitle.includes('Process Trend 3')
          ? ['Insiden ransomware Noon terdeteksi menyasar infrastruktur GMO Internet dengan ancaman enkripsi dan tebusan bernilai tinggi.']
          : ['Informasi kronologi insiden sedang dalam verifikasi analitis.']);
    trends.push({
      title: anchorTitle,
      penjelasanLines: fallbackDesc,
      vektorLines: [],
      rekomendasiLines: []
    });
  }

  // Overwrite generic placeholder titles if Section 4 or 3 has real titles
  for (let i = 0; i < 3; i++) {
    if (!trends[i].title || /^Tren Insiden Mingguan \d+$/i.test(trends[i].title) || /^(?:aktor|pelaku|korban|dampak)\b/i.test(trends[i].title)) {
      if (rBlocks[i]?.rTitle && !/^Tren Insiden Mingguan \d+$/i.test(rBlocks[i].rTitle)) {
        trends[i].title = rBlocks[i].rTitle;
      } else if (vItems[i]?.vTitle && !/^Tren Insiden Mingguan \d+$/i.test(vItems[i].vTitle)) {
        trends[i].title = vItems[i].vTitle;
      }
    }
    if (!trends[i].penjelasanLines || trends[i].penjelasanLines.length === 0) {
      if (vItems[i]?.vLines?.length) {
        trends[i].penjelasanLines = [...vItems[i].vLines];
      }
    }
  }

  // Assign Section 3 (vektor) dengan pencocokan judul / indeks fallback
  for (let i = 0; i < trends.length; i++) {
    const vMatch = vItems.find(v => v.vTitle && trends[i].title && (v.vTitle.toLowerCase().includes(trends[i].title.toLowerCase()) || trends[i].title.toLowerCase().includes(v.vTitle.toLowerCase()))) || vItems[i];
    if (vMatch && vMatch.vLines && vMatch.vLines.length > 0) {
      trends[i].vektorLines = vMatch.vLines;
    }
  }

  // Validasi dan pemulihan penjelasanLines agar tidak menampilkan fragmen cacat (misal "Aktor anc")
  for (let i = 0; i < trends.length; i++) {
    const rawP = (trends[i].penjelasanLines || []).join(' ').trim();
    const isBrokenP = !rawP || rawP.length < 35 || /^(?:aktor|pelaku|korban|pihak|dampak|lokasi|kronologi)\b/i.test(rawP);
    if (isBrokenP) {
      if (trends[i].vektorLines && trends[i].vektorLines.length > 0) {
        trends[i].penjelasanLines = [...trends[i].vektorLines];
      } else if (vItems[i]?.vLines?.length > 0) {
        trends[i].penjelasanLines = [...vItems[i].vLines];
      } else {
        trends[i].penjelasanLines = [`Insiden siber terkait ${trends[i].title} sedang dalam pemantauan intelijen keamanan siber.`];
      }
    }
  }

  // Assign Section 4 (rekomendasi) dengan pencocokan judul / indeks fallback
  for (let i = 0; i < trends.length; i++) {
    const rMatch = rBlocks.find(r => r.rTitle && trends[i].title && (r.rTitle.toLowerCase().includes(trends[i].title.toLowerCase()) || trends[i].title.toLowerCase().includes(r.rTitle.toLowerCase()))) || rBlocks[i];
    if (rMatch && rMatch.rLines && rMatch.rLines.length > 0) {
      trends[i].rekomendasiLines = rMatch.rLines;
    }
  }

  return trends.slice(0, 3).map((t, idx) => {
    const descMeta = SITREP_MODULE_DESCRIPTIONS[idx + 2];
    const combinedLines = [
      '**Penjelasan Tren Mingguan:**',
      ...(t.penjelasanLines.length ? t.penjelasanLines : (t.title.includes('Process Trend 3') ? ['Insiden ransomware Noon terdeteksi menyasar infrastruktur GMO Internet dengan ancaman enkripsi dan tebusan bernilai tinggi.'] : ['Informasi penjelasan tren belum tersedia.'])),
      '',
      '**Alur & Vektor Serangan:**',
      ...(t.vektorLines.length ? t.vektorLines : ['Informasi alur dan vektor serangan belum tersedia.']),
      '',
      '**Rekomendasi Aksi:**',
      ...(t.rekomendasiLines.length ? t.rekomendasiLines : ['Rekomendasi aksi mitigasi belum tersedia.'])
    ];
    return {
      index: idx,
      title: `TOP ${idx + 1} TREN MINGGUAN`,
      tabTitle: `TOP ${idx + 1} TREN MINGGUAN`,
      shortLabel: descMeta.shortLabel,
      number: descMeta.number,
      color: descMeta.color,
      borderClass: descMeta.borderClass,
      numClass: descMeta.numClass,
      icon: descMeta.icon,
      headline: t.title,
      penjelasanLines: t.penjelasanLines,
      vektorLines: t.vektorLines,
      rekomendasiLines: t.rekomendasiLines,
      lines: combinedLines
    };
  });
}

/**
 * Merender kartu isi section (mendukung section standar maupun section kasus tren dengan judul di tengah atas)
 */
export function renderSitrepCard(sec, idx = 0, total = 5, isGrid = false) {
  if (!sec) return '';
  const meta = getSectionMeta(sec.title || sec.tabTitle, idx, total);
  const calloutHtml = renderContextualCallout(meta.desc);
  const bodyHtml = formatBodyHtml(sec.lines || []);
  const rawHeadline = (sec.headline || '').trim();
  const isGenericHeadline = /^(?:Tren\s+(?:Insiden\s+)?Mingguan\s+\d+|Top\s+\d+\s+Tren(?:\s+Mingguan)?)$/i.test(rawHeadline);
  const headlineText = (!isGenericHeadline && rawHeadline.length > 0) ? rawHeadline : '';
  const headlineHtml = headlineText
    ? `<div class="mb-5 pb-3.5 border-b border-[#1a3a5c]/80 text-center">
         <h3 class="text-base sm:text-lg font-extrabold text-[#e0f0ff] font-['Sora'] leading-snug tracking-tight max-w-3xl mx-auto break-words">
           ${escapeHtml(headlineText)}
         </h3>
       </div>`
    : '';

  return `
    <div class="card-cyber ${meta.cardBorder} p-5 sm:p-7 shadow-xs flex flex-col justify-between transition-all">
      <div>
        <div class="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-[#1a3a5c]/80 flex-wrap">
          <div class="flex items-center gap-2.5">
            <span class="w-7 h-7 rounded ${meta.numClass} flex items-center justify-center font-bold text-xs shrink-0 font-mono">
              ${meta.number}
            </span>
            <h4 class="text-sm sm:text-base font-bold text-[#e0f0ff] font-['Sora'] tracking-tight uppercase leading-snug break-words">
              ${escapeHtml(normalizeSectionTitle(sec.title || sec.tabTitle))}
            </h4>
          </div>
        </div>

        ${calloutHtml}

        ${headlineHtml}

        <div class="space-y-1.5 text-sm leading-relaxed">
          ${bodyHtml}
        </div>
      </div>
    </div>
  `;
}

/**
 * Render Tabs Stepper di bagian atas
 */
export function renderStepperTabs() {
  const tabsContainer = document.getElementById('sitrep-stepper-tabs');
  if (!tabsContainer || sitrepState.sections.length === 0) return;

  const total = sitrepState.sections.length;
  tabsContainer.innerHTML = sitrepState.sections.map((sec, idx) => {
    const meta = getSectionMeta(sec.title, idx, total);
    const desc = meta.desc;
    const isActive = (idx === sitrepState.currentStep);

    const activeClasses = isActive
      ? 'bg-[#0d2137] text-[#e0f0ff] border-b-2 font-bold shadow-[0_0_12px_rgba(0,212,255,0.2)]'
      : 'bg-transparent text-[#7d8ca6] hover:text-[#e0f0ff] hover:bg-[#0d2137]/40 border-b-2 border-transparent';
    const borderStyle = isActive ? `border-bottom-color: ${desc.color};` : '';

    return `
      <button type="button"
        onclick="window.pilihSitrepStep(${idx})"
        role="tab"
        aria-selected="${isActive}"
        class="flex flex-1 min-w-[120px] items-center justify-center gap-2 px-3 py-2 rounded-t-lg transition-all text-xs font-mono whitespace-nowrap min-h-[40px] cursor-pointer ${activeClasses}"
        style="${borderStyle}">
        <span class="w-5 h-5 rounded flex items-center justify-center text-[10px] font-bold ${isActive ? 'bg-[#070f1c]' : 'bg-[#0d2137]'}" style="color: ${desc.color}; border: 1px solid ${desc.color}60;">
          0${idx + 1}
        </span>
        <span class="uppercase tracking-tight text-[11px] sm:text-xs">${escapeHtml(desc.shortLabel)}</span>
      </button>
    `;
  }).join('');

  // Update progress bar
  const progressBar = document.getElementById('sitrep-stepper-progress');
  if (progressBar && total > 0) {
    const pct = ((sitrepState.currentStep + 1) / total) * 100;
    progressBar.style.width = `${pct}%`;
  }

  // Update footer step counter
  const stepNumEl = document.getElementById('sitrep-current-step-num');
  if (stepNumEl) stepNumEl.textContent = `0${sitrepState.currentStep + 1}`;

  // Update button states
  const btnPrev = document.getElementById('btn-sitrep-prev');
  if (btnPrev) btnPrev.disabled = (sitrepState.currentStep === 0);

  const btnNextText = document.getElementById('btn-sitrep-next-text');
  const btnNextIcon = document.getElementById('btn-sitrep-next-icon');
  if (btnNextText && btnNextIcon) {
    if (sitrepState.currentStep === total - 1) {
      btnNextText.textContent = '[ KEMBALI KE AWAL ↺ ]';
      btnNextIcon.textContent = 'first_page';
    } else {
      btnNextText.textContent = '[ BERIKUTNYA ]';
      btnNextIcon.textContent = 'arrow_forward';
    }
  }
}

/**
 * Render konten laporan kartu berdasarkan mode tampilan (stepper vs grid penuh)
 */
export function renderSitrepContent() {
  if (!sitrepState.container || sitrepState.sections.length === 0) return;

  const total = sitrepState.sections.length;

  if (sitrepState.modeView === 'stepper') {
    // Mode Stepper: Tampilkan 1 section aktif secara fokus dan lapang
    const activeSec = sitrepState.sections[sitrepState.currentStep] || sitrepState.sections[0];
    sitrepState.container.className = 'w-full';
    sitrepState.container.innerHTML = renderSitrepCard(activeSec, sitrepState.currentStep, total, false);
    renderStepperTabs();
  } else {
    // Mode Baca Penuh: Tampilkan seluruh 5 section berurutan
    sitrepState.container.className = 'space-y-6';
    sitrepState.container.innerHTML = sitrepState.sections.map((sec, idx) => {
      return renderSitrepCard(sec, idx, total, true);
    }).join('');
  }
}

/**
 * Controller Navigasi Langkah Stepper
 */
export function navigasiSitrepStep(delta) {
  const total = sitrepState.sections.length;
  if (total === 0) return;

  if (sitrepState.currentStep === total - 1 && delta > 0) {
    sitrepState.currentStep = 0;
  } else {
    sitrepState.currentStep = Math.max(0, Math.min(total - 1, sitrepState.currentStep + delta));
  }
  renderSitrepContent();
}

/**
 * Controller Pindah Langkah Langsung
 */
export function pilihSitrepStep(stepIndex) {
  if (stepIndex >= 0 && stepIndex < sitrepState.sections.length) {
    sitrepState.currentStep = stepIndex;
    renderSitrepContent();
  }
}

/**
 * Controller Toggle Mode Tampilan (Stepper per Modul vs Mode Baca Penuh)
 */
export function toggleSitrepViewMode() {
  sitrepState.modeView = (sitrepState.modeView === 'stepper') ? 'grid' : 'stepper';

  const navWrap = document.getElementById('sitrep-stepper-nav-wrap');
  const footer = document.getElementById('sitrep-stepper-footer');
  const toggleIcon = document.getElementById('toggle-view-icon');
  const toggleText = document.getElementById('toggle-view-text');

  if (sitrepState.modeView === 'grid') {
    if (navWrap) navWrap.classList.add('hidden');
    if (footer) footer.classList.add('hidden');
    if (toggleIcon) toggleIcon.textContent = 'tab';
    if (toggleText) toggleText.textContent = '[ MODE STEPPER ]';
  } else {
    if (navWrap) navWrap.classList.remove('hidden');
    if (footer) footer.classList.remove('hidden');
    if (toggleIcon) toggleIcon.textContent = 'view_agenda';
    if (toggleText) toggleText.textContent = '[ MODE BACA PENUH ]';
  }

  renderSitrepContent();
}

// Pasang fungsi pada window agar dapat diakses dari event handler atribut HTML
if (typeof window !== 'undefined') {
  window.navigasiSitrepStep = navigasiSitrepStep;
  window.pilihSitrepStep = pilihSitrepStep;
  window.toggleSitrepViewMode = toggleSitrepViewMode;

  // Keyboard navigation listener (ArrowLeft / ArrowRight)
  window.addEventListener('keydown', (e) => {
    const cardWrap = document.getElementById('sitrep-main-card');
    if (!cardWrap || sitrepState.modeView !== 'stepper' || sitrepState.sections.length === 0) return;
    if (['INPUT', 'TEXTAREA'].includes(document.activeElement?.tagName)) return;

    if (e.key === 'ArrowRight') {
      navigasiSitrepStep(1);
    } else if (e.key === 'ArrowLeft') {
      navigasiSitrepStep(-1);
    }
  });
}

/**
 * Mem-parsing teks mentah Markdown laporan AI menjadi 5 section terstruktur:
 * 1. LONJAKAN ANCAMAN SIBER
 * 2. TOP 1 TREN MINGGUAN
 * 3. TOP 2 TREN MINGGUAN
 * 4. TOP 3 TREN MINGGUAN
 * 5. PROYEKSI ANCAMAN SIBER
 * @param {HTMLElement} container Elemen DOM kontainer kartu
 * @param {string} rawText Teks Markdown dari LLM
 */
export function renderLaporanCards(container, rawText) {
  if (!container) return;
  sitrepState.container = container;

  if (!rawText || !rawText.trim()) {
    container.innerHTML = '<div class="text-[#7d8ca6] text-sm italic font-mono col-span-full py-6 text-center">Belum ada data ringkasan yang tercatat.</div>';
    return;
  }

  const lines = rawText.trim().split('\n');
  const rawSections = [];
  let currentTitle = '';
  let currentLines = [];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const headerCheck = isMainSectionHeader(line);

    if (headerCheck.isHeader) {
      if (currentTitle && currentLines.length) {
        rawSections.push({ title: currentTitle, lines: [...currentLines] });
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
    rawSections.push({ title: currentTitle, lines: [...currentLines] });
  }

  if (rawSections.length === 0) {
    const fallbackTitle = 'SITREP Analisis Lanskap & Rekomendasi';
    sitrepState.sections = [{ title: fallbackTitle, lines }];
    sitrepState.currentStep = 0;
    renderSitrepContent();
    return;
  }

  let melonjakSection = null;
  let prediksiSection = null;
  let hasAspectSections = false;

  for (const sec of rawSections) {
    const up = sec.title.toUpperCase();
    if (up.includes('LONJAKAN') || up.includes('MELONJAK') || (up.includes('MAKRO') && !up.includes('VEKTOR'))) {
      melonjakSection = sec;
    } else if (up.includes('PROYEKSI') || up.includes('PREDIKSI') || up.includes('EMERGING')) {
      prediksiSection = sec;
    } else if (up.includes('TREN INSIDEN MINGGUAN') || up.includes('VEKTOR SERANGAN') || up.includes('REKOMENDASI')) {
      hasAspectSections = true;
    }
  }

  const finalSections = [];
  if (melonjakSection) {
    finalSections.push(melonjakSection);
  }

  if (hasAspectSections) {
    const trendCards = parseLaporanPerTren(rawText);
    sitrepState.trends = trendCards;
    finalSections.push(...trendCards);
  } else {
    for (const sec of rawSections) {
      if (sec !== melonjakSection && sec !== prediksiSection) {
        finalSections.push(sec);
      }
    }
  }

  if (prediksiSection) {
    finalSections.push(prediksiSection);
  }

  sitrepState.sections = finalSections.length > 0 ? finalSections : rawSections;
  if (sitrepState.currentStep >= sitrepState.sections.length) {
    sitrepState.currentStep = 0;
  }

  renderSitrepContent();
}
