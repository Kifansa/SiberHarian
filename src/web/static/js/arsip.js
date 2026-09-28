import { ambilArsip } from './api.js';
import { formatTanggalIndonesia, escapeHtml } from './utils.js';
import { buatCardBerita, buatCardCve, buatSection } from './cards.js';
import { resetDataLengkap } from './modal.js';
import { debounce } from './utils.js';

const tanggalSelect = document.getElementById('arsip-tanggal-select');
const kategoriSelect = document.getElementById('arsip-kategori-select');
const searchInput = document.getElementById('arsip-search-input');
const searchClear = document.getElementById('arsip-search-clear');
const cardContainer = document.getElementById('arsip-card-container');
const emptyState = document.getElementById('arsip-empty-state');
const arsipDesc = document.getElementById('arsip-desc');

let daftarHari = [];      
let tanggalTerpilih = 'semua'; // Default to "semua" as requested
let kategoriTerpilih = 'semua';
let sudahDimuat = false;  

function renderDropdownTanggal() {
    if (!tanggalSelect) return;
    
    let totalBerita = 0;
    let totalCve = 0;
    daftarHari.forEach(h => {
        totalBerita += h.berita.length;
        totalCve += h.cve.length;
    });
    const totalAll = totalBerita + totalCve;
    
    let optionsHtml = `<option value="semua" ${tanggalTerpilih === 'semua' ? 'selected' : ''}>Semua Tanggal (7 Hari) - ${totalAll} Data</option>`;
    
    optionsHtml += daftarHari.map(hari => {
        const jumlahTotal = hari.berita.length + hari.cve.length;
        const selected = hari.tanggal === tanggalTerpilih ? 'selected' : '';
        return `<option value="${hari.tanggal}" ${selected}>${formatTanggalIndonesia(hari.tanggal)} (${jumlahTotal})</option>`;
    }).join('');
    
    tanggalSelect.innerHTML = optionsHtml;
}

function renderCardUntukTanggalTerpilih() {
    resetDataLengkap();
    
    let semuaInsiden = [];
    let semuaAnalisis = [];
    let semuaCve = [];
    
    if (tanggalTerpilih === 'semua') {
        daftarHari.forEach(h => {
            semuaInsiden.push(...h.berita.filter(b => b.kategori === 'insiden_spesifik'));
            semuaAnalisis.push(...h.berita.filter(b => b.kategori !== 'insiden_spesifik'));
            semuaCve.push(...h.cve);
        });
    } else {
        const hari = daftarHari.find(h => h.tanggal === tanggalTerpilih);
        if (hari) {
            semuaInsiden = hari.berita.filter(b => b.kategori === 'insiden_spesifik');
            semuaAnalisis = hari.berita.filter(b => b.kategori !== 'insiden_spesifik');
            semuaCve = hari.cve;
        }
    }
    
    let html = '';
    const tampilInsiden = kategoriTerpilih === 'semua' || kategoriTerpilih === 'insiden_spesifik';
    const tampilEdukasi = kategoriTerpilih === 'semua' || kategoriTerpilih === 'edukasi';
    const tampilCve = kategoriTerpilih === 'semua' || kategoriTerpilih === 'cve';
    
    if (tampilInsiden && semuaInsiden.length > 0) {
        html += buatSection('Insiden Spesifik', semuaInsiden.map(buatCardBerita).join(''), semuaInsiden.length,
            { ikon: 'local_fire_department', kelas: 'bg-[#b91c1c] text-white', kategori: 'insiden_spesifik' });
    }
    if (tampilEdukasi && semuaAnalisis.length > 0) {
        html += buatSection('Edukasi / Evergreen', semuaAnalisis.map(buatCardBerita).join(''), semuaAnalisis.length,
            { ikon: 'school', kelas: 'bg-[#0A4174] text-white', kategori: 'edukasi' });
    }
    if (tampilCve && semuaCve.length > 0) {
        html += buatSection('CVE Critical', semuaCve.map(buatCardCve).join(''), semuaCve.length,
            { ikon: 'bug_report', kelas: 'bg-[#b45309] text-white', kategori: 'cve' });
    }
    
    if (!html) {
        cardContainer.innerHTML = '<p class="text-[#49769F] py-10 text-center font-medium">Tidak ada data arsip untuk pilihan ini.</p>';
    } else {
        cardContainer.innerHTML = html;
    }
    
    if (searchInput && searchInput.value) {
        filterArsipCards(searchInput.value);
    }
}

