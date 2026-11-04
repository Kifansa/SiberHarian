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
 * Menampilkan floating popup / toast notification taktis dengan tema dark cyber.
 */
export function tampilkanToast(pesan, tipe = 'sukses', durasiMs = null) {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'fixed top-5 right-5 sm:top-6 sm:right-6 z-[99999] flex flex-col gap-2.5 pointer-events-none max-w-sm sm:max-w-md w-full px-4 sm:px-0';
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  let borderCol = 'border-[#00ff9d]/60 text-[#00ff9d] shadow-[0_0_25px_rgba(0,255,157,0.25)]';
  let badgeCol = 'bg-[#00ff9d]/15 text-[#00ff9d] border border-[#00ff9d]/30';
  let icon = 'check_circle';
  let label = 'SUKSES';

  if (tipe === 'error') {
    borderCol = 'border-[#ff3366]/60 text-[#ff3366] shadow-[0_0_25px_rgba(255,51,102,0.3)]';
    badgeCol = 'bg-[#ff3366]/15 text-[#ff3366] border border-[#ff3366]/30';
    icon = 'error';
    label = 'GAGAL';
  } else if (tipe === 'warning') {
    borderCol = 'border-[#ffc107]/60 text-[#ffc107] shadow-[0_0_25px_rgba(255,193,7,0.3)]';
    badgeCol = 'bg-[#ffc107]/15 text-[#ffc107] border border-[#ffc107]/30';
    icon = 'warning';
    label = 'PERINGATAN';
  } else if (tipe === 'info') {
    borderCol = 'border-[#00d4ff]/60 text-[#00d4ff] shadow-[0_0_25px_rgba(0,212,255,0.3)]';
    badgeCol = 'bg-[#00d4ff]/15 text-[#00d4ff] border border-[#00d4ff]/30';
    icon = 'info';
    label = 'INFO';
  }

  const durasi = durasiMs || (tipe === 'error' ? 4500 : 3200);

  toast.className = `flex items-start gap-3 p-3.5 rounded-xl text-xs font-mono font-medium bg-[#0d2137]/95 backdrop-blur-md border transition-all duration-300 transform -translate-y-2 opacity-0 scale-95 pointer-events-auto ${borderCol}`;
  toast.innerHTML = `
    <span class="material-symbols-outlined text-lg shrink-0 mt-0.5" aria-hidden="true">${icon}</span>
    <div class="flex-1 min-w-0 pr-1">
      <div class="flex items-center gap-2 mb-1">
        <span class="text-[10px] px-1.5 py-0.5 rounded font-bold uppercase tracking-wider font-mono ${badgeCol}">[ ${label} ]</span>
      </div>
      <p class="text-[#e0f0ff] font-sans font-medium text-xs leading-relaxed break-words">${escapeHtml(pesan)}</p>
    </div>
    <button type="button" class="text-[#7d8ca6] hover:text-[#e0f0ff] cursor-pointer shrink-0 p-0.5 transition-colors" title="Tutup">
      <span class="material-symbols-outlined text-base">close</span>
    </button>
  `;

  // Tombol tutup manual
  const btnClose = toast.querySelector('button');
  let isClosed = false;
  const dismissToast = () => {
    if (isClosed) return;
    isClosed = true;
    toast.classList.remove('translate-y-0', 'opacity-100', 'scale-100');
    toast.classList.add('-translate-y-2', 'opacity-0', 'scale-95');
    setTimeout(() => toast.remove(), 250);
  };

  if (btnClose) {
    btnClose.addEventListener('click', dismissToast);
  }

  toastContainer.appendChild(toast);

  // Animasi Masuk
  requestAnimationFrame(() => {
    toast.classList.remove('-translate-y-2', 'opacity-0', 'scale-95');
    toast.classList.add('translate-y-0', 'opacity-100', 'scale-100');
  });

  // Animasi Keluar otomatis
  setTimeout(dismissToast, durasi);
}

/**
 * Menampilkan popup dialog konfirmasi modal di tengah layar dengan tema dark cyber.
 * Mengembalikan Promise<boolean>: true jika user menekan tombol konfirmasi, false jika batal/tutup/escape.
 */
