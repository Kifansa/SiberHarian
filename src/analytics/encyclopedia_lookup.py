import json
import os
import re
from typing import Dict, List, Optional, Union

# Constants
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENCYCLOPEDIA_DIR = os.path.join(BASE_DIR, 'data', 'encyclopedia')

FRAMEWORK_REGISTRY = {
    'mitre': 'mitre.json',
    'd3fend': 'd3fend.json',
    'cis_controls': 'cis_controls.json',
    'bssn': 'bssn.json',
    'indeks_kami': 'indeks_kami.json',
    'nist': 'nist.json',
    'cisa_cpg': 'cisa_cpg.json',
    'iso27001': 'iso27001.json',
    'owasp': 'owasp.json',
    'cwe': 'cwe.json',
    'csa_ccm': 'csa_ccm.json',
    'csirt_framework': 'csirt_framework.json'
}

RETIRED_FRAMEWORKS = {
    'cis_controls.json', 'bssn.json', 'indeks_kami.json', 'cisa_cpg.json',
    'iso27001.json', 'owasp.json', 'cwe.json', 'csa_ccm.json', 'csirt_framework.json'
}

_encyclopedia_cache = {}

def load_encyclopedia(filename: str) -> List[Dict]:
    if filename in _encyclopedia_cache:
        return _encyclopedia_cache[filename]
    try:
        # Jika berkas termasuk dalam 9 berkas yang dipensiunkan, kembalikan list kosong secara anggun
        if filename in RETIRED_FRAMEWORKS:
            _encyclopedia_cache[filename] = []
            return []

        path = os.path.join(ENCYCLOPEDIA_DIR, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                _encyclopedia_cache[filename] = data
                return data

        # Fallback resmi ke data aktif jika file JSON lokal tidak ada
        if filename == 'd3fend.json':
            from src.storage.db import ambil_semua_d3fend_techniques
            techs = ambil_semua_d3fend_techniques()
            fallback_d3 = [
                {
                    "id": t["technique_id"],
                    "tactic": t["tactic"],
                    "technique": t["name"],
                    "mitigation": t["definition"] or t["name"],
                    "keywords": [t["name"].lower(), t["technique_id"].lower()]
                }
                for t in techs
            ]
            _encyclopedia_cache[filename] = fallback_d3
            return fallback_d3

        if filename == 'mitre.json':
            prep_attack = os.path.join(BASE_DIR, 'data', 'prepared', 'attack_techniques.json')
            if os.path.exists(prep_attack):
                with open(prep_attack, 'r', encoding='utf-8') as f:
                    at_list = json.load(f)
                fallback_att = [
                    {
                        "id": t.get("technique_id", ""),
                        "tactic": (t.get("tactics") or ["Initial Access"])[0],
                        "technique": t.get("name", ""),
                        "keywords": [t.get("name", "").lower(), t.get("technique_id", "").lower()]
                    }
                    for t in at_list if not t.get("revoked") and not t.get("deprecated")
                ]
                _encyclopedia_cache[filename] = fallback_att
                return fallback_att

        if filename == 'nist.json':
            prep_nist = os.path.join(BASE_DIR, 'data', 'prepared', 'nist_controls.json')
            if os.path.exists(prep_nist):
                with open(prep_nist, 'r', encoding='utf-8') as f:
                    nist_list = json.load(f)
                fallback_nist = [
                    {
                        "function": c.get("family_or_function", "Protect"),
                        "category": c.get("control_id", ""),
                        "mitigation": c.get("title", ""),
                        "keywords": [c.get("title", "").lower(), c.get("control_id", "").lower()]
                    }
                    for c in nist_list
                ]
                _encyclopedia_cache[filename] = fallback_nist
                return fallback_nist

        return []
    except Exception as e:
        return []

def _cocok_kata_kunci(keywords_list: List[str], terms_to_check: List[str]) -> bool:
    for kw in keywords_list:
        kw_l = kw.lower()
        for q in terms_to_check:
            if kw_l == q or kw_l in q or q in kw_l:
                return True
    return False

# DRY SEARCH CONFIG (Hanya sumber resmi MITRE ATT&CK, MITRE D3FEND, dan NIST)
SEARCH_CONFIG = [
    {'name': 'mitre', 'header': 'REFERENSI MITRE ATT&CK:', 'format': lambda e: f"- Taktik {e['tactic']} [{e['id']}]: {e['technique']}"},
    {'name': 'd3fend', 'header': 'REFERENSI MITRE D3FEND:', 'format': lambda e: f"- Mitigasi {e['tactic']} [{e['id']}]: {e['mitigation']}"},
    {'name': 'nist', 'header': 'REFERENSI NIST CSF 2.0:', 'format': lambda e: f"- Panduan NIST {e['category']}: {e['mitigation']}"},
]

def get_all_framework_counts() -> Dict[str, int]:
    counts = {}
    for name, filename in FRAMEWORK_REGISTRY.items():
        data = load_encyclopedia(filename)
        counts[name] = len(data)
    return counts


def search_encyclopedia(query: Union[str, List[str]]) -> str:
    if isinstance(query, list):
        query_lower = [k.lower().strip() for k in query if k and len(k.strip()) > 2]
    else:
        query_lower = [q.strip() for q in query.lower().split() if len(q.strip()) > 2]
    if not query_lower:
        return "(Query terlalu pendek untuk pencarian ensiklopedia)"
    
    hasil_sections = []
    
    for fw in SEARCH_CONFIG:
        db = load_encyclopedia(FRAMEWORK_REGISTRY[fw['name']])
        matches = [fw['format'](e) for e in db if _cocok_kata_kunci(e.get("keywords", []), query_lower)]
        if matches:
            hasil_sections.append(fw['header'] + "\n" + "\n".join(sorted(set(matches))[:3]))
            
    return "\n\n".join(hasil_sections) if hasil_sections else "(Tidak ada kecocokan di database ensiklopedia lokal)"

# LAYER MAPPINGS: Murni MITRE D3FEND dan NIST (tanpa BSSN, SPBE, dll.)
INCIDENT_LAYERS = {
    'd3fend': [
        ('d3fend', lambda e: f"[{e['id']}] {e['mitigation']}")
    ],
    'nist': [
        ('nist', lambda e: f"[NIST {e['category'].split(' ')[0]}] {e['mitigation']}")
    ]
}

def search_encyclopedia_per_incident(nama_insiden: str, keywords_list: List[str]) -> List[str]:
    kw_lower = [k.lower().strip() for k in keywords_list if k and len(k.strip()) > 1]
    
    stop_words = ["yang", "oleh", "pada", "dalam", "untuk", "dari", "dengan", "akan", "telah"]
    for part in re.split(r"[\s\-_/]+", nama_insiden):
        p = part.lower().strip()
        if len(p) > 3 and p not in stop_words:
            kw_lower.append(p)

    rekomendasi = {k: [] for k in INCIDENT_LAYERS.keys()}
    
    for layer, mappings in INCIDENT_LAYERS.items():
        for fw_name, fmt_func in mappings:
            db = load_encyclopedia(FRAMEWORK_REGISTRY[fw_name])
            for e in db:
                if _cocok_kata_kunci(e.get("keywords", []), kw_lower):
                    rekomendasi[layer].append(fmt_func(e))

    hasil = []
    # 1. Rekomendasi pertama: MITRE D3FEND
    if rekomendasi['d3fend']:
        hasil.append(rekomendasi['d3fend'][0])
    else:
        hasil.append("[D3-MFA] Wajibkan Multi-Factor Authentication (MFA) berbasis aplikasi authenticator/FIDO2 hardware token untuk seluruh akses administratif dan portal ASN, serta hindari SMS OTP konvensional.")

    # 2. Rekomendasi kedua: Standar NIST
    if rekomendasi['nist']:
        hasil.append(rekomendasi['nist'][0])
    else:
        hasil.append("[NIST PR.AA-01] Terapkan segmentasi jaringan dan audit hak akses berkala (Least Privilege).")

    # Ambil elemen unik
    hasil_unik = list(dict.fromkeys(hasil))
    return hasil_unik[:2]

def lookup_mitre_technique(identifier_or_query: str) -> Optional[Dict]:
    mitre_db = load_encyclopedia("mitre.json")
    query = identifier_or_query.strip().upper()
    for entry in mitre_db:
        if entry["id"] == query or query in entry["technique"].upper():
            return entry
    return None
