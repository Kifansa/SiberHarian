"""
SiberHarian CTI Vector Store Engine (Milestone 3 / Tahap 3).

Mengelola 3 koleksi vektor terpisah:
1. `collection_attack`: 706 teknik MITRE ATT&CK Enterprise aktif (tanpa revoked/deprecated).
2. `collection_taxonomy`: 11 kategori taksonomi insiden eCSIRT.
3. `collection_nist`: 1.381 kontrol keamanan NIST SP 800-53 Rev 5 & CSF 2.0.

Fitur:
- Isolasi ketat antarkoleksi (namespace terpisah & direktori persisten mandiri).
- Integrasi embedding multibahasa via GeminiLLMAdapter (gemini-embedding-001, 768 dimensi).
- Algoritma fallback embedding lokal deterministik berbasis feature hashing n-gram untuk unit test & mode offline.
- Perankingan cosine similarity cepat.
- Strategi dual-text translation retrieval:
  - Taksonomi: pencarian dapat menggunakan teks Bahasa Indonesia dan/atau terjemahan teknis Bahasa Inggris.
  - ATT&CK & NIST: pencarian строго menggunakan kueri terjemahan teknis Bahasa Inggris untuk semantic alignment optimal.
"""

import os
import json
import math
import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.utils.logger import setup_logger
from src.utils.llm_adapter import GeminiLLMAdapter

logger = setup_logger(__name__)

DEFAULT_PREPARED_DIR = Path(__file__).resolve().parents[2] / "data" / "prepared"
DEFAULT_VECTOR_DIR = Path(__file__).resolve().parents[2] / "data" / "vector_stores"
VECTOR_DIMENSION = 768


