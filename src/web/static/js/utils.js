/**
 * Utility umum dipakai lintas tab (Beranda, Arsip, Tren Siber).
 */
export function escapeHtml(teks) {
  const div = document.createElement('div');
  div.textContent = teks ?? '';
  return div.innerHTML;
}

export function formatTanggalIndonesia(tanggalIso) {
  // tanggalIso format 'YYYY-MM-DD' (bucket tanggal publikasi dari backend)
  if (!tanggalIso || tanggalIso === 'tanggal_tidak_diketahui') return 'Tanggal tidak diketahui';
  const [tahun, bulan, tanggal] = tanggalIso.split('-').map(Number);
  const namaHari = ['Minggu', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu'];
  const namaBulan = ['Jan', 'Feb', 'Mar', 'Apr', 'Mei', 'Jun', 'Jul', 'Agu', 'Sep', 'Okt', 'Nov', 'Des'];
  const tanggalObj = new Date(tahun, bulan - 1, tanggal);
  return `${namaHari[tanggalObj.getDay()]}, ${tanggal} ${namaBulan[bulan - 1]} ${tahun}`;
}

export function formatWaktuSekarang() {
  return new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' }) + ' WIB';
}