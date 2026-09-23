"""
Modul RAG (Retrieval-Augmented Generation) & Analisis Pola Ancaman CTI.
Mengambil fakta artikel riil dari riwayat_tren di SQLite untuk diinjeksikan
ke prompt LLM (grounded context), serta menghitung proyeksi 1 pola serangan
terdepan (1 kata) berdasarkan momentum eskalasi historis.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from src.utils.config_loader import ConfigLoader
import re
from collections import Counter

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
                self.df_berita = self.df_riwayat[
                    (self.df_riwayat["kategori"] == "berita") & 
                    (self.df_riwayat["kategori_relevansi"] == "insiden_spesifik")
                ].copy()
                self.df_cve = self.df_riwayat[self.df_riwayat["kategori"] == "cve"].copy()

    def _extract_top_keywords(self, df: pd.DataFrame, top_n: int = 10) -> List[str]:
        """Ekstrak kata kunci dominan dari dataset secara dinamis."""
        all_keywords = []
        for _, row in df.iterrows():
            kws = str(row.get('kata_kunci', '')).split(',')
            for kw in kws:
                clean_kw = kw.strip().lower()
                if len(clean_kw) > 2:
                    all_keywords.append(clean_kw)
        
        if not all_keywords:
            return []
        return [k for k, v in Counter(all_keywords).most_common(top_n)]

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
            # Pembobotan
            rag_cfg = ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {})
            w_title = rag_cfg.get("scoring", {}).get("title_match_weight", 3)
            w_body = rag_cfg.get("scoring", {}).get("body_match_weight", 1)
            w_vector = rag_cfg.get("scoring", {}).get("vector_match_weight", 1)

            for kw in kw_set:
                if kw in judul.lower():
                    score += w_title
                elif kw in teks_gabung:
                    score += w_body

            for vec in vector_set:
                if vec in teks_gabung:
                    score += w_vector

            for vec in vector_set:
                if vec in teks_gabung:
                    score += 1

            if score > 0:
                tanggal = str(row.get("tanggal_publikasi", "Tanggal tidak diketahui")).split()[0]
                scored_articles.append((score, sumber, judul, ringkasan, tanggal))

        # Urutkan berdasarkan relevansi skor tertinggi
        scored_articles.sort(key=lambda x: x[0], reverse=True)

        # Ambil deduplikasi judul agar beragam
        judul_terpilih = set()
        chunks = []
        for _, sumber, judul, ringkasan, tanggal in scored_articles:
            if judul in judul_terpilih:
                continue
            judul_terpilih.add(judul)

            ringkas_teks = ringkasan[:ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("truncation", {}).get("berita_preview", 220)] + ("..." if len(ringkasan) > 220 else "") if ringkasan else judul
            chunks.append(f"- [{sumber} | {tanggal}] \"{judul}\": {ringkas_teks}")

            if len(chunks) >= limit:
                break

        if not chunks:
            # Fallback ke artikel terkini
            for _, row in self.df_berita.head(limit).iterrows():
                sumber = row.get("sumber", "Media")
                tanggal = str(row.get("tanggal_publikasi", "Tanggal tidak diketahui")).split()[0]
                judul = row.get("judul", "-")
                ringkas_teks = str(row.get("ringkasan_atau_narasi", ""))[:200]
                chunks.append(f"- [{sumber} | {tanggal}] \"{judul}\": {ringkas_teks}")

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
                ringkas_teks = ringkasan[:ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("truncation", {}).get("regional_preview", 180)] + ("..." if len(ringkasan) > 180 else "") if ringkasan else f"Kerentanan pada {produk}"
                cve_chunks.append(f"- [{cve_id}] {vendor} - {produk} (CVSS: {cvss}): {ringkas_teks}")

                if len(cve_chunks) >= limit:
                    break

        return "\n".join(cve_chunks) if cve_chunks else "(Volume CVE vendor stabil)"

    def retrieve_regional_context(self, cluster_items: List[Dict], wilayah_label: str, limit: int = 10) -> str:
        """
        Menyusun korpus fakta artikel riil untuk analisis makro ancaman wilayah (RAG).
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

            ringkas_teks = ringkasan[:ConfigLoader.get_config().get("cti_analysis", {}).get("rag", {}).get("truncation", {}).get("berita_preview", 220)] + ("..." if len(ringkasan) > 220 else "") if ringkasan else judul
            chunks.append(
                f"- [{sumber} | {tgl} | Liputan: {liputan} media{media_lain}] \"{judul}\"\n"
                f"  Konteks Insiden: {ringkas_teks}\n"
                f"  Link: {link}"
            )

        return "\n".join(chunks)

    def hitung_prediksi_pola_serangan(self) -> Dict[str, Any]:
        """
        Menganalisis data historis 14 hari menggunakan RAG lonjakan makro
        untuk mengidentifikasi 1 pola insiden yang mengalami eskalasi paling pesat.
        Semua bersifat dinamis berbasis frekuensi kata kunci dataset.
        """
        fallback = {
            "pola": "Insiden Dominan",
            "growth_persen": 0.0,
            "jumlah_terkini": 0,
            "tingkat_risiko": "SEDANG",
            "subteks": "vs minggu lalu"
        }

        if self.df_berita.empty:
            return fallback

        spiking = self.ambil_data_tren_makro_spiking()
        nama_pola = spiking.get("nama_pola", "Insiden Siber")
        
        # Ekstrak kata yang paling representatif dari nama pola (dinamis)
        pola_singkat = nama_pola[:20].strip().title() if nama_pola else "Insiden Dominan"
        growth = spiking.get("growth_persen", 0.0)
        jml = spiking.get("jumlah_artikel", 0)

        return {
            "pola": pola_singkat,
            "pola_lengkap": nama_pola,
            "growth_persen": int(growth),
            "jumlah_terkini": jml,
            "tingkat_risiko": "TINGGI" if growth >= 20.0 else "SEDANG",
            "subteks": "vs minggu lalu"
        }

    def hitung_prediksi_ancaman_baru(self) -> str:
        """
        Menganalisis data empiris RAG untuk mengidentifikasi 1-2 kata sinyal lemah (Emerging Threat).
        Dibuat sepenuhnya dinamis berdasar kata kunci yang tidak lazim / baru muncul.
        """
        if self.df_berita.empty:
            return "Kondisi Stabil"

        ancaman = self.ambil_berita_ancaman_baru()
        if not ancaman.get("ada"):
            return "Kondisi Stabil"

        nama = ancaman.get("nama", "")
        # Ekstrak representasi ringkas untuk UI / sinyal alert
        words = re.findall(r'[A-Za-z]{4,}', nama)
        if len(words) >= 2:
            return f"{words[0]} {words[1]}".upper()
        elif len(words) == 1:
            return words[0].upper()
        
        return "SIGNAL ALERT"

    def ambil_data_tren_makro_spiking(self) -> Dict[str, Any]:
        """
        Mengidentifikasi pola insiden mingguan yang melonjak paling cepat (growth spike tertinggi)
        secara dinamis berdasarkan klaster kata kunci.
        """
        if self.df_berita.empty:
            return {
                "nama_pola": "Insiden Siber Terkini",
                "growth_persen": 0.0,
                "jumlah_artikel": 0,
                "korpus_artikel": "(Tidak ada data insiden riil dalam database)"
            }

        from src.analytics.trend_analyzer import _split_periode, _dedup_ringan_lintas_hari, _hitung_growth

        df_dedup = _dedup_ringan_lintas_hari(self.df_berita)
        df_terkini, df_baseline = _split_periode(df_dedup)

        if df_terkini.empty:
            df_terkini = df_dedup

        # Bangun pola dinamis berdasarkan kata kunci paling top di df_terkini
        top_kws = self._extract_top_keywords(df_terkini, top_n=6)
        
        kandidat = []
        for kw in top_kws:
            matching_terkini = []
            for _, r in df_terkini.iterrows():
                teks = f"{r.get('judul', '')} {r.get('ringkasan_atau_narasi', '')} {r.get('kata_kunci', '')}".lower()
                if kw in teks:
                    matching_terkini.append(r)

            matching_baseline = []
            for _, r in df_baseline.iterrows():
                teks = f"{r.get('judul', '')} {r.get('ringkasan_atau_narasi', '')} {r.get('kata_kunci', '')}".lower()
                if kw in teks:
                    matching_baseline.append(r)

            cnt_terkini = len(matching_terkini)
            cnt_baseline = len(matching_baseline)
            growth = _hitung_growth(cnt_terkini, cnt_baseline)

            if cnt_terkini > 0:
                kandidat.append({
                    "nama_pola": f"Tren Lonjakan: {kw.title()}",
                    "growth_persen": growth,
                    "jumlah_terkini": cnt_terkini,
                    "artikel": matching_terkini
                })

        kandidat.sort(key=lambda x: (x["growth_persen"] > 0, x["growth_persen"], x["jumlah_terkini"]), reverse=True)
        top_spiking = kandidat[0] if kandidat else None

        if not top_spiking:
            top_spiking = {
                "nama_pola": "Insiden Siber Terkini",
                "growth_persen": 0.0,
                "jumlah_terkini": len(df_terkini),
                "artikel": [r for _, r in df_terkini.head(5).iterrows()]
            }

        cuplikan = []
        for r in top_spiking["artikel"][:6]:
            judul = r.get("judul", "-")
            ringkasan = str(r.get("ringkasan_atau_narasi", ""))
            cuplikan.append(f"- Judul: \"{judul}\"\n  Fakta & Kronologi: {ringkasan}")

        return {
            "nama_pola": top_spiking["nama_pola"],
            "growth_persen": top_spiking["growth_persen"],
            "jumlah_artikel": top_spiking["jumlah_terkini"],
            "korpus_artikel": "\n\n".join(cuplikan)
        }

    def ambil_top3_insiden_mikro(self) -> List[Dict[str, Any]]:
        """
        Mengambil TOP 3 insiden yang paling banyak dalam minggu ini menggunakan
        enhanced fuzzy clustering dinamis tanpa aturan entitas statis.
        """
        if self.df_berita.empty:
            return []

        from src.analytics.trend_analyzer import _split_periode, _bersihkan_judul_dan_publisher
        from rapidfuzz import fuzz

        df_terkini, _ = _split_periode(self.df_berita)
        if df_terkini.empty:
            df_terkini = self.df_berita

        unclustered = df_terkini.to_dict('records')
        clusters = {}

        # Klastering murni berbasis fuzzy kemiripan gabungan (judul + kata kunci)
        sudah_diproses = set()
        for i in range(len(unclustered)):
            if i in sudah_diproses:
                continue
            row_i = unclustered[i]
            raw_j_i = str(row_i.get("judul", "")).strip()
            kw_i = str(row_i.get("kata_kunci", "")).strip()
            clean_j_i, _ = _bersihkan_judul_dan_publisher(raw_j_i, "")
            
            sig_i = f"{clean_j_i} {kw_i}".lower()

            artikel_klaster = [row_i]
            sudah_diproses.add(i)

            for j in range(i + 1, len(unclustered)):
                if j in sudah_diproses:
                    continue
                row_j = unclustered[j]
                raw_j_j = str(row_j.get("judul", "")).strip()
                kw_j = str(row_j.get("kata_kunci", "")).strip()
                clean_j_j, _ = _bersihkan_judul_dan_publisher(raw_j_j, "")
                
                sig_j = f"{clean_j_j} {kw_j}".lower()

                # Gunakan token_set_ratio yang andal untuk word intersection
                if fuzz.token_set_ratio(sig_i, sig_j) >= 65:
                    sudah_diproses.add(j)
                    artikel_klaster.append(row_j)

            # Penamaan dinamis klaster: gunakan judul dari artikel pertama / paling representatif
            cid = f"dynamic_cluster_{i}"
            
            # Coba ekstrak kata kunci representatif dari klaster ini
            klaster_kws = []
            for ak in artikel_klaster:
                klaster_kws.extend([k.strip().title() for k in str(ak.get("kata_kunci", "")).split(",") if len(k.strip()) > 3])
            
            pola_nama = clean_j_i
            if klaster_kws:
                top_kw = Counter(klaster_kws).most_common(1)[0][0]
                pola_nama = f"Kampanye {top_kw}: {clean_j_i[:40]}..."

            clusters[cid] = {
                "judul_utama": clean_j_i,
                "nama_kampanye": pola_nama,
                "artikel_list": artikel_klaster
            }

        daftar_klaster = []
        for c in clusters.values():
            c["jumlah_artikel"] = len(c["artikel_list"])
            daftar_klaster.append(c)

        # Urutkan berdasarkan jumlah frekuensi insiden
        daftar_klaster.sort(key=lambda x: x["jumlah_artikel"], reverse=True)
        top3 = daftar_klaster[:3]

        from src.analytics.encyclopedia_lookup import search_encyclopedia_per_incident

        hasil_top3 = []
        for idx, cl in enumerate(top3):
            semua_teks = []
            kata_kunci_set = set()
            for art in cl["artikel_list"]:
                j = str(art.get("judul", ""))
                r = str(art.get("ringkasan_atau_narasi", ""))
                k = str(art.get("kata_kunci", ""))
                semua_teks.append(f"• Kasus/Laporan: \"{j}\"\n  Detail Kronologi & Cara Serangan: {r}")
                for item_k in k.split(","):
                    if item_k.strip():
                        kata_kunci_set.add(item_k.strip())

            gabungan_narasi = "\n".join(semua_teks[:4])
            mitigasi_list = search_encyclopedia_per_incident(cl["nama_kampanye"], list(kata_kunci_set))

            hasil_top3.append({
                "urutan": idx + 1,
                "nama_insiden": cl["nama_kampanye"],
                "jumlah_artikel": cl["jumlah_artikel"],
                "uraian_fakta": gabungan_narasi,
                "kata_kunci": list(kata_kunci_set),
                "mitigasi_ensiklopedia": mitigasi_list,
                "artikel_list": cl["artikel_list"]
            })

        return hasil_top3

    def ambil_berita_ancaman_baru(self) -> Dict[str, Any]:
        """
        Mengambil berita yang memberitakan ancaman siber baru (emerging threats, zero-day, malware varian baru).
        Mengekstrak secara dinamis artikel paling relevan berdasarkan fitur/kata kunci TF-IDF style yang langka/baru.
        """
        if self.df_berita.empty:
            return {"ada": False, "nama": "Menunggu Sinyal", "uraian": "(Tidak ada ancaman baru)", "sumber": "-"}

        from src.analytics.trend_analyzer import _split_periode
        df_terkini, df_baseline = _split_periode(self.df_berita)
        if df_terkini.empty:
            df_terkini = self.df_berita

        # Cari kata kunci yang ADA di terkini, tapi TIDAK ADA di baseline (atau frekuensinya melonjak dari 0)
        kw_baseline = set()
        for _, r in df_baseline.iterrows():
            for k in str(r.get("kata_kunci", "")).split(","):
                if len(k.strip()) > 3:
                    kw_baseline.add(k.strip().lower())
                    
        # Filter artikel terkini yang memiliki kata kunci baru
        kandidat = []
        for _, r in df_terkini.iterrows():
            kws = [k.strip().lower() for k in str(r.get("kata_kunci", "")).split(",") if len(k.strip()) > 3]
            baru = sum(1 for k in kws if k not in kw_baseline)
            if baru > 0:
                kandidat.append((baru, r))
                
        if kandidat:
            kandidat.sort(key=lambda x: x[0], reverse=True)
            top_baru = kandidat[0][1]
            return {
                "ada": True,
                "nama": str(top_baru.get("judul", "Ancaman Baru Terdeteksi")),
                "uraian": str(top_baru.get("ringkasan_atau_narasi", "")),
                "sumber": str(top_baru.get("sumber", "Media Intelijen"))
            }

        # Fallback jika tidak ada kata kunci yang benar-benar baru
        row_first = df_terkini.iloc[0]
        return {
            "ada": True,
            "nama": str(row_first.get("judul", "-")),
            "uraian": str(row_first.get("ringkasan_atau_narasi", "")),
            "sumber": str(row_first.get("sumber", "Media Intelijen"))
        }

