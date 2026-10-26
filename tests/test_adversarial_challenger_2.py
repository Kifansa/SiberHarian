# -*- coding: utf-8 -*-
"""
Adversarial Stress-Test Suite - Challenger Gate 2
Verification for SiberHarian CTI Dynamic Upgrade

Areas Tested:
1. Dynamic Shift Integrity: Alternating dominant categories across multiple simulated weeks.
   Verifies hitung_prediksi_pola_serangan dynamically tracks without lag, bias, or state caching.
2. Emerging Threat Fuzzing: Boundary test of 0 -> 1 -> 2 -> 3 cases.
   Verifies strictly >= 2 cases are required for emerging alert (1 case NEVER alerts).
   Verifies novelty > volume precedence.
   Verifies generic categories ('tidak_dapat_ditentukan', 'lainnya') are never emerging alerts.
3. DOM & UI Verification: Complete absence of 'Taksonomi Resmi: [...]' in HTML & JS.
4. Database Schema & Injection Resistance:
   SQL injection resistance, special characters, single/double quotes, unicode,
   and NULL handling in simpan_koreksi_admin_sektor and related DB queries.
"""

import os
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
import pytest

from src.analytics.rag_engine import (
    RAGEngine,
    CLOSED_11_TAXONOMY_CATEGORIES,
    TAXONOMY_DISPLAY_NAMES,
    resolve_article_taxonomy_category,
)
from src.storage.db import (
    init_db,
    simpan_koreksi_admin_sektor,
    ambil_intelijen_berita,
    ambil_semua_intelijen_berita,
    simpan_intelijen_berita,
)


# =====================================================================
# 1. DYNAMIC SHIFT STRESS-TEST (Alternating Dominant Categories)
# =====================================================================

