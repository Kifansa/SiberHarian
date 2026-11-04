import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Set
from src.storage.db import DEFAULT_DB_PATH, init_db
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

OBSOLETE_MODELS: Set[str] = {
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-3.5-flash",
    "embedding-001",
}


class PengaturanTidakValid(ValueError):
    """Nilai pengaturan tidak lolos validasi server."""


def _default_gemini_values() -> Dict[str, Any]:
    """Membaca nilai default Gemini dari config agar tidak ada duplikasi hardcode."""
    gemini = ConfigLoader.get_config().get("gemini", {}) or {}

    model_chain = [
        str(m).strip()
        for m in gemini.get("model_chain", [])
        if str(m).strip() and str(m).strip() not in OBSOLETE_MODELS
    ]

    rate_limits: Dict[str, float] = {}
    for k, v in (gemini.get("rate_limits") or {}).items():
        if str(k) in OBSOLETE_MODELS:
            continue
        try:
            rate_limits[str(k)] = float(v)
        except (TypeError, ValueError):
            continue

    proactive_thresholds: Dict[str, int] = {}
    for k, v in (gemini.get("proactive_thresholds") or {}).items():
        if str(k) in OBSOLETE_MODELS:
            continue
        try:
            proactive_thresholds[str(k)] = int(v)
        except (TypeError, ValueError):
            continue

    return {
        "model_chain": model_chain,
        "rate_limits": rate_limits,
        "proactive_thresholds": proactive_thresholds,
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
    "kasus_insiden_wilayah": {
        "nama": "Kasus Insiden Teramai",
        "kategori": "KASUS INSIDEN SIBER TERAMAI",
        "deskripsi": "Sintesis analisis kasus insiden siber teratas (#1) per wilayah (Internasional, Nasional, Jawa Timur) berbasis fakta berita CTI.",
    },
    "section_1_makro": {
        "nama": "01 LONJAKAN ANCAMAN",
        "kategori": "ANALISIS BERITA SIBER MINGGUAN",
        "deskripsi": "Sintesis pola ancaman makro berdasarkan lonjakan insiden riil mingguan.",
    },
    "section_2_mikro": {
        "nama": "02 TREN MINGGUAN",
        "kategori": "ANALISIS BERITA SIBER MINGGUAN",
        "deskripsi": "Analisis mendalam terhadap top 3 insiden dominan dalam 7 hari terakhir.",
    },
    "section_3_vektor": {
        "nama": "03 VEKTOR SERANGAN",
        "kategori": "ANALISIS BERITA SIBER MINGGUAN",
        "deskripsi": "Pemetaan metode serangan teknis dan sektor sasaran yang terdampak.",
    },
    "section_5_emerging": {
        "nama": "05 PROYEKSI ANCAMAN",
        "kategori": "ANALISIS BERITA SIBER MINGGUAN",
        "deskripsi": "Deteksi varian malware baru, taktik mutakhir, atau kelompok peretas baru.",
    },
}

PROMPT_SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "config" / "prompts"

KEYWORD_GROUPS: Set[str] = {
    "spesifik",
    "general",
    "english",
    "indonesia_mandiri",
    "objek_data_sensitif",
    "objek_aset_digital",
    "indikator_insiden",
    "ambigu_butuh_konteks",
}

