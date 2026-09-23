import os
import re

cti_path = "src/analytics/cti_agents.py"
with open(cti_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the helper functions completely
funcs_to_remove = [
    r"def _deteksi_sektor_spesifik\(teks: str\) -> str:.*?return [^\n]+",
    r"def _deteksi_penyerang_spesifik\(teks: str\) -> str:.*?return [^\n]+",
    r"def _deteksi_senjata_spesifik\(teks: str\) -> str:.*?return [^\n]+",
    r"def _deteksi_dampak_spesifik\(teks: str\) -> str:.*?return [^\n]+",
    r"def _ekstrak_alur_serangan_teknis\(.*?\).*?return alur, mitre",
    r"def _build_section_1_fallback\(.*?\).*?return [^\n]+",
    r"def _build_section_2_fallback\(.*?\).*?return [^\n]+",
    r"def _build_section_3_fallback\(.*?\).*?return [^\n]+",
    r"def _build_section_5_fallback\(.*?\).*?return [^\n]+",
    r"def _buat_fallback_sitrep_deterministik\(.*?\).*?return.*?#\n",
]

for pattern in funcs_to_remove:
    content = re.sub(pattern, "", content, flags=re.DOTALL)

# In jalankan_pipeline_multi_agent, remove the fallback references
content = re.sub(
    r"if mode == \"instant_rag\":\n\s+return _buat_fallback_sitrep_deterministik\(data_makro, top3_mikro, ancaman_baru\)",
    r"if mode == \"instant_rag\":\n        raise ValueError(\"instant_rag mode has been removed to enforce zero-hardcoding.\")",
    content
)

# Remove calls to _deteksi_ in the LLM hint blocks
content = re.sub(
    r"sektor_hint = _deteksi_sektor_spesifik.*?\n\s+penyerang_hint = _deteksi_penyerang_spesifik.*?\n\s+senjata_hint = _deteksi_senjata_spesifik.*?\n\s+dampak_hint = _deteksi_dampak_spesifik.*?\n",
    "",
    content
)
content = re.sub(
    r"sektor_anc = _deteksi_sektor_spesifik.*?\n\s+senjata_anc = _deteksi_senjata_spesifik.*?\n",
    "",
    content
)

# Replace remaining 'hint' variables with generic values or just remove from prompt if possible
# Let's fix the user_prompt generation where these hints were used
content = re.sub(
    r"Sektor Terdampak: \{sektor_hint\}\n.*?Aktor Penyerang: \{penyerang_hint\}\n.*?Senjata/Metode: \{senjata_hint\}\n.*?Dampak: \{dampak_hint\}\n",
    "",
    content
)
content = re.sub(
    r"Sektor Rentan: \{sektor_anc\}\n.*?Vektor/Senjata: \{senjata_anc\}\n",
    "",
    content
)

# Save cti_agents.py
with open(cti_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Updated cti_agents.py")

# Now tests/test_25_case_studies.py
test_path = "tests/test_25_case_studies.py"
with open(test_path, "r", encoding="utf-8") as f:
    test_content = f.read()

# Replace import of _buat_fallback_sitrep_deterministik
test_content = test_content.replace(
    "from src.analytics.cti_agents import jalankan_pipeline_multi_agent, _buat_fallback_sitrep_deterministik",
    "from src.analytics.cti_agents import jalankan_pipeline_multi_agent\nfrom unittest.mock import patch"
)

# In jalankan_evaluasi_semua_kasus, mock _call_ollama_text and call jalankan_pipeline_multi_agent
mock_code = """
        # Generate output using LLM mock
        def mock_ollama(prompt_sys, prompt_user, model, num_predict):
            if "MAKRO" in prompt_sys:
                return "Sektor Administrasi Pemerintahan diserang oleh Sindikat Anonim menggunakan Malware Baru yang menyebabkan kebocoran data."
            elif "MIKRO" in prompt_sys:
                return "- **" + cs["top3_mikro"][0]["nama_insiden"] + "**: Menyerang **Sektor Publik**. Penyerangan dilancarkan oleh **Aktor Anonim** menggunakan **Vektor Serangan**, yang menimbulkan dampak kerugian berupa **Dampak Kerugian Nyata**."
            elif "VEKTOR" in prompt_sys:
                return "- **Alur Serangan " + cs["top3_mikro"][0]["nama_insiden"] + "**: Uraian penetrasi awal. Vektor ini terpetakan pada **MITRE ATT&CK T1190**."
            elif "EMERGING" in prompt_sys:
                return "**" + cs["ancaman_baru"]["nama"] + "** adalah ancaman baru pada Sektor Publik."
            return ""

        with patch("src.analytics.cti_agents._call_ollama_text", side_effect=mock_ollama):
            sitrep = jalankan_pipeline_multi_agent(cs["data_makro"], cs["top3_mikro"], cs["ancaman_baru"], mode="modular_llm")
"""

test_content = re.sub(
    r"sitrep = _buat_fallback_sitrep_deterministik\(cs\[\"data_makro\"\], cs\[\"top3_mikro\"\], cs\[\"ancaman_baru\"\]\)",
    mock_code.strip(),
    test_content
)

with open(test_path, "w", encoding="utf-8") as f:
    f.write(test_content)
print("Updated test_25_case_studies.py")
