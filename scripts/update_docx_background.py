import docx
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# Teks 6 Paragraf Latar Belakang yang telah disetujui 100% oleh Auditor Akademik
paragraf_6 = [
    # Paragraf 1
    (
        "Akselerasi transformasi tata kelola pemerintahan digital melalui implementasi Sistem Pemerintahan "
        "Berbasis Elektronik (SPBE) di Indonesia berbanding lurus dengan peningkatan paparan ancaman kejahatan "
        "siber yang menyasar sistem elektronik sektor publik (Ariyaningsih et al., 2023). Tingginya kerentanan "
        "ruang siber nasional tersebut terkonfirmasi oleh data empiris yang mencatatkan 741.441.648 anomali ancaman "
        "siber sepanjang semester pertama tahun 2021 dengan tren peningkatan sebesar 6,15%, di mana serangan "
        "didominasi oleh peretasan penolakan layanan (DoS), penyusupan berkas jahat, dan kebocoran basis data "
        "sensitif (Parulian et al., 2021). Dampak kelumpuhan infrastruktur digital publik terbukti secara nyata pada "
        "insiden serangan siber ransomware terhadap Pusat Data Nasional Sementara (PDNS) tahun 2024 yang melumpuhkan "
        "ratusan layanan strategis kementerian, lembaga, dan pemerintah daerah akibat lemahnya manajemen risiko dan "
        "mekanisme deteksi dini (Fajar et al., 2025)."
    ),
    # Paragraf 2 (Telah diperbaiki: Diskominfo 2023 digantikan Hartanto et al., 2025 dengan akurasi 97,1%)
    (
        "Eskalasi kerentanan sistemik tersebut melandasi penetapan kebijakan nasional yang mewajibkan penyelenggara "
        "sistem elektronik untuk memperkuat ketahanan Infrastruktur Informasi Vital (IIV) sesuai amanat Perpres No. 82 "
        "Tahun 2022, di mana Tim Tanggap Insiden Siber (CSIRT) dituntut bertindak presisi dalam hitungan detik guna "
        "memitigasi anomali sebelum melumpuhkan layanan publik (Kurniati, 2024). Urgensi proteksi ketahanan siber "
        "tersebut diperkuat oleh studi empiris yang membuktikan bahwa penerapan model pembelajaran mesin mampu "
        "mendeteksi anomali serangan ransomware pada infrastruktur digital pemerintah secara cepat dan akurat dengan "
        "tingkat akurasi mencapai 97,1% (Hartanto et al., 2025). Guna mengimbangi beban operasional pengawasan yang "
        "masif tersebut, tata kelola teknologi sektor publik daerah memerlukan adopsi arsitektur data cerdas yang "
        "terbukti mampu menyajikan informasi secara presisi dengan tingkat keberhasilan mencapai 100% pada evaluasi "
        "akurasi dan F1-score (Hadie et al., 2025)."
    ),
    # Paragraf 3
    (
        "Tuntutan pengawasan proaktif tersebut berhadapan langsung dengan karakteristik data Cyber Threat "
        "Intelligence (CTI), di mana diperkirakan hingga 80% informasi ancaman siber tersebar dalam bentuk narasi teks "
        "tidak terstruktur pada laporan insiden, buletin kerentanan, dan artikel berita daring yang menuntut ekstraksi "
        "relasi semantik kompleks agar perilakunya dapat dipetakan secara akurat (Arazzi et al., 2025). Pada jenjang "
        "operasional tim keamanan siber, tingginya heterogenitas sumber, volume data harian yang masif, serta "
        "kompleksitas terminologi teknis menyebabkan penelaahan intelijen ancaman secara manual menyita banyak waktu dan "
        "tenaga analis sehingga memicu kelelahan peringatan (alert fatigue) dan memperlambat respon insiden (Alhuzali, 2025). "
        "Padahal, pemrosesan semantik pada teks berita serangan siber terbukti mampu memetakan identitas kerentanan "
        "perangkat lunak (Common Vulnerabilities and Exposures / CVE) secara presisi dengan tingkat akurasi mencapai 80% "
        "pada prediksi kerentanan urutan pertama (Othman et al., 2026). Selain itu, pemanfaatan model pembelajaran mesin "
        "berbasis data historis sangat diperlukan guna meramalkan pergeseran tren serangan siber dan merekomendasikan "
        "teknologi mitigasi yang objektif tanpa bias pertimbangan subjektif manusia (Almahmoud et al., 2024)."
    ),
    # Paragraf 4
    (
        "Upaya akselerasi mitigasi menggunakan model bahasa besar (Large Language Models / LLMs) secara mandiri tanpa "
        "penambatan basis data rujukan rentan memicu halusinasi fakta yang fatal dalam domain siber, di mana model "
        "ditemukan memunculkan stempel waktu fiktif serta artefak digital palsu yang sama sekali tidak terdapat pada berkas "
        "bukti aslinya (Loumachi et al., 2025). Guna menanggulangi distorsi fakta tersebut, integrasi pencarian semantik "
        "berbasis basis data vektor dengan kerangka kerja Retrieval-Augmented Generation (RAG) mampu menyatukan penarikan "
        "data padat (dense retrieval) dengan model generatif guna menambatkan luaran penalaran pada dokumen rujukan "
        "terverifikasi dan menekan halusinasi secara signifikan (Gandhi, 2023). Keunggulan pendekatan RAG ini terkonfirmasi "
        "secara kuantitatif pada pengujian rekomendasi perbaikan kerentanan perangkat lunak, di mana penambahan komponen RAG "
        "berhasil meningkatkan akurasi luaran dari 52,0% menjadi 76,7%–82,6% serta memangkas tingkat halusinasi model dari "
        "23,4% menjadi hanya 7,8% (Hsieh et al., 2026)."
    ),
    # Paragraf 5
    (
        "Eksplorasi sistem cerdas terdahulu pada ranah operasional pusat operasi keamanan seperti Security Event Response "
        "Copilot (SERC) telah mengintegrasikan pendekatan RAG guna memandu respon insiden, namun fokus arsitekturnya masih "
        "terbatas pada analisis log telemetri internal SIEM Wazuh yang dipetakan ke kerangka MITRE ATT&CK dan NIST CSF 2.0 "
        "sehingga belum menyentuh intelijen ancaman dari kurasi berita insiden publik eksternal (Ismail et al., 2025). Di sisi "
        "lain, pengembangan dashboard analitik siber berbasis NLP lainnya masih memusatkan pengolahan data pada aliran opini "
        "media sosial Twitter, di mana meskipun mampu membukukan akurasi klasifikasi teks mencapai 97,20%, data tersebut sarat "
        "akan derau (noise) serta belum terhubung dengan basis pengetahuan mitigasi resmi instansi pemerintah (Lughbi et al., 2024). "
        "Padahal, implementasi RAG dan basis data vektor pada domain instansi layanan publik di Indonesia terbukti efektif dalam "
        "menyelaraskan kebutuhan analisis pengguna dengan dokumen regulasi resmi secara konsisten dan terpercaya (Pujiono et al., 2024)."
    ),
    # Paragraf 6
    (
        "Menjawab kesenjangan riset tersebut, penelitian ini mengembangkan Dashboard Admin SiberHarian pada Dinas Komunikasi "
        "dan Informatika Provinsi Jawa Timur yang mengintegrasikan pengumpulan feed berita insiden siber publik secara kontinu "
        "dengan penalaran proaktif berbasis Retrieval-Augmented Generation (RAG) untuk menghasilkan analisis ancaman dan rekomendasi "
        "mitigasi harian (Paul et al., 2025). Keandalan arsitektur penarikan konteks RAG ini didukung oleh pengujian kerangka kerja "
        "metrik RAGAS yang membukukan skor Context Recall sebesar 0,97 dan Faithfulness sebesar 0,96, membuktikan bahwa rekomendasi "
        "mitigasi yang digenerasikan sistem terkunci secara konsisten pada fakta korpus acuan dengan tingkat halusinasi yang sangat "
        "minimal (Mahdini et al., 2026). Melalui orkestrasi visualisasi analitik interaktif dan efisiensi komputasi awan cerdas, "
        "Dashboard Admin SiberHarian menjadi instrumen pendukung keputusan intelijen ancaman siber yang dapat dijelaskan "
        "(explainable) bagi personel CSIRT Diskominfo Jawa Timur dengan tetap menempatkan analis manusia sebagai pemegang kendali "
        "keputusan akhir (human-in-the-loop) dalam mitigasi ruang siber daerah (Dinis et al., 2025)."
    )
]

