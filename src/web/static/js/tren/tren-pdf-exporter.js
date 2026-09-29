import { escapeHtml } from './tren-utils.js';
import { isMainSectionHeader } from './tren-ai-cards.js';
import { tampilkanToast } from '../utils.js';

/**
 * Mem-parsing teks Markdown laporan menjadi format HTML khusus siap cetak PDF
 * @param {string} raw Teks Markdown
 * @returns {string} HTML string
 */
export function parseMarkdownToHtmlForPdf(raw) {
  if (!raw || !raw.trim()) {
    return '<div class="card-block"><p style="color:#64748b;font-style:italic;">Belum ada data analisis tercatat.</p></div>';
  }

  const lines = raw.split('\n');
  let html = '';
  let inList = false;
  let inSection = false;

  for (let rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      if (inList) { html += '</ul>'; inList = false; }
      continue;
    }

    // Heading baris baru: section header, ###, atau **Judul**
    const headerCheck = isMainSectionHeader(line);
    const isHeading = headerCheck.isHeader || line.startsWith('###') || (/^\*\*[^*]+\*\*$/.test(line) && line.length < 80);
    if (isHeading) {
      if (inList) { html += '</ul>'; inList = false; }
      if (inSection) { html += '</div>'; }
      const cleanTitle = headerCheck.isHeader ? headerCheck.cleanTitle : line.replace(/^###\s*/, '').replace(/^\*\*|\*\*$/g, '').trim();
      html += `<div class="card-block"><h4 class="card-heading">${escapeHtml(cleanTitle)}</h4>`;
      inSection = true;
      continue;
    }

    // Bullet point
    if (line.startsWith('- ') || line.startsWith('* ') || /^\d+[\.\)]\s+/.test(line)) {
      if (!inList) {
        if (!inSection) { html += '<div class="card-block">'; inSection = true; }
        html += '<ul class="bullet-list">';
        inList = true;
      }
      let content = line.replace(/^[-*]\s+|\d+[\.\)]\s+/, '').trim();
      
      // Formatting badge mitigasi
      content = content
        .replace(/^Prioritas\s*:\s*/i, '<span class="badge-prio">PRIORITAS</span> ')
        .replace(/^Prioritas\s*1\s*(\([^\)]*\))?\s*:\s*/i, '<span class="badge-prio">PRIORITAS</span> ')
        .replace(/^Prioritas\s*2\s*(\([^\)]*\))?\s*:\s*/i, '<span class="badge-menengah">MENENGAH</span> ')
        .replace(/^Prioritas\s*3\s*(\([^\)]*\))?\s*:\s*/i, '<span class="badge-jangka">JANGKA PANJANG</span> ')
        .replace(/^Prioritas\s*Kritis\s*:\s*/i, '<span class="badge-prio">PRIORITAS</span> ');

      // Bold text formatting
      content = content.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      html += `<li>${content}</li>`;
      continue;
    }

    // Regular paragraph text
    if (inList) { html += '</ul>'; inList = false; }
    if (!inSection) { html += '<div class="card-block">'; inSection = true; }
    let pContent = line.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html += `<p class="card-text">${pContent}</p>`;
  }

  if (inList) html += '</ul>';
  if (inSection) html += '</div>';
  return html;
}

/**
 * Menghasilkan dan memicu pencetakan dokumen PDF resmi Laporan Eksekutif Mingguan
 * @param {Object} lastTrenData Data tren tersimpan terakhir
 */
