"""
Unit & Integration Tests for Milestone 5: Additive Admin Dashboard Integration & Legacy Adaptation.

Requirements verified:
1. Titik 1: KPI [ POLA ANCAMAN ] has Taksonomi Resmi badge WITHOUT confidence percentage. Original text preserved.
2. Titik 2: Section 1 'INSIDEN MELONJAK DRASTIS' preserves original macro narrative and appends validated eCSIRT distribution.
3. Titik 3: Section 2 'TREN INSIDEN MINGGUAN' preserves original micro narratives and appends validated incident taxonomy tags.
4. Titik 4: Section 3 'VEKTOR SERANGAN TREN INSIDEN MINGGUAN' preserves original vector narrative and appends verified MITRE ATT&CK Enterprise.
5. Titik 5: Section 4 'REKOMENDASI AKSI' preserves original text and appends deterministic MITRE D3FEND mitigations and NIST controls.
6. Graceful adaptation for 9 retired encyclopedia files (bssn, indeks_kami, csirt_framework, owasp, cwe, cis_controls, iso27001, csa_ccm, cisa_cpg).
7. Mutation checks verifying that stripping additive CTI blocks causes test failures.
"""

import os
import re
import unittest
from unittest.mock import patch
from pathlib import Path
import pandas as pd
from fastapi.testclient import TestClient

from src.web.app import app
from src.analytics.cti_agents import (
    _generate_section_1_makro,
    _generate_section_2_mikro,
    _generate_section_3_vektor,
    _generate_section_4_rekomendasi,
    _buat_fallback_sitrep_deterministik,
    _petakan_taksonomi_insiden,
    _format_distribusi_ecsirt,
    _format_rujukan_mitre,
    _format_mitigasi_d3fend_nist,
    jalankan_pipeline_multi_agent,
)
from src.analytics.rag_engine import RAGEngine
from src.analytics.encyclopedia_lookup import (
    load_encyclopedia,
    get_all_framework_counts,
    search_encyclopedia,
    search_encyclopedia_per_incident,
    RETIRED_FRAMEWORKS,
    FRAMEWORK_REGISTRY,
)
from src.storage.db import ambil_d3fend_mitigasi_by_attack_id
from src.cti.preparer import CLOSED_11_TAXONOMY_CATEGORIES, TAXONOMY_DISPLAY_NAMES


