import re

path = 'src/analytics/trend_predictor.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add config import
if 'from src.utils.config_loader import ConfigLoader' not in content:
    content = re.sub(
        r'(import pandas as pd)',
        r'\1\nfrom src.utils.config_loader import ConfigLoader',
        content
    )

# 1. Remove SYSTEM_PROMPT_TREN_BERITA and SYSTEM_PROMPT_TREN_CVE
content = re.sub(r'SYSTEM_PROMPT_TREN_BERITA\s*=\s*""".*?"""', '', content, flags=re.DOTALL)
content = re.sub(r'SYSTEM_PROMPT_TREN_CVE\s*=\s*""".*?"""', '', content, flags=re.DOTALL)

# 2. Update _panggil_llm to use config for model
content = re.sub(
    r'def _panggil_llm\(system_prompt: str, user_prompt: str, model: str\) -> Optional\[str\]:',
    r'def _panggil_llm(system_prompt: str, user_prompt: str, model: str = None) -> Optional[str]:\n    if not model:\n        model = ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {}).get("model", "llama3.2")',
    content
)

# 3. Use ConfigLoader in prediksi_tren_berita
content = re.sub(
    r'hasil_llm = _panggil_llm\(SYSTEM_PROMPT_TREN_BERITA, user_prompt, model\)',
    r'hasil_llm = _panggil_llm(ConfigLoader.get_prompt("trend_berita"), user_prompt, model)',
    content
)

# 4. Use ConfigLoader in prediksi_tren_cve
content = re.sub(
    r'hasil_llm = _panggil_llm\(SYSTEM_PROMPT_TREN_CVE, user_prompt, model\)',
    r'hasil_llm = _panggil_llm(ConfigLoader.get_prompt("trend_cve"), user_prompt, model)',
    content
)

# 5. normalisasi_isu_utama to use rules
norm_replace = r'''def _normalisasi_isu_utama(teks_isu: str, default: str = "Insiden Keamanan Siber") -> str:
    rules = ConfigLoader.get_rules("normalisasi_isu")
    if not rules:
        return default
    t = teks_isu.lower()
    for isu, keywords in rules.items():
        if any(kw in t for kw in keywords):
            return isu
    return default'''
content = re.sub(
    r'def _normalisasi_isu_utama.*?return default',
    norm_replace,
    content, flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("trend_predictor refactored")
