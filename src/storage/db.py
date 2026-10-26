"""
Modul penyimpanan state persisten menggunakan SQLite. Menyimpan histori
artikel insiden & intelijen yang sudah pernah dikirim ke channel notifikasi, supaya
pipeline yang jalan otomatis tiap hari tidak mengirim ulang konten yang
sama meskipun RSS sumber terlambat update atau di-scrape ulang.
"""
import json
import pandas as pd
import sqlite3
from src.utils.config_loader import ConfigLoader
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict, Any

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
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata_sistem (
                kunci TEXT PRIMARY KEY,
                nilai TEXT NOT NULL
            )
        """)
        # Migrasi ringan: kolom baru untuk kebutuhan tab Arsip (ringkasan
        # lengkap & link) - ditambahkan belakangan setelah tabel riwayat_tren
        # sudah ada sebelumnya untuk kebutuhan tren saja.
        _tambah_kolom_jika_belum_ada(conn, "riwayat_tren", "ringkasan_atau_narasi", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "riwayat_tren", "link", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "riwayat_tren", "skor_cvss", "REAL")
        _tambah_kolom_jika_belum_ada(conn, "riwayat_tren", "produk", "TEXT")
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
        _seed_admin_default(conn)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS d3fend_techniques (
                technique_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                tactic TEXT NOT NULL,
                definition TEXT,
                source_version TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS d3fend_attack_mappings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attack_technique_id TEXT NOT NULL,
                d3fend_technique_id TEXT NOT NULL,
                relationship_type TEXT DEFAULT 'mitigates',
                source_version TEXT NOT NULL,
                FOREIGN KEY (d3fend_technique_id) REFERENCES d3fend_techniques(technique_id)
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_d3fend_attack_lookup 
            ON d3fend_attack_mappings(attack_technique_id)
        """)
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_d3fend_mapping_unique
            ON d3fend_attack_mappings(attack_technique_id, d3fend_technique_id, relationship_type)
        """)
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
        _tambah_kolom_jika_belum_ada(conn, "intelijen_berita_tervalidasi", "flag_tinjauan", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "intelijen_berita_tervalidasi", "sektor_target", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "intelijen_berita_tervalidasi", "confidence_sektor", "REAL")
        _tambah_kolom_jika_belum_ada(conn, "intelijen_berita_tervalidasi", "kutipan_bukti_sektor", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "intelijen_berita_tervalidasi", "alasan_sektor", "TEXT")
        _tambah_kolom_jika_belum_ada(conn, "intelijen_berita_tervalidasi", "koreksi_admin_sektor", "TEXT")
    logger.info(f"Database state siap di: {db_path}")

def _seed_admin_default(conn):
    """Seed akun admin default jika tabel kosong."""
    row = conn.execute("SELECT count(*) FROM admin_users").fetchone()
    if row[0] == 0:
        import os
        import bcrypt
        # Buat superadmin default
        username = os.getenv("ADMIN_USERNAME", "admin")
        password = os.getenv("ADMIN_PASSWORD", "csirtjatim")
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute(
            "INSERT INTO admin_users (username, password, role, dibuat, diubah) VALUES (?, ?, ?, ?, ?)",
            (username, hashed, "superadmin", sekarang, sekarang)
        )
        # Buat viewer default
        hashed_viewer = bcrypt.hashpw(b"viewer123", bcrypt.gensalt()).decode("utf-8")
        conn.execute(
            "INSERT INTO admin_users (username, password, role, dibuat, diubah) VALUES (?, ?, ?, ?, ?)",
            ("viewer", hashed_viewer, "viewer", sekarang, sekarang)
        )


def ambil_identifier_terkirim(kategori: str, db_path: Path = DEFAULT_DB_PATH) -> set:
    """
    Mengambil seluruh identifier (URL artikel)
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


def catat_untuk_tren(items: List[dict], db_path: Path = DEFAULT_DB_PATH) -> None:
    tanggal_dicatat = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _koneksi(db_path) as conn:
        for item in items:
            conn.execute(
                """
                INSERT INTO riwayat_tren
                (kategori, identifier, judul, sumber, kata_kunci, kategori_relevansi,
                 severity, vendor, tanggal_publish, tanggal_dicatat, ringkasan_atau_narasi, link, skor_cvss, produk)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (item["kategori"], item["identifier"], item.get("judul", ""), item.get("sumber", ""),
                 item.get("kata_kunci", ""), item.get("kategori_relevansi", ""),
                 item.get("severity", ""), item.get("vendor", ""),
                 item.get("tanggal_publish", ""), tanggal_dicatat,
                 item.get("ringkasan_atau_narasi", ""), item.get("link", ""),
                 item.get("skor_cvss"), item.get("produk", "")),
            )
    logger.info(f"Mencatat {len(items)} item ke riwayat_tren (termasuk ringkasan untuk Arsip).")


def ambil_riwayat_tren(hari: int = 14, db_path: Path = DEFAULT_DB_PATH) -> "pd.DataFrame":
    """Mengambil riwayat dalam N tanggal unik publikasi terakhir untuk dianalisis trennya."""
    with _koneksi(db_path) as conn:
        df = pd.read_sql_query(
            "SELECT * FROM riwayat_tren ORDER BY tanggal_publish DESC",
            conn,
        )
        if df.empty:
            return df
        df_temp_tgl = df["tanggal_publish"].fillna("").astype(str).str.slice(0, 10)
        tanggal_unik_terbaru = df_temp_tgl[df_temp_tgl.str.match(r"^\d{4}-\d{2}-\d{2}$")].unique()[:hari]
        return df[df_temp_tgl.isin(tanggal_unik_terbaru)].copy()


def bersihkan_riwayat_tren_lama(hari_retensi: int = 14, db_path: Path = DEFAULT_DB_PATH) -> None:
    """Membuang data tren yang lebih tua dari window retensi berdasarkan tanggal_publish.
    Dipanggil TIAP RUN (bukan mingguan), supaya window tren selalu 'bergeser' harian."""
    with _koneksi(db_path) as conn:
        cursor = conn.execute(
            f"DELETE FROM riwayat_tren WHERE tanggal_publish < datetime('now', '-{hari_retensi} days')"
        )
        logger.info(f"Membersihkan {cursor.rowcount} baris riwayat_tren yang lebih tua dari {hari_retensi} hari.")


def _tambah_kolom_jika_belum_ada(conn: sqlite3.Connection, tabel: str, kolom: str, definisi_tipe: str) -> None:
    """Menambahkan kolom baru ke tabel yang sudah ada, idempotent (aman
    dipanggil berkali-kali) - migrasi skema ringan tanpa tool terpisah."""
    cursor = conn.execute(f"PRAGMA table_info({tabel})")
    kolom_ada = {row[1] for row in cursor.fetchall()}
    if kolom not in kolom_ada:
        conn.execute(f"ALTER TABLE {tabel} ADD COLUMN {kolom} {definisi_tipe}")

def ambil_riwayat_dikelompokkan_per_hari(hari: int = 14, db_path: Path = DEFAULT_DB_PATH) -> dict:
    """
    Mengambil riwayat_tren dan mengelompokkannya PER TANGGAL PUBLIKASI
    artikel (bukan tanggal pipeline dijalankan). Dikelompokkan berdasarkan tanggal_publish
    supaya satu run scraping besar langsung terdistribusi ke hari yang
    benar - bukan numpuk di satu hari berdasarkan kapan pipeline dijalankan.

    Returns: dict terurut dari tanggal TERBARU ke TERLAMA, contoh:
        {"2026-08-19": {"berita": [...]}, "2026-08-18": {...}, ...}
    """
    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT * FROM riwayat_tren
            ORDER BY tanggal_publish DESC
            """
        )
        baris = [dict(row) for row in cursor.fetchall()]

    hasil: dict = {}
    for item in baris:
        tanggal_publish = item.get("tanggal_publish") or ""
        tanggal_bucket = tanggal_publish[:10] if len(tanggal_publish) >= 10 else "tanggal_tidak_diketahui"

        if tanggal_bucket not in hasil:
            hasil[tanggal_bucket] = {"berita": []}

        if item["kategori"] == "berita":
            hasil[tanggal_bucket]["berita"].append({
                "sumber": item["sumber"],
                "judul": item["judul"],
                "tanggal": item["tanggal_publish"],
                "ringkasan": item["ringkasan_atau_narasi"],
                "link": item["link"],
                "kategori": item["kategori_relevansi"],
            })

    hasil = dict(list(hasil.items())[:hari])
    return hasil

