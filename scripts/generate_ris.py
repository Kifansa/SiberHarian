import os
import shutil

# 19 Referensi Terpilih untuk Latar Belakang 6 Paragraf
references = [
    {
        'id': '01_Ariyaningsih_2023',
        'type': 'JOUR',
        'authors': ['Ariyaningsih, Sindy', 'Andrianto, A. Ari', 'Kusuma, Adri Surya', 'Rezi, Rezi'],
        'title': 'Korelasi Kejahatan Siber dengan Percepatan Digitalisasi di Indonesia',
        'journal': 'Justisia: Jurnal Ilmu Hukum',
        'year': '2023',
        'volume': '8',
        'issue': '1',
        'pages': '1-11',
        'url': 'https://creativecommons.org/licenses/by-nc/4.0/',
        'abstract': 'Penelitian ini bertujuan untuk menganalisis korelasi kejahatan siber dengan percepatan digitalisasi di berbagai sektor di Indonesia, mencakup sektor komunikasi, bisnis, dan tata kelola pemerintahan digital pasca pandemi.'
    },
    {
        'id': '02_Parulian_2021',
        'type': 'JOUR',
        'authors': ['Parulian, Sahat', 'Pratiwi, Devi Anassalifa', 'Yustina, Meiliya Cahya'],
        'title': 'Ancaman dan Solusi Serangan Siber di Indonesia',
        'journal': 'TELNECT (Telecommunications, Networks, Electronics, and Computer Technologies)',
        'year': '2021',
        'volume': '1',
        'issue': '2',
        'pages': '85-92',
        'url': 'http://ejournal-purwakarta.upi.edu/telnect',
        'abstract': 'Sepanjang bulan Januari sampai Juli 2021 tercatat 741.441.648 ancaman siber terjadi di Indonesia dengan peningkatan sebesar 6,15%. Serangan didominasi DoS, pencurian data, dan malware yang menuntut strategi pertahanan siber terpadu.'
    },
    {
        'id': '03_Fajar_2025',
        'type': 'JOUR',
        'authors': ['Fajar, Habib Ferian', 'Fadhila, Afdhal', 'Yades, Muhammad Kevin'],
        'title': 'Redesain Kebijakan Hukum Keamanan dan Ketahanan Siber: Studi Kasus Serangan Siber pada Pusat Data Nasional Tahun 2024',
        'journal': 'Jurnal Hukum Novelty',
        'year': '2025',
        'volume': '14',
        'issue': '2',
        'pages': '285-314',
        'doi': '10.26555/novelty.v14i2.2155',
        'abstract': 'Studi kasus serangan siber ransomware Brain Cipher terhadap Pusat Data Nasional Sementara (PDNS 2) tahun 2024 yang melumpuhkan ratusan layanan publik instansi pemerintah daerah dan kementerian akibat kelemahan mitigasi risiko dan deteksi dini.'
    },
    {
        'id': '04_Kurniati_2024',
        'type': 'JOUR',
        'authors': ['Kurniati, Ana'],
        'title': 'Kajian Peran Artificial Intelligence untuk Memperkuat Keamanan Siber pada Infrastruktur Informasi Vital',
        'journal': 'MONAS: Jurnal Inovasi Aparatur',
        'year': '2024',
        'volume': '6',
        'issue': '2',
        'pages': '154-165',
        'doi': '10.54849/monas.v6i2.251',
        'abstract': 'Kajian implementasi AI dalam penguatan ketahanan 10 sektor Infrastruktur Informasi Vital (IIV) sesuai Perpres No. 82/2022 dan strategi operasional Tim Tanggap Insiden Siber (TTIS/CSIRT) yang dituntut merespons ancaman dalam hitungan detik.'
    },
    {
        'id': '05_Hartanto_2025',
        'type': 'CONF',
        'authors': ['Hartanto, M. Bagus', 'Winarko, Totok', 'Yunita, Hana Dwi', 'Fahurian, Fajar', 'Yuniarthe, Yuniarthe', 'Zuhri, Khairul'],
        'title': 'Model Prediksi Keamanan Siber Menggunakan Artificial Intelligence untuk Mitigasi Ancaman Digital',
        'journal': 'Prosiding Seminar Nasional Rekayasa Teknologi dan Informasi (KONSTELASI)',
        'year': '2025',
        'volume': '2',
        'issue': '1',
        'pages': '55-64',
        'url': 'https://prosiding.konstelasi.ftki.unibi.ac.id/index.php/konstelasi',
        'abstract': 'Penelitian ini mengembangkan model prediksi keamanan siber berbasis Machine Learning (LSTM) untuk mendeteksi ancaman serangan siber digital khususnya ransomware pada infrastruktur digital pemerintah, menghasilkan akurasi 97,1%, presisi 95,4%, recall 96,2%, dan F1-Score 95,8%.'
    },
    {
        'id': '06_Hadie_2025',
        'type': 'JOUR',
        'authors': ['Hadie, Alwan Naufal', 'Tahyudin, Imam', 'Hariguna, Taqwa'],
        'title': 'Enhancing Accessibility in Local Government Data Portals via Retrieval-Augmented Generation: A Case Study on Satu Data Indonesia in Banyumas Regency',
        'journal': 'Jurnal Teknik Informatika (JUTIF)',
        'year': '2025',
        'volume': '6',
        'issue': '4',
        'pages': '2420-2433',
        'doi': '10.52436/1.jutif.2025.6.4.5153',
        'abstract': 'Implementation of a Retrieval-Augmented Generation (RAG) architecture tailored for Indonesian local government data portals, achieving a perfect 100% score across accuracy, precision, recall, and F1-score on defined public data queries.'
    },
    {
        'id': '07_Arazzi_2025',
        'type': 'JOUR',
        'authors': ['Arazzi, Marco', 'Arikkat, Dheeraj R.', 'Nicolazzo, Serena', 'Nocera, Antonino', 'Rehiman, Rizwin K. A.', 'Vinod, P.', 'Conti, Mauro'],
        'title': 'NLP-based techniques for Cyber Threat Intelligence',
        'journal': 'Computer Science Review',
        'year': '2025',
        'volume': '56',
        'pages': '100765',
        'doi': '10.1016/j.cosrev.2025.100765',
        'abstract': 'A comprehensive survey on Natural Language Processing (NLP) techniques used to collect, process, and extract actionable Cyber Threat Intelligence (CTI) from unstructured public text and vulnerability reports to enable proactive defense.'
    },
    {
        'id': '08_Alhuzali_2025',
        'type': 'JOUR',
        'authors': ['Alhuzali, Areej'],
        'title': 'LLM-powered threat intelligence: a retrieval-augmented generation approach for cyber attack investigation',
        'journal': 'PeerJ Computer Science',
        'year': '2025',
        'volume': '11',
        'pages': 'e3371',
        'doi': '10.7717/peerj-cs.3371',
        'abstract': 'Development of RAGIntel framework integrating RAG with LLMs to automate cyberattack investigation mapped to MITRE ATT&CK, eliminating hallucinations, outdated knowledge, and technical misinterpretations inherent in standalone LLMs.'
    },
    {
        'id': '09_Othman_2026',
        'type': 'JOUR',
        'authors': ['Othman, Refat', 'Rimawi, Diaeddin', 'Rossi, Bruno', 'Russo, Barbara'],
        'title': 'Predicting known Vulnerabilities from Attack News: A Transformer-Based Approach',
        'journal': 'arXiv preprint arXiv:2602.19606',
        'year': '2026',
        'pages': '1-20',
        'url': 'https://arxiv.org/abs/2602.19606',
        'abstract': 'Predicting Common Vulnerabilities and Exposures (CVEs) directly from unstructured news descriptions using MPNet sentence transformers and semantic similarity, achieving 80% accuracy on the top-predicted vulnerability.'
    },
    {
        'id': '10_Almahmoud_2024',
        'type': 'JOUR',
        'authors': ['Almahmoud, Zaid', 'Yoo, Paul D.', 'Damiani, Ernesto', 'Choo, Kim-Kwang Raymond', 'Yeun, Chan Yeob'],
        'title': 'Forecasting Cyber Threats and Pertinent Mitigation Technologies',
        'journal': 'Technological Forecasting and Social Change',
        'year': '2024',
        'volume': '200',
        'pages': '123836',
        'doi': '10.1016/j.techfore.2024.123836',
        'abstract': 'A data-driven machine learning framework for forecasting cyber-attack trends and prescribing pertinent mitigation technologies, replacing subjective human bias with objective analytical models.'
    },
    {
        'id': '11_Loumachi_2025',
        'type': 'JOUR',
        'authors': ['Loumachi, Fatima Zahra', 'Ghanem, Mohamed Cherif', 'Ferrag, Mohamed Amine'],
        'title': 'Advancing Cyber Incident Timeline Analysis Through Retrieval-Augmented Generation and Large Language Models',
        'journal': 'Computers',
        'year': '2025',
        'volume': '14',
        'issue': '2',
        'pages': '67',
        'doi': '10.3390/computers14020067',
        'abstract': 'The GenDFIR framework demonstrates that generative LLMs without retrieval context produce fictitious timestamps and hallucinated forensic artifacts, whereas RAG effectively anchors analysis on original verifiable digital evidence.'
    },
    {
        'id': '12_Gandhi_2023',
        'type': 'JOUR',
        'authors': ['Gandhi, S. T.'],
        'title': 'RAG-Driven Cybersecurity Intelligence: Leveraging Semantic Search for Improved Threat Detection',
        'journal': 'International Journal of Research and Applied Innovations (IJRAI)',
        'year': '2023',
        'volume': '6',
        'issue': '3',
        'pages': '8889-8897',
        'doi': '10.15662/IJRAI.2023.0603003',
        'abstract': 'Combining dense vector retrieval with generative models to ground outputs in external documents, suppressing hallucinations and supporting up-to-date domain-specific reasoning for Cyber Threat Intelligence.'
    },
    {
        'id': '13_Hsieh_2026',
        'type': 'JOUR',
        'authors': ['Hsieh, Cheng-Hui', 'Cheng, Chen-Yi', 'Wang, Yung-Chung'],
        'title': 'A Zero-Touch Vulnerability Remediation Framework Based on OpenVAS, Threat Intelligence, and RAG-Enhanced Large Language Models',
        'journal': 'Mathematics',
        'year': '2026',
        'volume': '14',
        'issue': '6',
        'pages': '1072',
        'doi': '10.3390/math14061072',
        'abstract': 'On 350 real-world vulnerability cases, the full Prompt + RAG pipeline raised remediation accuracy from 52.0% to 76.7-82.6% (p < 0.001) and drastically reduced hallucination rate from 23.4% to 7.8%.'
    },
    {
        'id': '14_Ismail_2025',
        'type': 'JOUR',
        'authors': ['Ismail, Ismail', 'Kurnia, R.', 'Widyatama, F.', 'Wibawa, I. M.', 'Brata, Z. A.', 'Ukasyah, Ukasyah', 'Nelistiani, G. A.', 'Kim, H.'],
        'title': 'Enhancing Security Operations Center: Wazuh Security Event Response with Retrieval-Augmented-Generation-Driven Copilot',
        'journal': 'Sensors',
        'year': '2025',
        'volume': '25',
        'issue': '3',
        'pages': '870',
        'doi': '10.3390/s25030870',
        'abstract': 'SERC copilot leverages Wazuh SIEM telemetry with RAG and three vectorized knowledge bases (Incident Response, MITRE ATT&CK, NIST CSF 2.0) to guide SOC analysts during incident triage.'
    },
    {
        'id': '15_Lughbi_2024',
        'type': 'JOUR',
        'authors': ['Lughbi, Hany', 'Mars, Mhamed', 'Almotairi, Khaled'],
        'title': 'A Novel NLP-Driven Dashboard for Interactive CyberAttacks Tweet Classification and Visualization',
        'journal': 'Information',
        'year': '2024',
        'volume': '15',
        'issue': '3',
        'pages': '137',
        'doi': '10.3390/info15030137',
        'abstract': 'An interactive NLP-driven dashboard for classifying and visualizing cyberattack tweets, achieving 97.20% classification accuracy but revealing limitations in noisy social media feeds without official mitigation grounding.'
    },
    {
        'id': '16_Pujiono_2024',
        'type': 'JOUR',
        'authors': ['Pujiono, Ibnu', 'Agtyaputra, Irfan Murtadho', 'Ruldeviyani, Yova'],
        'title': 'Implementing Retrieval-Augmented Generation and Vector Databases for Chatbots in Public Services Agencies Context',
        'journal': 'Jurnal Ilmu Pengetahuan dan Teknologi Komputer (JITK)',
        'year': '2024',
        'volume': '10',
        'issue': '1',
        'pages': '216-223',
        'doi': '10.33480/jitk.v10i1.5572',
        'abstract': 'Implementing RAG and vector databases for public services agencies in Indonesia, proving that grounding LLM responses on official regulations eliminates factual errors in government information delivery.'
    },
    {
        'id': '17_Paul_2025',
        'type': 'JOUR',
        'authors': ['Paul, Shuva', 'Alemi, Farhad', 'Macwan, Richard'],
        'title': 'LLM-Assisted Proactive Threat Intelligence for Automated Reasoning',
        'journal': 'IEEE Transactions on Information Forensics and Security',
        'year': '2025',
        'pages': '1-10',
        'url': 'https://ieeexplore.ieee.org',
        'abstract': 'Enhancing real-time cyber threat detection and response by integrating LLMs and RAG systems with continuous threat intelligence feeds, transforming static threat analysis into dynamic proactive reasoning.'
    },
    {
        'id': '18_Mahdini_2026',
        'type': 'JOUR',
        'authors': ['Mahdini, Dini', 'Safaat H, Nazruddin', 'Vitriani, Yenti', 'Irsyad, Muhammad'],
        'title': 'Chatbot Generative AI Berbasis Hybrid RAG dengan Integrasi RIASEC untuk Rekomendasi Jurusan',
        'journal': 'Jurnal Pengembangan Teknologi Informasi dan Komunikasi (JUPTIK)',
        'year': '2026',
        'volume': '4',
        'issue': '1',
        'pages': '197-206',
        'doi': '10.52060/juptik.v4i1.4373',
        'abstract': 'Evaluasi sistem Hybrid RAG menggunakan metrik RAGAS membukukan skor Context Recall sebesar 0,97 dan Faithfulness sebesar 0,96, membuktikan keandalan respon generatif yang terikat kuat pada korpus referensi.'
    },
    {
        'id': '19_Dinis_2025',
        'type': 'RPRT',
        'authors': ['Dinis, Tiago', 'Tavares, Roger', 'Correia, Miguel'],
        'title': 'Large Language Models for Explainable Threat Intelligence',
        'publisher': 'INESC-ID, Instituto Superior Técnico, Universidade de Lisboa / UON',
        'year': '2025',
        'place': 'Lisbon, Portugal',
        'abstract': 'Exploring the use of LLMs with RAG for threat intelligence by combining real-time retrieval with domain-specific knowledge to produce explainable outputs and actionable mitigation for human security analysts.'
    }
]

