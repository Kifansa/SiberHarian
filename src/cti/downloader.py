"""
Modul CTI Downloader & Staging Pipeline.

Bertanggung jawab mengunduh payload sumber CTI resmi secara terverifikasi
ke folder staging data/raw/<sumber>/<YYYY-MM-DD>/ dengan metadata SHA-256,
pengecekan versi, timeout 45 detik, retry exponential backoff 3x,
dukungan proxy, dan mirror internal.
"""

import os
import time
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import requests

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DEFAULT_TIMEOUT = 45
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_FACTOR = 2.0

# URL Resmi Sumber CTI
OFFICIAL_URLS = {
    "misp_taxonomies": {
        "primary": "https://raw.githubusercontent.com/MISP/misp-taxonomies/main/ecsirt/machinetag.json",
        "files": {
            "machinetag.json": "https://raw.githubusercontent.com/MISP/misp-taxonomies/main/ecsirt/machinetag.json"
        },
    },
    "mitre_attack": {
        "primary": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json",
        "files": {
            "enterprise-attack.json": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/master/enterprise-attack/enterprise-attack.json"
        },
    },
    "mitre_d3fend": {
        "version_url": "https://d3fend.mitre.org/api/version.json",
        "techniques_url": "https://d3fend.mitre.org/api/technique/all.json",
        "mappings_pattern": "https://d3fend.mitre.org/ontologies/d3fend/{version}/d3fend-full-mappings.json",
    },
    "nist_oscal": {
        "sp800_53": "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/SP800-53/rev5/json/NIST_SP-800-53_rev5_catalog.json",
        "csf_2_0": "https://raw.githubusercontent.com/usnistgov/oscal-content/main/nist.gov/CSF/v2.0/json/NIST_CSF_v2.0_catalog.json",
    },
}


class DownloadError(Exception):
    """Exception dilempar saat proses unduhan gagal setelah seluruh retry dilakukan."""
    pass


