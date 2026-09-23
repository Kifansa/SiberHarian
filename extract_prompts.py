import os
import sys

base_dir = r'D:\penting\magang\kominfo\NOTIFIKASI-BERITA'
sys.path.insert(0, base_dir)

from src.analytics.cti_agents import (
    SYSTEM_PROMPT_SEC1_MAKRO,
    SYSTEM_PROMPT_SEC2_MIKRO,
    SYSTEM_PROMPT_SEC3_VEKTOR,
    SYSTEM_PROMPT_SEC5_EMERGING,
    SYSTEM_PROMPT_CVE_SEC1_VENDOR,
    SYSTEM_PROMPT_CVE_SEC2_VEKTOR,
    SYSTEM_PROMPT_CVE_SEC3_KRIPTO
)

prompts_dir = os.path.join(base_dir, 'config', 'prompts')
os.makedirs(prompts_dir, exist_ok=True)

prompts = {
    'section_1_makro': SYSTEM_PROMPT_SEC1_MAKRO,
    'section_2_mikro': SYSTEM_PROMPT_SEC2_MIKRO,
    'section_3_vektor': SYSTEM_PROMPT_SEC3_VEKTOR,
    'section_5_emerging': SYSTEM_PROMPT_SEC5_EMERGING,
    'cve_sec1_vendor': SYSTEM_PROMPT_CVE_SEC1_VENDOR,
    'cve_sec2_vektor': SYSTEM_PROMPT_CVE_SEC2_VEKTOR,
    'cve_sec3_kripto': SYSTEM_PROMPT_CVE_SEC3_KRIPTO
}

for name, content in prompts.items():
    with open(os.path.join(prompts_dir, f"{name}.txt"), 'w', encoding='utf-8') as f:
        f.write(content)

print('Prompts extracted')
