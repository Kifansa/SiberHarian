import { escapeHtml } from './utils.js';
import { dataLengkap } from './modal.js';

/**
 * Pembuat HTML card berita & CVE, dipakai bareng oleh tab Beranda dan
 * Arsip (dua-duanya menampilkan bentuk card yang sama, cuma sumber
 * datanya beda tanggal).
 */
export function buatCardBerita(item) {
  const isInsiden = item.kategori === 'insiden_spesifik';
  const pillClass = isInsiden ? 'bg-violet-50 text-violet-600' : 'bg-sky-50 text-sky-600';
  const pillLabel = isInsiden ? 'Insiden' : 'Analisis';
  const idx = dataLengkap.push({
    judul: item.judul, sumber: item.sumber, link: item.link,
    teksLengkap: item.ringkasan, pillClass, pillLabel
  }) - 1;
  return `
    <article class="bg-surface-container-lowest border border-outline-variant rounded-xl p-gutter custom-shadow flex flex-col transition-all group">
      <div class="flex justify-between items-center gap-2 mb-3">
        <span class="px-2 py-0.5 rounded font-label-sm text-label-sm ${pillClass}">${pillLabel}</span>
        <span class="font-caption text-caption text-on-surface-variant">${escapeHtml(item.sumber)}</span>
      </div>
      <h3 class="font-headline-md text-headline-md text-primary mb-3 line-clamp-2">${escapeHtml(item.judul)}</h3>
      <p class="text-on-surface-variant font-body-md text-body-md mb-4 line-clamp-3">${escapeHtml(item.ringkasan)}</p>
      <button class="text-primary font-bold text-left hover:underline underline-offset-4 mb-4 w-fit" onclick="bukaModal(${idx})">Selengkapnya</button>
      <div class="mt-auto pt-4 border-t border-outline-variant flex justify-between items-center">
        <a class="text-primary font-bold hover:underline underline-offset-4 flex items-center gap-1" href="${escapeHtml(item.link)}" target="_blank" rel="noopener">
          Baca sumber asli <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
        </a>
      </div>
    </article>`;
}

export function buatCardCve(item) {
  const pillClass = 'bg-error-container/20 text-error';
  const teks = item.narasi || 'Tidak ada narasi detail untuk CVE ini.';
  const idx = dataLengkap.push({
    judul: item.cve_id, sumber: item.vendor, link: item.link,
    teksLengkap: teks, pillClass, pillLabel: item.severity
  }) - 1;
  return `
    <article class="bg-surface-container-lowest border border-outline-variant rounded-xl p-gutter custom-shadow flex flex-col transition-all group">
      <div class="flex justify-between items-center gap-2 mb-3">
        <span class="px-2 py-0.5 rounded font-label-sm text-label-sm ${pillClass}">${escapeHtml(item.severity)}</span>
        <span class="font-caption text-caption text-on-surface-variant">${escapeHtml(item.vendor)}</span>
      </div>
      <h3 class="font-headline-md text-headline-md text-primary mb-3 line-clamp-2">${escapeHtml(item.cve_id)}</h3>
      <p class="text-on-surface-variant font-body-md text-body-md mb-4 line-clamp-3">${escapeHtml(teks)}</p>
      <button class="text-primary font-bold text-left hover:underline underline-offset-4 mb-4 w-fit" onclick="bukaModal(${idx})">Selengkapnya</button>
      <div class="mt-auto pt-4 border-t border-outline-variant flex justify-between items-center">
        <a class="text-primary font-bold hover:underline underline-offset-4 flex items-center gap-1" href="${escapeHtml(item.link)}" target="_blank" rel="noopener">
          Detail NVD <span class="material-symbols-outlined text-[18px]">arrow_forward</span>
        </a>
        <span class="font-label-sm text-label-sm text-on-surface-variant">CVSS ${item.skor_cvss ?? '-'}</span>
      </div>
    </article>`;
}

export function buatSection(label, cardsHtml, jumlah) {
  if (jumlah === 0) return '';
  return `
      <div class="mb-xl">
        <div class="flex items-center gap-2 mb-md">
          <h4 class="font-headline-md text-headline-md text-primary">${label}</h4>
          <span class="bg-primary text-on-primary font-label-sm text-label-sm px-2.5 py-0.5 rounded-full">${jumlah}</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">${cardsHtml}</div>
      </div>`;
}