class CTIDownloader:
    """
    Downloader tangguh untuk sumber-sumber threat intelligence resmi:
    MISP eCSIRT, MITRE ATT&CK, MITRE D3FEND, dan NIST OSCAL.
    """

    def __init__(
        self,
        base_staging_dir: Path = DEFAULT_RAW_DIR,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_BACKOFF_FACTOR,
        proxies: Optional[Dict[str, str]] = None,
        mirror_base_url: Optional[str] = None,
    ):
        self.base_staging_dir = Path(base_staging_dir)
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.proxies = proxies or self._get_system_proxies()
        self.mirror_base_url = mirror_base_url.rstrip("/") if mirror_base_url else None
        self.session = requests.Session()
        if self.proxies:
            self.session.proxies.update(self.proxies)

    @staticmethod
    def _get_system_proxies() -> Dict[str, str]:
        """Mengambil konfigurasi proxy dari variabel environment sistem."""
        proxies = {}
        for proto in ("http", "https"):
            val = os.getenv(f"{proto.upper()}_PROXY") or os.getenv(f"{proto}_proxy")
            if val:
                proxies[proto] = val
        return proxies

    def _resolve_url(self, original_url: str) -> str:
        """Mengganti base URL jika mirror internal dikonfigurasi."""
        if not self.mirror_base_url:
            return original_url
        # Jika mirror URL adalah path lokal atau base URL pengganti
        if self.mirror_base_url.startswith("http://") or self.mirror_base_url.startswith("https://"):
            from urllib.parse import urlparse
            parsed = urlparse(original_url)
            return f"{self.mirror_base_url}{parsed.path}"
        return original_url

    def _download_stream_with_retry(
        self, url: str, destination_path: Path
    ) -> Tuple[str, int]:
        """
        Mengunduh berkas dengan chunk streaming, menghitung SHA-256 secara langsung,
        dan melakukan retry exponential backoff jika terjadi kegagalan jaringan.
        Returns: (sha256_hex, file_size_bytes)
        """
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = destination_path.with_suffix(f"{destination_path.suffix}.tmp")
        resolved_url = self._resolve_url(url)

        # Cek jika mirror lokal berbasis filesystem (path direktori lokal)
        if self.mirror_base_url and Path(self.mirror_base_url).is_dir():
            local_candidate = Path(self.mirror_base_url) / destination_path.name
            if local_candidate.exists():
                logger.info(f"Menggunakan mirror lokal untuk {destination_path.name}: {local_candidate}")
                content = local_candidate.read_bytes()
                destination_path.write_bytes(content)
                sha256 = hashlib.sha256(content).hexdigest()
                return sha256, len(content)

        last_exception = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logger.info(
                    f"Mengunduh (attempt {attempt}/{self.max_retries}): {resolved_url} -> {destination_path.name}"
                )
                hasher = hashlib.sha256()
                total_bytes = 0

                headers = {
                    "User-Agent": "SiberHarian-CTI-Ingestion/2.0 (+https://diskominfo.jatimprov.go.id)"
                }
                response = self.session.get(
                    resolved_url,
                    headers=headers,
                    stream=True,
                    timeout=self.timeout,
                )
                response.raise_for_status()

                with open(tmp_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)
                            hasher.update(chunk)
                            total_bytes += len(chunk)

                if total_bytes == 0:
                    raise DownloadError(f"Unduhan menghasilkan berkas kosong (0 bytes) dari {resolved_url}")

                # Atomic rename
                if tmp_path.exists():
                    if destination_path.exists():
                        destination_path.unlink()
                    tmp_path.rename(destination_path)

                sha256_hex = hasher.hexdigest()
                logger.info(
                    f"Unduhan sukses: {destination_path.name} ({total_bytes:,} bytes, SHA-256: {sha256_hex[:12]}...)"
                )
                return sha256_hex, total_bytes

            except Exception as exc:
                last_exception = exc
                logger.warning(
                    f"Percobaan unduh ke-{attempt} gagal untuk {resolved_url}: {exc}"
                )
                if tmp_path.exists():
                    try:
                        tmp_path.unlink()
                    except OSError:
                        pass
                if attempt < self.max_retries:
                    sleep_time = self.backoff_factor ** attempt
                    time.sleep(sleep_time)

        raise DownloadError(
            f"Gagal mengunduh {resolved_url} setelah {self.max_retries} percobaan: {last_exception}"
        )

    def download_misp_taxonomy(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Mengunduh MISP eCSIRT machinetag.json ke folder staging.
        """
        date_folder = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        staging_dir = self.base_staging_dir / "misp_taxonomies" / date_folder
        url = OFFICIAL_URLS["misp_taxonomies"]["primary"]
        dest_file = staging_dir / "machinetag.json"

        sha256, size = self._download_stream_with_retry(url, dest_file)

        # Hitung jumlah predikat dan nilai taksonomi
        record_count = 0
        version_id = "2"
        try:
            with open(dest_file, "r", encoding="utf-8") as f:
                tax_data = json.load(f)
                version_id = str(tax_data.get("version", "2"))
                predicates = tax_data.get("predicates", [])
                for p in predicates:
                    record_count += len(p.get("values", [])) or 1
        except Exception as e:
            logger.warning(f"Gagal membaca record count dari {dest_file.name}: {e}")

        metadata = {
            "source_name": "misp_taxonomies",
            "source_url": url,
            "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "version_identifier": version_id,
            "file_sha256": sha256,
            "file_size_bytes": size,
            "record_count_parsed": record_count,
            "download_status": "SUCCESS",
            "staging_path": str(staging_dir),
            "files": {
                "machinetag.json": {
                    "sha256": sha256,
                    "size_bytes": size,
                    "record_count": record_count,
                }
            },
        }

        meta_file = staging_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata

    def download_mitre_attack(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Mengunduh MITRE ATT&CK Enterprise STIX 2.1 bundle ke folder staging.
        """
        date_folder = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        staging_dir = self.base_staging_dir / "mitre_attack" / date_folder
        url = OFFICIAL_URLS["mitre_attack"]["primary"]
        dest_file = staging_dir / "enterprise-attack.json"

        sha256, size = self._download_stream_with_retry(url, dest_file)

        record_count = 0
        version_id = "v20.0"
        try:
            with open(dest_file, "r", encoding="utf-8") as f:
                stix_data = json.load(f)
                for obj in stix_data.get("objects", []):
                    if obj.get("type") == "x-mitre-collection" and "x_mitre_version" in obj:
                        version_id = f"v{obj['x_mitre_version']}"
                    if obj.get("type") == "attack-pattern":
                        if not obj.get("revoked", False) and not obj.get("x_mitre_deprecated", False):
                            record_count += 1
        except Exception as e:
            logger.warning(f"Gagal memparsing record count dari {dest_file.name}: {e}")

        metadata = {
            "source_name": "mitre_attack",
            "source_url": url,
            "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "version_identifier": version_id,
            "file_sha256": sha256,
            "file_size_bytes": size,
            "record_count_parsed": record_count,
            "download_status": "SUCCESS",
            "staging_path": str(staging_dir),
            "files": {
                "enterprise-attack.json": {
                    "sha256": sha256,
                    "size_bytes": size,
                    "active_techniques_count": record_count,
                }
            },
        }

        meta_file = staging_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata

    def download_mitre_d3fend(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Mengunduh API & relasi D3FEND:
        1. /api/version.json untuk mendeteksi nomor rilis aktif (misal 1.6.0)
        2. /ontologies/d3fend/{version}/d3fend-full-mappings.json untuk relasi ATT&CK -> D3FEND
        3. /api/technique/all.json untuk direktori teknik pertahanan
        """
        date_folder = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        staging_dir = self.base_staging_dir / "mitre_d3fend" / date_folder

        # 1. Unduh version.json
        version_url = OFFICIAL_URLS["mitre_d3fend"]["version_url"]
        dest_version = staging_dir / "version.json"
        ver_sha, ver_size = self._download_stream_with_retry(version_url, dest_version)

        version_str = "1.6.0"
        try:
            with open(dest_version, "r", encoding="utf-8") as f:
                v_data = json.load(f)
                version_str = v_data.get("version", "1.6.0")
        except Exception as e:
            logger.warning(f"Gagal membaca versi D3FEND dari {dest_version.name}: {e}")

        # 2. Unduh technique-all.json
        tech_url = OFFICIAL_URLS["mitre_d3fend"]["techniques_url"]
        dest_tech = staging_dir / "technique-all.json"
        tech_sha, tech_size = self._download_stream_with_retry(tech_url, dest_tech)

        tech_count = 0
        try:
            with open(dest_tech, "r", encoding="utf-8") as f:
                tech_data = json.load(f)
                tech_count = len(tech_data.get("@graph", []))
        except Exception as e:
            logger.warning(f"Gagal membaca teknik D3FEND dari {dest_tech.name}: {e}")

        # 3. Unduh d3fend-full-mappings.json dari endpoint berversi
        mappings_url = OFFICIAL_URLS["mitre_d3fend"]["mappings_pattern"].format(version=version_str)
        dest_mappings = staging_dir / "d3fend-full-mappings.json"
        map_sha, map_size = self._download_stream_with_retry(mappings_url, dest_mappings)

        mapping_count = 0
        try:
            with open(dest_mappings, "r", encoding="utf-8") as f:
                map_data = json.load(f)
                mapping_count = len(map_data.get("results", {}).get("bindings", []))
        except Exception as e:
            logger.warning(f"Gagal membaca jumlah mapping D3FEND: {e}")

        total_records = tech_count + mapping_count
        metadata = {
            "source_name": "mitre_d3fend",
            "source_url": mappings_url,
            "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "version_identifier": version_str,
            "file_sha256": map_sha,
            "file_size_bytes": map_size,
            "record_count_parsed": total_records,
            "download_status": "SUCCESS",
            "staging_path": str(staging_dir),
            "files": {
                "version.json": {"sha256": ver_sha, "size_bytes": ver_size},
                "technique-all.json": {"sha256": tech_sha, "size_bytes": tech_size, "records": tech_count},
                "d3fend-full-mappings.json": {"sha256": map_sha, "size_bytes": map_size, "records": mapping_count},
            },
        }

        meta_file = staging_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata

    def download_nist_oscal(self, date_str: Optional[str] = None) -> Dict[str, Any]:
        """
        Mengunduh katalog resmi NIST OSCAL (SP 800-53 Rev 5 dan CSF 2.0).
        """
        date_folder = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")
        staging_dir = self.base_staging_dir / "nist_oscal" / date_folder

        # 1. SP 800-53 Rev 5
        sp800_url = OFFICIAL_URLS["nist_oscal"]["sp800_53"]
        dest_sp800 = staging_dir / "NIST_SP-800-53_rev5_catalog.json"
        sp800_sha, sp800_size = self._download_stream_with_retry(sp800_url, dest_sp800)

        sp800_count = 0
        try:
            with open(dest_sp800, "r", encoding="utf-8") as f:
                sp_data = json.load(f)
                for grp in sp_data.get("catalog", {}).get("groups", []):
                    sp800_count += len(grp.get("controls", []))
        except Exception as e:
            logger.warning(f"Gagal menghitung kontrol SP 800-53: {e}")

        # 2. CSF 2.0
        csf_url = OFFICIAL_URLS["nist_oscal"]["csf_2_0"]
        dest_csf = staging_dir / "CSF_2.0_catalog.json"
        csf_sha, csf_size = self._download_stream_with_retry(csf_url, dest_csf)

        csf_count = 0
        try:
            with open(dest_csf, "r", encoding="utf-8") as f:
                csf_data = json.load(f)
                for grp in csf_data.get("catalog", {}).get("groups", []):
                    for cat in grp.get("controls", []):
                        csf_count += len(cat.get("controls", [])) or 1
        except Exception as e:
            logger.warning(f"Gagal menghitung kontrol CSF 2.0: {e}")

        total_records = sp800_count + csf_count
        metadata = {
            "source_name": "nist_oscal",
            "source_url": sp800_url,
            "download_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "version_identifier": "SP800-53-Rev5 / CSF-2.0",
            "file_sha256": sp800_sha,
            "file_size_bytes": sp800_size,
            "record_count_parsed": total_records,
            "download_status": "SUCCESS",
            "staging_path": str(staging_dir),
            "files": {
                "NIST_SP-800-53_rev5_catalog.json": {
                    "sha256": sp800_sha,
                    "size_bytes": sp800_size,
                    "controls_count": sp800_count,
                },
                "CSF_2.0_catalog.json": {
                    "sha256": csf_sha,
                    "size_bytes": csf_size,
                    "subcategories_count": csf_count,
                },
            },
        }

        meta_file = staging_dir / "metadata.json"
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata

    def download_all(self, date_str: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Mengunduh seluruh 4 sumber data CTI resmi ke folder staging."""
        results = {}
        logger.info("Memulai pipeline unduh seluruh sumber CTI resmi...")
        results["misp_taxonomies"] = self.download_misp_taxonomy(date_str)
        results["mitre_attack"] = self.download_mitre_attack(date_str)
        results["mitre_d3fend"] = self.download_mitre_d3fend(date_str)
        results["nist_oscal"] = self.download_nist_oscal(date_str)
        logger.info("Selesai mengunduh seluruh sumber CTI resmi ke staging.")
        return results


# Modul fungsi pembungkus (convenience functions)
def download_misp_taxonomy(staging_dir: Path = DEFAULT_RAW_DIR, date_str: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    return CTIDownloader(base_staging_dir=staging_dir, **kwargs).download_misp_taxonomy(date_str)


def download_mitre_attack(staging_dir: Path = DEFAULT_RAW_DIR, date_str: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    return CTIDownloader(base_staging_dir=staging_dir, **kwargs).download_mitre_attack(date_str)


def download_mitre_d3fend(staging_dir: Path = DEFAULT_RAW_DIR, date_str: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    return CTIDownloader(base_staging_dir=staging_dir, **kwargs).download_mitre_d3fend(date_str)


def download_nist_oscal(staging_dir: Path = DEFAULT_RAW_DIR, date_str: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    return CTIDownloader(base_staging_dir=staging_dir, **kwargs).download_nist_oscal(date_str)


def download_all_sources(staging_dir: Path = DEFAULT_RAW_DIR, date_str: Optional[str] = None, **kwargs) -> Dict[str, Dict[str, Any]]:
    return CTIDownloader(base_staging_dir=staging_dir, **kwargs).download_all(date_str)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CTI Official Sources Ingestion Downloader")
    parser.add_argument("--source", choices=["all", "misp", "attack", "d3fend", "nist"], default="all")
    parser.add_argument("--date", help="Tanggal unduh (YYYY-MM-DD)")
    parser.add_argument("--mirror", help="Base URL mirror internal")
    args = parser.parse_args()

    downloader = CTIDownloader(mirror_base_url=args.mirror)
    if args.source == "all":
        res = downloader.download_all(args.date)
    elif args.source == "misp":
        res = downloader.download_misp_taxonomy(args.date)
    elif args.source == "attack":
        res = downloader.download_mitre_attack(args.date)
    elif args.source == "d3fend":
        res = downloader.download_mitre_d3fend(args.date)
    elif args.source == "nist":
        res = downloader.download_nist_oscal(args.date)

    print(json.dumps(res, indent=2, ensure_ascii=False))
