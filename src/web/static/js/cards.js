import { escapeHtml, sanitizeUrl } from './utils.js';
import { dataLengkap } from './modal.js';

export function buatCardBerita(item) {
  const safeLink = sanitizeUrl(item.link);
  const idx = dataLengkap.push({
    judul: item.judul, sumber: item.sumber, link: safeLink,
    teksLengkap: item.ringkasan, pillClass: '', pillLabel: ''
  }) - 1;
  return `
    <article class="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-6 shadow-xs card-enterprise flex flex-col justify-between" data-search-text="${escapeHtml((item.judul + ' ' + item.sumber + ' ' + (item.ringkasan || '')).toLowerCase())}">
      <div>
        <div class="flex justify-between items-center gap-2 mb-3.5">
          <span class="text-xs text-slate-500 font-medium">${escapeHtml(item.sumber)}</span>
        </div>
        <h3 class="text-lg font-bold text-slate-900 mb-2.5 line-clamp-2 leading-snug break-words">${escapeHtml(item.judul)}</h3>
        <p class="text-slate-600 text-sm mb-4 line-clamp-3 leading-relaxed break-words">${escapeHtml(item.ringkasan)}</p>
      </div>
      <div>
        <button class="text-blue-600 hover:text-blue-700 font-semibold text-xs text-left transition-colors mb-4 w-fit cursor-pointer underline-offset-4 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none rounded" onclick="bukaModal(${idx})" aria-label="Buka ringkasan lengkap: ${escapeHtml(item.judul)}">Selengkapnya →</button>
        <div class="pt-3.5 border-t border-slate-100 flex justify-between items-center">
          <a class="text-slate-500 text-xs hover:text-slate-800 transition-colors flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none rounded" href="${safeLink}" target="_blank" rel="noopener noreferrer">
            Baca sumber asli <span class="material-symbols-outlined text-sm" aria-hidden="true">open_in_new</span>
          </a>
        </div>
      </div>
    </article>`;
}

export function buatCardCve(item) {
  const teks = item.narasi || 'Tidak ada narasi detail untuk CVE ini.';
  const safeLink = sanitizeUrl(item.link);
  const idx = dataLengkap.push({
    judul: item.cve_id, sumber: item.vendor, link: safeLink,
    teksLengkap: teks, pillClass: '', pillLabel: ''
  }) - 1;
  return `
    <article class="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-6 shadow-xs card-enterprise flex flex-col justify-between" data-search-text="${escapeHtml((item.cve_id + ' ' + item.vendor + ' ' + (item.ringkasan_atau_narasi || teks)).toLowerCase())}">
      <div>
        <div class="flex justify-between items-center gap-2 mb-3.5">
          <span class="text-xs text-slate-500 font-medium">${escapeHtml(item.vendor)}</span>
        </div>
        <h3 class="text-lg font-bold text-slate-900 mb-2.5 line-clamp-2 leading-snug font-mono break-words">${escapeHtml(item.cve_id)}</h3>
        <p class="text-slate-600 text-sm mb-4 line-clamp-3 leading-relaxed break-words">${escapeHtml(item.ringkasan_atau_narasi || teks)}</p>
      </div>
      <div>
        <button class="text-blue-600 hover:text-blue-700 font-semibold text-xs text-left transition-colors mb-4 w-fit cursor-pointer underline-offset-4 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none rounded" onclick="bukaModal(${idx})" aria-label="Buka narasi CVE: ${escapeHtml(item.cve_id)}">Selengkapnya →</button>
        <div class="pt-3.5 border-t border-slate-100 flex justify-between items-center">
          <a class="text-slate-500 text-xs hover:text-slate-800 transition-colors flex items-center gap-1 focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:outline-none rounded" href="${safeLink}" target="_blank" rel="noopener noreferrer">
            Detail NVD <span class="material-symbols-outlined text-sm" aria-hidden="true">open_in_new</span>
          </a>
          <span class="px-2.5 py-1 rounded-lg bg-amber-500 text-white font-mono text-xs font-bold shadow-xs">CVSS ${item.skor_cvss ?? '-'}</span>
        </div>
      </div>
    </article>`;
}

export function buatSection(label, cardsHtml, jumlah, { ikon = '', kelas = '' } = {}) {
  if (jumlah === 0) return '';
  const ikonHtml = ikon
    ? `<span class="w-9 h-9 rounded-xl ${kelas} flex items-center justify-center shrink-0 shadow-sm"><span class="material-symbols-outlined text-lg" aria-hidden="true">${ikon}</span></span>`
    : '';
  return `
      <div class="mb-10 section-wrapper">
        <div class="flex items-center gap-3 mb-5 border-b border-slate-200 pb-3">
          ${ikonHtml}
          <h4 class="text-lg font-bold text-slate-900">${label}</h4>
          <span class="bg-slate-100 text-slate-700 border border-slate-200 text-xs font-semibold px-2.5 py-0.5 rounded-full count-badge">${jumlah}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 cards-grid">${cardsHtml}</div>
      </div>`;
}
