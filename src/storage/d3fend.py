"""Lookup deterministik D3FEND dari berkas prepared JSON."""

import json
from pathlib import Path
import threading
from typing import Dict, List, Optional

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

_ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_PREPARED_DIR = _ROOT_DIR / "data" / "prepared"

_cache_lock = threading.Lock()
_cache: Dict[Path, dict] = {}


def _prepared_dir(prepared_dir: Optional[Path] = None) -> Path:
    return Path(prepared_dir) if prepared_dir else DEFAULT_PREPARED_DIR


def _muat_cache(prepared_dir: Optional[Path] = None) -> Optional[dict]:
    """Memuat indeks mapping dan teknik dari prepared JSON; None bila file tidak ada."""
    p_dir = _prepared_dir(prepared_dir).resolve()
    map_file = p_dir / "d3fend_mappings.json"
    tech_file = p_dir / "d3fend_techniques.json"

    with _cache_lock:
        if p_dir in _cache:
            return _cache[p_dir]
        if not map_file.exists():
            return None

        try:
            raw_maps = json.loads(map_file.read_text(encoding="utf-8"))
            techniques = []
            if tech_file.exists():
                techniques = json.loads(tech_file.read_text(encoding="utf-8"))
            techniques_by_id = {
                str(item.get("technique_id", "")).strip(): item
                for item in techniques
                if item.get("technique_id")
            }

            index: Dict[str, Dict[str, dict]] = {}
            for item in raw_maps:
                attack_id = str(item.get("attack_technique_id", "")).strip()
                technique_id = item.get("technique_id") or item.get("d3fend_technique_id")
                if not attack_id or not technique_id:
                    continue
                detail = techniques_by_id.get(str(technique_id), {})
                entry = {
                    "technique_id": technique_id,
                    "name": detail.get("name") or item.get("name", ""),
                    "tactic": detail.get("tactic") or item.get("tactic", ""),
                    "definition": detail.get("definition") or item.get("definition", ""),
                    "relationship_type": item.get("relationship_type", "mitigates"),
                    "source_version": item.get("source_version", "1.6.0"),
                }
                index.setdefault(attack_id, {})
                index[attack_id].setdefault(technique_id, entry)

            data = {
                "mappings": {
                    attack_id: sorted(items.values(), key=lambda x: x["technique_id"])
                    for attack_id, items in index.items()
                },
                "techniques": techniques,
                "raw_mappings": raw_maps,
            }
            _cache[p_dir] = data
            return data
        except Exception as exc:
            logger.warning(f"Gagal memuat cache D3FEND dari JSON: {exc}")
            return None


def _invalidasi_cache(prepared_dir: Path) -> None:
    with _cache_lock:
        _cache.pop(Path(prepared_dir).resolve(), None)


def simpan_d3fend_techniques(
    techniques: List[dict], prepared_dir: Optional[Path] = None
) -> int:
    """Menulis daftar teknik D3FEND ke prepared JSON."""
    if not techniques:
        return 0
    p_dir = _prepared_dir(prepared_dir)
    p_dir.mkdir(parents=True, exist_ok=True)
    out_file = p_dir / "d3fend_techniques.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(techniques, f, indent=2, ensure_ascii=False)
    _invalidasi_cache(p_dir)
    logger.info(f"Berhasil menyimpan {len(techniques)} teknik D3FEND ke JSON ({out_file}).")
    return len(techniques)


def simpan_d3fend_attack_mappings(
    mappings: List[dict], prepared_dir: Optional[Path] = None
) -> int:
    """Menulis pemetaan ATT&CK ke D3FEND ke prepared JSON tanpa deduplikasi."""
    if not mappings:
        return 0
    p_dir = _prepared_dir(prepared_dir)
    p_dir.mkdir(parents=True, exist_ok=True)
    out_file = p_dir / "d3fend_mappings.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)
    _invalidasi_cache(p_dir)
    logger.info(f"Berhasil menyimpan {len(mappings)} pemetaan D3FEND-ATT&CK ke JSON ({out_file}).")
    return len(mappings)


def ambil_d3fend_mitigasi_by_attack_id(
    attack_technique_id: str, prepared_dir: Optional[Path] = None
) -> List[dict]:
    """Mencari mitigasi deterministik, dengan fallback parent/sub-teknik."""
    if not attack_technique_id:
        return []
    data = _muat_cache(prepared_dir)
    if not data:
        return []
    index = data["mappings"]
    clean_id = attack_technique_id.strip()

    if clean_id in index:
        return [dict(item) for item in index[clean_id]]

    if "." in clean_id:
        parent_id = clean_id.split(".")[0]
        if parent_id in index:
            return [dict(item) for item in index[parent_id]]

    if "." not in clean_id:
        prefix = f"{clean_id}."
        matched: Dict[str, dict] = {}
        for attack_id, items in index.items():
            if attack_id.startswith(prefix):
                for item in items:
                    matched.setdefault(item["technique_id"], item)
        return sorted(matched.values(), key=lambda x: x["technique_id"])
    return []


def ambil_semua_d3fend_techniques(prepared_dir: Optional[Path] = None) -> List[dict]:
    """Mengambil seluruh teknik D3FEND dari prepared JSON."""
    data = _muat_cache(prepared_dir)
    if not data:
        return []
    return [dict(item) for item in data["techniques"]]


def ambil_semua_d3fend_mappings(prepared_dir: Optional[Path] = None) -> List[dict]:
    """Mengambil seluruh pemetaan D3FEND dari prepared JSON."""
    data = _muat_cache(prepared_dir)
    if not data:
        return []
    return [
        {
            "attack_technique_id": item.get("attack_technique_id"),
            "d3fend_technique_id": item.get("d3fend_technique_id") or item.get("technique_id"),
            "relationship_type": item.get("relationship_type", "mitigates"),
            "source_version": item.get("source_version", "1.6.0"),
        }
        for item in data["raw_mappings"]
    ]
