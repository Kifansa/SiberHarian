import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

def update_capstone_docx():
    path = "LAPORAN DASHBOARD ADMIN/Laporan Akhir Capstone Design & Project.docx"
    doc = docx.Document(path)

    # Find "Rumusan Masalah" and "BAB II"
    rm_idx = None
    bab2_idx = None
    for i, p in enumerate(doc.paragraphs):
        if "RUMUSAN MASALAH" in p.text.upper() and rm_idx is None:
            rm_idx = i
        elif "BAB II" in p.text.upper() and bab2_idx is None:
            bab2_idx = i

    print(f"rm_idx: {rm_idx}, bab2_idx: {bab2_idx}")

    # Remove paragraphs from rm_idx up to bab2_idx - 1
    for k in range(bab2_idx - 1, rm_idx - 1, -1):
        p_elem = doc.paragraphs[k]._element
        p_elem.getparent().remove(p_elem)

    # Locate paragraph of BAB II again
    for p in doc.paragraphs:
        if "BAB II" in p.text.upper():
            p_bab2 = p
            break

    # Helper function to insert paragraph before p_bab2
    def insert_para(text, style_name="Normal", space_after=6, space_before=0, bold=False, italic=False):
        new_p = p_bab2.insert_paragraph_before()
        new_p.style = doc.styles[style_name]
        new_p.paragraph_format.line_spacing = 1.5
        new_p.paragraph_format.space_before = Pt(space_before)
        new_p.paragraph_format.space_after = Pt(space_after)
        if text:
            run = new_p.add_run(text)
            run.font.name = "Times New Roman"
            run.font.size = Pt(12)
            run.font.bold = bold
            run.font.italic = italic
            run.font.color.rgb = RGBColor(0, 0, 0)
        return new_p

    # Insert 1.2 Rumusan Masalah
    insert_para("1.2. Rumusan Masalah", style_name="Heading 2", space_before=12, space_after=6, bold=True)
    insert_para("Berdasarkan latar belakang di atas, maka rumusan permasalahan untuk penelitian ini adalah:")
    insert_para("1.  Bagaimana pembuatan dashboard admin dengan mengimplementasikan Retrieval-Augmented Generation (RAG) dapat digunakan untuk melakukan analisis serangan siber pada SiberHarian Dinas Komunikasi dan Informatika Provinsi Jawa Timur?")
    insert_para("2.  Bagaimana mengintegrasikan hasil analisis berita dengan pemberian rekomendasi keputusan pada dashboard admin SiberHarian Dinas Komunikasi dan Informatika Provinsi Jawa Timur?")

    # Insert 1.3 Tujuan Penelitian
    insert_para("1.3. Tujuan Penelitian", style_name="Heading 2", space_before=12, space_after=6, bold=True)
    insert_para("Sesuai perumusan masalah diatas, maka penelitian ini bertujuan untuk membuat:")
    insert_para("1.  Membuat rancangan dashboard admin berbasis Retrieval-Augmented Generation (RAG) yang dapat menganalisis berita serangan siber pada SiberHarian Dinas Komunikasi dan Informatika Provinsi Jawa Timur.")
    insert_para("2.  Mengintegrasikan hasil analisis berita dengan sistem pemberian rekomendasi keputusan mitigasi pada dashboard admin SiberHarian Dinas Komunikasi dan Informatika Provinsi Jawa Timur.")

    # Insert 1.4 Batasan dan Asumsi Penelitian
    insert_para("1.4. Batasan dan Asumsi Penelitian", style_name="Heading 2", space_before=12, space_after=6, bold=True)
    insert_para("Penelitian ini memiliki batasan untuk memberikan gambaran hasil penelitian yang lebih jelas sebagai berikut:")
    insert_para("1.  Tidak memfilter berita hoaks secara otomatis namun berita diambil dari sumber yang terpercaya.")
    insert_para("2.  Informasi dan dokumen pedoman keamanan digunakan sebagai sumber pendukung analisis dan rekomendasi pada staf internal Dinas Komunikasi dan Informatika Provinsi Jawa Timur.")

    # Insert 1.5 Manfaat Penelitian
    insert_para("1.5. Manfaat Penelitian", style_name="Heading 2", space_before=12, space_after=6, bold=True)
    insert_para("Penelitian diharapkan dapat memberikan manfaat penelitian sebagai berikut:")

    insert_para("1.5.1. Manfaat Bagi Ilmu Pengetahuan", style_name="Normal", space_before=6, space_after=4, bold=True)
    insert_para("1.  Memperkaya literatur dan kajian empiris pada disiplin ilmu Sistem Informasi dan Keamanan Siber.")
    insert_para("2.  Memberikan kontribusi teoretis mengenai efektivitas implementasi pendekatan Retrieval-Augmented Generation (RAG) yang diintegrasikan dengan Large Language Model (LLM).")
    insert_para("3.  Memproses data teks tidak terstruktur menjadi informasi Cyber Threat Intelligence (CTI) yang valid guna mereduksi risiko halusinasi informasi.")

    insert_para("1.5.2. Manfaat Bagi Peneliti", style_name="Normal", space_before=6, space_after=4, bold=True)
    insert_para("1.  Mengimplementasikan landasan teoretis dan keilmuan yang diperoleh selama masa studi ke dalam penyelesaian masalah empiris.")
    insert_para("2.  Meningkatkan kompetensi analitis dan teknis peneliti, khususnya pada ranah rekayasa sistem informasi, integrasi kecerdasan buatan, serta tata kelola keamanan siber.")

    insert_para("1.5.3. Manfaat Bagi Institusi", style_name="Normal", space_before=6, space_after=4, bold=True)
    insert_para("1.  Menambah perbendaharaan referensi kepustakaan akademik yang relevan dengan perkembangan teknologi kecerdasan buatan dan ketahanan siber.")
    insert_para("2.  Mewujudkan kontribusi nyata institusi pendidikan tinggi dalam menghasilkan inovasi teknologi yang solutif.")
    insert_para("3.  Mendukung penyelesaian permasalahan strategis pada sektor penyelenggaraan pemerintahan.")

    insert_para("1.5.4. Manfaat Bagi Objek Penelitian", style_name="Normal", space_before=6, space_after=4, bold=True)
    insert_para("1.  Menghasilkan dashboard admin yang dapat diimplementasikan sebagai instrumen pendukung operasional bagi analis Security Operations Center (SOC) dan Computer Security Incident Response Team (CSIRT) di lingkungan Dinas Komunikasi dan Informatika Provinsi Jawa Timur.")
    insert_para("2.  Mengoptimalkan efisiensi waktu identifikasi tren ancaman siber harian.")
    insert_para("3.  Merumuskan rekomendasi mitigasi yang terstruktur sebagai landasan pengambilan keputusan strategis dalam mengamankan Infrastruktur Informasi Vital (IIV).")

    doc.save(path)
    print("Berhasil mengupdate Bab 1 pada Laporan Akhir Capstone Design & Project.docx!")

if __name__ == "__main__":
    update_capstone_docx()
