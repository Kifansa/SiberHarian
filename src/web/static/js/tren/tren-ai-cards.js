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
 * Metadata resmi dan deskripsi kontekstual setiap section SITREP CTI
 * Menjelaskan apa maksud dari data yang disajikan pada masing-masing section.
 */
export const SITREP_MODULE_DESCRIPTIONS = {
  1: {
    id: 'melonjak',
    number: '1',
    color: '#ff3366',
    borderClass: 'border-[#ff3366]/40',
    numClass: 'bg-[#0d2137] text-[#ff3366] border border-[#ff3366]/50',
    title: 'INSIDEN MELONJAK DRASTIS',
    shortLabel: 'Melonjak Drastis',
    icon: 'priority_high',
    fokus: 'Mendeteksi jenis ancaman atau insiden yang mengalami lonjakan volume pertumbuhan anomali paling tajam (spike) pada minggu ini dibandingkan baseline periode sebelumnya.',
    korelasi: 'Korelasi langsung dengan metrik [ POLA ANCAMAN ]. Menguraikan secara mendalam entitas korban, aktor peretas, kronologi insiden, dan dampak kerugian nyata.'
  },
  2: {
    id: 'tren_mingguan',
    number: '2',
    color: '#00d4ff',
    borderClass: 'border-[#00d4ff]/40',
    numClass: 'bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/50',
    title: 'TREN INSIDEN MINGGUAN',
    shortLabel: 'Tren Mingguan',
    icon: 'stacked_line_chart',
    fokus: 'Menyajikan rangkuman 3 kasus insiden siber paling dominan dan berfrekuensi tinggi selama sepekan terakhir (di luar insiden yang melonjak drastis).',
    korelasi: 'Mengacu pada klasifikasi resmi taksonomi eCSIRT dan korpus berita terverifikasi, menguraikan aktor penyerang, pihak/sektor terdampak, wilayah, dan dampak nyata.'
  },
  3: {
    id: 'vektor_serangan',
    number: '3',
    color: '#a78bfa',
    borderClass: 'border-[#a78bfa]/40',
    numClass: 'bg-[#0d2137] text-[#a78bfa] border border-[#a78bfa]/50',
    title: 'VEKTOR SERANGAN TREN INSIDEN MINGGUAN',
    shortLabel: 'Vektor Serangan',
    icon: 'schema',
    fokus: 'Membedah anatomi dan alur teknis serangan (attack life-cycle) dari 3 tren insiden teratas dari awal penetrasi hingga dampak akhir serta metode yang digunakan.',
    korelasi: 'Menganalisis alur rantai serangan 3 tren mingguan dan memetakan TTPs penyerang secara langsung ke taktik dan teknik standar MITRE ATT&CK Enterprise.'
  },
  4: {
    id: 'rekomendasi_aksi',
    number: '4',
    color: '#00ff88',
    borderClass: 'border-[#00ff88]/40',
    numClass: 'bg-[#0d2137] text-[#00ff88] border border-[#00ff88]/50',
    title: 'REKOMENDASI AKSI',
    shortLabel: 'Rekomendasi Aksi',
    icon: 'verified_user',
    fokus: 'Panduan langkah mitigasi taktis terverifikasi dan aksi penangkal terukur untuk melindungi aset sistem informasi dari 3 tren insiden aktif.',
    korelasi: 'Diturunkan secara deterministik dari matriks pertahanan MITRE D3FEND serta kontrol tata kelola keamanan siber standar NIST SP 800-53 Rev. 5 dan NIST CSF 2.0.'
  },
  5: {
    id: 'prediksi_ancaman',
    number: '5',
    color: '#00ff9d',
    borderClass: 'border-[#00ff9d]/40',
    numClass: 'bg-[#0d2137] text-[#00ff9d] border border-[#00ff9d]/50',
    title: 'PREDIKSI TREN ANCAMAN SIBER',
    shortLabel: 'Prediksi Tren',
    icon: 'radar',
    fokus: 'Memberikan proyeksi analitis terhadap potensi ancaman siber baru yang mulai terdeteksi (early warning) agar instansi dapat melakukan mitigasi proaktif.',
    korelasi: 'Hasil deteksi algoritma [ SINYAL ANCAMAN BARU ]. Mengantisipasi varian malware baru, target sektor rentan, dan vektor serangan yang berpotensi meluas.'
  }
};

