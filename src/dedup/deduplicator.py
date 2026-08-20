"""
Deteksi dan penghapusan duplikat:
1. Duplikat lintas hari - artikel/CVE yang sudah pernah dikirim
   sebelumnya (dicek terhadap database state).
2. Duplikat dalam hari yang sama - artikel dari media berbeda yang
   membahas insiden yang sama (dideteksi lewat kemiripan judul).
"""
from pathlib import Path
from typing import List

import ollama
import pandas as pd
from rapidfuzz import fuzz

from src.storage.db import ambil_identifier_terkirim
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def filter_belum_terkirim(
    df: pd.DataFrame, kategori: str, kolom_identifier: str, db_path: Path
) -> pd.DataFrame:
    """
    Membuang baris yang identifier-nya (URL untuk berita, cve_id untuk
    CVE) sudah pernah tercatat terkirim sebelumnya.
    """
    if df.empty:
        return df

    identifier_lama = ambil_identifier_terkirim(kategori, db_path)
    jumlah_awal = len(df)
    df_baru = df[~df[kolom_identifier].isin(identifier_lama)].reset_index(drop=True)

    jumlah_dibuang = jumlah_awal - len(df_baru)
    if jumlah_dibuang > 0:
        logger.info(f"[{kategori}] {jumlah_dibuang} item dibuang karena sudah pernah dikirim sebelumnya.")
    return df_baru

def _hitung_cosine_similarity(vektor_a: list, vektor_b: list) -> float:
    """
    Menghitung cosine similarity antara 2 vektor embedding secara manual
    (tanpa numpy/scipy tambahan, cukup pakai operasi dasar Python untuk
    menjaga dependency tetap minim untuk operasi sesederhana ini).
    """
    dot_product = sum(a * b for a, b in zip(vektor_a, vektor_b))
    norma_a = sum(a * a for a in vektor_a) ** 0.5
    norma_b = sum(b * b for b in vektor_b) ** 0.5
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return dot_product / (norma_a * norma_b)


def _ambil_embedding(teks: str, model: str = "qwen3-embedding:0.6b") -> list:
    """Memanggil Ollama untuk mendapatkan vektor embedding dari sebuah teks."""
    respons = ollama.embeddings(model=model, prompt=teks)
    return respons["embedding"]


def deteksi_duplikat_hybrid(
    df: pd.DataFrame,
    kolom_judul: str = "judul",
    threshold_rapidfuzz_shortcut: int = 95,
    threshold_embedding: float = 0.60,
    model_embedding: str = "qwen3-embedding:0.6b",
) -> pd.DataFrame:
    """
    Deteksi duplikat berbasis EMBEDDING SEMANTIK sebagai penentu utama.
    Rapidfuzz TIDAK dipakai sebagai penentu (terbukti dari kalibrasi
    dengan data nyata: rentang skornya tumpang tindih antara kasus
    duplikat dan non-duplikat, sehingga tidak valid untuk membedakan
    keduanya untuk judul berita Bahasa Indonesia). Rapidfuzz hanya
    dipakai sebagai shortcut hemat komputasi untuk kasus judul yang
    identik/nyaris identik (skor sangat tinggi), untuk skip panggilan
    embedding yang tidak perlu.

    Threshold embedding 0.50 dikalibrasi dari data nyata: skor duplikat
    asli berkisar 0.58-0.86, skor non-duplikat 0.27-0.32 - ada celah
    besar di antaranya, 0.50 dipilih di titik tengah untuk margin aman.
    """
    if df.empty or len(df) <= 1:
        return df

    df = df.reset_index(drop=True)

    # Hitung embedding untuk semua judul di awal (1x panggilan model per judul)
    logger.info(f"Menghitung embedding untuk {len(df)} judul...")
    daftar_embedding = []
    for judul in df[kolom_judul]:
        try:
            daftar_embedding.append(_ambil_embedding(judul, model_embedding))
        except Exception as e:
            logger.warning(f"Gagal menghitung embedding untuk '{judul[:40]}...': {e}")
            daftar_embedding.append(None)

    sudah_diproses = set()
    baris_hasil = []

    for i in range(len(df)):
        if i in sudah_diproses:
            continue

        judul_i = df.loc[i, kolom_judul]
        grup_mirip = [i]

        for j in range(i + 1, len(df)):
            if j in sudah_diproses:
                continue

            judul_j = df.loc[j, kolom_judul]

            # Lapis 1: cek cepat pakai rapidfuzz dulu
            skor_fuzzy = fuzz.token_sort_ratio(judul_i, judul_j)
            if skor_fuzzy >= threshold_rapidfuzz_shortcut:
                grup_mirip.append(j)
                continue

            # Lapis 2: kalau rapidfuzz tidak yakin, cek makna via embedding
            if daftar_embedding[i] is not None and daftar_embedding[j] is not None:
                skor_semantic = _hitung_cosine_similarity(daftar_embedding[i], daftar_embedding[j])
                if skor_semantic >= threshold_embedding:
                    grup_mirip.append(j)
                    logger.debug(
                        f"Duplikat terdeteksi via embedding (skor {skor_semantic:.2f}): "
                        f"'{judul_i[:40]}...' ~ '{judul_j[:40]}...'"
                    )

        sudah_diproses.update(grup_mirip)

        if len(grup_mirip) == 1:
            baris_hasil.append(df.loc[i].to_dict())
        else:
            subset = df.loc[grup_mirip]
            idx_representatif = subset["teks_asli"].str.len().idxmax()
            baris_terpilih = df.loc[idx_representatif].to_dict()
            daftar_sumber = subset["sumber"].unique().tolist()
            baris_terpilih["sumber_lain"] = [s for s in daftar_sumber if s != baris_terpilih["sumber"]]
            baris_hasil.append(baris_terpilih)
            logger.info(f"Menggabungkan {len(grup_mirip)} berita mirip (representatif: '{baris_terpilih['judul'][:50]}...'):")
            for idx_anggota in grup_mirip:
                logger.info(f"    - [{idx_anggota}] {df.loc[idx_anggota, kolom_judul][:70]}")

    df_hasil = pd.DataFrame(baris_hasil)
    if len(df_hasil) < len(df):
        logger.info(f"Deduplikasi hybrid: {len(df)} -> {len(df_hasil)} entri.")
    return df_hasil