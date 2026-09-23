with open("tests/test_25_case_studies.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("Menyerang **Sektor Publik**", "Menyerang **sektor publik**")

with open("tests/test_25_case_studies.py", "w", encoding="utf-8") as f:
    f.write(content)
