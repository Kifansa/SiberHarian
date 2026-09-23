from tests.test_25_case_studies import CASE_STUDIES
from src.analytics.cti_agents import jalankan_pipeline_multi_agent
from unittest.mock import patch

def mock_ollama(prompt_sys, prompt_user, model, num_predict):
    if "MAKRO" in prompt_sys:
        return "Sektor Administrasi Pemerintahan diserang oleh Sindikat Anonim menggunakan Malware Baru yang menyebabkan kebocoran data."
    elif "MIKRO" in prompt_sys:
        return "- **" + CASE_STUDIES[0]["top3_mikro"][0]["nama_insiden"] + "**: Menyerang **sektor publik**. Penyerangan dilancarkan oleh **Aktor Anonim** menggunakan **Vektor Serangan**, yang menimbulkan dampak kerugian berupa **Dampak Kerugian Nyata**."
    elif "VEKTOR" in prompt_sys:
        return "- **Alur Serangan " + CASE_STUDIES[0]["top3_mikro"][0]["nama_insiden"] + "**: Uraian penetrasi awal. Vektor ini terpetakan pada **MITRE ATT&CK T1190**."
    elif "EMERGING" in prompt_sys:
        return "**" + CASE_STUDIES[0]["ancaman_baru"]["nama"] + "** adalah ancaman baru pada Sektor Publik."
    return ""

with patch("src.analytics.cti_agents._call_ollama_text", side_effect=mock_ollama):
    sitrep, _ = jalankan_pipeline_multi_agent(CASE_STUDIES[0]["data_makro"], CASE_STUDIES[0]["top3_mikro"], CASE_STUDIES[0]["ancaman_baru"], mode="modular_llm")
    print("SITREP:")
    print(sitrep)
