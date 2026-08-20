import { ambilTren } from './api.js';

const trenDesc = document.getElementById('tren-desc');
const trenEmptyState = document.getElementById('tren-empty-state');
const trenKontenContainer = document.getElementById('tren-konten-container');
const prediksiBeritaTeks = document.getElementById('prediksi-berita-teks');
const prediksiCveTeks = document.getElementById('prediksi-cve-teks');

let sudahDimuat = false;

export async function muatTabTren() {
    if (sudahDimuat) return;
    const data = await ambilTren();
    sudahDimuat = true;

    if (data.status !== 'ok') {
        trenEmptyState.classList.remove('hidden');
        trenKontenContainer.classList.add('hidden');
        return;
    }
    trenEmptyState.classList.add('hidden');
    trenKontenContainer.classList.remove('hidden');
    trenDesc.textContent = `Dihitung pada: ${data.tanggal_dihitung}`;
    prediksiBeritaTeks.textContent = data.prediksi_berita || 'Belum ada data prediksi tren berita.';
    prediksiCveTeks.textContent = data.prediksi_cve || 'Belum ada data prediksi tren CVE.';
}

export function muatUlangTabTren() {
    sudahDimuat = false;
    return muatTabTren();
}