def generate_ris_record(ref):
    lines = []
    lines.append('TY  - ' + ref['type'])
    for a in ref['authors']:
        lines.append('AU  - ' + a)
    lines.append('TI  - ' + ref['title'])
    if 'journal' in ref:
        lines.append('JO  - ' + ref['journal'])
        lines.append('T2  - ' + ref['journal'])
    if 'publisher' in ref:
        lines.append('PB  - ' + ref['publisher'])
    if 'school' in ref:
        lines.append('PB  - ' + ref['school'])
    if 'place' in ref:
        lines.append('CY  - ' + ref['place'])
    if 'year' in ref:
        lines.append('PY  - ' + str(ref['year']))
        lines.append('Y1  - ' + str(ref['year']))
    if 'volume' in ref:
        lines.append('VL  - ' + str(ref['volume']))
    if 'issue' in ref:
        lines.append('IS  - ' + str(ref['issue']))
    if 'pages' in ref:
        p_split = ref['pages'].split('-')
        if len(p_split) == 2:
            lines.append('SP  - ' + p_split[0])
            lines.append('EP  - ' + p_split[1])
        else:
            lines.append('SP  - ' + ref['pages'])
    if 'doi' in ref:
        lines.append('DO  - ' + ref['doi'])
    if 'url' in ref:
        lines.append('UR  - ' + ref['url'])
    if 'abstract' in ref:
        lines.append('AB  - ' + ref['abstract'])
    lines.append('ER  - \n')
    return '\n'.join(lines)

