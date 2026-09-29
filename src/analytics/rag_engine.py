"""
Modul RAG (Retrieval-Augmented Generation) & Analisis Pola Ancaman CTI.
Mengambil fakta artikel riil dari riwayat_tren di SQLite untuk diinjeksikan
ke prompt LLM (grounded context), serta menghitung proyeksi 1 pola serangan
terdepan (1 kata) berdasarkan momentum eskalasi historis.
"""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import math
import pandas as pd
from src.utils.config_loader import ConfigLoader
import re
from collections import Counter

from src.utils.llm_adapter import GeminiLLMAdapter
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_DB_PATH = Path(__file__).resolve().parents[2] / "data" / "state.db"

_EMBEDDING_CACHE: Dict[str, List[float]] = {}
_MITRE_EMBEDDING_CACHE: Dict[str, List[float]] = {}


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Menghitung cosine similarity antara dua vector embedding."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = 0.0
    sum_a = 0.0
    sum_b = 0.0
    for a, b in zip(vec_a, vec_b):
        dot += a * b
        sum_a += a * a
        sum_b += b * b
    if sum_a <= 0.0 or sum_b <= 0.0:
        return 0.0
    return dot / (math.sqrt(sum_a) * math.sqrt(sum_b))


def extract_threat_entity_organic(judul: str, narasi: str = "", kata_kunci: str = "") -> str:
    """
    Mengekstrak nama spesifik malware, exploit, zero-day, backdoor, botnet, atau modus serangan
    secara langsung dan organik dari teks berita tanpa menggunakan klasifikasi kaku.
    Contoh output:
    - 'Backdoor TASK#STOMP'
    - 'NetScaler Zero-Day'
    - 'Ransomware LockBit'
    - 'Trojan RemControl'
    - 'Botnet CARBONATO'
    - 'Phishing APK'
    - 'Penipuan Online'
    - 'Pencurian Kripto'
    """
    judul_clean = re.sub(r'[\"\'\`“”‘’]', '', str(judul or "")).strip()
    narasi_clean = re.sub(r'[\"\'\`“”‘’]', '', str(narasi or "")).strip()
    teks = f"{judul_clean}. {narasi_clean}"

    STOP_TERMS = {
        'pada', 'pencuri', 'yang', 'dan', 'untuk', 'dengan', 'dari', 'tersebut', 'kini',
        'baru', 'aktif', 'menyerang', 'seperti', 'antara', 'uses', 'hides', 'gives',
        'steals', 'from', 'terintegrasi', 'berbahaya', 'dalam', 'bisa', 'akan', 'hacks',
        'sistem', 'server', 'komputer', 'perangkat', 'jaringan', 'terhadap', 'adalah',
        'sejumlah', 'banyak', 'beberapa', 'sebuah', 'suatu', 'the', 'a', 'an', 'of', 'in',
        'on', 'at', 'to', 'for', 'ini', 'itu', 'atas', 'oleh', 'di', 'ke', 'juga', 'tagar'
    }

    # 1. Pola Malware/Backdoor/Ransomware/Trojan/Infostealer/Botnet/Spyware + Nama Entitas Spesifik
    m_malware = re.search(
        r'\b(Backdoor|Malware|Ransomware|Trojan|Infostealer|Stealer|Botnet|Spyware)\s+([A-Z0-9#@_\-\.]{3,25}|[A-Z][a-z0-9]+(?:\s+[A-Z0-9][a-z0-9]+)?)\b',
        teks, re.IGNORECASE
    )
    if m_malware:
        tipe = m_malware.group(1).title()
        nama = m_malware.group(2).strip()
        if nama.lower() not in STOP_TERMS and len(nama) > 2:
            return f"{tipe} {nama}"

    # 2. Pola Zero-Day atau CVE Produk / Vendor spesifik
    m_zero = re.search(r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)\s+(?:Zero-Days?|0-Days?)\b', teks, re.IGNORECASE)
    if m_zero and m_zero.group(1).lower() not in STOP_TERMS:
        return f"{m_zero.group(1)} Zero-Day"

    m_cve = re.search(r'\b(CVE-\d{4}-\d{4,7})\b', teks, re.IGNORECASE)
    if m_cve:
        m_prod = re.search(r'\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)?)\s+(?:Zero-Days?|0-Days?|Celah|Kerentanan|CVE)', judul_clean, re.IGNORECASE)
        if m_prod and m_prod.group(1).lower() not in STOP_TERMS:
            return f"{m_prod.group(1)} ({m_cve.group(1).upper()})"
        return m_cve.group(1).upper()

    # 3. APT / Aktor Ancaman Terorganisir
    m_apt = re.search(r'\b(APT[0-9]+|[A-Z][a-z0-9]+\s+(?:Typhoon|Spider|Blizzard|Bear|Panda|Chollima|Kitten|Jackal)|Lazarus|ShinyHunters|RansomHub|LockBit)\b', teks, re.IGNORECASE)
    if m_apt:
        return f"Aktor {m_apt.group(1).title()}"

    # 4. Modus Serangan dengan Preposisi (misal: "Peretasan terhadap FBI" -> "Peretasan FBI")
    m_prep = re.search(r'\b(Peretasan|Pencurian|Kebocoran|Pembobolan)\s+(?:terhadap|pada|oleh|di|ke|dari|untuk|dan|yang)\s+([A-Z0-9][a-zA-Z0-9\.\#\-]+(?:\s+[A-Z0-9][a-zA-Z0-9\.\#\-]+)?)', teks, re.IGNORECASE)
    if m_prep:
        target = m_prep.group(2).strip()
        first_w = target.split()[0].lower()
        if first_w not in STOP_TERMS and len(target) > 2:
            return f"{m_prep.group(1).title()} {target.title()}"

    # 5. Pola Serangan / Modus Spesifik Lainnya
    m_modus = re.search(
        r'\b(Judi\s+Online|Pencurian\s+Kripto|Penipuan\s+Online|Situs\s+Palsu|Phishing\s+APK|Data\s+Breach\s+[A-Z][a-zA-Z0-9]+|Kartu\s+Kredit\s+Dibobol|Kebocoran\s+Data\s+[A-Z][a-zA-Z0-9]+|Peretasan\s+[A-Z][a-zA-Z0-9]+)\b',
        teks, re.IGNORECASE
    )
    if m_modus:
        val = m_modus.group(1).title()
        words = val.split()
        if len(words) > 1 and words[1].lower() not in STOP_TERMS:
            return val

    # 6. Fallback ke subjek utama judul yang bersih
    clean_j = re.sub(r'^[0-9\.\,\s]+', '', judul_clean)
    clean_j = re.sub(r'\s*-\s*[A-Za-z0-9\.\s]+$', '', clean_j)
    words = [w for w in clean_j.split() if w.lower() not in STOP_TERMS][:3]
    return " ".join(words).title() if words else "Insiden Siber"


