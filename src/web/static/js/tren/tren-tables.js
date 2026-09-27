import { escapeHtml } from './tren-utils.js';

/**
 * Merender tabel lonjakan kata kunci dan tabel vendor CVE prioritas (Top 10)
 * @param {Object} stat Objek data statistik tren
 */
export function renderTables(stat) {
  if (!stat) return;

  // 1. Table Kata Kunci (Top 10)
  const tbodyKk = document.getElementById('tabel-kata-kunci-body');
  if (tbodyKk) {
    tbodyKk.innerHTML = '';
    const items = (stat.kata_kunci_naik || []).slice(0, 10);
    if (items.length === 0) {
      tbodyKk.innerHTML = '<tr><td colspan="3" class="py-6 text-center text-[#49769F] text-sm">Tidak ada lonjakan kata kunci saat ini.</td></tr>';
    } else {
      items.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-[#EEF5FA]/60 transition-colors border-b border-[#E2EDF8] last:border-b-0';
        tr.innerHTML = `
          <td class="py-2.5 px-3.5 font-semibold text-[#001D39]">
            <span class="inline-flex items-center gap-2">
              <span class="text-[11px] font-mono font-bold text-[#49769F] w-4 shrink-0 text-right">${index + 1}.</span>
              <span>${escapeHtml(item.kata_kunci)}</span>
            </span>
          </td>
          <td class="py-2.5 px-3.5 text-center font-mono">
            <span class="font-bold text-[#001D39] text-sm">${item.jumlah_terkini}</span>
            <span class="block text-[10px] font-normal text-[#49769F] font-sans">baseline: ${item.jumlah_baseline}</span>
          </td>
          <td class="py-2.5 px-3.5 text-right font-mono">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#15803d] text-white font-mono font-bold text-xs shadow-xs">
              <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">trending_up</span>
              <span>+${item.growth_persen}%</span>
            </span>
          </td>
        `;
        tbodyKk.appendChild(tr);
      });
    }
  }

  // 2. Table Vendor (Top 10)
  const tbodyVendor = document.getElementById('tabel-vendor-body');
  if (tbodyVendor) {
    tbodyVendor.innerHTML = '';
    const vendors = (stat.vendor_naik || []).slice(0, 10);
    if (vendors.length === 0) {
      tbodyVendor.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-[#49769F] text-sm">Tidak ada lonjakan vendor CVE saat ini.</td></tr>';
    } else {
      vendors.forEach((v, index) => {
        const topProdukList = (v.top_produk || []).filter(p => p.produk && p.produk !== '-' && p.produk !== '(lihat deskripsi)' && p.produk !== 'Lainnya / Belum Teridentifikasi');
        const fallbackVendor = v.vendor ? v.vendor.split('/')[0].trim() : 'Lainnya';
        
        const topProdukHtml = topProdukList.length > 0
          ? `<div class="flex flex-wrap items-center gap-1.5 py-0.5">` +
              topProdukList.map(p => `
                <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#EEF5FA] text-[#0A4174] text-xs font-medium border border-[#BDD8E9]">
                  <span class="font-semibold text-[#001D39]">${escapeHtml(p.produk)}</span>
                  <span class="text-[10px] text-[#49769F] font-mono font-bold">(${p.jumlah}x)</span>
                </span>
              `).join('') + `</div>`
          : `<span class="text-[#49769F] text-xs sm:text-sm">${escapeHtml(fallbackVendor)}</span>`;

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-[#EEF5FA]/60 transition-colors border-b border-[#E2EDF8] last:border-b-0';
        tr.innerHTML = `
          <td class="py-2.5 px-3.5 font-semibold text-[#001D39] align-middle">
            <span class="inline-flex items-center gap-2">
              <span class="text-[11px] font-mono font-bold text-[#49769F] w-4 shrink-0 text-right">${index + 1}.</span>
              <span>${escapeHtml(v.vendor)}</span>
            </span>
          </td>
          <td class="py-2.5 px-3.5 text-center align-middle font-mono">
            <span class="font-bold text-[#001D39] text-sm">${v.jumlah_terkini}</span>
            <span class="block text-[10px] font-normal text-[#49769F] font-sans">baseline: ${v.jumlah_baseline}</span>
          </td>
          <td class="py-2.5 px-3.5 align-middle whitespace-normal break-words leading-relaxed max-w-[300px] sm:max-w-[380px]">
            ${topProdukHtml}
          </td>
          <td class="py-2.5 px-3.5 text-right align-middle font-mono">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#b91c1c] text-white font-mono font-bold text-xs shadow-xs">
              <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">arrow_upward</span>
              <span>+${v.growth_persen}%</span>
            </span>
          </td>
        `;
        tbodyVendor.appendChild(tr);
      });
    }
  }

  // 3. Matriks Tindakan Ancaman Aktif
  renderMatriksTindakan(stat.matriks_tindakan || []);
}

/**
 * Merender tabel matriks tindakan taktis CTI (Remediation Checklist)
 * @param {Array} matriksList Daftar data matriks tindakan
 */
export function renderMatriksTindakan(matriksList) {
  const tbody = document.getElementById('tabel-matriks-tindakan-body');
  if (!tbody) return;

  if (!matriksList || matriksList.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="py-6 text-center text-[#49769F]">Nihil anomali ancaman khusus yang memerlukan tindakan darurat minggu ini.</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  matriksList.forEach((m) => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-[#EEF5FA]/60 transition-colors border-b border-[#E2EDF8] last:border-b-0';

    const urgensi = m.level_urgensi || 'SEDANG';
    let badgeClass = 'bg-blue-50 text-blue-700 border-blue-200';
    if (urgensi === 'KRITIS') {
      badgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
    } else if (urgensi === 'TINGGI') {
      badgeClass = 'bg-amber-50 text-amber-800 border-amber-200';
    } else if (urgensi === 'MONITOR' || urgensi === 'RENDAH') {
      badgeClass = 'bg-slate-50 text-slate-700 border-slate-200';
    }

    const growth = m.growth_persen ?? 0;
    const isUp = growth > 0;

    tr.innerHTML = `
      <td class="py-3 px-4 font-semibold text-[#001D39] whitespace-nowrap align-top">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-base text-[#0A4174]">${m.ikon || 'security'}</span>
          <span>${escapeHtml(m.kategori)}</span>
        </div>
      </td>
      <td class="py-3 px-4 text-center font-mono align-top whitespace-nowrap">
        <span class="font-bold text-[#001D39]">${m.jumlah_terkini}</span>
        <span class="text-[11px] font-semibold text-[#49769F] block">${isUp ? '+' : ''}${growth}%</span>
      </td>
      <td class="py-3 px-4 text-center align-top whitespace-nowrap">
        <span class="inline-block px-2.5 py-0.5 rounded text-[11px] font-bold border font-mono ${badgeClass}">
          ${urgensi}
        </span>
      </td>
      <td class="py-3 px-4 text-xs text-[#001D39] leading-relaxed max-w-[280px] align-top">
        ${escapeHtml(m.fokus_website || '-')}
      </td>
      <td class="py-3 px-4 text-xs text-slate-700 font-medium leading-relaxed max-w-[340px] align-top">
        ${escapeHtml(m.tindakan_taktis || '-')}
      </td>
    `;
    tbody.appendChild(tr);
  });
}
