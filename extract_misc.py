import os
import yaml

base_dir = r'D:\penting\magang\kominfo\NOTIFIKASI-BERITA'
rules_dir = os.path.join(base_dir, 'config', 'rules')

kategori = [
    {
        "id": "ransomware",
        "kategori": "Ransomware & Pemerasan",
        "ikon": "lock",
        "warna": "red",
        "keywords": ["ransomware", "tebusan", "pemerasan", "encryptor", "jadepuffer"],
        "fokus_website": "Pencegahan enkripsi basis data web, server cadangan, dan pemerasan data OPD.",
        "tindakan_taktis": "Isolasi database dari akses publik langsung, aktifkan immutable offline backup, dan perketat MFA.",
    },
    {
        "id": "defacement_rce",
        "kategori": "Web Defacement & Celah RCE",
        "ikon": "web",
        "warna": "amber",
        "keywords": ["deface", "defacement", "rce", "exploit", "celah", "vulnerability", "bypass", "web shell", "diretas", "hacked"],
        "fokus_website": "Perlindungan integritas halaman web, portal dinas, dan pencegahan backdoor/judi online.",
        "tindakan_taktis": "Nonaktifkan eksekusi PHP di folder upload (/uploads), terapkan WAF rule, dan update plugin/CMS.",
    },
    {
        "id": "phishing_kredensial",
        "kategori": "Pencurian Akun & Phishing",
        "ikon": "badge",
        "warna": "blue",
        "keywords": ["phishing", "kredensial", "credential", "password", "akun", "login", "otp", "rekayasa sosial", "stealer", "infostealer"],
        "fokus_website": "Mencegah pengambilalihan akun admin cPanel/CMS website melalui kebocoran kredensial staf.",
        "tindakan_taktis": "Wajibkan 2FA pada panel admin, batasi login admin dengan IP Whitelist, dan rotasi password berkala.",
    },
    {
        "id": "kebocoran_data",
        "kategori": "Kebocoran Data & Database Dump",
        "ikon": "database",
        "warna": "purple",
        "keywords": ["kebocoran data", "data bocor", "pencurian data", "data dijual", "breach", "dark web", "nik", "ktp", "dukcapil"],
        "fokus_website": "Mencegah eksfiltrasi data warga dan data operasional dari database layanan publik.",
        "tindakan_taktis": "Audit endpoint API publik, aktifkan enkripsi at-rest/in-transit, dan cegah akses open dump SQL.",
    }
]

with open(os.path.join(rules_dir, 'kategori_ancaman.yaml'), 'w', encoding='utf-8') as f:
    yaml.dump(kategori, f, sort_keys=False)

normalisasi = {
    "Ransomware & Pemerasan Siber": ["ransomware", "lockbit", "brain cipher", "jadepuffer", "enkripsi", "tebusan"],
    "Eksploitasi Celah Keamanan (CVE)": ["cve", "rce", "0-day", "zero-day", "kerentanan", "vulnerability"],
    "Web Defacement & Judi Online": ["deface", "judi online", "slot gacor", "hacked by", "diretas"],
    "Kebocoran Data Pribadi": ["bocor", "dark web", "breach", "leak", "nik", "data ktp", "dijual"],
    "Phishing & Pencurian Kredensial": ["phishing", "stealer", "kredensial", "akun", "otp", "apk palsu"]
}

with open(os.path.join(rules_dir, 'normalisasi_isu.yaml'), 'w', encoding='utf-8') as f:
    yaml.dump(normalisasi, f, sort_keys=False)

print('Kategori and normalisasi dumped')