def simpan_prediksi_tren(
    prediksi_berita: str,
    db_path: Path = DEFAULT_DB_PATH,
    *,
    kasus_wilayah_ai: Optional[str] = None,
    statistik_json: Optional[str] = None,
    prediksi_cve: str = "",
) -> None:
    """Menyimpan/menimpa prediksi tren terakhir (selalu 1 baris saja) beserta analisis kasus wilayah AI dan statistik dashboard."""
    tanggal = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _koneksi(db_path) as conn:
        conn.execute(
            """
            INSERT INTO prediksi_tren_terakhir (id, prediksi_berita, prediksi_cve, tanggal_dihitung, kasus_wilayah_ai, statistik_json)
            VALUES (1, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                prediksi_berita = excluded.prediksi_berita,
                prediksi_cve = excluded.prediksi_cve,
                tanggal_dihitung = excluded.tanggal_dihitung,
                kasus_wilayah_ai = coalesce(excluded.kasus_wilayah_ai, prediksi_tren_terakhir.kasus_wilayah_ai),
                statistik_json = coalesce(excluded.statistik_json, prediksi_tren_terakhir.statistik_json)
            """,
            (prediksi_berita, prediksi_cve, tanggal, kasus_wilayah_ai, statistik_json),
        )
    logger.info("Prediksi tren terakhir (termasuk kasus wilayah AI & statistik dashboard) disimpan ke database.")


def ambil_prediksi_tren_terakhir(db_path: Path = DEFAULT_DB_PATH) -> Optional[dict]:
    """Mengambil prediksi tren terakhir. None kalau belum pernah dihitung sama sekali."""
    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM prediksi_tren_terakhir WHERE id = 1")
        row = cursor.fetchone()
        return dict(row) if row else None

def simpan_metadata(kunci: str, nilai: str, db_path: Path = DEFAULT_DB_PATH) -> None:
    """Menyimpan atau memperbarui pasangan key-value metadata sistem."""
    with _koneksi(db_path) as conn:
        conn.execute(
            """
            INSERT INTO metadata_sistem (kunci, nilai)
            VALUES (?, ?)
            ON CONFLICT(kunci) DO UPDATE SET nilai = excluded.nilai
            """,
            (kunci, nilai),
        )


def ambil_metadata(kunci: str, db_path: Path = DEFAULT_DB_PATH) -> Optional[str]:
    """Mengambil nilai metadata sistem berdasarkan kunci."""
    with _koneksi(db_path) as conn:
        cursor = conn.execute("SELECT nilai FROM metadata_sistem WHERE kunci = ?", (kunci,))
        row = cursor.fetchone()
        return row[0] if row else None


def ambil_waktu_terakhir_scraping(db_path: Path = DEFAULT_DB_PATH) -> Optional[str]:
    """
    Mengambil timestamp terakhir kali scraping / pipeline dijalankan.
    Mengecek metadata_sistem terlebih dahulu, kemudian fallback ke riwayat_tren / konten_terkirim.
    """
    meta = ambil_metadata("waktu_terakhir_scraping", db_path)
    if meta:
        return meta
    with _koneksi(db_path) as conn:
        cursor = conn.execute("SELECT MAX(tanggal_dicatat) FROM riwayat_tren")
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        cursor = conn.execute("SELECT MAX(tanggal_kirim) FROM konten_terkirim")
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
    return None


def ambil_data_terbaru_per_kategori(hari: int = 7, db_path: Path = DEFAULT_DB_PATH) -> dict:
    """
    Data untuk Beranda mengambil kelompok berita terbaru dari database.
    """
    grup_per_tanggal = ambil_riwayat_dikelompokkan_per_hari(hari, db_path)  # sudah urut terbaru -> terlama

    tanggal_berita, daftar_berita = None, []

    for tanggal, isi in grup_per_tanggal.items():
        if tanggal_berita is None and isi.get("berita"):
            tanggal_berita, daftar_berita = tanggal, isi["berita"]
            break

    waktu_scraping = ambil_waktu_terakhir_scraping(db_path)

    return {
        "tanggal_berita": tanggal_berita,
        "berita": daftar_berita,
        "waktu_terakhir_scraping": waktu_scraping,
    }


