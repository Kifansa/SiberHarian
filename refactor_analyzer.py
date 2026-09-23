import re

path = 'src/analytics/trend_analyzer.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add import at the top
if 'from src.utils.config_loader import ConfigLoader' not in content:
    content = re.sub(
        r'(import pandas as pd)',
        r'\1\nfrom src.utils.config_loader import ConfigLoader',
        content
    )

# 1. Remove VEKTOR_RULES definition
content = re.sub(r'VEKTOR_RULES\s*=\s*\{.*?\}(?=\n\s*\n)', '', content, flags=re.DOTALL)
# 2. Remove SEKTOR_RULES definition
content = re.sub(r'SEKTOR_RULES\s*=\s*\{.*?\}(?=\n\s*\n)', '', content, flags=re.DOTALL)
# 3. Remove _SUMBER_INTERNASIONAL definition
content = re.sub(r'_SUMBER_INTERNASIONAL\s*=\s*\{.*?\}(?=\n\s*\n)', '', content, flags=re.DOTALL)
# 4. Remove _KEYWORDS_JAWA_TIMUR definition
content = re.sub(r'_KEYWORDS_JAWA_TIMUR\s*=\s*\[.*?\](?=\n\s*\n)', '', content, flags=re.DOTALL)

# Inject dynamic fetching inside hitung_tren_vektor_serangan
content = re.sub(
    r'(def hitung_tren_vektor_serangan.*?:\n(?:.*?""")?)',
    r'\1\n    VEKTOR_RULES = ConfigLoader.get_rules("vektor_rules")',
    content, flags=re.DOTALL
)

# Inject dynamic fetching inside hitung_tren_sektor
content = re.sub(
    r'(def hitung_tren_sektor.*?:\n(?:.*?""")?)',
    r'\1\n    SEKTOR_RULES = ConfigLoader.get_rules("sektor_rules")',
    content, flags=re.DOTALL
)

# Replace _SUMBER_INTERNASIONAL reference in _is_international
content = re.sub(
    r'(def _is_international\(publisher: str\) -> bool:)',
    r'\1\n    _SUMBER_INTERNASIONAL = ConfigLoader.get_rules("sumber_internasional")',
    content
)

# Replace _KEYWORDS_JAWA_TIMUR in hitung_kasus_insiden_wilayah
content = re.sub(
    r'_KEYWORDS_JAWA_TIMUR',
    r'ConfigLoader.get_rules("keywords_jawa_timur")',
    content
)
# Wait, _KEYWORDS_JATIM_REGEX compiles _KEYWORDS_JAWA_TIMUR globally.
# Let's remove the global regex and compile it inside hitung_kasus_insiden_wilayah
content = re.sub(
    r'_KEYWORDS_JATIM_REGEX\s*=\s*re\.compile\(\\n.*?\\n\)',
    '',
    content, flags=re.DOTALL
)

# Hardcode removal for threat posture (hitung_postur_ancaman_mingguan)
# (n_insiden * 0.035) + (n_cve * 0.012) + (avg_c * 0.35)
threat_posture_replace = r'''
    cfg = ConfigLoader.get_config().get("cti_analysis", {}).get("threat_posture", {})
    form_cfg = cfg.get("formula", {"incident_coeff": 0.035, "cve_coeff": 0.012, "cvss_coeff": 0.35})
    skor_mentah = (n_insiden * form_cfg["incident_coeff"]) + (n_cve * form_cfg["cve_coeff"]) + (avg_c * form_cfg["cvss_coeff"])
'''
content = re.sub(
    r'skor_mentah\s*=\s*\(n_insiden\s*\*\s*0\.035\)\s*\+\s*\(n_cve\s*\*\s*0\.012\)\s*\+\s*\(avg_c\s*\*\s*0\.35\)',
    threat_posture_replace.strip(),
    content
)

# Hardcode removal for levels
level_replace = r'''
    lvl_cfg = cfg.get("levels", {"kritis": 8.0, "tinggi": 6.0, "sedang": 4.0})
    if skor_mentah >= lvl_cfg["kritis"]:
        level = "KRITIS"
        warna = "red"
    elif skor_mentah >= lvl_cfg["tinggi"]:
        level = "TINGGI"
        warna = "amber"
    elif skor_mentah >= lvl_cfg["sedang"]:
        level = "SEDANG"
        warna = "blue"
    else:
        level = "TERKENDALI"
        warna = "green"
'''
content = re.sub(
    r'if skor_mentah >= 8\.0:.*?else:\s*level = "TERKENDALI"\s*warna = "green"',
    level_replace.strip(),
    content, flags=re.DOTALL
)

# Trend thresholds
trend_replace = r'''
    trend_cfg = cfg.get("trend_thresholds", {"meningkat": 5.0, "menurun": -5.0})
    if diff_growth > trend_cfg["meningkat"]:
        status_tren = "Meningkat Tajam"
    elif diff_growth < trend_cfg["menurun"]:
        status_tren = "Menurun"
    else:
        status_tren = "Relatif Stabil"
'''
content = re.sub(
    r'if diff_growth > 5\.0:.*?else:\s*status_tren = "Relatif Stabil"',
    trend_replace.strip(),
    content, flags=re.DOTALL
)

# For kategori_ancaman_definisi
kat_replace = r'''
    kategori_ancaman_definisi = ConfigLoader.get_rules("kategori_ancaman")
'''
content = re.sub(
    r'kategori_ancaman_definisi\s*=\s*\[.*?\](?=\n\s*matriks = \[\])',
    kat_replace.strip() + '\n',
    content, flags=re.DOTALL
)

# For urgency thresholds
urgency_replace = r'''
        urg_cfg = ConfigLoader.get_config().get("cti_analysis", {}).get("threat_posture", {}).get("urgency", {"kritis_count": 4, "kritis_growth": 50.0})
        if cnt_terkini >= urg_cfg["kritis_count"] or growth >= urg_cfg["kritis_growth"]:
'''
content = re.sub(
    r'if cnt_terkini >= 4 or growth >= 50\.0:',
    urgency_replace.strip(),
    content
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("trend_analyzer refactored")
