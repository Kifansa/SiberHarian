import { bukaModal, tutupModal, tutupModalJikaLuar, salinTeksModal } from './modal.js';
import { mulaiPipeline, batalkanPipeline } from './beranda.js';
import { muatTabArsip, muatUlangTabArsip, filterArsipCards } from './arsip.js';
import { muatTabTren, muatUlangTabTren } from './tren.js?v=9.2';

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

// Handler Logout Admin
window.logoutAdmin = async function() {
    try {
        await fetch('/api/auth/logout', { method: 'POST' });
    } catch (e) {
        console.error('Logout request failed:', e);
    } finally {
        window.location.href = '/';
    }
};

// Invalidate cache saat pipeline selesai jalan
window.addEventListener('pipeline-selesai', () => {
    muatUlangTabArsip();
    muatUlangTabTren();
});

// Setup Shortcuts
function inisialisasiPencarianDanShortcut() {
    window.addEventListener('keydown', (e) => {
        const isInputFocused = document.activeElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(document.activeElement.tagName);

        if (e.key === 'Escape' && isInputFocused) {
            const arsipSearch = document.getElementById('arsip-search-input');
            if (arsipSearch && document.activeElement === arsipSearch) {
                arsipSearch.value = '';
                const arsipClear = document.getElementById('arsip-search-clear');
                if (arsipClear) arsipClear.style.display = 'none';
                filterArsipCards('');
                arsipSearch.blur();
            }
        }
    });
}

async function inisialisasiAdmin() {
    inisialisasiPencarianDanShortcut();
    try {
        await muatTabTren();
    } catch (err) {
        console.error('Error saat inisialisasi data admin:', err);
    } finally {
        if (window.selesaikanPreloader) {
            window.selesaikanPreloader();
        }
    }
}

if (document.readyState === 'loading') {
    window.addEventListener('DOMContentLoaded', inisialisasiAdmin);
} else {
    inisialisasiAdmin();
}
