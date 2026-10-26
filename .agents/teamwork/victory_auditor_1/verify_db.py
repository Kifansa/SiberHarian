import sqlite3

conn = sqlite3.connect('data/state.db')
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [r[0] for r in cur.fetchall()]
print("Tables in state.db:", tables)

for t in ['d3fend_techniques', 'd3fend_attack_mappings', 'intelijen_berita_tervalidasi']:
    if t in tables:
        cur.execute(f"SELECT count(*) FROM {t}")
        count = cur.fetchone()[0]
        cur.execute(f"PRAGMA table_info({t})")
        cols = [c[1] for c in cur.fetchall()]
        print(f"{t}: count={count}, cols={cols}")
    else:
        print(f"{t}: NOT FOUND!")
conn.close()
