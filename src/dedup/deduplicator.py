"""
Deteksi dan penghapusan duplikat:
1. Duplikat lintas hari - artikel/CVE yang sudah pernah dikirim sebelumnya.
2. Duplikat dalam hari yang sama - dideteksi lewat kemiripan judul (rapidfuzz & batch semantic embedding).
"""
from pathlib import Path
from typing import List

from src.utils.embedding_adapter import GeminiEmbeddingAdapter
import pandas as pd
from rapidfuzz import fuzz

from src.storage.db import ambil_identifier_terkirim
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def filter_belum_terkirim(
    df: pd.DataFrame, kategori: str, kolom_identifier: str, db_path: Path
) -> pd.DataFrame:
    """Membuang baris yang identifier-nya sudah pernah tercatat terkirim sebelumnya."""
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
    """Menghitung cosine similarity antara 2 vektor embedding."""
    dot_product = sum(a * b for a, b in zip(vektor_a, vektor_b))
    norma_a = sum(a * a for a in vektor_a) ** 0.5
    norma_b = sum(b * b for b in vektor_b) ** 0.5
    if norma_a == 0 or norma_b == 0:
        return 0.0
    return dot_product / (norma_a * norma_b)


def _ambil_embedding(teks: str, model: str = None) -> list:
    """Memanggil Gemini untuk mendapatkan vektor embedding dari sebuah teks."""
    return GeminiEmbeddingAdapter.embed(teks)


def deteksi_duplikat_hybrid(
    df: pd.DataFrame,
    kolom_judul: str = "judul",
    threshold_rapidfuzz_shortcut: int = 95,
    threshold_embedding: float = 0.75,
    model_embedding: str = None,
) -> pd.DataFrame:
    """
    Deteksi duplikat berbasis batch semantic embedding dan shortcut rapidfuzz.
    Seluruh judul diproses dalam 1 panggilan batch resmi Google API.
    """
    if df.empty or len(df) <= 1:
        return df

    df = df.reset_index(drop=True)

    # Batch embedding untuk seluruh judul sekaligus (1 pemanggilan API)
    logger.info(f"Menghitung batch embedding untuk {len(df)} judul...")
    daftar_judul = df[kolom_judul].astype(str).tolist()
    daftar_embedding = GeminiEmbeddingAdapter.embed_batch(daftar_judul, batch_size=50)

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

            # Cek shortcut kesamaan string tinggi dengan rapidfuzz
            skor_fuzzy = fuzz.token_sort_ratio(judul_i, judul_j)
            if skor_fuzzy >= threshold_rapidfuzz_shortcut:
                grup_mirip.append(j)
                continue

            # Validasi makna semantik dengan embedding
            if i < len(daftar_embedding) and j < len(daftar_embedding):
                emb_i = daftar_embedding[i]
                emb_j = daftar_embedding[j]
                if emb_i is not None and emb_j is not None:
                    skor_semantic = _hitung_cosine_similarity(emb_i, emb_j)
                    if skor_semantic >= threshold_embedding:
                        grup_mirip.append(j)
                        logger.debug(
                            f"Duplikat terdeteksi via embedding ({skor_semantic:.2f}): "
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
