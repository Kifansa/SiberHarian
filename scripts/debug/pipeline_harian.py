if __name__ == "__main__":
    # Testing manual: python -m src.pipeline_harian
    hasil = jalankan_pipeline_harian()
    print("\n=== BERITA ===")
    if not hasil["berita"].empty:
        print(hasil["berita"][["sumber", "judul"]])
    else:
        print("Tidak ada berita baru.")

    print("\n=== CVE ===")
    print(f"Mode: {hasil['cve_struktur']['mode']}")