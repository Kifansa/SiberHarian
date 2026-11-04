import { ambilBeranda, ambilArsip, mulaiPipelineRequest, batalkanPipelineRequest, bukaStreamLog } from './api.js';
import { escapeHtml, formatWaktuScraping, tampilkanKonfirmasi } from './utils.js';
import { buatCardBerita } from './cards.js';
import { resetDataLengkap } from './modal.js';

function getEl(id) { return document.getElementById(id); }

let sumberAktif = null; // EventSource yang sedang berjalan
let dataBerandaTersimpan = { berita: [], waktu_terakhir_scraping: null };
let poolSemuaBerita7Hari = null;
let promiseMuatPool = null;
let queryFilterAktif = '';

function tambahBarisLog(item) {
    const consoleBody = getEl('console-body');
    if (!consoleBody) return;
    if (!consoleBody.dataset.filled) consoleBody.innerHTML = '';
    consoleBody.dataset.filled = '1';
    const waktu = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const warnaTeks = item.level === 'ERROR' ? 'text-red-400' : item.level === 'WARNING' ? 'text-amber-400' : 'text-slate-300';
    const baris = document.createElement('div');
    baris.className = `flex gap-2 opacity-0 translate-y-1 transition-all duration-300 log-line level-${item.level || 'INFO'}`;
    baris.innerHTML = `<span class="text-[#7d8ca6] font-mono">[${waktu}]</span> <span class="${warnaTeks} font-mono">${escapeHtml(item.message)}</span>`;
    
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

/**
 * Memuat dan meng-cache pool artikel dari seluruh 7 hari terakhir.
 * Memastikan berita lama dapat dicari dan dimunculkan di feed Beranda saat kata kunci dipilih.
 */
export async function muatPoolSemuaBerita() {
    if (poolSemuaBerita7Hari && poolSemuaBerita7Hari.length > 0) {
        return poolSemuaBerita7Hari;
    }
    if (promiseMuatPool) {
        return await promiseMuatPool;
    }
    promiseMuatPool = (async () => {
        try {
            const dataArsip = await ambilArsip();
            const beritaList = [];
            const seen = new Set();

            // 1. Masukkan berita tanggal terbaru dari Beranda
            if (dataBerandaTersimpan && Array.isArray(dataBerandaTersimpan.berita)) {
                for (const b of dataBerandaTersimpan.berita) {
                    if (b.kategori === 'analisis_relevan' || b.kategori === 'edukasi') continue;
                    const key = (b.link || b.judul || '').trim().toLowerCase();
                    if (key && !seen.has(key)) {
                        seen.add(key);
                        beritaList.push(b);
                    }
                }
            }

            // 2. Gabungkan berita dari seluruh hari dalam arsip (7 hari terakhir)
            if (dataArsip && dataArsip.status === 'ok' && Array.isArray(dataArsip.hari)) {
                for (const h of dataArsip.hari) {
                    if (Array.isArray(h.berita)) {
                        for (const b of h.berita) {
                            if (b.kategori === 'analisis_relevan' || b.kategori === 'edukasi') continue;
                            const key = (b.link || b.judul || '').trim().toLowerCase();
                            if (key && !seen.has(key)) {
                                seen.add(key);
                                beritaList.push({
                                    ...b,
                                    tanggal: b.tanggal || h.tanggal
                                });
                            }
                        }
                    }
                }
            }

            poolSemuaBerita7Hari = beritaList;
            return poolSemuaBerita7Hari;
        } catch (err) {
            console.error('Gagal memuat pool berita 7 hari:', err);
            return (dataBerandaTersimpan && dataBerandaTersimpan.berita) || [];
        } finally {
            promiseMuatPool = null;
        }
    })();

    return await promiseMuatPool;
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
            <div class="text-center py-12 card-cyber border-[#ff3366]/40 p-6 my-4 shadow-[0_0_20px_rgba(255,51,102,0.15)]">
                <span class="material-symbols-outlined text-3xl text-[#ff3366] mb-2 drop-shadow-[0_0_10px_rgba(255,51,102,0.4)]" aria-hidden="true">cloud_off</span>
                <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] mb-1">[ GAGAL MENGHUBUNGI SERVER CTI ]</h3>
                <p class="text-xs text-[#8892b0] mb-4 max-w-md mx-auto font-mono">Tidak dapat memuat ringkasan insiden terbaru (${escapeHtml(data.message || 'Koneksi terputus')}). Pastikan server backend aktif.</p>
                <button onclick="window.tampilkanBeranda()" class="btn-chamfer text-xs" style="height:36px;padding:0 18px;">
                    <span class="material-symbols-outlined text-sm" aria-hidden="true">refresh</span>
                    <span>[ COBA MUAT ULANG ]</span>
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
    dataBerandaTersimpan = {
        berita,
        waktu_terakhir_scraping: data.waktu_terakhir_scraping
    };
    // Saring hanya berita intelijen siber aktual (edukasi disajikan khusus pada Edukasi Keamanan Siber)
    const daftarBerita = berita.filter(b => b.kategori !== 'analisis_relevan' && b.kategori !== 'edukasi');
    
    if (resultsDesc) {
        const infoWaktu = data.waktu_terakhir_scraping ? `Diperbarui pada ${formatWaktuScraping(data.waktu_terakhir_scraping)}` : 'Pantauan intelijen terkini';
        resultsDesc.textContent = `${daftarBerita.length} Berita Terpantau • ${infoWaktu}`;
    }

    const filterBadge = getEl('beranda-filter-badge');
    if (filterBadge) filterBadge.classList.add('hidden');

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

    // Prefetch pool arsip 7 hari di latar belakang agar filtering instan
    setTimeout(() => {
        muatPoolSemuaBerita().catch(() => {});
    }, 120);
}

