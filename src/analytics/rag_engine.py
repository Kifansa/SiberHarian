"""
Modul RAG (Retrieval-Augmented Generation) & Analisis Pola Ancaman CTI.
Mengambil fakta artikel riil dari riwayat_tren di SQLite untuk diinjeksikan
ke prompt LLM (grounded context), serta menghitung proyeksi 1 pola serangan
terdepan (1 kata) berdasarkan momentum eskalasi historis.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "state.db"


class RAGEngine:
    """
    Engine RAG sederhana dan teroptimasi untuk mengambil korpus berita riil
    dan mengevaluasi proyeksi pola serangan berdasarkan data historis.
    """

    def __init__(self, df_riwayat: Optional[pd.DataFrame] = None):
        self.df_riwayat = df_riwayat if df_riwayat is not None else pd.DataFrame()
        self.df_berita = pd.DataFrame()
        self.df_cve = pd.DataFrame()

        if not self.df_riwayat.empty:
            if "kategori" in self.df_riwayat.columns:
                self.df_berita = self.df_riwayat[self.df_riwayat["kategori"] == "berita"].copy()
                self.df_cve = self.df_riwayat[self.df_riwayat["kategori"] == "cve"].copy()

    def retrieve_berita_context(
        self,
        top_keywords: List[str],
        top_vectors: Optional[List[str]] = None,
        limit: int = 7
    ) -> str:
        """
        Mengambil sampel artikel berita asli paling relevan berdasarkan kecocokan
        kata kunci tren lonjakan dan vektor ancaman utama.
        """
        if self.df_berita.empty:
            return "(Tidak ada korpus berita pada database)"

        # Bersihkan list kata kunci pencarian
        kw_set = [k.lower().strip() for k in top_keywords if k and len(k.strip()) > 2]
        vector_set = [v.lower().strip() for v in (top_vectors or []) if v]

        scored_articles = []
        for _, row in self.df_berita.iterrows():
            judul = str(row.get("judul", "")).strip()
            ringkasan = str(row.get("ringkasan_atau_narasi", "")).strip()
            kata_kunci = str(row.get("kata_kunci", "")).strip()
            sumber = str(row.get("sumber", "Media")).strip()

            teks_gabung = f"{judul} {ringkasan} {kata_kunci}".lower()

            score = 0
            # Pembobotan judul berita
            for kw in kw_set:
                if kw in judul.lower():
                    score += 3
                elif kw in teks_gabung:
                    score += 1

            for vec in vector_set:
                if vec in teks_gabung:
                    score += 1

            # Bonus untuk insiden berbobot tinggi
            if any(term in teks_gabung for term in ["infostealer", "rce", "phishing", "bocor", "paspor", "otp", "apk", "zero-day", "ransomware"]):
                score += 1

            if score > 0:
                scored_articles.append((score, sumber, judul, ringkasan))

        # Urutkan berdasarkan relevansi skor tertinggi
        scored_articles.sort(key=lambda x: x[0], reverse=True)

        # Ambil deduplikasi judul agar beragam
        judul_terpilih = set()
        chunks = []
        for _, sumber, judul, ringkasan in scored_articles:
            if judul in judul_terpilih:
                continue
            judul_terpilih.add(judul)

            ringkas_teks = ringkasan[:220] + ("..." if len(ringkasan) > 220 else "") if ringkasan else judul
            chunks.append(f"- [{sumber}] \"{judul}\": {ringkas_teks}")

            if len(chunks) >= limit:
                break

        if not chunks:
            # Fallback ke artikel terkini
            for _, row in self.df_berita.head(limit).iterrows():
                sumber = row.get("sumber", "Media")
                judul = row.get("judul", "-")
                ringkas_teks = str(row.get("ringkasan_atau_narasi", ""))[:200]
                chunks.append(f"- [{sumber}] \"{judul}\": {ringkas_teks}")

        return "\n".join(chunks)

    def retrieve_cve_context(self, top_vendors: List[str], limit: int = 5) -> str:
        """
        Mengambil sampel entri kerentanan CVE kritis yang relevan dengan vendor lonjakan tertinggi.
        """
        if self.df_cve.empty:
            return "(Tidak ada data CVE pada database)"

        vendor_set = [v.lower().strip() for v in top_vendors if v]
        cve_chunks = []
        cve_terpilih = set()

        for _, row in self.df_cve.iterrows():
            cve_id = str(row.get("identifier", "-")).strip()
            vendor = str(row.get("vendor", "")).strip()
            produk = str(row.get("produk", "")).strip()
            ringkasan = str(row.get("ringkasan_atau_narasi", "")).strip()
            cvss = row.get("skor_cvss", "-")

            if any(v in vendor.lower() for v in vendor_set):
                if cve_id in cve_terpilih:
                    continue
                cve_terpilih.add(cve_id)
                ringkas_teks = ringkasan[:180] + ("..." if len(ringkasan) > 180 else "") if ringkasan else f"Kerentanan pada {produk}"
                cve_chunks.append(f"- [{cve_id}] {vendor} - {produk} (CVSS: {cvss}): {ringkas_teks}")

                if len(cve_chunks) >= limit:
                    break

        return "\n".join(cve_chunks) if cve_chunks else "(Volume CVE vendor stabil)"

    def retrieve_regional_context(self, cluster_items: List[Dict], wilayah_label: str, limit: int = 10) -> str:
        """
        Menyusun korpus fakta artikel riil untuk analisis makro ancaman wilayah (RAG).
        Setiap entri menyertakan sumber, tanggal, liputan, konteks ringkasan, dan tautan.
        """
        if not cluster_items:
            return f"(Tidak ada insiden siber aktif pada wilayah {wilayah_label} dalam database)"

        chunks = []
        for c in cluster_items[:limit]:
            sumber = c.get("sumber", "Media")
            judul = c.get("judul", "-")
            ringkasan = c.get("ringkasan", "")
            tgl = c.get("tanggal", "")
            liputan = c.get("jumlah_liputan", 1)
            media_lain = f" + media lain ({', '.join(c.get('media_lain', [])[:2])})" if c.get("media_lain") else ""
            link = c.get("link", "#")

            ringkas_teks = ringkasan[:220] + ("..." if len(ringkasan) > 220 else "") if ringkasan else judul
            chunks.append(
                f"- [{sumber} | {tgl} | Liputan: {liputan} media{media_lain}] \"{judul}\"\n"
                f"  Konteks Insiden: {ringkas_teks}\n"
                f"  Link: {link}"
            )

        return "\n".join(chunks)

    def hitung_prediksi_pola_serangan(self) -> Dict:
        """
        Menganalisis data historis 14 hari (7 hari terkini vs 7 hari baseline)
        untuk mengidentifikasi 1 pola serangan yang paling berisiko / kemungkinan besar terjadi.
        Output pola tepat 1 KATA untuk kebutuhan ringkasan KPI eksekutif.
        """
        fallback = {
            "pola": "Ransomware",
            "growth_persen": 0.0,
            "jumlah_terkini": 0,
            "tingkat_risiko": "SEDANG",
            "subteks": "Tren Relatif Stabil"
        }

        if self.df_berita.empty:
            return fallback

        from src.analytics.trend_analyzer import _split_periode, _dedup_ringan_lintas_hari, _hitung_growth

        df_dedup = _dedup_ringan_lintas_hari(self.df_berita)
        df_terkini, df_baseline = _split_periode(df_dedup)

        if df_terkini.empty:
            return fallback

        # Taksonomi 5 pola serangan utama (1 kata representatif)
        KATALOG_POLA = {
            "RCE": ["rce", "remote code execution", "eksploitasi celah", "zero-day", "0-day", "vulnerability exploit"],
            "Infostealer": ["infostealer", "stealer", "trojan", "lumma", "redline", "vidar", "pencuri data", "malware apk", "otax"],
            "Phishing": ["phishing", "spear-phishing", "rekayasa sosial", "social engineering", "penipuan online", "otp"],
            "Ransomware": ["ransomware", "tebusan", "pemerasan", "lockbit", "enkripsi data"],
            "Botnet": ["botnet", "ddos", "weaponized ai", "credential stuffing", "brute force"],
        }

        hasil_analisis = []
        for nama_pola, keywords in KATALOG_POLA.items():
            cnt_terkini = sum(
                any(k in (str(r.get("judul", "")) + " " + str(r.get("ringkasan_atau_narasi", "")) + " " + str(r.get("kata_kunci", ""))).lower() for k in keywords)
                for _, r in df_terkini.iterrows()
            )
            cnt_baseline = sum(
                any(k in (str(r.get("judul", "")) + " " + str(r.get("ringkasan_atau_narasi", "")) + " " + str(r.get("kata_kunci", ""))).lower() for k in keywords)
                for _, r in df_baseline.iterrows()
            )
            growth = _hitung_growth(cnt_terkini, cnt_baseline)

            # Skor momentum = kombinasi pertumbuhan relatif dan bobot volume insiden terkini
            # Pola yang mengalami lonjakan tajam (> 20%) mendapatkan prioritas ancaman eskalasi
            skor_momentum = cnt_terkini * (1.0 + (growth / 100.0 if growth > 0 else 0.0))
            if growth >= 30.0:
                skor_momentum *= 1.4  # Bobot eskalasi aktif

            hasil_analisis.append({
                "pola": nama_pola,
                "growth_persen": growth,
                "jumlah_terkini": cnt_terkini,
                "jumlah_baseline": cnt_baseline,
                "skor": skor_momentum
            })

        # Urutkan berdasarkan skor momentum tertinggi
        hasil_analisis.sort(key=lambda x: (x["growth_persen"] > 0, x["skor"], x["jumlah_terkini"]), reverse=True)
        top = hasil_analisis[0] if hasil_analisis else None

        if not top or top["jumlah_terkini"] == 0:
            return fallback

        # Format subteks ringkas untuk badge KPI
        if top["growth_persen"] > 0:
            subteks = f"+{top['growth_persen']}% vs baseline"
        else:
            subteks = f"{top['jumlah_terkini']} insiden terdeteksi"

        return {
            "pola": top["pola"],  # 1 KATA: RCE, Infostealer, Phishing, Ransomware, atau Botnet
            "growth_persen": top["growth_persen"],
            "jumlah_terkini": top["jumlah_terkini"],
            "tingkat_risiko": "TINGGI" if top["growth_persen"] >= 20.0 else "SEDANG",
            "subteks": subteks
        }
