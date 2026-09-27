import sqlite3
from pathlib import Path
import bcrypt
from typing import Optional, Tuple
from src.storage.db import DEFAULT_DB_PATH, init_db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

def verifikasi_admin(username: str, password: str) -> Tuple[bool, str]:
    """
    Verifikasi kredensial admin terhadap hash bcrypt di database.
    Returns: (is_valid, role)
    """
    init_db(DEFAULT_DB_PATH)
    try:
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        row = conn.execute(
            "SELECT password, role FROM admin_users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        if row:
            hashed = row[0].encode("utf-8")
            role = row[1]
            if bcrypt.checkpw(password.encode("utf-8"), hashed):
                return True, role
    except Exception as e:
        logger.error(f"Gagal verifikasi admin: {e}")
    return False, ""

def ubah_password_admin(username: str, password_baru: str) -> bool:
    """Mengubah password admin (dipanggil dari settings panel)."""
    from datetime import datetime
    init_db(DEFAULT_DB_PATH)
    try:
        hashed = bcrypt.hashpw(password_baru.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        conn.execute(
            "UPDATE admin_users SET password = ?, diubah = ? WHERE username = ?",
            (hashed, sekarang, username)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Gagal ubah password: {e}")
        return False

def get_admin_user(username: str) -> Optional[dict]:
    """Mengambil informasi admin dari database berdasarkan username."""
    init_db(DEFAULT_DB_PATH)
    try:
        conn = sqlite3.connect(DEFAULT_DB_PATH)
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT id, username, role FROM admin_users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        logger.error(f"Gagal mengambil user admin: {e}")
        return None
