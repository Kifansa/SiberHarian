import { escapeHtml } from './tren-utils.js?v=9.5';

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

  window._cveWatchlistData = Array.isArray(cveList) ? cveList : [];

  if (!cveList || cveList.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3" class="py-6 text-center text-[#7d8ca6] font-mono text-xs">Nihil kerentanan CVE kritis atau zero-day baru yang dilaporkan tereksploitasi aktif minggu ini.</td></tr>';
    return;
  }

  tbody.innerHTML = '';
  cveList.forEach((cve, idx) => {
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
      <td class="py-2.5 px-3.5 text-xs text-[#8892b0] font-mono align-top max-w-md">
        <div class="p-2.5 rounded-lg border border-[#1a3a5c] bg-[#0a1628]/90 hover:bg-[#0d2137] hover:border-[#00d4ff]/50 transition-all shadow-sm">
          <div class="flex items-center justify-between gap-2 mb-1.5 flex-wrap">
            <button type="button" onclick="window.sorotAtauBukaBeritaCve(${idx}, false)"
              class="inline-flex items-center gap-1.5 text-left text-xs font-bold text-[#00d4ff] hover:text-[#00ff9d] transition-colors cursor-pointer focus-visible:outline-none"
              title="Klik untuk menavigasi & menyorot berita di arsip">
              <span class="material-symbols-outlined text-sm text-[#00d4ff]" aria-hidden="true">travel_explore</span>
              <span>[ ${escapeHtml(cve.sumber_terakhir)} ]</span>
            </button>
            <div class="flex items-center gap-1.5">
              <button type="button" onclick="window.sorotAtauBukaBeritaCve(${idx}, true)"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-[#0d2137] hover:bg-[#132c4a] text-[10px] font-mono text-[#00d4ff] hover:text-[#00ff9d] border border-[#00d4ff]/30 hover:border-[#00d4ff] transition-all cursor-pointer focus-visible:outline-none"
                title="Buka ringkasan intelijen">
                <span class="material-symbols-outlined text-xs" aria-hidden="true">description</span>
                <span>Rangkuman</span>
              </button>
              ${cve.link && cve.link !== '#' ? `
                <a href="${escapeHtml(cve.link)}" target="_blank" rel="noopener noreferrer"
                  class="text-[#7d8ca6] hover:text-[#00d4ff] p-1 rounded hover:bg-[#0d2137] transition-colors flex items-center"
                  title="Buka link asli media sumber">
                  <span class="material-symbols-outlined text-xs" aria-hidden="true">open_in_new</span>
                </a>
              ` : ''}
            </div>
          </div>
          <div onclick="window.sorotAtauBukaBeritaCve(${idx}, false)"
            class="text-[11px] text-[#e0f0ff] font-['Sora'] line-clamp-2 hover:line-clamp-none cursor-pointer hover:text-[#00d4ff] transition-colors leading-relaxed"
            title="Klik untuk menavigasi & menyorot berita ini">
            ${escapeHtml(cve.contoh_kasus || cve.judul_lengkap || '')}
          </div>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

/**
 * Menavigasi ke kartu berita di Arsip, melakukan smooth scroll dengan animasi,
 * lalu memberikan efek highlight pendaran neon (glow) agar kartu terlihat menyala.
 * Jika kartu tidak berada pada tampilan aktif, langsung membuka rangkuman modal berita.
 * @param {number} idx Indeks CVE pada daftar data watchlist
 * @param {boolean} bukaModalLangsung Paksa membuka modal tanpa berpindah tab
 */
export async function sorotAtauBukaBeritaCve(idx, bukaModalLangsung = false) {
  const cve = (window._cveWatchlistData && window._cveWatchlistData[idx]) ? window._cveWatchlistData[idx] : null;
  if (!cve) return;

  const targetJudul = (cve.judul_lengkap || cve.contoh_kasus || '').trim();
  const cveId = (cve.cve_id || '').trim();
  const sumber = (cve.sumber_terakhir || '').trim();
  const ringkasan = (cve.ringkasan || cve.contoh_kasus || '').trim();
  const link = (cve.link && cve.link !== '#') ? cve.link : '';

  // Jika tombol Rangkuman diklik langsung, buka modal popup
  if (bukaModalLangsung && window.bukaModal) {
    window.bukaModal({
      judul: targetJudul || `Laporan Intelijen ${cveId}`,
      teksLengkap: ringkasan || `Kerentanan ${cveId} (${cve.aplikasi_terdampak || 'Sistem'}) dilaporkan oleh ${sumber}.`,
      sumber: sumber,
      link: link,
      pillLabel: `[ ${cveId} ]`,
      pillClass: 'bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40 font-mono'
    });
    return;
  }

  // 1. Pindah ke tab 'arsip' tempat kartu-kartu berita insiden berada
  const alpineRoot = document.querySelector('[x-data]');
  if (alpineRoot && window.Alpine) {
    try {
      const alpineData = window.Alpine.$data(alpineRoot);
      if (alpineData && alpineData.tabAktif !== 'arsip') {
        alpineData.tabAktif = 'arsip';
      }
    } catch (e) {
      console.warn('Gagal beralih ke tab arsip Alpine:', e);
    }
  }

  // Pastikan data arsip termuat
  if (window.muatTabArsip) {
    await window.muatTabArsip();
  }

  // Berikan jeda untuk render dan transisi DOM tab Arsip
  await new Promise(r => setTimeout(r, 260));

  // Pastikan filter pencarian di arsip bersih agar kartu tidak terfilter
  const searchInput = document.getElementById('arsip-search-input');
  if (searchInput && searchInput.value) {
    searchInput.value = '';
    const searchClear = document.getElementById('arsip-search-clear');
    if (searchClear) searchClear.style.display = 'none';
    if (window.filterArsipCards) window.filterArsipCards('');
  }

  // 2. Cari elemen kartu berita di DOM arsip
  const cards = Array.from(document.querySelectorAll('#arsip-card-container article, main article'));
  let matchedCard = null;

  // A. Pencarian berdasarkan judul
  if (targetJudul) {
    const targetKeywords = targetJudul.toLowerCase().slice(0, 35);
    matchedCard = cards.find(card => {
      const h3 = (card.querySelector('h3')?.textContent || '').toLowerCase();
      const txt = (card.getAttribute('data-search-text') || '').toLowerCase();
      return h3.includes(targetKeywords) || txt.includes(targetKeywords);
    });
  }

  // B. Pencarian berdasarkan CVE ID
  if (!matchedCard && cveId && cveId.toUpperCase().startsWith('CVE-')) {
    const cveClean = cveId.toLowerCase();
    matchedCard = cards.find(card => {
      const txt = (card.getAttribute('data-search-text') || '').toLowerCase();
      return txt.includes(cveClean);
    });
  }

  // C. Pencarian berdasarkan aplikasi terdampak
  if (!matchedCard && cve.aplikasi_terdampak) {
    const appClean = cve.aplikasi_terdampak.toLowerCase();
    matchedCard = cards.find(card => {
      const txt = (card.getAttribute('data-search-text') || '').toLowerCase();
      return txt.includes(appClean);
    });
  }

  // 3. Jika kartu ditemukan di DOM: scroll animasi & nyalakan efek pendaran (glow)
  if (matchedCard) {
    // Animasi smooth scroll
    matchedCard.scrollIntoView({ behavior: 'smooth', block: 'center' });

    // Efek pendaran neon menyala sebagai penanda
    setTimeout(() => {
      matchedCard.classList.remove('animate-target-highlight');
      void matchedCard.offsetWidth; // trigger reflow
      matchedCard.classList.add('animate-target-highlight');
    }, 280);

    if (window.tampilkanToast) {
      window.tampilkanToast(`Berita ditemukan dan disorot di arsip`, 'sukses', 3000);
    }
  } else {
    // 4. Jika kartu tidak ditemukan pada rentang aktif arsip, buka langsung modal rangkuman berita
    if (window.bukaModal) {
      window.bukaModal({
        judul: targetJudul || `Laporan Intelijen ${cveId}`,
        teksLengkap: ringkasan || `Kerentanan ${cveId} (${cve.aplikasi_terdampak || 'Sistem'}) dilaporkan oleh ${sumber}.`,
        sumber: sumber,
        link: link,
        pillLabel: `[ ${cveId} ]`,
        pillClass: 'bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40 font-mono'
      });
    }
    if (window.tampilkanToast) {
      window.tampilkanToast(`Membuka rangkuman berita intelijen ${cveId}`, 'info', 3000);
    }
  }
}

window.sorotAtauBukaBeritaCve = sorotAtauBukaBeritaCve;