class TestDynamicShiftIntegrity:
    """
    Stress-test dynamic responsiveness across alternating dominant taxonomy categories.
    Ensures zero state leakage or caching between calls and full dynamic adaptation.
    """

    def _create_dataset_for_category(self, dominant_cat: str, other_cats: list):
        """Generates DataFrame where dominant_cat has majority of distinct articles."""
        rows = []
        display_name = TAXONOMY_DISPLAY_NAMES.get(dominant_cat, dominant_cat)
        
        target_entities = [
            "Perbankan Daerah", "Dinas Kesehatan", "Portal Pelayanan Pajak",
            "Sistem Kelistrikan Jawa", "PDAM Kota Surabaya", "Bandara Internasional",
            "Operator Logistik", "Universitas Negeri", "Sistem Transportasi", "Penyedia Jaringan"
        ]

        # 10 distinct dominant articles in terkini
        for i, ent in enumerate(target_entities):
            rows.append({
                "identifier": f"cur_{dominant_cat}_{i}",
                "judul": f"Insiden {display_name} Mengancam Infrastruktur {ent}",
                "ringkasan_atau_narasi": f"Laporan serangan {dominant_cat} terverifikasi menginfeksi sistem pada {ent}.",
                "kata_kunci": f"{dominant_cat}, siber, insiden, {ent.lower()}",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "kategori_taksonomi": dominant_cat,
                "tanggal_publish": "2026-10-20 10:00:00",
                "sumber": f"Security Media {i}"
            })

        # Other categories have 1 article each in terkini
        for idx, other_cat in enumerate(other_cats[:5]):
            other_disp = TAXONOMY_DISPLAY_NAMES.get(other_cat, other_cat)
            rows.append({
                "identifier": f"cur_other_{idx}",
                "judul": f"Inspeksi Berkala Temuan {other_disp} Skala Kecil",
                "ringkasan_atau_narasi": f"Kasus terkait {other_cat} dilaporkan dalam skala kecil tanpa eskalasi.",
                "kata_kunci": f"{other_cat}",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "kategori_taksonomi": other_cat,
                "tanggal_publish": "2026-10-19 09:00:00",
                "sumber": "Tech Portal"
            })

        # Baseline week (e.g., 2026-10-10) with equal distribution
        for cat in [dominant_cat] + other_cats[:5]:
            rows.append({
                "identifier": f"base_{cat}",
                "judul": f"Rekapitulasi Sejarah Insiden {cat} Periode Lalu",
                "ringkasan_atau_narasi": f"Ringkasan mingguan {cat}.",
                "kata_kunci": f"{cat}",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "kategori_taksonomi": cat,
                "tanggal_publish": "2026-10-10 08:00:00",
                "sumber": "Archive"
            })

        return pd.DataFrame(rows)

    def test_alternating_dominant_categories_rapid_succession(self):
        """
        Alternates dominant categories rapidly across 6 distinct categories:
        Ransomware -> DDoS -> Phishing -> Defacement -> Malware -> Exploit.
        Asserts hitung_prediksi_pola_serangan matches exactly each time with zero lag or cache bleed.
        """
        sequence = [
            ("ransomware", TAXONOMY_DISPLAY_NAMES["ransomware"]),
            ("ddos", TAXONOMY_DISPLAY_NAMES["ddos"]),
            ("phishing_penipuan", TAXONOMY_DISPLAY_NAMES["phishing_penipuan"]),
            ("defacement", TAXONOMY_DISPLAY_NAMES["defacement"]),
            ("malware", TAXONOMY_DISPLAY_NAMES["malware"]),
            ("eksploitasi_kerentanan", TAXONOMY_DISPLAY_NAMES["eksploitasi_kerentanan"])
        ]
        
        all_cats = [c[0] for c in sequence]

        for target_cat, expected_display in sequence:
            others = [c for c in all_cats if c != target_cat]
            df = self._create_dataset_for_category(target_cat, others)
            
            rag = RAGEngine(df)
            pola_res = rag.hitung_prediksi_pola_serangan()

            assert pola_res["kategori_taksonomi"] == target_cat, (
                f"Expected dominant category '{target_cat}', but got '{pola_res['kategori_taksonomi']}'"
            )
            assert pola_res["pola"] == expected_display, (
                f"Expected display name '{expected_display}', but got '{pola_res['pola']}'"
            )
            assert pola_res["jumlah_terkini"] == 10, (
                f"Expected 10 current articles, got {pola_res['jumlah_terkini']}"
            )
            assert pola_res["growth_persen"] > 0, "Expected positive growth for dominant category"

    def test_same_rag_instance_category_switch(self):
        """
        Tests reusing or mutating RAGEngine internal DataFrame across different weeks.
        Verifies no memoization or cached property retains previous week's winner.
        """
        df1 = self._create_dataset_for_category("ransomware", ["ddos", "malware"])
        df2 = self._create_dataset_for_category("ddos", ["ransomware", "malware"])

        rag = RAGEngine(df1)
        res1 = rag.hitung_prediksi_pola_serangan()
        assert res1["kategori_taksonomi"] == "ransomware"

        # Dynamically swap DataFrame
        rag.df_berita = df2
        res2 = rag.hitung_prediksi_pola_serangan()
        assert res2["kategori_taksonomi"] == "ddos", (
            f"Expected ddos after df_berita swap, got '{res2['kategori_taksonomi']}'"
        )

    def test_pola_serangan_empty_and_zero_state(self):
        """Test resilience to empty DataFrames."""
        rag_empty = RAGEngine(pd.DataFrame())
        res_empty = rag_empty.hitung_prediksi_pola_serangan()
        assert res_empty["pola"] == "Akses Tidak Sah / Pembobolan Akun"
        assert res_empty["jumlah_terkini"] == 0
        assert res_empty["growth_persen"] == 0.0


# =====================================================================
# 2. EMERGING THREAT FUZZING (0 -> 1 -> 2 Boundary Conditions)
# =====================================================================

