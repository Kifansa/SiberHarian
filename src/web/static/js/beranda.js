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
            <div class="text-center py-12 bg-red-50 rounded-lg border border-red-200/80 p-6 shadow-xs my-4">
                <span class="material-symbols-outlined text-3xl text-red-600 mb-2" aria-hidden="true">cloud_off</span>
                <h3 class="text-base font-bold text-[#001D39] mb-1">Gagal Menghubungi Server CTI</h3>
                <p class="text-xs text-[#49769F] mb-4 max-w-md mx-auto">Tidak dapat memuat ringkasan insiden terbaru (${escapeHtml(data.message || 'Koneksi terputus')}). Pastikan server backend aktif.</p>
                <button onclick="window.tampilkanBeranda()" class="px-4 py-2 bg-white hover:bg-[#EEF5FA] text-[#0A4174] hover:text-[#001D39] font-bold text-xs rounded-md shadow-2xs transition-all duration-200 cursor-pointer inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none">
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
        { ikon: 'local_fire_department', kelas: 'bg-[#b91c1c] text-white' });
    html += buatSection('Edukasi / Evergreen', analisis.map(buatCardBerita).join(''), analisis.length,
        { ikon: 'school', kelas: 'bg-[#0A4174] text-white' });
    html += buatSection('CVE Critical', cve.map(buatCardCve).join(''), cve.length,
        { ikon: 'bug_report', kelas: 'bg-[#b45309] text-white' });
    cardContainer.innerHTML = html;
}

export function filterBerandaCards(query) {
    const cardContainer = getEl('card-container');
    if (!cardContainer) return;
    const q = (query || '').trim().toLowerCase();
    const sections = cardContainer.querySelectorAll('.section-wrapper');
    let totalVisible = 0;

    sections.forEach(sec => {
        const cards = sec.querySelectorAll('article[data-search-text]');
        let countInSec = 0;
        cards.forEach(card => {
            const text = card.getAttribute('data-search-text') || '';
            if (!q || text.includes(q)) {
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

    let searchEmptyNotice = document.getElementById('search-empty-notice');
    if (totalVisible === 0 && q) {
        if (!searchEmptyNotice) {
            searchEmptyNotice = document.createElement('div');
            searchEmptyNotice.id = 'search-empty-notice';
            searchEmptyNotice.className = 'text-center py-12 bg-white rounded-lg border border-[#E2EDF8] p-6 shadow-xs';
            searchEmptyNotice.innerHTML = `
                <span class="material-symbols-outlined text-3xl text-[#49769F] mb-2" aria-hidden="true">search_off</span>
                <h4 class="text-base font-bold text-[#001D39] mb-1">Tidak ada hasil pencarian</h4>
                <p class="text-xs text-[#49769F]">Tidak ada artikel atau CVE yang cocok dengan kata kunci "<strong>${escapeHtml(q)}</strong>".</p>
            `;
            cardContainer.appendChild(searchEmptyNotice);
        } else {
            searchEmptyNotice.style.display = 'block';
            searchEmptyNotice.querySelector('strong').textContent = q;
        }
    } else if (searchEmptyNotice) {
        searchEmptyNotice.style.display = 'none';
    }
}

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