def compute_deterministic_embedding(text: str, dim: int = VECTOR_DIMENSION) -> List[float]:
    """
    Menghasilkan vector embedding 768-dimensi deterministik berbasis feature hashing
    word & n-gram dengan pembobotan term teknis.
    Digunakan saat API Gemini offline / tanpa API key agar pengujian unit tetap genuine.
    """
    if not text or not str(text).strip():
        return [0.0] * dim

    clean_text = str(text).lower()
    tokens = re.findall(r'[a-zA-Z0-9_\-\.]+', clean_text)
    if not tokens:
        return [0.0] * dim

    vec = [0.0] * dim

    # 1. Hashing token kata dengan bobot panjang kata
    for token in tokens:
        weight = 1.0 + (0.1 * min(len(token), 10))
        # Hash MD5
        h_md5 = int(hashlib.md5(token.encode('utf-8')).hexdigest(), 16)
        idx1 = h_md5 % dim
        sign1 = 1.0 if ((h_md5 >> 16) & 1) else -1.0
        vec[idx1] += sign1 * weight

        # Hash SHA256 untuk mendistribusikan sinyal secara merata
        h_sha = int(hashlib.sha256(token.encode('utf-8')).hexdigest(), 16)
        idx2 = h_sha % dim
        sign2 = 1.0 if ((h_sha >> 16) & 1) else -1.0
        vec[idx2] += sign2 * weight

    # 2. Hashing bigram untuk menangkap konteks frasa (mis. "data breach", "remote code")
    for i in range(len(tokens) - 1):
        bigram = f"{tokens[i]}_{tokens[i+1]}"
        h_bg = int(hashlib.md5(bigram.encode('utf-8')).hexdigest(), 16)
        idx_bg = h_bg % dim
        sign_bg = 1.0 if ((h_bg >> 16) & 1) else -1.0
        vec[idx_bg] += sign_bg * 1.8

    # 3. L2 Normalization
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0.0:
        vec = [x / norm for x in vec]

    return vec


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Menghitung cosine similarity antara dua vektor."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class CTIVectorStore:
    """
    Mesin RAG Vector Store multi-koleksi untuk SiberHarian CTI Layer.
    Mengelola 3 koleksi terisolasi: collection_attack, collection_taxonomy, collection_nist.
    """

    ALLOWED_COLLECTIONS = {
        "collection_attack",
        "collection_taxonomy",
        "collection_nist",
    }

    def __init__(
        self,
        prepared_dir: Optional[Path] = None,
        vector_dir: Optional[Path] = None,
        auto_load: bool = True,
        embedding_mode: str = "auto",  # 'auto', 'gemini', 'offline'
    ):
        self.prepared_dir = Path(prepared_dir) if prepared_dir else DEFAULT_PREPARED_DIR
        self.vector_dir = Path(vector_dir) if vector_dir else DEFAULT_VECTOR_DIR
        self.dimension = VECTOR_DIMENSION
        self.embedding_mode = embedding_mode
        self._gemini_available: Optional[bool] = None

        # Namespace koleksi terisolasi
        self.collection_attack: List[Dict[str, Any]] = []
        self.collection_taxonomy: List[Dict[str, Any]] = []
        self.collection_nist: List[Dict[str, Any]] = []

        # Status kesiapan tiap koleksi
        self.status = {
            "collection_attack": "UNINITIALIZED",
            "collection_taxonomy": "UNINITIALIZED",
            "collection_nist": "UNINITIALIZED",
        }

        # Direktori penyimpanan persisten mandiri per koleksi
        self.dir_attack = self.vector_dir / "attack"
        self.dir_taxonomy = self.vector_dir / "taxonomy"
        self.dir_nist = self.vector_dir / "nist"

        for d in [self.dir_attack, self.dir_taxonomy, self.dir_nist]:
            d.mkdir(parents=True, exist_ok=True)

        if auto_load:
            self.load_or_build_all()

    def _is_gemini_active(self) -> bool:
        """Mengecek apakah layanan Gemini Embedding online aktif atau sedang di-mock."""
        if self.embedding_mode == "offline":
            return False
        if self.embedding_mode == "gemini":
            return True

        from unittest.mock import Mock
        if isinstance(getattr(GeminiLLMAdapter, "embed_text", None), Mock):
            return True

        if self._gemini_available is not None:
            return self._gemini_available

        try:
            from src.utils.settings_manager import SettingsManager
            cfg = SettingsManager.get_gemini_config()
            raw_key = cfg.get("api_key", "") or os.environ.get("GEMINI_API_KEY", "")
            if not raw_key or not str(raw_key).startswith("AIza"):
                self._gemini_available = False
                return False

            probe = GeminiLLMAdapter.embed_text("probe")
            self._gemini_available = bool(probe and len(probe) == self.dimension)
        except Exception:
            self._gemini_available = False

        return bool(self._gemini_available)

    def get_embedding(self, text: str) -> List[float]:
        """
        Menghasilkan vector embedding untuk teks kueri.
        Mencoba Gemini embedding jika online/mocked; jika tidak tersedia,
        menggunakan fallback embedding deterministik.
        """
        if not text or not str(text).strip():
            return [0.0] * self.dimension

        if self._is_gemini_active():
            try:
                emb = GeminiLLMAdapter.embed_text(text)
                if emb and len(emb) == self.dimension:
                    return emb
            except Exception as e:
                logger.debug(f"Gemini embedding gagal: {e}. Menggunakan fallback deterministik.")

        return compute_deterministic_embedding(text, dim=self.dimension)

    def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Menghasilkan vector embeddings untuk kumpulan dokumen secara batch."""
        if not texts:
            return []

        if self._is_gemini_active():
            try:
                embs = GeminiLLMAdapter.embed_documents(texts, batch_size=50)
                if embs and len(embs) == len(texts) and all(e and len(e) == self.dimension for e in embs):
                    return embs
            except Exception as e:
                logger.debug(f"Gemini batch embedding gagal: {e}. Menggunakan fallback deterministik.")

        return [compute_deterministic_embedding(t, dim=self.dimension) for t in texts]

    # =========================================================================
    # BUILD & LOAD INDEXES
    # =========================================================================

    def _get_index_file(self, collection_name: str) -> Path:
        if collection_name == "collection_attack":
            return self.dir_attack / "index.json"
        elif collection_name == "collection_taxonomy":
            return self.dir_taxonomy / "index.json"
        elif collection_name == "collection_nist":
            return self.dir_nist / "index.json"
        raise ValueError(f"Koleksi tidak valid: {collection_name}")

    def build_taxonomy_index(self, force_rebuild: bool = False) -> int:
        """Membangun indeks untuk 11 kategori taksonomi insiden eCSIRT."""
        index_file = self._get_index_file("collection_taxonomy")
        if not force_rebuild and index_file.exists():
            try:
                data = json.loads(index_file.read_text(encoding="utf-8"))
                self.collection_taxonomy = data.get("records", [])
                self.status["collection_taxonomy"] = "READY"
                logger.info(f"Dimuat {len(self.collection_taxonomy)} taksonomi dari cache: {index_file}")
                return len(self.collection_taxonomy)
            except Exception as e:
                logger.warning(f"Cache taksonomi korup, membangun ulang: {e}")

        source_file = self.prepared_dir / "taxonomy_categories.json"
        if not source_file.exists():
            logger.warning(f"Berkas sumber {source_file} tidak ditemukan.")
            self.status["collection_taxonomy"] = "MISSING_SOURCE"
            return 0

        raw_categories = json.loads(source_file.read_text(encoding="utf-8"))
        records = []
        texts_to_embed = []

        for cat in raw_categories:
            cat_id = cat.get("category_id", "")
            name = cat.get("name", "")
            ecsirt_parent = cat.get("ecsirt_parent", "")
            definition = cat.get("definition", "")
            examples = " ".join(cat.get("representative_examples", []))

            # Teks representasi dokumen multibahasa
            doc_text = (
                f"[TAKSONOMI INSIDEN SIBER]\n"
                f"Kategori: {name} ({cat_id})\n"
                f"Induk eCSIRT: {ecsirt_parent}\n"
                f"Definisi: {definition}\n"
                f"Contoh Kasus: {examples}"
            ).strip()

            texts_to_embed.append(doc_text)
            records.append({
                "id": cat_id,
                "name": name,
                "ecsirt_parent": ecsirt_parent,
                "definition": definition,
                "representative_examples": cat.get("representative_examples", []),
                "metadata": cat.get("metadata", {}),
                "collection": "collection_taxonomy",
                "doc_text": doc_text,
            })

        vectors = self.get_embeddings_batch(texts_to_embed)
        for r, v in zip(records, vectors):
            r["vector"] = v

        payload = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "collection": "collection_taxonomy",
            "dimension": self.dimension,
            "records": records,
        }
        index_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        self.collection_taxonomy = records
        self.status["collection_taxonomy"] = "READY"
        logger.info(f"Berhasil mengindeks {len(records)} kategori taksonomi.")
        return len(records)

    def build_attack_index(self, force_rebuild: bool = False) -> int:
        """Membangun indeks untuk seluruh teknik MITRE ATT&CK aktif."""
        index_file = self._get_index_file("collection_attack")
        if not force_rebuild and index_file.exists():
            try:
                data = json.loads(index_file.read_text(encoding="utf-8"))
                self.collection_attack = data.get("records", [])
                self.status["collection_attack"] = "READY"
                logger.info(f"Dimuat {len(self.collection_attack)} teknik ATT&CK dari cache: {index_file}")
                return len(self.collection_attack)
            except Exception as e:
                logger.warning(f"Cache ATT&CK korup, membangun ulang: {e}")

        source_file = self.prepared_dir / "attack_techniques.json"
        if not source_file.exists():
            logger.warning(f"Berkas sumber {source_file} tidak ditemukan.")
            self.status["collection_attack"] = "MISSING_SOURCE"
            return 0

        raw_techniques = json.loads(source_file.read_text(encoding="utf-8"))
        records = []
        texts_to_embed = []

        for tech in raw_techniques:
            tech_id = tech.get("technique_id", "")
            name = tech.get("name", "")
            tactics = ", ".join(tech.get("tactics", []))
            platforms = ", ".join(tech.get("platforms", []))
            desc = tech.get("description", "")

            # Dokumen teks resmi MITRE ATT&CK
            doc_text = (
                f"[MITRE ATT&CK TECHNIQUE]\n"
                f"ID: {tech_id}\n"
                f"Name: {name}\n"
                f"Tactics: {tactics}\n"
                f"Platforms: {platforms}\n"
                f"Description: {desc[:1500]}"
            ).strip()

            texts_to_embed.append(doc_text)
            records.append({
                "id": tech_id,
                "technique_id": tech_id,
                "name": name,
                "tactics": tech.get("tactics", []),
                "platforms": tech.get("platforms", []),
                "description": desc,
                "is_subtechnique": tech.get("is_subtechnique", False),
                "metadata": tech.get("metadata", {}),
                "collection": "collection_attack",
                "doc_text": doc_text,
            })

        vectors = self.get_embeddings_batch(texts_to_embed)
        for r, v in zip(records, vectors):
            r["vector"] = v

        payload = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "collection": "collection_attack",
            "dimension": self.dimension,
            "records": records,
        }
        index_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.collection_attack = records
        self.status["collection_attack"] = "READY"
        logger.info(f"Berhasil mengindeks {len(records)} teknik aktif MITRE ATT&CK.")
        return len(records)

    def build_nist_index(self, force_rebuild: bool = False) -> int:
        """Membangun indeks untuk kontrol NIST SP 800-53 Rev 5 & CSF 2.0."""
        index_file = self._get_index_file("collection_nist")
        if not force_rebuild and index_file.exists():
            try:
                data = json.loads(index_file.read_text(encoding="utf-8"))
                self.collection_nist = data.get("records", [])
                self.status["collection_nist"] = "READY"
                logger.info(f"Dimuat {len(self.collection_nist)} kontrol NIST dari cache: {index_file}")
                return len(self.collection_nist)
            except Exception as e:
                logger.warning(f"Cache NIST korup, membangun ulang: {e}")

        source_file = self.prepared_dir / "nist_controls.json"
        if not source_file.exists():
            logger.warning(f"Berkas sumber {source_file} tidak ditemukan.")
            self.status["collection_nist"] = "MISSING_SOURCE"
            return 0

        raw_controls = json.loads(source_file.read_text(encoding="utf-8"))
        records = []
        texts_to_embed = []

        for ctrl in raw_controls:
            ctrl_id = ctrl.get("control_id", "")
            title = ctrl.get("title", "")
            framework = ctrl.get("framework", "")
            family = ctrl.get("family_or_function", "")
            stmt = ctrl.get("statement", "")

            doc_text = (
                f"[{framework}] {ctrl_id}: {title} ({family})\n"
                f"{stmt[:1500]}"
            ).strip()

            texts_to_embed.append(doc_text)
            records.append({
                "id": ctrl_id,
                "control_id": ctrl_id,
                "title": title,
                "framework": framework,
                "family_or_function": family,
                "statement": stmt,
                "metadata": ctrl.get("metadata", {}),
                "collection": "collection_nist",
                "doc_text": doc_text,
            })

        vectors = self.get_embeddings_batch(texts_to_embed)
        for r, v in zip(records, vectors):
            r["vector"] = v

        payload = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "collection": "collection_nist",
            "dimension": self.dimension,
            "records": records,
        }
        index_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        self.collection_nist = records
        self.status["collection_nist"] = "READY"
        logger.info(f"Berhasil mengindeks {len(records)} kontrol keamanan NIST.")
        return len(records)

    def load_or_build_all(self, force_rebuild: bool = False) -> None:
        """Memuat atau membangun ketiga koleksi vektor secara terisolasi."""
        try:
            self.build_taxonomy_index(force_rebuild=force_rebuild)
        except Exception as e:
            logger.error(f"Gagal memuat collection_taxonomy: {e}")
            self.status["collection_taxonomy"] = "FAILED"

        try:
            self.build_attack_index(force_rebuild=force_rebuild)
        except Exception as e:
            logger.error(f"Gagal memuat collection_attack: {e}")
            self.status["collection_attack"] = "FAILED"

        try:
            self.build_nist_index(force_rebuild=force_rebuild)
        except Exception as e:
            logger.error(f"Gagal memuat collection_nist: {e}")
            self.status["collection_nist"] = "FAILED"

    # =========================================================================
    # RETRIEVAL API WITH DUAL-TEXT TRANSLATION STRATEGY
    # =========================================================================

    def search_taxonomy(
        self,
        query_id: str,
        query_en: Optional[str] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Pencarian semantik pada collection_taxonomy.
        Mendukung strategi dual-text: kueri bahasa Indonesia (query_id)
        dan terjemahan teknis bahasa Inggris (query_en).
        """
        if not self.collection_taxonomy:
            return []

        emb_id = self.get_embedding(query_id) if query_id else None
        emb_en = self.get_embedding(query_en) if query_en else None

        results = []
        for item in self.collection_taxonomy:
            item_vec = item.get("vector")
            if not item_vec:
                continue

            score = 0.0
            if emb_id and emb_en:
                score_id = cosine_similarity(emb_id, item_vec)
                score_en = cosine_similarity(emb_en, item_vec)
                score = max(score_id, score_en)
            elif emb_id:
                score = cosine_similarity(emb_id, item_vec)
            elif emb_en:
                score = cosine_similarity(emb_en, item_vec)

            results.append({
                "id": item["id"],
                "category_id": item["id"],
                "name": item["name"],
                "ecsirt_parent": item["ecsirt_parent"],
                "definition": item["definition"],
                "representative_examples": item.get("representative_examples", []),
                "metadata": item.get("metadata", {}),
                "collection": "collection_taxonomy",
                "score": float(score),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def search_attack(self, query_en: str, top_k: int = 15) -> List[Dict[str, Any]]:
        """
        Pencarian semantik pada collection_attack.
        WAJIB menggunakan teks terjemahan teknis Bahasa Inggris (query_en)
        untuk semantic alignment terhadap terminologi MITRE ATT&CK.
        """
        if not self.collection_attack or not query_en:
            return []

        query_vec = self.get_embedding(query_en)

        results = []
        for item in self.collection_attack:
            item_vec = item.get("vector")
            if not item_vec:
                continue

            score = cosine_similarity(query_vec, item_vec)
            results.append({
                "id": item["technique_id"],
                "technique_id": item["technique_id"],
                "name": item["name"],
                "tactics": item.get("tactics", []),
                "platforms": item.get("platforms", []),
                "description": item.get("description", ""),
                "is_subtechnique": item.get("is_subtechnique", False),
                "metadata": item.get("metadata", {}),
                "collection": "collection_attack",
                "score": float(score),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def search_nist(self, query_en: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Pencarian semantik pada collection_nist.
        WAJIB menggunakan teks terjemahan teknis Bahasa Inggris (query_en)
        untuk semantic alignment terhadap standar NIST SP 800-53 / CSF 2.0.
        """
        if not self.collection_nist or not query_en:
            return []

        query_vec = self.get_embedding(query_en)

        results = []
        for item in self.collection_nist:
            item_vec = item.get("vector")
            if not item_vec:
                continue

            score = cosine_similarity(query_vec, item_vec)
            results.append({
                "id": item["control_id"],
                "control_id": item["control_id"],
                "title": item["title"],
                "framework": item["framework"],
                "family_or_function": item["family_or_function"],
                "statement": item.get("statement", ""),
                "metadata": item.get("metadata", {}),
                "collection": "collection_nist",
                "score": float(score),
            })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def query_collection(self, collection_name: str, query: str, top_k: int = 5) -> Any:
        """
        Wrapper terisolasi untuk mengueri koleksi spesifik.
        Menolak akses jika nama koleksi tidak terdaftar.
        """
        if collection_name not in self.ALLOWED_COLLECTIONS:
            raise ValueError(f"Unauthorized collection: {collection_name}")

        if collection_name == "collection_attack":
            return self.search_attack(query_en=query, top_k=top_k)
        elif collection_name == "collection_taxonomy":
            return self.search_taxonomy(query_id=query, query_en=query, top_k=top_k)
        elif collection_name == "collection_nist":
            return self.search_nist(query_en=query, top_k=top_k)

        return []
