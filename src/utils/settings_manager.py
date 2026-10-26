import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from src.storage.db import DEFAULT_DB_PATH, init_db
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

OFFICIAL_NARRATIVE_MODELS: List[str] = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]

OBSOLETE_MODELS: Set[str] = {
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-3.5-flash",
    "embedding-001",
}

DEFAULT_RATE_LIMITS: Dict[str, float] = {
    "gemini-2.5-flash": 5.0,
    "gemini-2.5-flash-lite": 10.0,
    "gemini-3-flash": 5.0,
    "gemini-3.1-flash-lite": 15.0,
    "gemini-3.6-flash": 5.0,
    "gemini-3.5-flash-lite": 15.0,
    "gemini-3.8-flash": 5.0,
    "gemini-embedding-001": 100.0,
    "gemini-embedding-exp-03-07": 100.0,
    "text-embedding-004": 100.0,
}

DEFAULT_PROACTIVE_THRESHOLDS: Dict[str, int] = {
    "gemini-2.5-flash": 4,
    "gemini-2.5-flash-lite": 9,
    "gemini-3-flash": 4,
    "gemini-3.1-flash-lite": 14,
    "gemini-3.6-flash": 4,
    "gemini-3.5-flash-lite": 14,
    "gemini-3.8-flash": 4,
    "gemini-embedding-001": 90,
    "gemini-embedding-exp-03-07": 90,
    "text-embedding-004": 90,
}

# Registri prompt aktif dengan nama ramah pengguna, kategori, dan deskripsi
PROMPT_METADATA: Dict[str, Dict[str, str]] = {
    "klasifikasi": {
        "nama": "Klasifikasi Relevansi Berita",
        "kategori": "Pipeline Harian",
        "deskripsi": "Menyaring berita hasil scraping ke dalam insiden_spesifik, analisis_relevan, atau tidak_relevan.",
    },
    "ringkas_berita": {
        "nama": "Ringkasan Eksekutif Berita",
        "kategori": "Pipeline Harian",
        "deskripsi": "Meringkas artikel insiden siber jadi 2-3 kalimat Bahasa Indonesia untuk digest.",
    },
    "section_1_makro": {
        "nama": "SITREP CTI - 1. Lanskap Makro",
        "kategori": "SITREP Tren Berita",
        "deskripsi": "Sintesis pola ancaman makro berdasarkan lonjakan insiden riil mingguan.",
    },
    "section_2_mikro": {
        "nama": "SITREP CTI - 2. Insiden Mikro",
        "kategori": "SITREP Tren Berita",
        "deskripsi": "Analisis mendalam terhadap top 3 insiden dominan dalam 7 hari terakhir.",
    },
    "section_3_vektor": {
        "nama": "SITREP CTI - 3. Vektor Serangan",
        "kategori": "SITREP Tren Berita",
        "deskripsi": "Pemetaan metode serangan teknis dan sektor sasaran yang terdampak.",
    },
    "section_5_emerging": {
        "nama": "SITREP CTI - 5. Ancaman Baru",
        "kategori": "SITREP Tren Berita",
        "deskripsi": "Deteksi varian malware baru, taktik mutakhir, atau kelompok peretas baru.",
    },
}


