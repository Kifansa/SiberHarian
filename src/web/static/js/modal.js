/**
 * State & kontrol modal "Selengkapnya" dengan animasi transisi & frosted glass blur.
 */
export const dataLengkap = [];

export function resetDataLengkap() {
  dataLengkap.length = 0;
}

let timeoutTutup = null;

export function bukaModal(idx) {
  const item = dataLengkap[idx];
  if (!item) return;

  if (timeoutTutup) {
    clearTimeout(timeoutTutup);
    timeoutTutup = null;
  }

  const pill = document.getElementById('modal-pill');
  const sumber = document.getElementById('modal-sumber');
  const judul = document.getElementById('modal-judul');
  const teks = document.getElementById('modal-teks');
  const link = document.getElementById('modal-link');
  const overlay = document.getElementById('modal-overlay');
  const modalBox = document.getElementById('modal-box');

  if (pill) {
    pill.textContent = item.pillLabel;
    pill.className = 'px-2.5 py-0.5 rounded-md font-mono text-xs font-semibold ' + item.pillClass;
  }
  if (sumber) sumber.textContent = item.sumber;
  if (judul) judul.textContent = item.judul;
  if (teks) teks.textContent = item.teksLengkap;
  if (link) link.href = item.link;

  if (overlay && modalBox) {
    overlay.classList.remove('hidden');
    overlay.classList.add('flex');
    
    // Trigger transisi buka dengan requestAnimationFrame
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        overlay.classList.remove('opacity-0', 'pointer-events-none');
        overlay.classList.add('opacity-100', 'pointer-events-auto');

        modalBox.classList.remove('scale-95', 'opacity-0', 'translate-y-4');
        modalBox.classList.add('scale-100', 'opacity-100', 'translate-y-0');
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

  modalBox.classList.remove('scale-100', 'opacity-100', 'translate-y-0');
  modalBox.classList.add('scale-95', 'opacity-0', 'translate-y-4');

  document.body.classList.remove('overflow-hidden');

  if (timeoutTutup) clearTimeout(timeoutTutup);
  timeoutTutup = setTimeout(() => {
    overlay.classList.add('hidden');
    overlay.classList.remove('flex');
  }, 250);
}

export function tutupModalJikaLuar(event) {
  if (event.target.id === 'modal-overlay') {
    tutupModal();
  }
}

// Support tombol ESC untuk menutup modal
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    const overlay = document.getElementById('modal-overlay');
    if (overlay && !overlay.classList.contains('hidden')) {
      tutupModal();
    }
  }
});