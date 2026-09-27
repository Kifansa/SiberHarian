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

_encyclopedia_cache = {}

def load_encyclopedia(filename: str) -> List[Dict]:
    if filename in _encyclopedia_cache:
        return _encyclopedia_cache[filename]
    try:
        path = os.path.join(ENCYCLOPEDIA_DIR, filename)
        if not os.path.exists(path):
            return []
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            _encyclopedia_cache[filename] = data
            return data
    except Exception as e:
        return []

def _cocok_kata_kunci(keywords_list: List[str], terms_to_check: List[str]) -> bool:
    for kw in keywords_list:
        kw_l = kw.lower()
        for q in terms_to_check:
            if kw_l == q or kw_l in q or q in kw_l:
                return True
    return False

# DRY SEARCH CONFIG
SEARCH_CONFIG = [
    {'name': 'mitre', 'header': 'REFERENSI MITRE ATT&CK:', 'format': lambda e: f"- Taktik {e['tactic']} [{e['id']}]: {e['technique']}"},
    {'name': 'd3fend', 'header': 'REFERENSI MITRE D3FEND:', 'format': lambda e: f"- Mitigasi {e['tactic']} [{e['id']}]: {e['mitigation']}"},
    {'name': 'cis_controls', 'header': 'REFERENSI CIS CONTROLS v8:', 'format': lambda e: f"- Kontrol {e['control']} [{e['id']}]: {e['mitigation']}"},
    {'name': 'bssn', 'header': 'REFERENSI BSSN & REGULASI NASIONAL:', 'format': lambda e: f"- Standar Nasional [{e['id']}] {e['standard']}: {e['mitigation']}"},
    {'name': 'indeks_kami', 'header': 'REFERENSI BSSN INDEKS KAMI (SPBE):', 'format': lambda e: f"- Standar Evaluasi KAMI [{e['id']}] {e['area']}: {e['mitigation']}"},
    {'name': 'nist', 'header': 'REFERENSI NIST CSF 2.0:', 'format': lambda e: f"- Panduan NIST {e['category']}: {e['mitigation']}"},
    {'name': 'cisa_cpg', 'header': 'REFERENSI CISA KEV & CPGs:', 'format': lambda e: f"- Panduan CISA [{e['id']}] {e['standard']}: {e['mitigation']}"},
    {'name': 'iso27001', 'header': 'REFERENSI ISO/IEC 27001:2022:', 'format': lambda e: f"- Kontrol ISO 27001 [{e['id']}] {e['theme']}: {e['mitigation']}"},
    {'name': 'owasp', 'header': 'REFERENSI OWASP TOP 10 / API:', 'format': lambda e: f"- Kerentanan OWASP {e['id']} ({e['category']}): {e['mitigation']}"},
    {'name': 'cwe', 'header': 'REFERENSI CWE TOP WEAKNESSES:', 'format': lambda e: f"- Kelemahan Software {e['id']} ({e['name']}): {e['mitigation']}"},
    {'name': 'csa_ccm', 'header': 'REFERENSI CLOUD SECURITY ALLIANCE (CCM v4):', 'format': lambda e: f"- Kontrol Cloud [{e['id']}] {e['domain']}: {e['mitigation']}"},
    {'name': 'csirt_framework', 'header': 'REFERENSI CSIRT SERVICES FRAMEWORK (FIRST.ORG & BSSN):', 'format': lambda e: f"- Layanan CSIRT [{e['id']}] {e['service']}: {e['mitigation']}"}
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

# LAYER MAPPINGS
INCIDENT_LAYERS = {
    'taktis': [
        ('d3fend', lambda e: f"[{e['id']}] {e['mitigation']}"),
        ('cis_controls', lambda e: f"[{e['id']}] {e['mitigation']}")
    ],
    'standar': [
        ('nist', lambda e: f"[NIST {e['category'].split(' ')[0]}] {e['mitigation']}"),
        ('iso27001', lambda e: f"[{e['id']}] {e['mitigation']}"),
        ('cisa_cpg', lambda e: f"[{e['id']}] {e['mitigation']}")
    ],
    'nasional': [
        ('bssn', lambda e: f"[{e['id']}] {e['mitigation']}"),
        ('indeks_kami', lambda e: f"[{e['id']}] {e['mitigation']}"),
        ('csirt_framework', lambda e: f"[{e['id']}] {e['mitigation']}")
    ],
    'aplikasi': [
        ('owasp', lambda e: f"[OWASP {e['id']}] {e['mitigation']}"),
        ('csa_ccm', lambda e: f"[CSA {e['id']}] {e['mitigation']}")  # Bug fixed here: prefixed with CSA
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
    if rekomendasi['taktis']: hasil.append(rekomendasi['taktis'][0])
    
    if rekomendasi['nasional']: hasil.append(rekomendasi['nasional'][0])
    elif rekomendasi['standar']: hasil.append(rekomendasi['standar'][0])
    
    if len(hasil) < 3:
        if rekomendasi['aplikasi']: hasil.append(rekomendasi['aplikasi'][0])
        elif rekomendasi['standar'] and rekomendasi['standar'][0] not in hasil:
            hasil.append(rekomendasi['standar'][0])
        elif len(rekomendasi['taktis']) > 1: hasil.append(rekomendasi['taktis'][1])
        elif len(rekomendasi['nasional']) > 1: hasil.append(rekomendasi['nasional'][1])

    hasil_unik = list(dict.fromkeys(hasil))
    if not hasil_unik:
        hasil_unik = [
            "[D3-MFA] Wajibkan Multi-Factor Authentication (MFA) berbasis aplikasi authenticator/FIDO2 hardware token untuk seluruh akses administratif dan portal ASN, serta hindari SMS OTP konvensional.",
            "[NIST PR.AA] Terapkan segmentasi jaringan dan audit hak akses berkala (Least Privilege)."
        ]
    return hasil_unik[:3]

def lookup_mitre_technique(identifier_or_query: str) -> Optional[Dict]:
    mitre_db = load_encyclopedia("mitre.json")
    query = identifier_or_query.strip().upper()
    for entry in mitre_db:
        if entry["id"] == query or query in entry["technique"].upper():
            return entry
    return None
