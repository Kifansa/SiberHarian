import { escapeHtml } from './tren-utils.js?v=9.5';

/**
 * Metadata visual untuk masing-masing wilayah (CSIRT Jatim Cyber-HUD Style)
 */
const WILAYAH_META = {
  intl: {
    label: 'Internasional',
    icon: 'public',
    iconColor: 'text-[#00d4ff]',
    badgeBg: 'bg-[#0d2137]',
    badgeText: 'text-[#00d4ff]'
  },
  nas: {
    label: 'Nasional',
    icon: 'flag',
    iconColor: 'text-[#00ff88]',
    badgeBg: 'bg-[#0d2137]',
    badgeText: 'text-[#00ff88]'
  },
  jatim: {
    label: 'Jawa Timur',
    icon: 'location_on',
    iconColor: 'text-[#ff8800]',
    badgeBg: 'bg-[#0d2137]',
    badgeText: 'text-[#ff8800]'
  }
};

/**
 * Penyimpanan memori data kasus insiden wilayah untuk modal pop-up CTI
 */
let currentKasusData = {
  intl: null,
  nas: null,
  jatim: null
};

/**
 * Helper pembuat badge kategori / jenis insiden (Tactical HUD)
 * @param {string} tag 
 * @returns {string} HTML string
 */
export function getTagBadge(tag) {
  const t = (tag || '').toLowerCase();
  if (t.includes('ransomware')) {
    return '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0d2137] text-[#ff3366] border border-[#ff3366]/40">[ Ransomware ]</span>';
  } else if (t.includes('bocor') || t.includes('data')) {
    return '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40">[ Kebocoran Data ]</span>';
  } else if (t.includes('peretasan') || t.includes('deface') || t.includes('slot')) {
    return '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0d2137] text-[#00ff88] border border-[#00ff88]/40">[ Peretasan Web ]</span>';
  } else if (t.includes('malware')) {
    return '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0d2137] text-[#a78bfa] border border-[#a78bfa]/40">[ Malware ]</span>';
  } else if (t.includes('phishing')) {
    return '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0d2137] text-[#38bdf8] border border-[#38bdf8]/40">[ Phishing ]</span>';
  } else if (t.includes('celah') || t.includes('zero-day')) {
    return '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0d2137] text-[#ff8800] border border-[#ff8800]/40">[ Eksploitasi Celah ]</span>';
  }
  return '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40">[ ' + escapeHtml(tag || 'Insiden Siber') + ' ]</span>';
}

/**
 * Format teks inline markdown (bold & italic) menjadi HTML yang aman
 * @param {string} str
 * @returns {string}
 */
export function formatMarkdownInline(str) {
  if (!str) return '';
  let res = escapeHtml(String(str).trim());
  res = res.replace(/\*\*\*(.*?)\*\*\*/g, '<strong class="font-bold text-[#00d4ff]"><em>$1</em></strong>');
  res = res.replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>');
  res = res.replace(/\*(.*?)\*/g, '<em class="text-[#8892b0] not-italic">$1</em>');
  return res;
}

/**
 * Merender blok Fakta & Kronologi Kasus Teramai dengan batasan visual yang jelas antara Kasus Teramai dan Kronologi
 * Mengganti label "Kasus Teramai (#1) & Liputan" menjadi "Kasus Teramai"
 * @param {string|Array} text
 * @returns {string} HTML string
 */
