import re

path = 'src/analytics/pasca_proses.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

if 'from src.utils.config_loader import ConfigLoader' not in content:
    content = re.sub(
        r'(import sqlite3)',
        r'\1\nfrom src.utils.config_loader import ConfigLoader',
        content
    )

content = re.sub(
    r'hari_retensi=14',
    r'hari_retensi=ConfigLoader.get_config().get("cti_analysis", {}).get("pasca_proses", {}).get("retention_days", 14)',
    content
)

content = content.replace(
    '["-", "(lihat deskripsi)", "Lainnya / Belum Teridentifikasi"]',
    'ConfigLoader.get_config().get("cti_analysis", {}).get("pasca_proses", {}).get("blacklist_values", ["-", "(lihat deskripsi)", "Lainnya / Belum Teridentifikasi"])'
)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print("pasca_proses refactored")
