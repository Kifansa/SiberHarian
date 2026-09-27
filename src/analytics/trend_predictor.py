"""
Menarasikan statistik tren (hasil trend_analyzer.py) menjadi teks yang
mudah dibaca tim security, menggunakan Gemini API (GeminiLLMAdapter). BUKAN sumber
angka - LLM di sini murni menerjemahkan angka yang SUDAH dihitung Python
jadi bahasa manusia, supaya tidak ada ruang untuk mengarang insiden
atau CVE yang tidak nyata.
"""
import json
import re
from typing import Dict, List, Optional, Any, Tuple

from src.utils.llm_adapter import GeminiLLMAdapter
import pandas as pd
from src.utils.config_loader import ConfigLoader

from src.analytics.trend_analyzer import hitung_kasus_insiden_wilayah
from src.utils.llm_text_cleaner import bersihkan_output_llm
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


# Ambang batas minimal supaya LLM tidak dipaksa menganalisis data yang
# terlalu tipis untuk bermakna (mis. cuma 1 kata kunci muncul 1x).
MIN_JUMLAH_TERKINI = 2
MIN_GROWTH_PERSEN = 20.0






def _panggil_llm(system_prompt: str, user_prompt: str, model: str = None) -> Optional[str]:
    """Memanggil Gemini, mengembalikan None kalau gagal."""
    hasil = GeminiLLMAdapter.chat(system_prompt, user_prompt, temperature=0.1, max_tokens=2048)
    return hasil if hasil else None


def _filter_naik_signifikan(items: List[Dict]) -> List[Dict]:
    """
    Membuang entri yang growth-nya tidak signifikan atau jumlahnya
    terlalu sedikit untuk dipercaya sebagai tren nyata.
    """
    return [
        item for item in items
        if item["jumlah_terkini"] >= MIN_JUMLAH_TERKINI and item["growth_persen"] >= MIN_GROWTH_PERSEN
    ]


def _format_kata_kunci_untuk_prompt(daftar_kk: List[Dict]) -> str:
    baris = [
        f"- '{kk['kata_kunci']}': muncul {kk['jumlah_terkini']}x dalam 7 hari terakhir "
        f"(sebelumnya {kk['jumlah_baseline']}x dalam 7 hari baseline), growth {kk['growth_persen']}%"
        for kk in daftar_kk
    ]
    return "\n".join(baris)


def _format_vendor_untuk_prompt(daftar_vendor: List[Dict]) -> str:
    baris = []
    for v in daftar_vendor:
        produk_teks = (
            ", ".join(f"{p['produk']} ({p['jumlah']}x)" for p in v["top_produk"])
            if v["top_produk"] else "produk tidak teridentifikasi"
        )
        baris.append(
            f"- {v['vendor']}: {v['jumlah_terkini']} CVE CRITICAL dalam 7 hari terakhir "
            f"(sebelumnya {v['jumlah_baseline']} dalam 7 hari baseline), growth {v['growth_persen']}%. "
            f"Produk terdampak: {produk_teks}"
        )
    return "\n".join(baris)


def _format_sampel_judul_untuk_prompt(daftar_judul: List[Dict]) -> str:
    if not daftar_judul:
        return "(tidak ada sampel judul insiden spesifik pada periode ini)"
    return "\n".join(f"- \"{j['judul']}\" ({j['sumber']})" for j in daftar_judul)


