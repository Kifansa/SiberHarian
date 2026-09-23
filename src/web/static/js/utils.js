/**
 * Utility umum dipakai lintas tab (Beranda, Arsip, Tren Siber).
 */
export function escapeHtml(teks) {
  const div = document.createElement('div');
  div.textContent = teks ?? '';
  return div.innerHTML;
}

export function sanitizeUrl(url) {
  if (!url || typeof url !== 'string') return '#';
  const trimmed = url.trim();
  if (trimmed.startsWith('https://') || trimmed.startsWith('http://')) {
    return trimmed;
  }
  return '#';
}

export function debounce(func, wait = 150) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

export function formatTanggalIndonesia(tanggalIso) {
  // tanggalIso format 'YYYY-MM-DD' (bucket tanggal publikasi dari backend)
  if (!tanggalIso || tanggalIso === 'tanggal_tidak_diketahui') return 'Tanggal tidak diketahui';
  const [tahun, bulan, tanggal] = tanggalIso.split('-').map(Number);
  const namaHari = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
  const namaBulan = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
  const tanggalObj = new Date(tahun, bulan - 1, tanggal);
  return `${namaHari[tanggalObj.getDay()]}, ${tanggal} ${namaBulan[bulan - 1]} ${tahun}`;
}

export function formatTanggalSingkat(tanggalIso) {
  if (!tanggalIso || tanggalIso === 'tanggal_tidak_diketahui') return tanggalIso;
  const parts = tanggalIso.slice(0, 10).split('-').map(Number);
  if (parts.length < 3) return tanggalIso;
  const [, bulan, tanggal] = parts;
  const namaBulan = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
  return `${tanggal} ${namaBulan[bulan - 1] || ''}`;
}

export function formatWaktuSekarang() {
  return new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) + ' WIB';
}

export function formatWaktuScraping(waktuStr) {
  if (!waktuStr) return 'Belum ada riwayat pembaruan';
  const parts = String(waktuStr).trim().split(/[- :T]/);
  if (parts.length >= 5) {
    const tahun = parts[0];
    const bulan = parseInt(parts[1], 10);
    const tgl = parseInt(parts[2], 10);
    const jam = parts[3].padStart(2, '0');
    const menit = parts[4].padStart(2, '0');
    const namaBulan = [
      'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
      'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
    ];
    const bulanNama = namaBulan[bulan - 1] || parts[1];
    return `${tgl} ${bulanNama} ${tahun}, ${jam}:${menit} WIB`;
  }
  return waktuStr;
}

/**
 * Menampilkan animasi angka bertambah secara halus (count-up animation).
 */
export function animateNumber(element, endVal, duration = 450, decimals = 0) {
  if (!element) return;
  const target = Number(endVal) || 0;
  const startVal = 0;
  const startTime = performance.now();

  function step(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / duration, 1);
    // Cubic ease-out
    const easeOut = 1 - Math.pow(1 - progress, 3);
    const current = startVal + (target - startVal) * easeOut;
    element.textContent = decimals > 0 ? current.toFixed(decimals) : Math.round(current);
    if (progress < 1) {
      requestAnimationFrame(step);
    } else {
      element.textContent = decimals > 0 ? target.toFixed(decimals) : target;
    }
  }
  requestAnimationFrame(step);
}

/**
 * Menampilkan toast notification mengambang di pojok kanan bawah.
 */
export function tampilkanToast(pesan, tipe = 'sukses') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed bottom-6 right-6 z-50 flex flex-col gap-2 pointer-events-none';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  let bg = 'bg-[#001D39] text-white border border-[#15803d]/70 shadow-xl';
  let icon = 'check_circle';
  let iconColor = 'text-emerald-400';

  if (tipe === 'error') {
    bg = 'bg-[#001D39] text-white border border-[#b91c1c]/70 shadow-xl';
    icon = 'error';
    iconColor = 'text-rose-400';
  } else if (tipe === 'warning') {
    bg = 'bg-[#001D39] text-white border border-[#b45309]/70 shadow-xl';
    icon = 'warning';
    iconColor = 'text-amber-400';
  } else if (tipe === 'info') {
    bg = 'bg-[#001D39] text-white border border-[#0A4174] shadow-xl';
    icon = 'info';
    iconColor = 'text-[#7BBDE8]';
  }

  toast.className = `flex items-center gap-2.5 px-4 py-2.5 rounded-md text-xs font-semibold shadow-md transition-all duration-300 transform translate-y-3 opacity-0 pointer-events-auto ${bg}`;
  toast.innerHTML = `
    <span class="material-symbols-outlined text-lg ${iconColor}" aria-hidden="true">${icon}</span>
    <span>${escapeHtml(pesan)}</span>
  `;

  toastContainer.appendChild(toast);

  // Animasi Masuk
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-3', 'opacity-0');
    toast.classList.add('translate-y-0', 'opacity-100');
  });

  // Animasi Keluar setelah 2.5 detik
  setTimeout(() => {
    toast.classList.remove('translate-y-0', 'opacity-100');
    toast.classList.add('translate-y-3', 'opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}