class RAGEngine:
    """
    Engine RAG sederhana dan teroptimasi untuk mengambil korpus berita riil
    dan mengevaluasi proyeksi pola serangan berdasarkan data historis.
    """

    def __init__(self, df_riwayat: Optional[pd.DataFrame] = None):
        self.df_riwayat = df_riwayat if df_riwayat is not None else pd.DataFrame()
        self.df_berita = pd.DataFrame()

        if not self.df_riwayat.empty:
            if "kategori" in self.df_riwayat.columns:
                self.df_berita = self.df_riwayat[
                    (self.df_riwayat["kategori"] == "berita") & 
                    (self.df_riwayat["kategori_relevansi"] == "insiden_spesifik")
                ].copy()

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

    def retrieve_berita_semantic(self, query: str, limit: int = 5) -> List[tuple]:
        """
        Mengambil artikel berita paling relevan secara semantik menggunakan
        vector embeddings text-embedding-004 dan cosine similarity.
        Mengembalikan list of (score, sumber, judul, ringkasan, tanggal).
        """
        if self.df_berita.empty or not query:
            return []

        try:
            query_emb = GeminiLLMAdapter.embed_text(query)
            if not query_emb:
                return []

            results = []
            sample_df = self.df_berita.head(30)
            items_to_embed = []
            keys_to_embed = []
            for _, row in sample_df.iterrows():
                judul = str(row.get("judul", "")).strip()
                ringkasan = str(row.get("ringkasan_atau_narasi", "")).strip()
                tanggal = str(row.get("tanggal_publish", "")).split()[0]
                teks = f"{judul}. {ringkasan}".strip()
                cache_key = f"{judul}_{tanggal}"
                if cache_key not in _EMBEDDING_CACHE and teks:
                    items_to_embed.append(teks)
                    keys_to_embed.append(cache_key)

            if items_to_embed:
                batch_embs = GeminiLLMAdapter.embed_documents(items_to_embed, batch_size=50)
                for k, emb in zip(keys_to_embed, batch_embs):
                    if emb:
                        _EMBEDDING_CACHE[k] = emb

            for _, row in sample_df.iterrows():
                judul = str(row.get("judul", "")).strip()
                ringkasan = str(row.get("ringkasan_atau_narasi", "")).strip()
                sumber = str(row.get("sumber", "Media")).strip()
                tanggal = str(row.get("tanggal_publish", "")).split()[0]
                cache_key = f"{judul}_{tanggal}"
                doc_emb = _EMBEDDING_CACHE.get(cache_key)
                if doc_emb:
                    sim = _cosine_similarity(query_emb, doc_emb)
                    results.append((sim, sumber, judul, ringkasan, tanggal))

            results.sort(key=lambda x: x[0], reverse=True)
            return results[:limit]
        except Exception as e:
            logger.debug(f"Semantic embedding search bypassed: {e}")
            return []

    def map_incident_to_mitre_semantic(
        self,
        incident_title: str,
        incident_narrative: str = "",
        keywords: Optional[List[str]] = None,
        top_k: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Memetakan insiden siber ke taktik dan teknik MITRE ATT&CK secara semantik (Hybrid Multi-Stage RAG).
        Tahap 1: Mengambil taktik & teknik dari data/encyclopedia/mitre.json.
        Tahap 2: Menghitung vector similarity teks insiden terhadap teknik MITRE via text-embedding-004.
        Tahap 3: Fallback anggun ke RapidFuzz token matching jika embedding offline / kuota limit tercapai.
        Mengembalikan daftar taktik & teknik MITRE terverifikasi dengan skor keyakinan tertinggi.
        """
        from src.analytics.encyclopedia_lookup import load_encyclopedia
        from rapidfuzz import fuzz

        mitre_db = load_encyclopedia("mitre.json")
        if not mitre_db:
            return []

        query_text = f"{incident_title}. {incident_narrative}".strip()
        if keywords:
            query_text += f" Kata kunci: {', '.join(keywords)}"

        results = []

        # 1. Semantic Vector Retrieval menggunakan text-embedding-004 & Cosine Similarity
        try:
            query_emb = GeminiLLMAdapter.embed_text(query_text[:1000])
            if query_emb:
                missing_keys = []
                missing_texts = []
                for entry in mitre_db:
                    tid = entry.get("id", "")
                    if tid and tid not in _MITRE_EMBEDDING_CACHE:
                        doc_text = f"MITRE {tid} {entry.get('technique', '')} ({entry.get('tactic', '')}). {', '.join(entry.get('keywords', []))}"
                        missing_keys.append(tid)
                        missing_texts.append(doc_text)

                if missing_texts:
                    batch_embs = GeminiLLMAdapter.embed_documents(missing_texts, batch_size=30)
                    for k, emb in zip(missing_keys, batch_embs):
                        if emb:
                            _MITRE_EMBEDDING_CACHE[k] = emb

                for entry in mitre_db:
                    tid = entry.get("id", "")
                    doc_emb = _MITRE_EMBEDDING_CACHE.get(tid)
                    if doc_emb:
                        sim = _cosine_similarity(query_emb, doc_emb)
                        results.append({
                            "id": tid,
                            "tactic": entry.get("tactic", "Enterprise"),
                            "technique": entry.get("technique", ""),
                            "score": round(sim, 3),
                            "method": "semantic_vector"
                        })
        except Exception as e:
            logger.debug(f"MITRE vector embedding search bypassed: {e}")

        # 2. Fallback Deterministik RapidFuzz Lexical Scoring
        if not results or (results and max(r["score"] for r in results) < 0.40):
            fuzzy_results = []
            q_lower = query_text.lower()
            for entry in mitre_db:
                kw_str = " ".join(entry.get("keywords", [])).lower()
                target_text = f"{entry.get('technique', '').lower()} {entry.get('tactic', '').lower()} {kw_str}"
                score_ratio = fuzz.token_set_ratio(q_lower, target_text) / 100.0

                for kw in entry.get("keywords", []):
                    if kw.lower() in q_lower:
                        score_ratio = min(1.0, score_ratio + 0.15)
                        break

                fuzzy_results.append({
                    "id": entry.get("id", ""),
                    "tactic": entry.get("tactic", "Enterprise"),
                    "technique": entry.get("technique", ""),
                    "score": round(score_ratio, 3),
                    "method": "lexical_fuzzy"
                })
            results = fuzzy_results

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def retrieve_berita_context(
        self,
        top_keywords: List[str],
        top_vectors: Optional[List[str]] = None,
        limit: int = 7
    ) -> str:
        """
        Mengambil sampel artikel berita asli paling relevan berdasarkan kecocokan
        semantik (vector embeddings) dan frekuensi kata kunci tren (lexical).
        """
        if self.df_berita.empty:
            return "(Tidak ada korpus berita pada database)"

        # Bersihkan list kata kunci pencarian
        kw_set = [k.lower().strip() for k in top_keywords if k and len(k.strip()) > 2]
        vector_set = [v.lower().strip() for v in (top_vectors or []) if v]

        # 1. Coba Semantic Vector Retrieval lebih dulu
        query_gabung = " ".join(kw_set[:5] + vector_set[:3])
        if query_gabung:
            semantic_matches = self.retrieve_berita_semantic(query_gabung, limit=limit)
            if semantic_matches and semantic_matches[0][0] >= 0.65:
                judul_terpilih = set()
                chunks = []
                for sim, sumber, judul, ringkasan, tanggal in semantic_matches:
                    if judul in judul_terpilih:
                        continue
                    judul_terpilih.add(judul)
                    ringkas_teks = ringkasan[:220] + ("..." if len(ringkasan) > 220 else "") if ringkasan else judul
                    chunks.append(f"- [{sumber} | {tanggal}] \"{judul}\": {ringkas_teks}")
                    if len(chunks) >= limit:
                        break
                if chunks:
                    return "\n".join(chunks)

        # 2. Fallback Lexical Scoring jika embedding belum aktif / similarity rendah
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
        Menganalisis data historis untuk mengidentifikasi 1 pola insiden yang sedang naik
        dibandingkan minggu kemarin secara organik dari berita tanpa klasifikasi kaku.
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
        nama_pola = spiking.get("nama_pola", "Insiden Dominan").strip()
        growth = spiking.get("growth_persen", 0.0)
        jml = spiking.get("jumlah_artikel", 0)

        return {
            "pola": nama_pola,
            "pola_lengkap": nama_pola,
            "growth_persen": int(growth),
            "jumlah_terkini": jml,
            "tingkat_risiko": "TINGGI" if growth >= 20.0 else "SEDANG",
            "subteks": "vs minggu lalu"
        }

    def hitung_prediksi_ancaman_baru(self) -> str:
        """
        Mengembalikan nama spesifik ancaman/malware/kasus baru dari berita
        tanpa diklasifikasikan ke kategori kaku.
        """
        if self.df_berita.empty:
            return "Kondisi Stabil"

        ancaman = self.ambil_berita_ancaman_baru()
        if not ancaman.get("ada"):
            return "Kondisi Stabil"

        return ancaman.get("nama") or ancaman.get("jenis_serangan") or "Kondisi Stabil"

    def ambil_data_tren_makro_spiking(self) -> Dict[str, Any]:
        """
        Mengidentifikasi pola insiden mingguan yang melonjak paling cepat (growth spike tertinggi)
        dibandingkan minggu kemarin secara dinamis langsung dari berita tanpa patokan klasifikasi.
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

        # Ekstrak pola entitas serangan secara organik untuk seluruh artikel terkini & baseline
        entity_terkini = {}
        for _, r in df_terkini.iterrows():
            ent = extract_threat_entity_organic(r.get("judul", ""), r.get("ringkasan_atau_narasi", ""), r.get("kata_kunci", ""))
            entity_terkini.setdefault(ent, []).append(r)

        entity_baseline = Counter()
        for _, r in df_baseline.iterrows():
            ent = extract_threat_entity_organic(r.get("judul", ""), r.get("ringkasan_atau_narasi", ""), r.get("kata_kunci", ""))
            entity_baseline[ent] += 1

        kandidat = []
        for ent, arts in entity_terkini.items():
            cnt_cur = len(arts)
            cnt_base = entity_baseline.get(ent, 0)
            growth = _hitung_growth(cnt_cur, cnt_base)
            kandidat.append({
                "nama_pola": ent,
                "growth_persen": growth,
                "jumlah_artikel": cnt_cur,
                "artikel": arts
            })

        # Urutkan berdasarkan lonjakan growth tertinggi dan volume artikel
        kandidat.sort(key=lambda x: (x["growth_persen"] > 0, x["growth_persen"], x["jumlah_artikel"]), reverse=True)
        top_spiking = kandidat[0] if kandidat else None

        if not top_spiking:
            top_spiking = {
                "nama_pola": "Insiden Siber Terkini",
                "growth_persen": 0.0,
                "jumlah_artikel": len(df_terkini),
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
            "jumlah_artikel": top_spiking.get("jumlah_artikel", len(top_spiking.get("artikel", []))),
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
            mitre_mapping = self.map_incident_to_mitre_semantic(
                incident_title=cl["nama_kampanye"],
                incident_narrative=gabungan_narasi,
                keywords=list(kata_kunci_set),
                top_k=2
            )

            hasil_top3.append({
                "urutan": idx + 1,
                "nama_insiden": cl["nama_kampanye"],
                "jumlah_artikel": cl["jumlah_artikel"],
                "uraian_fakta": gabungan_narasi,
                "kata_kunci": list(kata_kunci_set),
                "mitigasi_ensiklopedia": mitigasi_list,
                "mitre_mapping": mitre_mapping,
                "artikel_list": cl["artikel_list"]
            })

        return hasil_top3

    def ambil_berita_ancaman_baru(self) -> Dict[str, Any]:
        """
        Mengidentifikasi sinyal ancaman baru (emerging threats, novel malware, zero-day)
        dari korpus berita terkini dan mengekstrak entitas spesifiknya langsung dari teks berita
        secara organik tanpa patokan klasifikasi kaku.
        """
        if self.df_berita.empty:
            return {
                "ada": False,
                "nama": "Menunggu Sinyal",
                "jenis_serangan": "Kondisi Stabil",
                "uraian": "(Tidak ada ancaman baru)",
                "sumber": "-"
            }

        from src.analytics.trend_analyzer import _split_periode, _dedup_ringan_lintas_hari
        df_dedup = _dedup_ringan_lintas_hari(self.df_berita)
        df_terkini, df_baseline = _split_periode(df_dedup)
        if df_terkini.empty:
            df_terkini = df_dedup

        # Cari artikel yang melaporkan kasus ancaman/malware baru di periode terkini
        kandidat = []
        for _, r in df_terkini.iterrows():
            judul = str(r.get("judul", ""))
            narasi = str(r.get("ringkasan_atau_narasi", ""))
            kw = str(r.get("kata_kunci", ""))
            teks = f"{judul} {narasi} {kw}".lower()

            entitas = extract_threat_entity_organic(judul, narasi, kw)
            
            # Bobot indikator kebaruan & jenis ancaman (malware/exploit/zero-day)
            is_novel = any(w in teks for w in [
                "baru", "novel", "emerging", "modus baru", "zero-day", "0-day",
                "warning", "peringatan", "lonjakan", "kritis", "cve-2026", "cve-"
            ])
            has_malware = any(w in teks for w in [
                "malware", "backdoor", "trojan", "ransomware", "stealer", "botnet", "exploit", "cve"
            ])

            has_specific_threat = any(entitas.startswith(prefix) for prefix in [
                "Backdoor", "Malware", "Trojan", "Ransomware", "Infostealer", "Botnet", "Zero-Day", "CVE-"
            ])
            skor = (2.5 if is_novel else 1.0) * (2.0 if has_malware else 1.0) * (3.0 if has_specific_threat else 1.0)
            kandidat.append((skor, entitas, r))

        if kandidat:
            kandidat.sort(key=lambda x: x[0], reverse=True)
            top_skor, top_entitas, top_row = kandidat[0]
            judul = str(top_row.get("judul", "-"))

            return {
                "ada": True,
                "nama": top_entitas,
                "jenis_serangan": top_entitas,
                "uraian": str(top_row.get("ringkasan_atau_narasi", "")),
                "sumber": str(top_row.get("sumber", "Media Intelijen")),
                "judul": judul
            }

        row_first = df_terkini.iloc[0]
        ent = extract_threat_entity_organic(row_first.get("judul", ""), row_first.get("ringkasan_atau_narasi", ""), row_first.get("kata_kunci", ""))
        return {
            "ada": True,
            "nama": ent,
            "jenis_serangan": ent,
            "uraian": str(row_first.get("ringkasan_atau_narasi", "")),
            "sumber": str(row_first.get("sumber", "Media Intelijen")),
            "judul": str(row_first.get("judul", "-"))
        }

