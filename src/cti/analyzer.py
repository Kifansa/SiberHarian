"""
SiberHarian CTI News Analyzer & Guardrails Engine (Milestone 4 / Tahap 4).

Mengimplementasikan alur pemrosesan per berita intelijen siber:
1. Klasifikasi Insiden: Retrieval taksonomi eCSIRT, pemilihan 1 label utama dari daftar 11 kategori tertutup.
   Fallback wajib ke 'Tidak Dapat Ditentukan' bila bukti lemah/nihil.
2. Ekstraksi MITRE ATT&CK Kondisional: Dijalankan HANYA jika berita mendeskripsikan alur/cara serangan.
   Dilarang menebak! Jika bukti lemah, berhenti pada tingkat Taktik atau 'tidak_ditentukan'.
3. Active ATT&CK Validation Guard: Menolak keras ID teknik yang halusinasi, revoked, atau tidak aktif.
4. Deterministic D3FEND Mitigation Lookup: Lookup murni dari tabel SQLite relasional, zero LLM additions.
5. Referensi NIST On-Demand: Retrieval kontrol NIST SP 800-53 Rev 5 & CSF 2.0.
6. Provenance & Manual Correction: Penyimpanan persisten ke tabel `intelijen_berita_tervalidasi` di `data/state.db`.
"""

import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

from src.utils.logger import setup_logger
from src.utils.llm_adapter import GeminiLLMAdapter
from src.storage.db import (
    DEFAULT_DB_PATH,
    init_db,
    ambil_d3fend_mitigasi_by_attack_id,
    simpan_intelijen_berita,
    ambil_intelijen_berita,
    simpan_koreksi_admin_intelijen,
    simpan_koreksi_admin_sektor,
)
from src.cti.preparer import (
    CLOSED_11_TAXONOMY_CATEGORIES,
    TAXONOMY_DISPLAY_NAMES,
    ECSIRT_PARENT_MAPPINGS,
    CLOSED_10_IIV_SECTORS,
    IIV_SECTOR_DISPLAY_NAMES,
    InvalidSectorError,
)
from src.cti.vector_store import CTIVectorStore

logger = setup_logger(__name__)

DISCLAIMER_D3FEND = "Saran mitigasi umum untuk teknik terkait, bukan temuan spesifik insiden"


# =============================================================================
# SEKTOR IIV RULES (Perpres 82/2022 Pasal 4)
# =============================================================================
SEKTOR_IIV_KEYWORDS: Dict[str, List[str]] = {
    "Administrasi Pemerintahan": [
        "pemerintah", "pemda", "polres", "polri", "kementerian", "dprd", "bpjs",
        "pemkot", "desa", "asn", "bkn", "opd", "kelurahan", "pemprov", "dukcapil",
        "dinas", "kpu", "kejaksaan", "mahkamah", "kemendagri", "kominfo", "diskominfo",
        "bkd", "setda", "bupati", "walikota", "gubernur", "kemensetneg",
    ],
    "Energi & Sumber Daya Mineral": [
        "energi", "minyak", "gas", "pln", "pertamina", "listrik", "solar",
        "petroleum", "batu bara", "nuklir", "power grid", "esdm", "pgn",
    ],
    "Transportasi": [
        "transportasi", "tanker", "kapal", "maritim", "pelabuhan", "bandara",
        "pesawat", "kai", "kereta", "coast guard", "navigasi", "kemenhub",
        "pt kai", "pelindo", "angkasa pura", "damri",
    ],
    "Keuangan & Perbankan": [
        "bank", "keuangan", "kripto", "dompet", "pajak", "transaksi", "visa",
        "biocatch", "ethereum", "finansial", "m-banking", "atm", "rekening",
        "ojk", "bank indonesia", "bca", "mandiri", "bri", "bni", "fintech",
    ],
    "Kesehatan": [
        "kesehatan", "rumah sakit", "rsud", "pasien", "medis", "bpjs kesehatan",
        "obat", "farmasi", "rekam medis", "kemenkes", "puskesmas", "dokter",
    ],
    "Teknologi Informasi & Komunikasi (TIK)": [
        "developer", "rust", "wordpress", "netscaler", "citrix", "vmware",
        "unix", "dns", "server", "jaringan", "cdn", "cloud", "telekomunikasi",
        "provider", "telkom", "indosat", "hosting", "datacenter", "xl axiata",
        "isp", "data center", "komputasi awan",
    ],
    "Pertahanan & Keamanan": [
        "militer", "tni", "pertahanan", "kemhan", "intelijen", "radar",
        "senjata", "keamanan nasional", "pentagon", "tni-ad", "tni-al", "tni-au",
        "bais", "alutsista",
    ],
    "Pangan": [
        "pangan", "pertanian", "bulog", "beras", "pupuk", "perkebunan",
        "pangan nasional", "sembako", "kementan", "irigasi", "panen",
    ],
    "Pendidikan": [
        "sekolah", "kampus", "universitas", "siswa", "mahasiswa", "guru",
        "dosen", "ppdb", "akademik", "unair", "ugm", "itb", "kemendikbud",
        "pesantren", "madrasah", "perguruan tinggi", "fakultas",
    ],
    "Layanan Publik & Pengguna Digital": [
        "whatsapp", "android", "kartu", "game", "warga", "pengguna",
        "masyarakat", "konsumen", "publik", "aplikasi seluler", "e-commerce",
        "layanan publik", "warga sipil",
    ],
}


def _normalize_whitespace(s: str) -> str:
    """Normalisasi spasi putih dan lowercase untuk pencocokan substring eksak."""
    if not s:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip().lower()