export function tampilkanKonfirmasi(opsi) {
  let config = {
    judul: 'KONFIRMASI TINDAKAN',
    pesan: '',
    subteks: '',
    teksKonfirmasi: 'Konfirmasi',
    teksBatal: 'Batal',
    tipe: 'danger' // 'danger' | 'warning' | 'info'
  };

  if (typeof opsi === 'string') {
    config.pesan = opsi;
  } else if (typeof opsi === 'object' && opsi !== null) {
    config = Object.assign(config, opsi);
  }

  return new Promise((resolve) => {
    // Hilangkan dialog konfirmasi sebelumnya jika ada yang masih aktif
    const existingOverlay = document.getElementById('dialog-konfirmasi-overlay');
    if (existingOverlay) {
      existingOverlay.remove();
    }

    const overlay = document.createElement('div');
    overlay.id = 'dialog-konfirmasi-overlay';
    overlay.className = 'fixed inset-0 z-[100000] flex items-center justify-center p-4 bg-[#0a1628]/85 backdrop-blur-sm transition-opacity duration-200 opacity-0 pointer-events-auto';

    let borderCol = 'border-[#ff3366]/50 shadow-[0_0_35px_rgba(255,51,102,0.25)]';
    let iconCol = 'text-[#ff3366] bg-[#ff3366]/10 border border-[#ff3366]/30';
    let btnConfirmCol = 'bg-[#ff3366] hover:bg-[#ff3366]/80 text-white shadow-[0_0_15px_rgba(255,51,102,0.4)]';
    let icon = 'warning';
    let badgeText = 'PERINGATAN SISTEM';

    if (config.tipe === 'warning') {
      borderCol = 'border-[#ffc107]/50 shadow-[0_0_35px_rgba(255,193,7,0.25)]';
      iconCol = 'text-[#ffc107] bg-[#ffc107]/10 border border-[#ffc107]/30';
      btnConfirmCol = 'bg-[#ffc107] hover:bg-[#ffc107]/80 text-[#0a1628] font-bold shadow-[0_0_15px_rgba(255,193,7,0.4)]';
      icon = 'help';
      badgeText = 'PERINGATAN';
    } else if (config.tipe === 'info') {
      borderCol = 'border-[#00d4ff]/50 shadow-[0_0_35px_rgba(0,212,255,0.25)]';
      iconCol = 'text-[#00d4ff] bg-[#00d4ff]/10 border border-[#00d4ff]/30';
      btnConfirmCol = 'bg-[#00d4ff] hover:bg-[#00ff9d] text-[#0a1628] font-bold shadow-[0_0_15px_rgba(0,212,255,0.4)]';
      icon = 'info';
      badgeText = 'KONFIRMASI OPERASIONAL';
    }

    overlay.innerHTML = `
      <div class="relative bg-[#0d2137]/95 backdrop-blur-md rounded-2xl max-w-md w-full p-6 border ${borderCol} transform transition-all duration-200 scale-95 opacity-0 font-['Sora']" id="dialog-konfirmasi-box" role="dialog" aria-modal="true">
        <!-- Close 'X' button -->
        <button type="button" id="dialog-konfirmasi-close" class="absolute top-4 right-4 text-[#7d8ca6] hover:text-[#e0f0ff] w-8 h-8 rounded-lg hover:bg-[#132c4a] flex items-center justify-center transition-colors cursor-pointer" title="Tutup (Esc)">
          <span class="material-symbols-outlined text-lg">close</span>
        </button>

        <div class="flex items-start gap-3.5 mb-4 pr-6">
          <div class="w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${iconCol}">
            <span class="material-symbols-outlined text-xl">${icon}</span>
          </div>
          <div class="min-w-0">
            <span class="text-[10px] font-mono font-bold tracking-wider uppercase text-[#7d8ca6] block mb-0.5">[ ${badgeText} ]</span>
            <h3 class="text-base font-bold text-[#e0f0ff] leading-snug tracking-tight">${escapeHtml(config.judul)}</h3>
          </div>
        </div>

        <div class="mb-5 space-y-2">
          <p class="text-sm text-[#e0f0ff] leading-relaxed break-words font-medium">${escapeHtml(config.pesan)}</p>
          ${config.subteks ? `<p class="text-xs text-[#8892b0] font-mono leading-relaxed break-words">${escapeHtml(config.subteks)}</p>` : ''}
        </div>

        <div class="flex items-center justify-end gap-2.5 pt-3 border-t border-[#1a3a5c]">
          <button type="button" id="dialog-konfirmasi-batal" class="px-4 py-2 rounded-lg bg-[#1a3a5c] hover:bg-[#132c4a] text-[#e0f0ff] text-xs font-mono font-semibold transition-colors cursor-pointer">
            ${escapeHtml(config.teksBatal)}
          </button>
          <button type="button" id="dialog-konfirmasi-setuju" class="px-4 py-2 rounded-lg ${btnConfirmCol} text-xs font-mono font-bold tracking-wide transition-all cursor-pointer">
            ${escapeHtml(config.teksKonfirmasi)}
          </button>
        </div>
      </div>
    `;

    document.body.appendChild(overlay);

    const box = overlay.querySelector('#dialog-konfirmasi-box');
    const btnSetuju = overlay.querySelector('#dialog-konfirmasi-setuju');
    const btnBatal = overlay.querySelector('#dialog-konfirmasi-batal');
    const btnClose = overlay.querySelector('#dialog-konfirmasi-close');

    let resolved = false;
    const cleanup = (result) => {
      if (resolved) return;
      resolved = true;
      document.removeEventListener('keydown', handleKey);
      overlay.classList.remove('opacity-100');
      overlay.classList.add('opacity-0');
      if (box) {
        box.classList.remove('scale-100', 'opacity-100');
        box.classList.add('scale-95', 'opacity-0');
      }
      setTimeout(() => overlay.remove(), 200);
      resolve(result);
    };

    const handleKey = (e) => {
      if (e.key === 'Escape') {
        cleanup(false);
      }
    };

    document.addEventListener('keydown', handleKey);

    btnSetuju.addEventListener('click', () => cleanup(true));
    btnBatal.addEventListener('click', () => cleanup(false));
    btnClose.addEventListener('click', () => cleanup(false));
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay) cleanup(false);
    });

    // Animasi Masuk
    requestAnimationFrame(() => {
      overlay.classList.remove('opacity-0');
      overlay.classList.add('opacity-100');
      if (box) {
        box.classList.remove('scale-95', 'opacity-0');
        box.classList.add('scale-100', 'opacity-100');
      }
      btnSetuju.focus();
    });
  });
}

if (typeof window !== 'undefined') {
  window.tampilkanToast = tampilkanToast;
  window.tampilkanKonfirmasi = tampilkanKonfirmasi;
}
