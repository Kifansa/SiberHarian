"""
Script debug manual: menjalankan pipeline penuh (scraping -> summarization
-> prediksi tren) dan mengekspor HASIL MENTAH, RINGKASAN, dan PREDIKSI TREN
ke 3 file terpisah untuk keperluan perbandingan/QA manual.

Jalankan: python -m scripts.bandingkan_hasil
"""
from pathlib import Path

import pandas as pd

from src.analytics.pasca_proses import proses_arsip_dan_tren
from src.pipeline_harian import jalankan_pipeline_harian
from src.summarizer.llm_summarizer import proses_summarization_harian

FOLDER_OUTPUT = Path("data/debug")


def _ekstrak_baris_cve_mentah(cve_struktur: dict) -> list:
    """Meratakan struktur CVE (mode ada_critical/high_saja) jadi list baris datar."""
    baris = []
    if cve_struktur["mode"] == "ada_critical":
        for grup in cve_struktur["grup_critical"]:
            for cve in grup["cve_list"]:
                baris.append(cve)
    elif cve_struktur["mode"] == "high_saja":
        baris.extend(cve_struktur["high_untuk_narasi"])
    return baris


def main() -> None:
    FOLDER_OUTPUT.mkdir(parents=True, exist_ok=True)

    print("Menjalankan pipeline pengumpulan data (scraping + CVE)...")
    hasil_mentah = jalankan_pipeline_harian()

    # --- FILE 1: HASIL MENTAH (sebelum diringkas LLM) ---
    df_berita_mentah = hasil_mentah["berita"]
    if not df_berita_mentah.empty:
        df_berita_mentah[["sumber", "judul", "tanggal", "teks_asli", "link"]].to_csv(
            FOLDER_OUTPUT / "01_berita_mentah.csv", index=False, encoding="utf-8-sig"
        )
        print(f"  -> {len(df_berita_mentah)} berita mentah disimpan ke {FOLDER_OUTPUT / '01_berita_mentah.csv'}")
    else:
        print("  -> Tidak ada berita mentah untuk disimpan.")

    baris_cve_mentah = _ekstrak_baris_cve_mentah(hasil_mentah["cve_struktur"])
    if baris_cve_mentah:
        pd.DataFrame(baris_cve_mentah)[["cve_id", "severity", "skor_cvss", "vendor", "produk", "deskripsi", "link"]].to_csv(
            FOLDER_OUTPUT / "01_cve_mentah.csv", index=False, encoding="utf-8-sig"
        )
        print(f"  -> {len(baris_cve_mentah)} CVE mentah disimpan ke {FOLDER_OUTPUT / '01_cve_mentah.csv'}")
    else:
        print("  -> Tidak ada CVE mentah untuk disimpan.")

    # --- Proses summarization + prediksi tren ---
    print("\nMenjalankan summarization & prediksi tren (LLM)...")
    hasil_ringkas = proses_summarization_harian(hasil_mentah)
    hasil_ringkas = proses_arsip_dan_tren(hasil_ringkas)

    # --- FILE 2: HASIL RINGKASAN ---
    df_berita_ringkas = hasil_ringkas["berita"]
    if not df_berita_ringkas.empty:
        df_berita_ringkas[["sumber", "judul", "tanggal", "ringkasan", "link"]].to_csv(
            FOLDER_OUTPUT / "02_berita_ringkasan.csv", index=False, encoding="utf-8-sig"
        )
        print(f"  -> {len(df_berita_ringkas)} ringkasan berita disimpan ke {FOLDER_OUTPUT / '02_berita_ringkasan.csv'}")

    baris_cve_narasi = _ekstrak_baris_cve_mentah(hasil_ringkas["cve_struktur"])
    if baris_cve_narasi:
        pd.DataFrame(baris_cve_narasi)[["cve_id", "severity", "skor_cvss", "vendor", "narasi", "link"]].to_csv(
            FOLDER_OUTPUT / "02_cve_narasi.csv", index=False, encoding="utf-8-sig"
        )
        print(f"  -> {len(baris_cve_narasi)} narasi CVE disimpan ke {FOLDER_OUTPUT / '02_cve_narasi.csv'}")

    # --- FILE 3: HASIL PREDIKSI TREN ---
    prediksi = hasil_ringkas["prediksi_tren"]
    teks_prediksi = (
        "=== PREDIKSI TREN BERITA (7 hari terakhir) ===\n"
        f"{prediksi['prediksi_berita']}\n\n"
        "=== PREDIKSI TREN CVE (7 hari terakhir) ===\n"
        f"{prediksi['prediksi_cve']}\n"
    )
    (FOLDER_OUTPUT / "03_prediksi_tren.txt").write_text(teks_prediksi, encoding="utf-8")
    print(f"  -> Prediksi tren disimpan ke {FOLDER_OUTPUT / '03_prediksi_tren.txt'}")

    print(f"\nSELESAI. Semua file pembanding ada di folder: {FOLDER_OUTPUT.resolve()}")


if __name__ == "__main__":
    main()