def guard_sector_and_quote(
    sektor: str,
    kutipan_bukti: str,
    teks_berita: str,
    confidence: float = 0.85,
) -> Tuple[str, str, float, bool]:
    """
    Guardrail validasi ketat untuk sektor target IIV dan kutipan bukti:
    1. Jika sektor == 'Tidak dapat ditentukan', kutipan dipaksa '', confidence 0.0, valid = True.
    2. Sektor HARUS berada dalam CLOSED_10_IIV_SECTORS.
    3. Jika sektor adalah salah satu dari 10 IIV aktif, kutipan_bukti HARUS non-kosong dan
       merupakan substring persis (case-insensitive, normalized whitespace) dari teks_berita.
    4. Jika melanggar (sektor di luar daftar ATAU kutipan bukan substring persis),
       REJEK KERAS dan fallback ke 'Tidak dapat ditentukan', quote '', confidence 0.0, valid = False.
    """
    # 1. Fallback sah
    clean_sektor = str(sektor or "").strip()
    if not clean_sektor or clean_sektor.lower() in (
        "tidak dapat ditentukan",
        "tidak_dapat_ditentukan",
        "tidak ditentukan",
        "none",
        "-",
    ):
        return "Tidak dapat ditentukan", "", 0.0, True

    # Cek canonical sector
    matched_canonical = None
    for s_canon in CLOSED_10_IIV_SECTORS:
        if clean_sektor.lower() == s_canon.lower():
            matched_canonical = s_canon
            break

    # 2. Tolak keras jika di luar CLOSED_10_IIV_SECTORS
    if not matched_canonical or matched_canonical not in CLOSED_10_IIV_SECTORS:
        logger.warning(f"Guard Sector REJECT: Sektor '{clean_sektor}' di luar CLOSED_10_IIV_SECTORS.")
        return "Tidak dapat ditentukan", "", 0.0, False

    if matched_canonical == "Tidak dapat ditentukan":
        return "Tidak dapat ditentukan", "", 0.0, True

    # 3. Validasi kutipan bukti
    clean_quote = str(kutipan_bukti or "").strip()
    if not clean_quote or not teks_berita or not str(teks_berita).strip():
        logger.warning(f"Guard Sector REJECT: Kutipan bukti kosong untuk sektor '{matched_canonical}'.")
        return "Tidak dapat ditentukan", "", 0.0, False

    norm_quote = _normalize_whitespace(clean_quote)
    norm_text = _normalize_whitespace(teks_berita)

    if norm_quote not in norm_text:
        logger.warning(
            f"Guard Sector REJECT: Kutipan bukti '{clean_quote}' BUKAN substring dari teks berita."
        )
        return "Tidak dapat ditentukan", "", 0.0, False

    # Berhasil tervalidasi
    valid_conf = float(confidence) if (confidence is not None and confidence > 0.0) else 0.85
    return matched_canonical, clean_quote, valid_conf, True


