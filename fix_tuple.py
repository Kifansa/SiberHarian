with open("tests/test_25_case_studies.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    "sitrep = jalankan_pipeline_multi_agent(cs[\"data_makro\"], cs[\"top3_mikro\"], cs[\"ancaman_baru\"], mode=\"modular_llm\")",
    "sitrep, _ = jalankan_pipeline_multi_agent(cs[\"data_makro\"], cs[\"top3_mikro\"], cs[\"ancaman_baru\"], mode=\"modular_llm\")"
)

with open("tests/test_25_case_studies.py", "w", encoding="utf-8") as f:
    f.write(content)
