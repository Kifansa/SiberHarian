with open('src/analytics/cti_agents.py', 'a', encoding='utf-8') as f:
    f.write('''
def _deteksi_sektor_spesifik(teks: str) -> str:
    teks = teks.lower()
    if any(k in teks for k in ['pemerintah', 'pemprov', 'pemkab', 'pemkot', 'dinas']): return 'Sektor Administrasi Pemerintahan'
    if any(k in teks for k in ['sekolah', 'kampus', 'universitas', 'akademik']): return 'Sektor Pendidikan'
    if any(k in teks for k in ['rumah sakit', 'rsud', 'puskesmas', 'medis']): return 'Sektor Kesehatan'
    if any(k in teks for k in ['bank', 'keuangan', 'finansial']): return 'Sektor Keuangan'
    return 'Layanan Publik Daerah'

def _deteksi_senjata_spesifik(teks: str) -> str:
    teks = teks.lower()
    if 'ransomware' in teks: return 'Ransomware / File Encryptor'
    if 'phishing' in teks or 'apk' in teks: return 'Social Engineering & Malware APK'
    if 'deface' in teks or 'judi' in teks or 'slot' in teks: return 'Webshell & Defacement'
    if 'cve' in teks or 'rce' in teks: return 'Eksploitasi Celah Keamanan (RCE)'
    return 'Akses Ilegal & Eksploitasi Web'

def _deteksi_dampak_spesifik(teks: str) -> str:
    teks = teks.lower()
    if 'bocor' in teks or 'breach' in teks or 'dijual' in teks: return 'Kebocoran Data Sensitif'
    if 'lumpuh' in teks or 'down' in teks: return 'Kelumpuhan Layanan Publik'
    if 'enkripsi' in teks or 'tebusan' in teks: return 'Terkuncinya Basis Data Operasional'
    return 'Gangguan Integritas Sistem'

def _buat_fallback_sitrep_deterministik(data_makro: dict, top3_mikro: list, ancaman_baru: dict) -> str:
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    laporan = []
    pola = data_makro.get('nama_pola', 'Ancaman Siber')
    growth = data_makro.get('growth_persen', 0)
    laporan.append('### 1. LANSKAP & POLA ANCAMAN')
    laporan.append(f'- **Peningkatan Aktivitas {pola}**: Terdeteksi peningkatan ancaman sebesar {growth}% dalam seminggu terakhir.')
    laporan.append('\n### 2. VEKTOR SERANGAN & SEKTOR')
    laporan.append('### 3. IMPLIKASI PERSANDIAN & KEAMANAN')
    laporan.append('### 4. REKOMENDASI AKSI')
    for idx, inc in enumerate(top3_mikro):
        nama, _ = _bersihkan_judul_dan_publisher(inc.get('nama_insiden', f'Insiden {idx+1}'), '')
        fakta = inc.get('uraian_fakta', '')
        sektor = _deteksi_sektor_spesifik(fakta)
        senjata = _deteksi_senjata_spesifik(fakta)
        laporan[1] += f'\n- **Target {sektor}**: Menggunakan metode {senjata} pada kasus {nama}.'
        laporan[2] += f'\n- **Risiko Sistem**: {fakta[:150]}...'
        mitigasi = inc.get('mitigasi_ensiklopedia', [])
        if mitigasi:
            laporan[3] += f'\n- **Mitigasi untuk {nama}**: {mitigasi[0]}'
    laporan.append('\n### 5. PREDIKSI ANCAMAN MASA DEPAN')
    if ancaman_baru.get('ada'):
        nama_anc = ancaman_baru.get('nama', 'Ancaman Baru')
        laporan.append(f'- **{nama_anc}**: {ancaman_baru.get("uraian", "")[:200]}')
    else:
        laporan.append('- Tidak ada sinyal ancaman baru yang terdeteksi minggu ini.')
    return '\n'.join(laporan)''')
