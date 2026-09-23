import re

with open("src/analytics/cti_agents.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add the function back
func_to_add = """
def _generate_section_4_rekomendasi(top3_mikro: list) -> str:
    poin_rekomendasi = []
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher
    for idx, inc in enumerate(top3_mikro):
        nama_raw = inc.get("nama_insiden", f"Insiden Siber {idx+1}")
        nama, _ = _bersihkan_judul_dan_publisher(nama_raw, "")
        mitigasi = inc.get("mitigasi_ensiklopedia", [])

        mit_items = "\\n".join([f"- {m}" for m in mitigasi[:2]]) if mitigasi else "- [D3-MFA] Wajibkan autentikasi multifaktor berbasis token pada seluruh akses administratif.\\n- [NIST PR.AC] Terapkan segmentasi jaringan dan prinsip hak akses minimal."
        poin_rekomendasi.append(
            f"**Rekomendasi Aksi untuk {nama}**\\n{mit_items}"
        )
    return "\\n\\n".join(poin_rekomendasi)

def jalankan_pipeline_multi_agent(
"""

content = content.replace("def jalankan_pipeline_multi_agent(", func_to_add)

with open("src/analytics/cti_agents.py", "w", encoding="utf-8") as f:
    f.write(content)
