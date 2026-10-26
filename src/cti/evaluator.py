"""
SiberHarian CTI Evaluation Framework & Dataset Generator (Milestone 7 / Tahap 6, R4).

Menyediakan kerangka kerja evaluasi kinerja pipeline intelijen siber:
1. `generate_draft_dataset`:
   - Mengekstrak artikel berita dari tabel `riwayat_tren` di `data/state.db`.
   - Menjalankan analisis otomatis menggunakan `CTINewsAnalyzer`.
   - Menghasilkan berkas CSV draf berlabel: `data/evaluation/dataset_evaluasi_draf.csv`.
   - Ditandai secara eksplisit: `status_label = "DRAFT_PENDING_USER_REVIEW"`.
   - Kolom `verified_kategori` dan `verified_mitre_id` dibiarkan kosong agar mudah
     dikoreksi manual oleh analis CSIRT Diskominfo Jatim.
2. `calculate_evaluation_metrics`:
   - Membaca baris yang telah diverifikasi manusia (di mana `verified_kategori` tidak kosong).
   - Menghitung Precision, Recall, dan F1-Score per kategori taksonomi insiden (11 kategori).
   - Menghitung Macro-F1, Weighted-F1, dan Akurasi Keseluruhan.
   - Menghitung Akurasi Teknik MITRE ATT&CK (`predicted_id == verified_id`),
     tingkat halusinasi ID, dan akurasi abstensi ("tidak_ditentukan").
   - Memformat laporan ringkasan tabular yang rapi dan mudah dibaca.
   - Idempoten dan dapat langsung dijalankan ulang kapan pun prompt, model, atau label berubah.
"""

import os
import sys
import csv
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from src.utils.logger import setup_logger
from src.storage.db import DEFAULT_DB_PATH, _koneksi, init_db
from src.cti.analyzer import CTINewsAnalyzer, guard_sector_and_quote
from src.cti.preparer import (
    CLOSED_11_TAXONOMY_CATEGORIES,
    TAXONOMY_DISPLAY_NAMES,
    CLOSED_10_IIV_SECTORS,
    IIV_SECTOR_DISPLAY_NAMES,
)

logger = setup_logger(__name__)

DEFAULT_EVALUATION_DIR = Path(__file__).resolve().parents[2] / "data" / "evaluation"
DEFAULT_DRAFT_CSV_PATH = DEFAULT_EVALUATION_DIR / "dataset_evaluasi_draf.csv"


