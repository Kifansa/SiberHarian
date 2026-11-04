"""Skema, koneksi, dan bootstrap database SQLite aplikasi."""

from contextlib import contextmanager
from datetime import datetime
import os
from pathlib import Path
import sqlite3

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = Path(
    os.getenv("SIBERHARIAN_DB_PATH", str(_ROOT_DIR / "data" / "state.db"))
).expanduser()


def _resolve_active_db_path(db_path: Path) -> Path:
    """
    Menentukan path database aktif secara transparan. Jika db_path merujuk ke path default
    (data/state.db) dan terdapat basis data tersinkronisasi di temp yang lebih baru,
    gunakan path tersebut secara otomatis tanpa merusak database unit test yang independen.
    """
    target = Path(db_path)
    primary = (_ROOT_DIR / "data" / "state.db").resolve()
    target_resolved = target.resolve() if target.exists() else target
    if target_resolved == primary or str(target) == str(DEFAULT_DB_PATH):
        env_path = os.getenv("SIBERHARIAN_DB_PATH")
        if env_path:
            return Path(env_path).expanduser()
        import tempfile
        tmp_db = Path(tempfile.gettempdir()) / "siberharian_sync" / "state.db"
        if tmp_db.exists():
            try:
                if not os.access(primary, os.W_OK) or tmp_db.stat().st_mtime > primary.stat().st_mtime:
                    return tmp_db
            except Exception:
                pass
    return target


@contextmanager
def _koneksi(db_path: Path):
    """Membuka koneksi SQLite dan selalu menutupnya, termasuk saat exception."""
    db_path = _resolve_active_db_path(Path(db_path))
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Membuat tabel dan kolom yang belum ada; aman dipanggil berulang."""
    with _koneksi(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS konten_terkirim (
                identifier TEXT PRIMARY KEY,
                kategori TEXT NOT NULL,
                judul TEXT,
                sumber TEXT,
                tanggal_kirim TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS riwayat_tren (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kategori TEXT NOT NULL,
                identifier TEXT NOT NULL,
                judul TEXT,
                sumber TEXT,
                kata_kunci TEXT,
                kategori_relevansi TEXT,
                severity TEXT,
                vendor TEXT,
                tanggal_publish TEXT,
                tanggal_dicatat TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS prediksi_tren_terakhir (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                prediksi_berita TEXT,
                prediksi_cve TEXT,
                tanggal_dihitung TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata_sistem (
                kunci TEXT PRIMARY KEY,
                nilai TEXT NOT NULL
            )
        """)
        for kolom, tipe in (
            ("ringkasan_atau_narasi", "TEXT"),
            ("link", "TEXT"),
            ("skor_cvss", "REAL"),
            ("produk", "TEXT"),
        ):
            _tambah_kolom_jika_belum_ada(conn, "riwayat_tren", kolom, tipe)
        _tambah_kolom_jika_belum_ada(conn, "prediksi_tren_terakhir", "kasus_wilayah_ai", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "prediksi_tren_terakhir", "statistik_json", "TEXT")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pengaturan (
                kunci TEXT PRIMARY KEY,
                nilai TEXT NOT NULL,
                diubah TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'viewer',
                dibuat TEXT NOT NULL,
                diubah TEXT NOT NULL
            )
        """)
        _seed_admin_awal(conn)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS intelijen_berita_tervalidasi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_identifier TEXT NOT NULL UNIQUE,
                kategori_insiden TEXT NOT NULL,
                confidence_kategori REAL NOT NULL,
                kutipan_bukti_kategori TEXT,
                mitre_tactic TEXT,
                mitre_technique_id TEXT,
                mitre_technique_name TEXT,
                confidence_mitre REAL,
                kutipan_bukti_mitre TEXT,
                d3fend_mitigasi_json TEXT,
                nist_referensi_json TEXT,
                version_taxonomy TEXT NOT NULL,
                version_attack TEXT NOT NULL,
                version_d3fend TEXT NOT NULL,
                version_nist TEXT NOT NULL,
                dibuat_pada TEXT NOT NULL,
                koreksi_admin_kategori TEXT DEFAULT NULL,
                koreksi_admin_technique_id TEXT DEFAULT NULL,
                koreksi_admin_catatan TEXT DEFAULT NULL,
                koreksi_admin_oleh TEXT DEFAULT NULL,
                koreksi_admin_pada TEXT DEFAULT NULL,
                flag_tinjauan TEXT DEFAULT NULL,
                sektor_target TEXT DEFAULT NULL,
                confidence_sektor REAL DEFAULT NULL,
                kutipan_bukti_sektor TEXT DEFAULT NULL,
                alasan_sektor TEXT DEFAULT NULL,
                koreksi_admin_sektor TEXT DEFAULT NULL
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_intelijen_berita_identifier
            ON intelijen_berita_tervalidasi(article_identifier)
        """)
        for kolom, tipe in (
            ("flag_tinjauan", "TEXT"),
            ("sektor_target", "TEXT"),
            ("confidence_sektor", "REAL"),
            ("kutipan_bukti_sektor", "TEXT"),
            ("alasan_sektor", "TEXT"),
            ("koreksi_admin_sektor", "TEXT"),
        ):
            _tambah_kolom_jika_belum_ada(conn, "intelijen_berita_tervalidasi", kolom, tipe)
    logger.info(f"Database state siap di: {db_path}")


def _tambah_kolom_jika_belum_ada(
    conn: sqlite3.Connection, tabel: str, kolom: str, definisi_tipe: str
) -> None:
    kolom_tersedia = {row[1] for row in conn.execute(f"PRAGMA table_info({tabel})")}
    if kolom not in kolom_tersedia:
        conn.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {definisi_tipe}")


def _seed_admin_awal(conn: sqlite3.Connection) -> None:
    """Membuat akun awal hanya untuk database baru; gagal bila kredensial wajib kosong."""
    if conn.execute("SELECT count(*) FROM admin_users").fetchone()[0] > 0:
        return

    import bcrypt

    username = os.getenv("ADMIN_USERNAME", "").strip()
    password = os.getenv("ADMIN_PASSWORD", "")
    if not username or not password:
        raise RuntimeError(
            "Database baru memerlukan ADMIN_USERNAME dan ADMIN_PASSWORD yang tidak kosong."
        )

    sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    conn.execute(
        "INSERT INTO admin_users (username, password, role, dibuat, diubah) VALUES (?, ?, ?, ?, ?)",
        (username, hashed, "superadmin", sekarang, sekarang),
    )

    viewer_password = os.getenv("VIEWER_PASSWORD", "")
    if viewer_password:
        hashed_viewer = bcrypt.hashpw(viewer_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        conn.execute(
            "INSERT INTO admin_users (username, password, role, dibuat, diubah) VALUES (?, ?, ?, ?, ?)",
            ("viewer", hashed_viewer, "viewer", sekarang, sekarang),
        )
