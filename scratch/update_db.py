import sqlite3
import json

conn = sqlite3.connect('data/state.db')
models = [
    'gemini-2.5-flash',
    'gemini-2.5-flash-lite',
    'gemini-3-flash',
    'gemini-3.1-flash-lite',
    'gemini-3.6-flash',
    'gemini-3.5-flash-lite',
    'gemini-3.8-flash'
]
conn.execute("UPDATE pengaturan SET nilai = ?, diubah = datetime('now') WHERE kunci = 'gemini.model_chain'", (json.dumps(models),))

# Also ensure rate limits and proactive thresholds are fully updated
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
    "text-embedding-004": 100.0
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
    "text-embedding-004": 90
}
conn.execute("UPDATE pengaturan SET nilai = ?, diubah = datetime('now') WHERE kunci = 'gemini.rate_limits'", (json.dumps(rate_limits),))
conn.execute("UPDATE pengaturan SET nilai = ?, diubah = datetime('now') WHERE kunci = 'gemini.proactive_thresholds'", (json.dumps(proactive_thresholds),))

conn.commit()
conn.close()
print("Database state.db synced successfully!")
