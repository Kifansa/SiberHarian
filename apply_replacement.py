import re

with open("src/analytics/cti_agents.py", "r", encoding="utf-8") as f:
    content = f.read()

with open("replacement.py", "r", encoding="utf-8") as f:
    replacement = f.read()

# Replace _generate_section_1_makro
content = re.sub(
    r"def _generate_section_1_makro\(data_makro: Dict\[str, Any\], model: str = \"llama3\.2\"\) -> str:.*?return hasil_bersih",
    "",
    content, flags=re.DOTALL
)

# Replace _generate_section_2_mikro
content = re.sub(
    r"def _generate_section_2_mikro\(top3_mikro: List\[Dict\[str, Any\]\], model: str = \"llama3\.2\"\) -> str:.*?return hasil_bersih",
    "",
    content, flags=re.DOTALL
)

# Replace _generate_section_3_vektor
content = re.sub(
    r"def _generate_section_3_vektor\(top3_mikro: List\[Dict\[str, Any\]\], model: str = \"llama3\.2\"\) -> str:.*?return hasil_bersih",
    "",
    content, flags=re.DOTALL
)

# Replace _generate_section_5_emerging
content = re.sub(
    r"def _generate_section_5_emerging\(ancaman_baru: Dict\[str, Any\], model: str = \"llama3\.2\"\) -> str:.*?return hasil_bersih",
    "",
    content, flags=re.DOTALL
)

# Find where to insert replacements: right before jalankan_pipeline_multi_agent
parts = content.split("def jalankan_pipeline_multi_agent(")
new_content = parts[0] + replacement + "\n\ndef jalankan_pipeline_multi_agent(" + parts[1]

# Fix typing imports if needed
new_content = new_content.replace("Dict[str, Any]", "dict").replace("List[Dict[str, Any]]", "list")

with open("src/analytics/cti_agents.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Applied replacements")
