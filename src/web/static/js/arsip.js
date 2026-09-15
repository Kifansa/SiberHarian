import { ambilArsip } from './api.js';
import { formatTanggalIndonesia, escapeHtml } from './utils.js';
import { buatCardBerita, buatCardCve, buatSection } from './cards.js';
import { resetDataLengkap } from './modal.js';

const tombolContainer = document.getElementById('arsip-tombol-tanggal');
const cardContainer = document.getElementById('arsip-card-container');
const emptyState = document.getElementById('arsip-empty-state');
const arsipDesc = document.getElementById('arsip-desc');

let daftarHari = [];      // cache hasil /api/arsip
let tanggalTerpilih = null;
let sudahDimuat = false;  // hanya fetch sekali per kunjungan, sampai di-invalidate manual

function renderTombolTanggal() {
    tombolContainer.innerHTML = daftarHari.map(hari => {
        const aktif = hari.tanggal === tanggalTerpilih;
        const kelasAktif = aktif
            ? 'bg-[#0A4174] text-white border-[#0A4174] shadow-xs font-bold'
            : 'bg-white hover:bg-[#EEF5FA] text-[#49769F] hover:text-[#001D39] border-[#BDD8E9] hover:border-[#49769F] font-semibold shadow-2xs';
        const jumlahTotal = hari.berita.length + hari.cve.length;
        return `
      <button class="px-4 py-2 rounded-full border text-xs transition-all cursor-pointer focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none ${kelasAktif}" data-tanggal="${hari.tanggal}" aria-label="Arsip tanggal ${formatTanggalIndonesia(hari.tanggal)}, ${jumlahTotal} insiden">
        ${formatTanggalIndonesia(hari.tanggal)} <span class="opacity-75 font-normal">(${jumlahTotal})</span>
      </button>`;
    }).join('');

    tombolContainer.querySelectorAll('button[data-tanggal]').forEach(btn => {
        btn.addEventListener('click', () => {
            tanggalTerpilih = btn.dataset.tanggal;
            renderTombolTanggal();
            renderCardUntukTanggalTerpilih();
        });
    });
}

function renderCardUntukTanggalTerpilih() {
    const hari = daftarHari.find(h => h.tanggal === tanggalTerpilih);
    if (!hari) {
        cardContainer.innerHTML = '';
        return;
    }
    resetDataLengkap();
    const insiden = hari.berita.filter(b => b.kategori === 'insiden_spesifik');
    const analisis = hari.berita.filter(b => b.kategori !== 'insiden_spesifik');
    let html = '';
    html += buatSection('Insiden Spesifik', insiden.map(buatCardBerita).join(''), insiden.length,
        { ikon: 'local_fire_department', kelas: 'bg-[#b91c1c] text-white' });
    html += buatSection('Edukasi / Evergreen', analisis.map(buatCardBerita).join(''), analisis.length,
        { ikon: 'school', kelas: 'bg-[#0A4174] text-white' });
    html += buatSection('CVE Critical', hari.cve.map(buatCardCve).join(''), hari.cve.length,
        { ikon: 'bug_report', kelas: 'bg-[#b45309] text-white' });
    cardContainer.innerHTML = html || '<p class="text-[#49769F] py-10 text-center font-medium">Tidak ada berita atau CVE pada tanggal ini.</p>';
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
            searchEmptyNotice.className = 'text-center py-12 bg-white rounded-3xl border border-[#E2EDF8] p-6 shadow-xs';
            searchEmptyNotice.innerHTML = `
                <span class="material-symbols-outlined text-3xl text-[#49769F] mb-2" aria-hidden="true">search_off</span>
                <h4 class="text-base font-bold text-[#001D39] mb-1">Tidak ada hasil pencarian arsip</h4>
                <p class="text-xs text-[#49769F]">Tidak ada artikel atau CVE pada tanggal ini yang cocok dengan "<strong>${escapeHtml(q)}</strong>".</p>
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

export async function muatTabArsip() {
    if (sudahDimuat) return;
    const data = await ambilArsip();

    if (data.status === 'error') {
        emptyState.classList.add('hidden');
        cardContainer.innerHTML = `
            <div class="text-center py-12 bg-rose-50 rounded-3xl border border-rose-200/80 p-6 shadow-xs my-4">
                <span class="material-symbols-outlined text-3xl text-rose-600 mb-2" aria-hidden="true">cloud_off</span>
                <h3 class="text-base font-bold text-[#001D39] mb-1">Gagal Memuat Data Arsip</h3>
                <p class="text-xs text-[#49769F] mb-4 max-w-md mx-auto">Terjadi kendala saat mengambil riwayat arsip (${escapeHtml(data.message || 'Koneksi terputus')}).</p>
                <button onclick="window.muatUlangTabArsip()" class="px-5 py-2.5 bg-white hover:bg-[#EEF5FA] text-[#0A4174] hover:text-[#001D39] font-bold text-xs rounded-full border border-[#BDD8E9] shadow-2xs transition-all duration-200 cursor-pointer inline-flex items-center gap-1.5 focus-visible:ring-2 focus-visible:ring-[#0A4174] focus-visible:outline-none">
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
    tanggalTerpilih = daftarHari[0].tanggal; // default: tanggal terbaru
    renderTombolTanggal();
    renderCardUntukTanggalTerpilih();
}

export function muatUlangTabArsip() {
    sudahDimuat = false;
    return muatTabArsip();
}