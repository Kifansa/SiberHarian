import { ambilArsip } from './api.js';
import { formatTanggalIndonesia } from './utils.js';
import { buatCardBerita, buatCardCve, buatSection } from './cards.js';
import { resetDataLengkap } from './modal.js';

const tombolContainer = document.getElementById('arsip-tombol-tanggal');
const cardContainer = document.getElementById('arsip-card-container');
const emptyState = document.getElementById('arsip-empty-state');
const arsipDesc = document.getElementById('arsip-desc');

let daftarHari = [];      // cache hasil /api/arsip - supaya klik tombol tanggal tidak fetch ulang
let tanggalTerpilih = null;
let sudahDimuat = false;  // hanya fetch sekali per kunjungan, sampai di-invalidate manual

function renderTombolTanggal() {
    tombolContainer.innerHTML = daftarHari.map(hari => {
        const aktif = hari.tanggal === tanggalTerpilih;
        const kelasAktif = aktif
            ? 'tab-active shadow-sm font-semibold'
            : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50 hover:text-slate-900 font-medium';
        const jumlahTotal = hari.berita.length + hari.cve.length;
        return `
      <button class="px-3.5 py-1.5 rounded-xl border font-mono text-xs transition-all cursor-pointer ${kelasAktif}" data-tanggal="${hari.tanggal}">
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
        { ikon: 'local_fire_department', kelas: 'bg-red-50 text-google-red border border-red-100/60' });
    html += buatSection('Edukasi / Evergreen', analisis.map(buatCardBerita).join(''), analisis.length,
        { ikon: 'school', kelas: 'bg-blue-50 text-primary border border-blue-100/60' });
    html += buatSection('CVE Critical', hari.cve.map(buatCardCve).join(''), hari.cve.length,
        { ikon: 'bug_report', kelas: 'bg-amber-50 text-amber-700 border border-amber-100/60' });
    cardContainer.innerHTML = html || '<p class="text-on-surface-variant py-10 text-center">Tidak ada berita/CVE pada tanggal ini.</p>';
}

export async function muatTabArsip() {
    if (sudahDimuat) return;
    const data = await ambilArsip();
    daftarHari = data.hari || [];
    sudahDimuat = true;

    if (daftarHari.length === 0) {
        emptyState.classList.remove('hidden');
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