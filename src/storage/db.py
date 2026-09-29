"""
Modul penyimpanan state persisten menggunakan SQLite. Menyimpan histori
artikel insiden & intelijen yang sudah pernah dikirim ke channel notifikasi, supaya
pipeline yang jalan otomatis tiap hari tidak mengirim ulang konten yang
sama meskipun RSS sumber terlambat update atau di-scrape ulang.
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
        for judul, kata_kunci in rows_berita:
            teks = f"{judul or ''} {kata_kunci or ''}".lower()
            for s_nama, s_words in sektor_rules.items():
                if any(w in teks for w in s_words):
                    sektor_counts[s_nama] += 1

        top_sektor = [
            {"sektor": s, "jumlah": c}
            for s, c in sorted(sektor_counts.items(), key=lambda x: x[1], reverse=True)
            if c > 0
        ]
        if not top_sektor:
            top_sektor = [{"sektor": s, "jumlah": 0} for s in list(sektor_rules.keys())[:5]]

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

        kpi_insights = [
            {
                "id": "top_target",
                "judul": "Modus Paling Mengintai",
                "nilai": f"{top_cat['kategori']}" if top_cat["jumlah"] > 0 else "Kondisi Terkendali",
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

