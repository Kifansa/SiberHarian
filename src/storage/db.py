"""
Modul penyimpanan state persisten menggunakan SQLite. Menyimpan histori
artikel & CVE yang sudah pernah dikirim ke channel notifikasi, supaya
pipeline yang jalan otomatis tiap hari tidak mengirim ulang konten yang
sama meskipun RSS/API sumber terlambat update atau di-scrape ulang.
"""
import pandas as pd
import sqlite3
from src.utils.config_loader import ConfigLoader
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
    artikel (bukan tanggal pipeline dijalankan), dipisah lagi per kategori
    (berita/cve). Dikelompokkan berdasarkan tanggal_publish supaya satu run
    scraping besar (mis. window 7 hari) langsung terdistribusi ke hari yang
    benar - bukan numpuk di satu hari berdasarkan kapan pipeline dijalankan.

    Returns: dict terurut dari tanggal TERBARU ke TERLAMA, contoh:
        {"2026-08-19": {"berita": [...], "cve": [...]}, "2026-08-18": {...}, ...}
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

    hasil = dict(list(hasil.items())[:hari])
    return hasil

def simpan_prediksi_tren(
    prediksi_berita: str,
    prediksi_cve: str,
    db_path: Path = DEFAULT_DB_PATH,
    kasus_wilayah_ai: Optional[str] = None,
    statistik_json: Optional[str] = None,
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
    Data untuk Beranda, tanggal terbaru DIPISAH per kategori (bukan
    dipaksa 1 tanggal yang sama) - karena rangkaian waktu publikasi
    berita & CVE independen (CVE dari NVD kadang 'tanggal publish'-nya
    tidak secepat berita yang terus update tiap jam). Kalau dipaksa 1
    tanggal gabungan, salah satu kategori bisa tampil kosong padahal
    datanya ada di tanggal yang sedikit berbeda.
    """
    grup_per_tanggal = ambil_riwayat_dikelompokkan_per_hari(hari, db_path)  # sudah urut terbaru -> terlama

    tanggal_berita, daftar_berita = None, []
    tanggal_cve, daftar_cve = None, []

    for tanggal, isi in grup_per_tanggal.items():
        if tanggal_berita is None and isi["berita"]:
            tanggal_berita, daftar_berita = tanggal, isi["berita"]
        if tanggal_cve is None and isi["cve"]:
            tanggal_cve, daftar_cve = tanggal, isi["cve"]
        if tanggal_berita is not None and tanggal_cve is not None:
            break

    waktu_scraping = ambil_waktu_terakhir_scraping(db_path)

    return {
        "tanggal_berita": tanggal_berita, "berita": daftar_berita,
        "tanggal_cve": tanggal_cve, "cve": daftar_cve,
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
        total_cve = cur.execute("SELECT count(*) FROM riwayat_tren WHERE kategori = 'cve'").fetchone()[0] or 1
        cve_darurat_10 = cur.execute("SELECT count(*) FROM riwayat_tren WHERE kategori = 'cve' AND skor_cvss >= 10.0").fetchone()[0]
        avg_cvss = cur.execute("SELECT AVG(skor_cvss) FROM riwayat_tren WHERE kategori = 'cve'").fetchone()[0] or 9.5
        total_edukasi = cur.execute("SELECT count(*) FROM riwayat_tren WHERE kategori_relevansi = 'analisis_relevan'").fetchone()[0]

        # 2. Distribusi Kategori Ancaman Populer
        kategori_map = ConfigLoader.get_rules("publik_statistik").get("kategori_map", {})

        ancaman_counts = {k: 0 for k in kategori_map}
        rows_berita = cur.execute("SELECT judul, kata_kunci FROM riwayat_tren WHERE kategori = 'berita'").fetchall()
        for judul, kata_kunci in rows_berita:
            teks = f"{judul or ''} {kata_kunci or ''}".lower()
            for cat, info in kategori_map.items():
                if any(kw in teks for kw in info["keywords"]):
                    ancaman_counts[cat] += 1

        top_ancaman = [
            {
                "kategori": cat,
                "jumlah": ancaman_counts[cat],
                "icon": kategori_map[cat]["icon"],
                "deskripsi": kategori_map[cat]["desc"],
            }
            for cat in sorted(ancaman_counts, key=lambda x: ancaman_counts[x], reverse=True)
        ]

        # 3. Word Cloud Khusus Kasus Insiden Spesifik (Jendela 7 Hari Terkini)
        rows_insiden = cur.execute("""
            SELECT kata_kunci 
            FROM riwayat_tren 
            WHERE kategori_relevansi = 'insiden_spesifik'
              AND substr(tanggal_publish, 1, 10) >= (
                  SELECT date(max(substr(tanggal_publish, 1, 10)), '-7 days') 
                  FROM riwayat_tren
              )
        """).fetchall()
        if not rows_insiden:
            rows_insiden = cur.execute("""
                SELECT kata_kunci 
                FROM riwayat_tren 
                WHERE kategori_relevansi = 'insiden_spesifik'
                ORDER BY tanggal_publish DESC
                LIMIT 100
            """).fetchall()

        stop_words = set(ConfigLoader.get_rules("publik_statistik").get("stop_words", []))

        kws_list = []
        for r in rows_insiden:
            if r[0]:
                for k in r[0].split(","):
                    clean_k = k.strip().lower()
                    if clean_k and len(clean_k) > 2 and clean_k not in stop_words:
                        kws_list.append(clean_k)

        counter_kws = {}
        for kw in kws_list:
            counter_kws[kw] = counter_kws.get(kw, 0) + 1

        sorted_kws = sorted(counter_kws.items(), key=lambda x: x[1], reverse=True)[:32]
        word_cloud = [{"kata": item[0], "bobot": item[1]} for item in sorted_kws]

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

        # 6. Top Vendor & Software Populer Terpapar CVE Kritis
        rows_vendor = cur.execute("""
            SELECT vendor, count(*) as cnt 
            FROM riwayat_tren 
            WHERE kategori = 'cve' AND vendor != 'Lainnya / Belum Teridentifikasi' AND vendor != ''
            GROUP BY vendor 
            ORDER BY cnt DESC 
            LIMIT 7
        """).fetchall()
        top_vendor = [{"vendor": r[0], "total_cve": r[1]} for r in rows_vendor]

        # 7. Fluktuasi Pantauan Harian (10 Hari Terakhir)
        r_berita_tgl = dict(cur.execute("""
            SELECT substr(tanggal_publish, 1, 10) as tgl, count(*) 
            FROM riwayat_tren 
            WHERE kategori = 'berita' AND tgl IS NOT NULL AND tgl != ''
            GROUP BY tgl ORDER BY tgl DESC LIMIT 10
        """).fetchall())

        r_cve_tgl = dict(cur.execute("""
            SELECT substr(tanggal_publish, 1, 10) as tgl, count(*) 
            FROM riwayat_tren 
            WHERE kategori = 'cve' AND tgl IS NOT NULL AND tgl != ''
            GROUP BY tgl ORDER BY tgl DESC LIMIT 10
        """).fetchall())

        tanggal_gabungan = sorted(list(set(list(r_berita_tgl.keys()) + list(r_cve_tgl.keys()))))
        timeline_harian = {
            "label": tanggal_gabungan,
            "berita": [r_berita_tgl.get(d, 0) for d in tanggal_gabungan],
            "cve": [r_cve_tgl.get(d, 0) for d in tanggal_gabungan],
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

        vendor_names = [v["vendor"] for v in top_vendor[:2]] if top_vendor else []
        vendor_str = " & ".join(vendor_names) if vendor_names else "Terdistribusi Merata"

        total_media = sum(sebaran_media.values()) or 1
        nasional_count = sebaran_media.get("Media Nasional", 0)
        persen_nasional = round((nasional_count / total_media) * 100)

        kpi_insights = [
            {
                "id": "top_target",
                "judul": "Modus Paling Mengintai",
                "nilai": f"{top_cat['kategori']}" if top_cat["jumlah"] > 0 else "Kondisi Terkendali",
                "insight": f"Mencakup {persen_top}% ({top_cat['jumlah']} laporan) dari pantauan ancaman aktif yang dilaporkan media.",
                "badge": "Top Target Warga",
                "icon": "warning",
            },
            {
                "id": "top_vendor",
                "judul": "Software Terbanyak Celah",
                "nilai": vendor_str,
                "insight": f"Celah keamanan tertinggi terkonsentrasi pada software dan produk dari {vendor_str}.",
                "badge": "Ekosistem Populer",
                "icon": "devices",
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

        return {
            "status": "ok",
            "total_berita": total_berita,
            "total_cve": total_cve,
            "avg_cvss": round(float(avg_cvss), 1) if avg_cvss else 0.0,
            "cve_darurat_10": cve_darurat_10 or 0,
            "total_edukasi": total_edukasi or 0,
            "kpi_insights": kpi_insights,
            "word_cloud": word_cloud,
            "edukasi_list": edukasi_list,
            "top_ancaman": top_ancaman,
            "top_vendor": top_vendor,
            "timeline_harian": timeline_harian,
            "sebaran_media": sebaran_media,
            "waktu_terakhir_update": ambil_waktu_terakhir_scraping(db_path),
        }