class TestEmergingThreatFuzzing:
    """
    Fuzzes the boundary of emerging threats (Sinyal Ancaman Baru).
    Strict constraint: >= 2 cases required for alert.
    1 case MUST NEVER trigger an alert, even with max urgency keywords.
    """

    def _build_dataset(self, test_cat: str, count_cur: int, count_base: int = 0, with_novelty_kw: bool = True):
        rows = []
        kw = "zero-day, novel, baru, kritis, varian baru" if with_novelty_kw else "umum"

        target_entities = [
            "Server Sentral Keuangan", "Sistem Database Logistik", "Jaringan Internal Kampus",
            "Portal Integrasi Pajak", "Layanan Komputasi Awan", "Gateway Pembayaran Publik",
            "Infrastruktur Smart City", "Stasiun Pengisian Daya", "Terminal Petikemas", "Data Center Regional"
        ]

        # Current period (today)
        for i in range(count_cur):
            ent = target_entities[i % len(target_entities)]
            rows.append({
                "identifier": f"cur_emerging_{i}_{test_cat}",
                "judul": f"Eskalasi Baru Ancaman {test_cat} Menyerang {ent} #{i}",
                "ringkasan_atau_narasi": f"Ditemukan eksploitasi modus baru {test_cat} berstatus kritis pada {ent}.",
                "kata_kunci": kw,
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "kategori_taksonomi": test_cat,
                "tanggal_publish": "2026-10-21 08:00:00",
                "sumber": f"BSSN Alert {i}"
            })

        # Baseline period (last week)
        for j in range(count_base):
            ent = target_entities[j % len(target_entities)]
            rows.append({
                "identifier": f"base_emerging_{j}_{test_cat}",
                "judul": f"Riwayat Audit Insiden {test_cat} Lama pada {ent} #{j}",
                "ringkasan_atau_narasi": f"Insiden {test_cat} minggu lalu tercatat pada {ent}.",
                "kata_kunci": "arsip",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "kategori_taksonomi": test_cat,
                "tanggal_publish": "2026-10-10 08:00:00",
                "sumber": f"Archive {j}"
            })

        return pd.DataFrame(rows)

    def test_zero_cases_yields_kondisi_stabil(self):
        """0 cases in current period must return 'Kondisi Stabil'."""
        df = self._build_dataset("malware", count_cur=0, count_base=5)
        rag = RAGEngine(df)
        assert rag.hitung_prediksi_ancaman_baru() == "Kondisi Stabil"
        res_info = rag.ambil_berita_ancaman_baru()
        assert res_info["ada"] is False
        assert res_info["nama"] == "Kondisi Stabil"

    def test_boundary_exactly_one_case_never_alerts(self):
        """
        Adversarial test: Exactly 1 case of an extreme zero-day attack
        with highest urgency keywords ('zero-day', 'novel', 'kritis').
        MUST NOT alert. Must return 'Kondisi Stabil'.
        """
        df = self._build_dataset("eksploitasi_kerentanan", count_cur=1, count_base=0, with_novelty_kw=True)
        rag = RAGEngine(df)
        
        signal = rag.hitung_prediksi_ancaman_baru()
        assert signal == "Kondisi Stabil", (
            f"VIOLATION: Exactly 1 case triggered an emerging threat alert: '{signal}'!"
        )
        res = rag.ambil_berita_ancaman_baru()
        assert res["ada"] is False
        assert res["nama"] == "Kondisi Stabil"

    def test_boundary_exactly_two_cases_triggers_alert(self):
        """
        Boundary condition: Exactly 2 cases of a new attack category
        MUST trigger an alert if novel.
        """
        df = self._build_dataset("malware", count_cur=2, count_base=0, with_novelty_kw=True)
        rag = RAGEngine(df)
        
        signal = rag.hitung_prediksi_ancaman_baru()
        expected = TAXONOMY_DISPLAY_NAMES["malware"]
        assert signal == expected, f"Expected '{expected}', got '{signal}'"
        res = rag.ambil_berita_ancaman_baru()
        assert res["ada"] is True
        assert res["nama"] == expected
        assert res["jumlah_kasus"] == 2

    def test_novelty_beats_high_volume_established_category(self):
        """
        Stress test: Category A has 25 articles (established, no growth, 25 in base).
        Category B has only 2 articles (emerging, 0 in base, novelty keywords).
        Result: Category B MUST WIN the emerging threat card!
        """
        rows = []
        # Category A: 25 current, 25 base
        for i in range(25):
            rows.append({
                "identifier": f"cur_estab_{i}",
                "judul": f"Ransomware Rutin #{i}",
                "ringkasan_atau_narasi": "Serangan ransomware umum melanda server swasta.",
                "kata_kunci": "ransomware, rutin",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "kategori_taksonomi": "ransomware",
                "tanggal_publish": "2026-10-21 10:00:00",
                "sumber": "Daily Log"
            })
            rows.append({
                "identifier": f"base_estab_{i}",
                "judul": f"Ransomware Rutin Base #{i}",
                "ringkasan_atau_narasi": "Serangan ransomware minggu lalu.",
                "kata_kunci": "ransomware",
                "kategori": "berita",
                "kategori_relevansi": "insiden_spesifik",
                "kategori_taksonomi": "ransomware",
                "tanggal_publish": "2026-10-10 10:00:00",
                "sumber": "Daily Log"
            })

        # Category B: 2 current, 0 base, with novelty keywords
        rows.append({
            "identifier": "cur_novel_1",
            "judul": "Varian Baru Serangan DDoS Mengincar Server Jaringan Finansial",
            "ringkasan_atau_narasi": "Ditemukan varian baru botnet ddos zero-day berbahaya.",
            "kata_kunci": "ddos, zero-day, baru, varian baru",
            "kategori": "berita",
            "kategori_relevansi": "insiden_spesifik",
            "kategori_taksonomi": "ddos",
            "tanggal_publish": "2026-10-21 11:00:00",
            "sumber": "CERT Warning 1"
        })
        rows.append({
            "identifier": "cur_novel_2",
            "judul": "Celah Cepat Banjir Trafik Melumpuhkan Portal Layanan Publik Daerah",
            "ringkasan_atau_narasi": "Lonjakan trafik masif ddos melumpuhkan sistem operasional.",
            "kata_kunci": "ddos, lonjakan, ketersediaan, kritis",
            "kategori": "berita",
            "kategori_relevansi": "insiden_spesifik",
            "kategori_taksonomi": "ddos",
            "tanggal_publish": "2026-10-21 11:30:00",
            "sumber": "CERT Warning 2"
        })

        df = pd.DataFrame(rows)
        rag = RAGEngine(df)
        
        # POLA ANCAMAN should be Ransomware (highest volume)
        pola = rag.hitung_prediksi_pola_serangan()
        assert pola["kategori_taksonomi"] == "ransomware", (
            f"Expected Pola Ancaman = ransomware, got '{pola['kategori_taksonomi']}'"
        )

        # SINYAL ANCAMAN BARU should be DDoS (novelty > volume)
        sinyal = rag.hitung_prediksi_ancaman_baru()
        expected_ddos = TAXONOMY_DISPLAY_NAMES["ddos"]
        assert sinyal == expected_ddos, (
            f"Expected Emerging Threat = '{expected_ddos}', got '{sinyal}'"
        )

    def test_generic_categories_never_trigger_emerging_alert(self):
        """
        Adversarial test: 'tidak_dapat_ditentukan' and 'lainnya' with >= 2 cases and novelty keywords
        MUST NEVER trigger emerging threat alert.
        """
        for generic_cat in ["tidak_dapat_ditentukan", "lainnya"]:
            df = self._build_dataset(generic_cat, count_cur=5, count_base=0, with_novelty_kw=True)
            rag = RAGEngine(df)
            signal = rag.hitung_prediksi_ancaman_baru()
            assert signal == "Kondisi Stabil", (
                f"Generic category '{generic_cat}' breached emerging threat filter: '{signal}'!"
            )


