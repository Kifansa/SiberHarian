def _generate_section_1_makro(data_makro: dict, model: str = "llama3.2") -> str:
    pola_makro = data_makro.get("nama_pola", "Insiden Terkini")
    korpus = data_makro.get("korpus_artikel", "")
    user_prompt = f"Topik Dominan: {pola_makro}\nFakta Riil:\n{korpus[:1500]}\n\nInstruksi: Sintesis 1 paragraf mengalir sesuai pedoman."
    hasil = _call_ollama_text(SYSTEM_PROMPT_SEC1_MAKRO, user_prompt, model, num_predict=350)
    if not hasil or len(hasil) < 50:
        return f"Pola ancaman **{pola_makro}** mencatatkan eskalasi minggu ini."
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_2_mikro(top3_mikro: list, model: str = "llama3.2") -> str:
    if not top3_mikro:
        return "- (Belum ada data insiden aktif minggu ini)"
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    baris_input = []
    for idx, inc in enumerate(top3_mikro):
        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")
        fakta = inc.get("uraian_fakta", "")
        baris_input.append(f"{idx+1}. Kampanye: \"{nama_clean}\" ({inc.get('jumlah_artikel', 1)} laporan berita)\n   Detail: {fakta[:400]}")
    user_prompt = "Sintesiskan TEPAT 3 insiden berikut:\n\n" + "\n\n".join(baris_input)
    hasil = _call_ollama_text(SYSTEM_PROMPT_SEC2_MIKRO, user_prompt, model, num_predict=500)
    if not hasil or len(hasil) < 60:
        return "\n".join(f"- **{inc.get('nama_insiden', '')}**: {inc.get('uraian_fakta', '')[:100]}..." for inc in top3_mikro)
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_3_vektor(top3_mikro: list, model: str = "llama3.2") -> str:
    if not top3_mikro:
        return "- (Belum ada vektor ancaman aktif yang dilaporkan)"
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    baris_input = []
    for idx, inc in enumerate(top3_mikro):
        nama_clean, _ = _bersihkan_judul_dan_publisher(inc.get("nama_insiden", ""), "")
        fakta = inc.get("uraian_fakta", "")
        baris_input.append(f"{idx+1}. Kampanye: \"{nama_clean}\"\n   Detail Serangan: {fakta[:400]}")
    user_prompt = "Petakan alur teknis dan taktik MITRE ATT&CK dari insiden berikut:\n\n" + "\n\n".join(baris_input)
    hasil = _call_ollama_text(SYSTEM_PROMPT_SEC3_VEKTOR, user_prompt, model, num_predict=450)
    if not hasil or len(hasil) < 60:
        return "\n".join(f"- **Alur Serangan {inc.get('nama_insiden', '')}**: {inc.get('uraian_fakta', '')[:100]}..." for inc in top3_mikro)
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()

def _generate_section_5_emerging(ancaman_baru: dict, model: str = "llama3.2") -> str:
    nama_anc = ancaman_baru.get("nama", "Tidak Teridentifikasi")
    uraian_anc = ancaman_baru.get("uraian", "")
    if not ancaman_baru.get("ada"):
        return "Berdasarkan pemantauan korpus intelijen siber Jawa Timur minggu ini, tidak ditemukan sinyal anomali atau ancaman baru."
    user_prompt = f"Ancaman Baru Terdeteksi: {nama_anc}\nDetail Sinyal Ancaman:\n{uraian_anc[:1000]}\n\nInstruksi: Susun 1 paragraf analisis sinyal ancaman."
    hasil = _call_ollama_text(SYSTEM_PROMPT_SEC5_EMERGING, user_prompt, model, num_predict=300)
    if not hasil or len(hasil) < 50:
        return f"Terdeteksi sinyal ancaman baru berupa **{nama_anc}**. {uraian_anc[:200]}"
    return re.sub(r'^#+.*\n+', '', _bersihkan_tanggal_jika_ada(hasil)).strip()
