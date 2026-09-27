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

/**
 * Merender indikator komposit Indeks Postur Ancaman Siber Komparatif
 * @param {Object} posture Data postur ancaman dari backend
 * @param {boolean} isAnimated Apakah menggunakan animasi penghitungan angka
 */
export function renderThreatPosture(posture, isAnimated = false) {
  if (!posture) return;

  const elScore = document.getElementById('posture-score');
  const elBadge = document.getElementById('posture-badge');
  const elAdvice = document.getElementById('posture-advice');
  const elGrowth = document.getElementById('posture-growth');
  const elGrowthIcon = document.getElementById('posture-growth-icon');
  const elGrowthWrap = document.getElementById('posture-growth-wrap');
  const elStatus = document.getElementById('posture-status-tren');
  const elAvgCvss = document.getElementById('posture-avg-cvss');
  const elTotalInsiden = document.getElementById('posture-total-insiden');

  const skor = posture.skor ?? 1.0;
  if (elScore) {
    if (isAnimated) {
      animateNumber(elScore, Math.round(skor * 10) / 10, 450, 1);
    } else {
      elScore.textContent = Number(skor).toFixed(1);
    }
  }

  // Level badge styling
  const level = posture.level || 'SEDANG';
  const label = posture.level_label || `${level}`;
  if (elBadge) {
    elBadge.textContent = label;
    if (level === 'KRITIS') {
      elBadge.className = 'px-2.5 py-0.5 rounded text-[11px] font-bold border font-mono bg-rose-50 text-rose-700 border-rose-200';
    } else if (level === 'TINGGI') {
      elBadge.className = 'px-2.5 py-0.5 rounded text-[11px] font-bold border font-mono bg-amber-50 text-amber-800 border-amber-200';
    } else if (level === 'SEDANG') {
      elBadge.className = 'px-2.5 py-0.5 rounded text-[11px] font-bold border font-mono bg-blue-50 text-blue-700 border-blue-200';
    } else {
      elBadge.className = 'px-2.5 py-0.5 rounded text-[11px] font-bold border font-mono bg-emerald-50 text-emerald-700 border-emerald-200';
    }
  }

  // Contextual advice
  if (elAdvice) {
    if (level === 'KRITIS') {
      elAdvice.textContent = 'Status Darurat: Terdeteksi eskalasi signifikan pada insiden aktif dan celah keamanan bernilai kritis. Prioritaskan isolasi perimeter dan eksekusi emergency patching.';
    } else if (level === 'TINGGI') {
      elAdvice.textContent = 'Status Waspada: Peningkatan volume insiden dan kemunculan celah sistem baru. Disarankan audit port perimeter, verifikasi integritas backup, dan sosialisasi pencegahan phishing ke OPD.';
    } else if (level === 'SEDANG') {
      elAdvice.textContent = 'Status Terkendali: Aktivitas ancaman siber terpantau stabil. Lanjutkan pemantauan log berkala dan penerapan pembaruan rutin pada sistem operasional instansi.';
    } else {
      elAdvice.textContent = 'Status Kondusif: Tidak ditemukan anomali lonjakan ancaman signifikan dalam 7 hari terakhir. Pertahankan kepatuhan keamanan preventif dan kebersihan kredensial.';
    }
  }

  // Growth & Status Tren
  const growth = posture.growth_persen ?? 0;
  const statusTren = posture.status_tren || 'Stabil';
  if (elGrowth) {
    elGrowth.textContent = `${growth >= 0 ? '+' : ''}${growth}%`;
  }
  if (elStatus) {
    elStatus.textContent = `${statusTren} vs baseline`;
  }
  if (elGrowthWrap) {
    if (growth > 5) {
      elGrowthWrap.className = 'flex items-center sm:justify-end gap-1 font-mono font-bold text-sm text-rose-600';
      if (elGrowthIcon) elGrowthIcon.textContent = 'trending_up';
    } else if (growth < -5) {
      elGrowthWrap.className = 'flex items-center sm:justify-end gap-1 font-mono font-bold text-sm text-emerald-600';
      if (elGrowthIcon) elGrowthIcon.textContent = 'trending_down';
    } else {
      elGrowthWrap.className = 'flex items-center sm:justify-end gap-1 font-mono font-bold text-sm text-[#49769F]';
      if (elGrowthIcon) elGrowthIcon.textContent = 'trending_flat';
    }
  }

  if (elAvgCvss) {
    elAvgCvss.textContent = `${Number(posture.avg_cvss ?? 0).toFixed(1)} / 10`;
  }
  if (elTotalInsiden) {
    elTotalInsiden.textContent = `${posture.total_insiden ?? 0} kasus`;
  }
}
