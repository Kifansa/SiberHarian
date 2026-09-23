import { animateNumber } from '../utils.js';

/**
 * Memberikan efek highlight ring berkedip pada kartu KPI saat data berhasil diperbarui
 */
export function flashUpdatedCards() {
  const cards = document.querySelectorAll('.kpi-card, .chart-card');
  cards.forEach(card => {
    card.classList.add('ring-2', 'ring-[#7BBDE8]/60', 'ring-offset-1');
    setTimeout(() => {
      card.classList.remove('ring-2', 'ring-[#7BBDE8]/60', 'ring-offset-1');
    }, 800);
  });
}

/**
 * Merender metrik angka, persentase pertumbuhan, dan status pada kartu KPI eksekutif
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
    const colorClass = isUp ? 'text-emerald-600' : 'text-rose-600';
    kpiBeritaGrowth.className = `inline-flex items-center gap-1 text-xs sm:text-sm font-bold font-mono ${colorClass}`;
    kpiBeritaGrowth.innerHTML = `
      <span class="material-symbols-outlined text-base leading-none">${icon}</span>
      <span>${isUp ? '+' : ''}${insidenGrowth}%</span>
    `;
  }

  // KPI 2: Total CVE
  const kpiCve = document.getElementById('kpi-total-cve');
  const kpiCveGrowth = document.getElementById('kpi-cve-growth') || document.getElementById('kpi-cve-vendor');
  const totalCve = stat.total_cve ?? 0;
  if (kpiCve) {
    if (isAnimated) {
      animateNumber(kpiCve, totalCve, 450, 0);
    } else {
      kpiCve.textContent = totalCve;
    }
  }
  
  const cveGrowth = stat.cve_growth ?? (
    stat.threat_posture?.total_cve_baseline != null && stat.threat_posture.total_cve_baseline > 0
      ? Math.round(((totalCve - stat.threat_posture.total_cve_baseline) / stat.threat_posture.total_cve_baseline) * 100)
      : (stat.vendor_naik?.[0]?.growth_persen ?? 0)
  );
  if (kpiCveGrowth) {
    const isUp = cveGrowth >= 0;
    const icon = isUp ? 'trending_up' : 'trending_down';
    const colorClass = isUp ? 'text-emerald-600' : 'text-rose-600';
    kpiCveGrowth.className = `inline-flex items-center gap-1 text-xs sm:text-sm font-bold font-mono ${colorClass}`;
    kpiCveGrowth.innerHTML = `
      <span class="material-symbols-outlined text-base leading-none">${icon}</span>
      <span>${isUp ? '+' : ''}${cveGrowth}%</span>
    `;
  }

  // KPI 3: Prediksi Pola Serangan (1 Kata Saja)
  const kpiPola = document.getElementById('kpi-pola-serangan');
  const kpiPolaBadge = document.getElementById('kpi-pola-badge');
  const kpiPolaGrowth = document.getElementById('kpi-pola-growth');
  const kpiPolaSubtext = document.getElementById('kpi-pola-subtext');

  const polaData = stat.prediksi_pola_serangan || {};
  const namaPola = (polaData.pola || 'RCE').trim().toUpperCase();
  const polaGrowth = polaData.growth_persen ?? 50.0;

  if (kpiPola) {
    kpiPola.textContent = namaPola;
    kpiPola.title = `Pola Serangan Terprediksi: ${namaPola}`;
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
    const colorClass = isUp ? 'text-emerald-600' : 'text-rose-600';
    kpiPolaBadge.className = `inline-flex items-center gap-1 text-xs sm:text-sm font-bold font-mono ${colorClass}`;
    kpiPolaBadge.innerHTML = `
      <span class="material-symbols-outlined text-base leading-none">${icon}</span>
      <span id="kpi-pola-growth">${isUp ? '+' : ''}${polaGrowth}%</span>
    `;
  }

  // Card: Prediksi Ancaman Baru
  const elAncamanBaru = document.getElementById('kpi-ancaman-baru');
  if (elAncamanBaru) {
    const teksAncaman = stat.ancaman_baru || 'Menunggu Sinyal';
    elAncamanBaru.textContent = teksAncaman;
    elAncamanBaru.title = teksAncaman;
    
    // Auto-shrink font size jika teks terlalu panjang (> 15 karakter)
    if (teksAncaman.length > 25) {
      elAncamanBaru.className = "text-sm sm:text-base font-black text-[#001D39] tracking-tight font-sans leading-tight line-clamp-2";
    } else if (teksAncaman.length > 15) {
      elAncamanBaru.className = "text-lg sm:text-xl font-black text-[#001D39] tracking-tight font-sans leading-tight truncate";
    } else {
      elAncamanBaru.className = "text-2xl sm:text-3xl font-black text-[#001D39] tracking-tight font-sans leading-none uppercase truncate";
    }
  }
}