export function formatFaktaKronologiModalHtml(text) {
  if (!text || text === '-' || text === 'None') {
    return '<p class="text-xs text-[#7d8ca6] italic font-mono">Tidak ada catatan data.</p>';
  }

  let rawStr = '';
  if (Array.isArray(text)) {
    rawStr = text.join('\n');
  } else {
    rawStr = String(text).trim();
    if (rawStr.startsWith('[') && rawStr.endsWith(']')) {
      try {
        const parsed = JSON.parse(rawStr.replace(/'/g, '"'));
        if (Array.isArray(parsed)) rawStr = parsed.join('\n');
      } catch (e) {
        rawStr = rawStr.slice(1, -1).replace(/^['"]|['"]$/g, '');
      }
    }
  }

  // Ganti "Kasus Teramai (#1) & Liputan" atau variasi (#1) menjadi "Kasus Teramai"
  let cleanStr = rawStr
    .replace(/\*\*Kasus Teramai\s*(?:\(#1\))?\s*(?:&\s*Liputan)?\*\*\s*:/gi, '**Kasus Teramai**:')
    .replace(/Kasus Teramai\s*(?:\(#1\))?\s*(?:&\s*Liputan)?\s*:/gi, 'Kasus Teramai:');

  // Deteksi pemisah bagian Kronologi & Metode Serangan
  const kronologiRegex = /(?:^|\n)\s*[-*•]?\s*\**(?:\d+\.\s*)?(?:(?:Aktor[^\n*:]*?)?|(?:Alur\s*(?:&|dan)?\s*)?)Kronologi(?:\s*(?:&|dan)?\s*Metode)?(?:\s*Serangan)?\**\s*:\s*/i;
  const matchIdx = cleanStr.search(kronologiRegex);

  let kasusTeramaiText = cleanStr;
  let kronologiText = '';

  if (matchIdx !== -1) {
    kasusTeramaiText = cleanStr.substring(0, matchIdx).trim();
    kronologiText = cleanStr.substring(matchIdx).replace(kronologiRegex, '').trim();
  }

  // Bersihkan awalan label agar tidak duplikat dengan header badge box
  kasusTeramaiText = kasusTeramaiText
    .replace(/^\s*[-*•]?\s*\**Kasus\s*Teramai(?:\s*\(#1\))?(?:\s*&\s*Liputan)?\**\s*:\s*/i, '')
    .trim();

  if (!kronologiText) {
    return `
      <div class="p-3.5 sm:p-4 rounded-xl bg-[#0a1628]/85 border border-[#1a3a5c] shadow-xs">
        <div class="flex items-center gap-1.5 text-xs font-mono font-bold text-[#00d4ff] mb-2 uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">campaign</span>
          <span>[ KASUS TERAMAI ]</span>
        </div>
        <p class="text-xs text-[#e0f0ff] leading-relaxed font-sans">${formatMarkdownInline(kasusTeramaiText)}</p>
      </div>
    `;
  }

  return `
    <div class="space-y-3 pt-0.5">
      <!-- 1. Blok Kasus Teramai -->
      <div class="p-3.5 sm:p-4 rounded-xl bg-[#0a1628]/85 border border-[#1a3a5c] shadow-xs">
        <div class="flex items-center gap-1.5 text-xs font-mono font-bold text-[#00d4ff] mb-2 uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">campaign</span>
          <span>[ KASUS TERAMAI ]</span>
        </div>
        <p class="text-xs text-[#e0f0ff] leading-relaxed font-sans">${formatMarkdownInline(kasusTeramaiText)}</p>
      </div>

      <!-- 2. Blok Kronologi & Metode Serangan (Terpisah dengan Batasan Jelas) -->
      <div class="p-3.5 sm:p-4 rounded-xl bg-[#0a1628]/85 border border-[#1a3a5c] shadow-xs">
        <div class="flex items-center gap-1.5 text-xs font-mono font-bold text-[#00d4ff] mb-2 uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">timeline</span>
          <span>[ KRONOLOGI &amp; METODE SERANGAN ]</span>
        </div>
        <p class="text-xs text-[#e0f0ff] leading-relaxed font-sans">${formatMarkdownInline(kronologiText)}</p>
      </div>
    </div>
  `;
}

/**
 * Merender blok Dampak & Mitigasi Spesifik Kasus dengan batasan visual yang jelas antara Dampak dan Mitigasi
 * @param {string|Array} text
 * @returns {string} HTML string
 */
export function formatDampakMitigasiModalHtml(text) {
  if (!text || text === '-' || text === 'None') {
    return '<p class="text-xs text-[#7d8ca6] italic font-mono">Tidak ada catatan data.</p>';
  }

  let rawStr = '';
  if (Array.isArray(text)) {
    rawStr = text.join('\n');
  } else {
    rawStr = String(text).trim();
    if (rawStr.startsWith('[') && rawStr.endsWith(']')) {
      try {
        const parsed = JSON.parse(rawStr.replace(/'/g, '"'));
        if (Array.isArray(parsed)) rawStr = parsed.join('\n');
      } catch (e) {
        rawStr = rawStr.slice(1, -1).replace(/^['"]|['"]$/g, '');
      }
    }
  }

  // Deteksi pemisah bagian Mitigasi Teknis Spesifik
  const mitigasiRegex = /(?:^|\n)\s*[-*•]?\s*\**(?:\d+\.\s*)?(?:Rekomendasi\s*)?Mitigasi(?:\s*(?:Teknis|Spesifik|Preventif|Aksi|Taktis))*\**\s*:?\s*/i;
  const matchIdx = rawStr.search(mitigasiRegex);

  let dampakText = rawStr;
  let mitigasiText = '';

  if (matchIdx !== -1) {
    dampakText = rawStr.substring(0, matchIdx).trim();
    mitigasiText = rawStr.substring(matchIdx).replace(mitigasiRegex, '').trim();
  }

  // Bersihkan label awalan Dampak Spesifik Kasus dari teks isinya
  dampakText = dampakText
    .replace(/^\s*[-*•]?\s*\**Dampak(?:\s*Spesifik)?(?:\s*Kasus)?\**\s*:\s*/i, '')
    .trim();

  let mitigasiHtml = '';
  if (mitigasiText) {
    const rawLines = mitigasiText.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
    const items = rawLines.map((line, idx) => {
      const matchItem = line.match(/^(?:[-*•]|\d+\.)?\s*(?:\*\*(.*?)\*\*|\*(.*?)\*|\[(.*?)\])?\s*:?\s*(.*)$/);
      let num = idx + 1;
      let title = '';
      let body = line;

      if (matchItem) {
        title = (matchItem[1] || matchItem[2] || matchItem[3] || '').trim();
        body = (matchItem[4] || '').trim();
      }

      if (title && title.toLowerCase() !== 'mitigasi teknis spesifik') {
        const bodyHtml = body ? `: ${formatMarkdownInline(body)}` : '';
        return `
          <li class="flex items-start gap-2.5 text-xs text-[#e0f0ff] leading-relaxed">
            <span class="px-1.5 py-0.5 rounded bg-[#0d2137] text-[#00ff88] border border-[#00ff88]/30 font-mono font-bold text-[10px] shrink-0 mt-0.5">#${num}</span>
            <div class="flex-1 min-w-0">
              <strong class="font-bold text-[#00ff88] font-mono">[ ${escapeHtml(title)} ]</strong>
              <span class="text-[#e0f0ff] font-sans pl-1">${bodyHtml}</span>
            </div>
          </li>
        `;
      }

      const cleanLine = line.replace(/^[-*•]\s+/, '').replace(/^\d+\.\s+/, '');
      return `
        <li class="flex items-start gap-2.5 text-xs text-[#e0f0ff] leading-relaxed">
          <span class="w-1.5 h-1.5 rounded-full bg-[#00ff88] shrink-0 mt-1.5 shadow-[0_0_6px_#00ff88]"></span>
          <span class="flex-1">${formatMarkdownInline(cleanLine)}</span>
        </li>
      `;
    }).join('');

    mitigasiHtml = `<ul class="space-y-2 mt-2">${items}</ul>`;
  }

  if (!mitigasiText) {
    return `
      <div class="p-3.5 sm:p-4 rounded-xl bg-[#0a1628]/85 border border-[#1a3a5c] shadow-xs">
        <div class="flex items-center gap-1.5 text-xs font-mono font-bold text-[#ff8800] mb-2 uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">warning</span>
          <span>[ DAMPAK SPESIFIK KASUS ]</span>
        </div>
        <p class="text-xs text-[#e0f0ff] leading-relaxed font-sans">${formatMarkdownInline(dampakText)}</p>
      </div>
    `;
  }

  return `
    <div class="space-y-3 pt-0.5">
      <!-- 1. Blok Dampak Spesifik Kasus -->
      <div class="p-3.5 sm:p-4 rounded-xl bg-[#0a1628]/85 border border-[#1a3a5c] shadow-xs">
        <div class="flex items-center gap-1.5 text-xs font-mono font-bold text-[#ff8800] mb-2 uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">warning</span>
          <span>[ DAMPAK SPESIFIK KASUS ]</span>
        </div>
        <p class="text-xs text-[#e0f0ff] leading-relaxed font-sans">${formatMarkdownInline(dampakText)}</p>
      </div>

      <!-- 2. Blok Mitigasi Teknis Spesifik (Terpisah dengan Batasan Jelas) -->
      <div class="p-3.5 sm:p-4 rounded-xl bg-[#0a1628]/85 border border-[#1a3a5c] shadow-xs">
        <div class="flex items-center gap-1.5 text-xs font-mono font-bold text-[#00ff88] mb-2 uppercase tracking-wider">
          <span class="material-symbols-outlined text-[15px]">verified_user</span>
          <span>[ MITIGASI TEKNIS SPESIFIK ]</span>
        </div>
        ${mitigasiHtml}
      </div>
    </div>
  `;
}

/**
 * Memformat teks analisis menjadi HTML rapi bertema dark
 * @param {string} text 
 * @returns {string}
 */
export function formatPoinModalHtml(text) {
  if (!text || text === '-' || text === 'None') {
    return '<p class="text-xs text-[#7d8ca6] italic font-mono">Tidak ada catatan data.</p>';
  }

  let lines = [];
  if (Array.isArray(text)) {
    lines = text.map(l => String(l).trim()).filter(l => l.length > 0);
  } else {
    let rawStr = String(text).trim();
    if (rawStr.startsWith('[') && rawStr.endsWith(']')) {
      rawStr = rawStr.slice(1, -1).trim();
      lines = rawStr.split(/',\s*'/).map(l => l.replace(/^['"]|['"]$/g, '').trim()).filter(l => l.length > 0);
    } else {
      lines = rawStr.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
    }
  }

  const hasBullets = lines.some(l => /^[-*•]\s+/.test(l) || /^\d+\.\s+/.test(l)) || lines.length > 1;

  if (hasBullets) {
    const listItems = lines.map(line => {
      let cleanLine = line.replace(/^[-*•]\s+/, '').replace(/^\d+\.\s+/, '').trim();
      cleanLine = cleanLine.replace(/^['"]+|['"]+$/g, '').trim();
      cleanLine = cleanLine.replace(/\*{3,}/g, '**');

      const formatted = escapeHtml(cleanLine).replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>');
      return `
        <li class="flex items-start gap-2.5 text-xs text-[#e0f0ff] leading-relaxed">
          <span class="w-1.5 h-1.5 rounded-full bg-[#00d4ff] shrink-0 mt-1.5 shadow-[0_0_6px_#00d4ff]"></span>
          <span class="flex-1">${formatted}</span>
        </li>
      `;
    }).join('');
    return `<ul class="space-y-2.5">${listItems}</ul>`;
  }

  let raw = (lines[0] || String(text)).replace(/\*{3,}/g, '**');
  const formatted = escapeHtml(raw).replace(/\*\*(.*?)\*\*/g, '<strong class="font-bold text-[#00d4ff]">$1</strong>');
  return `<p class="text-xs text-[#e0f0ff] leading-relaxed">${formatted}</p>`;
}

/**
 * Merender daftar insiden teramai lainnya (#2, #3, dst.) di dalam modal wilayah
 * @param {Object} item Objek data wilayah
 * @returns {string} HTML string
 */
export function renderDaftarInsidenLainnyaHtml(item) {
  const list = Array.isArray(item?.daftar_insiden_lainnya) ? item.daftar_insiden_lainnya : [];
  if (list.length > 0) {
    const rows = list.map((inc, idx) => {
      const rank = inc.peringkat || (idx + 2);
      const judul = inc.judul || '-';
      const sumber = inc.sumber || 'Media';
      const kat = inc.kategori || inc.tag || 'Insiden Siber';
      const safeJudul = escapeHtml(judul).replace(/'/g, "\\'");
      const safeSumber = escapeHtml(sumber).replace(/'/g, "\\'");
      const safeLink = escapeHtml(inc.link || '').replace(/'/g, "\\'");

      const judulHtml = `
        <button type="button" onclick="window.sorotAtauBukaBeritaArsip('${safeJudul}', '${safeSumber}', '', '${safeLink}')"
          class="text-left hover:text-[#00d4ff] hover:underline font-semibold text-[#e0f0ff] cursor-pointer inline-flex items-baseline gap-1 focus-visible:outline-none leading-snug break-words">
          <span>${escapeHtml(judul)}</span>
          <span class="material-symbols-outlined text-[13px] text-[#00d4ff] shrink-0" aria-hidden="true">travel_explore</span>
        </button>
      `;

      return `
        <li class="flex items-start justify-between gap-3 py-2 border-b border-[#1a3a5c]/60 last:border-b-0 text-xs">
          <div class="flex items-start gap-2 min-w-0 flex-1">
            <span class="px-1.5 py-0.5 rounded bg-[#112240] text-[#a78bfa] font-mono font-bold text-[10px] border border-[#a78bfa]/30 shrink-0">#${rank}</span>
            <div class="space-y-0.5 min-w-0 flex-1">
              <div>${judulHtml}</div>
              <div class="text-[11px] font-mono text-[#7d8ca6]">${escapeHtml(sumber)} • ${escapeHtml(kat)}</div>
            </div>
          </div>
        </li>
      `;
    }).join('');
    return `<ul class="divide-y divide-[#1a3a5c]/40">${rows}</ul>`;
  }

  if (item?.teks_insiden_lainnya) {
    return formatPoinModalHtml(item.teks_insiden_lainnya);
  }

  return '<p class="text-xs text-[#7d8ca6] italic font-mono">Tidak ada insiden teramai lainnya yang tercatat di wilayah ini pada periode 7 hari terakhir.</p>';
}

/**
 * Membuka modal popup detail analisis ancaman
 * @param {string} wilayahKey 'intl' | 'nas' | 'jatim'
 */
export function bukaModalDetailKasus(wilayahKey) {
  const item = currentKasusData[wilayahKey];
  const meta = WILAYAH_META[wilayahKey] || WILAYAH_META.intl;
  const overlay = document.getElementById('modal-detail-ancaman-overlay');
  const box = document.getElementById('modal-detail-ancaman-box');
  if (!overlay || !box) return;

  const titleEl = document.getElementById('modal-ancaman-judul');
  const sumberEl = document.getElementById('modal-ancaman-sumber');
  const metaHeader = document.getElementById('modal-ancaman-meta-header');
  const urgensiEl = document.getElementById('modal-ancaman-urgensi');
  const potensiEl = document.getElementById('modal-ancaman-potensi');
  const sampelContentEl = document.getElementById('modal-ancaman-sampel-content');
  const lainnyaContentEl = document.getElementById('modal-ancaman-lainnya-content');
  const linkEl = document.getElementById('modal-ancaman-link');

  const isKosong = !item || !item.ada_kejadian || item.nama_kejadian === '-' || item.nama_kejadian === '' || item.nama_kejadian === 'None';
  const isuName = item?.isu_utama || (isKosong ? 'Kondusif' : (item?.kategori || 'Insiden Siber'));

  if (titleEl) {
    titleEl.textContent = isKosong
      ? `Analisis Ancaman Wilayah: ${meta.label}`
      : `Tren Ancaman: ${isuName}`;
  }
  if (sumberEl) {
    sumberEl.innerHTML = '';
  }
  if (metaHeader) metaHeader.style.display = 'none';

  if (urgensiEl) urgensiEl.innerHTML = formatFaktaKronologiModalHtml(item?.fakta_kronologi || item?.alasan_urgensi);
  if (potensiEl) potensiEl.innerHTML = formatDampakMitigasiModalHtml(item?.dampak_mitigasi || item?.potensi_ancaman);
  if (lainnyaContentEl) lainnyaContentEl.innerHTML = renderDaftarInsidenLainnyaHtml(item);

  // Render sampel contoh kejadian relevan (Kasus Teratas) di dalam modal
  if (sampelContentEl) {
    if (isKosong) {
      sampelContentEl.innerHTML = '<p class="text-xs text-[#7d8ca6] italic font-mono">Nihil laporan insiden siber aktif pada wilayah ini dalam 7 hari terakhir.</p>';
    } else {
      const lokasiHtml = item.lokasi && item.lokasi !== '-' ? `
        <span class="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[#8892b0] bg-[#0d2137] px-2.5 py-0.5 rounded border border-[#1a3a5c]">
          <span class="material-symbols-outlined text-[11px] text-[#00d4ff]">location_on</span>
          ${escapeHtml(item.lokasi)}
        </span>
      ` : '';
      const ringkasanHtml = item.ringkasan_kasus ? `
        <p class="text-[#8892b0] text-xs leading-relaxed pt-1 font-sans">${escapeHtml(item.ringkasan_kasus)}</p>
      ` : '';

      const safeNama = escapeHtml(item.nama_kejadian).replace(/'/g, "\\'");
      const safeSumber = escapeHtml(item.sumber || '').replace(/'/g, "\\'");
      const safeRingkasan = escapeHtml(item.ringkasan_kasus || '').replace(/'/g, "\\'");
      const safeLink = escapeHtml(item.link || '').replace(/'/g, "\\'");

      sampelContentEl.innerHTML = `
        <div class="space-y-1.5">
          <div class="flex items-center gap-1.5 flex-wrap mb-1">
            ${lokasiHtml}
            <span class="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[#00ff88] bg-[#0d2137] px-2.5 py-0.5 rounded border border-[#00ff88]/30">
              <span class="material-symbols-outlined text-[11px]">article</span>
              [ Kasus Teratas ]
            </span>
          </div>
          <h5 class="text-sm font-bold text-[#e0f0ff] leading-snug font-['Sora']">
            <button type="button" onclick="window.sorotAtauBukaBeritaArsip('${safeNama}', '${safeSumber}', '${safeRingkasan}', '${safeLink}')"
              class="text-left hover:text-[#00d4ff] hover:underline inline-flex items-baseline gap-1 text-[#e0f0ff] cursor-pointer focus-visible:outline-none transition-colors"
              title="Klik untuk menavigasi & menyorot berita di arsip">
              <span>${escapeHtml(item.nama_kejadian)}</span>
              <span class="material-symbols-outlined text-[13px] text-[#00d4ff] shrink-0" aria-hidden="true">travel_explore</span>
            </button>
          </h5>
          ${ringkasanHtml}
          <div class="flex items-center text-xs text-[#7d8ca6] pt-1 font-mono">
            <span class="inline-flex items-center gap-1 font-medium" title="${escapeHtml(item.sumber || '')}">
              <span class="material-symbols-outlined text-[13px] text-[#00d4ff] shrink-0">newspaper</span>
              <span>${escapeHtml(item.sumber || 'Media Intelijen')}</span>
            </span>
          </div>
        </div>
      `;
    }
  }

  // Atur link footer berita sumber
  if (linkEl) {
    const hasLink = !isKosong && item.link && item.link !== '#' && !item.link.startsWith('javascript:');
    if (hasLink) {
      linkEl.href = item.link;
      linkEl.style.display = 'inline-flex';
    } else {
      linkEl.style.display = 'none';
    }
  }

  // Buka modal dengan transisi
  overlay.classList.remove('hidden');
  overlay.classList.add('flex');
  overlay.setAttribute('aria-hidden', 'false');

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      overlay.classList.remove('opacity-0', 'pointer-events-none');
      overlay.classList.add('opacity-100', 'pointer-events-auto');

      box.classList.remove('scale-95', 'opacity-0', 'translate-y-4');
      box.classList.add('scale-100', 'opacity-100', 'translate-y-0');

      const closeBtn = box.querySelector('button[title]');
      if (closeBtn) closeBtn.focus();
    });
  });

  document.body.style.overflow = 'hidden';
}

/**
 * Menutup modal popup detail analisis ancaman
 */
export function tutupModalDetailKasus() {
  const overlay = document.getElementById('modal-detail-ancaman-overlay');
  const box = document.getElementById('modal-detail-ancaman-box');
  if (!overlay || !box) return;

  overlay.classList.remove('opacity-100', 'pointer-events-auto');
  overlay.classList.add('opacity-0', 'pointer-events-none');

  box.classList.remove('scale-100', 'opacity-100', 'translate-y-0');
  box.classList.add('scale-95', 'opacity-0', 'translate-y-4');

  setTimeout(() => {
    overlay.classList.remove('flex');
    overlay.classList.add('hidden');
    overlay.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
  }, 200);
}

/**
 * Handler penutup modal jika mengklik area luar (backdrop)
 * @param {Event} event 
 */
export function tutupModalJikaLuarKasus(event) {
  const box = document.getElementById('modal-detail-ancaman-box');
  if (box && !box.contains(event.target)) {
    tutupModalDetailKasus();
  }
}

// Pasang fungsi global ke window scope agar atribut onclick di HTML dapat memanggilnya
if (typeof window !== 'undefined') {
  window.bukaModalDetailKasus = bukaModalDetailKasus;
  window.tutupModalDetailKasus = tutupModalDetailKasus;
  window.tutupModalJikaLuarKasus = tutupModalJikaLuarKasus;

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const overlay = document.getElementById('modal-detail-ancaman-overlay');
      if (overlay && !overlay.classList.contains('hidden')) {
        tutupModalDetailKasus();
      }
    }
  });
}

/**
 * Menavigasi ke kartu berita di Arsip, melakukan smooth scroll dengan animasi,
 * lalu memberikan efek highlight pendaran neon (glow) agar kartu terlihat menyala.
 * Jika kartu tidak berada pada tampilan aktif, langsung membuka rangkuman modal berita.
 * @param {string} judul Judul berita yang dicari
 * @param {string} sumber Nama sumber media
 * @param {string} ringkasan Ringkasan singkat
 * @param {string} link Link artikel berita
 */
export async function sorotAtauBukaBeritaArsip(judul, sumber = '', ringkasan = '', link = '') {
  tutupModalDetailKasus();

  const targetJudul = (judul || '').trim();
  const safeSumber = (sumber || 'Media Intelijen').trim();
  const safeRingkasan = (ringkasan || '').trim();
  const safeLink = (link && link !== '#' && !link.startsWith('javascript:')) ? link : '';

  // 1. Pindah ke tab arsip
  const alpineRoot = document.querySelector('[x-data]');
  if (alpineRoot && window.Alpine) {
    try {
      const alpineData = window.Alpine.$data(alpineRoot);
      if (alpineData && alpineData.tabAktif !== 'arsip') {
        alpineData.tabAktif = 'arsip';
      }
    } catch (e) {
      console.warn('Gagal beralih ke tab arsip Alpine:', e);
    }
  }

  // Pastikan data arsip termuat
  if (window.muatTabArsip) {
    await window.muatTabArsip();
  }

  await new Promise(r => setTimeout(r, 260));

  // Bersihkan search input arsip
  const searchInput = document.getElementById('arsip-search-input');
  if (searchInput && searchInput.value) {
    searchInput.value = '';
    const searchClear = document.getElementById('arsip-search-clear');
    if (searchClear) searchClear.style.display = 'none';
    if (window.filterArsipCards) window.filterArsipCards('');
  }

  // 2. Cari elemen kartu berita di DOM
  const cards = Array.from(document.querySelectorAll('#arsip-card-container article, main article'));
  let matchedCard = null;

  if (targetJudul) {
    const targetKeywords = targetJudul.toLowerCase().slice(0, 35);
    matchedCard = cards.find(card => {
      const h3 = (card.querySelector('h3')?.textContent || '').toLowerCase();
      const txt = (card.getAttribute('data-search-text') || '').toLowerCase();
      return h3.includes(targetKeywords) || txt.includes(targetKeywords);
    });
  }

  // 3. Jika kartu ditemukan di DOM: scroll animasi & nyalakan efek glow
  if (matchedCard) {
    matchedCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setTimeout(() => {
      matchedCard.classList.remove('animate-target-highlight');
      void matchedCard.offsetWidth; // trigger reflow
      matchedCard.classList.add('animate-target-highlight');
    }, 280);

    if (window.tampilkanToast) {
      window.tampilkanToast('Berita ditemukan dan disorot di arsip', 'sukses', 3000);
    }
  } else {
    // 4. Jika kartu tidak ditemukan pada rentang aktif, buka langsung modal rangkuman berita
    if (window.bukaModal) {
      window.bukaModal({
        judul: targetJudul || 'Laporan Insiden Siber Teramai',
        teksLengkap: safeRingkasan || `Laporan insiden "${targetJudul}" dari sumber ${safeSumber}.`,
        sumber: safeSumber,
        link: safeLink,
        pillLabel: '[ Insiden Teramai ]',
        pillClass: 'bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40 font-mono'
      });
    }
    if (window.tampilkanToast) {
      window.tampilkanToast('Membuka rangkuman berita intelijen', 'info', 3000);
    }
  }
}

if (typeof window !== 'undefined') {
  window.sorotAtauBukaBeritaArsip = sorotAtauBukaBeritaArsip;
}

/**
 * Merender satu kartu KPI insiden wilayah terpilih
 * Menampilkan nama kejadian spesifik (#1)
 * @param {Object} item Data insiden wilayah
 * @param {string} wilayahKey Kode wilayah ('intl', 'nas', 'jatim')
 * @returns {string} HTML string
 */
export function renderSingleIncidentCard(item, wilayahKey) {
  const meta = WILAYAH_META[wilayahKey] || WILAYAH_META.intl;
  const isKosong = !item || !item.ada_kejadian || item.nama_kejadian === '-' || item.nama_kejadian === '' || item.nama_kejadian === 'None' || (item?.isu_utama && item.isu_utama.toLowerCase().includes('kondusif'));
  const isuUtama = isKosong ? 'Kondusif' : (item?.isu_utama || item?.kategori || 'Insiden Siber');
  const namaKejadian = isKosong ? '' : (item.nama_kejadian || '');

  return `
    <!-- Top Header KPI Style: Wilayah Left, Icon Right -->
    <div class="flex items-center justify-between gap-2 pb-3 border-b border-[#1a3a5c]">
      <div class="flex items-center gap-2 flex-wrap">
        <h4 class="text-[11px] sm:text-xs font-mono font-bold text-[#8892b0] uppercase tracking-wider leading-tight">[ ${escapeHtml(meta.label.toUpperCase())} ]</h4>
      </div>
      <div class="${meta.iconColor} shrink-0">
        <span class="material-symbols-outlined text-lg sm:text-xl" aria-hidden="true">${meta.icon}</span>
      </div>
    </div>

    <!-- Main Metric: Hasil Klasifikasi Tren (Bukan Judul Artikel) -->
    <div class="my-auto py-3.5 space-y-2">
      <div class="text-xl sm:text-2xl font-extrabold text-[#e0f0ff] tracking-tight font-['Sora'] leading-tight break-words min-w-0" title="Klasifikasi Tren: ${escapeHtml(isuUtama)}">
        ${escapeHtml(isuUtama)}
      </div>
      ${!isKosong && namaKejadian && namaKejadian !== '-' && !namaKejadian.toLowerCase().includes('kondusif') ? `
        <div class="text-xs text-[#8892b0] font-sans line-clamp-2 pt-1" title="${escapeHtml(namaKejadian)}">
          <span class="text-[#7d8ca6] font-mono text-[11px] font-semibold">Kasus Teratas:</span> ${escapeHtml(namaKejadian)}
        </div>
      ` : ''}
      ${!isKosong && item?.sumber && item.sumber !== '-' ? `<div class="text-[11px] font-mono text-[#7d8ca6] truncate">Sumber: ${escapeHtml(item.sumber)}</div>` : ''}
    </div>

    <!-- Bottom Footer: Tombol Detail Ancaman Chamfered -->
    <div class="pt-3 border-t border-[#1a3a5c] flex items-center justify-between gap-2 flex-wrap">
      <button type="button" 
        onclick="window.bukaModalDetailKasus('${wilayahKey}')"
        class="btn-chamfer text-xs whitespace-nowrap shrink-0" style="height:32px;padding:0 12px;"
        title="Buka rincian analisis ancaman ${escapeHtml(meta.label)}">
        <span>[ DETAIL ANALISIS → ]</span>
      </button>
      ${isKosong ? '<span class="text-[11px] font-mono font-medium text-[#7d8ca6] whitespace-nowrap shrink-0">[ Nihil Insiden ]</span>' : ''}
    </div>
  `;
}

/**
 * Helper memperkaya data wilayah dengan jumlah_liputan & daftar_insiden_lainnya dari cluster
 */
function enrichWilayahItem(aiItem, clusterList, defaultLokasi) {
  const clusters = Array.isArray(clusterList) ? clusterList : [];
  const topCluster = clusters[0] || null;
  const topTag = (topCluster?.tag || aiItem?.kategori || aiItem?.isu_utama || '').toLowerCase();

  const isMatchingTrend = (c) => {
    const t = (c.tag || c.kategori || '').toLowerCase();
    if (topTag && (t === topTag || t.includes(topTag) || topTag.includes(t))) return true;
    const txt = `${c.judul || ''} ${c.ringkasan || ''} ${c.kata_kunci || ''}`.toLowerCase();
    if (topTag.includes('malware') && (txt.includes('malware') || txt.includes('trojan') || txt.includes('stealer') || txt.includes('infostealer') || txt.includes('backdoor'))) return true;
    if (topTag.includes('ransom') && (txt.includes('ransom') || txt.includes('tebusan') || txt.includes('pemerasan'))) return true;
    if (topTag.includes('bocor') && (txt.includes('bocor') || txt.includes('leak') || txt.includes('breach') || txt.includes('data'))) return true;
    if ((topTag.includes('peretasan') || topTag.includes('web')) && (txt.includes('peretasan') || txt.includes('deface') || txt.includes('diretas') || txt.includes('hacker') || txt.includes('web shell'))) return true;
    if ((topTag.includes('celah') || topTag.includes('exploit')) && (txt.includes('celah') || txt.includes('vulnerability') || txt.includes('exploit') || txt.includes('zero-day') || txt.includes('rce'))) return true;
    if (topTag.includes('phishing') && (txt.includes('phishing') || txt.includes('quishing') || txt.includes('penipuan') || txt.includes('scam'))) return true;
    return false;
  };

  const matchingClusters = clusters.slice(1).filter(isMatchingTrend);
  const fallbackList = matchingClusters.length > 0 ? matchingClusters : clusters.slice(1, 6);
  const lainnya = fallbackList.slice(0, 5).map((c, idx) => ({
    peringkat: idx + 2,
    judul: c.judul || '-',
    jumlah_liputan: Number(c.jumlah_liputan || 1),
    sumber: c.sumber || 'Media',
    link: c.link || '#',
    kategori: c.tag || c.kategori || 'Insiden Siber'
  }));

  if (aiItem) {
    const aiLainnya = Array.isArray(aiItem.daftar_insiden_lainnya) ? aiItem.daftar_insiden_lainnya : [];
    const aiMatching = aiLainnya.filter(isMatchingTrend);
    const finalLainnya = (aiMatching.length > 0) ? aiMatching : (aiLainnya.length > 0 ? aiLainnya : lainnya);

    return {
      ...aiItem,
      jumlah_liputan: Number(aiItem.jumlah_liputan || topCluster?.jumlah_liputan || (aiItem.ada_kejadian ? 1 : 0)),
      daftar_insiden_lainnya: finalLainnya
    };
  }

  if (topCluster) {
    return {
      ada_kejadian: true,
      isu_utama: topCluster.tag || 'Insiden Siber',
      nama_kejadian: topCluster.judul,
      jumlah_liputan: Number(topCluster.jumlah_liputan || 1),
      ringkasan_kasus: topCluster.ringkasan_atau_narasi || topCluster.ringkasan || '',
      kategori: topCluster.tag || 'Insiden Siber',
      lokasi: defaultLokasi,
      alasan_urgensi: `- **Kasus Teramai**: **${topCluster.judul}** (${Number(topCluster.jumlah_liputan || 1)} liputan media).`,
      potensi_ancaman: `- **Mitigasi Spesifik**: Evaluasi kontrol keamanan sistem terkait vektor **${topCluster.tag || 'Insiden Siber'}**.`,
      daftar_insiden_lainnya: lainnya,
      sumber: topCluster.sumber,
      link: topCluster.link,
    };
  }

  return null;
}

/**
 * Merender 3 kolom sorotan insiden wilayah KPI: Internasional, Nasional, dan Jawa Timur
 * @param {Object} stat Objek data statistik tren
 */
export function renderKasusInsidenWilayah(stat) {
  const cardIntl = document.getElementById('card-kasus-intl');
  const cardNas = document.getElementById('card-kasus-nas');
  const cardJatim = document.getElementById('card-kasus-jatim');

  if (!stat) return;

  const aiData = stat.kasus_wilayah_ai || {};
  const clusterData = stat.kasus_wilayah || {};

  const intlItem = enrichWilayahItem(aiData.internasional, clusterData.internasional, 'Global');
  const nasItem = enrichWilayahItem(aiData.nasional, clusterData.nasional, 'Indonesia');
  const jatimItem = enrichWilayahItem(aiData.jawa_timur, clusterData.jawa_timur, 'Jawa Timur');

  currentKasusData.intl = intlItem;
  currentKasusData.nas = nasItem;
  currentKasusData.jatim = jatimItem;

  if (cardIntl) cardIntl.innerHTML = renderSingleIncidentCard(intlItem, 'intl');
  if (cardNas) cardNas.innerHTML = renderSingleIncidentCard(nasItem, 'nas');
  if (cardJatim) cardJatim.innerHTML = renderSingleIncidentCard(jatimItem, 'jatim');
}
