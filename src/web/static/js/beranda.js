import { ambilBeranda, mulaiPipelineRequest, batalkanPipelineRequest, bukaStreamLog } from './api.js';
import { escapeHtml, formatWaktuScraping } from './utils.js';
import { buatCardBerita, buatCardCve, buatSection } from './cards.js';
import { resetDataLengkap } from './modal.js';

function getEl(id) { return document.getElementById(id); }

let sumberAktif = null; // EventSource yang sedang berjalan
let dataBerandaTersimpan = { berita: [], cve: [] };


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
    const cve = data.cve || [];
    dataBerandaTersimpan = { berita, cve };
    const insiden = berita.filter(b => b.kategori === 'insiden_spesifik');
    const analisis = berita.filter(b => b.kategori !== 'insiden_spesifik');
    
    if (resultsDesc) {
        if (data.waktu_terakhir_scraping) {
            resultsDesc.textContent = `Diperbarui pada ${formatWaktuScraping(data.waktu_terakhir_scraping)}`;
        } else {
            resultsDesc.textContent = 'Belum ada riwayat pembaruan';
        }
    }

    if (berita.length === 0 && cve.length === 0) {
        if (emptyState) {
            emptyState.style.display = 'block';
            const h3 = emptyState.querySelector('h3');
            if (h3) h3.textContent = 'Tidak ada data pada tanggal terbaru';
            const p = emptyState.querySelector('p');
            if (p) p.textContent = 'Tidak ditemukan berita atau CVE CRITICAL pada tanggal ini.';
        }
        cardContainer.innerHTML = '';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';
    let html = '';
    html += buatSection('Insiden Spesifik', insiden.map(buatCardBerita).join(''), insiden.length,
        { ikon: 'local_fire_department', kelas: 'bg-[#b91c1c] text-white', kategori: 'insiden_spesifik' });
    html += buatSection('Edukasi / Evergreen', analisis.map(buatCardBerita).join(''), analisis.length,
        { ikon: 'school', kelas: 'bg-[#0A4174] text-white', kategori: 'edukasi' });
    html += buatSection('CVE Critical', cve.map(buatCardCve).join(''), cve.length,
        { ikon: 'bug_report', kelas: 'bg-[#b45309] text-white', kategori: 'cve' });
    cardContainer.innerHTML = html;

    inisialisasiFilterBerandaToolbar();
}

let kategoriFilterAktif = 'semua';
let queryFilterAktif = '';

export function filterBerandaCards(query = null, kategori = null) {
    if (query !== null) queryFilterAktif = (query || '').trim().toLowerCase();
    if (kategori !== null) kategoriFilterAktif = kategori;

    const cardContainer = getEl('card-container');
    if (!cardContainer) return;
    const sections = cardContainer.querySelectorAll('.section-wrapper');
    let totalVisible = 0;

    sections.forEach(sec => {
        const secKat = sec.getAttribute('data-kategori') || '';
        const isKatMatch = (kategoriFilterAktif === 'semua' || secKat === kategoriFilterAktif);

        if (!isKatMatch) {
            sec.style.display = 'none';
            return;
        }

        const cards = sec.querySelectorAll('article[data-search-text]');
        let countInSec = 0;
        cards.forEach(card => {
            const text = card.getAttribute('data-search-text') || '';
            if (!queryFilterAktif || text.includes(queryFilterAktif)) {
                card.style.display = 'flex';
                countInSec++;
                totalVisible++;
            } else {
                card.style.display = 'none';
            }
        });
        const badge = sec.querySelector('.count-badge');
        if (badge) badge.textContent = countInSec;
        sec.style.display = countInSec > 0 ? 'block' : 'none';
    });

    // Update Counter Badge
    const counterBadge = getEl('beranda-counter-badge');
    if (counterBadge) {
        counterBadge.textContent = `${totalVisible} Ditampilkan`;
    }

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
            <h4 class="text-base font-bold text-[#001D39] mb-1">Tidak Ada Hasil Saringan</h4>
            <p class="text-xs text-[#49769F] max-w-sm mx-auto mb-3">Tidak ditemukan artikel atau CVE yang cocok dengan kata kunci atau kategori aktif.</p>
            <button type="button" onclick="window.resetFilterBeranda && window.resetFilterBeranda()" class="px-4 py-2 bg-[#EEF5FA] hover:bg-[#BDD8E9] text-[#0A4174] font-bold text-xs rounded-xl border border-[#BDD8E9] transition-all cursor-pointer inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-[#0A4174]">
                <span class="material-symbols-outlined text-sm" aria-hidden="true">refresh</span>
                <span>Reset Saringan</span>
            </button>
        `;
    } else if (searchEmptyNotice) {
        searchEmptyNotice.style.display = 'none';
    }
}

function inisialisasiFilterBerandaToolbar() {
    const searchInput = getEl('beranda-search-input');
    const searchClear = getEl('beranda-search-clear');
    const pillsContainer = getEl('beranda-kategori-pills');

    if (searchInput && !searchInput.dataset.initialized) {
        searchInput.dataset.initialized = '1';
        searchInput.addEventListener('input', (e) => {
            filterBerandaCards(e.target.value, null);
        });
    }

    if (searchClear && !searchClear.dataset.initialized) {
        searchClear.dataset.initialized = '1';
        searchClear.addEventListener('click', () => {
            if (searchInput) {
                searchInput.value = '';
                searchInput.focus();
            }
            filterBerandaCards('', null);
        });
    }

    if (pillsContainer && !pillsContainer.dataset.initialized) {
        pillsContainer.dataset.initialized = '1';
        pillsContainer.addEventListener('click', (e) => {
            const btn = e.target.closest('.beranda-pill-filter');
            if (!btn) return;
            const kat = btn.getAttribute('data-kategori');
            
            pillsContainer.querySelectorAll('.beranda-pill-filter').forEach(p => {
                p.className = 'beranda-pill-filter px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap bg-[#EEF4F8] text-[#49769F] hover:text-[#001D39] hover:bg-[#E2EDF8]';
            });
            btn.className = 'beranda-pill-filter px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap bg-[#0A4174] text-white shadow-2xs';

            filterBerandaCards(null, kat);
        });
    }
}

window.resetFilterBeranda = function() {
    queryFilterAktif = '';
    kategoriFilterAktif = 'semua';
    const input = getEl('beranda-search-input');
    if (input) input.value = '';
    const clearBtn = getEl('beranda-search-clear');
    if (clearBtn) clearBtn.style.display = 'none';

    const pills = document.querySelectorAll('#beranda-kategori-pills .beranda-pill-filter');
    pills.forEach(p => {
        if (p.getAttribute('data-kategori') === 'semua') {
            p.className = 'beranda-pill-filter px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap bg-[#0A4174] text-white shadow-2xs';
        } else {
            p.className = 'beranda-pill-filter px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer whitespace-nowrap bg-[#EEF4F8] text-[#49769F] hover:text-[#001D39] hover:bg-[#E2EDF8]';
        }
    });

    filterBerandaCards('', 'semua');
    if (window.resetFilterWordCloud) {
        window.resetFilterWordCloud();
    }
};

export async function mulaiPipeline() {
    const konfirmasi = window.confirm(
        'Jalankan pipeline pengumpulan intelijen siber sekarang?\n\n' +
        'Proses ini akan mengambil feed berita RSS, data CVE terbaru dari NVD, dan memperbarui analisis tren.'
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