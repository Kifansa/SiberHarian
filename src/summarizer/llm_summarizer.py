import re
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


def _buat_fallback_ringkasan(judul: str, teks_asli: str) -> str:
    """
    Menyusun ringkasan fallback yang utuh, bersih dari sampah markup web,
    dan selalu berupa kalimat lengkap apabila API LLM tidak dapat dihubungi.
    """
    teks = (teks_asli or "").strip()
    # Bersihkan sampah navigasi / markup umum dari web
    teks = re.sub(r"^/?[A-Za-z0-9_/]+(?:\)|:)\s*", "", teks)
    teks = re.sub(r"https?://\S+", "", teks)
    teks = re.sub(r"[\r\n]+", " ", teks)
    teks = re.sub(r"\s+", " ", teks).strip()

    # Bersihkan judul untuk sintesis
    judul_bersih = re.sub(r"\s+-\s+[^-]+$", "", judul).strip().rstrip(".:-")

    # Jika teks mentah cukup panjang (>= 90 karakter), potong pada batas kalimat utuh
    if len(teks) >= 90:
        cuplikan = teks[:250].strip()
        # Cari tanda titik atau tanda baca pengakhir kalimat terakhir
        pos_titik = max(cuplikan.rfind(". "), cuplikan.rfind(".\n"), cuplikan.rfind("! "), cuplikan.rfind("? "))
        if pos_titik > 60:
            return cuplikan[:pos_titik + 1].strip()
        # Jika tidak ada titik dalam rentang tersebut, potong di kata terakhir dan beri titik
        pos_spasi = cuplikan.rfind(" ")
        if pos_spasi > 60:
            return cuplikan[:pos_spasi].rstrip(",;:- ") + "."
        return cuplikan.rstrip(",;:- ") + "."

    # Fallback sintetis berbasis judul jika konten mentah sangat pendek / tidak lengkap
    return f"Laporan keamanan siber terkait {judul_bersih}. Peristiwa ini menguraikan dinamika insiden dan langkah mitigasi yang diperlukan."


def ringkas_berita(judul: str, teks_asli: str, model: str = None) -> Optional[str]:
    """Meringkas satu artikel berita insiden siber menjadi 2-3 kalimat Bahasa Indonesia."""
    teks_dipotong = teks_asli[:MAKS_KARAKTER_ARTIKEL]
    user_prompt = f"Judul: {judul}\n\nIsi artikel:\n{teks_dipotong}"
    hasil = _panggil_llm(SettingsManager.get_prompt("ringkas_berita"), user_prompt, model)
    return bersihkan_output_llm(hasil, judul_atau_id=judul)


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

        if not ringkasan or len(ringkasan.strip()) < 40:
            logger.warning(f"Fallback ke cuplikan aman untuk: {row['judul'][:50]}")
            ringkasan = _buat_fallback_ringkasan(row["judul"], row["teks_asli"])

        ringkasan_list.append(ringkasan)

    df_berita["ringkasan"] = ringkasan_list
    return df_berita


def proses_summarization_harian(hasil_pipeline: dict, model: str = None) -> dict:
    """Titik masuk utama summarization harian untuk berita siber."""
    logger.info("Memulai proses summarization berita...")
    df_berita_ringkas = ringkas_semua_berita(hasil_pipeline["berita"], model)
    logger.info("Summarization selesai.")
    return {"berita": df_berita_ringkas}