# =====================================================================
# 3. DOM & UI VERIFICATION ('Taksonomi Resmi' Badge Complete Absence)
# =====================================================================

class TestDomAndUiVerification:
    """
    Scans HTML templates and JavaScript files for forbidden strings.
    'Taksonomi Resmi: [...]' was removed in R1 and must NOT appear in DOM or scripts.
    """

    def test_no_taksonomi_resmi_badge_in_html_partials(self):
        """Checks _tren.html and all partials for 'Taksonomi Resmi:'."""
        repo_root = Path(__file__).resolve().parent.parent
        templates_dir = repo_root / "src" / "web" / "templates"
        
        html_files = list(templates_dir.rglob("*.html"))
        assert len(html_files) > 0, "No HTML files found to inspect"

        offending_files = []
        for html_path in html_files:
            content = html_path.read_text(encoding="utf-8", errors="ignore")
            if "Taksonomi Resmi:" in content or "Taksonomi Resmi :" in content:
                offending_files.append(str(html_path))

        assert not offending_files, (
            f"Found forbidden badge 'Taksonomi Resmi:' in HTML files: {offending_files}"
        )

    def test_no_taksonomi_resmi_badge_in_js_files(self):
        """Checks all JS files in src/web/static/js for 'Taksonomi Resmi' injections."""
        repo_root = Path(__file__).resolve().parent.parent
        js_dir = repo_root / "src" / "web" / "static" / "js"
        
        js_files = list(js_dir.rglob("*.js"))
        assert len(js_files) > 0, "No JS files found to inspect"

        offending_files = []
        for js_path in js_files:
            content = js_path.read_text(encoding="utf-8", errors="ignore")
            if "Taksonomi Resmi:" in content or "Taksonomi Resmi :" in content:
                offending_files.append(str(js_path))

        assert not offending_files, (
            f"Found forbidden string 'Taksonomi Resmi:' in JS files: {offending_files}"
        )