class SettingsManager:
    """
    Manajer pengaturan persisten berbasis SQLite dengan fallback cerdas ke file konfigurasi.
    Menyimpan perubahan admin ke tabel `pengaturan` di state.db sehingga berlaku instan
    tanpa perlu me-restart server.
    """

    _initialized = False
    _db_path = DEFAULT_DB_PATH

    @classmethod
    def set_db_path(cls, path):
        cls._db_path = Path(path)
        cls._initialized = False

    @classmethod
    def reset_db_path(cls):
        cls._db_path = DEFAULT_DB_PATH
        cls._initialized = False

    @classmethod
    def _conn(cls):
        db_path = getattr(cls, "_db_path", DEFAULT_DB_PATH)
        if not cls._initialized:
            try:
                init_db(db_path)
            except Exception as e:
                logger.warning(f"SettingsManager init_db peringatan pada {db_path}: {e}")
            cls._initialized = True
            try:
                c = sqlite3.connect(db_path)
                cls._clean_obsolete_db(c)
                c.close()
            except Exception as e:
                logger.warning(f"SettingsManager _clean_obsolete_db peringatan pada {db_path}: {e}")
        return sqlite3.connect(db_path)

    @classmethod
    def _clean_obsolete_db(cls, conn):
        try:
            cur = conn.cursor()
            cur.execute("SELECT nilai FROM pengaturan WHERE kunci = 'gemini.model_chain'")
            row = cur.fetchone()
            if row:
                try:
                    models = json.loads(row[0])
                except Exception:
                    models = []
                clean = [m for m in models if m not in OBSOLETE_MODELS]
                if not clean or any(m in OBSOLETE_MODELS for m in models) or (clean and clean[0] != "gemini-2.5-flash" and set(clean) == set(OFFICIAL_NARRATIVE_MODELS)):
                    clean = OFFICIAL_NARRATIVE_MODELS
                if clean != models:
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = 'gemini.model_chain'", (json.dumps(clean),))
            else:
                cur.execute("INSERT INTO pengaturan (kunci, nilai, diubah) VALUES ('gemini.model_chain', ?, datetime('now'))", (json.dumps(OFFICIAL_NARRATIVE_MODELS),))

            cur.execute("SELECT nilai FROM pengaturan WHERE kunci = 'gemini.embedding_model_fallback'")
            row = cur.fetchone()
            if row:
                try:
                    fb = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                except Exception:
                    fb = []
                if isinstance(fb, list):
                    clean_fb = [m for m in fb if m not in OBSOLETE_MODELS]
                else:
                    clean_fb = []
                if not clean_fb:
                    clean_fb = ["gemini-embedding-exp-03-07", "text-embedding-004"]
                if clean_fb != fb:
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = 'gemini.embedding_model_fallback'", (json.dumps(clean_fb),))
            else:
                cur.execute("INSERT INTO pengaturan (kunci, nilai, diubah) VALUES ('gemini.embedding_model_fallback', ?, datetime('now'))", (json.dumps(["gemini-embedding-exp-03-07", "text-embedding-004"]),))

            cur.execute("SELECT nilai FROM pengaturan WHERE kunci = 'gemini.rate_limits'")
            row_rl = cur.fetchone()
            if row_rl:
                try:
                    current_rl = json.loads(row_rl[0])
                except Exception:
                    current_rl = {}
                for obs in OBSOLETE_MODELS:
                    current_rl.pop(obs, None)
                for k, v in DEFAULT_RATE_LIMITS.items():
                    if k not in current_rl:
                        current_rl[k] = v
                if current_rl != (json.loads(row_rl[0]) if row_rl and row_rl[0] else {}):
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = 'gemini.rate_limits'", (json.dumps(current_rl),))
            else:
                cur.execute("INSERT INTO pengaturan (kunci, nilai, diubah) VALUES ('gemini.rate_limits', ?, datetime('now'))", (json.dumps(DEFAULT_RATE_LIMITS),))

            cur.execute("SELECT nilai FROM pengaturan WHERE kunci = 'gemini.proactive_thresholds'")
            row_pt = cur.fetchone()
            if row_pt:
                try:
                    current_pt = json.loads(row_pt[0])
                except Exception:
                    current_pt = {}
                for obs in OBSOLETE_MODELS:
                    current_pt.pop(obs, None)
                for k, v in DEFAULT_PROACTIVE_THRESHOLDS.items():
                    if k not in current_pt:
                        current_pt[k] = v
                if current_pt != (json.loads(row_pt[0]) if row_pt and row_pt[0] else {}):
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = 'gemini.proactive_thresholds'", (json.dumps(current_pt),))
            else:
                cur.execute("INSERT INTO pengaturan (kunci, nilai, diubah) VALUES ('gemini.proactive_thresholds', ?, datetime('now'))", (json.dumps(DEFAULT_PROACTIVE_THRESHOLDS),))

            # Bersihkan karakter BOM (\ufeff) dari template prompt
            cur.execute("SELECT kunci, nilai FROM pengaturan WHERE kunci LIKE 'prompt.%'")
            for p_kunci, p_nilai in cur.fetchall():
                if isinstance(p_nilai, str) and p_nilai.startswith("\ufeff"):
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = ?", (p_nilai.lstrip("\ufeff"), p_kunci))

            conn.commit()
        except Exception as e:
            logger.warning(f"SettingsManager gagal mengeksekusi _clean_obsolete_db: {e}")

    @classmethod
    def get(cls, kunci: str, default: Any = None) -> Any:
        """Ambil setting dari DB. Jika belum ada atau terjadi kegagalan DB, kembalikan default yang aman."""
        val = None
        try:
            conn = cls._conn()
            row = conn.execute(
                "SELECT nilai FROM pengaturan WHERE kunci = ?", (kunci,)
            ).fetchone()
            conn.close()
            if row:
                try:
                    val = json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    val = row[0]
        except Exception as e:
            logger.warning(f"SettingsManager gagal membaca '{kunci}' dari database ({e}), menggunakan fallback.")

        if val is None:
            val = default

        # Sanitasi string: bersihkan byte order mark (BOM) jika ada
        if isinstance(val, str):
            val = val.lstrip("\ufeff")

        # Sanitasi model: pastikan model usang tidak pernah dikembalikan dan urutan resmi terjaga
        if kunci == "gemini.model_chain":
            if isinstance(val, str):
                val = [m.strip() for m in val.replace("\r\n", "\n").replace("\n", ",").split(",") if m.strip()]
            if isinstance(val, list):
                val = [m for m in val if m not in OBSOLETE_MODELS]
            else:
                val = []
            if not val or (val and val[0] != "gemini-2.5-flash" and set(val) == set(OFFICIAL_NARRATIVE_MODELS)):
                val = list(OFFICIAL_NARRATIVE_MODELS)

        elif kunci.startswith("keywords."):
            if isinstance(val, str):
                val = [k.strip().lower() for k in val.replace("\r\n", "\n").replace("\n", ",").split(",") if k.strip()]
            if not isinstance(val, list):
                val = []

        elif kunci == "gemini.embedding_model_fallback":
            if isinstance(val, str):
                val = [m.strip() for m in val.replace("\n", ",").split(",") if m.strip()]
            if isinstance(val, list):
                val = [m for m in val if m != "embedding-001"]
            if not val:
                val = ["gemini-embedding-exp-03-07", "text-embedding-004"]

        elif kunci == "gemini.embedding_model":
            if not val or val == "embedding-001":
                val = "gemini-embedding-001"

        elif kunci == "gemini.rate_limits":
            if not isinstance(val, dict):
                val = dict(DEFAULT_RATE_LIMITS)
            else:
                val = {k: float(v) for k, v in val.items() if k not in OBSOLETE_MODELS}
                for k, v in DEFAULT_RATE_LIMITS.items():
                    if k not in val:
                        val[k] = v

        elif kunci == "gemini.proactive_thresholds":
            if not isinstance(val, dict):
                val = dict(DEFAULT_PROACTIVE_THRESHOLDS)
            else:
                val = {k: int(v) for k, v in val.items() if k not in OBSOLETE_MODELS}
                for k, v in DEFAULT_PROACTIVE_THRESHOLDS.items():
                    if k not in val:
                        val[k] = v

        return val

    @classmethod
    def set(cls, kunci: str, nilai: Any) -> None:
        """Simpan setting ke DB (upsert)."""
        nilai_str = json.dumps(nilai, ensure_ascii=False) if not isinstance(nilai, str) else nilai
        sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = cls._conn()
        conn.execute(
            """INSERT INTO pengaturan (kunci, nilai, diubah)
               VALUES (?, ?, ?)
               ON CONFLICT(kunci) DO UPDATE SET nilai=excluded.nilai, diubah=excluded.diubah""",
            (kunci, nilai_str, sekarang)
        )
        conn.commit()
        conn.close()

    @classmethod
    def get_gemini_config(cls) -> dict:
        """Membaca konfigurasi Gemini lengkap: DB override, YAML fallback."""
        yaml_cfg = ConfigLoader.get_config().get("gemini", {})
        return {
            "api_key": cls.get("gemini.api_key", yaml_cfg.get("api_key", "")),
            "model_chain": cls.get("gemini.model_chain", yaml_cfg.get("model_chain", [])),
            "temperature": 0.1,  # Default tetap deterministik & akurat (0.1), admin tidak dapat mengubah
            "embedding_model": cls.get("gemini.embedding_model", yaml_cfg.get("embedding_model", "gemini-embedding-001")),
            "embedding_model_fallback": cls.get(
                "gemini.embedding_model_fallback",
                yaml_cfg.get("embedding_model_fallback", ["gemini-embedding-exp-03-07", "text-embedding-004"])
            ),
            "rate_limits": cls.get("gemini.rate_limits", yaml_cfg.get("rate_limits", {})),
            "proactive_thresholds": cls.get("gemini.proactive_thresholds", yaml_cfg.get("proactive_thresholds", {})),
            "batch_sizes": cls.get("gemini.batch_sizes", yaml_cfg.get("batch_sizes", {})),
        }

    @classmethod
    def get_keywords(cls) -> dict:
        """Membaca semua grup kata kunci langsung dari database SQLite (tabel pengaturan)."""
        return {
            grup: cls.get(f"keywords.{grup}", [])
            for grup in ["english", "indonesia_mandiri", "objek_data_sensitif",
                         "objek_aset_digital", "indikator_insiden", "ambigu_butuh_konteks"]
        }

    @classmethod
    def get_prompt(cls, nama: str) -> str:
        """Membaca template prompt CTI langsung dari database SQLite (tabel pengaturan), dengan fallback cerdas ke berkas konfigurasi lokal."""
        val = cls.get(f"prompt.{nama}", "")
        if not val or not str(val).strip():
            try:
                from src.utils.config_loader import ConfigLoader
                val = ConfigLoader.get_prompt(nama)
            except Exception:
                val = ""
        return str(val).lstrip("\ufeff")

    @classmethod
    def get_all_prompts_info(cls) -> List[dict]:
        """Mengembalikan daftar 6 prompt aktif dengan metadata nama, kategori, dan deskripsi dari database."""
        prompts_info = []
        for prompt_id, meta in PROMPT_METADATA.items():
            isi = cls.get_prompt(prompt_id)
            prompts_info.append({
                "id": prompt_id,
                "nama": meta["nama"],
                "kategori": meta["kategori"],
                "deskripsi": meta["deskripsi"],
                "cuplikan": isi[:180] + "..." if len(isi) > 180 else isi,
            })
        return prompts_info

    @classmethod
    def get_rss_sources(cls, tipe: str) -> list:
        """Membaca sumber feed RSS langsung dari database SQLite (tabel pengaturan)."""
        key = f"rss_sources_{tipe}"
        sources = cls.get(key, [])
        for s in sources:
            if "active" not in s:
                s["active"] = True
        return sources
