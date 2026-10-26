import tempfile
import shutil
import sqlite3

tf = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
tf.close()
shutil.copy2('data/state.db', tf.name)
conn = sqlite3.connect(tf.name)
conn.execute("UPDATE pengaturan SET nilai = '0.5' WHERE kunci = 'gemini.temperature'")
conn.commit()
row = conn.execute("SELECT nilai FROM pengaturan WHERE kunci = 'gemini.temperature'").fetchone()
print("Copy & Write OK:", row)
conn.close()
