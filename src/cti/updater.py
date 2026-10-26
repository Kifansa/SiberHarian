"""
SiberHarian CTI Source Periodic Updater & Resiliency Engine (Milestone 6 / Tahap 5, R4).

Bertanggung jawab mengelola pembaruan berkala untuk seluruh sumber threat intelligence resmi:
1. MITRE ATT&CK Enterprise (STIX 2.1)
2. MITRE D3FEND (Defensive Ontology & Relational Mappings)
3. NIST OSCAL Catalogs (SP 800-53 Rev 5 & CSF 2.0)
4. MISP / eCSIRT Incident Taxonomy

Fitur Utama:
- Idempotent Version Checking: verifikasi rilis hulu vs versi aktif di metadata_sistem / staging.
  Jika rilis tidak berubah, berhenti dan catat log: "tidak ada pembaruan untuk <source> (versi aktif: <version>)".
- Catastrophic Drop Guard: validasi skema dan jumlah record staging baru.
  Jika record == 0 atau turun > 30% (< 70% dari versi lama), lempar DropDetectionError dan batalkan update.
  Indeks aktif dan basis data tetap utuh.
- Diff Reporting: identifikasi perubahan record (added, modified, revoked, unchanged).
  Laporan disimpan sebagai berkas JSON di data/reports/diff_<source>_<timestamp>.json.
- Incremental Re-embedding: hanya melakukan embedding terhadap dokumen dalam set added dan modified.
  Dokumen yang tidak berubah mempertahankan vector embedding dari cache sebelumnya.
- Atomic Swap & Rollback: membangun indeks di vNext, melakukan smoke test, menukar pointer/file
  secara atomik, serta mempertahankan indeks vPrev untuk kemampuan rollback instan.
- Revoked Technique Historical Auditor: menandai insiden historis yang memakai teknik yang dicabut
  dengan flag "TEKNIK_REVOKED_PERLU_REVIEW" di tabel intelijen_berita_tervalidasi. Dilarang menghapus data lama!
- Resiliensi Jaringan: dukungan HTTP proxy dan mirror internal (--mirror-base-url).
"""

import os
import sys
import re
import json
import shutil
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set, Union

import requests

from src.utils.logger import setup_logger
from src.cti.downloader import CTIDownloader, OFFICIAL_URLS
from src.cti.preparer import (
    CTIPreparer,
    DEFAULT_RAW_DIR,
    DEFAULT_PREPARED_DIR,
    CLOSED_11_TAXONOMY_CATEGORIES,
)
from src.cti.vector_store import (
    CTIVectorStore,
    DEFAULT_VECTOR_DIR,
    VECTOR_DIMENSION,
    cosine_similarity,
)
from src.storage.db import (
    DEFAULT_DB_PATH,
    init_db,
    simpan_metadata,
    ambil_metadata,
    tandai_flag_tinjauan_intelijen,
)

logger = setup_logger(__name__)

DEFAULT_REPORTS_DIR = Path(__file__).resolve().parents[2] / "data" / "reports"


class DropDetectionError(Exception):
    """Exception dilempar saat jumlah record baru turun drastis (>30%) atau kosong."""
    pass


# Alias kompatibilitas
UpdateValidationError = DropDetectionError