def ambil_statistik_publik(db_path: Path = DEFAULT_DB_PATH) -> dict:
    """
    Menghitung agregat statistik publik berbasis 100% fakta empiris dari database.
    Mencakup:
    - 4 KPI Insightful (bukan angka polos, melainkan kesimpulan fakta bermakna bagi warga)
    - Word Cloud kasus insiden siber nyata (filter kategori_relevansi = 'insiden_spesifik')
    - Daftar intisari artikel edukasi siber nyata (kategori_relevansi = 'analisis_relevan')
    - Top ancaman populer, software terdampak, fluktuasi harian, dan sebaran media
    """
    with _koneksi(db_path) as conn:
        cur = conn.cursor()

        # 1. Hitung Dasar
        total_berita = cur.execute("SELECT count(*) FROM riwayat_tren WHERE kategori = 'berita'").fetchone()[0] or 1
        total_edukasi = cur.execute("SELECT count(*) FROM riwayat_tren WHERE kategori_relevansi = 'analisis_relevan'").fetchone()[0]

        # 2. Distribusi Kategori Ancaman Populer & Growth Pekanan (vs Pekan Lalu)
        from src.analytics.trend_analyzer import _hitung_growth

        # Bagi rentang waktu: 7 tanggal unik terkini (pekan ini) vs 7 tanggal unik sebelumnya (pekan lalu)
        rows_tgl = cur.execute("""
            SELECT DISTINCT substr(tanggal_publish, 1, 10) as tgl 
            FROM riwayat_tren 
            WHERE kategori = 'berita' AND tgl IS NOT NULL AND tgl != '' 
            ORDER BY tgl DESC
        """).fetchall()
        tanggal_unik = [r[0] for r in rows_tgl]
        tgl_terkini = set(tanggal_unik[:7])
        tgl_baseline = set(tanggal_unik[7:14])

        kategori_map = ConfigLoader.get_rules("publik_statistik").get("kategori_map", {})

        ancaman_counts = {k: 0 for k in kategori_map}
        ancaman_terkini = {k: 0 for k in kategori_map}
        ancaman_baseline = {k: 0 for k in kategori_map}

        rows_berita = cur.execute("""
            SELECT judul, kata_kunci, substr(tanggal_publish, 1, 10) 
            FROM riwayat_tren 
            WHERE kategori = 'berita'
        """).fetchall()

        for judul, kata_kunci, tgl in rows_berita:
            teks = f"{judul or ''} {kata_kunci or ''}".lower()
            in_terkini = tgl in tgl_terkini
            in_baseline = tgl in tgl_baseline
            for cat, info in kategori_map.items():
                if any(kw in teks for kw in info["keywords"]):
                    ancaman_counts[cat] += 1
                    if in_terkini:
                        ancaman_terkini[cat] += 1
                    if in_baseline:
                        ancaman_baseline[cat] += 1

        top_ancaman = [
            {
                "kategori": cat,
                "jumlah": ancaman_counts[cat],
                "jumlah_terkini": ancaman_terkini[cat],
                "jumlah_baseline": ancaman_baseline[cat],
                "growth_persen": _hitung_growth(ancaman_terkini[cat], ancaman_baseline[cat]),
                "icon": kategori_map[cat]["icon"],
                "deskripsi": kategori_map[cat]["desc"],
            }
            for cat in sorted(ancaman_counts, key=lambda x: ancaman_counts[x], reverse=True)
        ]

        # 3. Word Cloud Khusus Kasus Insiden Spesifik (Jendela 7 Hari Terkini)
        rows_insiden = cur.execute("""
            SELECT kata_kunci, judul, sumber 
            FROM riwayat_tren 
            WHERE kategori_relevansi = 'insiden_spesifik'
              AND substr(tanggal_publish, 1, 10) >= (
                  SELECT date(max(substr(tanggal_publish, 1, 10)), '-7 days') 
                  FROM riwayat_tren
              )
        """).fetchall()
        if not rows_insiden:
            rows_insiden = cur.execute("""
                SELECT kata_kunci, judul, sumber 
                FROM riwayat_tren 
                WHERE kategori_relevansi = 'insiden_spesifik'
                ORDER BY tanggal_publish DESC
                LIMIT 100
            """).fetchall()

        stop_words = set(ConfigLoader.get_rules("publik_statistik").get("stop_words", []))

        kws_sample = {}
        counter_kws = {}
        for r in rows_insiden:
            raw_kws, judul, sumber = r[0], r[1], r[2]
            if raw_kws:
                for k in raw_kws.split(","):
                    clean_k = k.strip().lower()
                    if clean_k and len(clean_k) > 2 and clean_k not in stop_words:
                        counter_kws[clean_k] = counter_kws.get(clean_k, 0) + 1
                        if clean_k not in kws_sample and judul:
                            kws_sample[clean_k] = {
                                "judul": str(judul).strip(),
                                "sumber": str(sumber or "Media Siber").strip()
                            }

        sorted_kws = sorted(counter_kws.items(), key=lambda x: x[1], reverse=True)[:32]
        word_cloud = [
            {
                "kata": item[0],
                "bobot": item[1],
                "contoh_judul": kws_sample.get(item[0], {}).get("judul", f"Kasus terkait {item[0]}"),
                "sumber": kws_sample.get(item[0], {}).get("sumber", "Laporan Media")
            }
            for item in sorted_kws
        ]

        # 5. Daftar Intisari Artikel Edukasi Asli (Jendela 7 Hari Terkini)
        rows_edukasi = cur.execute("""
            SELECT judul, sumber, ringkasan_atau_narasi, link, tanggal_publish
            FROM riwayat_tren 
            WHERE kategori_relevansi = 'analisis_relevan' 
              AND ringkasan_atau_narasi != ''
              AND substr(tanggal_publish, 1, 10) >= (
                  SELECT date(max(substr(tanggal_publish, 1, 10)), '-7 days') 
                  FROM riwayat_tren
              )
            ORDER BY tanggal_publish DESC
        """).fetchall()
        if not rows_edukasi:
            rows_edukasi = cur.execute("""
                SELECT judul, sumber, ringkasan_atau_narasi, link, tanggal_publish
                FROM riwayat_tren 
                WHERE kategori_relevansi = 'analisis_relevan' AND ringkasan_atau_narasi != ''
                ORDER BY tanggal_publish DESC
                LIMIT 20
            """).fetchall()

        edukasi_list = [
            {
                "judul": r[0],
                "sumber": r[1],
                "ringkasan": r[2],
                "link": r[3],
                "tanggal": r[4],
            }
            for r in rows_edukasi
        ]

        # 6. Sektor Vital Sasaran Serangan (IIV Perpres 82/2022)
        sektor_rules = ConfigLoader.get_rules("sektor_rules")
        sektor_counts = {s: 0 for s in sektor_rules}
        sektor_terkini = {s: 0 for s in sektor_rules}
        sektor_baseline = {s: 0 for s in sektor_rules}
        for judul, kata_kunci, tgl in rows_berita:
            teks = f"{judul or ''} {kata_kunci or ''}".lower()
            in_terkini = tgl in tgl_terkini
            in_baseline = tgl in tgl_baseline
            for s_nama, s_words in sektor_rules.items():
                if any(w in teks for w in s_words):
                    sektor_counts[s_nama] += 1
                    if in_terkini:
                        sektor_terkini[s_nama] += 1
                    if in_baseline:
                        sektor_baseline[s_nama] += 1

        top_sektor = [
            {
                "sektor": s,
                "jumlah": c,
                "growth_persen": _hitung_growth(sektor_terkini[s], sektor_baseline[s]),
            }
            for s, c in sorted(sektor_counts.items(), key=lambda x: x[1], reverse=True)
            if c > 0
        ]
        if not top_sektor:
            top_sektor = [{"sektor": s, "jumlah": 0, "growth_persen": 0.0} for s in list(sektor_rules.keys())[:5]]

        # 7. Fluktuasi Pantauan Harian (10 Hari Terakhir)
        r_berita_tgl = dict(cur.execute("""
            SELECT substr(tanggal_publish, 1, 10) as tgl, count(*) 
            FROM riwayat_tren 
            WHERE kategori = 'berita' AND tgl IS NOT NULL AND tgl != ''
            GROUP BY tgl ORDER BY tgl DESC LIMIT 10
        """).fetchall())

        timeline_harian = {
            "label": list(r_berita_tgl.keys()),
            "berita": list(r_berita_tgl.values()),
        }

        # 8. Sebaran Media Pelapor (Nasional vs Global)
        rows_media = cur.execute("""
            SELECT 
                CASE 
                    WHEN sumber LIKE '%Google News%' OR sumber IN ('Detikcom', 'CNN Indonesia', 'CNBC Indonesia', 'Antara News', 'Tempo.co', 'Katadata', 'Liputan6', 'Sindonews', 'Republika', 'Media Indonesia') THEN 'Media Nasional'
                    ELSE 'Media Global & CTI'
                END as tipe_media,
                count(*) as cnt
            FROM riwayat_tren 
            WHERE kategori = 'berita'
            GROUP BY tipe_media
        """).fetchall()
        sebaran_media = {r[0]: r[1] for r in rows_media}

        # Dynamic KPI Insights (3 Kartu Fakta Bersih)
        total_ancaman_count = sum(a["jumlah"] for a in top_ancaman) or 1
        top_cat = top_ancaman[0] if top_ancaman and top_ancaman[0]["jumlah"] > 0 else {"kategori": "Nihil Anomali", "jumlah": 0}
        persen_top = round((top_cat["jumlah"] / total_ancaman_count) * 100) if top_cat["jumlah"] > 0 else 0

        # Ambil sampel judul nyata dari kategori ancaman teratas untuk insight publik anti-halusinasi
        sample_headline = ""
        if top_cat["jumlah"] > 0:
            row_sample = cur.execute("""
                SELECT judul FROM riwayat_tren 
                WHERE kategori = 'berita' AND (kata_kunci LIKE ? OR judul LIKE ?)
                ORDER BY tanggal_publish DESC LIMIT 1
            """, (f"%{top_cat['kategori']}%", f"%{top_cat['kategori']}%")).fetchone()
            if row_sample and row_sample[0]:
                sample_clean = str(row_sample[0]).strip()
                sample_headline = f" Teranyar melibatkan insiden: \"{sample_clean[:75]}...\"" if len(sample_clean) > 75 else f" Teranyar melibatkan insiden: \"{sample_clean}\"."

        sektor_utama = top_sektor[0]["sektor"] if top_sektor and top_sektor[0]["jumlah"] > 0 else "Infrastruktur Vital"
        sektor_jml = top_sektor[0]["jumlah"] if top_sektor else 0

        total_media = sum(sebaran_media.values()) or 1
        nasional_count = sebaran_media.get("Media Nasional", 0)
        persen_nasional = round((nasional_count / total_media) * 100)

        top_growth = top_cat.get("growth_persen", 0.0)

        kpi_insights = [
            {
                "id": "top_target",
                "judul": "Modus Paling Mengintai",
                "nilai": f"{top_cat['kategori']}" if top_cat["jumlah"] > 0 else "Kondisi Terkendali",
                "growth_persen": top_growth,
                "insight": f"Mencakup {persen_top}% ({top_cat['jumlah']} laporan) dari pantauan ancaman siber aktif.{sample_headline}",
                "badge": "Top Target Warga",
                "icon": "warning",
            },
            {
                "id": "top_sektor",
                "judul": "Sektor Sasaran Utama",
                "nilai": sektor_utama,
                "insight": f"Sektor {sektor_utama} mencatat paparan tertinggi dengan {sektor_jml} insiden siber aktif.",
                "badge": "Infrastruktur Vital",
                "icon": "domain",
            },
            {
                "id": "fokus_wilayah",
                "judul": "Fokus Wilayah Paparan",
                "nilai": f"{persen_nasional}% Isu Nasional",
                "insight": f"Sebanyak {nasional_count} dari {total_media} pemberitaan berfokus langsung pada wilayah digital Indonesia.",
                "badge": "Ruang Digital RI",
                "icon": "policy",
            },
        ]

        takeaway_chart = (
            f"Kategori {top_cat['kategori']} mendominasi ruang ancaman publik dengan proporsi {persen_top}% "
            f"({top_cat['jumlah']} kasus terpantau). Pengamanan diprioritaskan pada verifikasi berkas digital dan proteksi kredensial."
        ) if top_cat["jumlah"] > 0 else (
            "Aktivitas ancaman digital terpantau stabil tanpa anomali lonjakan masif pada periode pemantauan terkini."
        )

        return {
            "status": "ok",
            "total_berita": total_berita,
            "total_edukasi": total_edukasi or 0,
            "kpi_insights": kpi_insights,
            "word_cloud": word_cloud,
            "edukasi_list": edukasi_list,
            "top_ancaman": top_ancaman,
            "top_sektor": top_sektor,
            "timeline_harian": timeline_harian,
            "sebaran_media": sebaran_media,
            "takeaway_chart": takeaway_chart,
            "waktu_terakhir_update": ambil_waktu_terakhir_scraping(db_path),
        }


