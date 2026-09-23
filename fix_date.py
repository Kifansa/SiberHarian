with open("src/analytics/cti_agents.py", "r", encoding="utf-8") as f:
    content = f.read()

if "def _bersihkan_tanggal_jika_ada" not in content:
    func_text = """
def _bersihkan_tanggal_jika_ada(teks: str) -> str:
    import re
    teks = re.sub(r'\\b(pada tanggal|tanggal|pada)\\s+\\d{1,2}\\s+(januari|februari|maret|april|mei|juni|juli|agustus|september|oktober|november|desember|jan|feb|mar|apr|mei|jun|jul|agu|sep|okt|nov|des)\\s*\\d{0,4}\\b', '', teks, flags=re.IGNORECASE)
    return teks
"""
    content = content.replace("def _generate_section_1_makro(", func_text + "\ndef _generate_section_1_makro(")

with open("src/analytics/cti_agents.py", "w", encoding="utf-8") as f:
    f.write(content)
