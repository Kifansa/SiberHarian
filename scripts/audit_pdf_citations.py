import pypdf
import os
import sys

# Set output encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

ref_dir = os.path.join('LAPORAN DASHBOARD ADMIN', 'REFERENSI')

papers = [
    ('1. Ariyaningsih et al. (2023)', 'KORELASI KEJAHATAN SIBER DENGAN PERCEPATAN  DIGITALISASI DI INDONESIA.pdf', 'With the acceleration of digitalization'),
    ('2. Parulian et al. (2021)', 'Ancaman dan Solusi Serangan Siber di Indonesia.pdf', '741.441.648'),
    ('3. Fajar et al. (2025)', '2155-5232-2-PB.pdf', 'Pusat Data Nasional Sementara'),
    ('4. Kurniati (2024)', 'Kajian Peran Artificial Intelligence untuk Memperkuat Keamanan Siber pada  Infrastruktur Informasi Vital.pdf', 'Setiap detik yang terlewat'),
    ('5. Hartanto et al. (2025)', 'Model Prediksi Keamanan Siber Menggunakan Artificial Intelligence untuk Mitigasi Ancaman Digital.pdf', 'infrastruktur digital pemerintah'),
    ('6. Hadie et al. (2025)', '47_ID5153_2420-2433.pdf', '100% score across accuracy'),
    ('7. Arazzi et al. (2025)', '1-s2.0-S1574013725000413-main.pdf', 'Cyber Threat Intelligence (CTI) is related to all'),
    ('8. Alhuzali (2025)', 'peerj-cs-3371.pdf', 'manually investigating cyberattacks'),
    ('9. Othman et al. (2026)', '2602.19606v1.pdf', 'achieving 80% with the first listed vulnerability'),
    ('10. Almahmoud et al. (2024)', '1-s2.0-S0040162524006346-main.pdf', 'cyber-attack trend forecasting predominantly relies'),
    ('11. Loumachi et al. (2025)', 'Advancing Cyber Incident Timeline Analysis Through Retrieval-Augmented Generation and Large Language Models.pdf', 'produce fictitious timestamps'),
    ('12. Gandhi (2023)', 'RAG-Driven Cybersecurity Intelligence Leveraging Semantic Search for Improved  Threat Detection.pdf', 'Retrieval-Augmented Generation (RAG) unifies dense retrieval'),
    ('13. Hsieh et al. (2026)', 'A Zero-Touch Vulnerability Remediation Framework Based on OpenVAS, Threat Intelligence, and RAG-Enhanced Large Language Models.pdf', 'raised accuracy from 52.0% to 76.7'),
    ('14. Ismail et al. (2025)', 'Enhancing Security Operations Center Wazuh Security Event Response with Retrieval-Augmented-Generation-Driven Copilot.pdf', 'SERC leverages Wazuh'),
    ('15. Lughbi et al. (2024)', 'A Novel NLP-Driven Dashboard for Interactive CyberAttacks Tweet Classification and Visualization.pdf', 'accuracy up to 97.20%'),
    ('16. Pujiono et al. (2024)', 'evitafitri,+25_Production_5572+(pp+216-223).pdf', 'implementing Retrieval-Augmented Generation and Vector Databases for chatbots in public services agencies'),
    ('17. Paul et al. (2025)', 'LLM-Assisted Proactive Threat Intelligence for Automated Reasoning.pdf', 'integrating large language models (LLMs) and Retrieval-Augmented Generation'),
    ('18. Mahdini et al. (2026)', 'Chatbot Generative AI Berbasis Hybrid RAG dengan Integrasi RIASEC  untuk Rekomendasi Jurusan.pdf', 'Context Recall sebesar 0,97'),
    ('19. Dinis et al. (2025)', 'Large Language Models for Explainable Threat  Intelligence.pdf', 'producing explainable outputs for human security analysts'),
]

print("=== AUDIT VERIFIKASI KALIMAT ASLI PADA SETIAP PDF DI FOLDER REFERENSI ===\n")
all_valid = True
for label, fn, kw in papers:
    fp = os.path.join(ref_dir, fn)
    if not os.path.exists(fp):
        print(f"[FILE NOT FOUND] {label}: {fn}\n")
        all_valid = False
        continue
    reader = pypdf.PdfReader(fp)
    found_page = None
    exact_snippet = None
    for p_idx, page in enumerate(reader.pages):
        text = page.extract_text()
        if kw.lower() in text.lower():
            found_page = p_idx + 1
            idx = text.lower().find(kw.lower())
            start = max(0, idx - 40)
            end = min(len(text), idx + len(kw) + 150)
            exact_snippet = text[start:end].replace('\n', ' ').strip()
            break
    if found_page:
        print(f"[VERIFIED] {label}")
        print(f"  File PDF : {fn}")
        print(f"  Halaman  : {found_page}")
        print(f"  Kutipan  : \"...{exact_snippet}...\"\n")
    else:
        print(f"[KEYWORD MISMATCH] {label} in {fn}\n")
        all_valid = False

print(f"Audit Status All 19 Papers Verified: {all_valid}")
