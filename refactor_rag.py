import re

path = 'src/analytics/rag_engine.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add config import
if 'from src.utils.config_loader import ConfigLoader' not in content:
    content = re.sub(
        r'(import pandas as pd)',
        r'\1\nfrom src.utils.config_loader import ConfigLoader',
        content
    )

# 1. Scoring weights
scoring_str = '''            # Pembobotan
            rag_cfg = ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {})
            w_title = rag_cfg.get("scoring", {}).get("title_match_weight", 3)
            w_body = rag_cfg.get("scoring", {}).get("body_match_weight", 1)
            w_vector = rag_cfg.get("scoring", {}).get("vector_match_weight", 1)

            for kw in kw_set:
                if kw in judul.lower():
                    score += w_title
                elif kw in teks_gabung:
                    score += w_body

            for vec in vector_set:
                if vec in teks_gabung:
                    score += w_vector'''

content = re.sub(
    r'# Pembobotan\s*for kw in kw_set:.*?score \+= 1',
    scoring_str.strip(),
    content, flags=re.DOTALL
)

# 2. Fuzzy threshold in ambil_top3_insiden_mikro
# original: if fuzz.token_set_ratio(t1, t2) >= 65:
content = re.sub(
    r'if fuzz\.token_set_ratio\(t1, t2\) >= 65:',
    r'if fuzz.token_set_ratio(t1, t2) >= ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("clustering", {}).get("fuzzy_threshold", 65):',
    content
)

# 3. Top N results in ambil_top3_insiden_mikro
# original: return insiden_terkini[:3]
content = re.sub(
    r'return insiden_terkini\[:3\]',
    r'top_n = ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("clustering", {}).get("top_n_results", 3)\n        return insiden_terkini[:top_n]',
    content
)

# 4. Truncation limits
# berita_preview: 220
content = re.sub(r'ringkasan\[:220\]', r'ringkasan[:ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("truncation", {}).get("berita_preview", 220)]', content)
# cve_preview: 200
content = re.sub(r'narasi\[:200\]', r'narasi[:ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("truncation", {}).get("cve_preview", 200)]', content)
# regional_preview: 180
content = re.sub(r'ringkasan\[:180\]', r'ringkasan[:ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("truncation", {}).get("regional_preview", 180)]', content)

# 5. Emerging threat threshold
# original: growth >= 20.0
content = re.sub(
    r'if float\(p.get\("growth_persen", 0\)\) >= 20\.0:',
    r'if float(p.get("growth_persen", 0)) >= ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("emerging_threat", {}).get("growth_threshold", 20.0):',
    content
)
# word length: [A-Za-z]{4,}
content = re.sub(
    r're\.findall\(r"\\b\[A-Za-z\]\{4,\}\\b"',
    r're.findall(r"\\b[A-Za-z]{" + str(ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("emerging_threat", {}).get("min_word_length", 4)) + r",}\\b"',
    content
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("rag_engine refactored")
