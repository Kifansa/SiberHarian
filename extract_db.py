import os
import yaml

base_dir = r'D:\penting\magang\kominfo\NOTIFIKASI-BERITA'
rules_dir = os.path.join(base_dir, 'config', 'rules')

publik_statistik = {
    "kategori_map": {
        "Phishing & Link Palsu": {
            "keywords": ["phishing", "penipuan online", "penipuan digital", "situs palsu", "social engineering"],
            "icon": "link_off",
            "desc": "Tautan jebakan yang menyamar sebagai instansi/bank untuk mencuri password & data."
        },
        "Judi Online & Defacement": {
            "keywords": ["judi online", "slot", "deface", "hacked by", "situs diretas"],
            "icon": "casino",
            "desc": "Penyusupan ke halaman web pemerintah/kampus untuk disisipi iklan ilegal."
        },
        "Ransomware & Malware": {
            "keywords": ["ransomware", "malware", "virus", "tebusan", "brain cipher", "jadepuffer"],
            "icon": "pest_control",
            "desc": "Program jahat yang menyandera file atau merusak sistem komputer."
        },
        "Pencurian Data Pribadi": {
            "keywords": ["bocor", "data pribadi", "breach", "dijual", "dark web", "dukcapil"],
            "icon": "fingerprint",
            "desc": "Penyalahgunaan dan penjualan data kependudukan tanpa izin."
        },
        "Penipuan Modus APK": {
            "keywords": ["apk", "surat tilang", "undangan", "kurir", "whatsapp", "infostealer"],
            "icon": "app_blocking",
            "desc": "Pencurian akses M-Banking dan OTP lewat aplikasi palsu di HP."
        },
        "Kerentanan Sistem (CVE)": {
            "keywords": ["cve", "0-day", "rce", "kerentanan", "celah keamanan"],
            "icon": "bug_report",
            "desc": "Kelemahan pada sistem operasi, website, atau software yang belum diperbarui."
        }
    },
    "stop_words": [
        "sistem", "situs", "jaringan", "server", "aplikasi", "website", 
        "dicuri", "bocor", "diretas", "online", "terkini", "baru"
    ],
    "kpi_insights": [
        {"title": "Prioritas Waspada Masyarakat", "desc": "Serangan Social Engineering via Chat", "value": "Akun & Phishing", "icon": "warning"},
        {"title": "Temuan Celah Sistem Nasional", "desc": "Didominasi Keterlambatan Pembaruan (Patch)", "value": "60% Isu Nasional", "icon": "security_update_warning"}
    ]
}

with open(os.path.join(rules_dir, 'publik_statistik.yaml'), 'w', encoding='utf-8') as f:
    yaml.dump(publik_statistik, f, sort_keys=False)

print('publik_statistik rule dumped')