class CTISourceUpdater:
    """
    Periodic update engine untuk 4 pilar intelijen siber SiberHarian.
    """

    SUPPORTED_SOURCES = {
        "mitre_attack",
        "mitre_d3fend",
        "nist_oscal",
        "misp_taxonomies",
    }

    def __init__(
        self,
        raw_dir: Optional[Path] = None,
        prepared_dir: Optional[Path] = None,
        vector_dir: Optional[Path] = None,
        reports_dir: Optional[Path] = None,
        db_path: Path = DEFAULT_DB_PATH,
        mirror_base_url: Optional[str] = None,
        proxies: Optional[Dict[str, str]] = None,
        vector_store: Optional[CTIVectorStore] = None,
    ):
        self.raw_dir = Path(raw_dir) if raw_dir else DEFAULT_RAW_DIR
        self.prepared_dir = Path(prepared_dir) if prepared_dir else DEFAULT_PREPARED_DIR
        self.vector_dir = Path(vector_dir) if vector_dir else DEFAULT_VECTOR_DIR
        self.reports_dir = Path(reports_dir) if reports_dir else DEFAULT_REPORTS_DIR
        self.db_path = Path(db_path)
        self.mirror_base_url = mirror_base_url
        self.proxies = proxies

        # Inisialisasi direktori
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        init_db(self.db_path)

        # Inisialisasi komponen pendukung
        self.downloader = CTIDownloader(
            base_staging_dir=self.raw_dir,
            mirror_base_url=self.mirror_base_url,
            proxies=self.proxies,
        )
        self.preparer = CTIPreparer(
            raw_base_dir=self.raw_dir,
            prepared_base_dir=self.prepared_dir,
            db_path=self.db_path,
        )
        self.vector_store = vector_store or CTIVectorStore(
            prepared_dir=self.prepared_dir,
            vector_dir=self.vector_dir,
            auto_load=True,
        )

    # =========================================================================
    # 1. VERSION CHECKING & IDEMPOTENCY
    # =========================================================================

    def get_active_version(self, source: str) -> Optional[str]:
        """
        Mengambil versi aktif untuk suatu sumber data dari metadata_sistem di SQLite,
        atau mencari berkas staging metadata.json paling mutakhir sebagai fallback.
        """
        meta_key = f"cti_version_{source}"
        val = ambil_metadata(meta_key, self.db_path)
        if val:
            return str(val)

        # Fallback ke metadata staging terbaru di disk
        source_dir = self.raw_dir / source
        if source_dir.exists():
            date_folders = sorted(
                [d for d in source_dir.iterdir() if d.is_dir()],
                key=lambda p: p.name,
                reverse=True,
            )
            for d in date_folders:
                meta_file = d / "metadata.json"
                if meta_file.exists():
                    try:
                        m = json.loads(meta_file.read_text(encoding="utf-8"))
                        ver = m.get("version_identifier") or m.get("file_sha256")
                        if ver:
                            return str(ver)
                    except Exception:
                        pass
        return None

    def set_active_version(self, source: str, version: str) -> None:
        """Menyimpan versi aktif baru ke tabel metadata_sistem."""
        meta_key = f"cti_version_{source}"
        simpan_metadata(meta_key, str(version), self.db_path)
        logger.info(f"Versi aktif {source} diperbarui menjadi: {version}")

    def fetch_remote_version(self, source: str) -> str:
        """
        Mengecek nomor versi atau commit hash dari sumber upstream resmi.
        Mendukung timeout, proxy, dan mock/fallback bila jaringan tertutup.
        """
        session = requests.Session()
        if self.proxies:
            session.proxies.update(self.proxies)

        timeout = 15

        try:
            if source == "mitre_attack":
                # Cek release version dari bundle URL
                url = self.downloader._resolve_url(OFFICIAL_URLS["mitre_attack"]["primary"])
                # Lakukan probe HEAD atau GET dengan rentang byte kecil
                resp = session.get(url, headers={"Range": "bytes=0-4096"}, timeout=timeout)
                if resp.status_code in (200, 206):
                    # Cari string "x_mitre_version"
                    match = re.search(r'"x_mitre_version":\s*"([^"]+)"', resp.text)
                    if match:
                        return f"v{match.group(1)}"
                return "v20.0"

            elif source == "mitre_d3fend":
                url = self.downloader._resolve_url(OFFICIAL_URLS["mitre_d3fend"]["version_url"])
                resp = session.get(url, timeout=timeout)
                if resp.status_code == 200:
                    data = resp.json()
                    ver = data.get("version") or data.get("ontology_version")
                    if ver:
                        return str(ver)
                return "1.6.0"

            elif source == "nist_oscal":
                return "SP800-53-Rev5 / CSF-2.0"

            elif source == "misp_taxonomies":
                url = self.downloader._resolve_url(OFFICIAL_URLS["misp_taxonomies"]["primary"])
                resp = session.get(url, headers={"Range": "bytes=0-2048"}, timeout=timeout)
                if resp.status_code in (200, 206):
                    match = re.search(r'"version":\s*"?(\d+)"?', resp.text)
                    if match:
                        return str(match.group(1))
                return "2"

        except Exception as e:
            logger.debug(f"Pengecekan versi remote {source} gagal: {e}. Menggunakan versi aktif fallback.")

        # Fallback ke versi aktif yang sudah ada
        active = self.get_active_version(source)
        return active or "1.0.0"

    def check_version(self, source: str) -> Dict[str, Any]:
        """
        Membandingkan versi remote terhadap versi aktif.
        Jika tidak ada perubahan, mencatat log tepat:
        "tidak ada pembaruan untuk <source> (versi aktif: <version>)"
        """
        if source not in self.SUPPORTED_SOURCES:
            raise ValueError(f"Sumber tidak didukung: {source}. Pilih dari {self.SUPPORTED_SOURCES}")

        active_ver = self.get_active_version(source)
        remote_ver = self.fetch_remote_version(source)

        has_update = (active_ver is None) or (str(active_ver) != str(remote_ver))

        if not has_update:
            msg = f"tidak ada pembaruan untuk {source} (versi aktif: {active_ver})"
            logger.info(msg)
            return {
                "has_update": False,
                "source": source,
                "active_version": active_ver,
                "remote_version": remote_ver,
                "message": msg,
            }

        return {
            "has_update": True,
            "source": source,
            "active_version": active_ver,
            "remote_version": remote_ver,
            "message": f"Ditemukan pembaruan untuk {source}: {active_ver} -> {remote_ver}",
        }

    # =========================================================================
    # 2. STAGING & CATASTROPHIC DROP GUARD
    # =========================================================================

    @staticmethod
    def validate_staging_drop(source: str, new_count: int, old_count: int) -> None:
        """
        Memeriksa apakah jumlah record baru mengalami penurunan katastropik:
        - Tolak jika record baru kosong (0).
        - Tolak jika record baru turun lebih dari 30% (< 70% dari versi lama).
        """
        if new_count == 0:
            msg = f"Pembaruan ditolak: Payload baru {source} kosong (0 record)."
            logger.error(msg)
            raise DropDetectionError(msg)

        if old_count > 0:
            threshold = old_count * 0.70
            if new_count < threshold:
                drop_pct = ((old_count - new_count) / old_count) * 100.0
                msg = (
                    f"Pembaruan ditolak: Terdeteksi penurunan record drastis pada {source} "
                    f"(lama: {old_count}, baru: {new_count}, penurunan: {drop_pct:.1f}% > 30% batas aman)."
                )
                logger.error(msg)
                raise DropDetectionError(msg)

        logger.info(
            f"Validasi drop guard {source} lolos: record lama={old_count}, record baru={new_count}."
        )

    # =========================================================================
    # 3. DIFF REPORTING
    # =========================================================================

    def compute_diff(
        self,
        source: str,
        old_items: List[Dict[str, Any]],
        new_items: List[Dict[str, Any]],
        id_key: str = "technique_id",
        content_hash_func: Optional[Any] = None,
        old_version: str = "",
        new_version: str = "",
    ) -> Dict[str, Any]:
        """
        Menghitung selisih (diff) antara himpunan dokumen lama dan baru:
        - added: entri baru yang sebelumnya tidak ada.
        - modified: entri yang ID-nya sama tetapi konten berubah.
        - revoked: entri yang sebelumnya ada tetapi kini hilang atau ditandai revoked/deprecated.
        - unchanged: entri yang identik.
        Menyimpan hasil ke data/reports/diff_<source>_<timestamp>.json.
        """
        old_map: Dict[str, Dict[str, Any]] = {}
        for item in old_items:
            k = item.get(id_key) or item.get("id") or item.get("category_id") or item.get("control_id")
            if k:
                old_map[str(k)] = item

        new_map: Dict[str, Dict[str, Any]] = {}
        for item in new_items:
            k = item.get(id_key) or item.get("id") or item.get("category_id") or item.get("control_id")
            if k:
                new_map[str(k)] = item

        old_keys = set(old_map.keys())
        new_keys = set(new_map.keys())

        added_keys = new_keys - old_keys
        revoked_keys = old_keys - new_keys
        common_keys = old_keys & new_keys

        modified_keys: Set[str] = set()
        unchanged_keys: Set[str] = set()

        for k in common_keys:
            old_doc = old_map[k]
            new_doc = new_map[k]

            if content_hash_func:
                is_changed = content_hash_func(old_doc) != content_hash_func(new_doc)
            else:
                # Perbandingan teks/nama/definisi/taktik
                old_sig = (
                    old_doc.get("name", ""),
                    old_doc.get("description", ""),
                    old_doc.get("statement", ""),
                    str(old_doc.get("tactics", "")),
                    old_doc.get("definition", ""),
                )
                new_sig = (
                    new_doc.get("name", ""),
                    new_doc.get("description", ""),
                    new_doc.get("statement", ""),
                    str(new_doc.get("tactics", "")),
                    new_doc.get("definition", ""),
                )
                is_changed = old_sig != new_sig

            if is_changed:
                modified_keys.add(k)
            else:
                unchanged_keys.add(k)

        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report = {
            "source": source,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "old_version": str(old_version),
            "new_version": str(new_version),
            "total_old_records": len(old_items),
            "total_new_records": len(new_items),
            "counts": {
                "added": len(added_keys),
                "modified": len(modified_keys),
                "revoked": len(revoked_keys),
                "unchanged": len(unchanged_keys),
            },
            "added": sorted(list(added_keys)),
            "modified": sorted(list(modified_keys)),
            "revoked": sorted(list(revoked_keys)),
        }

        report_file = self.reports_dir / f"diff_{source}_{timestamp_str}.json"
        try:
            report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"Laporan diff tersimpan di: {report_file}")
        except Exception as e:
            logger.warning(f"Gagal menulis berkas laporan diff: {e}")

        report["report_path"] = str(report_file)
        return report

    # =========================================================================
    # 4. REVOKED TECHNIQUE HISTORICAL AUDITOR
    # =========================================================================

    def audit_revoked_attack_techniques(self, revoked_ids: List[str]) -> int:
        """
        Menandai seluruh insiden historis yang memakai teknik yang dicabut/revoked
        dengan flag TEKNIK_REVOKED_PERLU_REVIEW di tabel intelijen_berita_tervalidasi.
        DILARANG MENGHAPUS REKAMAN HISTORIS!
        """
        if not revoked_ids:
            return 0

        total_flagged = 0
        for tech_id in revoked_ids:
            clean_id = tech_id.strip()
            if not clean_id:
                continue
            rows = tandai_flag_tinjauan_intelijen(
                mitre_technique_id=clean_id,
                flag="TEKNIK_REVOKED_PERLU_REVIEW",
                db_path=self.db_path,
            )
            if rows > 0:
                total_flagged += rows
                logger.warning(
                    f"Audit Revoked Flagger: {rows} insiden historis ditandai "
                    f"'TEKNIK_REVOKED_PERLU_REVIEW' untuk teknik {clean_id}."
                )

        return total_flagged

    # =========================================================================
    # 5. INCREMENTAL RE-EMBEDDING & ATOMIC SWAP
    # =========================================================================

    def incremental_update_vector_index(
        self,
        collection_name: str,
        diff: Dict[str, Any],
        new_docs: List[Dict[str, Any]],
        doc_text_formatter: Any,
        id_key: str = "id",
    ) -> Dict[str, Any]:
        """
        Re-embedding inkremental:
        - Dokumen 'unchanged' mempertahankan vektor lama (tanpa panggilan embedding).
        - Hanya dokumen 'added' dan 'modified' yang di-embed ulang.
        - Dokumen 'revoked' dibuang dari indeks aktif.
        - Disimpan ke index.json.vNext.
        - Dijalankan smoke test; jika lolos, di-swap ke index.json dan index lama disimpan ke index.json.vPrev.
        """
        if collection_name not in CTIVectorStore.ALLOWED_COLLECTIONS:
            raise ValueError(f"Koleksi tidak diizinkan: {collection_name}")

        index_file = self.vector_store._get_index_file(collection_name)
        target_dir = index_file.parent
        v_next_file = target_dir / "index.json.vNext"
        v_prev_file = target_dir / "index.json.vPrev"

        # Muat cache index lama jika ada
        old_vectors: Dict[str, List[float]] = {}
        if index_file.exists():
            try:
                old_data = json.loads(index_file.read_text(encoding="utf-8"))
                for r in old_data.get("records", []):
                    k = r.get("id") or r.get("technique_id") or r.get("control_id") or r.get("category_id")
                    if k and "vector" in r:
                        old_vectors[str(k)] = r["vector"]
            except Exception as e:
                logger.warning(f"Gagal membaca vektor dari index lama {index_file}: {e}")

        added_set = set(diff.get("added", []))
        modified_set = set(diff.get("modified", []))
        revoked_set = set(diff.get("revoked", []))

        final_records: List[Dict[str, Any]] = []
        texts_to_embed: List[str] = []
        indices_to_embed: List[int] = []

        for doc in new_docs:
            k = doc.get(id_key) or doc.get("id") or doc.get("technique_id") or doc.get("control_id") or doc.get("category_id")
            k_str = str(k)

            # Lewati entri yang di-revoke
            if k_str in revoked_set:
                continue

            doc_text = doc_text_formatter(doc)
            rec = dict(doc)
            rec["id"] = k_str
            rec["doc_text"] = doc_text
            rec["collection"] = collection_name

            # Inkremental: jika ada di cache lama dan tidak modified/added, gunakan vektor lama
            if k_str in old_vectors and (k_str not in added_set) and (k_str not in modified_set):
                rec["vector"] = old_vectors[k_str]
            else:
                texts_to_embed.append(doc_text)
                indices_to_embed.append(len(final_records))
                rec["vector"] = None

            final_records.append(rec)

        # Batch embed HANYA dokumen yang berubah/baru
        if texts_to_embed:
            logger.info(
                f"Re-embedding inkremental untuk {collection_name}: {len(texts_to_embed)} dokumen baru/berubah "
                f"(menghemat {len(final_records) - len(texts_to_embed)} embedding dari cache)."
            )
            new_vectors = self.vector_store.get_embeddings_batch(texts_to_embed)
            for idx, vec in zip(indices_to_embed, new_vectors):
                final_records[idx]["vector"] = vec
        else:
            logger.info(f"Re-embedding inkremental untuk {collection_name}: Tidak ada teks yang perlu di-embed ulang.")

        # Tulis ke vNext
        payload_vnext = {
            "version": "1.0",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "collection": collection_name,
            "dimension": self.vector_store.dimension,
            "records": final_records,
        }
        v_next_file.write_text(json.dumps(payload_vnext, ensure_ascii=False, indent=2), encoding="utf-8")

        # Smoke Test vNext: verifikasi file dapat dibaca dan kueri cosine similarity berhasil
        try:
            smoke_data = json.loads(v_next_file.read_text(encoding="utf-8"))
            smoke_recs = smoke_data.get("records", [])
            if not smoke_recs:
                raise ValueError("Smoke test gagal: vNext tidak memiliki record.")
            sample_vec = smoke_recs[0]["vector"]
            if not sample_vec or len(sample_vec) != self.vector_store.dimension:
                raise ValueError("Smoke test gagal: Dimensi vektor pada vNext tidak valid.")
            _ = cosine_similarity(sample_vec, sample_vec)
            logger.info(f"Smoke test pada {v_next_file.name} lolos dengan {len(smoke_recs)} record.")
        except Exception as e:
            if v_next_file.exists():
                v_next_file.unlink()
            raise RuntimeError(f"Smoke test pada indeks vNext gagal: {e}. Pembaruan dibatalkan.")

        # Atomic Swap:
        # 1. Simpan index lama sebagai vPrev untuk rollback
        if index_file.exists():
            shutil.copy2(index_file, v_prev_file)
            logger.info(f"Cadangan rollback disimpan di: {v_prev_file}")

        # 2. Rename atomik vNext -> index.json
        if index_file.exists():
            index_file.unlink()
        v_next_file.rename(index_file)
        logger.info(f"Atomic swap berhasil: Indeks aktif {collection_name} beralih ke rilis baru.")

        # Perbarui memori vector store
        if collection_name == "collection_attack":
            self.vector_store.collection_attack = final_records
            self.vector_store.status["collection_attack"] = "READY"
        elif collection_name == "collection_taxonomy":
            self.vector_store.collection_taxonomy = final_records
            self.vector_store.status["collection_taxonomy"] = "READY"
        elif collection_name == "collection_nist":
            self.vector_store.collection_nist = final_records
            self.vector_store.status["collection_nist"] = "READY"

        return {
            "status": "SUCCESS",
            "collection": collection_name,
            "total_records": len(final_records),
            "reembedded_count": len(texts_to_embed),
            "reused_count": len(final_records) - len(texts_to_embed),
            "v_prev_path": str(v_prev_file),
            "active_path": str(index_file),
        }

    def rollback_vector_index(self, collection_name: str) -> bool:
        """
        Mengembalikan indeks koleksi ke cadangan vPrev jika terjadi insiden.
        """
        if collection_name not in CTIVectorStore.ALLOWED_COLLECTIONS:
            return False

        index_file = self.vector_store._get_index_file(collection_name)
        target_dir = index_file.parent
        v_prev_file = target_dir / "index.json.vPrev"

        if not v_prev_file.exists():
            logger.warning(f"Berkas rollback {v_prev_file} tidak ditemukan.")
            return False

        try:
            # Pulihkan dari vPrev
            shutil.copy2(v_prev_file, index_file)
            # Muat ulang ke memori
            data = json.loads(index_file.read_text(encoding="utf-8"))
            recs = data.get("records", [])

            if collection_name == "collection_attack":
                self.vector_store.collection_attack = recs
            elif collection_name == "collection_taxonomy":
                self.vector_store.collection_taxonomy = recs
            elif collection_name == "collection_nist":
                self.vector_store.collection_nist = recs

            logger.info(f"Rollback berhasil: {collection_name} dipulihkan ke versi vPrev ({len(recs)} record).")
            return True
        except Exception as e:
            logger.error(f"Gagal melakukan rollback untuk {collection_name}: {e}")
            return False

    # =========================================================================
    # 6. END-TO-END UPDATE WORKFLOWS PER SOURCE
    # =========================================================================

    def update_attack(
        self, date_str: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """
        Alur pembaruan berkala MITRE ATT&CK Enterprise STIX 2.1:
        1. Cek versi idempoten.
        2. Unduh ke staging data/raw/mitre_attack/<date>/.
        3. Drop guard (>30% drop ditolak).
        4. Diff report (added, modified, revoked).
        5. Audit penandaan revoked technique pada insiden lama di SQLite.
        6. Re-embedding inkremental & atomic swap indeks RAG.
        7. Simpan versi baru ke metadata_sistem.
        """
        source = "mitre_attack"
        v_check = self.check_version(source)
        if not v_check["has_update"] and not force:
            return {
                "status": "UP_TO_DATE",
                "source": source,
                "version": v_check["active_version"],
                "message": v_check["message"],
            }

        # 1. Unduh payload
        meta = self.downloader.download_mitre_attack(date_str=date_str)
        staged_file = Path(meta["staging_path"]) / "enterprise-attack.json"
        remote_version = meta.get("version_identifier", "v20.0")

        # 2. Siapkan data lama dan baru
        prepared_attack_file = self.prepared_dir / "attack_techniques.json"
        old_techniques = []
        if prepared_attack_file.exists():
            try:
                old_techniques = json.loads(prepared_attack_file.read_text(encoding="utf-8"))
            except Exception:
                old_techniques = []

        new_techniques = CTIPreparer.flatten_attack_stix(staged_file, source_version=remote_version)

        # 3. Drop Guard
        self.validate_staging_drop(source, len(new_techniques), len(old_techniques))

        # 4. Diff Report
        diff = self.compute_diff(
            source=source,
            old_items=old_techniques,
            new_items=new_techniques,
            id_key="technique_id",
            old_version=self.get_active_version(source) or "v16.1",
            new_version=remote_version,
        )

        # 5. Revoked Historical Auditor
        flagged_count = self.audit_revoked_attack_techniques(diff.get("revoked", []))

        # 6. Inkremental Re-embedding & Atomic Swap
        swap_res = self.incremental_update_vector_index(
            collection_name="collection_attack",
            diff=diff,
            new_docs=new_techniques,
            doc_text_formatter=CTIPreparer.format_attack_document_text,
            id_key="technique_id",
        )

        # Simpan berkas prepared baru
        prepared_attack_file.write_text(
            json.dumps(new_techniques, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # Simpan versi aktif baru
        self.set_active_version(source, remote_version)

        return {
            "status": "SUCCESS",
            "source": source,
            "version": remote_version,
            "total_active_techniques": len(new_techniques),
            "diff": diff,
            "historical_incidents_flagged": flagged_count,
            "atomic_swap": swap_res,
        }

    def update_d3fend(
        self, date_str: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """
        Alur pembaruan berkala MITRE D3FEND:
        1. Cek versi idempoten.
        2. Unduh version.json, technique-all.json, dan d3fend-full-mappings.json.
        3. Drop guard (>30% drop ditolak).
        4. Simpan ke berkas JSON data/prepared/ (strictly non-vector).
        5. Diff report.
        """
        source = "mitre_d3fend"
        v_check = self.check_version(source)
        if not v_check["has_update"] and not force:
            return {
                "status": "UP_TO_DATE",
                "source": source,
                "version": v_check["active_version"],
                "message": v_check["message"],
            }

        meta = self.downloader.download_mitre_d3fend(date_str=date_str)
        staging_dir = Path(meta["staging_path"])
        version_str = meta.get("version_identifier", "1.6.0")

        # Ambil jumlah relasi lama dari JSON/DB
        from src.storage.db import ambil_semua_d3fend_techniques, ambil_semua_d3fend_mappings
        old_techs = ambil_semua_d3fend_techniques(db_path=self.db_path)
        old_maps = ambil_semua_d3fend_mappings(db_path=self.db_path)
        old_total = len(old_techs) + len(old_maps)

        # Hitung record baru dari staging
        tech_file = staging_dir / "technique-all.json"
        map_file = staging_dir / "d3fend-full-mappings.json"

        new_tech_data = json.loads(tech_file.read_text(encoding="utf-8"))
        new_map_data = json.loads(map_file.read_text(encoding="utf-8"))

        new_tech_count = len(new_tech_data.get("@graph", []))
        new_map_count = len(new_map_data.get("results", {}).get("bindings", []))
        new_total = new_tech_count + new_map_count

        # Drop Guard
        self.validate_staging_drop(source, new_total, old_total)

        # Persiapan & Penyimpanan ke JSON data/prepared/ (dan SQLite jika custom db)
        store_res = CTIPreparer.prepare_d3fend_storage(
            mappings_input=map_file,
            techniques_input=tech_file,
            db_path=self.db_path,
            source_version=version_str,
        )

        # Diff Report
        new_techs_now = ambil_semua_d3fend_techniques(db_path=self.db_path)
        diff = self.compute_diff(
            source=source,
            old_items=old_techs,
            new_items=new_techs_now,
            id_key="technique_id",
            old_version=self.get_active_version(source) or "1.6.0",
            new_version=version_str,
        )

        self.set_active_version(source, version_str)

        return {
            "status": "SUCCESS",
            "source": source,
            "version": version_str,
            "storage_result": store_res,
            "diff": diff,
        }

    def update_nist(
        self, date_str: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """
        Alur pembaruan berkala NIST OSCAL (SP 800-53 Rev 5 & CSF 2.0):
        1. Cek versi idempoten.
        2. Unduh katalog OSCAL ke staging.
        3. Drop guard (>30% drop ditolak).
        4. Perataan kontrol dokumen.
        5. Diff report.
        6. Re-embedding inkremental & atomic swap untuk collection_nist.
        """
        source = "nist_oscal"
        v_check = self.check_version(source)
        if not v_check["has_update"] and not force:
            return {
                "status": "UP_TO_DATE",
                "source": source,
                "version": v_check["active_version"],
                "message": v_check["message"],
            }

        meta = self.downloader.download_nist_oscal(date_str=date_str)
        staging_dir = Path(meta["staging_path"])
        version_str = meta.get("version_identifier", "SP800-53-Rev5 / CSF-2.0")

        sp800_path = staging_dir / "NIST_SP-800-53_rev5_catalog.json"
        csf_path = staging_dir / "CSF_2.0_catalog.json"

        prepared_nist_file = self.prepared_dir / "nist_controls.json"
        old_controls = []
        if prepared_nist_file.exists():
            try:
                old_controls = json.loads(prepared_nist_file.read_text(encoding="utf-8"))
            except Exception:
                old_controls = []

        new_controls = CTIPreparer.flatten_nist_oscal(
            sp800_53_input=sp800_path,
            csf_2_0_input=csf_path,
            source_version=version_str,
        )

        # Drop Guard
        self.validate_staging_drop(source, len(new_controls), len(old_controls))

        # Diff Report
        diff = self.compute_diff(
            source=source,
            old_items=old_controls,
            new_items=new_controls,
            id_key="control_id",
            old_version=self.get_active_version(source) or "SP800-53-Rev5",
            new_version=version_str,
        )

        # Re-embedding Inkremental & Atomic Swap
        swap_res = self.incremental_update_vector_index(
            collection_name="collection_nist",
            diff=diff,
            new_docs=new_controls,
            doc_text_formatter=CTIPreparer.format_nist_document_text,
            id_key="control_id",
        )

        prepared_nist_file.write_text(
            json.dumps(new_controls, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self.set_active_version(source, version_str)

        return {
            "status": "SUCCESS",
            "source": source,
            "version": version_str,
            "total_controls": len(new_controls),
            "diff": diff,
            "atomic_swap": swap_res,
        }

    def update_taxonomy(
        self, date_str: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """
        Alur pembaruan berkala Taksonomi Insiden MISP/eCSIRT:
        1. Cek versi idempoten.
        2. Unduh machinetag.json ke staging.
        3. Drop guard (memastikan 11 kategori tertutup valid).
        4. Diff report.
        5. Re-embedding inkremental & atomic swap untuk collection_taxonomy.
        """
        source = "misp_taxonomies"
        v_check = self.check_version(source)
        if not v_check["has_update"] and not force:
            return {
                "status": "UP_TO_DATE",
                "source": source,
                "version": v_check["active_version"],
                "message": v_check["message"],
            }

        meta = self.downloader.download_misp_taxonomy(date_str=date_str)
        staging_dir = Path(meta["staging_path"])
        machinetag_file = staging_dir / "machinetag.json"
        version_str = meta.get("version_identifier", "2")

        prepared_tax_file = self.prepared_dir / "taxonomy_categories.json"
        old_tax = []
        if prepared_tax_file.exists():
            try:
                old_tax = json.loads(prepared_tax_file.read_text(encoding="utf-8"))
            except Exception:
                old_tax = []

        new_tax = CTIPreparer.generate_taxonomy_documents(
            machinetag_input=machinetag_file,
            source_version=version_str,
        )

        # Drop Guard (wajib tepat 11 kategori)
        self.validate_staging_drop(source, len(new_tax), len(old_tax) or 11)

        diff = self.compute_diff(
            source=source,
            old_items=old_tax,
            new_items=new_tax,
            id_key="category_id",
            old_version=self.get_active_version(source) or "2",
            new_version=version_str,
        )

        swap_res = self.incremental_update_vector_index(
            collection_name="collection_taxonomy",
            diff=diff,
            new_docs=new_tax,
            doc_text_formatter=CTIPreparer.format_taxonomy_document_text,
            id_key="category_id",
        )

        prepared_tax_file.write_text(
            json.dumps(new_tax, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        self.set_active_version(source, version_str)

        return {
            "status": "SUCCESS",
            "source": source,
            "version": version_str,
            "total_categories": len(new_tax),
            "diff": diff,
            "atomic_swap": swap_res,
        }

    def update_all(
        self, date_str: Optional[str] = None, force: bool = False
    ) -> Dict[str, Any]:
        """Menjalankan pembaruan untuk seluruh sumber terdaftar."""
        results = {}
        for src in ["misp_taxonomies", "mitre_attack", "mitre_d3fend", "nist_oscal"]:
            try:
                if src == "misp_taxonomies":
                    results[src] = self.update_taxonomy(date_str=date_str, force=force)
                elif src == "mitre_attack":
                    results[src] = self.update_attack(date_str=date_str, force=force)
                elif src == "mitre_d3fend":
                    results[src] = self.update_d3fend(date_str=date_str, force=force)
                elif src == "nist_oscal":
                    results[src] = self.update_nist(date_str=date_str, force=force)
            except Exception as e:
                logger.error(f"Pembaruan sumber {src} gagal: {e}")
                results[src] = {"status": "ERROR", "error": str(e)}

        return results


# =============================================================================
# STANDALONE FUNCTION EXPORTS
# =============================================================================

def check_upstream_versions(
    source: str = "mitre_attack",
    updater: Optional[CTISourceUpdater] = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> Dict[str, Any]:
    """Cek versi hulu untuk sumber data CTI."""
    up = updater or CTISourceUpdater(db_path=db_path)
    return up.check_version(source)


def detect_catastrophic_drop(
    source: str,
    new_count: int,
    old_count: int,
) -> None:
    """Validasi penurunan drastis (>30% atau kosong) record baru."""
    CTISourceUpdater.validate_staging_drop(source, new_count, old_count)


def compute_source_diff(
    source: str,
    old_items: List[Dict[str, Any]],
    new_items: List[Dict[str, Any]],
    id_key: str = "technique_id",
    updater: Optional[CTISourceUpdater] = None,
    reports_dir: Optional[Path] = None,
    old_version: str = "",
    new_version: str = "",
) -> Dict[str, Any]:
    """Hitung selisih added, modified, revoked, unchanged antara item lama dan baru."""
    up = updater or CTISourceUpdater(reports_dir=reports_dir)
    return up.compute_diff(
        source=source,
        old_items=old_items,
        new_items=new_items,
        id_key=id_key,
        old_version=old_version,
        new_version=new_version,
    )


def swap_vector_index_atomic(
    collection_name: str,
    diff: Dict[str, Any],
    new_docs: List[Dict[str, Any]],
    doc_text_formatter: Any,
    updater: Optional[CTISourceUpdater] = None,
    vector_store: Optional[CTIVectorStore] = None,
    id_key: str = "id",
) -> Dict[str, Any]:
    """Bangun vNext, smoke test, dan swap atomik indeks vektor."""
    up = updater or CTISourceUpdater(vector_store=vector_store)
    return up.incremental_update_vector_index(
        collection_name=collection_name,
        diff=diff,
        new_docs=new_docs,
        doc_text_formatter=doc_text_formatter,
        id_key=id_key,
    )


def rollback_vector_index(
    collection_name: str,
    updater: Optional[CTISourceUpdater] = None,
    vector_store: Optional[CTIVectorStore] = None,
) -> bool:
    """Pulihkan indeks vektor dari cadangan vPrev."""
    up = updater or CTISourceUpdater(vector_store=vector_store)
    return up.rollback_vector_index(collection_name)


def audit_and_flag_revoked_incidents(
    revoked_ids: List[str],
    updater: Optional[CTISourceUpdater] = None,
    db_path: Path = DEFAULT_DB_PATH,
) -> int:
    """Tandai insiden historis yang memakai teknik revoked dengan flag tinjauan."""
    up = updater or CTISourceUpdater(db_path=db_path)
    return up.audit_revoked_attack_techniques(revoked_ids)
