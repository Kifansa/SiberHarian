import sqlite3
import json

conn = sqlite3.connect('data/state.db')
c = conn.cursor()
tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('TABLES:', tables)

for t in tables:
    cnt = c.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
    cols = [r[1] + ' (' + r[2] + ')' for r in c.execute(f"PRAGMA table_info({t})").fetchall()]
    print(f"\n--- TABLE {t} (count: {cnt}) ---")
    print("COLUMNS:", ", ".join(cols))

print("\n--- KATEGORI DISTRIBUTION IN riwayat_tren ---")
for row in c.execute("SELECT kategori, count(*) FROM riwayat_tren GROUP BY kategori").fetchall():
    print(row)

print("\n--- KATEGORI_RELEVANSI DISTRIBUTION IN riwayat_tren ---")
for row in c.execute("SELECT kategori_relevansi, count(*) FROM riwayat_tren GROUP BY kategori_relevansi").fetchall():
    print(row)

print("\n--- SAMPLE 3 ROWS FROM riwayat_tren ---")
for r in c.execute("SELECT id, kategori, judul, sumber, kategori_relevansi, tanggal_publish, substr(ringkasan_atau_narasi, 1, 100), link FROM riwayat_tren LIMIT 3").fetchall():
    print(r)

print("\n--- PREDIKSI_TREN_TERAKHIR COLUMNS & LENGTHS ---")
for r in c.execute("SELECT id, tanggal_dihitung, length(prediksi_berita), length(prediksi_cve), length(kasus_wilayah_ai), length(statistik_json) FROM prediksi_tren_terakhir").fetchall():
    print(r)

print("\n--- METADATA_SISTEM ---")
for r in c.execute("SELECT kunci, nilai FROM metadata_sistem").fetchall():
    print(r)

print("\n--- PENGATURAN ---")
for r in c.execute("SELECT kunci, diubah FROM pengaturan").fetchall():
    print(r)

conn.close()

import os
print("\n--- ROOT state.db CHECK ---")
if os.path.exists("state.db"):
    print("root state.db size:", os.path.getsize("state.db"))
    c2 = sqlite3.connect("state.db").cursor()
    print("root tables:", [r[0] for r in c2.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()])
    for t in ["konten_terkirim", "riwayat_tren"]:
        try:
            print(f"root {t} count:", c2.execute(f"SELECT count(*) FROM {t}").fetchone()[0])
        except Exception as e:
            print(e)
    c2.close()