RSS_TYPES: Set[str] = {"international", "indonesia"}


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
            defaults = _default_gemini_values()
            cur = conn.cursor()
            cur.execute("SELECT nilai FROM pengaturan WHERE kunci = 'gemini.model_chain'")
            row = cur.fetchone()
            if row:
                try:
                    models = json.loads(row[0])
                except Exception:
                    models = []
                clean = [m for m in models if m not in OBSOLETE_MODELS]
                if not clean or any(m in OBSOLETE_MODELS for m in models) or (clean and clean[0] != "gemini-2.5-flash" and set(clean) == set(defaults["model_chain"])):
                    clean = defaults["model_chain"]
                if clean != models:
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = 'gemini.model_chain'", (json.dumps(clean),))
            else:
                cur.execute("INSERT INTO pengaturan (kunci, nilai, diubah) VALUES ('gemini.model_chain', ?, datetime('now'))", (json.dumps(defaults["model_chain"]),))

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
                for k, v in defaults["rate_limits"].items():
                    if k not in current_rl:
                        current_rl[k] = v
                if current_rl != (json.loads(row_rl[0]) if row_rl and row_rl[0] else {}):
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = 'gemini.rate_limits'", (json.dumps(current_rl),))
            else:
                cur.execute("INSERT INTO pengaturan (kunci, nilai, diubah) VALUES ('gemini.rate_limits', ?, datetime('now'))", (json.dumps(defaults["rate_limits"]),))

            cur.execute("SELECT nilai FROM pengaturan WHERE kunci = 'gemini.proactive_thresholds'")
            row_pt = cur.fetchone()
            if row_pt:
                try:
                    current_pt = json.loads(row_pt[0])
                except Exception:
                    current_pt = {}
                for obs in OBSOLETE_MODELS:
                    current_pt.pop(obs, None)
                for k, v in defaults["proactive_thresholds"].items():
                    if k not in current_pt:
                        current_pt[k] = v
                if current_pt != (json.loads(row_pt[0]) if row_pt and row_pt[0] else {}):
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = 'gemini.proactive_thresholds'", (json.dumps(current_pt),))
            else:
                cur.execute("INSERT INTO pengaturan (kunci, nilai, diubah) VALUES ('gemini.proactive_thresholds', ?, datetime('now'))", (json.dumps(defaults["proactive_thresholds"]),))

            # Bersihkan karakter BOM (\ufeff) dari template prompt
            cur.execute("SELECT kunci, nilai FROM pengaturan WHERE kunci LIKE 'prompt.%'")
            for p_kunci, p_nilai in cur.fetchall():
                if isinstance(p_nilai, str) and p_nilai.startswith("\ufeff"):
                    cur.execute("UPDATE pengaturan SET nilai = ? WHERE kunci = ?", (p_nilai.lstrip("\ufeff"), p_kunci))

            # Pastikan semua template prompt dari registri tersemat di database
            for p_id in PROMPT_METADATA:
                cur.execute("SELECT nilai FROM pengaturan WHERE kunci = ?", (f"prompt.{p_id}",))
                row_p = cur.fetchone()
                if not row_p or not row_p[0]:
                    snap_file = PROMPT_SNAPSHOT_DIR / f"{p_id}.txt"
                    if snap_file.exists():
                        try:
                            isi_snap = snap_file.read_text(encoding="utf-8-sig").lstrip("\ufeff")
                            cur.execute(
                                "INSERT OR REPLACE INTO pengaturan (kunci, nilai, diubah) VALUES (?, ?, datetime('now'))",
                                (f"prompt.{p_id}", isi_snap),
                            )
                        except Exception:
                            pass

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
            default_chain = _default_gemini_values()["model_chain"]
            if not val or (val and val[0] != "gemini-2.5-flash" and set(val) == set(default_chain)):
                val = list(default_chain)

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
            defaults = _default_gemini_values()["rate_limits"]
            if not isinstance(val, dict):
                val = dict(defaults)
            else:
                val = {k: float(v) for k, v in val.items() if k not in OBSOLETE_MODELS}
                for k, v in defaults.items():
                    if k not in val:
                        val[k] = v

        elif kunci == "gemini.proactive_thresholds":
            defaults = _default_gemini_values()["proactive_thresholds"]
            if not isinstance(val, dict):
                val = dict(defaults)
            else:
                val = {k: int(v) for k, v in val.items() if k not in OBSOLETE_MODELS}
                for k, v in defaults.items():
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

    @staticmethod
    def sanitize_api_key_list(value: Any) -> List[str]:
        """Menormalkan daftar API key: trim, buang kosong, dedup, pertahankan urutan."""
        if isinstance(value, str):
            parsed = [
                k.strip()
                for k in value.replace("\r\n", "\n").replace("\n", ",").split(",")
                if k.strip()
            ]
        elif isinstance(value, (list, tuple)):
            parsed = [str(k).strip() for k in value if str(k).strip()]
        else:
            raise PengaturanTidakValid("Daftar API Key harus berupa teks atau array.")
        return list(dict.fromkeys(parsed))

    @classmethod
    def sanitize_api_key(cls, value: Any) -> Any:
        """Menormalkan API key; satu key disimpan sebagai string seperti perilaku lama."""
        if isinstance(value, str):
            keys = cls.sanitize_api_key_list(value)
            return keys if len(keys) > 1 else (keys[0] if keys else "")
        if isinstance(value, (list, tuple)):
            return cls.sanitize_api_key_list(value)
        raise PengaturanTidakValid("API Key harus berupa teks atau array.")

    @staticmethod
    def sanitize_model_chain(value: Any) -> List[str]:
        """Membersihkan rantai model dari model usang dan duplikat."""
        if isinstance(value, str):
            daftar = value.replace("\r\n", "\n").replace("\n", ",").split(",")
        elif isinstance(value, (list, tuple)):
            daftar = list(value)
        else:
            raise PengaturanTidakValid("Model chain harus berupa teks atau array.")

        bersih: List[str] = []
        for item in daftar:
            model = str(item).strip()
            if not model or model in OBSOLETE_MODELS or model in bersih:
                continue
            bersih.append(model)
        return bersih

    @staticmethod
    def sanitize_embedding_fallbacks(value: Any) -> List[str]:
        """Membersihkan daftar fallback embedding dari nilai usang dan duplikat."""
        if isinstance(value, str):
            daftar = value.replace("\r\n", "\n").replace("\n", ",").split(",")
        elif isinstance(value, (list, tuple)):
            daftar = list(value)
        else:
            raise PengaturanTidakValid("Fallback embedding harus berupa teks atau array.")

        bersih: List[str] = []
        for item in daftar:
            model = str(item).strip()
            if not model or model == "embedding-001" or model in bersih:
                continue
            bersih.append(model)
        return bersih

    @staticmethod
    def sanitize_keywords(value: Any) -> List[str]:
        """Menormalkan kata kunci menjadi huruf kecil, unik, dan tanpa nilai kosong."""
        if isinstance(value, str):
            daftar = value.replace("\r\n", "\n").replace("\n", ",").split(",")
        elif isinstance(value, (list, tuple)):
            daftar = list(value)
        else:
            raise PengaturanTidakValid("Kata kunci harus berupa teks atau array.")

        bersih: List[str] = []
        for item in daftar:
            kata = str(item).strip().lower()
            if kata and kata not in bersih:
                bersih.append(kata)
        return bersih

    @classmethod
    def sanitize_rss_sources(cls, value: Any) -> List[dict]:
        """Memvalidasi struktur sumber RSS: nama wajib, feed unik, status boolean."""
        if not isinstance(value, list):
            raise PengaturanTidakValid("Sumber RSS harus berupa array.")

        bersih: List[dict] = []
        for item in value:
            if not isinstance(item, dict):
                raise PengaturanTidakValid("Setiap sumber RSS harus berupa objek.")
            nama = str(item.get("nama", "")).strip()
            if not nama:
                raise PengaturanTidakValid("Nama sumber RSS wajib diisi.")

            feeds = item.get("feeds", [])
            if isinstance(feeds, str):
                daftar_feed = [
                    f.strip() for f in feeds.replace("\n", ",").split(",") if f.strip()
                ]
            elif isinstance(feeds, list):
                daftar_feed = [str(f).strip() for f in feeds if str(f).strip()]
            else:
                raise PengaturanTidakValid("Feed RSS harus berupa teks atau array.")

            bersih.append({
                "nama": nama,
                "feeds": list(dict.fromkeys(daftar_feed)),
                "active": bool(item.get("active", True)),
            })
        return bersih

    @staticmethod
    def sanitize_rate_limits(value: Any) -> Dict[str, float]:
        """Memvalidasi rate limit per model sebagai angka positif."""
        if not isinstance(value, dict):
            raise PengaturanTidakValid("Rate limit harus berupa objek.")
        bersih: Dict[str, float] = {}
        for k, v in value.items():
            model = str(k).strip()
            if not model or model in OBSOLETE_MODELS:
                continue
            try:
                angka = float(v)
            except (TypeError, ValueError):
                raise PengaturanTidakValid(f"Rate limit model '{model}' harus berupa angka.")
            if angka <= 0:
                raise PengaturanTidakValid(f"Rate limit model '{model}' harus lebih dari nol.")
            bersih[model] = angka
        return bersih

    @staticmethod
    def sanitize_proactive_thresholds(value: Any) -> Dict[str, int]:
        """Memvalidasi ambang proaktif per model sebagai bilangan bulat positif."""
        if not isinstance(value, dict):
            raise PengaturanTidakValid("Ambang proaktif harus berupa objek.")
        bersih: Dict[str, int] = {}
        for k, v in value.items():
            model = str(k).strip()
            if not model or model in OBSOLETE_MODELS:
                continue
            try:
                angka = int(v)
            except (TypeError, ValueError):
                raise PengaturanTidakValid(f"Ambang proaktif model '{model}' harus berupa bilangan bulat.")
            if angka <= 0:
                raise PengaturanTidakValid(f"Ambang proaktif model '{model}' harus lebih dari nol.")
            bersih[model] = angka
        return bersih

    @classmethod
    def reset_prompt(cls, nama: str) -> str:
        """Mengembalikan isi prompt ke snapshot beku `config/prompts/<nama>.txt`."""
        if nama not in PROMPT_METADATA:
            raise PengaturanTidakValid("Nama prompt tidak dikenal.")
        path = PROMPT_SNAPSHOT_DIR / f"{nama}.txt"
        if not path.exists():
            raise FileNotFoundError(f"Snapshot prompt tidak ditemukan: {path}")

        isi = path.read_text(encoding="utf-8-sig")
        cls.set(f"prompt.{nama}", isi)
        return isi

    @classmethod
    def get_keywords(cls) -> dict:
        """Membaca semua grup kata kunci langsung dari database SQLite (tabel pengaturan)."""
        res = {
            grup: cls.get(f"keywords.{grup}", [])
            for grup in ["spesifik", "general", "english", "indonesia_mandiri", "objek_data_sensitif",
                         "objek_aset_digital", "indikator_insiden", "ambigu_butuh_konteks"]
        }
        if not res.get("spesifik"):
            res["spesifik"] = list(dict.fromkeys((res.get("indonesia_mandiri") or []) + (res.get("english") or [])))
        if not res.get("general"):
            res["general"] = list(dict.fromkeys(
                (res.get("objek_data_sensitif") or []) +
                (res.get("objek_aset_digital") or []) +
                (res.get("indikator_insiden") or []) +
                (res.get("ambigu_butuh_konteks") or [])
            ))
        return res

    @classmethod
    def get_prompt(cls, nama: str) -> str:
        """Membaca template prompt CTI langsung dari database SQLite (tabel pengaturan), dengan fallback cerdas ke berkas konfigurasi lokal."""
        if nama in ("kasus_wilayah", "section_wilayah") and "kasus_insiden_wilayah" in PROMPT_METADATA:
            nama = "kasus_insiden_wilayah"
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
        """Mengembalikan daftar prompt aktif dengan metadata nama, kategori, dan deskripsi dari database."""
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