/**
 * State internal SITREP
 */
let sitrepState = {
  container: null,
  sections: [],
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

  if (/:\\s+\\S+/.test(trimmed) && !isNumberedBoldHeader && !isNumberedHeader) {
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
    'INSIDEN MELONJAK DRASTIS', 'MELONJAK', 'TREN INSIDEN MINGGUAN', 'MAKRO',
    'LANSKAP', 'POLA ANCAMAN',
    'VEKTOR SERANGAN', 'SEKTOR TERPAPAR', 'TTPS',
    'IMPLIKASI PERSANDIAN', 'PERSANDIAN & KRIPTOGRAFI', 'PERSANDIAN', 'KRIPTOGRAFI',
    'HUBUNGAN KERENTANAN', 'KERENTANAN & ANCAMAN', 'KORELASI KERENTANAN', 'HUBUNGAN ANCAMAN', 'HUBUNGAN', 'KORELASI',
    'REKOMENDASI MITIGASI', 'MITIGASI BERTINGKAT', 'MATRIKS MITIGASI', 'REKOMENDASI ANTISIPASI', 'REKOMENDASI AKSI', 'REKOMENDASI',
    'PREDIKSI', 'PREDIKSI TREN ANCAMAN SIBER', 'ANCAMAN MASA DEPAN', 'EMERGING THREATS'
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
  if (upper.includes('TREN INSIDEN MINGGUAN (MAKRO)') || upper.includes('MELONJAK')) {
    return 'INSIDEN MELONJAK DRASTIS';
  }
  if (upper.includes('LANSKAP & ENTITAS ANCAMAN (MIKRO)') || upper === 'TREN INSIDEN MINGGUAN') {
    return 'TREN INSIDEN MINGGUAN';
  }
  if (upper.includes('VEKTOR SERANGAN')) {
    return 'VEKTOR SERANGAN TREN INSIDEN MINGGUAN';
  }
  if (upper.includes('REKOMENDASI AKSI') || upper.includes('REKOMENDASI MITIGASI')) {
    return 'REKOMENDASI AKSI';
  }
  if (upper.includes('PREDIKSI') || upper.includes('EMERGING THREATS')) {
    return 'PREDIKSI TREN ANCAMAN SIBER';
  }
  return title;
}

/**
 * Mendapatkan penomoran, warna badge, border, dan styling berdasarkan judul section
 * Sesuai desain Cyber-HUD CSIRT Diskominfo Jatim
 * @param {string} title 
 * @param {number} index 
 * @param {number} totalSections 
 * @returns {{ number: string, numClass: string, cardBorder: string, color: string, meta: object }}
 */
export function getSectionMeta(title, index = 0, totalSections = 5) {
  const t = (title || '').toLowerCase();

  let stepKey = index + 1;
  if (t.includes('melonjak') || (t.includes('makro') && !t.includes('vektor'))) {
    stepKey = 1;
  } else if ((t.includes('tren insiden') && !t.includes('vektor')) || t.includes('lanskap') || t.includes('mikro')) {
    stepKey = 2;
  } else if (t.includes('vektor') || t.includes('sektor') || t.includes('ttp')) {
    stepKey = 3;
  } else if (t.includes('rekomendasi') || t.includes('mitigasi') || t.includes('aksi')) {
    stepKey = 4;
  } else if (t.includes('prediksi') || t.includes('masa depan') || t.includes('emerging')) {
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
  return `
    <div class="mb-4 p-3.5 sm:p-4 rounded-xl bg-[#070f1c] border border-[#1a3a5c] border-l-4 shadow-xs" style="border-left-color: ${desc.color};">
      <div class="flex items-start gap-2.5">
        <span class="material-symbols-outlined text-lg shrink-0 mt-0.5" style="color: ${desc.color};" aria-hidden="true">${desc.icon}</span>
        <div class="space-y-1.5 min-w-0 flex-1 font-sans text-xs">
          <div class="leading-relaxed text-[#e0f0ff]">
            <span class="font-mono font-bold uppercase tracking-wider" style="color: ${desc.color};">[ MAKSUD INFORMASI ]</span>: 
            ${escapeHtml(desc.fokus)}
          </div>
          <div class="leading-relaxed text-[#8892b0] pt-1 border-t border-[#1a3a5c]/60">
            <span class="font-mono font-semibold text-[#7d8ca6] uppercase tracking-wider">[ SUMBER &amp; KORELASI ]</span>: 
            ${escapeHtml(desc.korelasi)}
          </div>
        </div>
      </div>
    </div>
  `;
}

/**
 * Format baris-baris Markdown body menjadi HTML Cyber-HUD
 */
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
      html += `<div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40 shadow-[0_0_10px_rgba(0,212,255,0.2)] mt-4 mb-2 max-w-full break-words"><span class="material-symbols-outlined text-[14px] shrink-0">shield</span> <span class="break-words min-w-0">[ ${badgeText} ]</span></div>`;
      if (bodyText) {
          html += `<p class="text-[#e0f0ff] text-sm leading-relaxed mb-2 font-sans break-words">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>')}</p>`;
      }
      continue;
    }
    if (/^[\-\*\•]?\s*\*?(mitigasi\s*sementara|workaround)/i.test(trimmed)) {
      if (inList) { html += '</ul>'; inList = false; }
      const parts = trimmed.replace(/^[\*\-\•\s]+/, '').split(':');
      const badgeText = parts[0].replace(/\*\*(.*?)\*\*/g, '$1').trim();
      const bodyText = parts.slice(1).join(':').trim();
      html += `<div class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded text-xs font-mono font-bold bg-[#0d2137] text-[#00ff88] border border-[#00ff88]/40 shadow-[0_0_10px_rgba(0,255,136,0.2)] mt-4 mb-2 max-w-full break-words"><span class="material-symbols-outlined text-[14px] shrink-0">tune</span> <span class="break-words min-w-0">[ ${badgeText} ]</span></div>`;
      if (bodyText) {
          html += `<p class="text-[#e0f0ff] text-sm leading-relaxed mb-2 font-sans break-words">${bodyText.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00ff88]">$1</strong>')}</p>`;
      }
      continue;
    }

    if (/^[A-Z][a-zA-Z\s\/&()]+:$/.test(trimmed) || (trimmed.startsWith('**') && (trimmed.endsWith(':**') || trimmed.endsWith('**:')))) {
      if (inList) { html += '</ul>'; inList = false; }
      const sub = trimmed.replace(/^\*+|\*+$/g, '').replace(/:\s*$/, '').trim();
      html += `<p class="text-xs font-mono font-bold text-[#00d4ff] mt-3 mb-1.5 uppercase tracking-wider break-words">[ ${sub} ]</p>`;
      continue;
    }

    if (trimmed.startsWith('* ') || trimmed.startsWith('- ') || trimmed.startsWith('• ') || /^\+\s+/.test(trimmed)) {
      if (!inList) {
        html += '<ul class="space-y-2.5 my-2 text-xs sm:text-[13px] leading-relaxed font-sans">';
        inList = true;
      }
      const liContent = trimmed.replace(/^[\*\-•\+]\s+/, '').replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>');
      html += `<li class="flex items-start gap-2.5 text-[#e0f0ff]"><span class="w-1.5 h-1.5 rounded-full bg-[#00d4ff] mt-1.5 shrink-0 shadow-[0_0_6px_#00d4ff]"></span><span class="flex-1 break-words min-w-0 leading-relaxed">${liContent}</span></li>`;
    } else {
      if (inList) { html += '</ul>'; }
      const pContent = trimmed.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>');
      html += `<p class="text-[#8892b0] text-xs sm:text-[13px] leading-relaxed mb-2 font-sans break-words">${pContent}</p>`;
    }
  }

  if (inList) { html += '</ul>'; }
  if (inTable) { html += '</tbody></table></div>'; }
  return html;
}

