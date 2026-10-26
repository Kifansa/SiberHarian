"""
Unit & Integration Test Suite for Milestone 6 (Periodic Updater) & Milestone 7 (Evaluation Framework).

Menguji:
1. Idempotensi pengecekan versi (run kedua tidak mengubah apa pun dan mencatat 'tidak ada pembaruan').
2. Drop guard katastropik (>30% drop atau 0 record ditolak dan tidak merusak indeks/DB).
3. Diff reporting (identifikasi added, modified, revoked, unchanged).
4. Inkremental re-embedding (hanya dokumen baru/berubah yang di-embed ulang).
5. Atomic swap & rollback (vNext diuji lalu di-swap, vPrev dipertahankan untuk rollback).
6. Revoked technique historical auditor (menandai 'TEKNIK_REVOKED_PERLU_REVIEW' tanpa menghapus data).
7. Pembangkitan draf dataset evaluasi berlabel 'DRAFT_PENDING_USER_REVIEW'.
8. Kalkulasi metrik evaluasi (Precision, Recall, F1, Macro-F1, ATT&CK accuracy).
9. CLI scripts execution (update_*.py, generate_evaluation_draft.py, evaluate_pipeline.py).
"""

import os
import sys
import json
import csv
import shutil
import tempfile
import sqlite3
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.cti.updater import (
    CTISourceUpdater,
    DropDetectionError,
    UpdateValidationError,
)
from src.cti.evaluator import (
    CTIEvaluator,
    generate_draft_dataset,
    calculate_evaluation_metrics,
)
from src.cti.vector_store import CTIVectorStore
from src.storage.db import (
    init_db,
    _koneksi,
    simpan_metadata,
    ambil_metadata,
    simpan_intelijen_berita,
    ambil_intelijen_berita,
)


@pytest.fixture
def temp_workspace(tmp_path):
    """Membuat direktori kerja pengujian terisolasi."""
    raw_dir = tmp_path / "raw"
    prep_dir = tmp_path / "prepared"
    vec_dir = tmp_path / "vector_stores"
    rep_dir = tmp_path / "reports"
    eval_dir = tmp_path / "evaluation"
    db_file = tmp_path / "test_state.db"

    for d in [raw_dir, prep_dir, vec_dir, rep_dir, eval_dir]:
        d.mkdir(parents=True, exist_ok=True)

    init_db(db_file)

    # Siapkan data prepared tiruan minimal
    mock_attack = [
        {
            "technique_id": "T1486",
            "name": "Data Encrypted for Impact",
            "tactics": ["Impact"],
            "description": "Ransomware encryption.",
            "platforms": ["Windows", "Linux"],
            "is_subtechnique": False,
        },
        {
            "technique_id": "T1566",
            "name": "Phishing",
            "tactics": ["Initial Access"],
            "description": "Phishing email.",
            "platforms": ["Windows", "macOS"],
            "is_subtechnique": False,
        },
        {
            "technique_id": "T1190",
            "name": "Exploit Public-Facing Application",
            "tactics": ["Initial Access"],
            "description": "Vulnerability exploit.",
            "platforms": ["Linux", "Windows"],
            "is_subtechnique": False,
        },
    ]
    (prep_dir / "attack_techniques.json").write_text(
        json.dumps(mock_attack, indent=2), encoding="utf-8"
    )

    mock_tax = [
        {
            "category_id": "ransomware",
            "name": "Ransomware",
            "ecsirt_parent": "malicious-code:ransomware",
            "definition": "Enkripsi tebusan.",
            "representative_examples": ["PDNS lumpuh LockBit"],
        },
        {
            "category_id": "tidak_dapat_ditentukan",
            "name": "Tidak Dapat Ditentukan",
            "ecsirt_parent": "other:unspecified",
            "definition": "Non insiden.",
            "representative_examples": ["Rapat kerja"],
        },
    ]
    (prep_dir / "taxonomy_categories.json").write_text(
        json.dumps(mock_tax, indent=2), encoding="utf-8"
    )

    mock_nist = [
        {
            "control_id": "AC-2",
            "title": "Account Management",
            "statement": "The organization manages accounts.",
            "framework": "SP 800-53 Rev 5",
        }
    ]
    (prep_dir / "nist_controls.json").write_text(
        json.dumps(mock_nist, indent=2), encoding="utf-8"
    )

    vs = CTIVectorStore(
        prepared_dir=prep_dir,
        vector_dir=vec_dir,
        auto_load=True,
        embedding_mode="offline",
    )

    updater = CTISourceUpdater(
        raw_dir=raw_dir,
        prepared_dir=prep_dir,
        vector_dir=vec_dir,
        reports_dir=rep_dir,
        db_path=db_file,
        vector_store=vs,
    )

    return {
        "raw_dir": raw_dir,
        "prep_dir": prep_dir,
        "vec_dir": vec_dir,
        "rep_dir": rep_dir,
        "eval_dir": eval_dir,
        "db_file": db_file,
        "vs": vs,
        "updater": updater,
    }