_d3fend_cache_mappings: Optional[Dict[str, List[dict]]] = None
_d3fend_cache_techniques: Optional[List[dict]] = None
_d3fend_cache_raw_mappings: Optional[List[dict]] = None


def _get_d3fend_prepared_dir(prepared_dir: Optional[Path] = None) -> Path:
    if prepared_dir:
        return Path(prepared_dir)
    return Path(__file__).resolve().parents[2] / "data" / "prepared"


def _load_d3fend_json_cache(prepared_dir: Optional[Path] = None) -> bool:
    global _d3fend_cache_mappings, _d3fend_cache_techniques, _d3fend_cache_raw_mappings
    p_dir = _get_d3fend_prepared_dir(prepared_dir)
    map_file = p_dir / "d3fend_mappings.json"
    tech_file = p_dir / "d3fend_techniques.json"

    if not map_file.exists():
        return False

    try:
        raw_maps = json.loads(map_file.read_text(encoding="utf-8"))
        _d3fend_cache_raw_mappings = raw_maps

        # Membangun indeks mapping per attack_technique_id
        index: Dict[str, Dict[str, dict]] = {}
        for m in raw_maps:
            aid = str(m.get("attack_technique_id", "")).strip()
            if not aid:
                continue
            tid = m.get("technique_id") or m.get("d3fend_technique_id")
            if not tid:
                continue
            entry = {
                "technique_id": tid,
                "name": m.get("name", ""),
                "tactic": m.get("tactic", ""),
                "definition": m.get("definition", ""),
                "relationship_type": m.get("relationship_type", "mitigates"),
                "source_version": m.get("source_version", "1.6.0"),
            }
            if aid not in index:
                index[aid] = {}
            if tid not in index[aid]:
                index[aid][tid] = entry

        # Urutkan per technique_id ASC
        _d3fend_cache_mappings = {
            aid: sorted(tech_map.values(), key=lambda x: x["technique_id"])
            for aid, tech_map in index.items()
        }

        if tech_file.exists():
            _d3fend_cache_techniques = json.loads(tech_file.read_text(encoding="utf-8"))
        else:
            _d3fend_cache_techniques = []

        return True
    except Exception as e:
        logger.warning(f"Gagal memuat cache D3FEND dari JSON: {e}")
        return False


