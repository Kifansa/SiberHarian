import sqlite3
try:
    conn = sqlite3.connect("data/state.db")
    conn.execute("UPDATE pengaturan SET diubah=diubah WHERE kunci='gemini.temperature'")
    conn.commit()
    print("Direct write to state.db succeeded!")
    conn.close()
except Exception as e:
    print("Direct write to state.db failed:", e)
