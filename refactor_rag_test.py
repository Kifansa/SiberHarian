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

# 1. replace scoring (title += 3, body += 1, vector += 1)
score_replace = r'''
        cfg = ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {})
        scoring = cfg.get("scoring", {"title_match_weight": 3, "body_match_weight": 1, "vector_match_weight": 1})
        for idx, row in df.iterrows():
            if type_filter and row.get("kategori") != type_filter: continue
            
            score = 0
            t = f"{row.get('judul', '')}".lower()
            b = f"{row.get('ringkasan_atau_narasi', '')} {row.get('kata_kunci', '')}".lower()
            
            if q in t: score += scoring["title_match_weight"]
            elif q in b: score += scoring["body_match_weight"]
            
            # Additional vector matching
            if q in getattr(row, "vektor_serangan", "").lower(): score += scoring["vector_match_weight"]
            if score > 0: candidates.append({"idx": idx, "score": score})
'''
# Using regex to replace the loop body that calculates the score.
# Instead of complex regex, let's just do targeted string replaces.
content = content.replace("score += 3", 'score += ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("scoring", {}).get("title_match_weight", 3)')
content = content.replace("score += 1", 'score += ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("scoring", {}).get("body_match_weight", 1)')
# Wait, "score += 1" appears twice? One for body, one for vector. If I replace it globally, both get body_match_weight.
# Let's just use regex to target them.
