import { escapeHtml } from './tren-utils.js';

/**
 * Merender tabel lonjakan kata kunci (Top 10) dan Radar CVE Watchlist (CSIRT Jatim Cyber-HUD Style)
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
      tbodyKk.innerHTML = '<tr><td colspan="3" class="py-6 text-center text-[#7d8ca6] font-mono text-xs">Tidak ada lonjakan kata kunci saat ini.</td></tr>';
    } else {
      items.forEach((item, index) => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-[#132c4a]/50 transition-colors border-b border-[#1a3a5c] last:border-b-0';
        tr.innerHTML = `
          <td class="py-2.5 px-3.5 font-semibold text-[#e0f0ff] font-['Sora']">
            <span class="inline-flex items-center gap-2 max-w-full">
              <span class="text-[11px] font-mono font-bold text-[#00d4ff] w-4 shrink-0 text-right">${index + 1}.</span>
              <span class="break-words min-w-0">${escapeHtml(item.kata_kunci)}</span>
            </span>
          </td>
          <td class="py-2.5 px-3.5 text-center font-mono whitespace-nowrap">
            <span class="font-bold text-[#00d4ff] text-sm">${item.jumlah_terkini}</span>
            <span class="block text-[10px] font-normal text-[#7d8ca6] font-mono">baseline: ${item.jumlah_baseline}</span>
          </td>
          <td class="py-2.5 px-3.5 text-right font-mono whitespace-nowrap">
            <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#0d2137] text-[#00ff88] border border-[#00ff88]/40 font-mono font-bold text-xs shadow-[0_0_8px_rgba(0,255,136,0.2)]">
              <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">trending_up</span>
              <span>+${item.growth_persen}%</span>
            </span>
          </td>
        `;
        tbodyKk.appendChild(tr);
      });
    }
  }

  // 2. Radar Kerentanan & CVE Watchlist
  renderCveWatchlist(stat.cve_watchlist || []);

  // 3. Perbandingan Week-over-Week (P0 Admin)
  renderPerbandinganWoW(stat.perbandingan_wow);
}

/**
 * Merender tabel Perbandingan Week-over-Week (7H Terkini vs 7H Baseline)
 * @param {Object} wow Objek data perbandingan WoW
 */
export function renderPerbandinganWoW(wow) {
  const tbody = document.getElementById('tabel-wow-body');
  if (!tbody) return;

  if (!wow || Object.keys(wow).length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-[#7d8ca6] font-mono text-xs">Data perbandingan week-over-week belum tersedia.</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  const items = Object.values(wow);

  items.forEach((item) => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-[#132c4a]/50 transition-colors border-b border-[#1a3a5c] last:border-b-0';

    let statusBadge = '';
    if (item.growth !== undefined) {
      const isUp = item.growth >= 0;
      const icon = isUp ? 'trending_up' : 'trending_down';
      const color = isUp ? 'text-[#ff3366] border-[#ff3366]/40 shadow-[0_0_8px_rgba(255,51,102,0.2)]' : 'text-[#00ff88] border-[#00ff88]/40 shadow-[0_0_8px_rgba(0,255,136,0.2)]';
      statusBadge = `
        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#0d2137] ${color} font-mono font-bold text-xs border whitespace-nowrap">
          <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">${icon}</span>
          <span>${item.status}</span>
        </span>
      `;
    } else {
      const isTetap = item.status === 'Tetap';
      const color = isTetap ? 'text-[#8892b0] border-[#1a3a5c]' : 'text-[#00d4ff] border-[#00d4ff]/40 shadow-[0_0_8px_rgba(0,212,255,0.2)]';
      const icon = isTetap ? 'sync_alt' : 'swap_horiz';
      statusBadge = `
        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-[#0d2137] ${color} font-mono font-bold text-xs border whitespace-nowrap">
          <span class="material-symbols-outlined text-[13px] leading-none" aria-hidden="true">${icon}</span>
          <span>${escapeHtml(item.status)}</span>
        </span>
      `;
    }

    tr.innerHTML = `
      <td class="py-3 px-3.5 font-semibold text-[#e0f0ff] font-['Sora'] align-middle">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-[#00d4ff] text-base shrink-0" aria-hidden="true">${escapeHtml(item.icon || 'analytics')}</span>
          <span class="break-words min-w-0">${escapeHtml(item.label)}</span>
        </div>
      </td>
      <td class="py-3 px-3.5 text-center font-mono align-middle whitespace-nowrap">
        <span class="font-bold text-[#00d4ff] text-sm">${escapeHtml(String(item.terkini))}</span>
      </td>
      <td class="py-3 px-3.5 text-center font-mono align-middle whitespace-nowrap">
        <span class="text-[#8892b0] text-sm">${escapeHtml(String(item.baseline))}</span>
      </td>
      <td class="py-3 px-3.5 text-right font-mono align-middle whitespace-nowrap">
        ${statusBadge}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

/**
 * Merender tabel Radar Kerentanan & CVE Watchlist
 * @param {Array} cveList Daftar kerentanan yang dieksploitasi aktif
 */
export function renderCveWatchlist(cveList) {
  const tbody = document.getElementById('tabel-cve-watchlist-body');
  if (!tbody) return;

  if (!cveList || cveList.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" class="py-6 text-center text-[#7d8ca6] font-mono text-xs">Nihil kerentanan CVE kritis atau zero-day baru yang dilaporkan tereksploitasi aktif minggu ini.</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  cveList.forEach((cve) => {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-[#132c4a]/50 transition-colors border-b border-[#1a3a5c] last:border-b-0';
    tr.innerHTML = `
      <td class="py-3 px-3.5 font-bold font-mono text-[#00d4ff] align-top whitespace-nowrap">
        <div class="flex items-center gap-1.5">
          <span class="material-symbols-outlined text-[#ff3366] text-base shrink-0" aria-hidden="true">bug_report</span>
          <span>${escapeHtml(cve.cve_id)}</span>
        </div>
      </td>
      <td class="py-3 px-3.5 font-semibold text-[#e0f0ff] font-['Sora'] align-top break-words max-w-xs">
        ${escapeHtml(cve.aplikasi_terdampak)}
      </td>
      <td class="py-3 px-3.5 text-center align-top whitespace-nowrap">
        <span class="inline-block px-2.5 py-0.5 rounded text-[10px] font-bold border font-mono bg-[#0d2137] text-[#ff3366] border-[#ff3366]/40 shadow-[0_0_8px_rgba(255,51,102,0.25)]">
          [ ${escapeHtml(cve.status_urgensi)} ]
        </span>
      </td>
      <td class="py-3 px-3.5 text-center font-mono font-bold text-[#00ff88] align-top whitespace-nowrap">
        ${cve.jumlah_laporan}
      </td>
      <td class="py-3 px-3.5 text-xs text-[#8892b0] font-mono align-top break-words max-w-xs">
        <span class="font-semibold text-[#e0f0ff] block break-words">${escapeHtml(cve.sumber_terakhir)}</span>
        <span class="text-[11px] text-[#7d8ca6] line-clamp-1 break-words">${escapeHtml(cve.contoh_kasus || '')}</span>
      </td>
    `;
    tbody.appendChild(tr);
  });
}