# =====================================================================
# 4. DATABASE SCHEMA & INJECTION RESISTANCE
# =====================================================================

class TestDatabaseSchemaAndInjectionResistance:
    """
    Stress-tests simpan_koreksi_admin_sektor against malicious payloads,
    SQL injection attempts, unescaped quotes, null values, and unicode strings.
    """

    @pytest.fixture
    def test_db(self):
        """Creates an isolated temporary SQLite database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            temp_db_path = Path(f.name)
        
        init_db(temp_db_path)
        yield temp_db_path
        
        try:
            temp_db_path.unlink()
        except Exception:
            pass

    def test_sql_injection_payloads_in_sektor(self, test_db):
        """
        Attempts SQL injection in article_identifier, sektor, alasan, and oleh.
        Verifies query parameterization stops syntax errors and malicious execution.
        """
        malicious_inputs = [
            "'; DROP TABLE intelijen_berita_tervalidasi; --",
            "\" OR \"1\"=\"1",
            "Administrasi Pemerintahan' OR 1=1; --",
            "<script>alert('xss')</script>",
            "Robert'); DROP TABLE Students;--",
            "Sektor' -- comment",
            "None",
            "NULL",
            "D'Artagnan & O'Connor Sektor",
            "Sektor \u200b\ufeff\u0000 Zero-Byte & Invisible",
            "🎯 Sektor Pertahanan & Keamanan 🛡️"
        ]

        for idx, payload in enumerate(malicious_inputs):
            ident = f"article_test_{idx}_{payload[:10]}"
            # Must not crash, raise sqlite3.OperationalError, or drop tables
            ok = simpan_koreksi_admin_sektor(
                article_identifier=ident,
                sektor=payload,
                alasan=f"Alasan payload {payload}",
                oleh="Adversarial Tester",
                db_path=test_db
            )
            assert ok is True, f"Failed to save correction with payload: {payload}"

            # Query back and verify exact string matches without execution
            rec = ambil_intelijen_berita(ident, db_path=test_db)
            assert rec is not None, f"Record not found for identifier {ident}"
            assert rec["koreksi_admin_sektor"] == payload, (
                f"Data corrupted! Expected '{payload}', got '{rec['koreksi_admin_sektor']}'"
            )

        # Confirm table still exists and has records
        with sqlite3.connect(str(test_db)) as conn:
            cur = conn.execute("SELECT count(*) FROM intelijen_berita_tervalidasi")
            count = cur.fetchone()[0]
            assert count == len(malicious_inputs)

    def test_null_and_empty_edge_cases(self, test_db):
        """Tests handling of empty strings, None, and partial updates."""
        # Empty identifier returns False
        assert simpan_koreksi_admin_sektor("", "Energi", db_path=test_db) is False
        assert simpan_koreksi_admin_sektor(None, "Energi", db_path=test_db) is False

        # First insert record with normal data
        ident = "test_art_null_check"
        simpan_koreksi_admin_sektor(ident, "Energi", alasan="Awal", oleh="Admin1", db_path=test_db)

        # Update with None alasan (COALESCE should preserve previous alasan)
        simpan_koreksi_admin_sektor(ident, "Kesehatan", alasan=None, oleh="Admin2", db_path=test_db)
        rec = ambil_intelijen_berita(ident, db_path=test_db)
        assert rec["koreksi_admin_sektor"] == "Kesehatan"
        assert rec["alasan_sektor"] == "Awal"  # Preserved via COALESCE
        assert rec["koreksi_admin_oleh"] == "Admin2"