def prediksi_tren_berita(
    statistik_tren: Dict,
    df_riwayat: Optional[pd.DataFrame] = None,
    model: str = None,
    mode: Optional[str] = None
) -> tuple:
    from src.analytics.rag_engine import RAGEngine
    rag_engine = RAGEngine(df_riwayat)

    # 1. Ambil data makro (insiden yang melonjak cepat)
    data_makro = rag_engine.ambil_data_tren_makro_spiking()

    # 2. Ambil top 3 insiden mikro (volume terbanyak dalam 7 hari terakhir)
    top3_mikro = rag_engine.ambil_top3_insiden_mikro()

    # 3. Ambil data ancaman baru (emerging threats)
    ancaman_baru = rag_engine.ambil_berita_ancaman_baru()

    # Baca mode generasi CTI dari config (modular_llm / instant_rag)
    mode_cti = mode
    if not mode_cti:
        try:
            import yaml
            with open("config/config.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                mode_cti = cfg.get("analytics", {}).get("cti_generation_mode", "modular_llm")
        except Exception:
            mode_cti = "modular_llm"

    from src.analytics.cti_agents import jalankan_pipeline_multi_agent
    narasi_berita, data_analyst = jalankan_pipeline_multi_agent(
        data_makro=data_makro,
        top3_mikro=top3_mikro,
        ancaman_baru=ancaman_baru,
        model=model,
        mode=mode_cti
    )

    if not narasi_berita:
        return "Analisis CTI belum dapat dihasilkan karena keterbatasan data insiden riil.", {}

    return bersihkan_output_llm(narasi_berita), data_analyst


def prediksi_tren_cve(
    statistik_cve: Dict,
    df_riwayat: Optional[pd.DataFrame] = None,
    model: str = None,
    mode: str = "modular_llm"
) -> str:
    """Menghasilkan narasi tren CVE modular 4-bagian menggunakan RAG fakta riil dan Gemini API."""
    from src.analytics.cti_agents import jalankan_pipeline_cve_modular
    narasi_cve = jalankan_pipeline_cve_modular(
        statistik_cve=statistik_cve,
        df_riwayat=df_riwayat,
        model=model,
        mode=mode
    )
    return bersihkan_output_llm(narasi_cve)


def _bersihkan_link(raw_link: str) -> str:
    """Ekstrak URL tunggal yang valid dari output model LLM."""
    if not raw_link or str(raw_link).strip() in ["#", "-", "None"]:
        return "#"
    urls = re.findall(r'https?://[^\s,"\'<>]+', str(raw_link))
    return urls[0] if urls else "#"


def _normalisasi_isu_utama(isu: str, kategori: str = "") -> str:
    """
    Menormalkan keyword isu_utama menjadi 1-2 kata taksonomi ancaman CTI standar.
    Mencegah penyebutan nama vendor, tools, atau nama malware spesifik.
    """
    isu = (isu or "").strip().strip('"\'')
    if not isu or isu == "-" or isu.lower() == "none":
        return "Kondisi Kondusif"

    isu_lower = isu.lower()
    if any(m in isu_lower for m in ["grayrabbit", "infostealer", "trojan", "spyware", "stealer", "agenttesla", "lumma", "malware"]):
        return "Malware & Trojan"
    if "ransom" in isu_lower:
        return "Ransomware"
    if any(b in isu_lower for b in ["bocor", "leak", "breach", "data"]):
        return "Kebocoran Data"
    if any(p in isu_lower for p in ["bajak", "takeover", "akun"]):
        return "Pembajakan Akun"
    if any(c in isu_lower for c in ["celah", "rce", "vulnerability", "exploit", "zero-day", "0-day"]):
        return "Eksploitasi Celah"
    if any(f in isu_lower for f in ["phish", "fraud", "penipuan", "social engineering"]):
        return "Phishing & Fraud"
    if any(w in isu_lower for w in ["deface", "web", "slot", "ddos"]):
        return "Serangan Web & Defacement"

    words = isu.split()
    return " ".join(words[:2])


def _normalisasi_poin_cti(val: Any) -> str:
    """Membersihkan dan menormalisasi output poin dari LLM agar selalu berupa string multiline yang bersih."""
    if not val or val == "-":
        return "-"
    if isinstance(val, list):
        items = []
        for item in val:
            s = str(item).strip()
            s = s.strip("[]'\"")
            if s:
                items.append(s if s.startswith("- ") else f"- {s}")
        return "\n".join(items) if items else "-"
    
    val_str = str(val).strip()
    if val_str.startswith("[") and val_str.endswith("]"):
        try:
            import ast
            parsed = ast.literal_eval(val_str)
            if isinstance(parsed, list):
                return _normalisasi_poin_cti(parsed)
        except Exception:
            pass
        val_str = val_str[1:-1].strip()
        parts = [p.strip().strip("'\"") for p in val_str.split("', '")]
        return "\n".join(f"- {p}" if not p.startswith("-") else p for p in parts if p)

    return val_str


def _parse_urgensi_dan_potensi(teks_llm: str, fallback_urg: str, fallback_pot: str) -> Tuple[str, str]:
    """Mengekstrak alasan urgensi dan potensi ancaman dari output teks LLM secara toleran."""
    if not teks_llm:
        return fallback_urg, fallback_pot

    urg = ""
    pot = ""

    parts = re.split(r'POTENSI ANCAMAN[:\s]*', teks_llm, flags=re.IGNORECASE)
    if len(parts) >= 2:
        part_urg = re.sub(r'^.*?ALASAN URGENSI[:\s]*', '', parts[0], flags=re.IGNORECASE | re.DOTALL).strip()
        part_pot = parts[1].strip()
        if "- " in part_urg:
            urg = part_urg
        if "- " in part_pot:
            pot = part_pot
    elif "- " in teks_llm:
        lines = [l.strip() for l in teks_llm.splitlines() if l.strip().startswith("- ")]
        if len(lines) >= 3:
            urg = "\n".join(lines[:2])
            pot = "\n".join(lines[2:4])
        elif len(lines) >= 1:
            urg = "\n".join(lines)
            pot = fallback_pot

    return urg or fallback_urg, pot or fallback_pot


def analisis_kasus_insiden_wilayah_ai(
    df_riwayat: Optional[pd.DataFrame] = None,
    kasus_wilayah_cluster: Optional[Dict] = None,
    model: str = None,
    mode: str = "modular_llm"
) -> Dict:
    """
    Menganalisis penilaian CTI makro (lanskap ancaman, urgensi, proyeksi) beserta studi kasus
    secara sekuensial dan terisolasi untuk 3 wilayah (Internasional, Nasional, Jawa Timur).
    Bebas crash JSON escape sequence dan 100% menjamin kartu tidak pernah bernilai kosong '-'.
    """
    fallback_kosong = {
        "internasional": {
            "ada_kejadian": False, "isu_utama": "Kondisi Kondusif", "nama_kejadian": "-", "ringkasan_kasus": "", "kategori": "-",
            "lokasi": "Global", "alasan_urgensi": "- **Nihil Insiden Kritis**: Nihil anomali berkategori tinggi dalam 7 hari terakhir.", "potensi_ancaman": "- **Kesiapsiagaan**: Fokus pada audit celah sistem dan mitigasi unpatched CVE.", "sumber": "-", "link": "#"
        },
        "nasional": {
            "ada_kejadian": False, "isu_utama": "Kondisi Kondusif", "nama_kejadian": "-", "ringkasan_kasus": "", "kategori": "-",
            "lokasi": "Indonesia", "alasan_urgensi": "- **Nihil Insiden Kritis**: Nihil anomali berkategori tinggi dalam 7 hari terakhir.", "potensi_ancaman": "- **Kesiapsiagaan**: Peningkatan kewaspadaan aparatur terhadap credential phishing.", "sumber": "-", "link": "#"
        },
        "jawa_timur": {
            "ada_kejadian": False, "isu_utama": "Kondisi Kondusif", "nama_kejadian": "-", "ringkasan_kasus": "", "kategori": "-",
            "lokasi": "Jawa Timur", "alasan_urgensi": "- **Nihil Anomali**: Nihil anomali insiden siber yang menargetkan portal OPD di Jawa Timur dalam 7 hari terakhir.", "potensi_ancaman": "- **Kesiapsiagaan Preventif**: Pengetatan autentikasi multifaktor dan literasi keamanan siber ASN.", "sumber": "-", "link": "#"
        }
    }

    if kasus_wilayah_cluster is None:
        if df_riwayat is not None and not df_riwayat.empty:
            kasus_wilayah_cluster = hitung_kasus_insiden_wilayah(df_riwayat, top_n_per_wilayah=10)
        else:
            return fallback_kosong

    from src.analytics.rag_engine import RAGEngine
    rag_engine = RAGEngine(df_riwayat)

    from src.analytics.cti_agents import _deteksi_sektor_spesifik, _deteksi_senjata_spesifik, _deteksi_dampak_spesifik, _call_llm_text
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher

    def _sintesis_wilayah(nama_wilayah: str, label_wilayah: str) -> dict:
        cluster_items = (kasus_wilayah_cluster or {}).get(nama_wilayah, [])
        if not cluster_items:
            return {
                "ada_kejadian": False,
                "isu_utama": "Kondisi Kondusif",
                "nama_kejadian": "-",
                "ringkasan_kasus": "",
                "kategori": "-",
                "lokasi": label_wilayah,
                "alasan_urgensi": f"- **Nihil Anomali**: Nihil anomali atau insiden siber berkategori tinggi yang menargetkan infrastruktur di {label_wilayah} dalam 7 hari terakhir.",
                "potensi_ancaman": "- **Prioritas Kesiapsiagaan**: Fokus mitigasi tetap pada hardening celah sistem (unpatched CVE) dan peningkatan kewaspadaan aparatur terhadap rekayasa sosial / credential phishing.",
                "sumber": "-",
                "link": "#",
            }

        # 1. Ekstraksi deterministik sampel kasus riil terbaik
        top_art = cluster_items[0]
        raw_nama = top_art.get("judul", "-")
        nama_kejadian, _ = _bersihkan_judul_dan_publisher(raw_nama, "")
        ringkasan_kasus = top_art.get("ringkasan", "") or top_art.get("ringkasan_atau_narasi", "")
        sumber = top_art.get("sumber", "Media Intelijen")
        link = _bersihkan_link(top_art.get("link", "#"))
        kategori_raw = top_art.get("tag", "Insiden Siber")
        isu_utama = _normalisasi_isu_utama(kategori_raw, "")

        # 2. Fallback deterministik berbasis korpus fakta RAG riil (tidak pernah kosong)
        sektor_f = _deteksi_sektor_spesifik(f"{nama_kejadian} {ringkasan_kasus}")
        senjata_f = _deteksi_senjata_spesifik(f"{nama_kejadian} {ringkasan_kasus}")
        dampak_f = _deteksi_dampak_spesifik(f"{nama_kejadian} {ringkasan_kasus}")

        fallback_urgensi = (
            f"- **Lanskap Ancaman Aktif**: Terdeteksi {len(cluster_items)} laporan insiden siber dalam 7 hari terakhir di ranah {label_wilayah} dengan fokus eskalasi pada **{isu_utama}**.\n"
            f"- **Paparan Sektor & Metode**: Penyerangan menargetkan **{sektor_f}** dengan memanfaatkan **{senjata_f}**, yang memicu kerugian berupa **{dampak_f}**."
        )
        fallback_potensi = (
            f"- **Proyeksi Eskalasi Risiko**: Potensi replikasi teknik serangan serupa terhadap sistem informasi dan basis data instansi di wilayah {label_wilayah}.\n"
            f"- **Kesiapsiagaan Tim CSIRT**: Direkomendasikan pengetatan pemantauan log anomali, penegakan autentikasi multifaktor (MFA), dan audit konfigurasi server berkala."
        )

        if mode == "instant_rag":
            return {
                "ada_kejadian": True,
                "isu_utama": isu_utama,
                "nama_kejadian": nama_kejadian,
                "ringkasan_kasus": ringkasan_kasus,
                "kategori": kategori_raw,
                "lokasi": label_wilayah,
                "alasan_urgensi": _normalisasi_poin_cti(fallback_urgensi),
                "potensi_ancaman": _normalisasi_poin_cti(fallback_potensi),
                "sumber": sumber,
                "link": link,
            }

        # 3. Mode Modular LLM (Panggilan terisolasi ringan ~250 token)
        rag_context = rag_engine.retrieve_regional_context(cluster_items, label_wilayah, limit=6)
        user_prompt = (
            f"KORPUS FAKTA BERITA WILAYAH: {label_wilayah}\n{rag_context[:900]}\n\n"
            f"Instruksi: Terapkan prinsip BLUF (Bottom Line Up Front) dengan langsung menyajikan dampak kritis di baris awal. "
            f"Sertakan potensi dampak domino (cascading effect) lintas sektor dan implikasinya terhadap infrastruktur digital.\n"
            f"Format keluaran harus persis 2 bagian berikut:\n"
            f"ALASAN URGENSI:\n"
            f"- **[Dampak Kritis]**: [Analisis urgensi utama dan sektor vital yang terpapar di {label_wilayah}]\n"
            f"- **[Vektor & Taktik]**: [Metode penyerangan atau celah yang dieksploitasi]\n\n"
            f"POTENSI ANCAMAN:\n"
            f"- **[Proyeksi Risiko]**: [Eskalasi ancaman dan potensi penyebaran ke domain instansi publik]\n"
            f"- **[Tindakan Pengamanan]**: [Langkah preventif atau mitigasi taktis yang wajib disiapkan]"
        )

        try:
            hasil_teks = _call_llm_text(
                "Kamu adalah Senior CTI Strategic Advisor CSIRT Dinas Komunikasi dan Informatika Jawa Timur. Sajikan intelijen ringkas, tajam, dan actionable berbasis fakta. DILARANG menggunakan JSON atau kata klise.",
                user_prompt,
                model=model,
                num_predict=350
            )
            urgensi, potensi = _parse_urgensi_dan_potensi(hasil_teks, fallback_urgensi, fallback_potensi)
        except Exception as err:
            logger.warning(f"Fallback CTI AI wilayah {label_wilayah}: {err}")
            urgensi, potensi = fallback_urgensi, fallback_potensi

        return {
            "ada_kejadian": True,
            "isu_utama": isu_utama,
            "nama_kejadian": nama_kejadian,
            "ringkasan_kasus": ringkasan_kasus,
            "kategori": kategori_raw,
            "lokasi": label_wilayah,
            "alasan_urgensi": _normalisasi_poin_cti(urgensi),
            "potensi_ancaman": _normalisasi_poin_cti(potensi),
            "sumber": sumber,
            "link": link,
        }

    logger.info("[Wilayah 1/3] Menganalisis CTI Internasional (Global)...")
    hasil_intl = _sintesis_wilayah("internasional", "Internasional (Global)")

    logger.info("[Wilayah 2/3] Menganalisis CTI Nasional (Indonesia)...")
    hasil_nas = _sintesis_wilayah("nasional", "Nasional (Indonesia)")

    logger.info("[Wilayah 3/3] Menganalisis CTI Jawa Timur...")
    hasil_jatim = _sintesis_wilayah("jawa_timur", "Jawa Timur")

    return {
        "internasional": hasil_intl,
        "nasional": hasil_nas,
        "jawa_timur": hasil_jatim,
    }


def proses_prediksi_tren(
    statistik_tren: Dict,
    df_riwayat: Optional[pd.DataFrame] = None,
    model: str = None
) -> Dict:
    """
    Titik masuk utama: Menjalankan pipeline CTI secara sekuensial dan terisolasi
    (Berita -> CVE -> Kasus Wilayah), sehingga LLM tidak memproses hal besar bersamaan.
    """
    mode_cti = "modular_llm"
    try:
        import yaml
        with open("config/config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
            mode_cti = cfg.get("analytics", {}).get("cti_generation_mode", "modular_llm")
    except Exception:
        mode_cti = "modular_llm"

    logger.info(f"=== MEMULAI PIPELINE CTI SEQUENTIAL ISOLATED ({mode_cti.upper()}) ===")

    logger.info("[TAHAP 1/3] Menyusun prediksi tren berita CTI secara modular...")
    narasi_berita, data_analyst = prediksi_tren_berita(statistik_tren, df_riwayat=df_riwayat, model=model, mode=mode_cti)

    logger.info("[TAHAP 2/3] Menyusun prediksi tren CVE secara modular...")
    narasi_cve = prediksi_tren_cve(statistik_tren.get("cve", {}), df_riwayat=df_riwayat, model=model, mode=mode_cti)

    logger.info("[TAHAP 3/3] Menganalisis penilaian CTI makro wilayah secara sekuensial (Intl -> Nas -> Jatim)...")
    kasus_ai = analisis_kasus_insiden_wilayah_ai(df_riwayat=df_riwayat, model=model, mode=mode_cti)

    return {
        "prediksi_berita": narasi_berita,
        "prediksi_cve": narasi_cve,
        "kasus_wilayah_ai": kasus_ai,
        "data_analyst": data_analyst,
    }


if __name__ == "__main__":
    # Testing manual: python -m src.analytics.trend_predictor
    from src.analytics.trend_analyzer import susun_ringkasan_statistik_tren
    from src.storage.db import ambil_riwayat_tren

    df = ambil_riwayat_tren(hari=14)
    statistik = susun_ringkasan_statistik_tren(df)
    hasil = proses_prediksi_tren(statistik)

    print("=== PREDIKSI TREN BERITA ===")
    print(hasil["prediksi_berita"])
    print("\n=== PREDIKSI TREN CVE ===")
    print(hasil["prediksi_cve"])

