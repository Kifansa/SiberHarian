import { escapeHtml } from './tren-utils.js';

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
  const linkEl = document.getElementById('modal-ancaman-link');

  const isKosong = !item || !item.ada_kejadian || item.nama_kejadian === '-' || item.nama_kejadian === '' || item.nama_kejadian === 'None';
  const isuName = item?.isu_utama || (isKosong ? 'Kondisi Kondusif' : (item?.kategori || 'Insiden Siber'));

  if (titleEl) titleEl.textContent = `Analisis Ancaman Wilayah: ${meta.label}`;
  if (sumberEl) {
      sumberEl.innerHTML = `
      <span class="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono font-bold bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40 shadow-[0_0_10px_rgba(0,212,255,0.2)]">
        <span class="material-symbols-outlined text-[13px] text-[#00d4ff]">travel_explore</span>
        [ Sintesis Intelijen RAG: ${escapeHtml(meta.label)} (${escapeHtml(isuName)}) ]
      </span>
    `;
  }
  if (metaHeader) metaHeader.style.display = 'flex';

  if (urgensiEl) urgensiEl.innerHTML = formatPoinModalHtml(item?.alasan_urgensi);
  if (potensiEl) potensiEl.innerHTML = formatPoinModalHtml(item?.potensi_ancaman);

  // Render sampel contoh kejadian relevan di dalam modal
  if (sampelContentEl) {
    if (isKosong) {
      sampelContentEl.innerHTML = '<p class="text-xs text-[#7d8ca6] italic font-mono">Nihil laporan insiden siber aktif pada wilayah ini dalam 7 hari terakhir.</p>';
    } else {
      const hasLink = item.link && item.link !== '#' && !item.link.startsWith('javascript:');
      const lokasiHtml = item.lokasi && item.lokasi !== '-' ? `
        <span class="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[#8892b0] bg-[#0d2137] px-2.5 py-0.5 rounded border border-[#1a3a5c]">
          <span class="material-symbols-outlined text-[11px] text-[#00d4ff]">location_on</span>
          ${escapeHtml(item.lokasi)}
        </span>
      ` : '';
      const ringkasanHtml = item.ringkasan_kasus ? `
        <p class="text-[#8892b0] text-xs leading-relaxed pt-1 font-sans">${escapeHtml(item.ringkasan_kasus)}</p>
      ` : '';

      sampelContentEl.innerHTML = `
        <div class="space-y-1.5">
          <div class="flex items-center gap-1.5 flex-wrap mb-1">
            ${lokasiHtml}
            <span class="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-[#00ff88] bg-[#0d2137] px-2.5 py-0.5 rounded border border-[#00ff88]/30">
              <span class="material-symbols-outlined text-[11px]">article</span>
              [ Studi Kasus ]
            </span>
          </div>
          <h5 class="text-sm font-bold text-[#e0f0ff] leading-snug font-['Sora']">
            ${hasLink 
              ? `<a href="${escapeHtml(item.link)}" target="_blank" rel="noopener noreferrer" class="hover:text-[#00d4ff] hover:underline inline-flex items-baseline gap-1" title="Buka tautan berita sumber">
                   <span>${escapeHtml(item.nama_kejadian)}</span>
                   <span class="material-symbols-outlined text-[13px] text-[#00d4ff] shrink-0" aria-hidden="true">open_in_new</span>
                 </a>`
              : escapeHtml(item.nama_kejadian)
            }
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
 * Merender satu kartu KPI insiden wilayah terpilih
 * @param {Object} item Data insiden wilayah
 * @param {string} wilayahKey Kode wilayah ('intl', 'nas', 'jatim')
 * @returns {string} HTML string
 */
export function renderSingleIncidentCard(item, wilayahKey) {
  const meta = WILAYAH_META[wilayahKey] || WILAYAH_META.intl;
  const isKosong = !item || !item.ada_kejadian || item.nama_kejadian === '-' || item.nama_kejadian === '' || item.nama_kejadian === 'None';
  const isuUtama = item?.isu_utama || (isKosong ? 'Kondisi Kondusif' : (item?.kategori || 'Insiden Siber'));

  return `
    <!-- Top Header KPI Style: Wilayah Left, Icon Right -->
    <div class="flex items-center justify-between gap-3 pb-3 border-b border-[#1a3a5c]">
      <div>
        <h4 class="text-[11px] sm:text-xs font-mono font-bold text-[#8892b0] uppercase tracking-wider leading-tight">[ ${escapeHtml(meta.label.toUpperCase())} ]</h4>
      </div>
      <div class="${meta.iconColor}">
        <span class="material-symbols-outlined text-lg sm:text-xl" aria-hidden="true">${meta.icon}</span>
      </div>
    </div>

    <!-- Main Metric: Threat Issue Keyword -->
    <div class="my-auto py-4 space-y-1">
      <div class="text-xl sm:text-2xl font-extrabold text-[#e0f0ff] tracking-tight font-['Sora'] leading-tight break-words min-w-0">
        ${escapeHtml(isuUtama)}
      </div>
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
 * Merender 3 kolom sorotan insiden wilayah KPI: Internasional, Nasional, dan Jawa Timur
 * @param {Object} stat Objek data statistik tren
 */
export function renderKasusInsidenWilayah(stat) {
  const cardIntl = document.getElementById('card-kasus-intl');
  const cardNas = document.getElementById('card-kasus-nas');
  const cardJatim = document.getElementById('card-kasus-jatim');

  if (!stat) return;

  const aiData = stat.kasus_wilayah_ai || {};
  const intlItem = aiData.internasional || (stat.kasus_wilayah?.internasional?.[0] ? {
    ada_kejadian: true,
    isu_utama: "Kebocoran Data",
    nama_kejadian: stat.kasus_wilayah.internasional[0].judul,
    kategori: stat.kasus_wilayah.internasional[0].tag,
    lokasi: "Global",
    alasan_urgensi: "Insiden paling ramai dibicarakan media internasional dalam 7 hari terakhir.",
    potensi_ancaman: "Potensi eskalasi serangan siber global dan eksploitasi celah serupa.",
    sumber: stat.kasus_wilayah.internasional[0].sumber,
    link: stat.kasus_wilayah.internasional[0].link,
  } : null);

  const nasItem = aiData.nasional || (stat.kasus_wilayah?.nasional?.[0] ? {
    ada_kejadian: true,
    isu_utama: "Kebocoran Data",
    nama_kejadian: stat.kasus_wilayah.nasional[0].judul,
    kategori: stat.kasus_wilayah.nasional[0].tag,
    lokasi: "Indonesia",
    alasan_urgensi: "Kasus dengan liputan dan keterpaparan tertinggi di ranah siber nasional.",
    potensi_ancaman: "Peningkatan ancaman pencurian kredensial dan serangan terhadap infrastruktur publik.",
    sumber: stat.kasus_wilayah.nasional[0].sumber,
    link: stat.kasus_wilayah.nasional[0].link,
  } : null);

  const jatimItem = aiData.jawa_timur || (stat.kasus_wilayah?.jawa_timur?.[0] ? {
    ada_kejadian: true,
    isu_utama: "Pembajakan Akun",
    nama_kejadian: stat.kasus_wilayah.jawa_timur[0].judul,
    kategori: stat.kasus_wilayah.jawa_timur[0].tag,
    lokasi: "Jawa Timur",
    alasan_urgensi: "Insiden berdampak langsung pada entitas daerah di wilayah Jawa Timur.",
    potensi_ancaman: "Risiko peretasan web, kebocoran basis data, atau penyalahgunaan portal instansi.",
    sumber: stat.kasus_wilayah.jawa_timur[0].sumber,
    link: stat.kasus_wilayah.jawa_timur[0].link,
  } : null);

  currentKasusData.intl = intlItem;
  currentKasusData.nas = nasItem;
  currentKasusData.jatim = jatimItem;

  if (cardIntl) cardIntl.innerHTML = renderSingleIncidentCard(intlItem, 'intl');
  if (cardNas) cardNas.innerHTML = renderSingleIncidentCard(nasItem, 'nas');
  if (cardJatim) cardJatim.innerHTML = renderSingleIncidentCard(jatimItem, 'jatim');
}
