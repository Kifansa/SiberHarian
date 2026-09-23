import os
import yaml

base_dir = r'D:\penting\magang\kominfo\NOTIFIKASI-BERITA'
config_dir = os.path.join(base_dir, 'config')
rules_dir = os.path.join(config_dir, 'rules')
prompts_dir = os.path.join(config_dir, 'prompts')
os.makedirs(rules_dir, exist_ok=True)
os.makedirs(prompts_dir, exist_ok=True)

cti_analysis_config = ""
# === CTI Analysis Settings ===
cti_analysis:
  llm:
    model: "llama3.2"
    temperature: 0.1
    num_predict:
      section_makro: 350
      section_mikro: 500
      section_vektor: 450
      section_emerging: 300
      section_cve: 400
    truncation:
      korpus_max: 1500
      fakta_max: 400
      uraian_ancaman_max: 1000
      cve_context_max: 1000
    validation:
      min_length_default: 50
      min_length_mikro: 60
      min_length_vektor: 60
      min_length_emerging: 40

  rag:
    scoring:
      title_match_weight: 3
      body_match_weight: 1
      vector_match_weight: 1
    clustering:
      fuzzy_threshold: 65
      top_n_results: 3
    emerging_threat:
      min_word_length: 4
      growth_threshold: 20.0
    truncation:
      berita_preview: 220
      cve_preview: 200
      regional_preview: 180

  threat_posture:
    formula:
      incident_coeff: 0.035
      cve_coeff: 0.012
      cvss_coeff: 0.35
    levels:
      kritis: 8.0
      tinggi: 6.0
      sedang: 4.0
    trend_thresholds:
      meningkat: 5.0
      menurun: -5.0
    urgency:
      kritis_count: 4
      kritis_growth: 50.0

  vendor_significance:
    min_count: 2
    min_growth: 15.0

  pasca_proses:
    retention_days: 14
    blacklist_values:
      - "-"
      - "(lihat deskripsi)"
      - "Lainnya / Belum Teridentifikasi"
""

with open(os.path.join(config_dir, 'config.yaml'), 'a', encoding='utf-8') as f:
    f.write("\n" + cti_analysis_config)
