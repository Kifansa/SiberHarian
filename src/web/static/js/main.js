import { bukaModal, tutupModal, tutupModalJikaLuar, salinTeksModal } from './modal.js';
import { tampilkanBeranda, mulaiPipeline, batalkanPipeline, filterBerandaCards } from './beranda.js?v=9.9';
import { muatTabArsip, muatUlangTabArsip, filterArsipCards } from './arsip.js';
import { muatTabStatistikPublik } from './statistik-publik.js?v=9.8';
import { tampilkanToast, tampilkanKonfirmasi } from './utils.js';

// Expose handlers ke window untuk Alpine.js & atribut onclick
window.bukaModal = bukaModal;
window.tutupModal = tutupModal;
window.tutupModalJikaLuar = tutupModalJikaLuar;
window.salinTeksModal = salinTeksModal;
window.mulaiPipeline = mulaiPipeline;
window.batalkanPipeline = batalkanPipeline;
window.muatTabArsip = muatTabArsip;
window.filterArsipCards = filterArsipCards;
window.muatTabStatistikPublik = muatTabStatistikPublik;
window.tampilkanBeranda = tampilkanBeranda;
window.filterBerandaCards = filterBerandaCards;
window.tampilkanToast = tampilkanToast;
window.tampilkanKonfirmasi = tampilkanKonfirmasi;

// Invalidate cache saat pipeline selesai jalan
window.addEventListener('pipeline-selesai', () => {
    muatUlangTabArsip();
});

// Setup Keyboard Shortcuts
function inisialisasiPencarianDanShortcut() {
    window.addEventListener('keydown', (e) => {
        const isInputFocused = document.activeElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName);

        if (e.key === '/' && !isInputFocused) {
            const berandaSearch = document.getElementById('beranda-search-input');
            const arsipSearch = document.getElementById('arsip-search-input');

            // Cek tab mana yang sedang aktif dan terlihat
            if (berandaSearch && berandaSearch.offsetParent !== null) {
                e.preventDefault();
                berandaSearch.focus();
                berandaSearch.select();
                return;
            }
            if (arsipSearch && arsipSearch.offsetParent !== null) {
                e.preventDefault();
                arsipSearch.focus();
                arsipSearch.select();
                return;
            }
        }

        if (e.key === 'Escape' && isInputFocused) {
            const berandaSearch = document.getElementById('beranda-search-input');
            if (berandaSearch && document.activeElement === berandaSearch) {
                if (window.resetFilterBeranda) {
                    window.resetFilterBeranda();
                } else {
                    berandaSearch.value = '';
                }
                berandaSearch.blur();
                return;
            }

            const arsipSearch = document.getElementById('arsip-search-input');
            if (arsipSearch && document.activeElement === arsipSearch) {
                arsipSearch.value = '';
                const arsipClear = document.getElementById('arsip-search-clear');
                if (arsipClear) arsipClear.style.display = 'none';
                filterArsipCards('');
                arsipSearch.blur();
                return;
            }
        }

        // Tab Switching via Angka 1, 2 (hanya saat tidak mengetik di form)
        if (!isInputFocused && !e.ctrlKey && !e.metaKey && !e.altKey) {
            const bodyAlpine = document.body._x_dataStack ? document.body._x_dataStack[0] : null;
            if (bodyAlpine) {
                if (e.key === '1') {
                    bodyAlpine.tabAktif = 'beranda';
                } else if (e.key === '2') {
                    bodyAlpine.tabAktif = 'arsip';
                    muatTabArsip();
                }
            }
        }
    });
}

async function inisialisasiAplikasi() {
    inisialisasiPencarianDanShortcut();
    try {
        await Promise.allSettled([
            tampilkanBeranda(),
            muatTabStatistikPublik(),
        ]);
    } catch (err) {
        console.error('Error saat inisialisasi aplikasi:', err);
    } finally {
        if (window.selesaikanPreloader) {
            window.selesaikanPreloader();
        }
    }
}

if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', inisialisasiAplikasi);
} else {
    inisialisasiAplikasi();
}
