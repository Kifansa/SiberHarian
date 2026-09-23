import os
import yaml
import sys

base_dir = r'D:\penting\magang\kominfo\NOTIFIKASI-BERITA'
sys.path.insert(0, base_dir)

from src.analytics.trend_analyzer import VEKTOR_RULES, SEKTOR_RULES, _SUMBER_INTERNASIONAL, _KEYWORDS_JAWA_TIMUR
from src.analytics.trend_predictor import SYSTEM_PROMPT_TREN_BERITA, SYSTEM_PROMPT_TREN_CVE

rules_dir = os.path.join(base_dir, 'config', 'rules')
prompts_dir = os.path.join(base_dir, 'config', 'prompts')
os.makedirs(rules_dir, exist_ok=True)
os.makedirs(prompts_dir, exist_ok=True)

# Dump Rules
with open(os.path.join(rules_dir, 'vektor_rules.yaml'), 'w', encoding='utf-8') as f:
    yaml.dump(VEKTOR_RULES, f, sort_keys=False)

# Clean SEKTOR_RULES
clean_sektor = {}
for k, v in SEKTOR_RULES.items():
    if k == 'Administrasi Pemerintahan':
        clean_sektor[k] = [x for x in v if x not in ('tangsel', 'berlin', 'bgn', 'taiwan', 'irs')]
    elif k == 'Keuangan & Perbankan':
        clean_sektor[k] = [x for x in v if x not in ('bitcoin', 'btc', 'coldcard', 'swiss')]
    elif k == 'Teknologi Informasi & Komunikasi (TIK)':
        clean_sektor[k] = [x for x in v if x not in ('apple', 'windows', 'google', 'microsoft', 'cisco')]
    elif k == 'Layanan Publik & Pengguna Digital':
        clean_sektor[k] = [x for x in v if x not in ('gta', 'jungkook', 'iphone')]
    else:
        clean_sektor[k] = v

with open(os.path.join(rules_dir, 'sektor_rules.yaml'), 'w', encoding='utf-8') as f:
    yaml.dump(clean_sektor, f, sort_keys=False)

with open(os.path.join(rules_dir, 'sumber_internasional.yaml'), 'w', encoding='utf-8') as f:
    yaml.dump(list(_SUMBER_INTERNASIONAL), f, sort_keys=False)

with open(os.path.join(rules_dir, 'keywords_jawa_timur.yaml'), 'w', encoding='utf-8') as f:
    yaml.dump(_KEYWORDS_JAWA_TIMUR, f, sort_keys=False)

# Prompts
with open(os.path.join(prompts_dir, 'trend_berita.txt'), 'w', encoding='utf-8') as f:
    f.write(SYSTEM_PROMPT_TREN_BERITA)

with open(os.path.join(prompts_dir, 'trend_cve.txt'), 'w', encoding='utf-8') as f:
    f.write(SYSTEM_PROMPT_TREN_CVE)

print('Done')
