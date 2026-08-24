import { escapeHtml } from './utils.js';
import { dataLengkap } from './modal.js';

/**
 * Pembuat HTML card berita & CVE, dipakai bareng oleh tab Beranda dan
 * Arsip (dua-duanya menampilkan bentuk card yang sama, cuma sumber
 * datanya beda tanggal).
 */
export function buatCardBerita(item) {
  const isInsiden = item.kategori === 'insiden_spesifik';
  const pillClass = isInsiden ? 'bg-red-50 text-google-red border border-red-200' : 'bg-blue-50 text-primary border border-blue-200';
  const pillLabel = isInsiden ? 'Insiden' : 'Edukasi / Evergreen';
  const idx = dataLengkap.push({
    judul: item.judul, sumber: item.sumber, link: item.link,
    teksLengkap: item.ringkasan, pillClass, pillLabel
  }) - 1;
  return `
    <article class="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col justify-between transition-all hover:border-slate-300 hover:shadow-sm">
      <div>
        <div class="flex justify-between items-center gap-2 mb-3.5">
          <span class="px-2.5 py-0.5 rounded-md font-mono text-xs font-bold ${pillClass}">${pillLabel}</span>
          <span class="text-xs text-slate-500 font-medium">${escapeHtml(item.sumber)}</span>
        </div>
        <h3 class="text-lg font-bold text-slate-900 mb-2.5 line-clamp-2 leading-snug">${escapeHtml(item.judul)}</h3>
        <p class="text-slate-600 text-sm mb-4 line-clamp-3 leading-relaxed">${escapeHtml(item.ringkasan)}</p>
      </div>
      <div>
        <button class="text-slate-900 font-bold text-sm text-left hover:text-primary transition-colors hover:underline mb-4 w-fit cursor-pointer underline-offset-4" onclick="bukaModal(${idx})">Selengkapnya</button>
        <div class="pt-3.5 border-t border-slate-100 flex justify-between items-center">
          <a class="text-slate-900 font-bold text-sm hover:text-primary transition-colors hover:underline flex items-center gap-1 underline-offset-4" href="${escapeHtml(item.link)}" target="_blank" rel="noopener">
            Baca sumber asli <span class="material-symbols-outlined text-[16px]">open_in_new</span>
          </a>
        </div>
      </div>
    </article>`;
}

export function buatCardCve(item) {
  const pillClass = 'bg-red-50 text-google-red border border-red-200';
  const teks = item.narasi || 'Tidak ada narasi detail untuk CVE ini.';
  const idx = dataLengkap.push({
    judul: item.cve_id, sumber: item.vendor, link: item.link,
    teksLengkap: teks, pillClass, pillLabel: item.severity
  }) - 1;
  return `
    <article class="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col justify-between transition-all hover:border-slate-300 hover:shadow-sm">
      <div>
        <div class="flex justify-between items-center gap-2 mb-3.5">
          <span class="px-2.5 py-0.5 rounded-md font-mono text-xs font-bold ${pillClass}">${escapeHtml(item.severity)}</span>
          <span class="text-xs text-slate-500 font-medium">${escapeHtml(item.vendor)}</span>
        </div>
        <h3 class="text-lg font-bold text-slate-900 mb-2.5 line-clamp-2 leading-snug">${escapeHtml(item.cve_id)}</h3>
        <p class="text-slate-600 text-sm mb-4 line-clamp-3 leading-relaxed">${escapeHtml(item.ringkasan_atau_narasi || teks)}</p>
      </div>
      <div>
        <button class="text-slate-900 font-bold text-sm text-left hover:text-primary transition-colors hover:underline mb-4 w-fit cursor-pointer underline-offset-4" onclick="bukaModal(${idx})">Selengkapnya</button>
        <div class="pt-3.5 border-t border-slate-100 flex justify-between items-center">
          <a class="text-slate-900 font-bold text-sm hover:text-primary transition-colors hover:underline flex items-center gap-1 underline-offset-4" href="${escapeHtml(item.link)}" target="_blank" rel="noopener">
            Detail NVD <span class="material-symbols-outlined text-[16px]">open_in_new</span>
          </a>
          <span class="px-2.5 py-1 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-mono text-xs font-bold">CVSS ${item.skor_cvss ?? '-'}</span>
        </div>
      </div>
    </article>`;
}

export function buatSection(label, cardsHtml, jumlah) {
  if (jumlah === 0) return '';
  return `
      <div class="mb-10">
        <div class="flex items-center gap-3 mb-5 border-b border-slate-100 pb-3">
          <h4 class="text-xl font-bold text-slate-900">${label}</h4>
          <span class="bg-blue-50 text-primary border border-blue-200 font-mono text-xs font-bold px-2.5 py-0.5 rounded-full">${jumlah}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">${cardsHtml}</div>
      </div>`;
}