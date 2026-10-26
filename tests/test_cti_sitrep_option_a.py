"""
Unit tests for Option A implementation in src/analytics/cti_agents.py (R3 Audit & SITREP Remediation).

Verifies that all 5 findings from the audit are strictly remediated under Option A:
- Finding 1: eCSIRT distribution empty state outputs honest notice without hardcoded fallback categories.
- Finding 2: MITRE ATT&CK reference stops at tactic or outputs unmapped message without defaulting to T1190.
- Finding 3: MITRE D3FEND deterministic lookup outputs unmapped notice without defaulting to D3-MFA.
- Finding 4: NIST control reference outputs unmapped notice without defaulting to AC-2 / PR.AC-1.
- Finding 5: Heuristic detection and deterministic fallback SITREP rely strictly on verified facts without fabricating sectors or attack methods.
"""

import unittest
from unittest.mock import patch
from src.analytics.cti_agents import (
    _format_distribusi_ecsirt,
    _format_rujukan_mitre,
    _format_mitigasi_d3fend_nist,
    _deteksi_sektor_spesifik,
    _deteksi_senjata_spesifik,
    _deteksi_dampak_spesifik,
    _buat_fallback_sitrep_deterministik,
    _generate_section_3_vektor,
    _generate_section_4_rekomendasi,
    _petakan_taksonomi_insiden,
)


