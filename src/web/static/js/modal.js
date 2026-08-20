/**
 * State & kontrol modal "Selengkapnya" - dipakai bareng oleh card berita
 * & card CVE, baik di tab Beranda maupun Arsip.
 */
export const dataLengkap = [];

export function resetDataLengkap() {
  dataLengkap.length = 0;
}

export function bukaModal(idx) {
  const item = dataLengkap[idx];
  if (!item) return;
  document.getElementById('modal-pill').textContent = item.pillLabel;
  document.getElementById('modal-pill').className = 'px-2 py-0.5 rounded font-label-sm text-label-sm ' + item.pillClass;
  document.getElementById('modal-sumber').textContent = item.sumber;
  document.getElementById('modal-judul').textContent = item.judul;
  document.getElementById('modal-teks').textContent = item.teksLengkap;
  document.getElementById('modal-link').href = item.link;
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.remove('hidden');
  overlay.classList.add('flex');
}

export function tutupModal() {
  const overlay = document.getElementById('modal-overlay');
  overlay.classList.add('hidden');
  overlay.classList.remove('flex');
}

export function tutupModalJikaLuar(event) {
  if (event.target.id === 'modal-overlay') tutupModal();
}