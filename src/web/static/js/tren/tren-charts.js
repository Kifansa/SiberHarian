import { escapeHtml } from './tren-utils.js';

/**
 * Modul visualisasi analitik untuk Tab Tren
 */

// Global chart instances untuk pengelolaan lifecycle & cleanup
let chartVendorCve = null;
let chartRadarVektor = null;
let chartSektorTarget = null;

/**
 * Menghancurkan instance grafik yang sedang aktif agar tidak memori bocor atau bentrok saat re-render
 */
export function destroyCharts() {
  if (chartVendorCve) { chartVendorCve.destroy(); chartVendorCve = null; }
  if (chartRadarVektor && typeof chartRadarVektor.destroy === 'function') {
    chartRadarVektor.destroy();
    chartRadarVektor = null;
  }
  if (chartSektorTarget && typeof chartSektorTarget.destroy === 'function') {
    chartSektorTarget.destroy();
    chartSektorTarget = null;
  }
}

/**
 * Merender analitik visual: Vektor Serangan Siber (Desain Referensi), Sektor Target (Desain Referensi), dan Top Vendor CVE
 * @param {Object} stat Objek data statistik tren
 */
export function renderCharts(stat) {
  if (!stat) return;

  // Bersihkan grafik sebelumnya
  destroyCharts();

  // 1. Distribusi Vektor Serangan Siber (TTPs) - Horizontal Progress Bar ala Desain Referensi
  const elRadar = document.getElementById('chart-radar-vektor') || document.getElementById('chart-vektor-serangan');
  if (elRadar) {
    let containerRadar = elRadar;
    if (containerRadar.tagName === 'CANVAS') {
      const div = document.createElement('div');
      div.id = containerRadar.id;
      div.className = 'space-y-4 pt-1';
      containerRadar.parentNode.replaceChild(div, containerRadar);
      containerRadar = div;
    }

    const vektorList = stat.vektor_serangan || [];
    let displayList = vektorList.filter(d => d.jumlah > 0);
    if (displayList.length === 0) {
      displayList = vektorList.slice(0, 6);
    } else {
      displayList = displayList.slice(0, 6);
    }

    if (!displayList.length) {
      containerRadar.innerHTML = `<div class="text-[#49769F] text-xs py-8 text-center font-sans">Belum ada data vektor serangan untuk rentang waktu ini.</div>`;
    } else {
      const maxJumlah = Math.max(...displayList.map(d => d.jumlah), 1);

      // Warna solid sesuai palette saat ini
      const vektorSolidColors = {
        'Weaponized AI & Botnet': '#dc2626',
        'Ransomware': '#b91c1c',
        'Ransomware & Pemerasan': '#b91c1c',
        'Phishing': '#0A4174',
        'Phishing & Social Engineering': '#0A4174',
        'Kebocoran Data': '#4E8EA2',
        'Malware': '#001D39',
        'Malware & Infostealer': '#001D39',
        'Peretasan': '#49769F',
        'Eksploitasi Celah RCE': '#49769F',
        'Pembajakan Aset': '#7BBDE8',
        'Pembajakan Akun & Kredensial': '#7BBDE8',
        'Supply Chain & Repositori': '#0284c7',
      };

      // Warna teks kontras tinggi untuk angka metrik
      const vektorTextColors = {
        'Weaponized AI & Botnet': '#dc2626',
        'Ransomware': '#b91c1c',
        'Ransomware & Pemerasan': '#b91c1c',
        'Phishing': '#0A4174',
        'Phishing & Social Engineering': '#0A4174',
        'Kebocoran Data': '#0e7490',
        'Malware': '#001D39',
        'Malware & Infostealer': '#001D39',
        'Peretasan': '#1e40af',
        'Eksploitasi Celah RCE': '#0369a1',
        'Pembajakan Aset': '#0284c7',
        'Pembajakan Akun & Kredensial': '#0284c7',
        'Supply Chain & Repositori': '#0284c7',
      };

      containerRadar.innerHTML = displayList.map((item) => {
        const barColor = vektorSolidColors[item.vektor] || '#0A4174';
        const textColor = vektorTextColors[item.vektor] || barColor;
        const widthPct = item.jumlah > 0 ? Math.max(Math.min(Math.round((item.jumlah / maxJumlah) * 100), 100), 3) : 0;

        return `
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs font-sans">
              <div class="min-w-0 pr-2">
                <span class="text-[#001D39] font-medium truncate">${escapeHtml(item.vektor)}</span>
              </div>
              <div class="shrink-0 font-bold" style="color: ${textColor};">
                ${item.jumlah} artikel
              </div>
            </div>
            <div class="w-full bg-[#EEF4F8] rounded-full h-2 overflow-hidden border border-[#E2EDF8]">
              <div class="h-full rounded-full transition-all duration-700 ease-out" style="width: ${widthPct}%; background-color: ${barColor};"></div>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  // 2. Sektor Industri Target Terpapar - Horizontal Progress Bar ala Desain Referensi
  const elSektor = document.getElementById('chart-sektor-target');
  if (elSektor) {
    let containerSektor = elSektor;
    if (containerSektor.tagName === 'CANVAS') {
      const div = document.createElement('div');
      div.id = containerSektor.id;
      div.className = 'space-y-4 pt-1';
      containerSektor.parentNode.replaceChild(div, containerSektor);
      containerSektor = div;
    }

    const sektorList = stat.sektor_target || [];
    let displayList = sektorList.filter(d => d.jumlah > 0);
    if (displayList.length === 0) {
      displayList = sektorList.slice(0, 5);
    } else {
      displayList = displayList.slice(0, 5);
    }

    if (!displayList.length) {
      containerSektor.innerHTML = `<div class="text-[#49769F] text-xs py-8 text-center font-sans">Belum ada data sektor industri untuk rentang waktu ini.</div>`;
    } else {
      const maxSektor = Math.max(...displayList.map(d => d.jumlah), 1);
      const totalInsiden = stat.total_berita || displayList.reduce((acc, curr) => acc + curr.jumlah, 0) || 1;

      // Warna solid sesuai palette saat ini
      const sektorColorMap = {
        'Pengguna & Konsumen Ritel': { bar: '#0A4174', text: '#0A4174' },
        'Pengembang & Infrastruktur TI': { bar: '#4E8EA2', text: '#0e7490' },
        'Finansial, Bank & Kripto': { bar: '#001D39', text: '#001D39' },
        'Korporasi & Enterprise': { bar: '#49769F', text: '#1e40af' },
        'Pemerintahan & Instansi Publik': { bar: '#0284c7', text: '#0369a1' },
      };
      const defaultSektorColors = [
        { bar: '#0A4174', text: '#0A4174' },
        { bar: '#4E8EA2', text: '#0e7490' },
        { bar: '#001D39', text: '#001D39' },
        { bar: '#49769F', text: '#1e40af' },
        { bar: '#0284c7', text: '#0369a1' },
        { bar: '#6EA2B3', text: '#0891b2' },
        { bar: '#BDD8E9', text: '#0284c7' },
      ];

      containerSektor.innerHTML = displayList.map((item, idx) => {
        const colorObj = sektorColorMap[item.sektor] || defaultSektorColors[idx % defaultSektorColors.length];
        const barColor = colorObj.bar;
        const textColor = colorObj.text;
        const widthPct = item.jumlah > 0 ? Math.max(Math.min(Math.round((item.jumlah / maxSektor) * 100), 100), 3) : 0;
        const pctInsiden = Math.round((item.jumlah / totalInsiden) * 100);

        return `
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs font-sans">
              <div class="min-w-0 pr-2">
                <span class="text-[#001D39] font-medium truncate">${escapeHtml(item.sektor)}</span>
              </div>
              <div class="shrink-0 font-bold" style="color: ${textColor};">
                ${item.jumlah} insiden <span class="font-semibold text-[11px] opacity-90">(${pctInsiden}%)</span>
              </div>
            </div>
            <div class="w-full bg-[#EEF4F8] rounded-full h-2 overflow-hidden border border-[#E2EDF8]">
              <div class="h-full rounded-full transition-all duration-700 ease-out" style="width: ${widthPct}%; background-color: ${barColor};"></div>
            </div>
          </div>
        `;
      }).join('');
    }
  }

  // 3. Chart Vendor CVE Prioritas (Solid Horizontal Ranking Bar Chart)
  const elVendor = document.getElementById('chart-vendor-cve');
  if (elVendor) {
    const labels = (stat.vendor_naik || []).map(item => item.vendor);
    const counts = (stat.vendor_naik || []).map(item => item.jumlah_terkini);
    const vendorSolidColors = ['#0A4174', '#4E8EA2', '#001D39', '#7BBDE8', '#49769F', '#6EA2B3', '#BDD8E9'];

    chartVendorCve = new Chart(elVendor, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Total Kerentanan CVE',
          data: counts,
          backgroundColor: vendorSolidColors.slice(0, labels.length),
          borderRadius: 8,
          borderSkipped: false,
          barThickness: 16,
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            ...tooltipStyle,
            callbacks: {
              label: (ctx) => ` ${ctx.raw} kerentanan CVE kritis`
            }
          }
        },
        scales: {
          x: {
            grid: { color: solidGridColor },
            ticks: { color: solidTickColor, precision: 0 }
          },
          y: {
            grid: { display: false },
            ticks: {
              color: '#001D39',
              font: { family: 'Inter, sans-serif', weight: '600' }
            }
          }
        }
      }
    });
  }
}
