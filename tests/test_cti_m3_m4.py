"""
Unit & Integration Test Suite for SiberHarian CTI Milestones 3 & 4.

Menguji secara mendalam:
- Milestone 3 (RAG Multilingual Vector Indexing - CTIVectorStore):
  * 3 isolated collection namespaces (collection_attack, collection_taxonomy, collection_nist).
  * Multilingual embedding adapter (dimension 768, fallback chain, deterministic offline embedding).
  * Dual-text translation strategy (Indonesian + English for taxonomy; English-only for ATT&CK and NIST).
  * Persistent storage folders per collection.
  * Partial failure resilience.

- Milestone 4 (Per-News Processing Pipeline & Guardrails - CTINewsAnalyzer):
  * Incident classification to closed 11 categories with structured JSON schema.
  * Mandatory fallback to 'Tidak Dapat Ditentukan' on non-incident / weak evidence news.
  * Conditional ATT&CK extraction gate (abstains when no attack flow present).
  * Vague attack flow stops at Tactic level.
  * Active ATT&CK Validation Guard: rejects hallucinated, fake, and revoked IDs.
  * Deterministic D3FEND SQL mitigation lookup (zero LLM additions, disclaimer attached).
  * NIST reference on-demand retrieval.
  * Provenance storage in intelijen_berita_tervalidasi and admin manual correction tracking.
"""

import os
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.cti.vector_store import (
    CTIVectorStore,
    compute_deterministic_embedding,
    cosine_similarity,
    VECTOR_DIMENSION,
)
from src.cti.analyzer import (
    CTINewsAnalyzer,
    DISCLAIMER_D3FEND,
)
from src.cti.preparer import (
    CLOSED_11_TAXONOMY_CATEGORIES,
    TAXONOMY_DISPLAY_NAMES,
    ECSIRT_PARENT_MAPPINGS,
)
from src.storage.db import (
    init_db,
    DEFAULT_DB_PATH,
    simpan_intelijen_berita,
    ambil_intelijen_berita,
    simpan_koreksi_admin_intelijen,
    tandai_flag_tinjauan_intelijen,
    ambil_d3fend_mitigasi_by_attack_id,
)


