/**
 * State & kontrol modal "Selengkapnya" dengan animasi transisi, focus trapping, dan fitur Salin Rangkuman.
 */

// Global registry terpusat agar konsisten lintas modul dan perpindahan tab
if (!window.__siberDataLengkap) {
  window.__siberDataLengkap = [];
}
export const dataLengkap = window.__siberDataLengkap;

if (!window.__siberDataMap) {
  window.__siberDataMap = new Map();
}
export const dataMap = window.__siberDataMap;

export function simpanItemModal(item) {
  const id = dataLengkap.length;
  dataLengkap.push(item);
  if (item && item.judul) {
    dataMap.set(item.judul, item);
  }
  return id;
}

export function resetDataLengkap() {
  // Tidak mengosongkan array secara destruktif agar kartu berita yang sudah dirender di DOM
  // tetap dapat dibuka saat pengguna berpindah tab (Beranda <-> Arsip)
}

let timeoutTutup = null;
let elemenPemicuSebelumnya = null;

export function bukaModal(itemOrIdx, paramTeksLengkap, paramPillLabel, paramSumber, paramLink) {
  let item = null;

  if (typeof itemOrIdx === 'number' || (typeof itemOrIdx === 'string' && !isNaN(Number(itemOrIdx)) && itemOrIdx.trim() !== '' && arguments.length === 1)) {
    const idx = Number(itemOrIdx);
    item = dataLengkap[idx];
  } else if (typeof itemOrIdx === 'object' && itemOrIdx !== null) {
    item = itemOrIdx;
  } else if (typeof itemOrIdx === 'string') {
    if (dataMap.has(itemOrIdx) && arguments.length === 1) {
      item = dataMap.get(itemOrIdx);
    } else {
      item = {
        judul: itemOrIdx,
        teksLengkap: paramTeksLengkap || '',
        pillLabel: paramPillLabel || '',
        pillClass: paramPillLabel ? 'bg-[#0d2137] text-[#00d4ff] border border-[#00d4ff]/40 font-mono' : '',
        sumber: paramSumber || '',
        link: (paramLink && paramLink !== '#') ? paramLink : ''
      };
    }
  }

  if (!item) {
    console.warn('bukaModal: data ringkasan tidak ditemukan untuk', itemOrIdx);
    return;
  }

  if (timeoutTutup) {
    clearTimeout(timeoutTutup);
    timeoutTutup = null;
  }

  elemenPemicuSebelumnya = document.activeElement;

  const elPill = document.getElementById('modal-pill');
  const elSumber = document.getElementById('modal-sumber');
  const elJudul = document.getElementById('modal-judul');
  const elTeks = document.getElementById('modal-teks');
  const elLink = document.getElementById('modal-link');
  const elOverlay = document.getElementById('modal-overlay');
  const elModalBox = document.getElementById('modal-box');
  const btnCopy = document.getElementById('modal-btn-copy');

  if (elPill) {
    if (item.pillLabel) {
      elPill.textContent = item.pillLabel;
      elPill.className = 'px-2.5 py-0.5 rounded-md font-mono text-xs font-semibold ' + item.pillClass;
      elPill.style.display = 'inline-block';
    } else {
      elPill.textContent = '';
      elPill.className = '';
      elPill.style.display = 'none';
    }
  }
  if (elSumber) elSumber.textContent = item.sumber || '';
  if (elJudul) elJudul.textContent = item.judul || '';
  if (elTeks) elTeks.textContent = item.teksLengkap || '';
  if (elLink) {
    const safeLink = (item.link && item.link !== '#') ? item.link : '';
    if (safeLink) {
      elLink.href = safeLink;
      elLink.style.display = 'inline-flex';
    } else {
      elLink.style.display = 'none';
    }
  }

  if (btnCopy) {
    btnCopy.innerHTML = '<span class="material-symbols-outlined text-base" aria-hidden="true">content_copy</span><span>Salin Rangkuman</span>';
    btnCopy.disabled = false;
    btnCopy.onclick = () => salinTeksModal(item);
  }

  if (elOverlay && elModalBox) {
    elOverlay.classList.remove('hidden');
    elOverlay.classList.add('flex');
    elOverlay.setAttribute('aria-hidden', 'false');
    
    // Trigger transisi buka dengan requestAnimationFrame
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        elOverlay.classList.remove('opacity-0', 'pointer-events-none');
        elOverlay.classList.add('opacity-100', 'pointer-events-auto');

        elModalBox.classList.remove('scale-95', 'opacity-0', 'translate-y-4');
        elModalBox.classList.add('scale-100', 'opacity-100', 'translate-y-0');

        // Fokuskan tombol tutup untuk aksesibilitas keyboard
        const closeBtn = elModalBox.querySelector('button[aria-label="Tutup dialog"]') || elModalBox.querySelector('button');
        if (closeBtn) closeBtn.focus();
      });
    });

    document.body.classList.add('overflow-hidden');
  }
}

