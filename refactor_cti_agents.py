import re

path = 'src/analytics/cti_agents.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add config import
if 'from src.utils.config_loader import ConfigLoader' not in content:
    content = re.sub(
        r'(import re)',
        r'\1\nfrom src.utils.config_loader import ConfigLoader',
        content
    )

# 1. Remove all SYSTEM_PROMPT_*
content = re.sub(r'SYSTEM_PROMPT_[A-Z0-9_]+\s*=\s*""".*?"""\s*', '', content, flags=re.DOTALL)

# 2. Update _call_ollama_text to use config for model and num_predict
call_replace = r'''def _call_ollama_text(system_prompt: str, user_prompt: str, model: str = None, num_predict: int = 400) -> str:
    cfg = ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {})
    if not model: model = cfg.get("model", "llama3.2")
    temperature = cfg.get("temperature", 0.1)
    
    try:
        r = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            options={"temperature": temperature, "num_predict": num_predict}
        )'''
content = re.sub(
    r'def _call_ollama_text.*?options=\{"temperature": 0\.1, "num_predict": num_predict\}\s*\)',
    call_replace,
    content, flags=re.DOTALL
)

# 3. Replace the PROMPT usages in sections
content = re.sub(r'SYSTEM_PROMPT_SEC1_MAKRO', r'ConfigLoader.get_prompt("section_1_makro")', content)
content = re.sub(r'SYSTEM_PROMPT_SEC2_MIKRO', r'ConfigLoader.get_prompt("section_2_mikro")', content)
content = re.sub(r'SYSTEM_PROMPT_SEC3_VEKTOR', r'ConfigLoader.get_prompt("section_3_vektor")', content)
content = re.sub(r'SYSTEM_PROMPT_SEC5_EMERGING', r'ConfigLoader.get_prompt("section_5_emerging")', content)
content = re.sub(r'SYSTEM_PROMPT_CVE_SEC1_VENDOR', r'ConfigLoader.get_prompt("cve_sec1_vendor")', content)
content = re.sub(r'SYSTEM_PROMPT_CVE_SEC2_VEKTOR', r'ConfigLoader.get_prompt("cve_sec2_vektor")', content)
content = re.sub(r'SYSTEM_PROMPT_CVE_SEC3_KRIPTO', r'ConfigLoader.get_prompt("cve_sec3_kripto")', content)

# 4. Use LLM configuration in sections
# For example, section 1 num_predict
content = re.sub(
    r'num_predict=350',
    r'num_predict=ConfigLoader.get_config().get("cti_analysis", {}).get("llm", {}).get("num_predict", {}).get("section_makro", 350)',
    content
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("cti_agents refactored")