export function eksporLaporanTren(lastTrenData) {
  if (!lastTrenData || !lastTrenData.statistik) {
    tampilkanToast('Data tren belum tersedia untuk diekspor ke PDF', 'warning');
    return;
  }

  const stat = lastTrenData.statistik;
  const tglCetak = new Date().toLocaleDateString('id-ID', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  const jamCetak = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' });

  const htmlContent = `<!DOCTYPE html>
<html lang="id">
<head>
  <meta charset="utf-8">
  <title>Laporan Eksekutif CTI - SiberHarian</title>
  <style>
    @page {
      size: A4 portrait;
      margin: 12mm 15mm 15mm 15mm;
    }
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      color: #001D39;
      background: #ffffff;
      font-size: 9.5pt;
      line-height: 1.45;
      margin: 0;
      padding: 0;
    }
    .header-kop {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid #001D39;
      padding-bottom: 10px;
      margin-bottom: 14px;
    }
    .header-kop .instansi {
      font-size: 8pt;
      font-weight: 700;
      color: #64748b;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 2px;
    }
    .header-kop h1 {
      font-size: 13pt;
      font-weight: 900;
      color: #0A4174;
      margin: 0 0 2px 0;
      letter-spacing: -0.01em;
    }
    .header-kop .subjudul {
      font-size: 8.5pt;
      color: #334155;
      margin: 0;
    }
    .badge-gov {
      background: #EEF5FA;
      border: 1px solid #BDD8E9;
      color: #0A4174;
      padding: 4px 9px;
      border-radius: 6px;
      font-size: 7.5pt;
      font-weight: 800;
      text-align: right;
    }
    .posture-banner {
      background: #EEF5FA;
      border: 1px solid #BDD8E9;
      border-left: 4.5px solid #0A4174;
      padding: 9px 12px;
      border-radius: 6px;
      margin-bottom: 14px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .posture-banner .posture-title {
      font-size: 9.5pt;
      font-weight: 800;
      color: #001D39;
      margin: 0;
    }
    .posture-banner .posture-meta {
      font-size: 8pt;
      color: #475569;
      margin-top: 1px;
    }
    .posture-badge {
      background: #0A4174;
      color: #ffffff;
      padding: 3px 8px;
      border-radius: 4px;
      font-weight: 800;
      font-size: 8.5pt;
      letter-spacing: 0.05em;
    }
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 6px;
      margin-bottom: 14px;
    }
    .kpi-box {
      border: 1px solid #BDD8E9;
      background: #EEF4F8;
      border-radius: 6px;
      padding: 8px 10px;
    }
    .kpi-box .label {
      font-size: 7pt;
      text-transform: uppercase;
      font-weight: 700;
      color: #64748b;
      margin-bottom: 2px;
    }
    .kpi-box .val {
      font-size: 13pt;
      font-weight: 800;
      color: #001D39;
      font-family: monospace;
    }
    .kpi-box .sub {
      font-size: 7pt;
      color: #49769F;
      margin-top: 1px;
    }
    .section-title {
      font-size: 10pt;
      font-weight: 800;
      color: #001D39;
      border-bottom: 1.5px solid #BDD8E9;
      padding-bottom: 3px;
      margin: 14px 0 8px 0;
      text-transform: uppercase;
      letter-spacing: 0.03em;
      page-break-after: avoid;
    }
    .card-block {
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 9px 12px;
      margin-bottom: 8px;
      background: #ffffff;
      page-break-inside: avoid;
    }
    .card-heading {
      margin: 0 0 4px 0;
      font-size: 9.5pt;
      font-weight: 800;
      color: #0A4174;
    }
    .card-text {
      margin: 0 0 4px 0;
      font-size: 8.5pt;
      color: #334155;
    }
    .bullet-list {
      margin: 3px 0 0 0;
      padding-left: 16px;
      font-size: 8.5pt;
      color: #334155;
    }
    .bullet-list li {
      margin-bottom: 4px;
      line-height: 1.4;
    }
    .badge-prio {
      display: inline-block;
      background: #fee2e2;
      color: #991b1b;
      font-weight: 800;
      font-size: 7pt;
      padding: 1.5px 5px;
      border-radius: 6px;
      margin-right: 4px;
      font-family: monospace;
    }
    .badge-menengah {
      display: inline-block;
      background: #fef3c7;
      color: #92400e;
      font-weight: 800;
      font-size: 7pt;
      padding: 1.5px 5px;
      border-radius: 6px;
      margin-right: 4px;
      font-family: monospace;
    }
    .badge-jangka {
      display: inline-block;
      background: #ede9fe;
      color: #4338ca;
      font-weight: 800;
      font-size: 7pt;
      padding: 1.5px 5px;
      border-radius: 6px;
      margin-right: 4px;
      font-family: monospace;
    }
    table.data-table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 6px;
      font-size: 8pt;
      page-break-inside: avoid;
    }
    table.data-table th {
      background: #EEF4F8;
      border: 1px solid #BDD8E9;
      padding: 5px 8px;
      text-align: left;
      font-weight: 700;
      color: #001D39;
      text-transform: uppercase;
      font-size: 7.5pt;
    }
    table.data-table td {
      border: 1px solid #e2e8f0;
      padding: 5px 8px;
      color: #001D39;
    }
    .footer-meta {
      margin-top: 20px;
      border-top: 1px solid #e2e8f0;
      padding-top: 6px;
      display: flex;
      justify-content: space-between;
      font-size: 7pt;
      color: #64748b;
      page-break-inside: avoid;
    }
  </style>
</head>
<body>
  <div class="header-kop">
    <div>
      <div class="instansi">Pemerintah Provinsi Jawa Timur &bull; Diskominfo &bull; CSIRT</div>
      <h1>Laporan Resmi Intelijen Ancaman Siber Mingguan</h1>
      <div class="subjudul">Analisis Komparatif 7 Hari Terkini vs Baseline &amp; Rekomendasi Mitigasi Taktis</div>
    </div>
    <div class="badge-gov">
      <div>KLASIFIKASI: TLP:AMBER</div>
      <div style="font-weight:normal;color:#64748b;margin-top:2px;">${tglCetak}</div>
    </div>
  </div>

  <div class="posture-banner">
    <div>
      <div class="posture-title">Laporan Pemantauan Intelijen Ancaman Siber Mingguan &bull; CSIRT Diskominfo Jawa Timur</div>
      <div class="posture-meta">Fokus Utama: <strong>${escapeHtml(stat.top_focus || 'Keamanan Website & Infrastruktur OPD')}</strong> &bull; Pemantauan: 7 Hari Terkini</div>
    </div>
    <div class="posture-badge">RESMI</div>
  </div>

  ${(() => {
    const sektorList = stat.top_sektor || stat.sektor_target || [];
    const topSektorObj = sektorList[0] || {};
    const topSektorName = topSektorObj.sektor || stat.top_focus || 'Infrastruktur Vital';
    const topSektorGrowth = topSektorObj.growth_persen ?? 0;
    const polaName = (stat.prediksi_pola_serangan?.pola || 'Belum Ada Data').replace(/^TREN LONJAKAN:\s*/i, '').trim();
    const ancamanName = (stat.ancaman_baru || 'Kondisi Stabil').trim();

    return `
    <div class="kpi-grid">
      <div class="kpi-box">
        <div class="label">Total Berita Insiden (7H)</div>
        <div class="val">${stat.total_berita || 0}</div>
        <div class="sub">Artikel Insiden Terkini</div>
      </div>
      <div class="kpi-box">
        <div class="label">Sektor Paling Terdampak</div>
        <div class="val" style="font-size:9pt;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${escapeHtml(topSektorName)}">${escapeHtml(topSektorName)}</div>
        <div class="sub">${topSektorGrowth >= 0 ? '+' : ''}${topSektorGrowth}% vs minggu lalu</div>
      </div>
      <div class="kpi-box">
        <div class="label">Tren Insiden Mingguan</div>
        <div class="val" style="font-size:9pt;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${escapeHtml(polaName)}">${escapeHtml(polaName)}</div>
        <div class="sub">Lonjakan Pola Tercepat</div>
      </div>
      <div class="kpi-box">
        <div class="label">Prediksi Ancaman Baru</div>
        <div class="val" style="font-size:9pt;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="${escapeHtml(ancamanName)}">${escapeHtml(ancamanName)}</div>
        <div class="sub">Sinyal Dini Intelijen CSIRT</div>
      </div>
    </div>
    `;
  })()}

  <!-- 1. Kasus Insiden Siber Teramai -->
  <div class="section-title">1. Kasus Insiden Siber Teramai</div>
  <table class="data-table" style="margin-bottom:12px;">
    <thead>
      <tr>
        <th style="width:16%;">Lingkup Wilayah</th>
        <th style="width:14%;">Kategori</th>
        <th style="width:40%;">Kasus Insiden Terpilih (Model AI CTI)</th>
        <th style="width:30%;">Analisis Urgensi &amp; Potensi Ancaman</th>
      </tr>
    </thead>
    <tbody>
      <!-- Internasional -->
      ${(() => {
        const item = stat.kasus_wilayah_ai?.internasional || (stat.kasus_wilayah?.internasional?.[0] ? {
          ada_kejadian: true,
          nama_kejadian: stat.kasus_wilayah.internasional[0].judul,
          kategori: stat.kasus_wilayah.internasional[0].tag,
          lokasi: 'Global',
          alasan_urgensi: 'Insiden paling ramai dibicarakan media internasional 7 hari terakhir.',
          potensi_ancaman: 'Potensi eskalasi serangan siber global.',
          sumber: stat.kasus_wilayah.internasional[0].sumber
        } : null);
        if (!item || !item.ada_kejadian || item.nama_kejadian === '-') {
          return '<tr><td><span class="badge-menengah" style="background:#EEF5FA;color:#0A4174;">Internasional</span></td><td colspan="3" style="text-align:center;color:#49769F;font-weight:bold;">- (Tidak ada insiden tercatat)</td></tr>';
        }
        return `
          <tr>
            <td><span class="badge-menengah" style="background:#EEF5FA;color:#0A4174;">Internasional</span><br><span style="font-size:7pt;color:#49769F;">${escapeHtml(item.lokasi || 'Global')}</span></td>
            <td><strong>${escapeHtml(item.kategori || 'Insiden')}</strong></td>
            <td><strong>${escapeHtml(item.nama_kejadian)}</strong><br><span style="font-size:7pt;color:#64748b;">Sumber: ${escapeHtml(item.sumber || 'Media Intelijen')}</span></td>
            <td style="font-size:7.5pt;line-height:1.35;">
              <strong style="color:#b45309;">Urgensi:</strong> ${escapeHtml(item.alasan_urgensi || '-')}<br>
              <strong style="color:#b91c1c;">Potensi:</strong> ${escapeHtml(item.potensi_ancaman || '-')}
            </td>
          </tr>
        `;
      })()}

      <!-- Nasional -->
      ${(() => {
        const item = stat.kasus_wilayah_ai?.nasional || (stat.kasus_wilayah?.nasional?.[0] ? {
          ada_kejadian: true,
          nama_kejadian: stat.kasus_wilayah.nasional[0].judul,
          kategori: stat.kasus_wilayah.nasional[0].tag,
          lokasi: 'Indonesia',
          alasan_urgensi: 'Kasus dengan liputan tertinggi di ranah siber nasional.',
          potensi_ancaman: 'Peningkatan ancaman pencurian kredensial dan infrastruktur.',
          sumber: stat.kasus_wilayah.nasional[0].sumber
        } : null);
        if (!item || !item.ada_kejadian || item.nama_kejadian === '-') {
          return '<tr><td><span class="badge-menengah" style="background:#f0fdf4;color:#0f766e;">Nasional</span></td><td colspan="3" style="text-align:center;color:#64748b;font-weight:bold;">- (Tidak ada insiden tercatat)</td></tr>';
        }
        return `
          <tr>
            <td><span class="badge-menengah" style="background:#f0fdf4;color:#0f766e;">Nasional</span><br><span style="font-size:7pt;color:#64748b;">${escapeHtml(item.lokasi || 'Indonesia')}</span></td>
            <td><strong>${escapeHtml(item.kategori || 'Insiden')}</strong></td>
            <td><strong>${escapeHtml(item.nama_kejadian)}</strong><br><span style="font-size:7pt;color:#64748b;">Sumber: ${escapeHtml(item.sumber || 'Media Intelijen')}</span></td>
            <td style="font-size:7.5pt;line-height:1.35;">
              <strong style="color:#b45309;">Urgensi:</strong> ${escapeHtml(item.alasan_urgensi || '-')}<br>
              <strong style="color:#b91c1c;">Potensi:</strong> ${escapeHtml(item.potensi_ancaman || '-')}
            </td>
          </tr>
        `;
      })()}

      <!-- Jawa Timur -->
      ${(() => {
        const item = stat.kasus_wilayah_ai?.jawa_timur || (stat.kasus_wilayah?.jawa_timur?.[0] ? {
          ada_kejadian: true,
          nama_kejadian: stat.kasus_wilayah.jawa_timur[0].judul,
          kategori: stat.kasus_wilayah.jawa_timur[0].tag,
          lokasi: 'Jawa Timur',
          alasan_urgensi: 'Insiden berdampak langsung pada entitas Jawa Timur.',
          potensi_ancaman: 'Risiko peretasan portal instansi daerah.',
          sumber: stat.kasus_wilayah.jawa_timur[0].sumber
        } : null);
        const isKosong = !item || !item.ada_kejadian || item.nama_kejadian === '-' || item.nama_kejadian === '' || item.nama_kejadian === 'None';
        if (isKosong) {
          return `
            <tr>
              <td><span class="badge-menengah" style="background:#f1f5f9;color:#475569;">Jawa Timur</span></td>
              <td colspan="3" style="text-align:center;font-weight:bold;font-size:10pt;color:#64748b;">- (Tidak ada kasus insiden siber tercatat pada 38 Kab/Kota Jatim)</td>
            </tr>
          `;
        }
        return `
          <tr style="background:#fefce8;">
            <td><span class="badge-prio" style="background:#fef3c7;color:#92400e;">Jawa Timur</span><br><span style="font-size:7pt;color:#92400e;font-weight:bold;">${escapeHtml(item.lokasi || 'Jawa Timur')}</span></td>
            <td><strong>${escapeHtml(item.kategori || 'Insiden')}</strong></td>
            <td><strong>${escapeHtml(item.nama_kejadian)}</strong><br><span style="font-size:7pt;color:#64748b;">Sumber: ${escapeHtml(item.sumber || 'Media Intelijen')}</span></td>
            <td style="font-size:7.5pt;line-height:1.35;">
              <strong style="color:#b45309;">Urgensi:</strong> ${escapeHtml(item.alasan_urgensi || '-')}<br>
              <strong style="color:#b91c1c;">Potensi:</strong> ${escapeHtml(item.potensi_ancaman || '-')}
            </td>
          </tr>
        `;
      })()}
    </tbody>
  </table>

  <div class="section-title">2. SITREP Intelijen Ancaman &amp; Rekomendasi Mitigasi</div>
  ${parseMarkdownToHtmlForPdf(lastTrenData.prediksi_berita)}

  <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:10px;page-break-inside:avoid;">
    <div>
      <div class="section-title" style="margin-top:0;">3. Kata Kunci Lonjakan Tertinggi</div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Kata Kunci</th>
            <th style="text-align:center;">Kemunculan (7H)</th>
            <th style="text-align:right;">Growth</th>
          </tr>
        </thead>
        <tbody>
          ${(stat.kata_kunci_naik || []).slice(0, 6).map(k => `
            <tr>
              <td><strong>${escapeHtml(k.kata_kunci)}</strong></td>
              <td style="text-align:center;font-weight:600;">${k.jumlah_terkini}</td>
              <td style="text-align:right;"><span style="display:inline-block;background:#15803d;color:#ffffff;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:10.5px;">+${k.growth_persen}%</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
    <div>
      <div class="section-title" style="margin-top:0;">4. Sektor Sasaran Terpapar (IIV)</div>
      <table class="data-table">
        <thead>
          <tr>
            <th>Sektor Vital</th>
            <th style="text-align:center;">Total Insiden</th>
            <th style="text-align:right;">Status</th>
          </tr>
        </thead>
        <tbody>
          ${(stat.top_sektor || stat.sektor_target || []).slice(0, 6).map(s => `
            <tr>
              <td><strong>${escapeHtml(s.sektor)}</strong></td>
              <td style="text-align:center;font-weight:600;">${s.jumlah || 0}</td>
              <td style="text-align:right;"><span style="display:inline-block;background:#0A4174;color:#ffffff;padding:2px 8px;border-radius:4px;font-weight:bold;font-size:10.5px;">PRIORITAS</span></td>
            </tr>
          `).join('')}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Lembar Pengesahan Resmi -->
  <div style="margin-top:24px;display:flex;justify-content:space-between;page-break-inside:avoid;font-size:8pt;color:#334155;">
    <div style="text-align:center;width:200px;">
      <div>Disusun Oleh,</div>
      <div style="font-weight:bold;margin-top:4px;">Analis Intelijen Ancaman Siber (CTI)</div>
      <div style="margin-top:45px;border-bottom:1px solid #cbd5e1;width:160px;margin-left:auto;margin-right:auto;"></div>
      <div style="margin-top:4px;font-size:7.5pt;color:#64748b;">Tim CSIRT Diskominfo Jatim</div>
    </div>
    <div style="text-align:center;width:200px;">
      <div>Mengetahui,</div>
      <div style="font-weight:bold;margin-top:4px;">Kepala Bidang Keamanan Siber</div>
      <div style="margin-top:45px;border-bottom:1px solid #cbd5e1;width:160px;margin-left:auto;margin-right:auto;"></div>
      <div style="margin-top:4px;font-size:7.5pt;color:#64748b;">Pemerintah Provinsi Jawa Timur</div>
    </div>
  </div>

  <div class="footer-meta">
    <div>Platform Intelijen Ancaman Siber Mingguan &bull; Diskominfo Provinsi Jawa Timur &bull; On-Premise (Local First)</div>
    <div>Dicetak pada: ${tglCetak} pukul ${jamCetak} WIB</div>
  </div>
</body>
</html>`;

  // Render ke iframe tersembunyi untuk memicu dialog cetak / Simpan sebagai PDF native browser
  const printIframe = document.createElement('iframe');
  printIframe.style.position = 'fixed';
  printIframe.style.right = '0';
  printIframe.style.bottom = '0';
  printIframe.style.width = '0';
  printIframe.style.height = '0';
  printIframe.style.border = 'none';
  document.body.appendChild(printIframe);

  const doc = printIframe.contentWindow.document;
  doc.open();
  doc.write(htmlContent);
  doc.close();

  tampilkanToast('Membuka dialog Simpan sebagai PDF...', 'info');

  printIframe.contentWindow.focus();
  setTimeout(() => {
    try {
      printIframe.contentWindow.print();
    } catch (e) {
      console.error('Print iframe error:', e);
      // Fallback: buka popup window
      const win = window.open('', '_blank');
      if (win) {
        win.document.write(htmlContent);
        win.document.close();
        win.focus();
        win.print();
      }
    }
    setTimeout(() => {
      if (document.body.contains(printIframe)) {
        document.body.removeChild(printIframe);
      }
    }, 2000);
  }, 350);
}
