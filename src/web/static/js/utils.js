/**
 * Utility umum dipakai lintas tab (Beranda, Arsip, Tren Siber).
 */
export function escapeHtml(teks) {
  const div = document.createElement('div');
  div.textContent = teks ?? '';
  return div.innerHTML;
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
  const bg = tipe === 'sukses' 
    ? 'bg-slate-900/95 text-white border border-slate-700/50 shadow-2xl' 
    : 'bg-rose-900/95 text-white border border-rose-700/50 shadow-2xl';
  const icon = tipe === 'sukses' ? 'check_circle' : 'error';
  const iconColor = tipe === 'sukses' ? 'text-emerald-400' : 'text-rose-400';

  toast.className = `flex items-center gap-2.5 px-4 py-2.5 rounded-xl text-xs font-semibold backdrop-blur transition-all duration-300 transform translate-y-3 opacity-0 pointer-events-auto ${bg}`;
  toast.innerHTML = `
    <span class="material-symbols-outlined text-[18px] ${iconColor}">${icon}</span>
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