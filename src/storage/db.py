"""
Modul penyimpanan state persisten menggunakan SQLite. Menyimpan histori
artikel & CVE yang sudah pernah dikirim ke channel notifikasi, supaya
pipeline yang jalan otomatis tiap hari tidak mengirim ulang konten yang
sama meskipun RSS/API sumber terlambat update atau di-scrape ulang.
"""
import pandas as pd
import sqlite3
from collections import OrderedDict
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "state.db"


@contextmanager
def _koneksi(db_path: Path):
    """Context manager supaya koneksi SQLite selalu ditutup dengan benar, termasuk saat exception."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Membuat tabel jika belum ada. Aman dipanggil berkali-kali (idempotent)."""
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
        # Migrasi ringan: kolom baru untuk kebutuhan tab Arsip (ringkasan
        # lengkap & link) - ditambahkan belakangan setelah tabel riwayat_tren
        # sudah ada sebelumnya untuk kebutuhan tren saja.
        _tambah_kolom_jika_belum_ada(conn, "riwayat_tren", "ringkasan_atau_narasi", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "riwayat_tren", "link", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "riwayat_tren", "skor_cvss", "REAL")
    logger.info(f"Database state siap di: {db_path}")

def ambil_identifier_terkirim(kategori: str, db_path: Path = DEFAULT_DB_PATH) -> set:
    """
    Mengambil seluruh identifier (URL untuk berita, cve_id untuk CVE)
    yang sudah pernah tercatat terkirim untuk kategori tertentu.
    Dipanggil sekali di awal pipeline harian untuk keperluan filter cepat.
    """
    with _koneksi(db_path) as conn:
        cursor = conn.execute(
            "SELECT identifier FROM konten_terkirim WHERE kategori = ?", (kategori,)
        )
        return {row[0] for row in cursor.fetchall()}


def catat_terkirim(
    identifiers: List[dict], kategori: str, db_path: Path = DEFAULT_DB_PATH
) -> None:
    """
    Mencatat konten yang baru saja berhasil dikirim, supaya tidak
    terkirim ulang di hari-hari berikutnya. Dipanggil SETELAH notifikasi
    berhasil terkirim (bukan sebelum), supaya kalau pengiriman gagal,
    konten tersebut tetap dicoba lagi di run berikutnya.

    identifiers: list of dict dengan key 'identifier', 'judul', 'sumber'.
    """
    tanggal_kirim = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _koneksi(db_path) as conn:
        for item in identifiers:
            conn.execute(
                """
                INSERT OR IGNORE INTO konten_terkirim
                (identifier, kategori, judul, sumber, tanggal_kirim)
                VALUES (?, ?, ?, ?, ?)
                """,
                (item["identifier"], kategori, item.get("judul", ""), item.get("sumber", ""), tanggal_kirim),
            )
    logger.info(f"Mencatat {len(identifiers)} item kategori '{kategori}' sebagai sudah terkirim.")


def bersihkan_histori_lama(hari_retensi: int = 90, db_path: Path = DEFAULT_DB_PATH) -> None:
    """
    Menghapus catatan yang lebih tua dari N hari, supaya database tidak
    membengkak tanpa batas. Dipanggil berkala (misal mingguan), bukan
    tiap run harian.
    """
    with _koneksi(db_path) as conn:
        cursor = conn.execute(
            f"DELETE FROM konten_terkirim WHERE tanggal_kirim < datetime('now', '-{hari_retensi} days')"
        )
        logger.info(f"Membersihkan {cursor.rowcount} catatan histori yang lebih tua dari {hari_retensi} hari.")

