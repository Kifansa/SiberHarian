import json
import re
from typing import List, Optional

import pandas as pd
from src.utils.config_loader import ConfigLoader
from src.utils.llm_adapter import GeminiLLMAdapter
from src.utils.logger import setup_logger
from src.utils.settings_manager import SettingsManager

logger = setup_logger(__name__)

MAKS_KARAKTER_UNTUK_KLASIFIKASI = (
    ConfigLoader.get_config().get("gemini", {}).get("max_karakter_klasifikasi", 1500)
)
KATEGORI_VALID = {"insiden_spesifik", "analisis_relevan", "tidak_relevan"}
BATCH_SIZE_DEFAULT = 5


def _ekstrak_label(respons_mentah: str) -> Optional[str]:
    """Parsing label dari respons LLM untuk evaluasi artikel tunggal."""
    if not respons_mentah:
        return None

    for baris in respons_mentah.splitlines():
        baris_lower = baris.strip().lower()
        if "kategori" in baris_lower or "category" in baris_lower:
            for label in ("insiden_spesifik", "analisis_relevan", "tidak_relevan"):
                if label in baris_lower:
                    return label

    baris_terakhir = respons_mentah.strip().splitlines()[-1].lower()
    for label in ("insiden_spesifik", "analisis_relevan", "tidak_relevan"):
        if label in baris_terakhir:
            return label

    teks = respons_mentah.strip().lower()
    for label in ("insiden_spesifik", "tidak_relevan", "analisis_relevan"):
        if label in teks:
            return label

    return None


def klasifikasi_relevansi(judul: str, teks_asli: str, model: str = None) -> str:
    """Mengklasifikasikan satu artikel dengan fallback aman ke analisis_relevan."""
    teks_dipotong = teks_asli[:MAKS_KARAKTER_UNTUK_KLASIFIKASI]
    user_prompt = f"Judul: {judul}\n\nCuplikan isi:\n{teks_dipotong}"

    try:
        system_prompt = SettingsManager.get_prompt("klasifikasi")
        respons_teks = GeminiLLMAdapter.chat(system_prompt, user_prompt, temperature=0.0)
        label = _ekstrak_label(respons_teks)
        if label:
            return label
        logger.warning(f"Gagal parsing label untuk '{judul[:50]}...', menggunakan fallback analisis_relevan.")
        return "analisis_relevan"
    except Exception as e:
        logger.error(f"Gagal memanggil classifier untuk '{judul[:50]}...': {e}")
        return "analisis_relevan"


def _ekstrak_json_batch(respons: str) -> Optional[List[dict]]:
    """Mengekstrak list JSON dari respons batch LLM."""
    if not respons:
        return None

    match = re.search(r"\[\s*\{.*?\}\s*\]", respons, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

    # Fallback pencarian baris per baris format id dan kategori
    hasil = []
    pola = re.compile(r'ART-(\d+)["\s:]+([a-zA-Z_]+)', re.IGNORECASE)
    for match in pola.finditer(respons):
        idx = int(match.group(1))
        label_raw = match.group(2).lower().strip()
        label = label_raw if label_raw in KATEGORI_VALID else "analisis_relevan"
        hasil.append({"id": f"ART-{idx}", "kategori": label})

    return hasil if hasil else None


def klasifikasi_batch_5(daftar_artikel: List[dict], model: str = None) -> List[str]:
    """
    Mengklasifikasikan hingga 5 artikel sekaligus dalam 1 prompt terstruktur.
    Jika format respons tidak lengkap, otomatis mundur ke pemrosesan per artikel.
    """
    if not daftar_artikel:
        return []

    konten_dokumen = []
    for idx, art in enumerate(daftar_artikel, start=1):
        judul = art.get("judul", "")
        teks = art.get("teks_asli", "")[:MAKS_KARAKTER_UNTUK_KLASIFIKASI]
        konten_dokumen.append(
            f'<artikel id="ART-{idx}">\nJudul: {judul}\nCuplikan isi: {teks}\n</artikel>'
        )

    user_prompt = (
        "Klasifikasikan setiap artikel berikut ke dalam salah satu label valid:\n"
        "- insiden_spesifik: insiden siber nyata, ransomware, kebocoran data, deface, malware aktif\n"
        "- analisis_relevan: riset keamanan siber, analisis ancaman, advisori keamanan penting\n"
        "- tidak_relevan: berita umum, lifestyle, gadget konsumen, politik tanpa insiden siber\n\n"
        "Format jawaban WAJIB array JSON valid berisi pasangan ID dan kategori:\n"
        "[\n"
        '  {"id": "ART-1", "kategori": "<label>"}\n'
        "]\n\n"
        "Daftar Dokumen:\n" + "\n\n".join(konten_dokumen)
    )

    system_prompt = (
        SettingsManager.get_prompt("klasifikasi")
        or "Anda adalah analis CTI (Cyber Threat Intelligence). Tugas Anda mengklasifikasikan "
        "relevansi artikel berita ke kategori valid. Jawab strictly dalam format JSON array."
    )

    respons = GeminiLLMAdapter.chat(system_prompt, user_prompt, temperature=0.0)
    data_json = _ekstrak_json_batch(respons)

    if data_json:
        peta_hasil = {}
        for item in data_json:
            id_str = str(item.get("id", "")).upper()
            kat = str(item.get("kategori", "")).lower()
            if kat in KATEGORI_VALID:
                peta_hasil[id_str] = kat

        # Pastikan seluruh ID dalam batch terpetakan
        semua_lengkap = all(f"ART-{i}" in peta_hasil for i in range(1, len(daftar_artikel) + 1))
        if semua_lengkap:
            return [peta_hasil[f"ART-{i}"] for i in range(1, len(daftar_artikel) + 1)]

    logger.warning("Respons batch tidak lengkap atau parsing gagal. Melakukan auto-fallback per artikel...")
    hasil_fallback = []
    for art in daftar_artikel:
        lbl = klasifikasi_relevansi(art.get("judul", ""), art.get("teks_asli", ""), model)
        hasil_fallback.append(lbl)
    return hasil_fallback


def filter_artikel_relevan(df: pd.DataFrame, model: str = None) -> pd.DataFrame:
    """
    Menjalankan klasifikasi batch 5 artikel, membuang artikel tidak_relevan,
    dan menyimpan label relevansi untuk artikel yang tersisa.
    """
    if df.empty:
        return df

    df = df.copy().reset_index(drop=True)
    label_list = []
    total = len(df)

    logger.info(f"Mengklasifikasikan relevansi {total} artikel dalam batch 5 artikel...")
    for start in range(0, total, BATCH_SIZE_DEFAULT):
        end = min(start + BATCH_SIZE_DEFAULT, total)
        batch_rows = [df.iloc[k].to_dict() for k in range(start, end)]
        batch_labels = klasifikasi_batch_5(batch_rows, model=model)
        label_list.extend(batch_labels)

        for offset, lbl in enumerate(batch_labels):
            idx = start + offset
            logger.info(f"[{idx+1}/{total}] [{lbl}] {df.iloc[idx]['judul'][:55]}...")

    df["kategori_relevansi"] = label_list
    jumlah_sebelum = len(df)
    df_relevan = df[df["kategori_relevansi"] != "tidak_relevan"].reset_index(drop=True)
    jumlah_dibuang = jumlah_sebelum - len(df_relevan)

    logger.info(
        f"Filter relevansi LLM: {jumlah_sebelum} -> {len(df_relevan)} "
        f"({jumlah_dibuang} dibuang sebagai tidak relevan)"
    )
    return df_relevan