class TestCTISourceUpdater:
    """Pengujian Unit & Integrasi Milestone 6: Periodic Update Engine."""

    def test_idempotent_version_check_no_update(self, temp_workspace):
        updater = temp_workspace["updater"]
        db_file = temp_workspace["db_file"]

        # Tetapkan versi aktif
        updater.set_active_version("mitre_attack", "v20.0")

        # Mock fetch remote version mengembalikan versi yang sama
        with patch.object(updater, "fetch_remote_version", return_value="v20.0"):
            check = updater.check_version("mitre_attack")
            assert check["has_update"] is False
            assert "tidak ada pembaruan untuk mitre_attack (versi aktif: v20.0)" in check["message"]

            # Jalankan update_attack: harus mengembalikan UP_TO_DATE tanpa modifikasi
            res = updater.update_attack(force=False)
            assert res["status"] == "UP_TO_DATE"
            assert "tidak ada pembaruan" in res["message"]

    def test_catastrophic_drop_guard_rejects_empty_payload(self, temp_workspace):
        updater = temp_workspace["updater"]

        # Drop guard harus menolak count 0
        with pytest.raises(DropDetectionError) as exc_info:
            updater.validate_staging_drop("mitre_attack", new_count=0, old_count=706)
        assert "kosong" in str(exc_info.value) or "penurunan" in str(exc_info.value)

    def test_catastrophic_drop_guard_rejects_severe_drop(self, temp_workspace):
        updater = temp_workspace["updater"]

        # Penurunan dari 706 menjadi 200 (>70% drop) harus ditolak
        with pytest.raises(DropDetectionError) as exc_info:
            updater.validate_staging_drop("mitre_attack", new_count=200, old_count=706)
        assert "penurunan record drastis" in str(exc_info.value)

        # Penurunan wajar < 30% (misal 706 menjadi 700) harus lolos
        updater.validate_staging_drop("mitre_attack", new_count=700, old_count=706)

    def test_diff_reporting_computes_sets_and_writes_json(self, temp_workspace):
        updater = temp_workspace["updater"]
        rep_dir = temp_workspace["rep_dir"]

        old_items = [
            {"technique_id": "T1001", "name": "Old Tech 1", "description": "Desc 1"},
            {"technique_id": "T1002", "name": "Tech to Modify", "description": "Old Desc"},
            {"technique_id": "T1003", "name": "Tech to Revoke", "description": "Will be dropped"},
        ]
        new_items = [
            {"technique_id": "T1001", "name": "Old Tech 1", "description": "Desc 1"},  # unchanged
            {"technique_id": "T1002", "name": "Tech to Modify", "description": "New Updated Desc"},  # modified
            {"technique_id": "T1004", "name": "Brand New Tech", "description": "New Tech"},  # added
        ]

        diff = updater.compute_diff(
            source="mitre_attack",
            old_items=old_items,
            new_items=new_items,
            id_key="technique_id",
            old_version="v1.0",
            new_version="v2.0",
        )

        assert diff["added"] == ["T1004"]
        assert diff["modified"] == ["T1002"]
        assert diff["revoked"] == ["T1003"]
        assert diff["counts"]["unchanged"] == 1

        # Verifikasi berkas JSON diff tersimpan
        report_path = Path(diff["report_path"])
        assert report_path.exists()
        saved_data = json.loads(report_path.read_text(encoding="utf-8"))
        assert saved_data["source"] == "mitre_attack"
        assert saved_data["counts"]["added"] == 1

    def test_incremental_reembedding_and_atomic_swap(self, temp_workspace):
        updater = temp_workspace["updater"]
        vs = temp_workspace["vs"]
        vec_dir = temp_workspace["vec_dir"]

        attack_idx_file = vs._get_index_file("collection_attack")
        assert attack_idx_file.exists()

        initial_data = json.loads(attack_idx_file.read_text(encoding="utf-8"))
        initial_recs = initial_data.get("records", [])
        assert len(initial_recs) == 3

        # Siapkan pembaruan: 1 teknik baru ditambahkan, 2 teknik lama tetap unchanged
        diff = {
            "added": ["T9999"],
            "modified": [],
            "revoked": [],
            "unchanged": ["T1486", "T1566", "T1190"],
        }
        new_docs = [
            {
                "technique_id": "T1486",
                "name": "Data Encrypted for Impact",
                "tactics": ["Impact"],
                "description": "Ransomware encryption.",
            },
            {
                "technique_id": "T1566",
                "name": "Phishing",
                "tactics": ["Initial Access"],
                "description": "Phishing email.",
            },
            {
                "technique_id": "T1190",
                "name": "Exploit Public-Facing Application",
                "tactics": ["Initial Access"],
                "description": "Vulnerability exploit.",
            },
            {
                "technique_id": "T9999",
                "name": "Super New Technique",
                "tactics": ["Persistence"],
                "description": "Novel persistence mechanism.",
            },
        ]

        def formatter(d):
            return f"{d.get('technique_id')} {d.get('name')}"

        swap_res = updater.incremental_update_vector_index(
            collection_name="collection_attack",
            diff=diff,
            new_docs=new_docs,
            doc_text_formatter=formatter,
            id_key="technique_id",
        )

        assert swap_res["status"] == "SUCCESS"
        assert swap_res["total_records"] == 4
        # Hanya 1 teks baru yang di-embed ulang
        assert swap_res["reembedded_count"] == 1
        assert swap_res["reused_count"] == 3

        # Verifikasi index.json aktif memiliki 4 teknik
        updated_data = json.loads(attack_idx_file.read_text(encoding="utf-8"))
        assert len(updated_data["records"]) == 4

        # Verifikasi cadangan vPrev tersimpan
        v_prev_file = attack_idx_file.parent / "index.json.vPrev"
        assert v_prev_file.exists()
        prev_data = json.loads(v_prev_file.read_text(encoding="utf-8"))
        assert len(prev_data["records"]) == 3

    def test_rollback_vector_index(self, temp_workspace):
        updater = temp_workspace["updater"]
        vs = temp_workspace["vs"]

        attack_idx_file = vs._get_index_file("collection_attack")
        v_prev_file = attack_idx_file.parent / "index.json.vPrev"

        # Jalankan update terlebih dahulu agar cadangan vPrev terbuat
        diff = {
            "added": ["T9999"],
            "modified": [],
            "revoked": [],
            "unchanged": ["T1486", "T1566", "T1190"],
        }
        new_docs = [
            {"technique_id": "T1486", "name": "Data Encrypted", "tactics": ["Impact"], "description": "Desc"},
            {"technique_id": "T1566", "name": "Phishing", "tactics": ["Initial Access"], "description": "Desc"},
            {"technique_id": "T1190", "name": "Exploit", "tactics": ["Initial Access"], "description": "Desc"},
            {"technique_id": "T9999", "name": "New Tech", "tactics": ["Persistence"], "description": "Desc"},
        ]
        updater.incremental_update_vector_index(
            collection_name="collection_attack",
            diff=diff,
            new_docs=new_docs,
            doc_text_formatter=lambda d: d["name"],
            id_key="technique_id",
        )

        # Pastikan vPrev tersedia
        assert v_prev_file.exists()

        # Eksekusi rollback
        ok = updater.rollback_vector_index("collection_attack")
        assert ok is True

        # Index aktif harus kembali menjadi 3 record
        rolled_data = json.loads(attack_idx_file.read_text(encoding="utf-8"))
        assert len(rolled_data["records"]) == 3
        assert len(vs.collection_attack) == 3

    def test_revoked_technique_auditor_flags_historical_records(self, temp_workspace):
        updater = temp_workspace["updater"]
        db_file = temp_workspace["db_file"]

        # Simpan 2 insiden historis yang memakai teknik T1086 (PowerShell, revoked)
        record1 = {
            "article_identifier": "art_history_1",
            "kategori_insiden": "Malware / Infostealer",
            "confidence_kategori": 0.85,
            "mitre_technique_id": "T1086",
            "mitre_technique_name": "PowerShell",
            "version_taxonomy": "2",
            "version_attack": "v15.0",
            "version_d3fend": "1.5.0",
            "version_nist": "SP800-53-Rev5",
        }
        record2 = {
            "article_identifier": "art_history_2",
            "kategori_insiden": "Akses Tidak Sah / Pembobolan Akun",
            "confidence_kategori": 0.90,
            "mitre_technique_id": "T1086",
            "mitre_technique_name": "PowerShell",
            "version_taxonomy": "2",
            "version_attack": "v15.0",
            "version_d3fend": "1.5.0",
            "version_nist": "SP800-53-Rev5",
        }
        simpan_intelijen_berita(record1, db_path=db_file)
        simpan_intelijen_berita(record2, db_path=db_file)

        # Verifikasi awal flag_tinjauan masih None
        r1_before = ambil_intelijen_berita("art_history_1", db_path=db_file)
        assert r1_before["flag_tinjauan"] is None

        # Jalankan audit untuk teknik T1086 yang dicabut
        flagged_count = updater.audit_revoked_attack_techniques(["T1086"])
        assert flagged_count == 2

        # Verifikasi insiden historis tidak dihapus melainkan ditandai
        r1_after = ambil_intelijen_berita("art_history_1", db_path=db_file)
        r2_after = ambil_intelijen_berita("art_history_2", db_path=db_file)
        assert r1_after is not None
        assert r2_after is not None
        assert r1_after["flag_tinjauan"] == "TEKNIK_REVOKED_PERLU_REVIEW"
        assert r2_after["flag_tinjauan"] == "TEKNIK_REVOKED_PERLU_REVIEW"


