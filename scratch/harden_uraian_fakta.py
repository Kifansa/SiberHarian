import os

path = "src/analytics/cti_agents.py"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

replacements = [
    ('fakta = inc.get("uraian_fakta", "")', 'fakta = str(inc.get("uraian_fakta") or "")'),
    ('fakta = inc.get("uraian_fakta", "").strip()', 'fakta = str(inc.get("uraian_fakta") or "").strip()'),
    ('str(inc.get("uraian_fakta", ""))', 'str(inc.get("uraian_fakta") or "")'),
]

for old, new in replacements:
    count = content.count(old)
    content = content.replace(old, new)
    print(f"Replaced {count} instances of: {old[:40]}...")

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(content)

print("Update complete.")
