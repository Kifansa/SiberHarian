import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect("data/state.db")
cur = conn.cursor()

official_chain = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]

rate_limits = {
    "gemini-2.5-flash": 5.0,
    "gemini-2.5-flash-lite": 10.0,
    "gemini-3-flash": 5.0,
    "gemini-3.1-flash-lite": 15.0,
    "gemini-3.6-flash": 5.0,
    "gemini-3.5-flash-lite": 15.0,
    "gemini-3.8-flash": 5.0,
    "gemini-embedding-001": 100.0,
    "gemini-embedding-exp-03-07": 100.0,
    "text-embedding-004": 100.0,
}

proactive_thresholds = {
    "gemini-2.5-flash": 4,
    "gemini-2.5-flash-lite": 9,
    "gemini-3-flash": 4,
    "gemini-3.1-flash-lite": 14,
    "gemini-3.6-flash": 4,
    "gemini-3.5-flash-lite": 14,
    "gemini-3.8-flash": 4,
    "gemini-embedding-001": 90,
    "gemini-embedding-exp-03-07": 90,
    "text-embedding-004": 90,
}

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

cur.execute("UPDATE pengaturan SET nilai = ?, diubah = ? WHERE kunci = 'gemini.model_chain'", (json.dumps(official_chain), now))
cur.execute("UPDATE pengaturan SET nilai = ?, diubah = ? WHERE kunci = 'gemini.rate_limits'", (json.dumps(rate_limits), now))
cur.execute("UPDATE pengaturan SET nilai = ?, diubah = ? WHERE kunci = 'gemini.proactive_thresholds'", (json.dumps(proactive_thresholds), now))

conn.commit()

# Verify
cur.execute("SELECT kunci, nilai FROM pengaturan WHERE kunci IN ('gemini.model_chain', 'gemini.rate_limits', 'gemini.proactive_thresholds')")
for k, v in cur.fetchall():
    print(k, "=>", json.loads(v))

conn.close()