daftar_pustaka_apa = [
    "Alhuzali, A. (2025). LLM-powered threat intelligence: a retrieval-augmented generation approach for cyber attack investigation. PeerJ Computer Science, 11, e3371. https://doi.org/10.7717/peerj-cs.3371",
    "Almahmoud, Z., Yoo, P. D., Damiani, E., Choo, K.-K. R., & Yeun, C. Y. (2024). Forecasting cyber threats and pertinent mitigation technologies. Technological Forecasting and Social Change, 200, 123836. https://doi.org/10.1016/j.techfore.2024.123836",
    "Arazzi, M., Arikkat, D. R., Nicolazzo, S., Nocera, A., Rehiman, R. K. A., Vinod, P., & Conti, M. (2025). NLP-based techniques for Cyber Threat Intelligence. Computer Science Review, 56, 100765. https://doi.org/10.1016/j.cosrev.2025.100765",
    "Ariyaningsih, S., Andrianto, A. A., Kusuma, A. S., & Rezi, R. (2023). Korelasi kejahatan siber dengan percepatan digitalisasi di Indonesia. Justisia: Jurnal Ilmu Hukum, 8(1), 1–11.",
    "Dinis, T., Tavares, R., & Correia, M. (2025). Large language models for explainable threat intelligence. INESC-ID, Instituto Superior Técnico, Universidade de Lisboa.",
    "Fajar, H. F., Fadhila, A., & Yades, M. K. (2025). Redesain kebijakan hukum keamanan dan ketahanan siber: Studi kasus serangan siber pada Pusat Data Nasional tahun 2024. Jurnal Hukum Novelty, 14(2), 285–314. https://doi.org/10.26555/novelty.v14i2.2155",
    "Gandhi, S. T. (2023). RAG-Driven cybersecurity intelligence: Leveraging semantic search for improved threat detection. International Journal of Research and Applied Innovations (IJRAI), 6(3), 8889–8897. https://doi.org/10.15662/IJRAI.2023.0603003",
    "Hadie, A. N., Tahyudin, I., & Hariguna, T. (2025). Enhancing accessibility in local government data portals via Retrieval-Augmented Generation: A case study on Satu Data Indonesia in Banyumas Regency. Jurnal Teknik Informatika (JUTIF), 6(4), 2420–2433. https://doi.org/10.52436/1.jutif.2025.6.4.5153",
    "Hartanto, M. B., Winarko, T., Yunita, H. D., Fahurian, F., Yuniarthe, Y., & Zuhri, K. (2025). Model prediksi keamanan siber menggunakan Artificial Intelligence untuk mitigasi ancaman digital. Prosiding Seminar Nasional Rekayasa Teknologi dan Informasi (KONSTELASI), 2(1), 55–64.",
    "Hsieh, C.-H., Cheng, C.-Y., & Wang, Y.-C. (2026). A zero-touch vulnerability remediation framework based on OpenVAS, threat intelligence, and RAG-enhanced large language models. Mathematics, 14(6), 1072. https://doi.org/10.3390/math14061072",
    "Ismail, I., Kurnia, R., Widyatama, F., Wibawa, I. M., Brata, Z. A., Ukasyah, U., Nelistiani, G. A., & Kim, H. (2025). Enhancing Security Operations Center: Wazuh security event response with retrieval-augmented-generation-driven copilot. Sensors, 25(3), 870. https://doi.org/10.3390/s25030870",
    "Kurniati, A. (2024). Kajian peran Artificial Intelligence untuk memperkuat keamanan siber pada infrastruktur informasi vital. MONAS: Jurnal Inovasi Aparatur, 6(2), 154–165. https://doi.org/10.54849/monas.v6i2.251",
    "Loumachi, F. Z., Ghanem, M. C., & Ferrag, M. A. (2025). Advancing cyber incident timeline analysis through retrieval-augmented generation and large language models. Computers, 14(2), 67. https://doi.org/10.3390/computers14020067",
    "Lughbi, H., Mars, M., & Almotairi, K. (2024). A novel NLP-driven dashboard for interactive cyberattacks tweet classification and visualization. Information, 15(3), 137. https://doi.org/10.3390/info15030137",
    "Mahdini, D., Safaat H, N., Vitriani, Y., & Irsyad, M. (2026). Chatbot Generative AI berbasis Hybrid RAG dengan integrasi RIASEC untuk rekomendasi jurusan. Jurnal Pengembangan Teknologi Informasi dan Komunikasi (JUPTIK), 4(1), 197–206. https://doi.org/10.52060/juptik.v4i1.4373",
    "Othman, R., Rimawi, D., Rossi, B., & Russo, B. (2026). Predicting known vulnerabilities from attack news: A transformer-based approach. arXiv preprint arXiv:2602.19606.",
    "Parulian, S., Pratiwi, D. A., & Yustina, M. C. (2021). Ancaman dan solusi serangan siber di Indonesia. TELNECT (Telecommunications, Networks, Electronics, and Computer Technologies), 1(2), 85–92.",
    "Paul, S., Alemi, F., & Macwan, R. (2025). LLM-assisted proactive threat intelligence for automated reasoning. IEEE Transactions on Information Forensics and Security, 1–10.",
    "Pujiono, I., Agtyaputra, I. M., & Ruldeviyani, Y. (2024). Implementing Retrieval-Augmented Generation and vector databases for chatbots in public services agencies context. Jurnal Ilmu Pengetahuan dan Teknologi Komputer (JITK), 10(1), 216–223. https://doi.org/10.33480/jitk.v10i1.5572"
]

