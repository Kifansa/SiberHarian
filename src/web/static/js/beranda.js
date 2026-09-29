import { ambilBeranda, mulaiPipelineRequest, batalkanPipelineRequest, bukaStreamLog } from './api.js';
import { escapeHtml, formatWaktuScraping } from './utils.js';
import { buatCardBerita } from './cards.js';
import { resetDataLengkap } from './modal.js';

function getEl(id) { return document.getElementById(id); }

let sumberAktif = null; // EventSource yang sedang berjalan
let dataBerandaTersimpan = { berita: [] };


function tambahBarisLog(item) {
    const consoleBody = getEl('console-body');
    if (!consoleBody) return;
    if (!consoleBody.dataset.filled) consoleBody.innerHTML = '';
    consoleBody.dataset.filled = '1';
    const waktu = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const warnaTeks = item.level === 'ERROR' ? 'text-red-400' : item.level === 'WARNING' ? 'text-amber-400' : 'text-slate-300';
    const baris = document.createElement('div');
    baris.className = `flex gap-2 opacity-0 translate-y-1 transition-all duration-300 log-line level-${item.level || 'INFO'}`;
    baris.innerHTML = `<span class="text-[#49769F] font-mono">[${waktu}]</span><span class="${warnaTeks} font-mono">${escapeHtml(item.message)}</span>`;
    
    // Cek apakah posisi scroll saat ini berada di dekat dasar (jarak <= 45px)
    const isNearBottom = (consoleBody.scrollHeight - consoleBody.scrollTop - consoleBody.clientHeight) <= 45;
    
    consoleBody.appendChild(baris);
    
    if (isNearBottom) {
        consoleBody.scrollTop = consoleBody.scrollHeight;
    }
    setTimeout(() => baris.classList.remove('opacity-0', 'translate-y-1'), 30);
}

function resetTombol() {
    const btnRun = getEl('btn-run');
    const btnCancel = getEl('btn-cancel');
    if (btnRun) {
        btnRun.disabled = false;
        btnRun.style.display = '';
    }
    if (btnCancel) {
        btnCancel.classList.remove('visible');
    }
}

