"""Penyimpanan hasil analisis intelijen berita dan koreksi admin."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import List, Optional

from src.storage.schema import DEFAULT_DB_PATH, _koneksi, init_db
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


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
    try:
        with _koneksi(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM intelijen_berita_tervalidasi WHERE article_identifier = ?",
                (article_identifier,),
            ).fetchone()
    except sqlite3.OperationalError:
        return None
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
