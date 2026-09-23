import re

with open("src/analytics/pasca_proses.py", "r", encoding="utf-8") as f:
    content = f.read()

new_func = """
def _susun_item_arsip_berita(df_berita_ringkas) -> List[Dict]:
    \"\"\"Meratakan DataFrame berita (sudah ada kolom 'ringkasan') jadi list dict siap disimpan.\"\"\"
    if df_berita_ringkas.empty:
        return []
    df = df_berita_ringkas.copy()
    df['kategori'] = 'berita'
    df['identifier'] = df['link']
    df['severity'] = ''
    df['vendor'] = ''
    df['tanggal_publish'] = df.get('tanggal', '')
    df['ringkasan_atau_narasi'] = df.get('ringkasan', '')
    
    if 'kata_kunci' not in df.columns:
        df['kata_kunci'] = ''
    if 'kategori_relevansi' not in df.columns:
        df['kategori_relevansi'] = ''
        
    cols = ['kategori', 'identifier', 'judul', 'sumber', 'kata_kunci', 'kategori_relevansi', 
            'severity', 'vendor', 'tanggal_publish', 'ringkasan_atau_narasi', 'link']
    return df[cols].to_dict('records')
"""

content = re.sub(r"def _susun_item_arsip_berita\(df_berita_ringkas\) -> List\[Dict\]:.*?for _, row in df_berita_ringkas\.iterrows\(\)\n\s+\]", new_func.strip(), content, flags=re.DOTALL)

with open("src/analytics/pasca_proses.py", "w", encoding="utf-8") as f:
    f.write(content)
