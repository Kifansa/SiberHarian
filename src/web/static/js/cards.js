import { escapeHtml, sanitizeUrl } from './utils.js';
import { simpanItemModal } from './modal.js';

export function buatCardBerita(item) {
  const safeLink = sanitizeUrl(item.link);
  const idx = simpanItemModal({
    judul: item.judul,
    sumber: item.sumber,
    link: safeLink,
    teksLengkap: item.ringkasan,
    pillClass: 'bg-[#EEF5FA] text-[#0A4174] border border-[#BDD8E9]',
    pillLabel: 'Berita Insiden'
  });
  return `
    <article class="bg-white border border-[#E2EDF8] hover:border-[#7BBDE8]/70 rounded-xl p-6 shadow-card hover:shadow-card-hover card-enterprise flex flex-col justify-between group transition-all duration-200 active:scale-[0.99]" data-search-text="${escapeHtml((item.judul + ' ' + item.sumber + ' ' + (item.ringkasan || '')).toLowerCase())}">
      <div>
        <div class="flex justify-between items-center gap-2 mb-3">
          <span class="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#0A4174] bg-[#EEF5FA] border border-[#BDD8E9]/70 px-2.5 py-0.5 rounded-full shadow-2xs">
            <span class="w-1.5 h-1.5 rounded-full bg-[#4E8EA2]"></span>
            <span>${escapeHtml(item.sumber)}</span>
          </span>
        </div>
        <h3 class="text-base sm:text-lg font-bold text-[#001D39] mb-2.5 line-clamp-2 leading-snug tracking-tight group-hover:text-[#0A4174] transition-colors break-words" style="text-wrap: balance;">${escapeHtml(item.judul)}</h3>
        <p class="text-slate-600 text-xs sm:text-sm mb-4 line-clamp-3 leading-relaxed break-words">${escapeHtml(item.ringkasan)}</p>
      </div>
      <div class="mt-auto pt-3.5 border-t border-[#E2EDF8] flex items-center justify-between gap-2">
        <button type="button" class="px-3 py-1.5 rounded-lg bg-[#EEF5FA] hover:bg-[#E2EDF8] text-[#0A4174] font-bold text-xs transition-all cursor-pointer inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none active:scale-95 border border-[#BDD8E9]/70 shadow-2xs" onclick="window.bukaModal ? window.bukaModal(${idx}) : bukaModal(${idx})" aria-haspopup="dialog" aria-label="Buka ringkasan lengkap: ${escapeHtml(item.judul)}">
          <span>Rangkuman</span>
          <span class="material-symbols-outlined text-sm transition-transform duration-200 group-hover:translate-x-0.5" aria-hidden="true">arrow_forward</span>
        </button>
        <a class="px-2.5 py-1.5 rounded-lg text-[#49769F] hover:text-[#001D39] hover:bg-[#EEF4F8] text-xs font-semibold transition-all inline-flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none active:scale-95" href="${safeLink}" target="_blank" rel="noopener noreferrer">
          <span>Sumber Asli</span>
          <span class="material-symbols-outlined text-sm" aria-hidden="true">open_in_new</span>
        </a>
      </div>
    </article>`;
}

export function buatCardCve(item) {
  const teks = item.narasi || 'Tidak ada narasi detail untuk CVE ini.';
  const safeLink = sanitizeUrl(item.link);
  const cvssBadgeClass = 'bg-[#EEF5FA] text-[#0A4174] border-[#BDD8E9]';
  const cvssLabel = 'CVSS ' + (item.skor_cvss ?? '-');

  const idx = simpanItemModal({
    judul: item.cve_id,
    sumber: item.vendor,
    link: safeLink,
    teksLengkap: teks,
    pillClass: cvssBadgeClass,
    pillLabel: cvssLabel
  });

  return `
    <article class="bg-white border border-[#E2EDF8] hover:border-[#7BBDE8]/70 rounded-xl p-6 shadow-card hover:shadow-card-hover card-enterprise flex flex-col justify-between group transition-all duration-200 active:scale-[0.99]" data-search-text="${escapeHtml((item.cve_id + ' ' + item.vendor + ' ' + (item.ringkasan_atau_narasi || teks)).toLowerCase())}">
      <div>
        <div class="flex justify-between items-center gap-2 mb-3">
          <span class="inline-flex items-center gap-1 text-[11px] font-bold text-[#49769F] bg-[#EEF5FA] border border-[#BDD8E9]/70 px-2.5 py-0.5 rounded-full shadow-2xs">
            <span class="material-symbols-outlined text-xs text-[#0A4174]" aria-hidden="true">apps</span>
            <span>${escapeHtml(item.vendor)}</span>
          </span>
          <span class="px-2.5 py-0.5 rounded-md border font-mono text-[11px] shadow-2xs tabular-nums ${cvssBadgeClass}">${cvssLabel}</span>
        </div>
        <h3 class="text-base sm:text-lg font-bold text-[#001D39] mb-2.5 line-clamp-2 leading-snug font-mono tracking-tight group-hover:text-[#0A4174] transition-colors break-words tabular-nums" style="text-wrap: balance;">${escapeHtml(item.cve_id)}</h3>
        <p class="text-slate-600 text-xs sm:text-sm mb-4 line-clamp-3 leading-relaxed break-words">${escapeHtml(item.ringkasan_atau_narasi || teks)}</p>
      </div>
      <div class="mt-auto pt-3.5 border-t border-[#E2EDF8] flex items-center justify-between gap-2">
        <button type="button" class="px-3 py-1.5 rounded-lg bg-[#EEF5FA] hover:bg-[#E2EDF8] text-[#0A4174] font-bold text-xs transition-all cursor-pointer inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none active:scale-95 border border-[#BDD8E9]/70 shadow-2xs" onclick="window.bukaModal ? window.bukaModal(${idx}) : bukaModal(${idx})" aria-haspopup="dialog" aria-label="Buka narasi CVE: ${escapeHtml(item.cve_id)}">
          <span>Analisis CVE</span>
          <span class="material-symbols-outlined text-sm transition-transform duration-200 group-hover:translate-x-0.5" aria-hidden="true">arrow_forward</span>
        </button>
        <a class="px-2.5 py-1.5 rounded-lg text-[#49769F] hover:text-[#001D39] hover:bg-[#EEF4F8] text-xs font-semibold transition-all inline-flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none active:scale-95" href="${safeLink}" target="_blank" rel="noopener noreferrer">
          <span>Detail NVD</span>
          <span class="material-symbols-outlined text-sm" aria-hidden="true">open_in_new</span>
        </a>
      </div>
    </article>`;
}

export function buatSection(label, cardsHtml, jumlah, { ikon = '', kelas = '', kategori = '' } = {}) {
  if (jumlah === 0) return '';
  const ikonHtml = ikon
    ? `<span class="w-8 h-8 rounded-lg ${kelas} flex items-center justify-center shrink-0 shadow-2xs"><span class="material-symbols-outlined text-lg" aria-hidden="true">${ikon}</span></span>`
    : '';
  return `
      <div class="mb-10 section-wrapper" data-kategori="${kategori}">
        <div class="flex items-center gap-3 mb-5 border-b border-[#BDD8E9]/70 pb-3.5">
          ${ikonHtml}
          <h3 class="text-lg font-extrabold text-[#001D39] tracking-tight">${label}</h3>
          <span class="bg-[#EEF5FA] text-[#0A4174] border border-[#BDD8E9] text-xs font-bold px-2.5 py-0.5 rounded-full count-badge shadow-2xs">${jumlah}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 cards-grid">${cardsHtml}</div>
      </div>`;
}
