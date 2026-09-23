import { bukaModal, tutupModal, tutupModalJikaLuar, salinTeksModal } from './modal.js';
import { tampilkanBeranda, mulaiPipeline, batalkanPipeline, filterBerandaCards } from './beranda.js';
import { muatTabArsip, muatUlangTabArsip, filterArsipCards } from './arsip.js';
import { muatTabTren, muatUlangTabTren, eksporLaporanTren } from './tren.js';
import { muatTabStatistikPublik } from './statistik-publik.js';
import { debounce } from './utils.js';


// Expose handlers ke window untuk Alpine.js & atribut onclick
window.bukaModal = bukaModal;
window.tutupModal = tutupModal;
window.tutupModalJikaLuar = tutupModalJikaLuar;
window.salinTeksModal = salinTeksModal;
window.mulaiPipeline = mulaiPipeline;
window.batalkanPipeline = batalkanPipeline;
window.muatTabArsip = muatTabArsip;
window.muatTabTren = muatTabTren;
window.muatUlangTabTren = muatUlangTabTren;
window.eksporLaporanTren = eksporLaporanTren;
window.muatTabStatistikPublik = muatTabStatistikPublik;
window.tampilkanBeranda = tampilkanBeranda;

// Invalidate cache saat pipeline selesai jalan
window.addEventListener('pipeline-selesai', () => {
    muatUlangTabArsip();
    muatUlangTabTren();
});

// Setup Global Live Search & Keyboard Shortcuts
function inisialisasiPencarianDanShortcut() {
    const searchInput = document.getElementById('global-search-input');
    const searchClear = document.getElementById('global-search-clear');

    if (searchInput) {
        const executeFilter = debounce((val) => {
            filterBerandaCards(val);
            filterArsipCards(val);
        }, 120);

        searchInput.addEventListener('input', (e) => {
            const val = e.target.value;
            if (searchClear) {
                searchClear.style.display = val ? 'flex' : 'none';
            }
            executeFilter(val);
        });

        if (searchClear) {
            searchClear.addEventListener('click', () => {
                searchInput.value = '';
                searchClear.style.display = 'none';
                filterBerandaCards('');
                filterArsipCards('');
                searchInput.focus();
            });
        }
    }

    // Keyboard Shortcuts: 1, 2, 3 untuk switch tab & / untuk fokus search
    window.addEventListener('keydown', (e) => {
        const isInputFocused = document.activeElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName);

        if (e.key === '/' && !isInputFocused) {
            const arsipSearch = document.getElementById('arsip-search-input');
            if (arsipSearch && arsipSearch.offsetParent !== null) {
                e.preventDefault();
                arsipSearch.focus();
                arsipSearch.select();
            }
            return;
        }

        if (e.key === 'Escape' && isInputFocused) {
            const arsipSearch = document.getElementById('arsip-search-input');
            if (arsipSearch && document.activeElement === arsipSearch) {
                arsipSearch.value = '';
                const arsipClear = document.getElementById('arsip-search-clear');
                if (arsipClear) arsipClear.style.display = 'none';
                filterArsipCards('');
                arsipSearch.blur();
            }
            return;
        }

        // Tab Switching via Angka 1, 2, 3 (hanya saat tidak mengetik di form)
        if (!isInputFocused && !e.ctrlKey && !e.metaKey && !e.altKey) {
            const bodyAlpine = document.body._x_dataStack ? document.body._x_dataStack[0] : null;
            if (bodyAlpine) {
                if (e.key === '1') {
                    bodyAlpine.tabAktif = 'beranda';
                } else if (e.key === '2') {
                    bodyAlpine.tabAktif = 'arsip';
                    muatTabArsip();
                } else if (e.key === '3') {
                    bodyAlpine.tabAktif = 'tren';
                    muatTabTren();
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