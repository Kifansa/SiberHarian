import { bukaModal, tutupModal, tutupModalJikaLuar } from './modal.js';
import { tampilkanBeranda, mulaiPipeline, batalkanPipeline } from './beranda.js';
import { muatTabArsip, muatUlangTabArsip } from './arsip.js';
import { muatTabTren, muatUlangTabTren } from './tren.js';

// Fungsi-fungsi ini dipanggil lewat atribut onclick="" / Alpine @click di
// HTML (baik markup statis maupun yang di-generate lewat template string di
// cards.js). Karena pakai ES module, fungsi TIDAK otomatis jadi global -
// jadi ditempel manual ke window supaya tetap bisa dipanggil dari HTML.
window.bukaModal = bukaModal;
window.tutupModal = tutupModal;
window.tutupModalJikaLuar = tutupModalJikaLuar;
window.mulaiPipeline = mulaiPipeline;
window.batalkanPipeline = batalkanPipeline;
window.muatTabArsip = muatTabArsip;
window.muatTabTren = muatTabTren;

// Saat pipeline selesai jalan, cache tab Arsip & Tren (kalau sudah sempat
// dimuat sebelumnya) di-invalidate supaya kekinian data sinkron dengan
// hasil run terbaru.
window.addEventListener('pipeline-selesai', () => {
    muatUlangTabArsip();
    muatUlangTabTren();
});

window.addEventListener('DOMContentLoaded', () => {
    tampilkanBeranda();
});