import sqlite3
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

conn = sqlite3.connect("data/state.db")
cur = conn.cursor()
cur.execute("SELECT kunci, nilai FROM pengaturan ORDER BY kunci")
for k, v in cur.fetchall():
    try:
        parsed = json.loads(v)
        preview = str(parsed)[:80]
    except Exception:
        preview = v.replace("\n", " ")[:80]
    print(f"{k}: {preview}")
conn.close()
