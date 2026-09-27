import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.storage.db import DEFAULT_DB_PATH, init_db
from src.utils.config_loader import ConfigLoader
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Registri 10 prompt aktif dengan nama ramah pengguna, kategori, dan deskripsi
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
    "ringkas_cve": {
        "nama": "Narasi Kerentanan CVE",
        "kategori": "Pipeline Harian",
        "deskripsi": "Menerjemahkan dan menarasikan CVE kritis dari NVD ke bahasa Indonesia.",
    },
    "section_1_makro": {
        "nama": "SITREP Berita - 1. Lanskap Makro",
        "kategori": "SITREP Tren Berita",
        "deskripsi": "Sintesis pola ancaman makro berdasarkan lonjakan insiden riil mingguan.",
    },
    "section_2_mikro": {
        "nama": "SITREP Berita - 2. Insiden Mikro",
        "kategori": "SITREP Tren Berita",
        "deskripsi": "Analisis mendalam terhadap top 3 insiden dominan dalam 7 hari terakhir.",
    },
    "section_3_vektor": {
        "nama": "SITREP Berita - 3. Vektor Serangan",
        "kategori": "SITREP Tren Berita",
        "deskripsi": "Pemetaan metode serangan teknis dan sektor sasaran yang terdampak.",
    },
    "section_5_emerging": {
        "nama": "SITREP Berita - 4. Ancaman Baru",
        "kategori": "SITREP Tren Berita",
        "deskripsi": "Deteksi varian malware baru, taktik mutakhir, atau kelompok peretas baru.",
    },
    "cve_sec1_vendor": {
        "nama": "SITREP CVE - 1. Vendor & Produk Prioritas",
        "kategori": "SITREP Tren Kerentanan CVE",
        "deskripsi": "Analisis vendor perangkat lunak dan produk dengan lonjakan CVE kritis tertinggi.",
    },
    "cve_sec2_vektor": {
        "nama": "SITREP CVE - 2. Vektor Eksploitasi",
        "kategori": "SITREP Tren Kerentanan CVE",
        "deskripsi": "Analisis tipe kerentanan dominan (Remote Code Execution, Auth Bypass, DoS).",
    },
    "cve_sec3_kripto": {
        "nama": "SITREP CVE - 3. Eksploitabilitas & Weaponization (PoC)",
        "kategori": "SITREP Tren Kerentanan CVE",
        "deskripsi": "Analisis ketersediaan exploit publik, kemudahan weaponization, dan bukti konsep (PoC).",
    },
}


class SettingsManager:
    """
    Manajer pengaturan persisten berbasis SQLite dengan fallback cerdas ke file konfigurasi.
    Menyimpan perubahan admin ke tabel `pengaturan` di state.db sehingga berlaku instan
    tanpa perlu me-restart server.
    """

    _initialized = False

    @classmethod
    def _conn(cls):
        if not cls._initialized:
            init_db(DEFAULT_DB_PATH)
            cls._initialized = True
        return sqlite3.connect(DEFAULT_DB_PATH)

    @classmethod
    def get(cls, kunci: str, default: Any = None) -> Any:
        """Ambil setting dari DB. Jika belum ada, kembalikan default."""
        try:
            conn = cls._conn()
            row = conn.execute(
                "SELECT nilai FROM pengaturan WHERE kunci = ?", (kunci,)
            ).fetchone()
            conn.close()
            if row:
                try:
                    return json.loads(row[0])
                except (json.JSONDecodeError, TypeError):
                    return row[0]
        except Exception:
            pass
        return default

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
            "temperature": cls.get("gemini.temperature", yaml_cfg.get("temperature", 0.1)),
            "max_output_tokens": cls.get("gemini.max_output_tokens", yaml_cfg.get("max_output_tokens", 500)),
            "embedding_model": cls.get("gemini.embedding_model", yaml_cfg.get("embedding_model", "text-embedding-004")),
            "rate_limits": cls.get("gemini.rate_limits", yaml_cfg.get("rate_limits", {})),
            "batch_sizes": cls.get("gemini.batch_sizes", yaml_cfg.get("batch_sizes", {})),
        }

    @classmethod
    def get_keywords(cls) -> dict:
        """Membaca semua grup kata kunci: DB override, YAML fallback."""
        yaml_kw = ConfigLoader.get_config().get("keywords", {})
        return {
            grup: cls.get(f"keywords.{grup}", yaml_kw.get(grup, []))
            for grup in ["english", "indonesia_mandiri", "objek_data_sensitif",
                         "objek_aset_digital", "indikator_insiden", "ambigu_butuh_konteks"]
        }

    @classmethod
    def get_prompt(cls, nama: str) -> str:
        """Baca prompt: DB override, file fallback."""
        db_val = cls.get(f"prompt.{nama}")
        if db_val:
            return db_val
        return ConfigLoader.get_prompt(nama)

    @classmethod
    def get_all_prompts_info(cls) -> List[dict]:
        """Mengembalikan daftar 10 prompt aktif dengan metadata nama, kategori, dan deskripsi."""
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
        """Baca RSS sources: DB override, YAML fallback. tipe = 'international' atau 'indonesia'."""
        key = f"rss_sources_{tipe}"
        db_val = cls.get(key)
        if db_val is not None:
            return db_val

        yaml_sources = ConfigLoader.get_config().get(key, [])
        for s in yaml_sources:
            if "active" not in s:
                s["active"] = True
        return yaml_sources
