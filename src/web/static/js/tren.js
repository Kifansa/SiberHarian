/**
 * Modul Controller Utama Tab Tren (Orkestrator Komponen Modular)
 * Mengintegrasikan submodul di static/js/tren/ untuk menjaga kode tetap bersih, modular, dan ringan.
 */
import { ambilTren } from './api.js';
import { formatWaktuSekarang, tampilkanToast } from './utils.js';

import { renderKpiCards, flashUpdatedCards } from './tren/tren-kpi.js?v=9.2';
import { renderCharts } from './tren/tren-charts.js';
import { renderKasusInsidenWilayah } from './tren/tren-wilayah.js';
import { renderTables } from './tren/tren-tables.js';
import { renderLaporanCards, tampilAiTab } from './tren/tren-ai-cards.js?v=9.2';

let sudahDimuat = false;
let sedangMemuat = false;

// Expose tab switcher pada window agar selalu dapat diakses dari HTML
window.tampilAiTab = tampilAiTab;

/**
 * Memuat dan mengorkestrasi render seluruh submodul pada Tab Tren
 * @param {boolean} isManualReload Apakah pemanggilan berasal dari tombol refresh manual
 */
export async function muatTabTren(isManualReload = false) {
  if (sedangMemuat) return;
  if (sudahDimuat && !isManualReload) return;

  const trenDesc = document.getElementById('tren-desc');
  const trenLoadingState = document.getElementById('tren-loading-state');
  const trenEmptyState = document.getElementById('tren-empty-state');
  const trenKontenContainer = document.getElementById('tren-konten-container');
  const btnRefresh = document.getElementById('btn-refresh-tren');
  const btnRefreshIcon = document.getElementById('btn-refresh-tren-icon');
  const btnRefreshText = document.getElementById('btn-refresh-tren-text');

  sedangMemuat = true;

  // Feedback visual saat reload manual
  if (isManualReload) {
    if (btnRefresh) {
      btnRefresh.disabled = true;
      btnRefresh.classList.add('opacity-70', 'cursor-not-allowed');
    }
    if (btnRefreshIcon) {
      btnRefreshIcon.classList.add('animate-spin');
    }
    if (btnRefreshText) {
      btnRefreshText.textContent = 'Memperbarui...';
    }
    if (trenKontenContainer && !trenKontenContainer.classList.contains('hidden')) {
      trenKontenContainer.classList.add('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
    }
    if (trenDesc) {
      trenDesc.textContent = 'Memperbarui data tren siber...';
    }
  } else {
    // First load: tampilkan loading radar & shimmer skeleton
    if (trenLoadingState) trenLoadingState.classList.remove('hidden');
    if (trenKontenContainer) trenKontenContainer.classList.add('hidden');
    if (trenEmptyState) trenEmptyState.classList.add('hidden');
    if (trenDesc) trenDesc.textContent = 'Menganalisis data tren intelijen siber...';
  }

  try {
    const [data] = await Promise.all([
      ambilTren(),
      new Promise(r => setTimeout(r, isManualReload ? 500 : 450))
    ]);

    if (!data || data.status !== 'ok') {
      sudahDimuat = false;
      if (trenLoadingState) trenLoadingState.classList.add('hidden');
      if (trenEmptyState) trenEmptyState.classList.remove('hidden');
      if (trenKontenContainer) {
        trenKontenContainer.classList.add('hidden');
        trenKontenContainer.classList.remove('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
      }
      if (trenDesc) {
        trenDesc.textContent = data && data.message ? `Gagal: ${data.message}` : 'Belum ada data tren.';
      }
      if (isManualReload) {
        tampilkanToast('Gagal memuat data tren siber', 'error');
      }
      return;
    }

    sudahDimuat = true;

    if (trenLoadingState) trenLoadingState.classList.add('hidden');
    if (trenEmptyState) trenEmptyState.classList.add('hidden');
    if (trenKontenContainer) {
      trenKontenContainer.classList.remove('hidden');
      trenKontenContainer.classList.remove('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
      trenKontenContainer.classList.add('opacity-100', 'scale-100');
    }

    if (trenDesc) {
      trenDesc.textContent = `Diperbarui pada ${formatWaktuSekarang()}`;
    }

    // 1. Delegasi ke tren-ai-cards (SITREP CTI AI 5 Modul)
    const containerBerita = document.getElementById('prediksi-berita-cards');
    if (containerBerita) renderLaporanCards(containerBerita, data.prediksi_berita, 'berita');

    // 2. Delegasi ke submodul analitik
    const stat = data.statistik;
    if (stat) {
      renderKpiCards(stat, isManualReload);
      renderKasusInsidenWilayah(stat);
      renderTables(stat);
      
      // Render grafik terisolasi dengan delay singkat
      setTimeout(() => {
        try {
          renderCharts(stat);
        } catch (errChart) {
          console.error('Gagal merender chart tren:', errChart);
        }
      }, 50);

      if (isManualReload) {
        flashUpdatedCards();
      }
    }

    // Feedback selesai reload
    if (isManualReload) {
      if (btnRefreshIcon) {
        btnRefreshIcon.classList.remove('animate-spin');
        btnRefreshIcon.textContent = 'refresh';
      }
      if (btnRefreshText) {
        btnRefreshText.textContent = 'Muat Ulang Data';
      }
      if (btnRefresh) {
        btnRefresh.disabled = false;
        btnRefresh.classList.remove('opacity-70', 'cursor-not-allowed');
      }
      tampilkanToast('Data tren keamanan siber berhasil diperbarui');
    }
  } catch (err) {
    console.error('Error saat memuat tab tren:', err);
    sudahDimuat = false;
    if (trenLoadingState) trenLoadingState.classList.add('hidden');
    if (trenEmptyState) trenEmptyState.classList.remove('hidden');
    if (trenKontenContainer) {
      trenKontenContainer.classList.add('hidden');
      trenKontenContainer.classList.remove('opacity-40', 'scale-[0.995]', 'blur-[0.5px]', 'pointer-events-none');
    }
    if (trenDesc) {
      trenDesc.textContent = 'Terjadi kesalahan saat memuat data tren.';
    }
    if (isManualReload) {
      tampilkanToast('Gagal memperbarui data tren siber', 'error');
      if (btnRefreshIcon) {
        btnRefreshIcon.classList.remove('animate-spin');
        btnRefreshIcon.textContent = 'refresh';
      }
      if (btnRefreshText) {
        btnRefreshText.textContent = 'Muat Ulang Data';
      }
      if (btnRefresh) {
        btnRefresh.disabled = false;
        btnRefresh.classList.remove('opacity-70', 'cursor-not-allowed');
      }
    }
  } finally {
    sedangMemuat = false;
  }
}

/**
 * Memuat ulang data tren secara manual (bypass cache in-memory)
 */
export function muatUlangTabTren() {
  sudahDimuat = false;
  return muatTabTren(true);
}

// Binds ke window untuk kompatibilitas penuh dengan atribut event handler inline HTML
window.muatTabTren = muatTabTren;
window.muatUlangTabTren = muatUlangTabTren;