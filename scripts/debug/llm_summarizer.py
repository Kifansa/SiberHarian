if __name__ == "__main__":
    # Testing manual: python -m src.summarizer.llm_summarizer
    from pathlib import Path

    from src.pipeline_harian import jalankan_pipeline_harian

    hasil_mentah = jalankan_pipeline_harian()

    # --- opsional: batasi jumlah artikel dulu untuk tes cepat ---
    # Uncomment baris di bawah kalau mau tes cepat tanpa nunggu semua artikel diringkas.
    # hasil_mentah["berita"] = hasil_mentah["berita"].head(5).reset_index(drop=True)

    hasil_ringkas = proses_summarization_harian(hasil_mentah)

    Path("data").mkdir(parents=True, exist_ok=True)

    # --- Ekspor CSV: Berita ---
    df_berita = hasil_ringkas["berita"]
    if not df_berita.empty:
        df_berita[["sumber", "judul", "tanggal", "teks_asli", "ringkasan", "link"]].to_csv(
            "data/cek_ringkasan_berita.csv", index=False, encoding="utf-8-sig"
        )
        print(f"Tersimpan {len(df_berita)} ringkasan berita ke data/cek_ringkasan_berita.csv")
    else:
        print("Tidak ada berita untuk diringkas.")

    # --- Ekspor CSV: CVE ---
    cve_struktur = hasil_ringkas["cve_struktur"]
    baris_cve = []

    if cve_struktur["mode"] == "ada_critical":
        for grup in cve_struktur["grup_critical"]:
            for cve in grup["cve_list"]:
                baris_cve.append({
                    "vendor_grup": grup["vendor"],
                    "cve_id": cve["cve_id"],
                    "severity": cve["severity"],
                    "skor_cvss": cve["skor_cvss"],
                    "produk": cve["produk"],
                    "deskripsi_asli": cve["deskripsi"],
                    "narasi": cve.get("narasi", ""),
                    "link": cve["link"],
                })
    elif cve_struktur["mode"] == "high_saja":
        for cve in cve_struktur["high_untuk_narasi"]:
            baris_cve.append({
                "vendor_grup": cve.get("vendor", "-"),
                "cve_id": cve["cve_id"],
                "severity": cve["severity"],
                "skor_cvss": cve["skor_cvss"],
                "produk": cve["produk"],
                "deskripsi_asli": cve["deskripsi"],
                "narasi": cve.get("narasi", ""),
                "link": cve["link"],
            })

    if baris_cve:
        pd.DataFrame(baris_cve).to_csv(
            "data/cek_ringkasan_cve.csv", index=False, encoding="utf-8-sig"
        )
        print(f"Tersimpan {len(baris_cve)} baris CVE ke data/cek_ringkasan_cve.csv")
    else:
        print(f"Tidak ada CVE untuk ditampilkan (mode: {cve_struktur['mode']}).")