def format_p(p, text, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    p.text = ""
    p.alignment = align
    p.paragraph_format.line_spacing = 1.5
    p.paragraph_format.first_line_indent = Inches(0.4)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.space_before = Pt(0)
    run = p.add_run(text)
    run.font.name = "Times New Roman"
    run.font.size = Pt(12)

def update_capstone_doc():
    doc_path = "LAPORAN DASHBOARD ADMIN/Laporan Akhir Capstone Design & Project.docx"
    doc = docx.Document(doc_path)
    
    # Update Paragraphs 28 to 33
    for idx, p_text in enumerate(paragraf_6):
        target_idx = 28 + idx
        format_p(doc.paragraphs[target_idx], p_text)
    print("Updated 6 paragraphs in Laporan Akhir Capstone Design & Project.docx")

    # Update DAFTAR PUSTAKA at p[122]
    # Check where DAFTAR PUSTAKA is
    dp_idx = None
    for i, p in enumerate(doc.paragraphs):
        if p.text.strip() == "DAFTAR PUSTAKA":
            dp_idx = i
            break
            
    if dp_idx is not None:
        # Clear empty paragraphs between DAFTAR PUSTAKA and LAMPIRAN
        insert_pos = dp_idx + 1
        # Insert references before LAMPIRAN
        lampiran_idx = None
        for i in range(dp_idx, len(doc.paragraphs)):
            if "LAMPIRAN" in doc.paragraphs[i].text.upper():
                lampiran_idx = i
                break
                
        # Remove existing empty paragraphs in between
        if lampiran_idx:
            for k in range(lampiran_idx - 1, dp_idx, -1):
                p_to_remove = doc.paragraphs[k]
                p_to_remove._element.getparent().remove(p_to_remove._element)
                
        # Insert each reference before LAMPIRAN
        lampiran_p = None
        for p in doc.paragraphs:
            if "LAMPIRAN" in p.text.upper():
                lampiran_p = p
                break
                
        for ref_text in daftar_pustaka_apa:
            if lampiran_p:
                new_p = lampiran_p.insert_paragraph_before()
            else:
                new_p = doc.add_paragraph()
            new_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            new_p.paragraph_format.line_spacing = 1.15
            new_p.paragraph_format.left_indent = Inches(0.4)
            new_p.paragraph_format.first_line_indent = Inches(-0.4)
            new_p.paragraph_format.space_after = Pt(6)
            run = new_p.add_run(ref_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
            
        print("Updated DAFTAR PUSTAKA in Laporan Akhir Capstone Design & Project.docx")

    doc.save(doc_path)

def update_babi_doc():
    doc_path = "LAPORAN DASHBOARD ADMIN/BAB I Lengkap - Dashboard Admin SiberHarian.docx"
    doc = docx.Document(doc_path)
    
    # In BAB I Lengkap, background is p[3] to p[8]
    for idx, p_text in enumerate(paragraf_6):
        target_idx = 3 + idx
        format_p(doc.paragraphs[target_idx], p_text)
    print("Updated 6 paragraphs in BAB I Lengkap - Dashboard Admin SiberHarian.docx")
    
    # Check if DAFTAR PUSTAKA exists, if not add it at the end
    has_dp = False
    for p in doc.paragraphs:
        if "DAFTAR PUSTAKA" in p.text.upper():
            has_dp = True
            break
            
    if not has_dp:
        dp_head = doc.add_paragraph()
        dp_head.alignment = WD_ALIGN_PARAGRAPH.CENTER
        dp_head.paragraph_format.space_before = Pt(18)
        dp_head.paragraph_format.space_after = Pt(12)
        run_h = dp_head.add_run("DAFTAR PUSTAKA BAB I")
        run_h.font.name = "Times New Roman"
        run_h.font.size = Pt(14)
        run_h.bold = True
        
        for ref_text in daftar_pustaka_apa:
            new_p = doc.add_paragraph()
            new_p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            new_p.paragraph_format.line_spacing = 1.15
            new_p.paragraph_format.left_indent = Inches(0.4)
            new_p.paragraph_format.first_line_indent = Inches(-0.4)
            new_p.paragraph_format.space_after = Pt(6)
            run = new_p.add_run(ref_text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(11)
        print("Added DAFTAR PUSTAKA to BAB I Lengkap - Dashboard Admin SiberHarian.docx")
        
    doc.save(doc_path)

if __name__ == "__main__":
    update_capstone_doc()
    update_babi_doc()
    print("Semua berkas Word (.docx) berhasil diperbarui secara sempurna!")
