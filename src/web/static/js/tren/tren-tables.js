import { escapeHtml } from './tren-utils.js';

/**
 * Merender tabel lonjakan kata kunci dan tabel vendor CVE prioritas
 * @param {Object} stat Objek data statistik tren
 */
export function renderTables(stat) {
  if (!stat) return;

  // 1. Table Kata Kunci
  const tbodyKk = document.getElementById('tabel-kata-kunci-body');
  if (tbodyKk) {
    tbodyKk.innerHTML = '';
    const items = stat.kata_kunci_naik || [];
    if (items.length === 0) {
      tbodyKk.innerHTML = '<tr><td colspan="3" class="py-6 text-center text-[#49769F] text-sm">Tidak ada lonjakan kata kunci saat ini.</td></tr>';
    } else {
      items.forEach(item => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-[#EEF5FA]/60 transition-colors';
        tr.innerHTML = `
          <td class="py-3.5 px-3.5 font-semibold text-[#001D39]">
            ${escapeHtml(item.kata_kunci)}
          </td>
          <td class="py-3.5 px-3.5 text-center font-mono">
            <span class="font-bold text-[#001D39] text-sm">${item.jumlah_terkini}</span>
            <span class="block text-[10px] font-normal text-[#49769F] font-sans">baseline: ${item.jumlah_baseline}</span>
          </td>
          <td class="py-3.5 px-3.5 text-right font-mono">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#15803d] text-white font-mono font-bold text-xs shadow-xs">
              <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">trending_up</span>
              <span>+${item.growth_persen}%</span>
            </span>
          </td>
        `;
        tbodyKk.appendChild(tr);
      });
    }
  }

  // 2. Table Vendor
  const tbodyVendor = document.getElementById('tabel-vendor-body');
  if (tbodyVendor) {
    tbodyVendor.innerHTML = '';
    const vendors = stat.vendor_naik || [];
    if (vendors.length === 0) {
      tbodyVendor.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-[#49769F] text-sm">Tidak ada lonjakan vendor CVE saat ini.</td></tr>';
    } else {
      vendors.forEach(v => {
        const topProdukList = (v.top_produk || []).filter(p => p.produk && p.produk !== '-' && p.produk !== '(lihat deskripsi)' && p.produk !== 'Lainnya / Belum Teridentifikasi');
        const fallbackVendor = v.vendor ? v.vendor.split('/')[0].trim() : 'Lainnya';
        
        const topProdukHtml = topProdukList.length > 0
          ? `<div class="flex flex-wrap items-center gap-1.5 py-0.5">` +
              topProdukList.map(p => `
                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-[#EEF5FA] text-[#0A4174] text-xs font-medium border border-[#BDD8E9]">
                  <span class="font-semibold text-[#001D39]">${escapeHtml(p.produk)}</span>
                  <span class="text-[10px] text-[#49769F] font-mono font-bold">(${p.jumlah}x)</span>
                </span>
              `).join('') + `</div>`
          : `<span class="text-[#49769F] text-xs sm:text-sm">${escapeHtml(fallbackVendor)}</span>`;

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-[#EEF5FA]/60 transition-colors';
        tr.innerHTML = `
          <td class="py-3.5 px-3.5 font-semibold text-[#001D39] align-middle">
            ${escapeHtml(v.vendor)}
          </td>
          <td class="py-3.5 px-3.5 text-center align-middle font-mono">
            <span class="font-bold text-[#001D39] text-sm">${v.jumlah_terkini}</span>
            <span class="block text-[10px] font-normal text-[#49769F] font-sans">baseline: ${v.jumlah_baseline}</span>
          </td>
          <td class="py-3.5 px-3.5 align-middle whitespace-normal break-words leading-relaxed max-w-[320px] sm:max-w-[400px]">
            ${topProdukHtml}
          </td>
          <td class="py-3.5 px-3.5 text-right align-middle font-mono">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#b91c1c] text-white font-mono font-bold text-xs shadow-xs">
              <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">arrow_upward</span>
              <span>+${v.growth_persen}%</span>
            </span>
          </td>
        `;
        tbodyVendor.appendChild(tr);
      });
    }
  }
}