export async function tampilkanBeranda() {
    const data = await ambilBeranda();
    resetDataLengkap();

    const resultsDesc = getEl('results-desc');
    const emptyState = getEl('empty-state');
    const cardContainer = getEl('card-container');

    if (!cardContainer) return;

    if (data.status === 'error') {
        if (resultsDesc) resultsDesc.textContent = 'Gagal memuat data intelijen';
        if (emptyState) emptyState.style.display = 'none';
        cardContainer.innerHTML = `
            <div class="text-center py-12 bg-red-50/70 rounded-xl border border-red-200 p-6 shadow-card my-4">
                <span class="material-symbols-outlined text-3xl text-red-600 mb-2" aria-hidden="true">cloud_off</span>
                <h3 class="text-base font-bold text-[#001D39] mb-1">Gagal Menghubungi Server CTI</h3>
                <p class="text-xs text-[#49769F] mb-4 max-w-md mx-auto">Tidak dapat memuat ringkasan insiden terbaru (${escapeHtml(data.message || 'Koneksi terputus')}). Pastikan server backend aktif.</p>
                <button onclick="window.tampilkanBeranda()" class="px-4 py-2 bg-white hover:bg-[#EEF5FA] text-[#0A4174] hover:text-[#001D39] font-bold text-xs rounded-xl border border-[#BDD8E9] shadow-2xs transition-all duration-200 cursor-pointer inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none">
                    <span class="material-symbols-outlined text-base text-[#49769F]" aria-hidden="true">refresh</span> Coba Muat Ulang
                </button>
            </div>`;
        return;
    }

    if (data.status !== 'ok') {
        if (resultsDesc) resultsDesc.textContent = 'Belum ada riwayat pembaruan';
        if (emptyState) {
            emptyState.style.display = 'block';
            const h3 = emptyState.querySelector('h3');
            if (h3) h3.textContent = 'Belum ada data intelijen';
            const p = emptyState.querySelector('p');
            if (p) p.textContent = 'Jalankan pipeline untuk mengisi data pertama kali.';
        }
        cardContainer.innerHTML = '';
        return;
    }

    const berita = data.berita || [];
    dataBerandaTersimpan = { berita };
    // Saring hanya berita intelijen siber aktual (edukasi disajikan khusus pada Edukasi Keamanan Siber)
    const daftarBerita = berita.filter(b => b.kategori !== 'analisis_relevan' && b.kategori !== 'edukasi');
    
    if (resultsDesc) {
        const infoWaktu = data.waktu_terakhir_scraping ? `Diperbarui pada ${formatWaktuScraping(data.waktu_terakhir_scraping)}` : 'Pantauan intelijen terkini';
        resultsDesc.textContent = `${daftarBerita.length} Berita Terpantau • ${infoWaktu}`;
    }

    if (daftarBerita.length === 0) {
        if (emptyState) {
            emptyState.style.display = 'block';
            const h3 = emptyState.querySelector('h3');
            if (h3) h3.textContent = 'Tidak ada berita pada tanggal terbaru';
            const p = emptyState.querySelector('p');
            if (p) p.textContent = 'Tidak ditemukan berita siber pada tanggal ini.';
        }
        cardContainer.innerHTML = '';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';
    cardContainer.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="beranda-cards-grid">
            ${daftarBerita.map(buatCardBerita).join('')}
        </div>
    `;

    inisialisasiFilterBerandaToolbar();
}

let queryFilterAktif = '';

export function filterBerandaCards(query = null) {
    if (query !== null) queryFilterAktif = (query || '').trim().toLowerCase();

    const cardContainer = getEl('card-container');
    if (!cardContainer) return;
    const cards = cardContainer.querySelectorAll('article[data-search-text]');
    let totalVisible = 0;

    cards.forEach(card => {
        const text = card.getAttribute('data-search-text') || '';
        if (!queryFilterAktif || text.includes(queryFilterAktif)) {
            card.style.display = 'flex';
            totalVisible++;
        } else {
            card.style.display = 'none';
        }
    });

    // Toggle clear search button
    const clearBtn = getEl('beranda-search-clear');
    if (clearBtn) {
        clearBtn.style.display = queryFilterAktif ? 'flex' : 'none';
    }

    let searchEmptyNotice = document.getElementById('search-empty-notice');
    if (totalVisible === 0) {
        if (!searchEmptyNotice) {
            searchEmptyNotice = document.createElement('div');
            searchEmptyNotice.id = 'search-empty-notice';
            searchEmptyNotice.className = 'text-center py-12 bg-white rounded-xl border border-[#E2EDF8] p-6 shadow-card';
            cardContainer.appendChild(searchEmptyNotice);
        }
        searchEmptyNotice.style.display = 'block';
        searchEmptyNotice.innerHTML = `
            <span class="material-symbols-outlined text-3xl text-[#49769F] mb-2" aria-hidden="true">search_off</span>
            <h4 class="text-base font-bold text-[#001D39] mb-1">Tidak Ada Hasil Pencarian</h4>
            <p class="text-xs text-[#49769F] max-w-sm mx-auto mb-3">Tidak ditemukan artikel berita siber yang cocok dengan kata kunci pencarian.</p>
            <button type="button" onclick="window.resetFilterBeranda && window.resetFilterBeranda()" class="px-4 py-2 bg-[#EEF5FA] hover:bg-[#BDD8E9] text-[#0A4174] font-bold text-xs rounded-xl border border-[#BDD8E9] transition-all cursor-pointer inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-[#0A4174]">
                <span class="material-symbols-outlined text-sm" aria-hidden="true">refresh</span>
                <span>Reset Pencarian</span>
            </button>
        `;
    } else if (searchEmptyNotice) {
        searchEmptyNotice.style.display = 'none';
    }
}

function inisialisasiFilterBerandaToolbar() {
    const searchInput = getEl('beranda-search-input');
    const searchClear = getEl('beranda-search-clear');

    if (searchInput && !searchInput.dataset.initialized) {
        searchInput.dataset.initialized = '1';
        searchInput.addEventListener('input', (e) => {
            filterBerandaCards(e.target.value);
        });
    }

    if (searchClear && !searchClear.dataset.initialized) {
        searchClear.dataset.initialized = '1';
        searchClear.addEventListener('click', () => {
            if (searchInput) {
                searchInput.value = '';
                searchInput.focus();
            }
            filterBerandaCards('');
        });
    }
}

window.resetFilterBeranda = function() {
    queryFilterAktif = '';
    const input = getEl('beranda-search-input');
    if (input) input.value = '';
    const clearBtn = getEl('beranda-search-clear');
    if (clearBtn) clearBtn.style.display = 'none';

    filterBerandaCards('');
    if (window.resetFilterWordCloud) {
        window.resetFilterWordCloud();
    }
};

export async function mulaiPipeline() {
    const konfirmasi = window.confirm(
        'Jalankan pipeline pengumpulan intelijen siber sekarang?\n\n' +
        'Proses ini akan mengambil feed berita RSS intelijen siber, menganalisis sektor sasaran, dan memperbarui tren ancaman.'
    );
    if (!konfirmasi) return;

    const btnRun = getEl('btn-run');
    const btnCancel = getEl('btn-cancel');
    const consoleStatus = getEl('console-status');
    const cardContainer = getEl('card-container');
    const emptyState = getEl('empty-state');
    const consoleBody = getEl('console-body');

    if (btnRun) btnRun.style.display = 'none';
    if (btnCancel) btnCancel.classList.add('visible');
    if (consoleStatus) consoleStatus.textContent = '[pipeline berjalan]';
    if (cardContainer) cardContainer.innerHTML = '';
    if (emptyState) emptyState.style.display = 'none';
    if (consoleBody) {
        consoleBody.innerHTML = '';
        consoleBody.dataset.filled = '';
    }

    const data = await mulaiPipelineRequest();
    if (data.status === 'sudah_berjalan') {
        tambahBarisLog({ level: 'WARNING', message: 'Pipeline sudah berjalan, tunggu sampai selesai.' });
        return;
    } else if (data.status === 'error') {
        tambahBarisLog({ level: 'ERROR', message: `Gagal memulai pipeline: ${data.message || 'Server error'}` });
        resetTombol();
        if (consoleStatus) consoleStatus.textContent = '[error]';
        return;
    }

    sumberAktif = bukaStreamLog(
        async (item) => {
            if (item.type === 'log') {
                tambahBarisLog(item);
            } else if (item.type === 'selesai') {
                sumberAktif.close();
                sumberAktif = null;
                resetTombol();
                if (consoleStatus) consoleStatus.textContent = item.sukses ? '[selesai]' : '[gagal, cek log di atas]';
                if (item.sukses) {
                    await tampilkanBeranda();
                    window.dispatchEvent(new CustomEvent('pipeline-selesai'));
                }
            }
        },
        () => {
            if (sumberAktif) {
                sumberAktif.close();
                sumberAktif = null;
            }
            resetTombol();
            const consoleStatus = getEl('console-status');
            if (consoleStatus) consoleStatus.textContent = '[koneksi terputus]';
            tambahBarisLog({ level: 'WARNING', message: 'Koneksi log stream ke server terputus.' });
        }
    );
}

export async function batalkanPipeline() {
    tambahBarisLog({ level: 'WARNING', message: 'Membatalkan pipeline…' });
    try {
        await batalkanPipelineRequest();
    } catch (e) {
        // biarkan, tetap hentikan koneksi di sisi klien
    }
    if (sumberAktif) {
        sumberAktif.close();
        sumberAktif = null;
    }
    const consoleStatus = getEl('console-status');
    if (consoleStatus) consoleStatus.textContent = '[dibatalkan]';
    resetTombol();
}