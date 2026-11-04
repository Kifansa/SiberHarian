import { animateNumber } from '../utils.js?v=9.5';

/**
 * Memberikan efek highlight ring berkedip pada kartu KPI saat data berhasil diperbarui
 */
export function flashUpdatedCards() {
  const cards = document.querySelectorAll('.kpi-card, .chart-card');
  cards.forEach(card => {
    card.classList.add('ring-2', 'ring-[#00d4ff]/60', 'ring-offset-1', 'ring-offset-[#0a1628]');
    setTimeout(() => {
      card.classList.remove('ring-2', 'ring-[#00d4ff]/60', 'ring-offset-1', 'ring-offset-[#0a1628]');
    }, 800);
  });
}

/**
 * Menyesuaikan ukuran font elemen KPI secara dinamis berdasarkan panjang karakter
 * @param {HTMLElement} element Elemen yang akan disesuaikan kelas fontnya
 * @param {string} text Teks yang ditampilkan
 * @param {Object} options Konfigurasi ambang batas karakter (shortMax, medMax)
 */
export function adjustKpiFontSize(element, text, options = {}) {
  if (!element) return;
  const str = String(text || '').trim();
  const len = str.length;

  element.classList.remove(
    'text-3xl', 'sm:text-4xl',
    'text-2xl', 'sm:text-3xl',
    'text-xl', 'sm:text-2xl',
    'text-lg', 'sm:text-xl',
    'text-base', 'sm:text-lg',
    'text-sm', 'sm:text-base',
    'text-xs', 'sm:text-sm',
    'leading-none', 'leading-snug', 'leading-tight',
    'truncate'
  );

  const shortMax = options.shortMax ?? 10;
  const medMax = options.medMax ?? 20;

  if (len <= shortMax) {
    element.classList.add('text-2xl', 'sm:text-3xl', 'font-extrabold', 'leading-tight', 'break-words');
  } else if (len <= medMax) {
    element.classList.add('text-lg', 'sm:text-xl', 'font-bold', 'leading-snug', 'break-words');
  } else {
    element.classList.add('text-sm', 'sm:text-base', 'font-bold', 'leading-tight', 'break-words');
  }
}

/**
 * Merender metrik angka, persentase pertumbuhan, dan status pada kartu KPI eksekutif (CSIRT Jatim Cyber-HUD Style)
 * @param {Object} stat Data statistik tren dari backend
 * @param {boolean} isAnimated Apakah menggunakan animasi penghitungan angka
 */