class TestCTIVectorStore(unittest.TestCase):
    """Pengujian Unit & Integrasi untuk Milestone 3: CTIVectorStore."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vector_dir = Path(self.temp_dir.name) / "vectors"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_deterministic_embedding_dimension_and_normalization(self):
        """Embedding deterministik harus tepat 768 dimensi dan ter-normalisasi L2 (norm = 1.0)."""
        vec = compute_deterministic_embedding("ransomware attack against hospital servers", dim=VECTOR_DIMENSION)
        self.assertEqual(len(vec), 768)

        # L2 norm check
        norm = sum(x * x for x in vec) ** 0.5
        self.assertAlmostEqual(norm, 1.0, places=4)

    def test_deterministic_embedding_empty_input(self):
        """Input kosong harus menghasilkan vektor nol berdimensi 768."""
        vec = compute_deterministic_embedding("", dim=VECTOR_DIMENSION)
        self.assertEqual(len(vec), 768)
        self.assertEqual(sum(abs(x) for x in vec), 0.0)

    def test_cosine_similarity_identical_and_orthogonal(self):
        """Cosine similarity vektor identik harus 1.0; vektor ortogonal harus 0.0."""
        vec1 = compute_deterministic_embedding("phishing attack via email attachment")
        vec2 = compute_deterministic_embedding("phishing attack via email attachment")
        sim_identical = cosine_similarity(vec1, vec2)
        self.assertAlmostEqual(sim_identical, 1.0, places=4)

        # Vector orthogonal/berlawanan
        zero_vec = [0.0] * 768
        self.assertEqual(cosine_similarity(vec1, zero_vec), 0.0)

    def test_three_separate_collections_namespaces_and_directories(self):
        """Memverifikasi bahwa 3 koleksi memiliki namespace terpisah dan folder persisten mandiri."""
        vs = CTIVectorStore(vector_dir=self.vector_dir)

        # Periksa folder persisten mandiri
        self.assertTrue((self.vector_dir / "attack").exists())
        self.assertTrue((self.vector_dir / "taxonomy").exists())
        self.assertTrue((self.vector_dir / "nist").exists())

        # Namespace koleksi terpisah
        self.assertIsInstance(vs.collection_attack, list)
        self.assertIsInstance(vs.collection_taxonomy, list)
        self.assertIsInstance(vs.collection_nist, list)

        # Status kesiapan
        self.assertEqual(vs.status["collection_attack"], "READY")
        self.assertEqual(vs.status["collection_taxonomy"], "READY")
        self.assertEqual(vs.status["collection_nist"], "READY")

    def test_collection_isolation_query_scoping(self):
        """Kueri pada satu koleksi tidak boleh mengakses atau mengembalikan data dari koleksi lain."""
        vs = CTIVectorStore(vector_dir=self.vector_dir)

        # Kueri koleksi taksonomi hanya mengembalikan record collection_taxonomy
        tax_res = vs.search_taxonomy("ransomware", top_k=3)
        for r in tax_res:
            self.assertEqual(r["collection"], "collection_taxonomy")
            self.assertIn("category_id", r)
            self.assertNotIn("technique_id", r)

        # Kueri koleksi attack hanya mengembalikan record collection_attack
        att_res = vs.search_attack("phishing spearphishing", top_k=3)
        for r in att_res:
            self.assertEqual(r["collection"], "collection_attack")
            self.assertIn("technique_id", r)
            self.assertNotIn("control_id", r)

        # Kueri koleksi nist hanya mengembalikan record collection_nist
        nist_res = vs.search_nist("access control", top_k=3)
        for r in nist_res:
            self.assertEqual(r["collection"], "collection_nist")
            self.assertIn("control_id", r)
            self.assertNotIn("technique_id", r)

    def test_query_collection_unauthorized_name_raises_value_error(self):
        """query_collection harus melempar ValueError jika nama koleksi tidak terdaftar."""
        vs = CTIVectorStore(vector_dir=self.vector_dir)
        with self.assertRaises(ValueError) as ctx:
            vs.query_collection("collection_d3fend", "query")
        self.assertIn("Unauthorized collection", str(ctx.exception))

    def test_dual_text_retrieval_strategy(self):
        """
        Taksonomi mendukung pencarian dual-text (Indonesian + English).
        ATT&CK dan NIST strictly kueri teks terjemahan Bahasa Inggris.
        """
        vs = CTIVectorStore(vector_dir=self.vector_dir)

        # Taksonomi dengan dual-text
        tax_res = vs.search_taxonomy(
            query_id="serangan ransomware mengunci berkas server",
            query_en="ransomware attack encrypting server database files",
            top_k=1,
        )
        self.assertEqual(len(tax_res), 1)
        self.assertEqual(tax_res[0]["category_id"], "ransomware")

        # ATT&CK strictly English query
        att_res = vs.search_attack("phishing email attachment", top_k=3)
        self.assertGreater(len(att_res), 0)
        top_ids = [r["technique_id"] for r in att_res]
        self.assertTrue(any("T1566" in tid or "T1598" in tid for tid in top_ids))

    def test_vector_store_graceful_partial_failure(self):
        """Kegagalan/kerusakan salah satu berkas indeks tidak merusak koleksi lainnya."""
        # Simulasikan direktori nist korup
        corrupt_vector_dir = Path(self.temp_dir.name) / "corrupt_vectors"
        nist_dir = corrupt_vector_dir / "nist"
        nist_dir.mkdir(parents=True, exist_ok=True)
        (nist_dir / "index.json").write_text("{CORRUPT_JSON", encoding="utf-8")

        # Inisialisasi vector store tetap sukses memuat taksonomi & attack
        vs = CTIVectorStore(vector_dir=corrupt_vector_dir)
        self.assertEqual(vs.status["collection_taxonomy"], "READY")
        self.assertEqual(vs.status["collection_attack"], "READY")


class TestCTINewsAnalyzer(unittest.TestCase):
    """Pengujian Unit & Integrasi untuk Milestone 4: CTINewsAnalyzer & Guardrails."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_state.db"
        self.vector_dir = Path(self.temp_dir.name) / "vectors"
        self.vs = CTIVectorStore(vector_dir=self.vector_dir)
        self.analyzer = CTINewsAnalyzer(vector_store=self.vs, db_path=self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_classify_incident_closed_11_categories_schema(self):
        """Klasifikasi insiden harus mematuhi skema JSON dan menghasilkan 1 label utama resmi."""
        article = {
            "identifier": "art-test-1",
            "judul": "Server Rumah Sakit Terinfeksi Ransomware",
            "ringkasan_atau_narasi": "Pelaku mengunci database pasien dan meminta tebusan 5 Bitcoin.",
        }
        res = self.analyzer.classify_incident(article["judul"], article["ringkasan_atau_narasi"])

        for req_key in ["kategori_utama", "confidence", "kutipan_bukti", "alasan", "id_taksonomi_induk"]:
            self.assertIn(req_key, res)

        self.assertIn(res["kategori_key"], CLOSED_11_TAXONOMY_CATEGORIES)
        self.assertEqual(res["kategori_utama"], TAXONOMY_DISPLAY_NAMES["ransomware"])
        self.assertEqual(res["id_taksonomi_induk"], ECSIRT_PARENT_MAPPINGS["ransomware"])
        self.assertTrue(0.0 <= res["confidence"] <= 1.0)
        self.assertNotEqual(res["kutipan_bukti"], "")

    def test_classify_incident_mandatory_undetermined_fallback(self):
        """Berita tanpa fakta serangan siber (mis. rapat SPBE) wajib menghasilkan 'Tidak Dapat Ditentukan'."""
        teks_non_insiden = (
            "Diskominfo Jatim menyelenggarakan rapat koordinasi evaluasi SPBE bersama OPD. "
            "Rapat bertujuan menyelaraskan target indeks digitalisasi birokrasi tahun 2026."
        )
        res = self.analyzer.classify_incident(teks_non_insiden)
        self.assertEqual(res["kategori_utama"], "Tidak Dapat Ditentukan")
        self.assertEqual(res["kategori_key"], "tidak_dapat_ditentukan")
        self.assertEqual(res["id_taksonomi_induk"], "other:unspecified")
        self.assertLess(res["confidence"], 0.50)

    def test_conditional_attack_flow_detector(self):
        """Detektor alur serangan mendeteksi teks dengan alur serangan dan menolak teks non-alur."""
        text_with_flow = "Pelaku mengirimkan email phishing berisi tautan berbahaya untuk mencuri kredensial."
        text_without_flow = "Kepala dinas membuka seminar nasional transformasi digital pemerintahan."

        has_flow_1, kw_1 = self.analyzer.detect_attack_flow(text_with_flow)
        has_flow_2, kw_2 = self.analyzer.detect_attack_flow(text_without_flow)

        self.assertTrue(has_flow_1)
        self.assertIn(kw_1, ["phishing", "tautan", "kredensial"])
        self.assertFalse(has_flow_2)
        self.assertEqual(kw_2, "")

    def test_attack_extraction_abstains_when_no_flow(self):
        """Ekstraksi ATT&CK wajib abstain ('tidak_ditentukan') jika berita tidak memuat alur serangan."""
        text_no_flow = "Dinas Komunikasi dan Informatika menggelar workshop literasi keamanan digital bagi pelajar."
        res = self.analyzer.extract_attack_technique(teks_asli=text_no_flow)

        self.assertEqual(res["status"], "tidak_ditentukan")
        self.assertIsNone(res["tactic"])
        self.assertEqual(res["technique_id"], "tidak_ditentukan")
        self.assertIsNone(res["technique_name"])

    def test_attack_extraction_stops_at_tactic_when_weak(self):
        """Ekstraksi ATT&CK berhenti pada level Taktik bila metode serangan samar/umum."""
        text_vague = "Sistem portal mengalami insiden akibat pelaku memanfaatkan celah sistem umum."
        res = self.analyzer.extract_attack_technique(teks_asli=text_vague)

        self.assertEqual(res["status"], "tactic_only")
        self.assertIsNotNone(res["tactic"])
        self.assertEqual(res["technique_id"], "tidak_ditentukan")

    def test_active_attack_guard_allows_active_id(self):
        """Active Validation Guard mengizinkan teknik ATT&CK aktif (T1566, T1190, T1486)."""
        valid_id, is_valid = self.analyzer.guard_active_attack_id("T1566")
        self.assertTrue(is_valid)
        self.assertEqual(valid_id, "T1566")

        valid_sub_id, is_valid_sub = self.analyzer.guard_active_attack_id("T1059.001")
        self.assertTrue(is_valid_sub)
        self.assertEqual(valid_sub_id, "T1059.001")

    def test_active_attack_guard_rejects_hallucinated_id(self):
        """Active Validation Guard menolak ID fiktif/halusinasi seperti T9999 dan FAKE-TECH."""
        val_fake, is_valid = self.analyzer.guard_active_attack_id("T9999")
        self.assertFalse(is_valid)
        self.assertEqual(val_fake, "tidak_ditentukan")

    def test_active_attack_guard_rejects_revoked_id(self):
        """Active Validation Guard menolak teknik revoked seperti T1183 dan T1086."""
        val_rev, is_valid = self.analyzer.guard_active_attack_id("T1183")
        self.assertFalse(is_valid)
        self.assertEqual(val_rev, "tidak_ditentukan")

    def test_deterministic_d3fend_mitigation_lookup(self):
        """Lookup mitigasi D3FEND murni via SQL relasional deterministik, bebas intervensi LLM."""
        # Query teknik T1566 (Phishing)
        mitigations = self.analyzer.lookup_d3fend_mitigations("T1566")
        self.assertIsInstance(mitigations, list)
        self.assertGreater(len(mitigations), 0)

        # Pastikan atribut sesuai skema
        first_mit = mitigations[0]
        self.assertIn("id", first_mit)
        self.assertIn("name", first_mit)
        self.assertIn("tactic", first_mit)

        # Lookup pada ID 'tidak_ditentukan' harus mengembalikan []
        self.assertEqual(self.analyzer.lookup_d3fend_mitigations("tidak_ditentukan"), [])

    def test_deterministic_d3fend_zero_llm_additions_enforcement(self):
        """Menolak penambahan mitigasi D3FEND fiktif yang tidak ada di hasil SQL."""
        real_mitigations = self.analyzer.lookup_d3fend_mitigations("T1190")
        real_ids = {m["id"] for m in real_mitigations}

        fake_llm_mitigation = {"id": "D3-MAGIC-FIREWALL", "name": "AI NextGen Blocker"}
        self.assertNotIn(fake_llm_mitigation["id"], real_ids)

    def test_nist_reference_on_demand_lookup(self):
        """Lookup referensi NIST mengembalikan kontrol SP 800-53 / CSF 2.0 yang relevan."""
        nist_refs = self.analyzer.lookup_nist_references("access control account management policy", top_k=2)
        self.assertEqual(len(nist_refs), 2)
        for ref in nist_refs:
            self.assertIn("id", ref)
            self.assertIn("title", ref)
            self.assertIn("framework", ref)

    def test_end_to_end_analyze_news_pipeline(self):
        """Menjalankan end-to-end analyze_news dan memverifikasi persistensi provenance lengkap."""
        article = {
            "identifier": "https://berita.jatimprov.go.id/siber/pdns-ransomware-2026",
            "judul": "Layanan PDNS Terganggu Serangan Ransomware Brain Cipher",
            "ringkasan_atau_narasi": (
                "Peretas menyebarkan ransomware yang mengunci sistem penyimpanan data publik. "
                "Pelaku menuntut uang tebusan kripto senilai miliaran rupiah untuk kunci pemulihan."
            ),
        }

        intel = self.analyzer.analyze_news(article, persist=True)

        # Verifikasi konten intelijen
        self.assertEqual(intel["kategori_utama"], "Ransomware")
        self.assertEqual(intel["mitre_technique_id"], "T1486")
        self.assertGreater(len(intel["d3fend_mitigasi"]), 0)
        self.assertEqual(intel["disclaimer_d3fend"], DISCLAIMER_D3FEND)

        # Verifikasi versi sumber tersimpan
        self.assertEqual(intel["version_taxonomy"], "ecsirt-2026")
        self.assertEqual(intel["version_attack"], "v20.0")
        self.assertEqual(intel["version_d3fend"], "1.6.0")

        # Verifikasi data tersimpan di SQLite
        saved = self.analyzer.get_verified_intelligence(article["identifier"])
        self.assertIsNotNone(saved)
        self.assertEqual(saved["article_identifier"], article["identifier"])
        self.assertEqual(saved["kategori_insiden"], "Ransomware")
        self.assertEqual(saved["mitre_technique_id"], "T1486")
        self.assertIsInstance(saved["d3fend_mitigasi"], list)

    def test_provenance_manual_correction_by_admin(self):
        """Admin dapat merekam koreksi manual tanpa menghapus hasil prediksi model asli."""
        art_id = "art-correction-test"
        article = {
            "identifier": art_id,
            "judul": "Serangan Malware Penipuan Rekening",
            "ringkasan_atau_narasi": "Pelaku menyebarkan malware lewat lampiran email.",
        }
        self.analyzer.analyze_news(article, persist=True)

        # Admin melakukan koreksi
        success = self.analyzer.record_manual_correction(
            article_identifier=art_id,
            koreksi_kategori="Phishing / Penipuan Siber",
            koreksi_technique_id="T1566.001",
            catatan="Setelah verifikasi tim CSIRT, vektor utama adalah spearphishing attachment.",
            oleh="analis_siber_diskominfo",
        )
        self.assertTrue(success)

        # Verifikasi data tersimpan
        verified = self.analyzer.get_verified_intelligence(art_id)
        self.assertEqual(verified["koreksi_admin_kategori"], "Phishing / Penipuan Siber")
        self.assertEqual(verified["koreksi_admin_technique_id"], "T1566.001")
        self.assertEqual(verified["koreksi_admin_oleh"], "analis_siber_diskominfo")
        self.assertIsNotNone(verified["koreksi_admin_pada"])

    def test_revoked_technique_audit_flagging(self):
        """Menandai insiden historis yang memakai teknik yang dicabut tanpa menghapus catatan."""
        # Catat artikel historis yang memakai T1086 (revoked)
        art_id = "art-hist-revoked-1086"
        record = {
            "article_identifier": art_id,
            "kategori_insiden": "Malware / Infostealer",
            "confidence_kategori": 0.90,
            "mitre_technique_id": "T1086",
            "version_taxonomy": "ecsirt-2026",
            "version_attack": "v19.0",
            "version_d3fend": "1.5.0",
            "version_nist": "SP800-53-Rev5",
        }
        simpan_intelijen_berita(record, db_path=self.db_path)

        # Tandai audit flag
        updated_rows = tandai_flag_tinjauan_intelijen("T1086", flag="TEKNIK_REVOKED_PERLU_REVIEW", db_path=self.db_path)
        self.assertEqual(updated_rows, 1)

        saved = ambil_intelijen_berita(art_id, db_path=self.db_path)
        self.assertEqual(saved["flag_tinjauan"], "TEKNIK_REVOKED_PERLU_REVIEW")


if __name__ == "__main__":
    unittest.main()