def _ambil_d3fend_mitigasi_from_db(clean_id: str, conn: sqlite3.Connection) -> List[dict]:
    # 1. Coba exact match terlebih dahulu
    cursor = conn.execute(
        """
        SELECT DISTINCT t.technique_id, t.name, t.tactic, t.definition, m.relationship_type, m.source_version
        FROM d3fend_attack_mappings m
        JOIN d3fend_techniques t ON m.d3fend_technique_id = t.technique_id
        WHERE m.attack_technique_id = ?
        ORDER BY t.technique_id ASC
        """,
        (clean_id,),
    )
    rows = [dict(r) for r in cursor.fetchall()]

    # 2. Jika input adalah sub-teknik (misal T1059.001) dan tidak ada hasil, fallback ke parent (T1059)
    if not rows and "." in clean_id:
        parent_id = clean_id.split(".")[0]
        cursor = conn.execute(
            """
            SELECT DISTINCT t.technique_id, t.name, t.tactic, t.definition, m.relationship_type, m.source_version
            FROM d3fend_attack_mappings m
            JOIN d3fend_techniques t ON m.d3fend_technique_id = t.technique_id
            WHERE m.attack_technique_id = ?
            ORDER BY t.technique_id ASC
            """,
            (parent_id,),
        )
        rows = [dict(r) for r in cursor.fetchall()]

    # 3. Jika input adalah parent teknik (misal T1566) dan D3FEND hanya memetakan sub-teknik (T1566.001, dll)
    if not rows and "." not in clean_id:
        cursor = conn.execute(
            """
            SELECT DISTINCT t.technique_id, t.name, t.tactic, t.definition, m.relationship_type, m.source_version
            FROM d3fend_attack_mappings m
            JOIN d3fend_techniques t ON m.d3fend_technique_id = t.technique_id
            WHERE m.attack_technique_id LIKE ?
            ORDER BY t.technique_id ASC
            """,
            (f"{clean_id}.%",),
        )
        rows = [dict(r) for r in cursor.fetchall()]

    return rows


def simpan_d3fend_techniques(
    techniques: List[dict],
    db_path: Path = DEFAULT_DB_PATH,
    prepared_dir: Optional[Path] = None,
) -> int:
    """
    Menyimpan atau memperbarui daftar teknik D3FEND ke berkas JSON data/prepared/d3fend_techniques.json.
    Jika db_path kustom diberikan, juga melakukan sinkronisasi ke tabel relasional SQLite.
    """
    if not techniques:
        return 0

    # Hanya tulis ke file JSON jika prepared_dir eksplisit atau db_path adalah DEFAULT_DB_PATH (bukan unit test temp DB)
    if prepared_dir is not None or Path(db_path) == Path(DEFAULT_DB_PATH):
        global _d3fend_cache_techniques, _d3fend_cache_mappings
        _d3fend_cache_techniques = None
        _d3fend_cache_mappings = None

        p_dir = _get_d3fend_prepared_dir(prepared_dir)
        p_dir.mkdir(parents=True, exist_ok=True)
        out_file = p_dir / "d3fend_techniques.json"
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(techniques, f, indent=2, ensure_ascii=False)
            logger.info(f"Berhasil menyimpan {len(techniques)} teknik D3FEND ke JSON ({out_file}).")
        except Exception as e:
            logger.warning(f"Gagal menyimpan d3fend_techniques ke JSON: {e}")

    # Sinkronisasi ke DB jika custom DB atau jika diminta
    if Path(db_path) != Path(DEFAULT_DB_PATH):
        init_db(db_path)
        sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with _koneksi(db_path) as conn:
            for t in techniques:
                conn.execute(
                    """
                    INSERT INTO d3fend_techniques (technique_id, name, tactic, definition, source_version, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(technique_id) DO UPDATE SET
                        name = excluded.name,
                        tactic = excluded.tactic,
                        definition = excluded.definition,
                        source_version = excluded.source_version,
                        updated_at = excluded.updated_at
                    """,
                    (
                        t["technique_id"],
                        t["name"],
                        t.get("tactic", ""),
                        t.get("definition", ""),
                        t.get("source_version", "1.6.0"),
                        t.get("updated_at", sekarang),
                    ),
                )
    return len(techniques)