/**
 * Render Tabs Stepper di bagian atas
 */
function renderStepperTabs() {
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
        class="flex items-center gap-2 px-3 py-2 rounded-t-lg transition-all text-xs font-mono whitespace-nowrap min-h-[40px] cursor-pointer ${activeClasses}"
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
function renderSitrepContent() {
  if (!sitrepState.container || sitrepState.sections.length === 0) return;

  const total = sitrepState.sections.length;

  if (sitrepState.modeView === 'stepper') {
    // Mode Stepper: Tampilkan 1 section aktif secara fokus dan lapang
    const activeSec = sitrepState.sections[sitrepState.currentStep] || sitrepState.sections[0];
    const meta = getSectionMeta(activeSec.title, sitrepState.currentStep, total);
    const calloutHtml = renderContextualCallout(meta.desc);
    const bodyHtml = formatBodyHtml(activeSec.lines);

    sitrepState.container.className = 'w-full';
    sitrepState.container.innerHTML = `
      <div class="card-cyber ${meta.cardBorder} p-5 sm:p-7 shadow-xs flex flex-col justify-between transition-all">
        <div>
          <div class="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-[#1a3a5c]/80 flex-wrap">
            <div class="flex items-center gap-2.5">
              <span class="w-7 h-7 rounded ${meta.numClass} flex items-center justify-center font-bold text-xs shrink-0 font-mono">
                ${meta.number}
              </span>
              <h4 class="text-sm sm:text-base font-bold text-[#e0f0ff] font-['Sora'] tracking-tight uppercase leading-snug break-words">
                ${escapeHtml(normalizeSectionTitle(activeSec.title))}
              </h4>
            </div>
            <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-[#070f1c] border border-[#1a3a5c]" style="color: ${meta.color};">
              <span class="w-1.5 h-1.5 rounded-full" style="background-color: ${meta.color};"></span>
              MODUL ${meta.number} DARI ${total}
            </span>
          </div>

          ${calloutHtml}

          <div class="space-y-1.5 text-sm leading-relaxed">
            ${bodyHtml}
          </div>
        </div>
      </div>
    `;

    renderStepperTabs();
  } else {
    // Mode Baca Penuh: Tampilkan seluruh 5 section berurutan
    sitrepState.container.className = 'space-y-6';
    sitrepState.container.innerHTML = sitrepState.sections.map((sec, idx) => {
      const meta = getSectionMeta(sec.title, idx, total);
      const calloutHtml = renderContextualCallout(meta.desc);
      const bodyHtml = formatBodyHtml(sec.lines);

      return `
        <div class="card-cyber ${meta.cardBorder} p-5 sm:p-7 shadow-xs flex flex-col justify-between transition-all">
          <div>
            <div class="flex items-center justify-between gap-3 mb-4 pb-3 border-b border-[#1a3a5c]/80 flex-wrap">
              <div class="flex items-center gap-2.5">
                <span class="w-7 h-7 rounded ${meta.numClass} flex items-center justify-center font-bold text-xs shrink-0 font-mono">
                  ${meta.number}
                </span>
                <h4 class="text-sm sm:text-base font-bold text-[#e0f0ff] font-['Sora'] tracking-tight uppercase leading-snug break-words">
                  ${escapeHtml(normalizeSectionTitle(sec.title))}
                </h4>
              </div>
              <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-[#070f1c] border border-[#1a3a5c]" style="color: ${meta.color};">
                MODUL ${meta.number} / ${total}
              </span>
            </div>

            ${calloutHtml}

            <div class="space-y-1.5 text-sm leading-relaxed">
              ${bodyHtml}
            </div>
          </div>
        </div>
      `;
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
 * Mem-parsing teks mentah Markdown laporan AI menjadi section terstruktur dan merendernya
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

  if (sections.length === 0) {
    const fallbackTitle = 'SITREP Analisis Lanskap & Rekomendasi';
    sections.push({ title: fallbackTitle, lines });
  }

  sitrepState.sections = sections;
  // Pertahankan step jika masih dalam range, atau reset ke 0 jika di luar
  if (sitrepState.currentStep >= sections.length) {
    sitrepState.currentStep = 0;
  }

  renderSitrepContent();
}
