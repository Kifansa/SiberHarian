import sqlite3
import json

conn = sqlite3.connect("data/state.db")
cur = conn.cursor()
cur.execute("SELECT kunci, nilai FROM pengaturan WHERE kunci LIKE 'gemini%'")
rows = cur.fetchall()
for k, v in rows:
    try:
        parsed = json.loads(v)
        print(f"[{k}] => {parsed}")
    except Exception:
        print(f"[{k}] => {v}")
conn.close()
