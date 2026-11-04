import { escapeHtml, sanitizeUrl } from './utils.js';
import { simpanItemModal } from './modal.js';

export function buatCardBerita(item) {
  const safeLink = sanitizeUrl(item.link);
  const idx = simpanItemModal({
    judul: item.judul,
    sumber: item.sumber,
    link: safeLink,
    teksLengkap: item.ringkasan,
    pillClass: 'bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40 font-mono',
    pillLabel: '[ Berita Insiden ]'
  });
  return `
    <article class="card-cyber p-6 flex flex-col justify-between group transition-all duration-200 active:scale-[0.99]" data-search-text="${escapeHtml(((item.judul || '') + ' ' + (item.sumber || '') + ' ' + (item.ringkasan || '') + ' ' + (item.kata_kunci || '') + ' ' + (item.tanggal || '')).toLowerCase())}">
      <div>
        <div class="flex justify-between items-center gap-2 mb-3">
          <span class="inline-flex items-center text-[11px] font-mono font-bold text-[#00d4ff] bg-[#0d2137] border border-[#00d4ff]/30 px-2.5 py-0.5 rounded shadow-[0_0_8px_rgba(0,212,255,0.15)]">
            <span>[ ${escapeHtml(item.sumber || 'Media Siber')} ]</span>
          </span>
          ${item.tanggal ? `<span class="text-[10px] font-mono text-[#7d8ca6] tracking-wider">${escapeHtml(item.tanggal)}</span>` : ''}
        </div>
        <h3 class="text-base sm:text-lg font-bold text-[#e0f0ff] font-['Sora'] mb-2.5 line-clamp-2 leading-snug tracking-tight group-hover:text-[#00d4ff] transition-colors break-words" style="text-wrap: balance;">${escapeHtml(item.judul || '')}</h3>
        <p class="text-[#7d8ca6] text-xs sm:text-sm mb-4 line-clamp-3 leading-relaxed break-words font-['Sora']">${escapeHtml(item.ringkasan || '')}</p>
      </div>
      <div class="mt-auto pt-3.5 border-t border-[#1a3a5c] flex items-center justify-between gap-2 flex-wrap">
        <button type="button" class="btn-chamfer text-xs whitespace-nowrap shrink-0" style="height:36px;padding:0 14px;" onclick="window.bukaModal ? window.bukaModal(${idx}) : bukaModal(${idx})" aria-haspopup="dialog" aria-label="Buka ringkasan lengkap: ${escapeHtml(item.judul || '')}">
          <span>[ RANGKUMAN → ]</span>
        </button>
        <a class="px-2.5 py-1.5 rounded text-[#8892b0] hover:text-[#00d4ff] hover:bg-[#0d2137] text-xs font-mono font-medium transition-all inline-flex items-center gap-1 focus-visible:ring-1 focus-visible:ring-[#00d4ff] outline-none whitespace-nowrap shrink-0" href="${safeLink}" target="_blank" rel="noopener noreferrer">
          <span>Sumber Asli</span>
          <span class="material-symbols-outlined text-sm" aria-hidden="true">open_in_new</span>
        </a>
      </div>
    </article>`;
}

export function buatSection(label, cardsHtml, jumlah, { ikon = '', kelas = '', kategori = '' } = {}) {
  if (jumlah === 0) return '';
  const ikonHtml = ikon
    ? `<span class="w-8 h-8 rounded-lg bg-[#0d2137] border border-[#1a3a5c] text-[#00d4ff] flex items-center justify-center shrink-0 shadow-[0_0_10px_rgba(0,212,255,0.2)]"><span class="material-symbols-outlined text-lg" aria-hidden="true">${ikon}</span></span>`
    : '';
  return `
      <div class="mb-10 section-wrapper" data-kategori="${kategori}">
        <div class="flex items-center gap-3 mb-5 border-b border-[#1a3a5c] pb-3.5">
          ${ikonHtml}
          <h3 class="text-lg font-extrabold text-[#e0f0ff] font-['Sora'] tracking-tight">[ ${label.toUpperCase()} ]</h3>
          <span class="bg-[#0d2137] text-[#00ff9d] border border-[#00ff9d]/30 font-mono text-xs font-bold px-2.5 py-0.5 rounded shadow-[0_0_8px_rgba(0,255,157,0.2)] count-badge">${jumlah}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 cards-grid">${cardsHtml}</div>
      </div>`;
}
