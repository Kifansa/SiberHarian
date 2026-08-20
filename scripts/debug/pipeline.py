if __name__ == "__main__":
    # Jalankan langsung untuk testing manual: python -m src.scraper.pipeline
    df = jalankan_pipeline_berita()
    print(df[["sumber", "judul", "tanggal"]] if not df.empty else "Tidak ada artikel ditemukan.")