class TestCTISitrepOptionA(unittest.TestCase):
    """Test verification suite for Option A genuine logic & zero hardcoding."""

    # -------------------------------------------------------------------------
    # FINDING 1: Bagian 1 - eCSIRT distribution when DB empty
    # -------------------------------------------------------------------------
    def test_finding_1_ecsirt_distribution_empty_state_option_a(self):
        """Pastikan jika tabel database kosong, output menampilkan pesan jujur tanpa string kategori palsu."""
        with patch("src.storage.db._koneksi") as mock_conn:
            # Simulasi DB mengembalikan 0 rows
            mock_cursor = mock_conn.return_value.__enter__.return_value
            mock_cursor.execute.return_value.fetchall.return_value = []

            output = _format_distribusi_ecsirt({"nama_pola": "Ancaman Umum"})

            self.assertIn("**Distribusi Taksonomi Insiden Tervalidasi (eCSIRT)**:", output)
            self.assertIn("- (Belum ada data distribusi taksonomi tervalidasi pada periode ini)", output)
            # Pastikan kategori palsu tidak pernah muncul saat data kosong
            self.assertNotIn("Akses Tidak Sah / Pembobolan Akun (eCSIRT: intrusions:account-compromise)", output)
            self.assertNotIn("Eksploitasi Kerentanan (Exploit / Zero-Day) (eCSIRT: intrusion-attempts:ids-alert)", output)
            self.assertNotIn("Malware / Infostealer (eCSIRT: malicious-code:malware)", output)

    # -------------------------------------------------------------------------
    # FINDING 2: Bagian 3 - ATT&CK technique fallback
    # -------------------------------------------------------------------------
    def test_finding_2_mitre_attack_fallback_option_a(self):
        """Pastikan jika alur serangan tidak terpetakan, sistem TIDAK melakukan fallback ke T1190."""
        # Kasus 1: Insiden tanpa mitre_mapping sama sekali
        incidents_unmapped = [
            {"nama_insiden": "Insiden Tanpa Alur Jelas", "mitre_mapping": []}
        ]
        output = _format_rujukan_mitre(incidents_unmapped)
        self.assertIn("**Rujukan Terverifikasi MITRE ATT&CK Enterprise**:", output)
        self.assertIn("- Alur serangan tidak terpetakan pada teknik spesifik ATT&CK", output)
        self.assertNotIn("T1190", output)
        self.assertNotIn("Exploit Public-Facing Application", output)

        # Kasus 2: Insiden hanya terpetakan pada tingkat taktik tanpa teknik
        incidents_tactic_only = [
            {"nama_insiden": "Insiden Hanya Taktik", "mitre_mapping": [{"tactic": "Persistence"}]}
        ]
        output_tactic = _format_rujukan_mitre(incidents_tactic_only)
        self.assertIn("- Taktik ATT&CK: **Persistence** (Teknik spesifik tidak ditentukan)", output_tactic)
        self.assertNotIn("T1190", output_tactic)

    def test_finding_2_section_3_vector_llm_fallback_option_a(self):
        """Pastikan prompt dan fallback generator narasi vektor tidak menyuntikkan T1190 sembarangan."""
        incidents = [
            {"nama_insiden": "Insiden Kredensial", "uraian_fakta": "Akun login dicuri.", "mitre_mapping": []}
        ]
        with patch("src.analytics.cti_agents._call_llm_text", return_value=""):
            sec3 = _generate_section_3_vektor(incidents)
            self.assertIn("Alur serangan tidak terpetakan pada teknik spesifik ATT&CK", sec3)
            self.assertNotIn("T1190", sec3)

    # -------------------------------------------------------------------------
    # FINDING 3: Bagian 4 - D3FEND mitigation fallback
    # -------------------------------------------------------------------------
    def test_finding_3_d3fend_mitigation_fallback_option_a(self):
        """Pastikan jika lookup D3FEND tidak menemukan pemetaan, tidak ada fallback ke D3-MFA."""
        incidents = [
            {"nama_insiden": "Insiden Tanpa Mitigasi", "mitre_mapping": [{"id": "T9999", "technique": "Fake"}]}
        ]
        with patch("src.storage.db.ambil_d3fend_mitigasi_by_attack_id", return_value=[]):
            d3_block, _ = _format_mitigasi_d3fend_nist(incidents)
            self.assertIn("**Saran Mitigasi Terverifikasi MITRE D3FEND (Lookup Deterministik)**:", d3_block)
            self.assertIn("- Tidak ditemukan pemetaan mitigasi D3FEND spesifik untuk teknik ini", d3_block)
            self.assertNotIn("[D3-MFA]", d3_block)

    # -------------------------------------------------------------------------
    # FINDING 4: Bagian 4 - NIST controls fallback
    # -------------------------------------------------------------------------
    def test_finding_4_nist_controls_fallback_option_a(self):
        """Pastikan jika kontrol NIST tidak cocok atau tidak tersedia, tidak ada fallback ke AC-2 / PR.AC-1."""
        incidents = [{"nama_insiden": "Insiden X", "mitre_mapping": []}]
        with patch("pathlib.Path.exists", return_value=False):
            _, nist_block = _format_mitigasi_d3fend_nist(incidents)
            self.assertIn("**Referensi Standar NIST Tambahan**:", nist_block)
            self.assertIn("- Referensi kontrol NIST tambahan tidak tersedia", nist_block)
            self.assertNotIn("[AC-2]", nist_block)
            self.assertNotIn("[PR.AC-1]", nist_block)

    def test_finding_4_section_4_rekomendasi_no_hardcoded_controls(self):
        """Pastikan _generate_section_4_rekomendasi tidak menyuntikkan D3-MFA / NIST PR.AC saat mitigasi kosong."""
        incidents = [
            {"nama_insiden": "Insiden Kosong", "mitigasi_ensiklopedia": []}
        ]
        sec4 = _generate_section_4_rekomendasi(incidents)
        self.assertIn("- Referensi kontrol NIST tambahan tidak tersedia", sec4)
        self.assertNotIn("[D3-MFA] Wajibkan autentikasi", sec4)

    # -------------------------------------------------------------------------
    # FINDING 5: Heuristik deteksi & narasi fallback deterministik
    # -------------------------------------------------------------------------
    def test_finding_5_heuristic_detectors_no_fabricated_defaults(self):
        """Pastikan detektor heuristik mengembalikan None bila entitas tidak terdeteksi (tidak ada 'Layanan Publik Daerah')."""
        teks_acak = "Sebuah peristiwa terjadi di suatu tempat tanpa rincian sektor atau metode."
        self.assertIsNone(_deteksi_sektor_spesifik(teks_acak))
        self.assertIsNone(_deteksi_senjata_spesifik(teks_acak))
        self.assertIsNone(_deteksi_dampak_spesifik(teks_acak))

        # Jika ada bukti nyata, harus terdeteksi secara akurat
        teks_bukti = "Peretas menyusupkan ransomware ke rumah sakit umum daerah dan mengunci data rekam medis."
        self.assertEqual(_deteksi_sektor_spesifik(teks_bukti), "Sektor Kesehatan")
        self.assertEqual(_deteksi_senjata_spesifik(teks_bukti), "Ransomware / File Encryptor")

    def test_finding_5_fallback_sitrep_deterministik_option_a(self):
        """Pastikan _buat_fallback_sitrep_deterministik tidak mengarang Target Layanan Publik Daerah atau Akses Ilegal."""
        data_makro = {"nama_pola": "Ancaman Umum", "growth_persen": 50}
        top3_mikro = [
            {
                "nama_insiden": "Kebocoran Kredensial Rahasia",
                "uraian_fakta": "Ditemukan kredensial beredar di forum gelap.",
                "mitre_mapping": [],
                "mitigasi_ensiklopedia": []
            }
        ]
        ancaman_baru = {"ada": False}

        sitrep = _buat_fallback_sitrep_deterministik(data_makro, top3_mikro, ancaman_baru)

        # Tidak boleh ada fabrikasi default palsu
        self.assertNotIn("Target Layanan Publik Daerah", sitrep)
        self.assertNotIn("Akses Ilegal & Eksploitasi Web", sitrep)
        self.assertNotIn("Gangguan Integritas Sistem", sitrep)
        self.assertNotIn("T1190", sitrep)
        self.assertIn("Alur serangan tidak terpetakan pada teknik spesifik ATT&CK", sitrep)


if __name__ == "__main__":
    unittest.main()