def simpan_d3fend_attack_mappings(
    mappings: List[dict],
    db_path: Path = DEFAULT_DB_PATH,
    prepared_dir: Optional[Path] = None,
) -> int:
    """
    Menyimpan pemetaan ATT&CK ID ke D3FEND Technique ID ke berkas JSON data/prepared/d3fend_mappings.json.
    Jika db_path kustom diberikan, juga melakukan sinkronisasi ke tabel d3fend_attack_mappings SQLite.
    """
    if not mappings:
        return 0

    # Hanya tulis ke file JSON jika prepared_dir eksplisit atau db_path adalah DEFAULT_DB_PATH (bukan unit test temp DB)
    if prepared_dir is not None or Path(db_path) == Path(DEFAULT_DB_PATH):
        global _d3fend_cache_mappings, _d3fend_cache_raw_mappings
        _d3fend_cache_mappings = None
        _d3fend_cache_raw_mappings = None

        p_dir = _get_d3fend_prepared_dir(prepared_dir)
        p_dir.mkdir(parents=True, exist_ok=True)
        out_file = p_dir / "d3fend_mappings.json"
        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(mappings, f, indent=2, ensure_ascii=False)
            logger.info(f"Berhasil menyimpan {len(mappings)} pemetaan D3FEND-ATT&CK ke JSON ({out_file}).")
        except Exception as e:
            logger.warning(f"Gagal menyimpan d3fend_mappings ke JSON: {e}")

    count = len(mappings)
    if Path(db_path) != Path(DEFAULT_DB_PATH):
        init_db(db_path)
        count = 0
        with _koneksi(db_path) as conn:
            for m in mappings:
                cur = conn.execute(
                    """
                    INSERT OR IGNORE INTO d3fend_attack_mappings
                    (attack_technique_id, d3fend_technique_id, relationship_type, source_version)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        m["attack_technique_id"],
                        m.get("d3fend_technique_id") or m.get("technique_id"),
                        m.get("relationship_type", "mitigates"),
                        m.get("source_version", "1.6.0"),
                    ),
                )
                count += cur.rowcount
        return count
    return len(mappings)


def ambil_d3fend_mitigasi_by_attack_id(
    attack_technique_id: str,
    db_path: Path = DEFAULT_DB_PATH,
    prepared_dir: Optional[Path] = None,
) -> List[dict]:
    """
    Melakukan lookup deterministik mitigasi D3FEND untuk suatu ID teknik ATT&CK.
    Strictly non-vector, deterministic lookup dari berkas JSON data/prepared/d3fend_mappings.json.
    Mendukung fallback hierarki (parent <-> sub-technique).
    """
    if not attack_technique_id:
        return []

    clean_id = attack_technique_id.strip()

    # Cek apakah pemanggil menggunakan custom db_path pada unit testing yang memiliki data tabel SQLite
    if Path(db_path) != Path(DEFAULT_DB_PATH) and Path(db_path).exists():
        try:
            with _koneksi(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='d3fend_attack_mappings'")
                if cur.fetchone()[0] > 0:
                    cnt = conn.execute("SELECT count(*) FROM d3fend_attack_mappings").fetchone()[0]
                    if cnt > 0:
                        return _ambil_d3fend_mitigasi_from_db(clean_id, conn)
        except Exception:
            pass

    # Gunakan cache JSON data/prepared/d3fend_mappings.json
    global _d3fend_cache_mappings
    if _d3fend_cache_mappings is None:
        loaded = _load_d3fend_json_cache(prepared_dir)
        if not loaded:
            try:
                init_db(db_path)
                with _koneksi(db_path) as conn:
                    conn.row_factory = sqlite3.Row
                    return _ambil_d3fend_mitigasi_from_db(clean_id, conn)
            except Exception:
                return []

    if _d3fend_cache_mappings is None:
        return []

    # 1. Exact match
    if clean_id in _d3fend_cache_mappings:
        return [dict(x) for x in _d3fend_cache_mappings[clean_id]]

    # 2. Sub-teknik fallback ke parent (misal T1059.001 -> T1059)
    if "." in clean_id:
        parent_id = clean_id.split(".")[0]
        if parent_id in _d3fend_cache_mappings:
            return [dict(x) for x in _d3fend_cache_mappings[parent_id]]

    # 3. Parent teknik fallback ke sub-teknik (misal T1566 -> T1566.001, dll)
    if "." not in clean_id:
        prefix = f"{clean_id}."
        matched: Dict[str, dict] = {}
        for aid, items in _d3fend_cache_mappings.items():
            if aid.startswith(prefix):
                for item in items:
                    tid = item["technique_id"]
                    if tid not in matched:
                        matched[tid] = item
        if matched:
            return sorted(matched.values(), key=lambda x: x["technique_id"])

    return []


def ambil_semua_d3fend_techniques(
    db_path: Path = DEFAULT_DB_PATH,
    prepared_dir: Optional[Path] = None,
) -> List[dict]:
    """Mengambil semua teknik D3FEND yang tersimpan (dari JSON data/prepared/)."""
    if Path(db_path) != Path(DEFAULT_DB_PATH) and Path(db_path).exists():
        try:
            with _koneksi(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='d3fend_techniques'")
                if cur.fetchone()[0] > 0:
                    cnt = conn.execute("SELECT count(*) FROM d3fend_techniques").fetchone()[0]
                    if cnt > 0:
                        cursor = conn.execute(
                            "SELECT technique_id, name, tactic, definition, source_version, updated_at FROM d3fend_techniques ORDER BY technique_id ASC"
                        )
                        return [dict(r) for r in cursor.fetchall()]
        except Exception:
            pass

    global _d3fend_cache_techniques
    if _d3fend_cache_techniques is None:
        _load_d3fend_json_cache(prepared_dir)

    if _d3fend_cache_techniques is not None and len(_d3fend_cache_techniques) > 0:
        return [dict(x) for x in _d3fend_cache_techniques]

    # Fallback to DB
    init_db(db_path)
    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT technique_id, name, tactic, definition, source_version, updated_at FROM d3fend_techniques ORDER BY technique_id ASC"
        )
        return [dict(r) for r in cursor.fetchall()]


def ambil_semua_d3fend_mappings(
    db_path: Path = DEFAULT_DB_PATH,
    prepared_dir: Optional[Path] = None,
) -> List[dict]:
    """Mengambil semua pemetaan D3FEND-ATT&CK yang tersimpan (dari JSON data/prepared/)."""
    if Path(db_path) != Path(DEFAULT_DB_PATH) and Path(db_path).exists():
        try:
            with _koneksi(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='d3fend_attack_mappings'")
                if cur.fetchone()[0] > 0:
                    cnt = conn.execute("SELECT count(*) FROM d3fend_attack_mappings").fetchone()[0]
                    if cnt > 0:
                        cursor = conn.execute(
                            "SELECT attack_technique_id, d3fend_technique_id, relationship_type, source_version FROM d3fend_attack_mappings ORDER BY attack_technique_id ASC"
                        )
                        return [dict(r) for r in cursor.fetchall()]
        except Exception:
            pass

    global _d3fend_cache_raw_mappings
    if _d3fend_cache_raw_mappings is None:
        _load_d3fend_json_cache(prepared_dir)

    if _d3fend_cache_raw_mappings is not None and len(_d3fend_cache_raw_mappings) > 0:
        return [
            {
                "attack_technique_id": m.get("attack_technique_id"),
                "d3fend_technique_id": m.get("d3fend_technique_id") or m.get("technique_id"),
                "relationship_type": m.get("relationship_type", "mitigates"),
                "source_version": m.get("source_version", "1.6.0"),
            }
            for m in _d3fend_cache_raw_mappings
        ]

    # Fallback to DB
    init_db(db_path)
    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            "SELECT attack_technique_id, d3fend_technique_id, relationship_type, source_version FROM d3fend_attack_mappings ORDER BY attack_technique_id ASC"
        )
        return [dict(r) for r in cursor.fetchall()]

def simpan_intelijen_berita(record: dict, db_path: Path = DEFAULT_DB_PATH) -> int:
    """
    Menyimpan hasil analisis intelijen berita terverifikasi ke tabel intelijen_berita_tervalidasi.
    Mendukung upsert berdasarkan article_identifier unik.
    """
    if not record or not record.get("article_identifier"):
        return 0
    init_db(db_path)

    # Format JSON fields if they are lists/dicts
    d3fend_json = record.get("d3fend_mitigasi_json")
    if isinstance(d3fend_json, (list, dict)):
        d3fend_json = json.dumps(d3fend_json, ensure_ascii=False)
    elif d3fend_json is None:
        d3fend_json = json.dumps([])

    nist_json = record.get("nist_referensi_json")
    if isinstance(nist_json, (list, dict)):
        nist_json = json.dumps(nist_json, ensure_ascii=False)
    elif nist_json is None:
        nist_json = json.dumps([])

    dibuat_pada = record.get("dibuat_pada") or datetime.now(timezone.utc).isoformat()

    with _koneksi(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO intelijen_berita_tervalidasi (
                article_identifier, kategori_insiden, confidence_kategori, kutipan_bukti_kategori,
                mitre_tactic, mitre_technique_id, mitre_technique_name, confidence_mitre, kutipan_bukti_mitre,
                d3fend_mitigasi_json, nist_referensi_json,
                version_taxonomy, version_attack, version_d3fend, version_nist,
                dibuat_pada, koreksi_admin_kategori, koreksi_admin_technique_id,
                koreksi_admin_catatan, koreksi_admin_oleh, koreksi_admin_pada, flag_tinjauan,
                sektor_target, confidence_sektor, kutipan_bukti_sektor, alasan_sektor, koreksi_admin_sektor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(article_identifier) DO UPDATE SET
                kategori_insiden = excluded.kategori_insiden,
                confidence_kategori = excluded.confidence_kategori,
                kutipan_bukti_kategori = excluded.kutipan_bukti_kategori,
                mitre_tactic = excluded.mitre_tactic,
                mitre_technique_id = excluded.mitre_technique_id,
                mitre_technique_name = excluded.mitre_technique_name,
                confidence_mitre = excluded.confidence_mitre,
                kutipan_bukti_mitre = excluded.kutipan_bukti_mitre,
                d3fend_mitigasi_json = excluded.d3fend_mitigasi_json,
                nist_referensi_json = excluded.nist_referensi_json,
                version_taxonomy = excluded.version_taxonomy,
                version_attack = excluded.version_attack,
                version_d3fend = excluded.version_d3fend,
                version_nist = excluded.version_nist,
                flag_tinjauan = COALESCE(excluded.flag_tinjauan, intelijen_berita_tervalidasi.flag_tinjauan),
                sektor_target = COALESCE(excluded.sektor_target, intelijen_berita_tervalidasi.sektor_target),
                confidence_sektor = COALESCE(excluded.confidence_sektor, intelijen_berita_tervalidasi.confidence_sektor),
                kutipan_bukti_sektor = COALESCE(excluded.kutipan_bukti_sektor, intelijen_berita_tervalidasi.kutipan_bukti_sektor),
                alasan_sektor = COALESCE(excluded.alasan_sektor, intelijen_berita_tervalidasi.alasan_sektor),
                koreksi_admin_sektor = COALESCE(excluded.koreksi_admin_sektor, intelijen_berita_tervalidasi.koreksi_admin_sektor)
            """,
            (
                record["article_identifier"],
                record.get("kategori_insiden", "Tidak Dapat Ditentukan"),
                float(record.get("confidence_kategori", 0.0)),
                record.get("kutipan_bukti_kategori", ""),
                record.get("mitre_tactic"),
                record.get("mitre_technique_id", "tidak_ditentukan"),
                record.get("mitre_technique_name"),
                float(record.get("confidence_mitre", 0.0)) if record.get("confidence_mitre") is not None else None,
                record.get("kutipan_bukti_mitre", ""),
                d3fend_json,
                nist_json,
                record.get("version_taxonomy", "ecsirt-2026"),
                record.get("version_attack", "v20.0"),
                record.get("version_d3fend", "1.6.0"),
                record.get("version_nist", "SP800-53-Rev5"),
                dibuat_pada,
                record.get("koreksi_admin_kategori"),
                record.get("koreksi_admin_technique_id"),
                record.get("koreksi_admin_catatan"),
                record.get("koreksi_admin_oleh"),
                record.get("koreksi_admin_pada"),
                record.get("flag_tinjauan"),
                record.get("sektor_target"),
                float(record["confidence_sektor"]) if record.get("confidence_sektor") is not None else None,
                record.get("kutipan_bukti_sektor"),
                record.get("alasan_sektor"),
                record.get("koreksi_admin_sektor"),
            ),
        )
        return cursor.lastrowid or 1


