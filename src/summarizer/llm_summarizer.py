from typing import Optional
import pandas as pd

from src.utils.config_loader import ConfigLoader
from src.utils.llm_adapter import GeminiLLMAdapter
from src.utils.llm_text_cleaner import bersihkan_output_llm
from src.utils.logger import setup_logger
from src.utils.settings_manager import SettingsManager

logger = setup_logger(__name__)

MAKS_KARAKTER_ARTIKEL = ConfigLoader.get_config().get("gemini", {}).get("max_karakter_artikel", 4000)


def _panggil_llm(system_prompt: str, user_prompt: str, model: str = None) -> Optional[str]:
    """Memanggil model via Gemini API melalui adapter terpusat."""
    hasil = GeminiLLMAdapter.chat(system_prompt, user_prompt, temperature=0.3)
    return hasil if hasil else None


def ringkas_berita(judul: str, teks_asli: str, model: str = None) -> Optional[str]:
    """Meringkas satu artikel berita insiden siber menjadi 2-3 kalimat Bahasa Indonesia."""
    teks_dipotong = teks_asli[:MAKS_KARAKTER_ARTIKEL]
    user_prompt = f"Judul: {judul}\n\nIsi artikel:\n{teks_dipotong}"
    hasil = _panggil_llm(SettingsManager.get_prompt("ringkas_berita"), user_prompt, model)
    return bersihkan_output_llm(hasil, judul_atau_id=judul)


def narasikan_cve(cve: dict, model: str = None) -> Optional[str]:
    """Menarasikan satu CVE kritis/tinggi menjadi penjelasan 2-3 kalimat Bahasa Indonesia."""
    vendor = cve.get("vendor", "")
    produk = cve.get("produk", "")
    if not vendor or "Lainnya" in vendor or "Belum" in vendor:
        vendor_produk_baris = "Lainnya / Belum Teridentifikasi"
    else:
        vendor_produk_baris = f"{vendor} - {produk or '-'}"

    user_prompt = (
        f"CVE ID: {cve.get('cve_id', '')}\n"
        f"Skor CVSS: {cve.get('skor_cvss', '')} ({cve.get('severity', '')})\n"
        f"Produk/Vendor: {vendor_produk_baris}\n"
        f"Deskripsi asli: {cve.get('deskripsi', '')}"
    )
    hasil = _panggil_llm(SettingsManager.get_prompt("ringkas_cve"), user_prompt, model)
    return bersihkan_output_llm(hasil, judul_atau_id=cve.get("cve_id", ""))


def ringkas_semua_berita(df_berita: pd.DataFrame, model: str = None) -> pd.DataFrame:
    """
    Meringkas setiap artikel secara 1-per-1 untuk menjaga pemisahan konteks dan integritas fakta.
    Laju request dikendalikan otomatis oleh GeminiRateLimiter pada adapter.
    """
    if df_berita.empty:
        return df_berita

    df_berita = df_berita.copy()
    ringkasan_list = []

    for i, row in df_berita.iterrows():
        logger.info(f"Meringkas [{i+1}/{len(df_berita)}]: {row['judul'][:50]}...")
        ringkasan = ringkas_berita(row["judul"], row["teks_asli"], model)

        if ringkasan is None:
            logger.warning(f"Fallback ke cuplikan teks asli untuk: {row['judul'][:50]}")
            ringkasan = row["teks_asli"][:200].strip() + "..."

        ringkasan_list.append(ringkasan)

    df_berita["ringkasan"] = ringkasan_list
    return df_berita


def ringkas_daftar_cve(daftar_cve: list, model: str = None) -> list:
    """Menambahkan narasi ke setiap dict CVE secara sekuensial dengan rate limiter terpusat."""
    for cve in daftar_cve:
        logger.info(f"Menarasikan {cve.get('severity', '')}: {cve.get('cve_id', '')}")
        narasi = narasikan_cve(cve, model)
        cve["narasi"] = narasi or (cve.get("deskripsi", "")[:200] + "...")
    return daftar_cve


def proses_summarization_harian(hasil_pipeline: dict, model: str = None) -> dict:
    """Titik masuk utama summarization harian untuk berita dan CVE."""
    logger.info("Memulai proses summarization berita...")
    df_berita_ringkas = ringkas_semua_berita(hasil_pipeline["berita"], model)

    cve_struktur = hasil_pipeline.get("cve_struktur", {})
    if cve_struktur.get("mode") == "ada_critical":
        for grup in cve_struktur.get("grup_critical", []):
            ringkas_daftar_cve(grup.get("cve_list", []), model)

    logger.info("Summarization selesai.")
    return {"berita": df_berita_ringkas, "cve_struktur": cve_struktur}