export function renderKpiCards(stat, isAnimated = false) {
  if (!stat) return;

  // KPI 1: Insiden Berita
  const kpiBerita = document.getElementById('kpi-total-berita');
  const kpiBeritaGrowth = document.getElementById('kpi-berita-growth');
  const totalBerita = stat.total_berita ?? 0;
  if (kpiBerita) {
    if (isAnimated) {
      animateNumber(kpiBerita, totalBerita, 450, 0);
    } else {
      kpiBerita.textContent = totalBerita;
    }
  }

  const insidenGrowth = stat.tren_kategori?.insiden_spesifik?.growth_persen ?? 0;
  if (kpiBeritaGrowth) {
    const isUp = insidenGrowth >= 0;
    const icon = isUp ? 'trending_up' : 'trending_down';
    const colorClass = isUp ? 'text-[#00ff88]' : 'text-[#ff3366]';
    kpiBeritaGrowth.className = `inline-flex items-center gap-1 text-xs sm:text-sm font-bold font-mono whitespace-nowrap shrink-0 ${colorClass}`;
    kpiBeritaGrowth.innerHTML = `
      <span class="material-symbols-outlined text-base leading-none">${icon}</span>
      <span>${isUp ? '+' : ''}${insidenGrowth}%</span>
    `;
  }

  // KPI 2: Sektor Paling Terdampak
  const kpiSektor = document.getElementById('kpi-top-sektor') || document.getElementById('kpi-total-insiden-kritis');
  const kpiSektorBadge = document.getElementById('kpi-sektor-badge') || document.getElementById('kpi-insiden-kritis-growth');
  const kpiSektorSubtext = document.getElementById('kpi-sektor-subtext');

  const sektorList = stat.top_sektor || stat.sektor_target || [];
  const topSektor = sektorList.length > 0 ? sektorList[0] : null;

  if (kpiSektor) {
    const namaSektor = topSektor ? topSektor.sektor : 'Belum Ada Data';
    kpiSektor.textContent = namaSektor;
    kpiSektor.title = `Sektor Paling Terdampak: ${namaSektor}`;
    adjustKpiFontSize(kpiSektor, namaSektor, { shortMax: 14, medMax: 26 });
  }

  if (topSektor && kpiSektorBadge) {
    const growthSektor = topSektor.growth_persen ?? 0;
    const isUp = growthSektor >= 0;
    const icon = isUp ? 'trending_up' : 'trending_down';
    const colorClass = isUp ? 'text-[#00ff88]' : 'text-[#ff3366]';
    kpiSektorBadge.className = `inline-flex items-center gap-1 text-xs sm:text-sm font-bold font-mono whitespace-nowrap shrink-0 ${colorClass}`;
    kpiSektorBadge.innerHTML = `
      <span class="material-symbols-outlined text-base leading-none" id="kpi-sektor-icon">${icon}</span>
      <span id="kpi-sektor-growth">${isUp ? '+' : ''}${growthSektor}%</span>
    `;
    if (kpiSektorSubtext) {
      kpiSektorSubtext.textContent = 'vs minggu lalu';
    }
  } else if (kpiSektorBadge) {
    kpiSektorBadge.innerHTML = '<span>-</span>';
  }

  // KPI 3: Tren Insiden Mingguan (Pola Serangan Organik Dinamis)
  const kpiPola = document.getElementById('kpi-pola-serangan');
  const kpiPolaBadge = document.getElementById('kpi-pola-badge');
  const kpiPolaGrowth = document.getElementById('kpi-pola-growth');
  const kpiPolaSubtext = document.getElementById('kpi-pola-subtext');

  const polaData = stat.prediksi_pola_serangan || {};
  let namaPola = (polaData.pola || 'Belum Ada Data').trim();
  namaPola = namaPola.replace(/^TREN LONJAKAN:\s*/i, '');
  const polaGrowth = polaData.growth_persen ?? 0.0;

  if (kpiPola) {
    kpiPola.textContent = namaPola;
    kpiPola.title = `Tren Insiden Mingguan: ${namaPola}`;
    adjustKpiFontSize(kpiPola, namaPola, { shortMax: 14, medMax: 24 });
  }
  if (kpiPolaGrowth) {
    kpiPolaGrowth.textContent = `${polaGrowth >= 0 ? '+' : ''}${polaGrowth}%`;
  }
  if (kpiPolaSubtext) {
    kpiPolaSubtext.textContent = 'vs minggu lalu';
  }
  if (kpiPolaBadge) {
    const isUp = polaGrowth >= 0;
    const icon = isUp ? 'trending_up' : 'trending_down';
    const colorClass = isUp ? 'text-[#00ff88]' : 'text-[#ff3366]';
    const colorHex = isUp ? '#00ff88' : '#ff3366';
    kpiPolaBadge.className = `inline-flex items-center gap-1 text-xs sm:text-sm font-bold font-mono whitespace-nowrap shrink-0 ${colorClass}`;
    kpiPolaBadge.style.color = colorHex;
    kpiPolaBadge.innerHTML = `
      <span class="material-symbols-outlined text-base leading-none" id="kpi-pola-icon" style="color: ${colorHex}">${icon}</span>
      <span id="kpi-pola-growth" style="color: ${colorHex}">${isUp ? '+' : ''}${polaGrowth}%</span>
    `;
  }

  // KPI 4: Prediksi Ancaman Baru (Kategori Taksonomi Sinyal Baru)
  const elAncamanBaru = document.getElementById('kpi-ancaman-baru');
  if (elAncamanBaru) {
    const teksAncaman = (stat.ancaman_baru || 'Kondisi Stabil').trim();
    elAncamanBaru.textContent = teksAncaman;
    elAncamanBaru.title = `Prediksi Ancaman Baru: ${teksAncaman}`;
    adjustKpiFontSize(elAncamanBaru, teksAncaman, { shortMax: 14, medMax: 26 });
  }
}