# fungsi baru di db.py
def catat_untuk_tren(items: List[dict], db_path: Path = DEFAULT_DB_PATH) -> None:
    tanggal_dicatat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _koneksi(db_path) as conn:
        for item in items:
            conn.execute(
                """
                INSERT INTO riwayat_tren
                (kategori, identifier, judul, sumber, kata_kunci, kategori_relevansi,
                 severity, vendor, tanggal_publish, tanggal_dicatat, ringkasan_atau_narasi, link, skor_cvss)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (item["kategori"], item["identifier"], item.get("judul", ""), item.get("sumber", ""),
                 item.get("kata_kunci", ""), item.get("kategori_relevansi", ""),
                 item.get("severity", ""), item.get("vendor", ""),
                 item.get("tanggal_publish", ""), tanggal_dicatat,
                 item.get("ringkasan_atau_narasi", ""), item.get("link", ""),
                 item.get("skor_cvss")),
            )
    logger.info(f"Mencatat {len(items)} item ke riwayat_tren (termasuk ringkasan untuk Arsip).")


def ambil_riwayat_tren(hari: int = 7, db_path: Path = DEFAULT_DB_PATH) -> "pd.DataFrame":
    """Mengambil seluruh riwayat dalam N hari terakhir untuk dianalisis trennya."""
    import pandas as pd
    with _koneksi(db_path) as conn:
        return pd.read_sql_query(
            f"SELECT * FROM riwayat_tren WHERE tanggal_dicatat >= datetime('now', '-{hari} days')",
            conn,
        )


def bersihkan_riwayat_tren_lama(hari_retensi: int = 7, db_path: Path = DEFAULT_DB_PATH) -> None:
    """Membuang data tren yang lebih tua dari window (default 7 hari).
    Dipanggil TIAP RUN (bukan mingguan), supaya window tren selalu 'bergeser' harian."""
    with _koneksi(db_path) as conn:
        cursor = conn.execute(
            f"DELETE FROM riwayat_tren WHERE tanggal_dicatat < datetime('now', '-{hari_retensi} days')"
        )
        logger.info(f"Membersihkan {cursor.rowcount} baris riwayat_tren yang lebih tua dari {hari_retensi} hari.")

def _tambah_kolom_jika_belum_ada(conn: sqlite3.Connection, tabel: str, kolom: str, definisi_tipe: str) -> None:
    """Menambahkan kolom baru ke tabel yang sudah ada, idempotent (aman
    dipanggil berkali-kali) - migrasi skema ringan tanpa tool terpisah."""
    cursor = conn.execute(f"PRAGMA table_info({tabel})")
    kolom_ada = {row[1] for row in cursor.fetchall()}
    if kolom not in kolom_ada:
        conn.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {definisi_tipe}")

def ambil_riwayat_dikelompokkan_per_hari(hari: int = 7, db_path: Path = DEFAULT_DB_PATH) -> "OrderedDict":
    """
    Mengambil riwayat_tren dan mengelompokkannya PER TANGGAL PUBLIKASI
    artikel (bukan tanggal pipeline dijalankan), dipisah lagi per kategori
    (berita/cve). Dikelompokkan berdasarkan tanggal_publish supaya satu run
    scraping besar (mis. window 7 hari) langsung terdistribusi ke hari yang
    benar - bukan numpuk di satu hari berdasarkan kapan pipeline dijalankan.

    Returns: OrderedDict terurut dari tanggal TERBARU ke TERLAMA, contoh:
        {"2026-08-19": {"berita": [...], "cve": [...]}, "2026-08-18": {...}, ...}
    """
    from collections import OrderedDict

    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            f"""
            SELECT * FROM riwayat_tren
            WHERE tanggal_publish >= datetime('now', '-{hari} days')
            ORDER BY tanggal_publish DESC
            """
        )
        baris = [dict(row) for row in cursor.fetchall()]

    hasil: "OrderedDict" = OrderedDict()
    for item in baris:
        tanggal_publish = item.get("tanggal_publish") or ""
        tanggal_bucket = tanggal_publish[:10] if len(tanggal_publish) >= 10 else "tanggal_tidak_diketahui"

        if tanggal_bucket not in hasil:
            hasil[tanggal_bucket] = {"berita": [], "cve": []}

        if item["kategori"] == "berita":
            hasil[tanggal_bucket]["berita"].append({
                "sumber": item["sumber"],
                "judul": item["judul"],
                "tanggal": item["tanggal_publish"],
                "ringkasan": item["ringkasan_atau_narasi"],
                "link": item["link"],
                "kategori": item["kategori_relevansi"],
            })
        elif item["kategori"] == "cve":
            hasil[tanggal_bucket]["cve"].append({
                "vendor": item["vendor"],
                "cve_id": item["identifier"],
                "severity": item["severity"],
                "skor_cvss": item["skor_cvss"],
                "narasi": item["ringkasan_atau_narasi"],
                "link": item["link"],
            })

    return hasil

def simpan_prediksi_tren(prediksi_berita: str, prediksi_cve: str, db_path: Path = DEFAULT_DB_PATH) -> None:
    """Menyimpan/menimpa prediksi tren terakhir (selalu 1 baris saja)."""
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _koneksi(db_path) as conn:
        conn.execute(
            """
            INSERT INTO prediksi_tren_terakhir (id, prediksi_berita, prediksi_cve, tanggal_dihitung)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                prediksi_berita = excluded.prediksi_berita,
                prediksi_cve = excluded.prediksi_cve,
                tanggal_dihitung = excluded.tanggal_dihitung
            """,
            (prediksi_berita, prediksi_cve, tanggal),
        )
    logger.info("Prediksi tren terakhir disimpan ke database.")


def ambil_prediksi_tren_terakhir(db_path: Path = DEFAULT_DB_PATH) -> Optional[dict]:
    """Mengambil prediksi tren terakhir. None kalau belum pernah dihitung sama sekali."""
    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM prediksi_tren_terakhir WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else None