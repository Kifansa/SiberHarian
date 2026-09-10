/**
 * State & kontrol modal "Selengkapnya" dengan animasi transisi, focus trapping, dan fitur Salin Rangkuman.
 */
export const dataLengkap = [];

export function resetDataLengkap() {
  dataLengkap.length = 0;
}

let timeoutTutup = null;
let elemenPemicuSebelumnya = null;

export function bukaModal(idx) {
  const item = dataLengkap[idx];
  if (!item) return;

  if (timeoutTutup) {
    clearTimeout(timeoutTutup);
    timeoutTutup = null;
  }

  elemenPemicuSebelumnya = document.activeElement;

  const pill = document.getElementById('modal-pill');
  const sumber = document.getElementById('modal-sumber');
  const judul = document.getElementById('modal-judul');
  const teks = document.getElementById('modal-teks');
  const link = document.getElementById('modal-link');
  const overlay = document.getElementById('modal-overlay');
  const modalBox = document.getElementById('modal-box');
  const btnCopy = document.getElementById('modal-btn-copy');

  if (pill) {
    if (item.pillLabel) {
      pill.textContent = item.pillLabel;
      pill.className = 'px-2.5 py-0.5 rounded-lg font-mono text-xs font-semibold ' + item.pillClass;
      pill.style.display = 'inline-block';
    } else {
      pill.textContent = '';
      pill.className = '';
      pill.style.display = 'none';
    }
  }
  if (sumber) sumber.textContent = item.sumber;
  if (judul) judul.textContent = item.judul;
  if (teks) teks.textContent = item.teksLengkap;
  if (link) {
    const safeLink = (item.link && item.link !== '#') ? item.link : '';
    if (safeLink) {
      link.href = safeLink;
      link.style.display = 'inline-flex';
    } else {
      link.style.display = 'none';
    }
  }

  if (btnCopy) {
    btnCopy.innerHTML = '<span class="material-symbols-outlined text-base" aria-hidden="true">content_copy</span><span>Salin Rangkuman</span>';
    btnCopy.disabled = false;
    btnCopy.onclick = () => salinTeksModal(item);
  }

  if (overlay && modalBox) {
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');
    overlay.setAttribute('aria-hidden', 'false');
    
    // Trigger transisi buka dengan requestAnimationFrame
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        overlay.classList.remove('opacity-0', 'pointer-events-none');
        overlay.classList.add('opacity-100', 'pointer-events-auto');

        modalBox.classList.remove('scale-95', 'opacity-0', 'translate-y-4');
        modalBox.classList.add('scale-100', 'opacity-100', 'translate-y-0');

        // Fokuskan tombol tutup untuk aksesibilitas keyboard
        const closeBtn = modalBox.querySelector('button[title]');
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
      btnCopy.innerHTML = '<span class="material-symbols-outlined text-[16px] text-emerald-600" aria-hidden="true">check</span><span class="text-emerald-700 font-bold">Tersalin ke Clipboard!</span>';
      setTimeout(() => {
        if (btnCopy) {
          btnCopy.innerHTML = '<span class="material-symbols-outlined text-[16px]" aria-hidden="true">content_copy</span><span>Salin Rangkuman</span>';
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