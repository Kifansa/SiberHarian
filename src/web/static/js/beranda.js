import { ambilBeranda, mulaiPipelineRequest, batalkanPipelineRequest, bukaStreamLog } from './api.js';
import { escapeHtml, formatWaktuSekarang, formatTanggalIndonesia } from './utils.js';
import { buatCardBerita, buatCardCve, buatSection } from './cards.js';
import { resetDataLengkap } from './modal.js';

const btnRun = document.getElementById('btn-run');
const btnRunText = document.getElementById('btn-run-text');
const runIcon = document.getElementById('run-icon');
const btnCancel = document.getElementById('btn-cancel');
const consoleBody = document.getElementById('console-body');
const consoleStatus = document.getElementById('console-status');
const cardContainer = document.getElementById('card-container');
const emptyState = document.getElementById('empty-state');
const resultsDesc = document.getElementById('results-desc');

let sumberAktif = null; // EventSource yang sedang berjalan

function tambahBarisLog(item) {
    if (!consoleBody.dataset.filled) consoleBody.innerHTML = '';
    consoleBody.dataset.filled = '1';
    const waktu = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const warnaTeks = item.level === 'ERROR' ? 'text-red-400' : item.level === 'WARNING' ? 'text-amber-400' : '';
    const baris = document.createElement('div');
    baris.className = `flex gap-2 opacity-0 translate-y-1 transition-all duration-300 log-line level-${item.level || 'INFO'}`;
    baris.innerHTML = `<span class="text-slate-500">[${waktu}]</span><span class="${warnaTeks}">${escapeHtml(item.message)}</span>`;
    consoleBody.appendChild(baris);
    consoleBody.scrollTop = consoleBody.scrollHeight;
    setTimeout(() => baris.classList.remove('opacity-0', 'translate-y-1'), 30);
}

function resetTombol() {
    btnRun.disabled = false;
    btnRunText.textContent = 'Jalankan Pipeline';
    runIcon.textContent = 'play_arrow';
    btnCancel.classList.remove('visible');
}

export async function tampilkanBeranda() {
    const data = await ambilBeranda();
    resetDataLengkap();

    if (data.status !== 'ok') {
        emptyState.style.display = 'block';
        emptyState.querySelector('h3').textContent = 'Belum ada hasil';
        emptyState.querySelector('p').textContent = 'Jalankan pipeline untuk mengisi data pertama kali.';
        cardContainer.innerHTML = '';
        return;
    }

    const berita = data.berita || [];
    const cve = data.cve || [];
    const insiden = berita.filter(b => b.kategori === 'insiden_spesifik');
    const analisis = berita.filter(b => b.kategori !== 'insiden_spesifik');
    resultsDesc.textContent = `Berita tanggal ${formatTanggalIndonesia(data.tanggal)} · diperbarui ${formatWaktuSekarang()}`;

    if (berita.length === 0 && cve.length === 0) {
        emptyState.style.display = 'block';
        emptyState.querySelector('h3').textContent = 'Tidak ada hasil pada tanggal terbaru';
        emptyState.querySelector('p').textContent = 'Tidak ditemukan berita atau CVE CRITICAL pada tanggal ini.';
        cardContainer.innerHTML = '';
        return;
    }

    emptyState.style.display = 'none';
    let html = '';
    html += buatSection('🚨 Insiden Spesifik', insiden.map(buatCardBerita).join(''), insiden.length);
    html += buatSection('📊 Analisis &amp; Tren', analisis.map(buatCardBerita).join(''), analisis.length);
    html += buatSection('🔴 CVE Critical', cve.map(buatCardCve).join(''), cve.length);
    cardContainer.innerHTML = html;
}

export async function mulaiPipeline() {
    btnRun.disabled = true;
    btnRunText.textContent = 'Sedang berjalan…';
    runIcon.textContent = 'autorenew';
    btnCancel.classList.add('visible');
    consoleStatus.textContent = '— pipeline berjalan —';
    cardContainer.innerHTML = '';
    emptyState.style.display = 'none';
    consoleBody.innerHTML = '';
    consoleBody.dataset.filled = '';

    const data = await mulaiPipelineRequest();
    if (data.status === 'sudah_berjalan') {
        tambahBarisLog({ level: 'WARNING', message: 'Pipeline sudah berjalan, tunggu sampai selesai.' });
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
                consoleStatus.textContent = item.sukses ? '— selesai —' : '— gagal, cek log di atas —';
                if (item.sukses) {
                    await tampilkanBeranda();
                    // Beri tahu tab Arsip & Tren (kalau sudah pernah dimuat) supaya
                    // cache-nya di-refresh, biar tidak nampilin data basi.
                    window.dispatchEvent(new CustomEvent('pipeline-selesai'));
                }
            }
        },
        () => {
            if (sumberAktif) sumberAktif.close();
            sumberAktif = null;
            resetTombol();
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
    consoleStatus.textContent = '— dibatalkan —';
    resetTombol();
}