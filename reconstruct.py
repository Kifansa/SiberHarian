import re

with open("src/analytics/cti_agents.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Extract the top part (Imports + Prompts)
top_part_match = re.search(r"^(.*?)(?=# =====================================================================\n# HELPER DETEKSI ENTITAS & VEKTOR \(RULE-BASED GROUND TRUTH\))", content, flags=re.DOTALL)
if not top_part_match:
    print("Top part not found")
top_part = top_part_match.group(1)

# 2. Extract _build_section_4_rekomendasi
rec_match = re.search(r"(def _build_section_4_rekomendasi.*?return \"\\n\\n\"\.join\(poin_rekomendasi\)\n)", content, flags=re.DOTALL)
if not rec_match:
    print("Rec match not found")
rec_func = rec_match.group(1).replace("_build_section_4_rekomendasi", "_generate_section_4_rekomendasi")

# 3. Extract bottom part (_call_ollama_text onwards)
bottom_match = re.search(r"(# =====================================================================\n# MODULAR SECTION RUNNERS.*?)$", content, flags=re.DOTALL)
if not bottom_match:
    print("Bottom match not found")
bottom_part = bottom_match.group(1)

# Assemble
new_content = top_part + "\n\n" + rec_func + "\n\n" + bottom_part

# Clean up bottom part (remove the old _generate_section_4_rekomendasi which just wraps the build func)
new_content = re.sub(r"def _generate_section_4_rekomendasi\(top3_mikro: List\[Dict\[str, Any\]\]\) -> str:\n\s+return _build_section_4_rekomendasi\(top3_mikro\)\n", "", new_content, flags=re.DOTALL)

# Ensure no references to fallback in jalankan_pipeline_multi_agent
new_content = re.sub(
    r"if mode == \"instant_rag\":\n\s+return _buat_fallback_sitrep_deterministik\(data_makro, top3_mikro, ancaman_baru\)",
    r"if mode == \"instant_rag\":\n        raise ValueError(\"instant_rag mode has been removed to enforce zero-hardcoding.\")",
    new_content
)

with open("src/analytics/cti_agents.py", "w", encoding="utf-8") as f:
    f.write(new_content)
print("File successfully reconstructed!")