class CTIEvaluator:
    """
    Kerangka kerja evaluasi pipeline CTI untuk pengukuran precision, recall, F1,
    dan akurasi ATT&CK pada dataset berlabel manual.
    """

    def __init__(
        self,
        db_path: Path = DEFAULT_DB_PATH,
        evaluation_dir: Optional[Path] = None,
        analyzer: Optional[CTINewsAnalyzer] = None,
    ):
        self.db_path = Path(db_path)
        self.evaluation_dir = Path(evaluation_dir) if evaluation_dir else DEFAULT_EVALUATION_DIR
        self.evaluation_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = analyzer or CTINewsAnalyzer(db_path=self.db_path)

    # =========================================================================
    # 1. GENERATE DRAFT DATASET
    # =========================================================================

    def generate_draft_dataset(
        self,
        output_csv_path: Optional[Union[str, Path]] = None,
        sample_size: int = 200,
    ) -> Path:
        """
        Mengekstrak artikel berita dari riwayat_tren di SQLite dan menghasilkan draf
        dataset berlabel otomatis dengan penanda DRAFT_PENDING_USER_REVIEW.
        Kolom verified_kategori dan verified_mitre_id dibiarkan kosong untuk koreksi user.
        """
        dest_path = Path(output_csv_path) if output_csv_path else DEFAULT_DRAFT_CSV_PATH
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        init_db(self.db_path)

        # Ambil artikel berita dari riwayat_tren
        articles: List[Dict[str, Any]] = []
        with _koneksi(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                """
                SELECT id, identifier, judul, sumber, ringkasan_atau_narasi, link, kategori_relevansi
                FROM riwayat_tren
                WHERE kategori = 'berita'
                ORDER BY id DESC
                LIMIT ?
                """,
                (sample_size,),
            )
            rows = cursor.fetchall()
            articles = [dict(r) for r in rows]

        if not articles:
            logger.warning(f"Tidak ada artikel berita ditemukan di {self.db_path} tabel riwayat_tren.")
            # Buat file CSV kosong dengan header standar
            headers = [
                "id_berita",
                "judul",
                "ringkasan",
                "prediksi_kategori",
                "confidence_kategori",
                "verified_kategori",
                "prediksi_mitre_id",
                "verified_mitre_id",
                "prediksi_sektor",
                "confidence_sektor",
                "kutipan_bukti_sektor",
                "verified_sektor",
                "status_label",
            ]
            with open(dest_path, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            return dest_path

        logger.info(
            f"Mengekstrak {len(articles)} artikel dari database untuk pembentukan draf dataset evaluasi."
        )

        rows_to_write = []
        for art in articles:
            art_id = art.get("id")
            judul = art.get("judul", "")
            ringkasan = art.get("ringkasan_atau_narasi", "")

            # Analisis dengan CTINewsAnalyzer tanpa persistensi DB tambahan
            analysis = self.analyzer.analyze_news(art, persist=False)

            pred_cat = analysis.get("kategori_utama", "Tidak Dapat Ditentukan")
            conf_cat = analysis.get("confidence_kategori", 0.0)
            pred_mitre = analysis.get("mitre_technique_id") or "tidak_ditentukan"
            pred_sektor = analysis.get("sektor_target", "Tidak dapat ditentukan")
            conf_sektor = analysis.get("confidence_sektor", 0.0)
            quote_sektor = analysis.get("kutipan_bukti_sektor", "")

            rows_to_write.append({
                "id_berita": art_id,
                "judul": judul,
                "ringkasan": ringkasan,
                "prediksi_kategori": pred_cat,
                "confidence_kategori": f"{conf_cat:.2f}",
                "verified_kategori": "",  # Dibiarkan kosong untuk diisi user
                "prediksi_mitre_id": pred_mitre,
                "verified_mitre_id": "",  # Dibiarkan kosong untuk diisi user
                "prediksi_sektor": pred_sektor,
                "confidence_sektor": f"{conf_sektor:.2f}",
                "kutipan_bukti_sektor": quote_sektor,
                "verified_sektor": "",  # Dibiarkan kosong untuk diisi user
                "status_label": "DRAFT_PENDING_USER_REVIEW",
            })

        # Tulis ke berkas CSV dengan UTF-8 with BOM agar kompatibel dengan Excel / Google Sheets
        fieldnames = [
            "id_berita",
            "judul",
            "ringkasan",
            "prediksi_kategori",
            "confidence_kategori",
            "verified_kategori",
            "prediksi_mitre_id",
            "verified_mitre_id",
            "prediksi_sektor",
            "confidence_sektor",
            "kutipan_bukti_sektor",
            "verified_sektor",
            "status_label",
        ]

        with open(dest_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows_to_write)

        logger.info(
            f"Draf dataset evaluasi ({len(rows_to_write)} entri) berhasil disimpan di: {dest_path}"
        )
        return dest_path

    # =========================================================================
    # 2. CALCULATE EVALUATION METRICS
    # =========================================================================

    def calculate_evaluation_metrics(
        self, csv_path: Union[str, Path]
    ) -> Dict[str, Any]:
        """
        Menghitung metrik evaluasi (Precision, Recall, F1, ATT&CK Accuracy) dari berkas dataset CSV.
        Hanya memproses baris yang memiliki verified_kategori atau verified_mitre_id terisi.
        Jika belum ada baris terverifikasi, mengembalikan status informatif NO_VERIFIED_ROWS.
        """
        file_path = Path(csv_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Berkas dataset tidak ditemukan: {file_path}")

        records = []
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                records.append(r)

        total_rows = len(records)
        if total_rows == 0:
            return {
                "status": "EMPTY_DATASET",
                "total_rows": 0,
                "verified_rows": 0,
                "message": "Dataset kosong tanpa baris data.",
                "categories": {},
                "macro_f1": 0.0,
                "weighted_f1": 0.0,
                "accuracy": 0.0,
                "attack_accuracy": 0.0,
                "summary_table": "Dataset kosong.",
            }

        # Filter baris yang diverifikasi manusia
        verified_records = [
            r for r in records
            if (r.get("verified_kategori") and r.get("verified_kategori").strip())
            or (r.get("verified_mitre_id") and r.get("verified_mitre_id").strip())
            or (r.get("verified_sektor") and r.get("verified_sektor").strip())
        ]

        if not verified_records:
            msg = (
                f"Ground truth belum diisi. Seluruh {total_rows} entri masih berstatus draf "
                "(kolom verified_kategori, verified_mitre_id, dan verified_sektor kosong). "
                "Silakan isi kolom verifikasi manual sebelum menghitung metrik."
            )
            logger.info(msg)
            return {
                "status": "NO_VERIFIED_ROWS",
                "total_rows": total_rows,
                "verified_rows": 0,
                "message": msg,
                "categories": {},
                "macro_f1": 0.0,
                "weighted_f1": 0.0,
                "accuracy": 0.0,
                "attack_accuracy": 0.0,
                "sectors": {},
                "sector_accuracy": 0.0,
                "quote_validity_rate": 0.0,
                "summary_table": "Peringatan: Tidak ada baris terverifikasi untuk dievaluasi.",
            }

        # Normalisasi nama kategori ke representasi standar
        def _normalize_category(name: Optional[str]) -> str:
            if not name:
                return "Tidak Dapat Ditentukan"
            clean = name.strip()
            # Cek jika input adalah slug id
            if clean in TAXONOMY_DISPLAY_NAMES:
                return TAXONOMY_DISPLAY_NAMES[clean]
            # Cek case-insensitive terhadap nama tampilan resmi
            for slug, d_name in TAXONOMY_DISPLAY_NAMES.items():
                if clean.lower() == d_name.lower():
                    return d_name
                if clean.lower() == slug.lower():
                    return d_name
            return clean

        # 1. Evaluasi Taksonomi Insiden
        cat_verified_records = [
            r for r in verified_records
            if r.get("verified_kategori") and r.get("verified_kategori").strip()
        ]

        # Kumpulkan seluruh kategori yang muncul pada ground truth maupun prediksi
        observed_categories = set()
        for r in cat_verified_records:
            v_cat = _normalize_category(r.get("verified_kategori"))
            p_cat = _normalize_category(r.get("prediksi_kategori"))
            observed_categories.add(v_cat)
            observed_categories.add(p_cat)

        cat_metrics: Dict[str, Dict[str, Any]] = {}
        total_tp = 0
        total_samples = len(cat_verified_records)

        for cat in sorted(list(observed_categories)):
            tp = sum(
                1 for r in cat_verified_records
                if _normalize_category(r.get("prediksi_kategori")) == cat
                and _normalize_category(r.get("verified_kategori")) == cat
            )
            fp = sum(
                1 for r in cat_verified_records
                if _normalize_category(r.get("prediksi_kategori")) == cat
                and _normalize_category(r.get("verified_kategori")) != cat
            )
            fn = sum(
                1 for r in cat_verified_records
                if _normalize_category(r.get("prediksi_kategori")) != cat
                and _normalize_category(r.get("verified_kategori")) == cat
            )
            support = sum(
                1 for r in cat_verified_records
                if _normalize_category(r.get("verified_kategori")) == cat
            )

            precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            total_tp += tp
            cat_metrics[cat] = {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "support": support,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
            }

        # Hitung Macro-F1 & Weighted-F1
        active_cats_with_support = [c for c, m in cat_metrics.items() if m["support"] > 0]
        if active_cats_with_support:
            macro_f1 = sum(cat_metrics[c]["f1_score"] for c in active_cats_with_support) / len(active_cats_with_support)
            weighted_f1 = sum(cat_metrics[c]["f1_score"] * cat_metrics[c]["support"] for c in active_cats_with_support) / sum(cat_metrics[c]["support"] for c in active_cats_with_support)
        else:
            macro_f1 = 0.0
            weighted_f1 = 0.0

        cat_accuracy = (total_tp / total_samples) if total_samples > 0 else 0.0

        # 2. Evaluasi Teknik MITRE ATT&CK
        attack_verified_records = [
            r for r in verified_records
            if r.get("verified_mitre_id") and r.get("verified_mitre_id").strip()
        ]

        attack_matches = 0
        attack_hallucinations = 0
        abstain_tp = 0
        abstain_total = 0

        # Muat daftar active techniques untuk deteksi halusinasi ID
        active_attack_ids = set(self.analyzer.active_attack_techniques.keys())

        for r in attack_verified_records:
            v_id = r.get("verified_mitre_id", "").strip().upper()
            p_id = r.get("prediksi_mitre_id", "").strip().upper()

            # Normalisasi representasi tidak ditentukan
            if v_id in ("TIDAK_DITENTUKAN", "NONE", "-", ""):
                v_id = "TIDAK_DITENTUKAN"
            if p_id in ("TIDAK_DITENTUKAN", "NONE", "-", ""):
                p_id = "TIDAK_DITENTUKAN"

            if v_id == "TIDAK_DITENTUKAN":
                abstain_total += 1
                if p_id == "TIDAK_DITENTUKAN":
                    abstain_tp += 1

            if p_id == v_id:
                attack_matches += 1

            # Deteksi halusinasi: ID tidak ada di teknik aktif dan bukan abstain
            if p_id != "TIDAK_DITENTUKAN" and p_id not in active_attack_ids:
                attack_hallucinations += 1

        attack_sample_count = len(attack_verified_records)
        attack_accuracy = (attack_matches / attack_sample_count) if attack_sample_count > 0 else 0.0
        hallucination_rate = (attack_hallucinations / attack_sample_count) if attack_sample_count > 0 else 0.0
        abstain_accuracy = (abstain_tp / abstain_total) if abstain_total > 0 else 1.0

        # 3. Evaluasi Sektor Korban (10 IIV Perpres 82/2022)
        sector_verified_records = [
            r for r in verified_records
            if r.get("verified_sektor") and r.get("verified_sektor").strip()
        ]

        def _normalize_sector(name: Optional[str]) -> str:
            if not name:
                return "Tidak dapat ditentukan"
            clean = name.strip()
            for canon in CLOSED_10_IIV_SECTORS:
                if clean.lower() == canon.lower():
                    return canon
            return clean

        observed_sectors = set()
        for r in sector_verified_records:
            v_sec = _normalize_sector(r.get("verified_sektor"))
            p_sec = _normalize_sector(r.get("prediksi_sektor"))
            observed_sectors.add(v_sec)
            observed_sectors.add(p_sec)

        sector_metrics: Dict[str, Dict[str, Any]] = {}
        total_sec_tp = 0
        total_sec_samples = len(sector_verified_records)
        valid_evidence_quotes = 0

        for sec in sorted(list(observed_sectors)):
            tp = sum(
                1 for r in sector_verified_records
                if _normalize_sector(r.get("prediksi_sektor")) == sec
                and _normalize_sector(r.get("verified_sektor")) == sec
            )
            fp = sum(
                1 for r in sector_verified_records
                if _normalize_sector(r.get("prediksi_sektor")) == sec
                and _normalize_sector(r.get("verified_sektor")) != sec
            )
            fn = sum(
                1 for r in sector_verified_records
                if _normalize_sector(r.get("prediksi_sektor")) != sec
                and _normalize_sector(r.get("verified_sektor")) == sec
            )
            support = sum(
                1 for r in sector_verified_records
                if _normalize_sector(r.get("verified_sektor")) == sec
            )

            precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
            recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
            f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

            total_sec_tp += tp
            sector_metrics[sec] = {
                "tp": tp,
                "fp": fp,
                "fn": fn,
                "support": support,
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1_score": round(f1, 4),
            }

        for r in sector_verified_records:
            pred_sec = _normalize_sector(r.get("prediksi_sektor"))
            quote = (r.get("kutipan_bukti_sektor") or "").strip()
            news_text = f"{r.get('judul', '')} {r.get('ringkasan', '')}".strip()
            _, _, _, is_valid = guard_sector_and_quote(pred_sec, quote, news_text)
            if is_valid:
                valid_evidence_quotes += 1

        active_secs_with_support = [s for s, m in sector_metrics.items() if m["support"] > 0]
        if active_secs_with_support:
            macro_sec_f1 = sum(sector_metrics[s]["f1_score"] for s in active_secs_with_support) / len(active_secs_with_support)
            weighted_sec_f1 = sum(sector_metrics[s]["f1_score"] * sector_metrics[s]["support"] for s in active_secs_with_support) / sum(sector_metrics[s]["support"] for s in active_secs_with_support)
        else:
            macro_sec_f1 = 0.0
            weighted_sec_f1 = 0.0

        sector_accuracy = (total_sec_tp / total_sec_samples) if total_sec_samples > 0 else 0.0
        quote_validity_rate = (valid_evidence_quotes / total_sec_samples) if total_sec_samples > 0 else 0.0

        # 4. Format Tabel Ringkasan (Markdown Table)
        table_lines = [
            "| Kategori Insiden | Precision | Recall | F1-Score | Support |",
            "| :--- | :---: | :---: | :---: | :---: |",
        ]
        for cat, m in cat_metrics.items():
            if m["support"] > 0 or m["tp"] > 0 or m["fp"] > 0:
                table_lines.append(
                    f"| {cat} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1_score']:.2f} | {m['support']} |"
                )

        if cat_metrics:
            table_lines.append("| :--- | :---: | :---: | :---: | :---: |")
            table_lines.append(
                f"| **Macro Average** | - | - | **{macro_f1:.4f}** | {total_samples} |"
            )
            table_lines.append(
                f"| **Weighted Average** | - | - | **{weighted_f1:.4f}** | {total_samples} |"
            )
            table_lines.append(
                f"| **Overall Accuracy** | - | - | **{cat_accuracy:.4f}** | {total_samples} |"
            )

        if attack_sample_count > 0:
            table_lines.append("")
            table_lines.append("**Evaluasi Teknik MITRE ATT&CK Enterprise**:")
            table_lines.append(f"- Sampel Terverifikasi: {attack_sample_count}")
            table_lines.append(f"- Akurasi Teknik Presisi: {attack_accuracy * 100:.2f}% ({attack_matches}/{attack_sample_count})")
            table_lines.append(f"- Tingkat Halusinasi ID: {hallucination_rate * 100:.2f}% ({attack_hallucinations} ID tidak valid)")
            table_lines.append(f"- Akurasi Abstensi (tidak ditentukan): {abstain_accuracy * 100:.2f}% ({abstain_tp}/{abstain_total})")

        if total_sec_samples > 0:
            table_lines.append("")
            table_lines.append("**Evaluasi Sektor Target Terpapar (10 IIV Perpres 82/2022)**:")
            table_lines.append("| Sektor IIV | Precision | Recall | F1-Score | Support |")
            table_lines.append("| :--- | :---: | :---: | :---: | :---: |")
            for sec, m in sector_metrics.items():
                if m["support"] > 0 or m["tp"] > 0 or m["fp"] > 0:
                    table_lines.append(
                        f"| {sec} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1_score']:.2f} | {m['support']} |"
                    )
            table_lines.append("| :--- | :---: | :---: | :---: | :---: |")
            table_lines.append(f"| **Macro Average** | - | - | **{macro_sec_f1:.4f}** | {total_sec_samples} |")
            table_lines.append(f"| **Overall Accuracy** | - | - | **{sector_accuracy:.4f}** | {total_sec_samples} |")
            table_lines.append(f"- Tingkat Validitas Kutipan Bukti: {quote_validity_rate * 100:.2f}% ({valid_evidence_quotes}/{total_sec_samples})")

        summary_table = "\n".join(table_lines)

        return {
            "status": "SUCCESS",
            "total_rows": total_rows,
            "verified_rows": len(verified_records),
            "category_samples": total_samples,
            "attack_samples": attack_sample_count,
            "sector_samples": total_sec_samples,
            "categories": cat_metrics,
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "accuracy": round(cat_accuracy, 4),
            "attack_accuracy": round(attack_accuracy, 4),
            "hallucination_rate": round(hallucination_rate, 4),
            "abstain_accuracy": round(abstain_accuracy, 4),
            "sectors": sector_metrics,
            "sector_metrics": sector_metrics,
            "sector_macro_f1": round(macro_sec_f1, 4),
            "sector_weighted_f1": round(weighted_sec_f1, 4),
            "sector_accuracy": round(sector_accuracy, 4),
            "quote_validity_rate": round(quote_validity_rate, 4),
            "summary_table": summary_table,
        }


# =============================================================================
# STANDALONE FUNCTION EXPORTS
# =============================================================================

def generate_draft_dataset(
    db_path: Path = DEFAULT_DB_PATH,
    output_csv_path: Optional[Union[str, Path]] = None,
    sample_size: int = 200,
) -> Path:
    """Fungsi wrapper praktis untuk membangkitkan draf dataset evaluasi."""
    evaluator = CTIEvaluator(db_path=db_path)
    return evaluator.generate_draft_dataset(output_csv_path=output_csv_path, sample_size=sample_size)


def calculate_evaluation_metrics(csv_path: Union[str, Path]) -> Dict[str, Any]:
    """Fungsi wrapper praktis untuk menghitung metrik evaluasi dari berkas CSV."""
    evaluator = CTIEvaluator()
    return evaluator.calculate_evaluation_metrics(csv_path=csv_path)


# Aliases for test suite compatibility
generate_draft_evaluation_dataset = generate_draft_dataset
calculate_cti_metrics = calculate_evaluation_metrics