export function filterArsipCards(query) {
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

    let searchEmptyNotice = document.getElementById('arsip-search-empty-notice');
    if (totalVisible === 0 && q) {
        if (!searchEmptyNotice) {
            searchEmptyNotice = document.createElement('div');
            searchEmptyNotice.id = 'arsip-search-empty-notice';
            searchEmptyNotice.className = 'text-center py-12 bg-white rounded-xl border border-[#E2EDF8] p-6 shadow-card mt-6';
            searchEmptyNotice.innerHTML = `
                <span class="material-symbols-outlined text-3xl text-[#49769F] mb-2" aria-hidden="true">search_off</span>
                <h4 class="text-base font-bold text-[#001D39] mb-1">Tidak ada hasil pencarian arsip</h4>
                <p class="text-xs text-[#49769F]">Tidak ada hasil yang cocok dengan "<strong>${escapeHtml(q)}</strong>".</p>
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

function inisialisasiQuickDatePills() {
    const pillsContainer = document.getElementById('arsip-quick-date-pills');
    if (!pillsContainer || pillsContainer.dataset.initialized) return;
    pillsContainer.dataset.initialized = '1';

    pillsContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('.arsip-pill-date');
        if (!btn) return;

        let targetVal = btn.getAttribute('data-val');
        const offset = btn.getAttribute('data-offset');

        if (offset !== null) {
            const idx = parseInt(offset, 10);
            if (daftarHari[idx]) {
                targetVal = daftarHari[idx].tanggal;
            } else {
                targetVal = 'semua';
            }
        }

        if (!targetVal) targetVal = 'semua';

        pillsContainer.querySelectorAll('.arsip-pill-date').forEach(p => {
            p.className = 'arsip-pill-date px-3 py-1.5 rounded-lg text-xs font-bold bg-[#EEF4F8] text-[#49769F] hover:text-[#001D39] hover:bg-[#E2EDF8] transition-all cursor-pointer whitespace-nowrap active:scale-95';
        });
        btn.className = 'arsip-pill-date px-3 py-1.5 rounded-lg text-xs font-bold bg-[#0A4174] text-white shadow-2xs transition-all cursor-pointer whitespace-nowrap active:scale-95';

        if (tanggalSelect) {
            tanggalSelect.value = targetVal;
        }
        tanggalTerpilih = targetVal;
        renderCardUntukTanggalTerpilih();
    });
}

if (tanggalSelect) {
    tanggalSelect.addEventListener('change', (e) => {
        tanggalTerpilih = e.target.value;
        const pillsContainer = document.getElementById('arsip-quick-date-pills');
        if (pillsContainer) {
            pillsContainer.querySelectorAll('.arsip-pill-date').forEach(p => {
                p.className = 'arsip-pill-date px-3 py-1.5 rounded-lg text-xs font-bold bg-[#EEF4F8] text-[#49769F] hover:text-[#001D39] hover:bg-[#E2EDF8] transition-all cursor-pointer whitespace-nowrap active:scale-95';
            });
        }
        renderCardUntukTanggalTerpilih();
    });
}
if (kategoriSelect) {
    kategoriSelect.addEventListener('change', (e) => {
        kategoriTerpilih = e.target.value;
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
            <div class="text-center py-12 bg-rose-50 rounded-lg -200/80 p-6 shadow-xs my-4">
                <span class="material-symbols-outlined text-3xl text-rose-600 mb-2" aria-hidden="true">cloud_off</span>
                <h3 class="text-base font-bold text-[#001D39] mb-1">Gagal Memuat Data Arsip</h3>
                <p class="text-xs text-[#49769F] mb-4 max-w-md mx-auto">Terjadi kendala saat mengambil riwayat arsip (${escapeHtml(data.message || 'Koneksi terputus')}).</p>
                <button onclick="window.muatUlangTabArsip()" class="px-4 py-2 bg-white hover:bg-[#EEF5FA] text-[#0A4174] hover:text-[#001D39] font-bold text-xs rounded-md shadow-2xs transition-all duration-200 cursor-pointer inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none">
                    <span class="material-symbols-outlined text-base text-[#49769F]" aria-hidden="true">refresh</span> Coba Muat Ulang
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
    inisialisasiQuickDatePills();
}

export function muatUlangTabArsip() {
    sudahDimuat = false;
    return muatTabArsip();
}