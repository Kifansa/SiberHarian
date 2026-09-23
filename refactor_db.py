import re

path = 'src/storage/db.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'from src.utils.config_loader import ConfigLoader' not in content:
    content = re.sub(
        r'(import sqlite3)',
        r'\1\nfrom src.utils.config_loader import ConfigLoader',
        content
    )

# 1. kategori_map
content = re.sub(
    r'kategori_map\s*=\s*\{.*?\}(?=\n\s*ancaman_counts)',
    r'kategori_map = ConfigLoader.get_rules("publik_statistik").get("kategori_map", {})',
    content, flags=re.DOTALL
)

# 2. kpi_insights
content = re.sub(
    r'kpi_insights\s*=\s*\[.*?\](?=\n\s*# 4\.)',
    r'kpi_insights = ConfigLoader.get_rules("publik_statistik").get("kpi_insights", [])',
    content, flags=re.DOTALL
)

# 3. stop_words
content = re.sub(
    r'stop_words\s*=\s*\{.*?\}',
    r'stop_words = set(ConfigLoader.get_rules("publik_statistik").get("stop_words", []))',
    content, flags=re.DOTALL
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("db.py refactored")