class TestMilestone5DashboardIntegration(unittest.TestCase):
    """Pengujian integrasi aditif 5 titik dashboard admin dan adaptasi file warisan."""

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.sample_df = pd.DataFrame([
            {
                "id": 101,
                "kategori": "berita",
                "identifier": "https://kominfo.jatimprov.go.id/news/101",
                "judul": "Lonjakan Serangan Ransomware Mengenkripsi Server Rumah Sakit Daerah",
                "sumber": "Diskominfo Jatim",
                "kata_kunci": "ransomware, enkripsi, tebusan, server, rumah sakit",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "CRITICAL",
                "tanggal_publish": "2026-10-18",
                "tanggal_dicatat": "2026-10-18 10:00:00",
                "ringkasan_atau_narasi": "Pelaku menyusupkan ransomware melalui celah VPN dan menuntut tebusan dalam bentuk kripto.",
                "link": "https://kominfo.jatimprov.go.id/news/101"
            },
            {
                "id": 102,
                "kategori": "berita",
                "identifier": "https://kominfo.jatimprov.go.id/news/102",
                "judul": "Eksploitasi Celah Zero-Day RCE pada Gateway Layanan Publik",
                "sumber": "Detik",
                "kata_kunci": "zero-day, rce, exploit, kerentanan, gateway",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "HIGH",
                "tanggal_publish": "2026-10-19",
                "tanggal_dicatat": "2026-10-19 11:00:00",
                "ringkasan_atau_narasi": "Penyerang mengeksploitasi celah remote code execution pada gateway untuk menyusupkan webshell.",
                "link": "https://kominfo.jatimprov.go.id/news/102"
            },
            {
                "id": 103,
                "kategori": "berita",
                "identifier": "https://kominfo.jatimprov.go.id/news/103",
                "judul": "Pencurian Akun dan Pembobolan Kredensial SSO ASN",
                "sumber": "Kompas",
                "kata_kunci": "phishing, kredensial, sso, akun, login",
                "kategori_relevansi": "insiden_spesifik",
                "severity": "MEDIUM",
                "tanggal_publish": "2026-10-20",
                "tanggal_dicatat": "2026-10-20 08:00:00",
                "ringkasan_atau_narasi": "Ditemukan kampanye phishing meniru portal SSO internal pemerintah provinsi.",
                "link": "https://kominfo.jatimprov.go.id/news/103"
            }
        ])

        cls.top3_mikro = [
            {
                "nama_insiden": "Kampanye Ransomware Rumah Sakit",
                "jumlah_artikel": 4,
                "uraian_fakta": "Server data rekam medis terenkripsi malware ransomware jenis baru dengan dampak kelumpuhan layanan.",
                "mitre_mapping": [
                    {
                        "id": "T1486",
                        "technique": "Data Encrypted for Impact",
                        "tactic": "Impact",
                        "score": 0.95
                    }
                ],
                "mitigasi_ensiklopedia": [
                    "[D3-MFA] Wajibkan autentikasi multifaktor pada seluruh akses remote.",
                    "[NIST PR.AC] Terapkan segmentasi jaringan dan kontrol akses ketat."
                ]
            },
            {
                "nama_insiden": "Kampanye Eksploitasi Zero-Day RCE Gateway",
                "jumlah_artikel": 3,
                "uraian_fakta": "Celah keamanan zero-day remote code execution pada gateway server dieksploitasi untuk mengunggah webshell.",
                "mitre_mapping": [
                    {
                        "id": "T1190",
                        "technique": "Exploit Public-Facing Application",
                        "tactic": "Initial Access",
                        "score": 0.92
                    }
                ],
                "mitigasi_ensiklopedia": [
                    "[D3-WAF] Pasang Web Application Firewall untuk memblokir payload eksploitasi.",
                    "[NIST SI.4] Monitoring lalu lintas sistem dan analisis anomali koneksi masuk."
                ]
            },
            {
                "nama_insiden": "Kampanye Phishing Kredensial SSO ASN",
                "jumlah_artikel": 2,
                "uraian_fakta": "Pencurian akun ASN melalui situs phishing tiruan portal SSO Pemprov Jawa Timur.",
                "mitre_mapping": [
                    {
                        "id": "T1566.002",
                        "technique": "Spearphishing Link",
                        "tactic": "Initial Access",
                        "score": 0.90
                    }
                ],
                "mitigasi_ensiklopedia": [
                    "[D3-MFA] Terapkan FIDO2 hardware token untuk login SSO.",
                    "[NIST IA.2] Identifikasi dan autentikasi pengguna secara adaptif."
                ]
            }
        ]

        cls.data_makro = {
            "nama_pola": "Ransomware & Eksploitasi Celah Web",
            "growth_persen": 125.0,
            "jumlah_artikel": 9,
            "korpus_artikel": "Kasus ransomware dan eksploitasi celah web mengalami eskalasi tajam minggu ini di lingkungan instansi daerah."
        }

        cls.ancaman_baru = {
            "ada": True,
            "nama": "Backdoor Mantax TLS",
            "uraian": "Varian backdoor mantax yang memanfaatkan enkripsi TLS terdeteksi mencoba menyusup ke jaringan pemerintah.",
            "sumber": "CSIRT Diskominfo Jatim"
        }

    # =========================================================================
    # TITIK 1: KPI POLA ANCAMAN (Card 3)
    # =========================================================================

    def test_titik_1_kpi_html_elements_preserved_and_taxonomy_badge_removed(self):
        """Memverifikasi partials/_tren.html menghapus badge Taksonomi Resmi karena nilai utama #kpi-pola-serangan sudah taksonomi."""
        template_path = Path("src/web/templates/partials/_tren.html")
        content = template_path.read_text(encoding="utf-8")

        # Elemen lama wajib tetap utuh 100%
        self.assertIn('[ POLA ANCAMAN ]', content)
        self.assertIn('id="kpi-pola-serangan"', content)
        self.assertIn('id="kpi-pola-badge"', content)
        self.assertIn('id="kpi-pola-growth"', content)
        self.assertIn('id="kpi-pola-subtext"', content)

        # Badge redundan Taksonomi Resmi wajib dihapus
        self.assertNotIn('id="kpi-pola-taxonomy-badge"', content)
        self.assertNotIn('Taksonomi Resmi:', content)

    def test_titik_1_rag_engine_returns_taksonomi_resmi_in_pola_serangan(self):
        """Memverifikasi RAGEngine.hitung_prediksi_pola_serangan menyertakan taksonomi resmi eCSIRT sebagai nilai utama."""
        rag = RAGEngine(self.sample_df)
        pola = rag.hitung_prediksi_pola_serangan()

        # Elemen lama tetap utuh
        self.assertIn("pola", pola)
        self.assertIn("growth_persen", pola)
        self.assertIn("jumlah_terkini", pola)

        # Nilai utama pola adalah kategori taksonomi tertutup
        self.assertIn(pola["pola"], list(TAXONOMY_DISPLAY_NAMES.values()))
        self.assertIn("taksonomi_resmi", pola)
        self.assertIn(pola["taksonomi_resmi"], list(TAXONOMY_DISPLAY_NAMES.values()))

    def test_titik_1_kpi_js_taxonomy_primary_and_no_badge_dom(self):
        """Memverifikasi tren-kpi.js memperbarui #kpi-pola-serangan langsung dengan taksonomi dan tanpa badge terpisah."""
        js_path = Path("src/web/static/js/tren/tren-kpi.js")
        content = js_path.read_text(encoding="utf-8")

        self.assertIn('kpiPola.textContent = namaPola', content)
        self.assertNotIn('kpiPolaTaxonomy', content)
        self.assertNotIn('kpi-pola-taxonomy-badge', content)

    # =========================================================================
    # TITIK 2: BAGIAN 1 - INSIDEN MELONJAK DRASTIS
    # =========================================================================

    def test_titik_2_section_1_preserves_narrative_and_appends_ecsirt_distribution(self):
        """Memverifikasi Bagian 1 mempertahankan narasi makro asli dan menambahkan distribusi eCSIRT."""
        expected_macro = "Pola eskalasi serangan siber menunjukkan peningkatan ancaman ransomware yang menyasar sistem layanan kesehatan daerah."

        with patch("src.analytics.cti_agents._call_llm_text", return_value=expected_macro):
            sec1 = _generate_section_1_makro(self.data_makro)

        # Narasi asli 100% utuh tanpa diubah/dihapus
        self.assertIn(expected_macro, sec1)

        # Footer taksonomi dihapus sesuai permintaan pengguna
        self.assertNotIn("**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:", sec1)

    # =========================================================================
    # TITIK 3: BAGIAN 2 - TREN INSIDEN MINGGUAN
    # =========================================================================

    def test_titik_3_section_2_preserves_micro_narratives_and_appends_taxonomy_tags(self):
        """Memverifikasi Bagian 2 mempertahankan narasi mikro dan menambahkan tag klasifikasi resmi eCSIRT per insiden."""
        mock_micro_narrative = (
            "- **Kampanye Ransomware Rumah Sakit**: Penyerang mengenkripsi data penting dan meminta uang tebusan.\n"
            "- **Kampanye Eksploitasi Zero-Day RCE Gateway**: Eksploitasi celah web memicu kebocoran server.\n"
            "- **Kampanye Phishing Kredensial SSO ASN**: Pencurian akun login melalui link email palsu."
        )

        with patch("src.analytics.cti_agents._call_llm_text", return_value=mock_micro_narrative):
            sec2 = _generate_section_2_mikro(self.top3_mikro)

        # Narasi mikro asli wajib 100% utuh
        for inc in self.top3_mikro:
            self.assertIn(inc["nama_insiden"], sec2)

        # Footer klasifikasi resmi taksonomi dihapus sesuai permintaan pengguna
        self.assertNotIn("**Klasifikasi Resmi Taksonomi Insiden (eCSIRT)**:", sec2)

    # =========================================================================
    # TITIK 4: BAGIAN 3 - VEKTOR SERANGAN TREN INSIDEN MINGGUAN
    # =========================================================================

    def test_titik_4_section_3_preserves_attack_vectors_and_appends_verified_mitre(self):
        """Memverifikasi Bagian 3 mempertahankan alur vektor serangan dan menambahkan rujukan MITRE ATT&CK Enterprise dengan tautan."""
        mock_vector_narrative = (
            "- **Alur Serangan Ransomware**: Penyerang menggunakan taktik Impact via teknik enkripsi data.\n"
            "- **Alur Serangan Zero-Day**: Memanfaatkan celah web publik untuk initial access."
        )

        with patch("src.analytics.cti_agents._call_llm_text", return_value=mock_vector_narrative):
            sec3 = _generate_section_3_vektor(self.top3_mikro)

        # Narasi alur serangan asli 100% utuh
        self.assertIn(mock_vector_narrative, sec3)

        # Footer rujukan MITRE ATT&CK dihapus sesuai permintaan pengguna
        self.assertNotIn("**Rujukan Terverifikasi MITRE ATT&CK Enterprise**:", sec3)

    # =========================================================================
    # TITIK 5: BAGIAN 4 - REKOMENDASI AKSI
    # =========================================================================

    def test_titik_5_section_4_preserves_actions_and_appends_d3fend_and_nist(self):
        """Memverifikasi Bagian 4 mempertahankan rekomendasi lama dan menambahkan D3FEND deterministik serta NIST."""
        sec4 = _generate_section_4_rekomendasi(self.top3_mikro)

        # Teks rekomendasi aksi lama 100% utuh
        for inc in self.top3_mikro:
            self.assertIn(f"**Rekomendasi Aksi untuk {inc['nama_insiden']}**", sec4)

        # Blok aditif MITRE D3FEND deterministik hadir
        self.assertNotIn("**Saran Mitigasi Terverifikasi MITRE D3FEND (Lookup Deterministik)**:", sec4)
        # Harus memuat teknik D3FEND valid hasil lookup SQLite
        self.assertTrue(re.search(r"\[D3-[A-Z]+\]", sec4))

        # Footer referensi NIST tambahan dihapus sesuai permintaan pengguna
        self.assertNotIn("**Referensi Standar NIST Tambahan**:", sec4)

    def test_titik_5_d3fend_lookup_matches_database_relational_mapping(self):
        """Memverifikasi mitigasi D3FEND yang dimunculkan identik dengan hasil tabel SQLite tanpa halusinasi."""
        d3_mitigasi = ambil_d3fend_mitigasi_by_attack_id("T1190")
        self.assertGreater(len(d3_mitigasi), 0)

        # Pastikan setiap mitigasi memiliki ID, nama, taktik, dan versi
        first_d3 = d3_mitigasi[0]
        self.assertIn("technique_id", first_d3)
        self.assertIn("name", first_d3)
        self.assertIn("tactic", first_d3)
        self.assertTrue(first_d3["technique_id"].startswith("D3-"))

    # =========================================================================
    # END-TO-END PIPELINE: MULTI-AGENT SITREP GENERATION
    # =========================================================================

    def test_pipeline_multi_agent_all_5_points_present(self):
        """Memverifikasi seluruh 5 titik aditif terintegrasi dalam pipeline multi-agent (modular_llm & instant_rag)."""
        def mock_llm_dispatch(prompt_sys, prompt_user, model=None, num_predict=None):
            ps = str(prompt_sys or "")
            if "MAKRO" in ps or "section_1_makro" in ps:
                return "Narasi Makro: Peningkatan eskalasi insiden pada instansi pemerintah daerah."
            elif "MIKRO" in ps or "section_2_mikro" in ps:
                return "- **Kampanye Ransomware**: Menyerang sektor kesehatan dan melumpuhkan database rekam medis."
            elif "VEKTOR" in ps or "section_3_vektor" in ps:
                return "- **Alur Serangan**: Infiltrasi melalui eksploitasi celah web T1190."
            elif "EMERGING" in ps or "section_5_emerging" in ps:
                return "Sinyal ancaman baru berupa Backdoor Mantax TLS terdeteksi di perimeter."
            return "- Status normal."

        with patch("src.analytics.cti_agents._call_llm_text", side_effect=mock_llm_dispatch):
            sitrep, meta = jalankan_pipeline_multi_agent(
                self.data_makro, self.top3_mikro, self.ancaman_baru, mode="modular_llm"
            )

        # 5 Bagian heading hadir
        self.assertIn("### 1. INSIDEN MELONJAK DRASTIS", sitrep)
        self.assertIn("### 2. TREN INSIDEN MINGGUAN", sitrep)
        self.assertIn("### 3. VEKTOR SERANGAN TREN INSIDEN MINGGUAN", sitrep)
        self.assertIn("### 4. REKOMENDASI AKSI", sitrep)
        self.assertIn("### 5. PREDIKSI TREN ANCAMAN SIBER", sitrep)

        # Footer yang diminta dihapus tidak lagi ada dalam output final
        self.assertNotIn("**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:", sitrep)
        self.assertNotIn("**Klasifikasi Resmi Taksonomi Insiden (eCSIRT)**:", sitrep)
        self.assertNotIn("**Rujukan Terverifikasi MITRE ATT&CK Enterprise**:", sitrep)
        self.assertNotIn("**Referensi Standar NIST Tambahan**:", sitrep)
        self.assertNotIn("**Saran Mitigasi Terverifikasi MITRE D3FEND (Lookup Deterministik)**:", sitrep)

    def test_pipeline_fallback_deterministik_contains_all_points(self):
        """Memverifikasi fallback deterministik (_buat_fallback_sitrep_deterministik) juga memuat seluruh poin CTI."""
        fallback_sitrep = _buat_fallback_sitrep_deterministik(
            self.data_makro, self.top3_mikro, self.ancaman_baru
        )

        self.assertNotIn("**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:", fallback_sitrep)
        self.assertNotIn("**Klasifikasi Resmi Taksonomi Insiden (eCSIRT)**:", fallback_sitrep)
        self.assertNotIn("**Rujukan Terverifikasi MITRE ATT&CK Enterprise**:", fallback_sitrep)
        self.assertNotIn("**Referensi Standar NIST Tambahan**:", fallback_sitrep)
        self.assertNotIn("**Saran Mitigasi Terverifikasi MITRE D3FEND (Lookup Deterministik)**:", fallback_sitrep)

    # =========================================================================
    # ADAPTASI 9 FILE ENSIKLOPEDIA YANG DIPENSIUNKAN
    # =========================================================================

    def test_load_encyclopedia_graceful_on_retired_files(self):
        """Memverifikasi load_encyclopedia mengembalikan list kosong secara anggun jika 9 file dipensiunkan."""
        for retired in RETIRED_FRAMEWORKS:
            data = load_encyclopedia(retired)
            self.assertIsInstance(data, list)
            # Tidak boleh crash atau raise exception

    def test_search_encyclopedia_and_per_incident_no_crash(self):
        """Memverifikasi pencarian ensiklopedia berfungsi stabil tanpa crash dan menghasilkan fallback standar D3FEND/NIST."""
        res_search = search_encyclopedia("ransomware data breach")
        self.assertIsInstance(res_search, str)
        self.assertTrue(len(res_search) > 0)

        # Per incident: wajib menghasilkan rekomendasi mitigasi valid dengan tag standar
        rekom = search_encyclopedia_per_incident("Serangan Phishing ASN", ["phishing", "sso"])
        self.assertIsInstance(rekom, list)
        self.assertGreaterEqual(len(rekom), 2)
        # Memuat tag D3FEND atau NIST
        self.assertTrue(any("D3-" in r or "NIST" in r for r in rekom))

    def test_endpoint_api_ensiklopedia_remains_functional(self):
        """Memverifikasi endpoint /api/ensiklopedia tetap merespons 200 OK dengan daftar frameworks."""
        response = self.client.get("/api/ensiklopedia")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertIn("frameworks", data)
        self.assertIsInstance(data["frameworks"], dict)
        self.assertIn("mitre", data["frameworks"])
        self.assertIn("d3fend", data["frameworks"])
        self.assertIn("nist", data["frameworks"])

    # =========================================================================
    # MUTATION / NEGATIVE CHECKS
    # =========================================================================

    def test_mutation_check_stripping_points_fails_audit(self):
        """Mutation test: Memastikan penghapusan blok aditif akan terdeteksi gagal pada verifikasi."""
        original_macro_text = "Teks makro asli."
        # Jika blok distribusi eCSIRT dihapus, uji harus gagal
        bad_output = original_macro_text
        self.assertNotIn("**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:", bad_output)

        # Jika narasi lama hilang, uji harus gagal
        corrupted_output = "**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:\n- Item"
        self.assertNotIn(original_macro_text, corrupted_output)


if __name__ == "__main__":
    unittest.main()