class TestCTIEvaluator:
    """Pengujian Unit & Integrasi Milestone 7: Evaluation Framework."""

    def test_generate_draft_dataset_extracts_and_marks_draft(self, temp_workspace):
        db_file = temp_workspace["db_file"]
        eval_dir = temp_workspace["eval_dir"]

        # Masukkan contoh berita ke riwayat_tren
        with _koneksi(db_file) as conn:
            conn.execute(
                """
                INSERT INTO riwayat_tren (kategori, identifier, judul, ringkasan_atau_narasi, link, tanggal_publish, tanggal_dicatat)
                VALUES ('berita', 'art_eval_test', 'Serangan Ransomware PDNS', 'Server dienkripsi tebusan kripto.', 'https://news.id/1', '2026-10-20', '2026-10-20')
                """
            )

        evaluator = CTIEvaluator(db_path=db_file, evaluation_dir=eval_dir)
        output_csv = eval_dir / "draft_test.csv"

        gen_path = evaluator.generate_draft_dataset(output_csv_path=output_csv, sample_size=10)
        assert gen_path.exists()

        rows = []
        with open(gen_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)

        assert len(rows) == 1
        row = rows[0]
        assert row["status_label"] == "DRAFT_PENDING_USER_REVIEW"
        assert row["verified_kategori"] == ""  # Siap diisi user
        assert row["verified_mitre_id"] == ""  # Siap diisi user
        assert row["prediksi_kategori"] in ("Ransomware", "Tidak Dapat Ditentukan")

    def test_metrics_handles_unverified_dataset_gracefully(self, temp_workspace):
        eval_dir = temp_workspace["eval_dir"]
        csv_file = eval_dir / "unverified.csv"

        # Tulis dataset yang belum diverifikasi
        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["id_berita", "judul", "ringkasan", "prediksi_kategori", "confidence_kategori", "verified_kategori", "prediksi_mitre_id", "verified_mitre_id", "status_label"])
            writer.writerow(["1", "Judul", "Ringkasan", "Ransomware", "0.90", "", "T1486", "", "DRAFT_PENDING_USER_REVIEW"])

        evaluator = CTIEvaluator(evaluation_dir=eval_dir)
        res = evaluator.calculate_evaluation_metrics(csv_file)

        assert res["status"] == "NO_VERIFIED_ROWS"
        assert res["total_rows"] == 1
        assert res["verified_rows"] == 0
        assert "Ground truth belum diisi" in res["message"]

    def test_metrics_calculation_verified_ground_truth(self, temp_workspace):
        eval_dir = temp_workspace["eval_dir"]
        csv_file = eval_dir / "verified_ground_truth.csv"

        # Buat dataset terverifikasi dengan hasil metrik yang telah dihitung manual
        data = [
            # Case 1: TP Ransomware, TP T1486
            {"prediksi_kategori": "Ransomware", "verified_kategori": "Ransomware", "prediksi_mitre_id": "T1486", "verified_mitre_id": "T1486"},
            # Case 2: TP Ransomware, TP T1486
            {"prediksi_kategori": "Ransomware", "verified_kategori": "Ransomware", "prediksi_mitre_id": "T1486", "verified_mitre_id": "T1486"},
            # Case 3: FP Ransomware / FN Data Breach
            {"prediksi_kategori": "Ransomware", "verified_kategori": "Data Breach / Kebocoran Data", "prediksi_mitre_id": "T1566", "verified_mitre_id": "T1048"},
            # Case 4: TP Data Breach, TP T1048
            {"prediksi_kategori": "Data Breach / Kebocoran Data", "verified_kategori": "Data Breach / Kebocoran Data", "prediksi_mitre_id": "T1048", "verified_mitre_id": "T1048"},
            # Case 5: TP Tidak Dapat Ditentukan, Abstain TP
            {"prediksi_kategori": "Tidak Dapat Ditentukan", "verified_kategori": "Tidak Dapat Ditentukan", "prediksi_mitre_id": "tidak_ditentukan", "verified_mitre_id": "tidak_ditentukan"},
        ]

        with open(csv_file, "w", encoding="utf-8-sig", newline="") as f:
            fieldnames = ["id_berita", "judul", "ringkasan", "prediksi_kategori", "confidence_kategori", "verified_kategori", "prediksi_mitre_id", "verified_mitre_id", "status_label"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for idx, item in enumerate(data):
                writer.writerow({
                    "id_berita": idx + 1,
                    "judul": f"News {idx+1}",
                    "ringkasan": f"Summary {idx+1}",
                    "prediksi_kategori": item["prediksi_kategori"],
                    "confidence_kategori": "0.90",
                    "verified_kategori": item["verified_kategori"],
                    "prediksi_mitre_id": item["prediksi_mitre_id"],
                    "verified_mitre_id": item["verified_mitre_id"],
                    "status_label": "VERIFIED_HUMAN",
                })

        evaluator = CTIEvaluator(evaluation_dir=eval_dir)
        metrics = evaluator.calculate_evaluation_metrics(csv_file)

        assert metrics["status"] == "SUCCESS"
        assert metrics["total_rows"] == 5
        assert metrics["verified_rows"] == 5

        # Ransomware: TP=2, FP=1, FN=0 -> Precision = 2/3 = 0.6667, Recall = 2/2 = 1.0, F1 = 0.80
        rw_m = metrics["categories"]["Ransomware"]
        assert rw_m["tp"] == 2
        assert rw_m["fp"] == 1
        assert rw_m["fn"] == 0
        assert rw_m["precision"] == 0.6667
        assert rw_m["recall"] == 1.0
        assert rw_m["f1_score"] == 0.8

        # Overall Accuracy = 4/5 = 0.80
        assert metrics["accuracy"] == 0.80

        # ATT&CK Accuracy = 4/5 = 0.80 (cases 1, 2, 4, 5 matched)
        assert metrics["attack_accuracy"] == 0.80
        assert metrics["hallucination_rate"] == 0.0

        # Table formatting check
        assert "| Ransomware |" in metrics["summary_table"]
        assert "**Macro Average**" in metrics["summary_table"]


class TestCLIScripts:
    """Pengujian eksekusi CLI script (scripts/update_*.py & scripts/evaluate_*.py)."""

    def test_cli_update_scripts_help_and_exit_cleanly(self):
        scripts = [
            "scripts/update_attack.py",
            "scripts/update_d3fend.py",
            "scripts/update_nist.py",
            "scripts/update_taxonomy.py",
            "scripts/generate_evaluation_draft.py",
            "scripts/evaluate_pipeline.py",
        ]
        for s in scripts:
            p = Path(s)
            assert p.exists(), f"Script {s} tidak ditemukan."
            res = subprocess.run(
                [sys.executable, str(p), "--help"],
                capture_output=True,
                text=True,
            )
            assert res.returncode == 0, f"Script {s} --help gagal: {res.stderr}"

    def test_cli_evaluate_pipeline_runs_on_verified_sample(self):
        sample_file = Path("data/evaluation/dataset_evaluasi_verified_sample.csv")
        assert sample_file.exists()

        res = subprocess.run(
            [sys.executable, "scripts/evaluate_pipeline.py", "--dataset", str(sample_file), "--format", "json"],
            capture_output=True,
            text=True,
        )
        assert res.returncode == 0
        raw_stdout = res.stdout
        json_start = raw_stdout.find("{")
        json_end = raw_stdout.rfind("}") + 1
        assert json_start != -1 and json_end > json_start, f"Tidak ada JSON di stdout: {raw_stdout}"
        data = json.loads(raw_stdout[json_start:json_end])
        assert data["status"] == "SUCCESS"
        assert data["verified_rows"] > 0
        assert "macro_f1" in data
