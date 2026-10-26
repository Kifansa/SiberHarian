# -*- coding: utf-8 -*-
"""
Generator Skrip Utama untuk Menghasilkan Dokumen Word:
Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx
"""

import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

from logbook_data import WEEKS_DATA

def set_cell_shading(cell, color_hex):
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)

def set_cell_margins(cell, top=120, bottom=120, left=140, right=140):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="B0BEC5", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def make_callout(doc, title, text, bg_color="F0F4F8", border_color="0A1628"):
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    c = tbl.cell(0, 0)
    set_cell_shading(c, bg_color)
    set_cell_margins(c, top=120, bottom=120, left=180, right=180)
    
    tcPr = c._tc.get_or_add_tcPr()
    borders = parse_xml(
        f'<w:tcBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="single" w:sz="24" w:space="0" w:color="{border_color}"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    tcPr.append(borders)
    
    p = c.paragraphs[0]
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    run_t = p.add_run(f"📌 {title}: ")
    run_t.font.name = "Calibri"
    run_t.font.size = Pt(9.5)
    run_t.font.bold = True
    run_t.font.color.rgb = RGBColor(10, 22, 40)
    
    run_b = p.add_run(text)
    run_b.font.name = "Calibri"
    run_b.font.size = Pt(9)
    run_b.font.italic = True
    run_b.font.color.rgb = RGBColor(50, 60, 70)
    
    p_after = doc.add_paragraph()
    p_after.paragraph_format.space_before = Pt(0)
    p_after.paragraph_format.space_after = Pt(4)


def add_header_footer(doc):
    for s in doc.sections:
        # Header
        h = s.header
        hp = h.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("LOGBOOK MAGANG DISKOMINFO PROVINSI JAWA TIMUR — CSIRT JATIM (SIBERHARIAN)")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.italic = True
        hrun.font.color.rgb = RGBColor(120, 140, 160)
        
        # Footer
        f = s.footer
        fp = f.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run("Program Magang & Capstone Design Project 18 Minggu | Bidang Keamanan Informasi & Persandian")
        frun.font.name = "Calibri"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(120, 140, 160)

def set_para_style(p, before=0, after=4, line_spacing=1.15, align=WD_ALIGN_PARAGRAPH.LEFT):
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = line_spacing
    p.alignment = align

def add_styled_heading(doc, text, level=1, space_before=12, space_after=6):
    p = doc.add_paragraph()
    set_para_style(p, before=space_before, after=space_after, line_spacing=1.15)
    run = p.add_run(text)
    run.font.name = "Arial"
    run.font.bold = True
    if level == 1:
        run.font.size = Pt(14)
        run.font.color.rgb = RGBColor(10, 22, 40) # Dark Navy
    elif level == 2:
        run.font.size = Pt(12)
        run.font.color.rgb = RGBColor(15, 45, 85) # Slate Navy
    elif level == 3:
        run.font.size = Pt(11)
        run.font.color.rgb = RGBColor(30, 70, 120)
    return p

def create_document():
    doc = docx.Document()
    
    # Page setup: A4, standard margin (Top/Bottom 2.5cm, Left 3cm, Right 2.5cm)
    sec = doc.sections[0]
    sec.page_width = Inches(8.27)
    sec.page_height = Inches(11.69)
    sec.top_margin = Inches(0.98) # 2.5 cm
    sec.bottom_margin = Inches(0.98) # 2.5 cm
    sec.left_margin = Inches(1.18) # 3.0 cm
    sec.right_margin = Inches(0.98) # 2.5 cm
    
    add_header_footer(doc)
    
    # ==========================================
    # HALAMAN COVER / JUDUL UTAMA
    # ==========================================
    p_inst = doc.add_paragraph()
    set_para_style(p_inst, before=10, after=2, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_inst.add_run("PEMERINTAH PROVINSI JAWA TIMUR\nDINAS KOMUNIKASI DAN INFORMATIKA\nBIDANG KEAMANAN INFORMASI DAN PERSANDIAN\nCOMPUTER SECURITY INCIDENT RESPONSE TEAM (CSIRT JATIM)")
    r.font.name = "Arial"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = RGBColor(10, 22, 40)
    
    p_line = doc.add_paragraph()
    set_para_style(p_line, before=2, after=24, align=WD_ALIGN_PARAGRAPH.CENTER)
    r_line = p_line.add_run("―" * 50)
    r_line.font.name = "Arial"
    r_line.font.size = Pt(12)
    r_line.font.color.rgb = RGBColor(0, 160, 210)
    
    p_title = doc.add_paragraph()
    set_para_style(p_title, before=10, after=8, align=WD_ALIGN_PARAGRAPH.CENTER)
    r_t1 = p_title.add_run("LOGBOOK KEGIATAN MAGANG &\nCAPSTONE DESIGN PROJECT\n(DURASI 18 MINGGU)")
    r_t1.font.name = "Arial"
    r_t1.font.size = Pt(17)
    r_t1.font.bold = True
    r_t1.font.color.rgb = RGBColor(10, 22, 40)
    
    p_sub = doc.add_paragraph()
    set_para_style(p_sub, before=6, after=28, align=WD_ALIGN_PARAGRAPH.CENTER)
    r_sub = p_sub.add_run("PENGEMBANGAN DASHBOARD ADMIN BERBASIS RAG UNTUK ANALISIS BERITA SERANGAN SIBER DAN REKOMENDASI MITIGASI SIBERHARIAN PADA DISKOMINFO PROVINSI JAWA TIMUR")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(11.5)
    r_sub.font.bold = True
    r_sub.font.color.rgb = RGBColor(40, 60, 90)
    
    # Tabel Identitas Mahasiswa & Instansi
    t_id = doc.add_table(rows=8, cols=3)
    t_id.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_id, color="CFD8DC", sz="4")
    
    id_data = [
        ("Nama Mahasiswa", ":", "Kifansa Fadhlurrohman"),
        ("NIM / Program Studi", ":", "S1 Sistem Informasi / Teknik Informatika"),
        ("Perguruan Tinggi", ":", "[Universitas / Institut Asal Mahasiswa]"),
        ("Instansi Magang", ":", "Dinas Komunikasi dan Informatika Provinsi Jawa Timur"),
        ("Unit Kerja / Divisi", ":", "Bidang Keamanan Informasi dan Persandian (Tim CSIRT Jatim)"),
        ("Alamat Instansi", ":", "Jl. Ahmad Yani No. 242-244, Gayungan, Surabaya, Jawa Timur 60235"),
        ("Periode Magang", ":", "22 Juni 2026 – 23 Oktober 2026 (18 Minggu Penuh)"),
        ("Pembimbing Lapangan", ":", "Pembimbing Lapangan Tim CSIRT Diskominfo Jatim")
    ]
    
    col_w = [Inches(1.8), Inches(0.2), Inches(4.3)]
    for r_idx, row in enumerate(id_data):
        for c_idx in range(3):
            cell = t_id.cell(r_idx, c_idx)
            cell.width = col_w[c_idx]
            set_cell_margins(cell, top=80, bottom=80, left=100, right=100)
            if r_idx % 2 == 1:
                set_cell_shading(cell, "F8FAFC")
            p = cell.paragraphs[0]
            set_para_style(p, before=1, after=1, line_spacing=1.1)
            run = p.add_run(row[c_idx])
            run.font.name = "Calibri"
            run.font.size = Pt(10)
            if c_idx == 0:
                run.font.bold = True
                run.font.color.rgb = RGBColor(30, 45, 65)
            elif c_idx == 2 and r_idx in [0, 3, 4, 6]:
                run.font.bold = True
                run.font.color.rgb = RGBColor(10, 22, 40)
    
    doc.add_page_break()
    
    # ==========================================
    # LEMBAR PENGESAHAN LOGBOOK
    # ==========================================
    add_styled_heading(doc, "LEMBAR PENGESAHAN LOGBOOK KEGIATAN MAGANG", level=1, space_before=10, space_after=12)
    
    p_peng = doc.add_paragraph()
    set_para_style(p_peng, before=4, after=16, line_spacing=1.2)
    r = p_peng.add_run("Logbook kegiatan praktik kerja magang dan penyusunan Capstone Design & Project dengan judul ")
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r_b = p_peng.add_run('"Pengembangan Dashboard Admin Berbasis RAG untuk Analisis Berita Serangan Siber dan Rekomendasi Mitigasi SiberHarian pada Diskominfo Jawa Timur"')
    r_b.font.name = "Calibri"
    r_b.font.size = Pt(10.5)
    r_b.font.bold = True
    r_c = p_peng.add_run(" yang dilaksanakan pada tanggal 22 Juni 2026 sampai dengan 23 Oktober 2026 (18 Minggu) di Bidang Keamanan Informasi dan Persandian Diskominfo Provinsi Jawa Timur, telah diperiksa, diverifikasi, dan disetujui sesuai dengan realisasi pelaksanaan sesungguhnya.")
    r_c.font.name = "Calibri"
    r_c.font.size = Pt(10.5)
    
    # Tabel Tanda Tangan
    t_ttd = doc.add_table(rows=4, cols=2)
    t_ttd.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_ttd, color="FFFFFF", sz="0")
    
    ttd_col_w = [Inches(3.1), Inches(3.2)]
    
    # Row 0: Tanggal
    c0 = t_ttd.cell(0, 0)
    p0 = c0.paragraphs[0]
    set_para_style(p0, before=2, after=2)
    r = p0.add_run("Mengetahui,\nDosen Pembimbing Akademik")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.bold = True
    
    c1 = t_ttd.cell(0, 1)
    p1 = c1.paragraphs[0]
    set_para_style(p1, before=2, after=2)
    r = p1.add_run("Surabaya, 23 Oktober 2026\nMenyetujui,\nPembimbing Lapangan Diskominfo Jatim")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.bold = True
    
    # Row 1: Space for signature
    for idx in range(2):
        c = t_ttd.cell(1, idx)
        p = c.paragraphs[0]
        set_para_style(p, before=40, after=10)
        p.add_run("\n\n\n")
        
    # Row 2: Nama dan NIP
    c_dosen = t_ttd.cell(2, 0)
    p_d = c_dosen.paragraphs[0]
    set_para_style(p_d, before=2, after=1)
    r = p_d.add_run("( ______________________________ )\nNIDN. ........................................")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    
    c_pemb = t_ttd.cell(2, 1)
    p_p = c_pemb.paragraphs[0]
    set_para_style(p_p, before=2, after=1)
    r = p_p.add_run("( ______________________________ )\nNIP. ........................................")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    
    # Row 3: Mengetahui Pejabat Instansi
    t_ttd2 = doc.add_table(rows=3, cols=1)
    t_ttd2.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_ttd2, color="FFFFFF", sz="0")
    
    c_kabid = t_ttd2.cell(0, 0)
    p_k = c_kabid.paragraphs[0]
    set_para_style(p_k, before=24, after=40, align=WD_ALIGN_PARAGRAPH.CENTER)
    r = p_k.add_run("Mengesahkan,\nKepala Bidang Keamanan Informasi dan Persandian\nDinas Komunikasi dan Informatika Provinsi Jawa Timur\n\n\n\n\n( ___________________________________________ )\nNIP. .............................................................")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r.font.bold = True
    
    doc.add_page_break()
    
    # ==========================================
    # RINGKASAN EKSEKUTIF & ROADMAP 18 MINGGU
    # ==========================================
    add_styled_heading(doc, "RINGKASAN EKSEKUTIF & ROADMAP PROYEK (18 MINGGU)", level=1, space_before=6, space_after=10)
    
    p_desc = doc.add_paragraph()
    set_para_style(p_desc, before=2, after=10, line_spacing=1.2)
    r = p_desc.add_run("Proyek magang ini dilaksanakan selama 18 minggu (22 Juni 2026 – 23 Oktober 2026) di bawah bimbingan langsung Tim CSIRT Bidang Keamanan Informasi dan Persandian Diskominfo Provinsi Jawa Timur. Proyek berfokus pada pengembangan platform ")
    r.font.name = "Calibri"
    r.font.size = Pt(10.5)
    r_b = p_desc.add_run("SiberHarian")
    r_b.font.name = "Calibri"
    r_b.font.size = Pt(10.5)
    r_b.font.bold = True
    r_c = p_desc.add_run(", sebuah sistem intelijen ancaman siber (*Cyber Threat Intelligence* / CTI) dan portal edukasi keamanan siber terpadu berbasis Retrieval-Augmented Generation (RAG) dan Google Gemini API. Perjalanan rekayasa sistem melalui 7 fase evolusi terencana sebagai berikut:")
    r_c.font.name = "Calibri"
    r_c.font.size = Pt(10.5)
    
    # Tabel Roadmap 7 Fase
    t_road = doc.add_table(rows=8, cols=4)
    t_road.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_road, color="B0BEC5", sz="4")
    
    headers = ["Fase Proyek", "Rentang Minggu", "Fokus Utama & Deliverables", "Status Capaian"]
    for c_idx, h_text in enumerate(headers):
        c = t_road.cell(0, c_idx)
        set_cell_shading(c, "0D2137")
        set_cell_margins(c, top=100, bottom=100, left=120, right=120)
        p = c.paragraphs[0]
        set_para_style(p, before=1, after=1, align=WD_ALIGN_PARAGRAPH.CENTER)
        run = p.add_run(h_text)
        run.font.name = "Arial"
        run.font.size = Pt(9.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    phases_data = [
        ("Fase I", "Minggu 1 – 4\n(22 Jun – 17 Jul 2026)", "Onboarding Diskominfo, observasi alur kerja SOC, penyusunan proposal, presentasi review, revisi proposal, penetapan stack teknologi (FastAPI, SQLite, Jinja2, Tailwind).", "100% Selesai\n(Disahkan Instansi)"),
        ("Fase II", "Minggu 5 – 8\n(20 Jul – 14 Agu 2026)", "Desain skema data state.db, eksperimen scraping multi-feed, eksperimen model LLM lokal (Ollama Llama3/Mistral), identifikasi bottleneck latensi/VRAM, terbitnya log sistem perdana (31 Juli 2026), integrasi awal CVE NVD API.", "100% Selesai\n(Log 31/07 & CSV)"),
        ("Fase III", "Minggu 9 – 12\n(17 Agu – 11 Sep 2026)", "Inisialisasi Git resmi (first commit f1786aa, v1.0.0), pembuatan UI beranda & arsip, integrasi SSE terminal (v2 cc96e8d), evaluasi kepatuhan hak cipta (UU No. 28/2014), penegakan aturan parafrase faktual (v3 98a42e7), dokumen PRODUCT.md, audit RSS feed, dan evaluasi paruh waktu (Mid-term v4 bd271f4).", "100% Selesai\n(Mid-Term Review)"),
        ("Fase IV", "Minggu 13 – 14\n(14 Sep – 25 Sep 2026)", "Modularisasi frontend (tren-*.js), fitur ekspor PDF resmi, audit antislop UI (WCAG AAA), PIVOT AI: Migrasi total Ollama lokal ke Google Gemini Cloud API (fallback chain gemini-3.1-flash-lite s.d. 3.7-flash), semantic embedding text-embedding-004, RBAC auth bcrypt, kepatuhan robots.txt (v5, v6, v7).", "100% Selesai\n(Performa 19x Cepat)"),
        ("Fase V", "Minggu 15\n(28 Sep – 2 Okt 2026)", "PIVOT FUNDAMENTAL & RILIS BESAR v3.0.0 (commit v8 & v9 9b1aceb): Eradikasi total modul CVE (-680 baris cve_fetcher.py), adopsi 10 Sektor Infrastruktur Informasi Vital (IIV Perpres 82/2022), formula Threat Posture murni CTI, laporan SITREP 5 modul, dan redesign total antarmuka Cyber-HUD selaras csirt.jatimprov.go.id.", "100% Selesai\n(Rilis Akbar v3.0.0)"),
        ("Fase VI", "Minggu 16 – 17\n(5 Okt – 16 Okt 2026)", "Suite pengujian menyeluruh (pytest 59 test lolos), uji anti-halusinasi CTI, evaluasi RAGAS (Context Recall 0.97, Faithfulness 0.96), penyusunan naskah Laporan Akhir Capstone Design & Project (BAB I-III), pembuatan manual panduan operasional admin CSIRT.", "100% Selesai\n(Naskah Laporan)"),
        ("Fase VII", "Minggu 18\n(19 Okt – 23 Okt 2026)", "Finalisasi dokumen laporan & logbook resmi 18 minggu, gladi bersih staging server, presentasi akhir dan live demo di hadapan jajaran pimpinan Diskominfo Jatim, Berita Acara Serah Terima (BAST) sistem, dan penutupan magang.", "100% Selesai\n(Handover Resmi)")
    ]
    
    r_w = [Inches(0.9), Inches(1.3), Inches(3.3), Inches(1.0)]
    for r_idx, (f_name, f_weeks, f_desc, f_stat) in enumerate(phases_data, start=1):
        row_cells = t_road.rows[r_idx].cells
        row_cells[0].text = f_name
        row_cells[1].text = f_weeks
        row_cells[2].text = f_desc
        row_cells[3].text = f_stat
        
        bg_col = "FFFFFF" if r_idx % 2 == 1 else "F8FAFC"
        for c_idx in range(4):
            c = row_cells[c_idx]
            c.width = r_w[c_idx]
            set_cell_shading(c, bg_col)
            set_cell_margins(c, top=80, bottom=80, left=90, right=90)
            p = c.paragraphs[0]
            align = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 1, 3] else WD_ALIGN_PARAGRAPH.LEFT
            set_para_style(p, before=1, after=1, line_spacing=1.1, align=align)
            p.runs[0].font.name = "Calibri"
            p.runs[0].font.size = Pt(8.5)
            if c_idx == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(10, 22, 40)
            elif c_idx == 3:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0, 130, 70)
                
    doc.add_page_break()
    
    # ==========================================
    # LOGBOOK RINCI 18 MINGGU (MINGGU 1 S.D. 18)
    # ==========================================
    add_styled_heading(doc, "CATATAN LOGBOOK RINCI PER MINGGU (MINGGU 1 S.D. 18)", level=1, space_before=6, space_after=12)
    
    p_intro = doc.add_paragraph()
    set_para_style(p_intro, before=2, after=12, line_spacing=1.15)
    r = p_intro.add_run("Berikut adalah catatan harian logbook kegiatan mahasiswa selama 18 minggu masa magang dan pengerjaan Capstone Design & Project pada Bidang Keamanan Informasi dan Persandian Diskominfo Provinsi Jawa Timur. Format tabel mencakup 4 elemen pokok instansi: ")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r_b = p_intro.add_run("Rencana Kegiatan, Hasil Kegiatan & Artefak Kerja, Hambatan yang Dihadapi, serta Perbaikan & Tindak Lanjut Solusi")
    r_b.font.name = "Calibri"
    r_b.font.size = Pt(10)
    r_b.font.bold = True
    r_c = p_intro.add_run(", dilengkapi uraian refleksi teknis mingguan dan pengesahan pembimbing lapangan.")
    r_c.font.name = "Calibri"
    r_c.font.size = Pt(10)
    
    for w_data in WEEKS_DATA:
        w_num = w_data["week_num"]
        w_dates = w_data["date_range"]
        w_theme = w_data["theme"]
        w_phase = w_data["phase"]
        
        # Heading Minggu
        p_wh = doc.add_paragraph()
        set_para_style(p_wh, before=14, after=2, line_spacing=1.15)
        r = p_wh.add_run(f"MINGGU KE-{w_num:02d} ({w_dates})")
        r.font.name = "Arial"
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.color.rgb = RGBColor(10, 22, 40)
        
        p_wt = doc.add_paragraph()
        set_para_style(p_wt, before=1, after=8, line_spacing=1.15)
        r_ph = p_wt.add_run(f"[{w_phase}] ")
        r_ph.font.name = "Calibri"
        r_ph.font.size = Pt(9.5)
        r_ph.font.bold = True
        r_ph.font.color.rgb = RGBColor(0, 130, 180)
        
        r_th = p_wt.add_run(w_theme)
        r_th.font.name = "Calibri"
        r_th.font.size = Pt(9.5)
        r_th.font.italic = True
        r_th.font.color.rgb = RGBColor(50, 60, 75)
        
        # Tabel 5 Kolom: Hari/Tgl | Rencana | Hasil | Hambatan | Perbaikan
        table = doc.add_table(rows=6, cols=5)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table, color="B0BEC5", sz="4")
        
        t_headers = ["Hari / Tanggal", "Rencana Kegiatan", "Hasil Kegiatan & Artefak", "Hambatan yang Dihadapi", "Perbaikan & Tindak Lanjut"]
        col_widths = [Inches(1.0), Inches(1.5), Inches(1.6), Inches(1.2), Inches(1.2)]
        
        # Header Row
        for c_idx, h_name in enumerate(t_headers):
            cell = table.cell(0, c_idx)
            cell.width = col_widths[c_idx]
            set_cell_shading(cell, "0D2137")
            set_cell_margins(cell, top=80, bottom=80, left=90, right=90)
            p = cell.paragraphs[0]
            set_para_style(p, before=1, after=1, align=WD_ALIGN_PARAGRAPH.CENTER)
            run = p.add_run(h_name)
            run.font.name = "Arial"
            run.font.size = Pt(8.5)
            run.font.bold = True
            run.font.color.rgb = RGBColor(255, 255, 255)
            
        # Day Rows (1 s.d. 5)
        for d_idx, day_info in enumerate(w_data["days"], start=1):
            row_cells = table.rows[d_idx].cells
            
            row_cells[0].text = day_info["day"]
            row_cells[1].text = day_info["plan"]
            row_cells[2].text = day_info["result"]
            row_cells[3].text = day_info["obstacle"]
            row_cells[4].text = day_info["solution"]
            
            row_bg = "FFFFFF" if d_idx % 2 == 1 else "F9FBFC"
            
            for c_idx in range(5):
                c = row_cells[c_idx]
                c.width = col_widths[c_idx]
                set_cell_shading(c, row_bg)
                set_cell_margins(c, top=70, bottom=70, left=80, right=80)
                p = c.paragraphs[0]
                align = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
                set_para_style(p, before=1, after=1, line_spacing=1.1, align=align)
                p.runs[0].font.name = "Calibri"
                p.runs[0].font.size = Pt(8)
                if c_idx == 0:
                    p.runs[0].font.bold = True
                    p.runs[0].font.color.rgb = RGBColor(20, 35, 55)
                elif c_idx == 3:
                    p.runs[0].font.color.rgb = RGBColor(160, 40, 20) # Reddish amber for obstacle
                elif c_idx == 4:
                    p.runs[0].font.color.rgb = RGBColor(10, 110, 50) # Greenish for solution
                    
        # Refleksi Teknis Callout Box
        make_callout(doc, f"Refleksi & Justifikasi Rekayasa Teknis Minggu ke-{w_num}", w_data["tech_reflection"], bg_color="F0F5FA", border_color="00A0D2")
        
        # Kotak Catatan & Paraf Pembimbing
        t_paraf = doc.add_table(rows=1, cols=2)
        t_paraf.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(t_paraf, color="CFD8DC", sz="4")
        
        c_left = t_paraf.cell(0, 0)
        c_left.width = Inches(5.1)
        set_cell_shading(c_left, "FAFCFD")
        set_cell_margins(c_left, top=60, bottom=60, left=100, right=100)
        p_l = c_left.paragraphs[0]
        set_para_style(p_l, before=1, after=1)
        r_pl_t = p_l.add_run("Catatan / Evaluasi Pembimbing Lapangan:\n")
        r_pl_t.font.name = "Calibri"
        r_pl_t.font.size = Pt(8.5)
        r_pl_t.font.bold = True
        r_pl_t.font.color.rgb = RGBColor(15, 30, 50)
        r_pl_c = p_l.add_run(f'"{w_data["supervisor_note"]}"')
        r_pl_c.font.name = "Calibri"
        r_pl_c.font.size = Pt(8.5)
        r_pl_c.font.italic = True
        r_pl_c.font.color.rgb = RGBColor(40, 55, 75)
        
        c_right = t_paraf.cell(0, 1)
        c_right.width = Inches(1.4)
        set_cell_shading(c_right, "FFFFFF")
        set_cell_margins(c_right, top=60, bottom=60, left=60, right=60)
        p_r = c_right.paragraphs[0]
        set_para_style(p_r, before=1, after=1, align=WD_ALIGN_PARAGRAPH.CENTER)
        r_pr = p_r.add_run("Status: Disetujui\nParaf Pembimbing\n\n\n( ____________ )")
        r_pr.font.name = "Calibri"
        r_pr.font.size = Pt(7.5)
        r_pr.font.color.rgb = RGBColor(80, 95, 110)
        
        p_sp = doc.add_paragraph()
        set_para_style(p_sp, before=0, after=10)
        
        # Add page break after every 2 weeks to keep document clean
        if w_num % 2 == 0 and w_num < 18:
            doc.add_page_break()
            
    doc.add_page_break()
    
    # ==========================================
    # MATRIKS KOMPARASI EVOLUSI PROYEK SIBERHARIAN
    # ==========================================
    add_styled_heading(doc, "MATRIKS KOMPARASI EVOLUSI PROYEK SIBERHARIAN", level=1, space_before=6, space_after=10)
    
    p_komp = doc.add_paragraph()
    set_para_style(p_komp, before=2, after=10, line_spacing=1.15)
    r = p_komp.add_run("Tabel berikut merangkum evolusi teknis dan keputusan rekayasa krusial selama 18 minggu, membandingkan kondisi sistem ")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r_b = p_komp.add_run("Sebelum Pivot Arsitektur (v1.0.0 s.d. v4.0.0, Minggu 1-12)")
    r_b.font.name = "Calibri"
    r_b.font.size = Pt(10)
    r_b.font.bold = True
    r_c = p_komp.add_run(" versus ")
    r_c.font.name = "Calibri"
    r_c.font.size = Pt(10)
    r_d = p_komp.add_run("Sesudah Pivot Fundamental (v5.0.0 s.d. v3.0.0, Minggu 13-18)")
    r_d.font.name = "Calibri"
    r_d.font.size = Pt(10)
    r_d.font.bold = True
    r_e = p_komp.add_run(":")
    r_e.font.name = "Calibri"
    r_e.font.size = Pt(10)
    
    t_ev = doc.add_table(rows=9, cols=3)
    t_ev.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_ev, color="B0BEC5", sz="4")
    
    ev_headers = ["Dimensi Arsitektur & Rekayasa", "Sebelum Pivot (Minggu 1 – 12)\nSiberHarian v1.0.0 – v4.0.0", "Sesudah Pivot (Minggu 13 – 18)\nSiberHarian v3.0.0 (Final Enterprise)"]
    ev_col_w = [Inches(1.8), Inches(2.3), Inches(2.4)]
    
    for c_idx, h_text in enumerate(ev_headers):
        c = t_ev.cell(0, c_idx)
        c.width = ev_col_w[c_idx]
        set_cell_shading(c, "0D2137")
        set_cell_margins(c, top=80, bottom=80, left=100, right=100)
        p = c.paragraphs[0]
        set_para_style(p, before=1, after=1, align=WD_ALIGN_PARAGRAPH.CENTER)
        run = p.add_run(h_text)
        run.font.name = "Arial"
        run.font.size = Pt(8.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    ev_rows = [
        ("Lingkup & Fokus Data", "Dual-Stream: Berita Insiden + Pelacakan unpatched CVE software pihak ketiga (NVD API NIST).", "Murni Cyber Threat Intelligence (CTI) & Publikasi Berita Insiden 10 Sektor Infrastruktur Informasi Vital (IIV Perpres 82/2022). Modul CVE dihapus total."),
        ("Mesin Inferensi AI", "Model LLM Lokal via Ollama runtime (Llama 3 8B, Mistral 7B Instruct) dijalankan pada workstation.", "Cloud-Accelerated Intelligence: Google Gemini API dengan rantai fallback otomatis (gemini-3.1-flash-lite s.d. 3.7-flash) & Token Bucket Rate Limiter."),
        ("Kecepatan Inferensi & Beban Server", "Sangat lambat (25 – 45 detik per artikel berita). Beban RAM mencapai 94%, risiko OOM tinggi, komputasi batch memakan >20 menit.", "Sangat cepat (1,5 – 2,2 detik per artikel, 19x lebih cepat!). Beban server instansi sangat ringan, komputasi batch tuntas <1 menit tanpa OOM."),
        ("Kepatuhan Hak Cipta Pers", "Ringkasan awal masih ekstraktif (memotong teks depan artikel berita asli), berisiko melanggar hak cipta pers.", "Mematuhi UU Hak Cipta No. 28/2014 Pasal 43 huruf c: Wajib parafrase faktual (*factual paraphrasing*), tanpa copy-paste, disertai atribusi media penerbit."),
        ("Kepatuhan Web Scraping", "Scraping bebas tanpa verifikasi perizinan situs berita; rentan pemblokiran IP (HTTP 403 Forbidden).", "Modul robots_checker.py memeriksa izin robots.txt situs secara otomatis sebelum perayapan; User-Agent transparan identitas resmi CSIRT Jatim."),
        ("Penyusunan Rekomendasi Mitigasi", "Rekomendasi generatif murni dari prompt AI tanpa rujukan dokumen standar, rentan halusinasi fakta siber.", "Retrieval-Augmented Generation (RAG) berbasis Semantic Vector (text-embedding-004) terhubung ke Ensiklopedia 12 Standar Siber (165 entitas standar)."),
        ("Desain Antarmuka Visual (UI)", "Tampilan web standar seperti blog berita biasa; tombol operasional scraping terbuka untuk publik umum.", "Cyber-HUD / Tactical Dark Terminal Edition resmi selaras csirt.jatimprov.go.id (Dark Navy #0a1628, cyan neon #00d4ff, chamfered corner 10px, WCAG AAA)."),
        ("Hak Akses & Pengaturan", "Akses tunggal terbuka (tanpa sistem login dan otentikasi peran); konfigurasi hard-coded di file YAML.", "Role-Based Access Control (RBAC) dengan password bcrypt (Superadmin & Viewer); Panel Pengaturan dinamis via UI web (_settings.html).")
    ]
    
    for r_idx, (dim, b4, aft) in enumerate(ev_rows, start=1):
        row_cells = t_ev.rows[r_idx].cells
        row_cells[0].text = dim
        row_cells[1].text = b4
        row_cells[2].text = aft
        
        bg_col = "FFFFFF" if r_idx % 2 == 1 else "F8FAFC"
        for c_idx in range(3):
            c = row_cells[c_idx]
            c.width = ev_col_w[c_idx]
            set_cell_shading(c, bg_col)
            set_cell_margins(c, top=70, bottom=70, left=90, right=90)
            p = c.paragraphs[0]
            align = WD_ALIGN_PARAGRAPH.CENTER if c_idx == 0 else WD_ALIGN_PARAGRAPH.LEFT
            set_para_style(p, before=1, after=1, line_spacing=1.1, align=align)
            p.runs[0].font.name = "Calibri"
            p.runs[0].font.size = Pt(8)
            if c_idx == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(15, 30, 50)
            elif c_idx == 1:
                p.runs[0].font.color.rgb = RGBColor(120, 40, 20)
            elif c_idx == 2:
                p.runs[0].font.color.rgb = RGBColor(10, 100, 50)
                p.runs[0].font.bold = True
                
    doc.add_page_break()
    
    # ==========================================
    # METRIK PENGUJIAN RAGAS & HASIL BENCHMARK
    # ==========================================
    add_styled_heading(doc, "HASIL EVALUASI KUANTITATIF & METRIK KEBERHASILAN SISTEM", level=1, space_before=6, space_after=10)
    
    p_met = doc.add_paragraph()
    set_para_style(p_met, before=2, after=10, line_spacing=1.15)
    r = p_met.add_run("Pengujian sistem dilakukan secara bertingkat mencakup verifikasi logika unit (*unit testing*), integritas end-to-end, uji anti-halusinasi, serta evaluasi matematis pada arsitektur Retrieval-Augmented Generation (RAG) menggunakan kerangka kerja metrik standar ")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    r_b = p_met.add_run("RAGAS (Retrieval Augmented Generation Assessment)")
    r_b.font.name = "Calibri"
    r_b.font.size = Pt(10)
    r_b.font.bold = True
    r_c = p_met.add_run(" pada 50 sampel kasus insiden siber riil:")
    r_c.font.name = "Calibri"
    r_c.font.size = Pt(10)
    
    t_met = doc.add_table(rows=6, cols=4)
    t_met.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_met, color="B0BEC5", sz="4")
    
    m_headers = ["Parameter Pengujian", "Metrik / Indikator", "Nilai Capaian Sistem", "Interpretasi & Standar Keberhasilan"]
    m_col_w = [Inches(1.7), Inches(1.5), Inches(1.3), Inches(2.0)]
    
    for c_idx, h_text in enumerate(m_headers):
        c = t_met.cell(0, c_idx)
        c.width = m_col_w[c_idx]
        set_cell_shading(c, "0D2137")
        set_cell_margins(c, top=80, bottom=80, left=90, right=90)
        p = c.paragraphs[0]
        set_para_style(p, before=1, after=1, align=WD_ALIGN_PARAGRAPH.CENTER)
        run = p.add_run(h_text)
        run.font.name = "Arial"
        run.font.size = Pt(8.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    met_data = [
        ("Evaluasi RAG: Kelengkapan Dokumen", "Context Recall (RAGAS)", "0,97 (97,0%)", "Sangat Tinggi (Target > 0.85). Korpus standar siber (MITRE/NIST) berhasil ditarik lengkap sesuai konteks insiden."),
        ("Evaluasi RAG: Validitas Rekomendasi", "Faithfulness (RAGAS)", "0,96 (96,0%)", "Sangat Tinggi (Target > 0.90). 96% rekomendasi mitigasi terkunci erat pada fakta dokumen rujukan, bebas halusinasi bebas."),
        ("Guardrail Semantik CTI", "Semantic Role Separation Rate", "100,0% Valid", "Sempurna. Pihak vendor peneliti keamanan tidak pernah tertukar atau keliru dilabeli sebagai pelaku penyerang."),
        ("Kecepatan Komputasi Pipeline", "Average Inference Latency", "1,8 Detik / Artikel", "Optimal. Meningkat 19x lipat dibandingkan model lokal Ollama (35 detik), memungkinkan eksekusi harian < 1 menit."),
        ("Throughput Database SQLite", "Public Stats Aggregation Latency", "3,2 Milidetik", "Sangat Kilat. Kueri agregasi SQL dengan indeks teroptimasi melayani data dasbor instan (< 5 ms).")
    ]
    
    for r_idx, (prm, ind, val, intp) in enumerate(met_data, start=1):
        row_cells = t_met.rows[r_idx].cells
        row_cells[0].text = prm
        row_cells[1].text = ind
        row_cells[2].text = val
        row_cells[3].text = intp
        
        bg_col = "FFFFFF" if r_idx % 2 == 1 else "F8FAFC"
        for c_idx in range(4):
            c = row_cells[c_idx]
            c.width = m_col_w[c_idx]
            set_cell_shading(c, bg_col)
            set_cell_margins(c, top=70, bottom=70, left=80, right=80)
            p = c.paragraphs[0]
            align = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [1, 2] else WD_ALIGN_PARAGRAPH.LEFT
            set_para_style(p, before=1, after=1, line_spacing=1.1, align=align)
            p.runs[0].font.name = "Calibri"
            p.runs[0].font.size = Pt(8)
            if c_idx == 0:
                p.runs[0].font.bold = True
            elif c_idx == 2:
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0, 130, 70)
                
    doc.add_page_break()
    
    # ==========================================
    # LAMPIRAN RIWAYAT COMMIT GIT RESMI
    # ==========================================
    add_styled_heading(doc, "LAMPIRAN: RIWAYAT COMMIT REPOSITORI GIT SIBERHARIAN", level=1, space_before=6, space_after=10)
    
    p_git = doc.add_paragraph()
    set_para_style(p_git, before=2, after=10, line_spacing=1.15)
    r = p_git.add_run("Tabel berikut membuktikan keaslian dan kronologi riil pengembangan kode sumber proyek SiberHarian yang tercatat secara resmi pada log repositori Git (*commit history*):")
    r.font.name = "Calibri"
    r.font.size = Pt(10)
    
    t_git = doc.add_table(rows=10, cols=4)
    t_git.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(t_git, color="B0BEC5", sz="4")
    
    g_headers = ["Commit Hash", "Tanggal & Waktu", "Pesan Commit", "Signifikansi Perubahan Teknis"]
    g_col_w = [Inches(1.0), Inches(1.5), Inches(1.2), Inches(2.8)]
    
    for c_idx, h_text in enumerate(g_headers):
        c = t_git.cell(0, c_idx)
        c.width = g_col_w[c_idx]
        set_cell_shading(c, "0D2137")
        set_cell_margins(c, top=80, bottom=80, left=90, right=90)
        p = c.paragraphs[0]
        set_para_style(p, before=1, after=1, align=WD_ALIGN_PARAGRAPH.CENTER)
        run = p.add_run(h_text)
        run.font.name = "Arial"
        run.font.size = Pt(8.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        
    git_commits = [
        ("f1786aa", "20 Agu 2026 13:44 WIB", "first commit", "Inisialisasi basis kode resmi v1.0.0 (72 berkas, +15.488 baris); modul scraper, SQLite db, FastAPI, Jinja2 template."),
        ("cc96e8d", "24 Agu 2026 22:14 WIB", "update v2", "Penambahan Server-Sent Events (SSE) terminal monitor real-time, tab tren awal, modal detail berita (+5.281 baris)."),
        ("98a42e7", "01 Sep 2026 14:25 WIB", "update v3", "Pembersihan cache, berkas PRODUCT.md resmi, penegakan aturan parafrase faktual ketat demi mematuhi UU Hak Cipta No. 28/2014."),
        ("bd271f4", "10 Sep 2026 11:05 WIB", "update v4", "Penambahan logo resmi CSIRT Jatim, skrip audit kualitas feed RSS (audit_feeds.py), perbaikan layout evaluasi tengah magang (+4.807 baris)."),
        ("8bddc2f", "15 Sep 2026 07:40 WIB", "update v5", "Modularisasi JavaScript (tren-*.js), generator ekspor PDF resmi CSIRT, inisialisasi RAG engine, adopsi aturan antislop UI & WCAG AAA."),
        ("20a6eed", "23 Sep 2026 08:20 WIB", "update v6", "Integrasi 12 framework ensiklopedia siber (165 entitas), agen CTI modular SIMP, tab statistik publik dinamis, test suite 25 studi kasus (+6.645 baris)."),
        ("46bb58d", "27 Sep 2026 22:37 WIB", "update v7", "PIVOT AI: Migrasi total Ollama lokal ke Google Gemini API (fallback chain), vector embedding text-embedding-004, RBAC bcrypt, modul robots_checker.py."),
        ("03c8595", "28 Sep 2026 08:41 WIB", "update v8", "Penyempurnaan layout admin dan publik, perbaikan query SQL statistik, optimasi performa render modal dan cards."),
        ("9b1aceb", "29 Sep 2026 09:24 WIB", "update v9", "PIVOT FUNDAMENTAL v3.0.0: Eradikasi total modul CVE (-680 baris cve_fetcher.py), adopsi 10 Sektor IIV Perpres 82/2022, Threat Posture CTI, redesign total Cyber-HUD CSIRT Jatim.")
    ]
    
    for r_idx, (chash, cdate, cmsg, csig) in enumerate(git_commits, start=1):
        row_cells = t_git.rows[r_idx].cells
        row_cells[0].text = chash
        row_cells[1].text = cdate
        row_cells[2].text = cmsg
        row_cells[3].text = csig
        
        bg_col = "FFFFFF" if r_idx % 2 == 1 else "F8FAFC"
        for c_idx in range(4):
            c = row_cells[c_idx]
            c.width = g_col_w[c_idx]
            set_cell_shading(c, bg_col)
            set_cell_margins(c, top=70, bottom=70, left=80, right=80)
            p = c.paragraphs[0]
            align = WD_ALIGN_PARAGRAPH.CENTER if c_idx in [0, 1] else WD_ALIGN_PARAGRAPH.LEFT
            set_para_style(p, before=1, after=1, line_spacing=1.1, align=align)
            p.runs[0].font.name = "Calibri"
            p.runs[0].font.size = Pt(8)
            if c_idx == 0:
                p.runs[0].font.name = "Consolas"
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0, 100, 180)
            elif c_idx == 2:
                p.runs[0].font.bold = True
                
    output_filename = "Logbook_Magang_SiberHarian_Diskominfo_Jatim.docx"
    doc.save(output_filename)
    print(f"File dokumen Word berhasil digenerasi dengan sempurna: {output_filename}")
    return output_filename

if __name__ == "__main__":
    create_document()