export function tutupModal() {
  const overlay = document.getElementById('modal-overlay');
  const modalBox = document.getElementById('modal-box');
  if (!overlay || !modalBox) return;

  overlay.classList.remove('opacity-100', 'pointer-events-auto');
  overlay.classList.add('opacity-0', 'pointer-events-none');
  overlay.setAttribute('aria-hidden', 'true');

  modalBox.classList.remove('scale-100', 'opacity-100', 'translate-y-0');
  modalBox.classList.add('scale-95', 'opacity-0', 'translate-y-4');

  document.body.classList.remove('overflow-hidden');

  if (timeoutTutup) clearTimeout(timeoutTutup);
  timeoutTutup = setTimeout(() => {
    overlay.classList.add('hidden');
    overlay.classList.remove('flex');
    if (elemenPemicuSebelumnya && typeof elemenPemicuSebelumnya.focus === 'function') {
      elemenPemicuSebelumnya.focus();
      elemenPemicuSebelumnya = null;
    }
  }, 250);
}

export function tutupModalJikaLuar(event) {
  if (event.target.id === 'modal-overlay') {
    tutupModal();
  }
}

export async function salinTeksModal(item) {
  if (!item) return;
  const btnCopy = document.getElementById('modal-btn-copy');
  const headerLabel = item.pillLabel ? `[SIBERHARIAN - ${item.pillLabel.toUpperCase()}]` : `[SIBERHARIAN]`;
  const teksSalin = `${headerLabel}\nJudul: ${item.judul}\nSumber / Vendor: ${item.sumber}\n\nRingkasan:\n${item.teksLengkap}\n\nTautan Sumber: ${item.link}`;

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(teksSalin);
    } else {
      const textarea = document.createElement('textarea');
      textarea.value = teksSalin;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand('copy');
      document.body.removeChild(textarea);
    }

    if (btnCopy) {
      btnCopy.innerHTML = '<span class="material-symbols-outlined text-base text-emerald-600" aria-hidden="true">check</span><span class="text-emerald-700 font-bold">Tersalin ke Clipboard!</span>';
      setTimeout(() => {
        if (btnCopy) {
          btnCopy.innerHTML = '<span class="material-symbols-outlined text-base" aria-hidden="true">content_copy</span><span>Salin Rangkuman</span>';
        }
      }, 2000);
    }
  } catch (err) {
    console.error('Gagal menyalin:', err);
    if (btnCopy) {
      btnCopy.textContent = 'Gagal menyalin';
    }
  }
}

// Trap focus keyboard di dalam modal & tombol ESC
window.addEventListener('keydown', (e) => {
  const overlay = document.getElementById('modal-overlay');
  const modalBox = document.getElementById('modal-box');
  const isModalOpen = overlay && !overlay.classList.contains('hidden') && overlay.classList.contains('opacity-100');

  if (!isModalOpen) return;

  if (e.key === 'Escape') {
    tutupModal();
    return;
  }

  if (e.key === 'Tab') {
    const focusable = modalBox.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
    if (!focusable || focusable.length === 0) return;

    const firstElement = focusable[0];
    const lastElement = focusable[focusable.length - 1];

    if (e.shiftKey) {
      if (document.activeElement === firstElement) {
        lastElement.focus();
        e.preventDefault();
      }
    } else {
      if (document.activeElement === lastElement) {
        firstElement.focus();
        e.preventDefault();
      }
    }
  }
});

// Self-expose ke window untuk kemudahan pemanggilan dari inline onclick HTML
if (typeof window !== 'undefined') {
  window.bukaModal = bukaModal;
  window.tutupModal = tutupModal;
  window.tutupModalJikaLuar = tutupModalJikaLuar;
  window.salinTeksModal = salinTeksModal;
}