with open("tests/test_25_case_studies.py", "r", encoding="utf-8") as f:
    content = f.read()

# Replace the mock inside the test file
new_mock = """
        def mock_ollama(prompt_sys, prompt_user, model, num_predict):
            if "MAKRO" in prompt_sys or "ancaman siber MAKRO" in prompt_sys:
                return "Sektor Administrasi Pemerintahan diserang oleh Sindikat Anonim menggunakan Malware Baru yang menyebabkan kebocoran data."
            elif "MIKRO" in prompt_sys or "Top 3" in prompt_sys and "alur" not in prompt_sys:
                return "- **" + cs["top3_mikro"][0]["nama_insiden"] + "**: Menyerang **Sektor Publik**. Penyerangan dilancarkan oleh **Aktor Anonim** menggunakan **Vektor Serangan**, yang menimbulkan dampak kerugian berupa **Dampak Kerugian Nyata**."
            elif "VEKTOR" in prompt_sys or "alur kronologi" in prompt_sys:
                return "- **Alur Serangan " + cs["top3_mikro"][0]["nama_insiden"] + "**: Uraian penetrasi awal. Vektor ini terpetakan pada **MITRE ATT&CK T1190**."
            elif "EMERGING" in prompt_sys or "sinyal ancaman siber baru" in prompt_sys:
                return "**" + cs["ancaman_baru"]["nama"] + "** adalah ancaman baru pada Sektor Publik."
            return ""
"""

import re
content = re.sub(
    r"def mock_ollama\(prompt_sys, prompt_user, model, num_predict\):.*?return \"\"\s+",
    new_mock.strip() + "\n",
    content, flags=re.DOTALL
)

with open("tests/test_25_case_studies.py", "w", encoding="utf-8") as f:
    f.write(content)