def ambil_intelijen_berita(article_identifier: str, db_path: Path = DEFAULT_DB_PATH) -> Optional[dict]:
    """Mengambil satu data intelijen berita berdasarkan article_identifier."""
    if not article_identifier:
        return None
    init_db(db_path)
    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            "SELECT * FROM intelijen_berita_tervalidasi WHERE article_identifier = ?",
            (article_identifier,),
        ).fetchone()
        if not row:
            return None
        res = dict(row)
        try:
            res["d3fend_mitigasi"] = json.loads(res.get("d3fend_mitigasi_json") or "[]")
        except Exception:
            res["d3fend_mitigasi"] = []
        try:
            res["nist_referensi"] = json.loads(res.get("nist_referensi_json") or "[]")
        except Exception:
            res["nist_referensi"] = []
        return res


def ambil_semua_intelijen_berita(limit: int = 100, offset: int = 0, db_path: Path = DEFAULT_DB_PATH) -> List[dict]:
    """Mengambil daftar seluruh rekaman intelijen berita terverifikasi."""
    init_db(db_path)
    with _koneksi(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM intelijen_berita_tervalidasi ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
        result = []
        for r in rows:
            item = dict(r)
            try:
                item["d3fend_mitigasi"] = json.loads(item.get("d3fend_mitigasi_json") or "[]")
            except Exception:
                item["d3fend_mitigasi"] = []
            try:
                item["nist_referensi"] = json.loads(item.get("nist_referensi_json") or "[]")
            except Exception:
                item["nist_referensi"] = []
            result.append(item)
        return result


def simpan_koreksi_admin_intelijen(
    article_identifier: str,
    koreksi_kategori: Optional[str] = None,
    koreksi_technique_id: Optional[str] = None,
    catatan: Optional[str] = None,
    oleh: Optional[str] = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> bool:
    """Menyimpan koreksi manual admin pada hasil analisis berita."""
    if not article_identifier:
        return False
    init_db(db_path)
    waktu_koreksi = datetime.now(timezone.utc).isoformat()
    with _koneksi(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE intelijen_berita_tervalidasi
            SET koreksi_admin_kategori = COALESCE(?, koreksi_admin_kategori),
                koreksi_admin_technique_id = COALESCE(?, koreksi_admin_technique_id),
                koreksi_admin_catatan = COALESCE(?, koreksi_admin_catatan),
                koreksi_admin_oleh = COALESCE(?, koreksi_admin_oleh),
                koreksi_admin_pada = ?
            WHERE article_identifier = ?
            """,
            (koreksi_kategori, koreksi_technique_id, catatan, oleh, waktu_koreksi, article_identifier),
        )
        return cur.rowcount > 0


def simpan_koreksi_admin_sektor(
    article_identifier: str,
    sektor: str,
    alasan: Optional[str] = None,
    oleh: Optional[str] = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> bool:
    """Menyimpan koreksi manual admin pada sektor sasaran berita."""
    if not article_identifier:
        return False
    init_db(db_path)
    waktu_koreksi = datetime.now(timezone.utc).isoformat()
    with _koneksi(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE intelijen_berita_tervalidasi
            SET koreksi_admin_sektor = ?,
                alasan_sektor = COALESCE(?, alasan_sektor),
                koreksi_admin_catatan = COALESCE(?, koreksi_admin_catatan),
                koreksi_admin_oleh = COALESCE(?, koreksi_admin_oleh),
                koreksi_admin_pada = ?
            WHERE article_identifier = ?
            """,
            (sektor, alasan, alasan, oleh, waktu_koreksi, article_identifier),
        )
        if cur.rowcount > 0:
            return True

        # Jika record belum ada, buat record baru dengan koreksi admin
        conn.execute(
            """
            INSERT INTO intelijen_berita_tervalidasi (
                article_identifier, kategori_insiden, confidence_kategori,
                sektor_target, koreksi_admin_sektor, alasan_sektor,
                koreksi_admin_catatan, koreksi_admin_oleh, koreksi_admin_pada,
                version_taxonomy, version_attack, version_d3fend, version_nist, dibuat_pada
            ) VALUES (?, 'Tidak Dapat Ditentukan', 0.0, ?, ?, ?, ?, ?, ?, 'ecsirt-2026', 'v20.0', '1.6.0', 'SP800-53-Rev5', ?)
            ON CONFLICT(article_identifier) DO UPDATE SET
                koreksi_admin_sektor = excluded.koreksi_admin_sektor,
                alasan_sektor = COALESCE(excluded.alasan_sektor, intelijen_berita_tervalidasi.alasan_sektor),
                koreksi_admin_catatan = COALESCE(excluded.koreksi_admin_catatan, intelijen_berita_tervalidasi.koreksi_admin_catatan),
                koreksi_admin_oleh = COALESCE(excluded.koreksi_admin_oleh, intelijen_berita_tervalidasi.koreksi_admin_oleh),
                koreksi_admin_pada = excluded.koreksi_admin_pada
            """,
            (article_identifier, sektor, sektor, alasan, alasan, oleh, waktu_koreksi, waktu_koreksi),
        )
        return True


def tandai_flag_tinjauan_intelijen(
    mitre_technique_id: str,
    flag: str = "TEKNIK_REVOKED_PERLU_REVIEW",
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Menandai insiden historis yang memakai teknik yang dicabut (revoked)."""
    if not mitre_technique_id:
        return 0
    init_db(db_path)
    with _koneksi(db_path) as conn:
        cur = conn.execute(
            """
            UPDATE intelijen_berita_tervalidasi
            SET flag_tinjauan = ?
            WHERE mitre_technique_id = ?
            """,
            (flag, mitre_technique_id),
        )
        return cur.rowcount