export async function filterBerandaCards(query = null) {
    if (query !== null) queryFilterAktif = (query || '').trim().toLowerCase();

    const cardContainer = getEl('card-container');
    const resultsDesc = getEl('results-desc');
    const filterBadge = getEl('beranda-filter-badge');
    const filterBadgeText = getEl('beranda-filter-badge-text');
    const clearBtn = getEl('beranda-search-clear');
    const emptyState = getEl('empty-state');

    if (!cardContainer) return;

    if (clearBtn) {
        clearBtn.style.display = queryFilterAktif ? 'flex' : 'none';
    }

    // KASUS 1: Query kosong (Kondisi default Beranda harian)
    if (!queryFilterAktif) {
        if (filterBadge) filterBadge.classList.add('hidden');
        const defaultBerita = (dataBerandaTersimpan.berita || []).filter(
            b => b.kategori !== 'analisis_relevan' && b.kategori !== 'edukasi'
        );

        if (resultsDesc) {
            const infoWaktu = dataBerandaTersimpan.waktu_terakhir_scraping
                ? `Diperbarui pada ${formatWaktuScraping(dataBerandaTersimpan.waktu_terakhir_scraping)}`
                : 'Pantauan intelijen terkini';
            resultsDesc.textContent = `${defaultBerita.length} Berita Terpantau • ${infoWaktu}`;
        }

        if (defaultBerita.length === 0) {
            if (emptyState) emptyState.style.display = 'block';
            cardContainer.innerHTML = '';
        } else {
            if (emptyState) emptyState.style.display = 'none';
            cardContainer.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="beranda-cards-grid">
                    ${defaultBerita.map(buatCardBerita).join('')}
                </div>
            `;
        }
        return;
    }

    // KASUS 2: Query aktif (mencari ke seluruh pool 7 hari termasuk berita lama)
    if (emptyState) emptyState.style.display = 'none';

    if (!poolSemuaBerita7Hari && resultsDesc) {
        resultsDesc.textContent = `Menyaring arsip insiden: "${queryFilterAktif}"...`;
    }

    const pool = await muatPoolSemuaBerita();
    const kecocokan = pool.filter(b => {
        const teks = (
            (b.judul || '') + ' ' +
            (b.sumber || '') + ' ' +
            (b.ringkasan || '') + ' ' +
            (b.kategori || '') + ' ' +
            (b.kata_kunci || '') + ' ' +
            (b.tanggal || '')
        ).toLowerCase();
        return teks.includes(queryFilterAktif);
    });

    if (filterBadge && filterBadgeText) {
        filterBadgeText.textContent = `TAG: ${queryFilterAktif.toUpperCase()} (${kecocokan.length})`;
        filterBadge.classList.remove('hidden');
    }

    if (resultsDesc) {
        resultsDesc.textContent = `${kecocokan.length} Berita Ditemukan • Menyaring: "${queryFilterAktif}"`;
    }

    if (kecocokan.length === 0) {
        cardContainer.innerHTML = `
            <div class="text-center py-12 card-cyber p-6 mt-4 w-full" id="search-empty-notice">
                <span class="material-symbols-outlined text-3xl text-[#00d4ff] mb-2 drop-shadow-[0_0_10px_rgba(0,212,255,0.4)]" aria-hidden="true">search_off</span>
                <h4 class="text-base font-bold text-[#e0f0ff] font-['Sora'] mb-1">[ TIDAK ADA HASIL PENCARIAN ]</h4>
                <p class="text-xs text-[#8892b0] max-w-sm mx-auto mb-4 font-mono">Tidak ditemukan artikel berita siber yang cocok dengan kata kunci "${escapeHtml(queryFilterAktif)}".</p>
                <button type="button" onclick="window.resetFilterBeranda && window.resetFilterBeranda()" class="btn-chamfer text-xs" style="height:36px;padding:0 16px;">
                    <span class="material-symbols-outlined text-sm" aria-hidden="true">refresh</span>
                    <span>[ RESET PENCARIAN ]</span>
                </button>
            </div>
        `;
    } else {
        cardContainer.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="beranda-cards-grid">
                ${kecocokan.map(buatCardBerita).join('')}
            </div>
        `;
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
            if (window.resetFilterWordCloud) {
                window.resetFilterWordCloud();
            }
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
    const konfirmasi = await tampilkanKonfirmasi({
        judul: 'Jalankan Pipeline Intelijen',
        pesan: 'Jalankan pipeline pengumpulan intelijen siber sekarang?',
        subteks: 'Proses ini akan mengambil feed berita RSS intelijen siber, menganalisis sektor sasaran, dan memperbarui tren ancaman.',
        teksKonfirmasi: 'Mulai Pipeline',
        teksBatal: 'Batal',
        tipe: 'info'
    });
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
                    poolSemuaBerita7Hari = null; // Invalidate cache pool saat ada data baru
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
