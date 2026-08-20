if __name__ == "__main__":
    import yaml
    from pathlib import Path

    config_path = Path(__file__).resolve().parents[2] / "config" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    cve_cfg = config["cve_source"]
    pipeline_cfg = config["pipeline"]
    daftar_vendor = config.get("known_vendors", [])

    df_cve = ambil_cve_terbaru(
        base_url=cve_cfg["base_url"],
        window_hours=pipeline_cfg.get("window_hours", 24),
        min_cvss_score=cve_cfg.get("min_cvss_score", 7.0),
        daftar_vendor_dikenal=daftar_vendor,
    )

    struktur = susun_struktur_digest_cve(df_cve)
    print(f"Mode: {struktur['mode']}")

    if struktur["mode"] == "ada_critical":
        print(f"Total CRITICAL: {struktur['jumlah_critical_total']}, Total HIGH: {struktur['jumlah_high_total']}")
        for grup in struktur["grup_critical"][:5]:
            print(f"\n=== {grup['vendor']} ({grup['jumlah_critical']} CRITICAL) ===")
            for cve in grup["cve_list"][:2]:
                print(f"  {cve['cve_id']} (CVSS {cve['skor_cvss']}) - {cve['produk']}")
    elif struktur["mode"] == "high_saja":
        print(f"Total HIGH: {struktur['jumlah_high_total']}, ditampilkan top {len(struktur['high_untuk_narasi'])}")