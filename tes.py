from src.summarizer.llm_summarizer import _panggil_llm, bersihkan_output_llm, SYSTEM_PROMPT_BERITA
import pandas as pd

df = pd.read_csv("data/perbandingan_ringkasan_v2.csv")
row = df.iloc[31]

teks_dipotong = row["teks_asli"][:4000]
user_prompt = f"Judul: {row['judul']}\n\nIsi artikel:\n{teks_dipotong}"

# Panggil LLM langsung, TANPA post-processing, untuk lihat output mentahnya
respons_mentah = _panggil_llm(SYSTEM_PROMPT_BERITA, user_prompt)
print("=== OUTPUT MENTAH (sebelum bersihkan_output_llm) ===")
print(repr(respons_mentah))

print("\n=== SETELAH bersihkan_output_llm ===")
print(repr(bersihkan_output_llm(respons_mentah, judul_atau_id=row["judul"])))