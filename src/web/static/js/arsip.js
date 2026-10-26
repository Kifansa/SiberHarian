import { ambilArsip } from './api.js';
import { formatTanggalIndonesia, escapeHtml } from './utils.js';
import { buatCardBerita } from './cards.js';
import { resetDataLengkap } from './modal.js';
import { debounce } from './utils.js';

const tanggalSelect = document.getElementById('arsip-tanggal-select');
const searchInput = document.getElementById('arsip-search-input');
const searchClear = document.getElementById('arsip-search-clear');
const cardContainer = document.getElementById('arsip-card-container');
const emptyState = document.getElementById('arsip-empty-state');
const arsipDesc = document.getElementById('arsip-desc');

let daftarHari = [];      
let tanggalTerpilih = 'semua'; // Default to "semua" as requested
let sudahDimuat = false;  


function renderDropdownTanggal() {
    if (!tanggalSelect) return;
    
    let totalBerita = 0;
    daftarHari.forEach(h => {
        totalBerita += (h.berita || []).length;
    });
    
    let optionsHtml = `<option value="semua" ${tanggalTerpilih === 'semua' ? 'selected' : ''}>[ SEMUA TANGGAL (7 HARI) - ${totalBerita} BERITA ]</option>`;
    
    optionsHtml += daftarHari.map(hari => {
        const jumlahTotal = (hari.berita || []).length;
        const selected = hari.tanggal === tanggalTerpilih ? 'selected' : '';
        return `<option value="${hari.tanggal}" ${selected}>${formatTanggalIndonesia(hari.tanggal)} (${jumlahTotal} Berita)</option>`;
    }).join('');
    
    tanggalSelect.innerHTML = optionsHtml;
}

function renderCardUntukTanggalTerpilih() {
    resetDataLengkap();
    
    let daftarBerita = [];
    
    if (tanggalTerpilih === 'semua') {
        daftarHari.forEach(h => {
            const bList = h.berita || [];
            daftarBerita.push(...bList.filter(b => b.kategori !== 'analisis_relevan' && b.kategori !== 'edukasi'));
        });
    } else {
        const hari = daftarHari.find(h => h.tanggal === tanggalTerpilih);
        if (hari) {
            const bList = hari.berita || [];
            daftarBerita = bList.filter(b => b.kategori !== 'analisis_relevan' && b.kategori !== 'edukasi');
        }
    }
    
    if (daftarBerita.length === 0) {
        cardContainer.innerHTML = `
            <div class="text-center py-12 card-cyber p-6 mt-4">
                <span class="material-symbols-outlined text-3xl text-[#00d4ff] mb-2 drop-shadow-[0_0_10px_rgba(0,212,255,0.4)]" aria-hidden="true">folder_off</span>
                <h4 class="text-base font-bold text-[#e0f0ff] font-['Sora'] mb-1">[ DATA ARSIP TIDAK DITEMUKAN ]</h4>
                <p class="text-xs text-[#7d8ca6] font-mono">Tidak ada data arsip berita siber untuk pilihan rentang tanggal ini.</p>
            </div>
        `;
        return;
    }
    
    cardContainer.innerHTML = `
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5" id="arsip-cards-grid">
            ${daftarBerita.map(buatCardBerita).join('')}
        </div>
    `;
    
    if (searchInput && searchInput.value) {
        filterArsipCards(searchInput.value);
    }
}

export function filterArsipCards(query) {
    const q = (query || '').trim().toLowerCase();
    const cards = cardContainer.querySelectorAll('article[data-search-text]');
    let totalVisible = 0;

    cards.forEach(card => {
        const text = card.getAttribute('data-search-text') || '';
        if (!q || text.includes(q)) {
            card.style.display = 'flex';
            totalVisible++;
        } else {
            card.style.display = 'none';
        }
    });

    let searchEmptyNotice = document.getElementById('arsip-search-empty-notice');
    if (totalVisible === 0 && q) {
        if (!searchEmptyNotice) {
            searchEmptyNotice = document.createElement('div');
            searchEmptyNotice.id = 'arsip-search-empty-notice';
            searchEmptyNotice.className = 'text-center py-12 card-cyber p-6 mt-6';
            searchEmptyNotice.innerHTML = `
                <span class="material-symbols-outlined text-3xl text-[#00d4ff] mb-2 drop-shadow-[0_0_10px_rgba(0,212,255,0.4)]" aria-hidden="true">search_off</span>
                <h4 class="text-base font-bold text-[#e0f0ff] font-['Sora'] mb-1">[ TIDAK ADA HASIL PENCARIAN ARSIP ]</h4>
                <p class="text-xs text-[#7d8ca6] font-mono">Tidak ada hasil yang cocok dengan "<strong class="text-[#00d4ff]">${escapeHtml(q)}</strong>".</p>
            `;
            cardContainer.appendChild(searchEmptyNotice);
        } else {
            searchEmptyNotice.style.display = 'block';
            const strongEl = searchEmptyNotice.querySelector('strong');
            if (strongEl) strongEl.textContent = q;
        }
    } else if (searchEmptyNotice) {
        searchEmptyNotice.style.display = 'none';
    }
}

if (tanggalSelect) {
    tanggalSelect.addEventListener('change', (e) => {
        tanggalTerpilih = e.target.value;
        renderCardUntukTanggalTerpilih();
    });
}

if (searchInput) {
    const executeFilter = debounce((val) => {
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
            filterArsipCards('');
            searchInput.focus();
        });
    }
}

export async function muatTabArsip() {
    if (sudahDimuat) return;
    const data = await ambilArsip();

    if (data.status === 'error') {
        emptyState.classList.add('hidden');
        cardContainer.innerHTML = `
            <div class="text-center py-12 card-cyber border-[#ff3366]/40 p-6 my-4 shadow-[0_0_20px_rgba(255,51,102,0.2)]">
                <span class="material-symbols-outlined text-3xl text-[#ff3366] mb-2 drop-shadow-[0_0_10px_rgba(255,51,102,0.4)]" aria-hidden="true">cloud_off</span>
                <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] mb-1">Gagal Memuat Data Arsip</h3>
                <p class="text-xs text-[#7d8ca6] mb-4 max-w-md mx-auto font-sans">Terjadi kendala saat mengambil riwayat arsip (${escapeHtml(data.message || 'Koneksi terputus')}).</p>
                <button onclick="window.muatUlangTabArsip()" class="btn-chamfer text-xs" style="height:36px;padding:0 18px;">
                    <span class="material-symbols-outlined text-sm text-[#00d4ff]" aria-hidden="true">refresh</span>
                    <span>[ COBA MUAT ULANG → ]</span>
                </button>
            </div>`;
        arsipDesc.textContent = 'Gagal memuat data arsip.';
        return;
    }

    daftarHari = data.hari || [];
    sudahDimuat = true;

    if (daftarHari.length === 0) {
        emptyState.classList.remove('hidden');
        cardContainer.innerHTML = '';
        arsipDesc.textContent = 'Belum ada data arsip.';
        return;
    }
    emptyState.classList.add('hidden');
    arsipDesc.textContent = `Menampilkan ${daftarHari.length} hari terakhir.`;
    // Default to "semua"
    tanggalTerpilih = 'semua';
    renderDropdownTanggal();
    renderCardUntukTanggalTerpilih();
}

export function muatUlangTabArsip() {
    sudahDimuat = false;
    return muatTabArsip();
}