class CTINewsAnalyzer:
    """
    Engine Analisis Berita CTI & Guardrails Tervalidasi.
    """

    def __init__(
        self,
        vector_store: Optional[CTIVectorStore] = None,
        db_path: Path = DEFAULT_DB_PATH,
        prepared_dir: Optional[Path] = None,
        llm_mode: str = "auto",  # 'auto', 'gemini', 'offline'
    ):
        self.db_path = Path(db_path)
        init_db(self.db_path)

        self.vector_store = vector_store or CTIVectorStore(prepared_dir=prepared_dir)
        self.prepared_dir = (
            Path(prepared_dir) if prepared_dir else self.vector_store.prepared_dir
        )
        self.llm_mode = llm_mode
        self._gemini_chat_available: Optional[bool] = None

        # Muat daftar teknik ATT&CK aktif (706 teknik aktif dari data/prepared/attack_techniques.json)
        self.active_attack_techniques: Dict[str, Dict[str, Any]] = {}
        self._load_active_attack_techniques()

        # Versi standar sumber data
        self.version_info = {
            "taxonomy": "ecsirt-2026",
            "attack": "v20.0",
            "d3fend": "1.6.0",
            "nist": "SP800-53-Rev5",
        }

    def _is_gemini_active(self) -> bool:
        """Mengecek apakah Gemini LLM chat aktif atau sedang di-mock dalam testing."""
        if self.llm_mode == "offline":
            return False
        if self.llm_mode == "gemini":
            return True

        from unittest.mock import Mock
        if isinstance(getattr(GeminiLLMAdapter, "chat", None), Mock):
            return True

        if self._gemini_chat_available is not None:
            return self._gemini_chat_available

        try:
            from src.utils.settings_manager import SettingsManager
            cfg = SettingsManager.get_gemini_config()
            raw_key = cfg.get("api_key", "") or os.environ.get("GEMINI_API_KEY", "")
            if not raw_key or not str(raw_key).startswith("AIza"):
                self._gemini_chat_available = False
                return False

            self._gemini_chat_available = True
        except Exception:
            self._gemini_chat_available = False

        return bool(self._gemini_chat_available)

    def _load_active_attack_techniques(self) -> None:
        """Memuat kamus teknik ATT&CK aktif yang valid untuk active validation guard."""
        attack_file = self.prepared_dir / "attack_techniques.json"
        if attack_file.exists():
            try:
                data = json.loads(attack_file.read_text(encoding="utf-8"))
                for t in data:
                    tid = t.get("technique_id")
                    if tid and not t.get("revoked", False) and not t.get("deprecated", False):
                        self.active_attack_techniques[tid] = t
                logger.info(f"Loaded {len(self.active_attack_techniques)} active ATT&CK techniques for validation.")
            except Exception as e:
                logger.error(f"Gagal memuat attack_techniques.json: {e}")

        # Fallback baseline active techniques jika berkas belum ada
        if not self.active_attack_techniques:
            baseline_ids = [
                "T1566", "T1566.001", "T1566.002", "T1190", "T1486", "T1059.001",
                "T1078", "T1505.003", "T1003", "T1498", "T1053.005", "T1055.011"
            ]
            for bid in baseline_ids:
                self.active_attack_techniques[bid] = {"technique_id": bid, "name": bid}

    # =========================================================================
    # GUARDRAILS & DETECTORS
    # =========================================================================

    def detect_attack_flow(self, text: str) -> Tuple[bool, str]:
        """
        Mengecek apakah teks berita mendeskripsikan alur/cara serangan (attack flow).
        Mengembalikan (has_flow: bool, keyword_or_phrase: str).
        Jika berita hanya memuat rapat, regulasi, atau tidak memuat alur serangan, return False.
        """
        if not text or not str(text).strip():
            return False, ""

        clean = str(text).lower()

        # Deteksi teks rapat / koordinasi / regulasi murni tanpa insiden
        non_incident_signals = [
            "rapat koordinasi", "evaluasi spbe", "sosialisasi perda", "seminar nasional",
            "workshop spbe", "digitalisasi birokrasi", "audiensi", "penandatanganan mou"
        ]
        has_incident_core = any(ic in clean for ic in [
            "serangan", "peretas", "korban", "diretas", "hacked", "breach", "ransomware", "malware", "phishing"
        ])
        if any(nis in clean for nis in non_incident_signals) and not has_incident_core:
            return False, ""

        # Pola kata kunci alur/cara serangan siber
        attack_flow_keywords = [
            "phishing", "spearphishing", "lampiran", "attachment", "email penipuan", "email palsu",
            "ransomware", "enkripsi file", "enkripsi", "terkunci", "uang tebusan", "pemulihan file",
            "malware", "trojan", "infostealer", "spyware", "backdoor", "apk palsu",
            "eksploitasi", "kerentanan", "vulnerability", "cve-", "remote code execution", "rce",
            "celah sistem", "celah keamanan", "celah", "peretasan",
            "sql injection", "sqli", "cross-site scripting", "xss", "web shell", "webshell",
            "brute force", "credential dumping", "pencurian kredensial", "bypass authentication",
            "ddos", "denial of service", "syn flood", "dns amplification",
            "defacement", "peretasan web", "judi slot", "slot gacor",
            "zero-day", "0-day", "privilege escalation", "lateral movement",
            "powershell", "reverse shell", "script execution"
        ]

        # Deteksi dengan word boundary untuk kata kunci pendek (<= 4 huruf)
        for kw in attack_flow_keywords:
            if len(kw) <= 4:
                if re.search(r'\b' + re.escape(kw) + r'\b', clean):
                    return True, kw
            else:
                if kw in clean:
                    return True, kw

        return False, ""

    def guard_active_attack_id(self, technique_id: Optional[str]) -> Tuple[str, bool]:
        """
        Active ATT&CK Validation Guard:
        Memverifikasi bahwa technique_id ada pada set ATT&CK Enterprise aktif.
        Jika fiktif, halusinasi (mis. T9999), atau revoked (mis. T1183, T1086):
        Tolak, catat log audit peringatan, dan fallback ke 'tidak_ditentukan'.
        """
        if not technique_id or str(technique_id).strip().lower() in ["", "none", "null", "tidak_ditentukan"]:
            return "tidak_ditentukan", False

        clean_id = str(technique_id).strip()

        if clean_id in self.active_attack_techniques:
            return clean_id, True

        # Rejection & Audit Logging
        logger.warning(
            f"Active ATT&CK Guard REJECTION: ID Teknik '{technique_id}' ditolak karena tidak ada dalam "
            f"katalog ATT&CK aktif ({len(self.active_attack_techniques)} teknik aktif)."
        )
        return "tidak_ditentukan", False

    def validate_category(self, category_str: str) -> str:
        """
        Memastikan kategori klasifikasi termasuk dalam 11 kategori tertutup resmi.
        Jika tidak dikenal, fallback ke 'tidak_dapat_ditentukan'.
        """
        if not category_str:
            return "tidak_dapat_ditentukan"

        clean = str(category_str).strip().lower().replace(" ", "_").replace("-", "_")
        for valid_key in CLOSED_11_TAXONOMY_CATEGORIES:
            if clean == valid_key or valid_key in clean:
                return valid_key

        # Check by display name
        for key, display in TAXONOMY_DISPLAY_NAMES.items():
            if str(category_str).strip().lower() == display.lower():
                return key

        return "tidak_dapat_ditentukan"

    def guard_sector_and_quote(
        self,
        sektor: str,
        kutipan_bukti: str,
        teks_berita: str,
        confidence: float = 0.85,
    ) -> Tuple[str, str, float, bool]:
        """Metode pembungkus untuk guardrail sektor target IIV & kutipan bukti."""
        return guard_sector_and_quote(sektor, kutipan_bukti, teks_berita, confidence=confidence)

    # =========================================================================
    # CORE PROCESSING STEPS
    # =========================================================================

    def classify_incident(
        self,
        teks_asli: str,
        teks_terjemahan: Optional[str] = None,
        top_candidates: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Tahap 4 Langkah 1: Klasifikasi Insiden ke SATU label utama dari daftar 11 kategori tertutup.
        Output structured JSON: kategori_utama, confidence, kutipan_bukti, alasan, id_taksonomi_induk.
        """
        full_text = f"{teks_asli} {teks_terjemahan or ''}".strip()
        if not full_text:
            return {
                "kategori_utama": TAXONOMY_DISPLAY_NAMES["tidak_dapat_ditentukan"],
                "kategori_key": "tidak_dapat_ditentukan",
                "kategori_tambahan": None,
                "confidence": 0.0,
                "kutipan_bukti": "",
                "alasan": "Teks artikel kosong.",
                "id_taksonomi_induk": ECSIRT_PARENT_MAPPINGS["tidak_dapat_ditentukan"],
            }

        # 1. Retrieval kandidat taksonomi dari vector store
        candidates = top_candidates or self.vector_store.search_taxonomy(
            query_id=teks_asli[:1000],
            query_en=(teks_terjemahan or "")[:1000],
            top_k=3,
        )

        # 2. Coba klasifikasi via Gemini LLM jika tersedia
        llm_classified = None
        has_flow, _ = self.detect_attack_flow(full_text)

        if self._is_gemini_active():
            # Strict prompt untuk LLM
            system_prompt = (
                "You are an authoritative CTI Classifier for CSIRT Diskominfo Jawa Timur.\n"
                "Classify the news incident into EXACTLY ONE primary category from this CLOSED 11 list:\n"
                "- ransomware\n"
                "- data_breach\n"
                "- ddos\n"
                "- defacement\n"
                "- phishing_penipuan\n"
                "- malware\n"
                "- eksploitasi_kerentanan\n"
                "- akses_tidak_sah\n"
                "- pelecehan_konten\n"
                "- lainnya\n"
                "- tidak_dapat_ditentukan\n\n"
                "MANDATORY RULES:\n"
                "1. Output MUST be valid JSON with keys: kategori_utama, confidence, kutipan_bukti, alasan, id_taksonomi_induk.\n"
                "2. If evidence of a cyber incident is weak, absent, or merely government coordination/regulation, you MUST select 'tidak_dapat_ditentukan'.\n"
                "3. Confidence MUST be a float between 0.0 and 1.0."
            )

            user_prompt = (
                f"Berita:\n{teks_asli[:1500]}\n\n"
                f"Kandidat Taksonomi Relevan:\n"
                + "\n".join(f"- {c['name']} (ID: {c['category_id']}): {c.get('definition', '')[:100]}" for c in candidates)
            )

            try:
                raw_response = GeminiLLMAdapter.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.1,
                )
                if raw_response:
                    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        cat_key = self.validate_category(parsed.get("kategori_utama", ""))
                        llm_classified = {
                            "kategori_utama": TAXONOMY_DISPLAY_NAMES.get(cat_key, "Tidak Dapat Ditentukan"),
                            "kategori_key": cat_key,
                            "kategori_tambahan": parsed.get("kategori_tambahan"),
                            "confidence": float(min(max(parsed.get("confidence", 0.5), 0.0), 1.0)),
                            "kutipan_bukti": str(parsed.get("kutipan_bukti", "")),
                            "alasan": str(parsed.get("alasan", "")),
                            "id_taksonomi_induk": ECSIRT_PARENT_MAPPINGS.get(cat_key, "other:unspecified"),
                        }
            except Exception as e:
                logger.debug(f"LLM Classification fallback: {e}")

        if llm_classified:
            return llm_classified

        # 3. Fallback Heuristik Tervalidasi (Deterministic Semantic Classifier)
        clean = full_text.lower()
        has_incident_core = any(ic in clean for ic in [
            "serangan", "peretas", "korban", "diretas", "hacked", "breach",
            "ransomware", "malware", "phishing", "kebocoran", "enkripsi",
            "tebusan", "defacement", "judi slot", "gangguan", "ddos"
        ])
        if not has_flow and not has_incident_core:
            return {
                "kategori_utama": TAXONOMY_DISPLAY_NAMES["tidak_dapat_ditentukan"],
                "kategori_key": "tidak_dapat_ditentukan",
                "kategori_tambahan": None,
                "confidence": 0.25,
                "kutipan_bukti": "",
                "alasan": "Tidak ada bukti serangan siber dalam artikel.",
                "id_taksonomi_induk": ECSIRT_PARENT_MAPPINGS["tidak_dapat_ditentukan"],
            }

        if candidates:
            best_cat = candidates[0]
            cat_key = self.validate_category(best_cat.get("category_id", ""))
            score = float(best_cat.get("score", 0.75))
            score = min(max(score, 0.40), 0.95)

            # Ekstrak kutipan kalimat bukti sederhana dari teks asli
            quote = ""
            for sentence in re.split(r'[.\n]', teks_asli):
                s_clean = sentence.strip()
                if len(s_clean) > 15 and any(w in s_clean.lower() for w in [cat_key.replace('_', ' '), "serangan", "peretas", "korban", "sistem"]):
                    quote = s_clean
                    break
            if not quote and teks_asli:
                quote = teks_asli.strip()[:100]

            return {
                "kategori_utama": TAXONOMY_DISPLAY_NAMES.get(cat_key, "Tidak Dapat Ditentukan"),
                "kategori_key": cat_key,
                "kategori_tambahan": None,
                "confidence": round(score, 2),
                "kutipan_bukti": quote,
                "alasan": f"Ditemukan indikasi kuat sesuai taksonomi {TAXONOMY_DISPLAY_NAMES.get(cat_key)}.",
                "id_taksonomi_induk": ECSIRT_PARENT_MAPPINGS.get(cat_key, "other:unspecified"),
            }

        return {
            "kategori_utama": TAXONOMY_DISPLAY_NAMES["tidak_dapat_ditentukan"],
            "kategori_key": "tidak_dapat_ditentukan",
            "kategori_tambahan": None,
            "confidence": 0.30,
            "kutipan_bukti": "",
            "alasan": "Tidak ada kandidat taksonomi yang cocok.",
            "id_taksonomi_induk": ECSIRT_PARENT_MAPPINGS["tidak_dapat_ditentukan"],
        }

    def extract_attack_technique(
        self,
        teks_asli: str,
        teks_terjemahan: Optional[str] = None,
        top_k: int = 15,
    ) -> Dict[str, Any]:
        """
        Tahap 4 Langkah 2: Ekstraksi teknik ATT&CK secara kondisional.
        - Dijalankan HANYA jika berita mendeskripsikan alur/cara serangan.
        - Jika bukti nihil: return {"status": "tidak_ditentukan", ...}. Dilarang menebak!
        - Jika bukti lemah: berhenti di tactic level.
        - Dilindungi oleh Active ATT&CK Validation Guard.
        """
        full_text = f"{teks_asli} {teks_terjemahan or ''}".strip()
        has_flow, evidence_term = self.detect_attack_flow(full_text)

        # Gate Kondisi: Jika TIDAK ADA alur serangan, abstain langsung!
        if not has_flow:
            return {
                "status": "tidak_ditentukan",
                "tactic": None,
                "technique_id": "tidak_ditentukan",
                "technique_name": None,
                "confidence": 0.0,
                "kutipan_bukti": "",
            }

        # Retrieval top-15 kandidat ATT&CK dari vector store strictly query teks Bahasa Inggris
        query_en = teks_terjemahan or teks_asli
        candidates = self.vector_store.search_attack(query_en=query_en[:1500], top_k=top_k)

        if not candidates:
            return {
                "status": "tidak_ditentukan",
                "tactic": None,
                "technique_id": "tidak_ditentukan",
                "technique_name": None,
                "confidence": 0.0,
                "kutipan_bukti": "",
            }

        # Coba ekstraksi via LLM
        extracted = None
        if self._is_gemini_active():
            system_prompt = (
                "You are a Senior Threat Intelligence Analyst for CSIRT Diskominfo Jatim.\n"
                "Analyze the news article and determine the MITRE ATT&CK technique used by the attacker.\n"
                "CRITICAL RULES:\n"
                "1. ONLY select a technique if the article provides explicit evidence of the attack flow/method.\n"
                "2. If evidence is vague/weak, output tactic level only and set technique_id to 'tidak_ditentukan'.\n"
                "3. DO NOT GUESS.\n"
                "4. Output JSON: {'technique_id': str, 'tactic': str, 'technique_name': str, 'confidence': float, 'kutipan_bukti': str}"
            )
            user_prompt = (
                f"Teks Berita (English translation):\n{query_en[:1500]}\n\n"
                f"Kandidat Top ATT&CK:\n"
                + "\n".join(f"- {c['technique_id']}: {c['name']} (Tactics: {c['tactics']})" for c in candidates[:10])
            )

            try:
                raw_response = GeminiLLMAdapter.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.1,
                )
                if raw_response:
                    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                    if match:
                        parsed = json.loads(match.group(0))
                        raw_id = parsed.get("technique_id")
                        val_id, is_valid = self.guard_active_attack_id(raw_id)
                        tech_meta = self.active_attack_techniques.get(val_id, {})
                        extracted = {
                            "status": "technique_extracted" if is_valid else "tactic_only",
                            "tactic": parsed.get("tactic") or (tech_meta.get("tactics", [None])[0] if tech_meta else None),
                            "technique_id": val_id,
                            "technique_name": tech_meta.get("name") or parsed.get("technique_name"),
                            "confidence": float(min(max(parsed.get("confidence", 0.5), 0.0), 1.0)),
                            "kutipan_bukti": str(parsed.get("kutipan_bukti", "")),
                        }
            except Exception as e:
                logger.debug(f"LLM ATT&CK extraction fallback: {e}")

        if extracted:
            return extracted

        # Fallback Heuristik Tervalidasi
        clean_text = full_text.lower()
        selected_id = None
        selected_tactic = "Initial Access"
        is_vague = False

        # Cek apakah bukti spesifik atau sekadar metode umum/samar
        vague_phrases = ["celah sistem", "alur tidak diketahui", "metode umum", "celah keamanan umum"]
        if any(vp in clean_text for vp in vague_phrases) and not any(kw in clean_text for kw in ["phishing", "ransomware", "enkripsi", "powershell", "webshell", "cve-", "sql injection"]):
            is_vague = True

        # Petakan indikator spesifik bila ada
        if not is_vague:
            if "ransomware" in clean_text or "enkripsi" in clean_text or "tebusan" in clean_text:
                selected_id = "T1486"
                selected_tactic = "Impact"
            elif "phishing" in clean_text or "lampiran" in clean_text or "email palsu" in clean_text:
                if "lampiran" in clean_text or "attachment" in clean_text:
                    selected_id = "T1566.001"
                elif "link" in clean_text or "tautan" in clean_text:
                    selected_id = "T1566.002"
                else:
                    selected_id = "T1566"
                selected_tactic = "Initial Access"
            elif "cve-" in clean_text or "remote code execution" in clean_text or "rce" in clean_text or "eksploitasi" in clean_text:
                selected_id = "T1190"
                selected_tactic = "Initial Access"
            elif "powershell" in clean_text:
                selected_id = "T1059.001"
                selected_tactic = "Execution"
            elif "web shell" in clean_text or "webshell" in clean_text:
                selected_id = "T1505.003"
                selected_tactic = "Persistence"
            elif "ddos" in clean_text or "syn flood" in clean_text or "gangguan ketersediaan" in clean_text:
                selected_id = "T1498"
                selected_tactic = "Impact"
            elif "credential" in clean_text or "kata sandi" in clean_text:
                selected_id = "T1003"
                selected_tactic = "Credential Access"

        # Jika tidak ada pola spesifik atau samar, ambil kandidat teratas dari pencarian vektor
        if not selected_id and not is_vague and candidates:
            top_cand = candidates[0]
            if top_cand.get("score", 0.0) >= 0.12:
                selected_id = top_cand.get("technique_id")
                t_list = top_cand.get("tactics", ["Initial Access"])
                selected_tactic = t_list[0] if isinstance(t_list, list) and t_list else "Initial Access"

        # Jika bukti samar/lemah: berhenti pada tingkat Tactic
        if is_vague or not selected_id:
            top_tactic = "Initial Access"
            if candidates:
                t_list = candidates[0].get("tactics", ["Initial Access"])
                top_tactic = t_list[0] if isinstance(t_list, list) and t_list else "Initial Access"
            return {
                "status": "tactic_only",
                "tactic": top_tactic,
                "technique_id": "tidak_ditentukan",
                "technique_name": None,
                "confidence": 0.40,
                "kutipan_bukti": f"Penyebutan alur serangan bersifat umum ({evidence_term}), tidak cukup spesifik untuk menentukan ID teknik.",
            }

        # Validasi ID lewat Active Guard
        val_id, is_valid = self.guard_active_attack_id(selected_id)
        tech_meta = self.active_attack_techniques.get(val_id, {})

        # Cari kutipan kalimat bukti
        quote = ""
        for sentence in re.split(r'[.\n]', teks_asli):
            if evidence_term in sentence.lower():
                quote = sentence.strip()
                break
        if not quote:
            quote = f"Terdapat bukti alur serangan terkait {evidence_term}."

        return {
            "status": "technique_extracted" if is_valid else "tactic_only",
            "tactic": selected_tactic,
            "technique_id": val_id,
            "technique_name": tech_meta.get("name") if is_valid else None,
            "confidence": 0.85 if is_valid else 0.40,
            "kutipan_bukti": quote,
        }

    def classify_sector(self, article: Union[Dict[str, Any], str]) -> Dict[str, Any]:
        """
        Tahap 4 & R4: Klasifikasi Sektor Korban (10 Sektor IIV Perpres 82/2022 Pasal 4).
        Memakai LLM jika online, atau deterministic keyword matching jika offline/fallback.
        Semua hasil WAJIB melewati guard_sector_and_quote.
        """
        if isinstance(article, str):
            teks_berita = article
            judul = ""
            ringkasan = ""
        else:
            judul = str(article.get("judul") or "")
            ringkasan = str(
                article.get("ringkasan_atau_narasi")
                or article.get("ringkasan")
                or article.get("konten")
                or ""
            )
            teks_berita = str(article.get("teks_asli") or f"{judul}. {ringkasan}".strip())

        if not teks_berita.strip():
            return {
                "sektor": "Tidak dapat ditentukan",
                "sektor_target": "Tidak dapat ditentukan",
                "confidence": 0.0,
                "confidence_sektor": 0.0,
                "kutipan_bukti": "",
                "kutipan_bukti_sektor": "",
                "alasan": "Teks berita kosong.",
                "alasan_sektor": "Teks berita kosong.",
                "is_valid": True,
            }

        # 1. Coba via LLM jika Gemini aktif
        if self._is_gemini_active():
            try:
                system_prompt = (
                    "You are an authoritative CTI Sector Analyst for CSIRT Diskominfo Jawa Timur.\n"
                    "Classify the victim sector of the cyber incident into EXACTLY ONE sector from the 10 Critical Information Infrastructure (IIV) sectors under Perpres 82/2022 Pasal 4:\n"
                    "1. Administrasi Pemerintahan\n"
                    "2. Energi & Sumber Daya Mineral\n"
                    "3. Transportasi\n"
                    "4. Keuangan & Perbankan\n"
                    "5. Kesehatan\n"
                    "6. Teknologi Informasi & Komunikasi (TIK)\n"
                    "7. Pertahanan & Keamanan\n"
                    "8. Pangan\n"
                    "9. Pendidikan\n"
                    "10. Layanan Publik & Pengguna Digital\n"
                    "11. Tidak dapat ditentukan\n\n"
                    "STRICT REQUIREMENTS:\n"
                    "1. 'kutipan_bukti' MUST be an EXACT VERBATIM SUBSTRING from the news text proving the victim/target.\n"
                    "2. If no explicit victim/target organization is mentioned, choose 'Tidak dapat ditentukan' and kutipan_bukti: \"\".\n"
                    "3. 'sektor' MUST be chosen strictly from the 11 list above.\n"
                    "Return ONLY a JSON object: {\"sektor\": \"...\", \"kutipan_bukti\": \"...\", \"confidence\": 0.85, \"alasan\": \"...\"}"
                )
                user_prompt = f"Judul: {judul}\n\nTeks Berita:\n{teks_berita[:2000]}"
                raw_response = GeminiLLMAdapter.chat(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    temperature=0.1,
                )
                if raw_response:
                    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
                    if match:
                        data = json.loads(match.group(0))
                        cand_sektor = data.get("sektor")
                        cand_quote = data.get("kutipan_bukti", "")
                        cand_conf = float(data.get("confidence", 0.85))
                        cand_alasan = data.get("alasan", "")

                        val_sektor, val_quote, val_conf, is_valid = guard_sector_and_quote(
                            cand_sektor, cand_quote, teks_berita, confidence=cand_conf
                        )
                        if is_valid:
                            return {
                                "sektor": val_sektor,
                                "sektor_target": val_sektor,
                                "confidence": val_conf,
                                "confidence_sektor": val_conf,
                                "kutipan_bukti": val_quote,
                                "kutipan_bukti_sektor": val_quote,
                                "alasan": cand_alasan or f"Terklasifikasi sektor {val_sektor} dengan bukti kutipan.",
                                "alasan_sektor": cand_alasan or f"Terklasifikasi sektor {val_sektor} dengan bukti kutipan.",
                                "is_valid": True,
                            }
                        else:
                            logger.warning(
                                f"LLM sector prediction rejected by guard: {cand_sektor}. Falling back to deterministic matching."
                            )
            except Exception as e:
                logger.debug(f"LLM sector classification error: {e}. Falling back to deterministic matching.")

        # 2. Deterministic / Offline Keyword Matching Fallback
        return self._classify_sector_deterministic(teks_berita)

    def _classify_sector_deterministic(self, teks_berita: str) -> Dict[str, Any]:
        """
        Klasifikasi sektor deterministik/offline berdasarkan keyword matching
        dan pengekstrakan kalimat kutipan eksak langsung dari irisan teks berita.
        """
        lower_text = teks_berita.lower()

        # Deteksi konteks insiden/gangguan siber nyata (bukan sekadar seremonial/gowes)
        incident_signals = [
            "serangan", "peretas", "korban", "diretas", "hacked", "hacker", "breach",
            "ransomware", "malware", "phishing", "kebocoran", "gangguan", "sistem",
            "data", "server", "keamanan", "cyber", "siber", "insiden", "kejahatan",
            "penipuan", "tumbang", "down", "kebobolan", "cve", "kerentanan", "virus",
            "trojan", "ddos", "defacement", "rekening", "apk", "kompromi", "akses",
            "spbe", "jaringan", "bocor", "pencurian", "eksploitasi", "injeksi",
            "pembobolan", "kelumpuhan", "lumpuh", "kebocoran data",
        ]
        has_incident_context = any(s in lower_text for s in incident_signals)
        if not has_incident_context:
            val_sektor, val_quote, val_conf, is_valid = guard_sector_and_quote(
                "Tidak dapat ditentukan", "", teks_berita, confidence=0.0
            )
            return {
                "sektor": val_sektor,
                "sektor_target": val_sektor,
                "confidence": val_conf,
                "confidence_sektor": val_conf,
                "kutipan_bukti": val_quote,
                "kutipan_bukti_sektor": val_quote,
                "alasan": "Berita tidak memuat konteks insiden atau gangguan keamanan siber.",
                "alasan_sektor": "Berita tidak memuat konteks insiden atau gangguan keamanan siber.",
                "is_valid": is_valid,
            }

        best_sector = "Tidak dapat ditentukan"
        best_score = 0
        best_pos = len(teks_berita)
        best_kw = ""

        # Hitung skor kemunculan kata kunci per sektor
        for sector_name, keywords in SEKTOR_IIV_KEYWORDS.items():
            score = 0
            earliest_pos = len(teks_berita)
            first_kw = ""
            for kw in keywords:
                # Cari kata/frasa
                pattern = r"\b" + re.escape(kw.lower()) + r"\b"
                match = re.search(pattern, lower_text)
                if match:
                    score += 1
                    pos = match.start()
                    if pos < earliest_pos:
                        earliest_pos = pos
                        first_kw = kw

            if score > best_score or (score == best_score and score > 0 and earliest_pos < best_pos):
                best_score = score
                best_pos = earliest_pos
                best_kw = first_kw
                best_sector = sector_name

        if best_score > 0 and best_pos < len(teks_berita):
            # Ekstrak kalimat utuh di sekitar best_pos sebagai kutipan eksak
            delimiters_back = [". ", ".\n", "! ", "!\n", "? ", "?\n", "\n\n", "\n"]
            start = 0
            for d in delimiters_back:
                idx = teks_berita.rfind(d, 0, best_pos)
                if idx != -1:
                    start = max(start, idx + len(d))

            end = len(teks_berita)
            for d in [". ", ".\n", "!\n", "! ", "?\n", "? ", "\n"]:
                idx = teks_berita.find(d, best_pos)
                if idx != -1:
                    end = min(end, idx + (1 if d.startswith(".") else len(d)))
            if end == len(teks_berita):
                for p in [".", "!", "?"]:
                    idx = teks_berita.find(p, best_pos)
                    if idx != -1:
                        end = min(end, idx + 1)

            exact_quote = teks_berita[start:end].strip(" \t\n\r.")
            if not exact_quote:
                exact_quote = teks_berita[best_pos:min(len(teks_berita), best_pos + len(best_kw))].strip(" \t\n\r.")

            calc_conf = round(min(0.70 + 0.05 * best_score, 0.95), 2)
            val_sektor, val_quote, val_conf, is_valid = guard_sector_and_quote(
                best_sector, exact_quote, teks_berita, confidence=calc_conf
            )
            alasan = f"Terdeteksi kata kunci sektor '{best_kw}' dalam bukti kutipan berita."
            return {
                "sektor": val_sektor,
                "sektor_target": val_sektor,
                "confidence": val_conf,
                "confidence_sektor": val_conf,
                "kutipan_bukti": val_quote,
                "kutipan_bukti_sektor": val_quote,
                "alasan": alasan,
                "alasan_sektor": alasan,
                "is_valid": is_valid,
            }

        # Fallback jika tidak ada kata kunci sektor yang cocok
        val_sektor, val_quote, val_conf, is_valid = guard_sector_and_quote(
            "Tidak dapat ditentukan", "", teks_berita, confidence=0.0
        )
        alasan = "Tidak ditemukan indikasi eksplisit sektor korban IIV dalam teks berita."
        return {
            "sektor": val_sektor,
            "sektor_target": val_sektor,
            "confidence": val_conf,
            "confidence_sektor": val_conf,
            "kutipan_bukti": val_quote,
            "kutipan_bukti_sektor": val_quote,
            "alasan": alasan,
            "alasan_sektor": alasan,
            "is_valid": is_valid,
        }

    def lookup_d3fend_mitigations(self, attack_technique_id: Optional[str]) -> List[Dict[str, Any]]:
        """
        Tahap 4 Langkah 4: Lookup deterministik mitigasi D3FEND via SQL murni.
        STRICT GUARD: LLM dilarang menambah atau memodifikasi hasil mitigasi.
        """
        if not attack_technique_id or attack_technique_id == "tidak_ditentukan":
            return []

        rows = ambil_d3fend_mitigasi_by_attack_id(attack_technique_id, db_path=self.db_path)
        if not rows and self.db_path != DEFAULT_DB_PATH and DEFAULT_DB_PATH.exists():
            rows = ambil_d3fend_mitigasi_by_attack_id(attack_technique_id, db_path=DEFAULT_DB_PATH)

        mitigations = []
        for r in rows:
            mitigations.append({
                "id": r.get("technique_id"),
                "name": r.get("name"),
                "tactic": r.get("tactic"),
                "definition": r.get("definition"),
            })
        return mitigations

    def lookup_nist_references(self, query_en: str, top_k: int = 2) -> List[Dict[str, Any]]:
        """
        Tahap 4 Langkah 5: Retrieval kontrol NIST SP 800-53 Rev 5 & CSF 2.0 on-demand.
        """
        if not self.vector_store or not query_en:
            return []

        controls = self.vector_store.search_nist(query_en=query_en, top_k=top_k)
        results = []
        for c in controls:
            results.append({
                "id": c.get("control_id"),
                "title": c.get("title"),
                "framework": c.get("framework"),
                "statement": (c.get("statement") or "")[:350],
            })
        return results

    # =========================================================================
    # END-TO-END PIPELINE & PERSISTENCE
    # =========================================================================

    def translate_to_technical_english(self, teks_asli: str) -> str:
        """
        Membangkitkan ringkasan fakta teknis dalam bahasa Inggris terstandarisasi CTI
        untuk keperluan semantic matching ATT&CK dan NIST.
        """
        if not teks_asli or not str(teks_asli).strip():
            return ""

        # Jika Gemini LLM aktif, gunakan untuk terjemahan CTI presisi
        if self._is_gemini_active():
            prompt = (
                "Translate the following Indonesian cyber incident news summary into a concise "
                "technical English threat intelligence report highlighting the attacker, method, "
                "vulnerability, target, and impact:\n\n"
                f"{teks_asli[:1500]}"
            )
            try:
                res = GeminiLLMAdapter.chat(
                    system_prompt="You are a specialized Cyber Threat Intelligence translator.",
                    user_prompt=prompt,
                    temperature=0.1,
                )
                if res and len(res.strip()) > 10:
                    return res.strip()
            except Exception as e:
                logger.debug(f"LLM translation fallback: {e}")

        # Fallback translasi terminologi teknis jika offline
        replacements = [
            ("rumah sakit", "hospital"),
            ("diretas", "breached and hacked"),
            ("data pribadi", "personal identifiable information data"),
            ("bocor", "leaked and exfiltrated"),
            ("perangkat lunak pemeras", "ransomware"),
            ("tebusan", "ransom demand"),
            ("judi slot", "gambling slot defacement"),
            ("lampiran", "attachment"),
            ("celah keamanan", "vulnerability exploit"),
            ("lumpuh", "disabled and unavailable"),
        ]
        text_en = teks_asli
        for ind, eng in replacements:
            text_en = re.sub(re.escape(ind), eng, text_en, flags=re.IGNORECASE)
        return text_en

    def analyze_news(self, article: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
        """
        Pipeline lengkap pemrosesan intelijen per berita (Tahap 4 & R2):
        1. Menyiapkan dual-text (teks asli & terjemahan teknis).
        2. Klasifikasi insiden eCSIRT.
        3. Ekstraksi teknik ATT&CK kondisional + Active validation guard.
        4. Lookup deterministik D3FEND.
        5. Lookup referensi NIST on-demand.
        6. Persistensi provenance ke SQLite.
        """
        identifier = (
            article.get("identifier")
            or article.get("article_identifier")
            or article.get("link")
            or f"art_{datetime.now(timezone.utc).timestamp()}"
        )

        judul = article.get("judul", "")
        ringkasan = article.get("ringkasan_atau_narasi", "")
        teks_asli = article.get("teks_asli") or f"{judul}. {ringkasan}".strip()
        teks_terjemahan = article.get("teks_terjemahan")

        if not teks_terjemahan and teks_asli:
            teks_terjemahan = self.translate_to_technical_english(teks_asli)

        # 1. Klasifikasi Taksonomi
        klasifikasi = self.classify_incident(teks_asli, teks_terjemahan)

        # 2. Ekstraksi Teknik ATT&CK
        ekstraksi_att = self.extract_attack_technique(teks_asli, teks_terjemahan)

        # 3. Klasifikasi Sektor IIV Perpres 82/2022
        klasifikasi_sektor = self.classify_sector(article)

        # 4. Lookup Deterministik D3FEND
        mitre_id = ekstraksi_att.get("technique_id")
        d3fend_mitigasi = self.lookup_d3fend_mitigations(mitre_id)

        # 5. Lookup Referensi NIST
        nist_query = f"{klasifikasi.get('kategori_utama', '')} {ekstraksi_att.get('technique_name', '')} {teks_terjemahan or ''}"
        nist_referensi = self.lookup_nist_references(nist_query, top_k=2)

        # Susun Record Intelijen Lengkap
        dibuat_pada = datetime.now(timezone.utc).isoformat()
        intel_record = {
            "article_identifier": identifier,
            "kategori_insiden": klasifikasi["kategori_utama"],
            "kategori_utama": klasifikasi["kategori_utama"],
            "kategori_key": klasifikasi["kategori_key"],
            "kategori_tambahan": klasifikasi.get("kategori_tambahan"),
            "confidence_kategori": klasifikasi["confidence"],
            "kutipan_bukti_kategori": klasifikasi["kutipan_bukti"],
            "alasan_kategori": klasifikasi.get("alasan", ""),
            "id_taksonomi_induk": klasifikasi["id_taksonomi_induk"],
            "mitre_tactic": ekstraksi_att.get("tactic"),
            "mitre_technique_id": ekstraksi_att.get("technique_id"),
            "mitre_technique_name": ekstraksi_att.get("technique_name"),
            "confidence_mitre": ekstraksi_att.get("confidence"),
            "kutipan_bukti_mitre": ekstraksi_att.get("kutipan_bukti"),
            "sektor_target": klasifikasi_sektor.get("sektor_target", "Tidak dapat ditentukan"),
            "confidence_sektor": klasifikasi_sektor.get("confidence_sektor", 0.0),
            "kutipan_bukti_sektor": klasifikasi_sektor.get("kutipan_bukti_sektor", ""),
            "alasan_sektor": klasifikasi_sektor.get("alasan_sektor", ""),
            "d3fend_mitigasi": d3fend_mitigasi,
            "d3fend_mitigasi_json": d3fend_mitigasi,
            "nist_referensi": nist_referensi,
            "nist_referensi_json": nist_referensi,
            "version_taxonomy": self.version_info["taxonomy"],
            "version_attack": self.version_info["attack"],
            "version_d3fend": self.version_info["d3fend"],
            "version_nist": self.version_info["nist"],
            "version_info": self.version_info,
            "disclaimer_d3fend": DISCLAIMER_D3FEND,
            "dibuat_pada": dibuat_pada,
            "teks_asli": teks_asli,
            "teks_terjemahan": teks_terjemahan,
        }

        # 5. Persistensi ke database SQLite
        if persist:
            simpan_intelijen_berita(intel_record, db_path=self.db_path)

        return intel_record

    def record_manual_correction(
        self,
        article_identifier: str,
        koreksi_kategori: Optional[str] = None,
        koreksi_technique_id: Optional[str] = None,
        catatan: Optional[str] = None,
        oleh: Optional[str] = None,
        koreksi_sektor: Optional[str] = None,
    ) -> bool:
        """Mencatat koreksi manual admin pada hasil analisis berita."""
        res_intel = simpan_koreksi_admin_intelijen(
            article_identifier=article_identifier,
            koreksi_kategori=koreksi_kategori,
            koreksi_technique_id=koreksi_technique_id,
            catatan=catatan,
            oleh=oleh,
            db_path=self.db_path,
        )
        if koreksi_sektor:
            simpan_koreksi_admin_sektor(
                article_identifier=article_identifier,
                sektor=koreksi_sektor,
                alasan=catatan,
                oleh=oleh,
                db_path=self.db_path,
            )
            return True
        return res_intel

    def record_manual_sector_correction(
        self,
        article_identifier: str,
        sektor: str,
        alasan: Optional[str] = None,
        oleh: Optional[str] = None,
    ) -> bool:
        """Mencatat koreksi manual admin pada sektor berita."""
        return simpan_koreksi_admin_sektor(
            article_identifier=article_identifier,
            sektor=sektor,
            alasan=alasan,
            oleh=oleh,
            db_path=self.db_path,
        )

    def get_verified_intelligence(self, article_identifier: str) -> Optional[Dict[str, Any]]:
        """Mengambil data intelijen tersimpan beserta koreksi admin."""
        return ambil_intelijen_berita(article_identifier=article_identifier, db_path=self.db_path)


# =============================================================================
# STANDALONE FUNCTION EXPORTS
# =============================================================================

def classify_sector(
    article: Union[Dict[str, Any], str],
    analyzer: Optional[CTINewsAnalyzer] = None,
) -> Dict[str, Any]:
    """Fungsi pembungkus praktis untuk klasifikasi sektor sasaran IIV per berita."""
    if analyzer is None:
        analyzer = CTINewsAnalyzer()
    return analyzer.classify_sector(article)
