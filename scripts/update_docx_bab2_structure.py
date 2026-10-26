import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def update_bab2():
    doc_path = "LAPORAN DASHBOARD ADMIN/Laporan Akhir Capstone Design & Project.docx"
    doc = docx.Document(doc_path)

    # Find BAB II and BAB III
    bab2_idx = None
    bab3_idx = None
    for i, p in enumerate(doc.paragraphs):
        if "BAB II" in p.text.upper() and bab2_idx is None:
            bab2_idx = i
        elif "BAB III" in p.text.upper() and bab3_idx is None:
            bab3_idx = i

    print(f"BAB II at index {bab2_idx}, BAB III at index {bab3_idx}")

    # Remove all paragraphs between BAB II title and BAB III
    # But keep paragraph 65 (BAB II) and insert clean content before BAB III
    p_bab3 = doc.paragraphs[bab3_idx]

    # Delete paragraphs between bab2_idx + 1 and bab3_idx
    for k in range(bab3_idx - 1, bab2_idx, -1):
        p_elem = doc.paragraphs[k]._element
        p_elem.getparent().remove(p_elem)

    # Re-fetch BAB III paragraph after deletions
    for p in doc.paragraphs:
        if "BAB III" in p.text.upper():
            p_bab3 = p
            break

    # Structure data for BAB II
    sections = [
        # (type, number, title, description)
        ("H1", "2.1", "Literatur Terkait Teori, Konsep Umum, Model, dan Kerangka Kerja", 
         "Sub-bab ini menyajikan landasan teoretis, regulasi nasional, konsep komputasi, dan kerangka kerja resmi yang mendasari perancangan sistem Dashboard Admin SiberHarian berbasis Retrieval-Augmented Generation (RAG)."),
        ("H2", "2.1.1", "Tata Kelola Keamanan Siber Sektor Publik dan Perlindungan Infrastruktur Informasi Vital (IIV)",
         "Membahas implementasi Sistem Pemerintahan Berbasis Elektronik (SPBE), mandat Perpres No. 82 Tahun 2022 tentang perlindungan 10 sektor IIV, serta doktrin operasional Computer Security Incident Response Team (CSIRT) dalam menangani insiden dalam hitungan detik."),
        ("H2", "2.1.2", "Cyber Threat Intelligence (CTI) Berbasis OSINT dan Karakteristik Teks Berita Serangan Siber",
         "Menguraikan taksonomi CTI (Strategis, Operasional, Taktis, Teknis), protokol penanganan informasi (TLP:CLEAR), karakteristik 80% data teks tidak terstruktur, mitigasi alert fatigue analis, serta standar kerentanan CVE, CWE, dan keparahan CVSS v3.1."),
        ("H2", "2.1.3", "Natural Language Processing (NLP), Web Scraping Etis, dan Representasi Semantik",
         "Menjelaskan pipeline ingestion otomatis (RSS & Google News), scraping etis (robots.txt, UU Hak Cipta No. 28/2014), kepatuhan privasi (UU PDP No. 27/2022 via PII masking), deduplikasi hybrid (Jaccard & Cosine Similarity), strategi chunking dokumen, serta dense multilingual embeddings."),
        ("H2", "2.1.4", "Keterbatasan Large Language Models (LLMs) dan Isu Halusinasi Faktual (Fact Hallucination)",
         "Menganalisis arsitektur Transformer, batasan memori parametrik, fenomena stochastic parrot, serta risiko halusinasi faktual (stempel waktu fiktif dan artefak digital palsu) pada model generatif tanpa penambatan data."),
        ("H2", "2.1.5", "Arsitektur Retrieval-Augmented Generation (RAG) dan Basis Data Vektor",
         "Menguraikan paradigma RAG (Naive RAG vs Advanced/Modular RAG, dense retrieval, hybrid search BM25 + vektor), basis data vektor (FAISS/ANN Index), serta strategi penambatan fakta (factual grounding) untuk menekan halusinasi."),
        ("H2", "2.1.6", "Kerangka Kerja Keamanan Siber Resmi sebagai Basis Pengetahuan Mitigasi (Official Knowledge Base)",
         "Membedah taksonomi TTP musuh MITRE ATT&CK, taksonomi penangkalan teknis MITRE D3FEND, pemetaan ontologis relasional ATT&CK ke D3FEND, serta integrasi 6 fungsi tata kelola NIST Cybersecurity Framework (NIST CSF 2.0)."),
        ("H2", "2.1.7", "Decision Support System (DSS) dan Perancangan Dashboard Admin Analitik",
         "Membahas teori DSS, prinsip Human-in-the-Loop analis keamanan siber, analisis deret waktu mingguan (Week-over-Week / WoW), deteksi ambang lonjakan (spike threshold), klastering 3 wilayah (Jatim, Nasional, Global), dan CVE Watchlist."),
        ("H2", "2.1.8", "Kerangka Kerja Evaluasi Kualitas RAG (Metrik RAGAS)",
         "Menjelaskan arsitektur pengujian Retrieval-Augmented Generation Assessment (RAGAS) dan formulasi matematis dari 4 dimensi evaluasi: Faithfulness, Answer Relevance, Context Precision, dan Context Recall."),
        
        ("H1", "2.2", "Penelitian Terdahulu (State-of-the-Art) dan Analisis Kesenjangan (Research Gap)",
         "Sub-bab ini membedah penelitian-penelitian terdahulu yang relevan dalam ranah CTI, NLP, dan RAG, serta menyajikan matriks komparatif multi-dimensi guna menegaskan posisi kebaruan (novelty) penelitian ini."),
        ("H2", "2.2.1", "Kajian Komparatif Sistem CTI, NLP, dan Dashboard Keamanan Siber Terdahulu",
         "Menganalisis kelebihan dan keterbatasan sistem sejenis: SERC Copilot SIEM Wazuh (Ismail et al., 2025), NLP Tweet Dashboard (Lughbi et al., 2024), RAG instansi layanan publik (Pujiono et al., 2024; Hadie et al., 2025), dan Proactive CTI RAG (Paul et al., 2025; Alhuzali, 2025)."),
        ("H2", "2.2.2", "Matriks Perbandingan Penelitian Terdahulu dan Posisi Kebaruan (Novelty)",
         "Menyajikan tabel matriks perbandingan komprehensif berdasarkan 8 parameter teknis (sumber data, domain, bahasa, arsitektur RAG, basis pengetahuan defensif D3FEND, visualisasi DSS, metrik RAGAS, lokus instansi) untuk mengunci kebaruan riset."),

        ("H1", "2.3", "Alasan dan Justifikasi Pemilihan Teori, Model, dan Kerangka Kerja",
         "Sub-bab ini menyajikan pertimbangan ilmiah, komparasi rekayasa (architectural trade-offs), dan analisis kelayakan di balik pemilihan teori, model cerdas, dan kerangka kerja yang diadopsi."),
        ("H2", "2.3.1", "Justifikasi Pemilihan Arsitektur RAG Dibandingkan LLM Standalone atau Model Fine-Tuning",
         "Membedah keunggulan RAG dari aspek efisiensi komputasi lokal, fleksibilitas pembaruan data real-time tanpa pelatihan ulang (no retraining), mitigasi catastrophic forgetting, dan supresi halusinasi."),
        ("H2", "2.3.2", "Justifikasi Pemilihan Kerangka Kerja MITRE ATT&CK, MITRE D3FEND, dan NIST CSF 2.0",
         "Menjelaskan pentingnya standarisasi internasional, sifat rekomendasi mitigasi yang preskriptif-operasional, dan kesesuaian terhadap tupoksi CSIRT sektor publik."),
        ("H2", "2.3.3", "Justifikasi Pemilihan Kerangka Kerja Evaluasi RAGAS (Empat Dimensi Lengkap)",
         "Menguraikan urgensi evaluasi kuantitatif independen pada komponen penarikan informasi (retriever) dan pembangkitan jawaban (generator) untuk menjamin factual groundedness pada domain kritis."),
        ("H2", "2.3.4", "Justifikasi Pendekatan Human-in-the-Loop dan Keamanan Kedaulatan Data Cloud API",
         "Menegaskan kedaulatan analis manusia dalam otorisasi mitigasi pertahanan siber daerah serta pembatasan transmisi API awan hanya untuk data intelijen terbuka (OSINT TLP:CLEAR).")
    ]

    for sec_type, sec_num, sec_title, sec_desc in sections:
        # Title paragraph
        p_head = p_bab3.insert_paragraph_before()
        p_head.paragraph_format.space_before = Pt(12 if sec_type == "H1" else 8)
        p_head.paragraph_format.space_after = Pt(4)
        run_h = p_head.add_run(f"{sec_num} {sec_title}")
        run_h.font.name = "Times New Roman"
        run_h.font.size = Pt(12)
        run_h.bold = True

        # Description paragraph
        p_body = p_bab3.insert_paragraph_before()
        p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_body.paragraph_format.line_spacing = 1.5
        p_body.paragraph_format.first_line_indent = Inches(0.4)
        p_body.paragraph_format.space_after = Pt(6)
        run_b = p_body.add_run(sec_desc)
        run_b.font.name = "Times New Roman"
        run_b.font.size = Pt(12)

    doc.save(doc_path)
    print("Berhasil memperbarui struktur BAB II pada Laporan Akhir Capstone Design & Project.docx!")

if __name__ == "__main__":
    update_bab2()