def main():
    target_dirs = [
        os.path.join('LAPORAN DASHBOARD ADMIN', 'REFERENSI_RIS'),
        'REFERENSI_RIS'
    ]

    for td in target_dirs:
        # Bersihkan folder dari file lama
        if os.path.exists(td):
            for old_f in os.listdir(td):
                os.remove(os.path.join(td, old_f))
        os.makedirs(td, exist_ok=True)
        
        all_records = []
        for ref in references:
            ris_content = generate_ris_record(ref)
            all_records.append(ris_content)
            single_path = os.path.join(td, ref['id'] + '.ris')
            with open(single_path, 'w', encoding='utf-8') as f:
                f.write(ris_content)
        
        master_path = os.path.join(td, 'ALL_REFERENCES_MENDELEY.ris')
        with open(master_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(all_records))
            
        readme_path = os.path.join(td, 'README_MENDELEY_IMPORT.txt')
        readme_text = '''================================================================================
PANDUAN IMPORT REFERENSI KE MENDELEY (DESKTOP & REFERENCE MANAGER)
================================================================================

Folder ini berisi 19 file RIS individual dan 1 file RIS master gabungan
untuk seluruh sitasi yang digunakan pada Latar Belakang 6 Paragraf Dashboard Admin SiberHarian:

PILIHAN 1: IMPORT SEMUA REFERENSI SEKALIGUS (SANGAT DIREKOMENDASIKAN):
1. Buka aplikasi Mendeley Reference Manager atau Mendeley Desktop.
2. Buat folder/collection baru, misal: 'Capstone SiberHarian Diskominfo Jatim'.
3. Klik tombol 'Add new' (di pojok kiri atas) -> Pilih 'Import library' -> 'RIS (*.ris)'.
4. Pilih berkas: 'ALL_REFERENCES_MENDELEY.ris'.
5. Selesai! Seluruh 19 referensi otomatis masuk ke library Mendeley Anda lengkap dengan
   nama author, judul, nama jurnal, volume, nomor halaman, tahun, DOI, dan abstrak.

PILIHAN 2: IMPORT SATU PER SATU:
- Anda dapat mengimpor file individual sesuai kebutuhan dari nomor 01 hingga 19:
  01_Ariyaningsih_2023.ris
  02_Parulian_2021.ris
  03_Fajar_2025.ris
  04_Kurniati_2024.ris
  05_Hartanto_2025.ris
  06_Hadie_2025.ris
  07_Arazzi_2025.ris
  08_Alhuzali_2025.ris
  09_Othman_2026.ris
  10_Almahmoud_2024.ris
  11_Loumachi_2025.ris
  12_Gandhi_2023.ris
  13_Hsieh_2026.ris
  14_Ismail_2025.ris
  15_Lughbi_2024.ris
  16_Pujiono_2024.ris
  17_Paul_2025.ris
  18_Mahdini_2026.ris
  19_Dinis_2025.ris

File RIS ini 100% kompatibel dengan Mendeley, Zotero, dan EndNote.
================================================================================
'''
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_text)

    print('Berhasil memperbarui 19 file RIS dan 1 master ALL_REFERENCES_MENDELEY.ris!')

if __name__ == '__main__':
    main()
