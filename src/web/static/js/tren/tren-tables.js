import { escapeHtml } from './tren-utils.js';

/**
 * Merender tabel lonjakan kata kunci dan tabel sektor vital IIV terpapar (Top 10)
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

  // 2. Table Sektor Sasaran Terpapar (IIV)
  const tbodySektor = document.getElementById('tabel-sektor-body') || document.getElementById('tabel-vendor-body');
  if (tbodySektor) {
    tbodySektor.innerHTML = '';
    const sektorList = stat.top_sektor || stat.sektor_target || [];
    const items = sektorList.slice(0, 10);
    if (items.length === 0) {
      tbodySektor.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-[#49769F] text-sm">Tidak ada data sektor terpapar saat ini.</td></tr>';
    } else {
      const totalSemua = items.reduce((acc, curr) => acc + (curr.jumlah || 0), 0) || 1;
      items.forEach((s, index) => {
        const proporsi = Math.round(((s.jumlah || 0) / totalSemua) * 100);
        let badgeClass = 'bg-blue-50 text-blue-700 border-blue-200';
        let urgensi = 'SEDANG';
        if (proporsi >= 30) {
          badgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
          urgensi = 'KRITIS';
        } else if (proporsi >= 15) {
          badgeClass = 'bg-amber-50 text-amber-800 border-amber-200';
          urgensi = 'TINGGI';
        }

        let subKlasterBadge = '';
        const sektorLower = (s.sektor || '').toLowerCase();
        if (sektorLower.includes('pemerintah')) {
          subKlasterBadge = '<span class="text-[10px] text-[#0A4174] bg-[#EEF5FA] border border-[#BDD8E9] px-1.5 py-0.5 rounded font-sans block mt-1 w-fit">Portal OPD &amp; Pemda</span>';
        } else if (sektorLower.includes('kesehatan')) {
          subKlasterBadge = '<span class="text-[10px] text-teal-700 bg-teal-50 border border-teal-200 px-1.5 py-0.5 rounded font-sans block mt-1 w-fit">RSUD &amp; Faskes Daerah</span>';
        } else if (sektorLower.includes('pendidikan')) {
          subKlasterBadge = '<span class="text-[10px] text-indigo-700 bg-indigo-50 border border-indigo-200 px-1.5 py-0.5 rounded font-sans block mt-1 w-fit">SIAKAD &amp; Kampus</span>';
        } else if (sektorLower.includes('keuangan')) {
          subKlasterBadge = '<span class="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 py-0.5 rounded font-sans block mt-1 w-fit">BPR &amp; Keuangan Daerah</span>';
        }

        const tr = document.createElement('tr');
        tr.className = 'hover:bg-[#EEF5FA]/60 transition-colors border-b border-[#E2EDF8] last:border-b-0';
        tr.innerHTML = `
          <td class="py-2.5 px-3.5 font-semibold text-[#001D39] align-middle">
            <span class="inline-flex items-center gap-2">
              <span class="text-[11px] font-mono font-bold text-[#49769F] w-4 shrink-0 text-right">${index + 1}.</span>
              <span>${escapeHtml(s.sektor)}</span>
            </span>
            ${subKlasterBadge}
          </td>
          <td class="py-2.5 px-3.5 text-center align-middle font-mono">
            <span class="font-bold text-[#001D39] text-sm">${s.jumlah || 0}</span>
            <span class="block text-[10px] font-normal text-[#49769F] font-sans">insiden</span>
          </td>
          <td class="py-2.5 px-3.5 align-middle whitespace-normal break-words leading-relaxed max-w-[300px]">
            <div class="flex items-center gap-2">
              <div class="w-24 bg-[#EEF4F8] rounded h-1.5 overflow-hidden border border-[#E2EDF8]">
                <div class="h-full rounded bg-[#0A4174]" style="width: ${proporsi}%"></div>
              </div>
              <span class="text-xs font-mono font-bold text-[#0A4174]">${proporsi}%</span>
            </div>
          </td>
          <td class="py-2.5 px-3.5 text-right align-middle font-mono">
            <span class="inline-block px-2.5 py-0.5 rounded text-[11px] font-bold border font-mono ${badgeClass}">
              ${urgensi}
            </span>
          </td>
        `;
        tbodySektor.appendChild(tr);
      });
    }
  }

  // 3. Radar Kerentanan & CVE Watchlist
  renderCveWatchlist(stat.cve_watchlist || []);
}

/**
 * Merender tabel Radar Kerentanan & CVE Watchlist
 * @param {Array} cveList Daftar kerentanan yang dieksploitasi aktif
 */
export function renderCveWatchlist(cveList) {
  const tbody = document.getElementById('tabel-cve-watchlist-body');
  if (!tbody) return;

  if (!cveList || cveList.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="py-6 text-center text-[#49769F] text-xs">Nihil kerentanan CVE kritis atau zero-day baru yang dilaporkan tereksploitasi aktif minggu ini.</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  cveList.forEach((cve) => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-[#EEF5FA]/60 transition-colors border-b border-[#E2EDF8] last:border-b-0';
    tr.innerHTML = `
      <td class="py-3 px-3.5 font-bold font-mono text-[#001D39] align-top whitespace-nowrap">
        <div class="flex items-center gap-1.5">
          <span class="material-symbols-outlined text-rose-600 text-base" aria-hidden="true">bug_report</span>
          <span>${escapeHtml(cve.cve_id)}</span>
        </div>
      </td>
      <td class="py-3 px-3.5 font-semibold text-[#0A4174] align-top">
        ${escapeHtml(cve.aplikasi_terdampak)}
      </td>
      <td class="py-3 px-3.5 text-center align-top whitespace-nowrap">
        <span class="inline-block px-2.5 py-0.5 rounded text-[10px] font-bold border font-mono bg-rose-50 text-rose-700 border-rose-200">
          ${escapeHtml(cve.status_urgensi)}
        </span>
      </td>
      <td class="py-3 px-3.5 text-center font-mono font-bold text-[#001D39] align-top">
        ${cve.jumlah_laporan}
      </td>
      <td class="py-3 px-3.5 text-xs text-[#49769F] align-top">
        <span class="font-semibold text-slate-700 block">${escapeHtml(cve.sumber_terakhir)}</span>
        <span class="text-[11px] text-[#49769F] line-clamp-1">${escapeHtml(cve.contoh_kasus || '')}</span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}
