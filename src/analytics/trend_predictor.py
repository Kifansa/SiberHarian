"""
Menarasikan statistik tren (hasil trend_analyzer.py) menjadi teks yang
mudah dibaca tim security, menggunakan Gemini API (GeminiLLMAdapter). BUKAN sumber
angka - LLM di sini murni menerjemahkan angka yang SUDAH dihitung Python
jadi bahasa manusia, supaya tidak ada ruang untuk mengarang insiden
atau ancaman yang tidak nyata.
"""
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
        return "Kondusif"

    isu_lower = isu.lower()
    if any(m in isu_lower for m in ["grayrabbit", "infostealer", "trojan", "spyware", "stealer", "agenttesla", "lumma", "malware"]):
        return "Malware & Trojan"
    if "ransom" in isu_lower:
        return "Ransomware"
    if any(b in isu_lower for b in ["bocor", "leak", "breach", "data"]):
        return "Kebocoran Data"
    if any(p in isu_lower for p in ["bajak", "takeover", "akun"]):
        return "Pembajakan Akun"
    if re.search(r'\b(?:celah|rce|vulnerability|exploit|zero-day|0-day)\b', isu_lower):
        return "Eksploitasi Celah"
    if any(f in isu_lower for f in ["phish", "quish", "fraud", "penipuan", "social engineering"]):
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
            s = str(item).strip().strip("[]'\"")
            if s:
                items.append(s if s.startswith("- ") else f"- {s}")
        return "\n".join(items) if items else "-"

    val_str = str(val).strip()
    if val_str.startswith("[") and val_str.endswith("]"):
        val_str = val_str[1:-1].strip()
        parts = [p.strip().strip("'\"") for p in val_str.split(",") if p.strip().strip("'\"")]
        return "\n".join(f"- {p}" if not p.startswith("-") else p for p in parts)

    return val_str


def _susun_mitigasi_spesifik_kasus(senjata: str, sektor: str, kategori: str) -> str:
    """
    Menyusun langkah mitigasi teknis yang spesifik dan selaras dengan vektor serangan
    serta sektor korban pada Kasus Teratas (#1), tanpa memaksakan terminologi pemerintah
    (OPD/Pemprov Jatim/ASN) apabila korban bukan instansi pemerintahan.
    """
    gabung = f"{senjata} {kategori}".lower()
    konteks_entitas = (
        "infrastruktur instansi layanan publik terkait"
        if "pemerintah" in (sektor or "").lower()
        else f"sistem operasional pada {sektor.lower()}" if sektor and sektor != "Entitas Sistem Terdampak"
        else "sistem dan infrastruktur organisasi terdampak"
    )

    if "ransomware" in gabung or "encrypt" in gabung:
        return (
            f"Isolasi segera host/segmen jaringan pada {konteks_entitas}, verifikasi ketersediaan "
            f"cadangan data terisolasi (immutable/offline backup), rotasi kredensial akses berprivilese, "
            f"serta lakukan pemindaian endpoint menyeluruh untuk memutus rantai enkripsi."
        )
    if any(k in gabung for k in ["phishing", "quishing", "social engineering", "apk", "fraud"]):
        return (
            f"Blokir domain/tautan tiruan pada DNS dan gateway komunikasi, terapkan verifikasi integritas "
            f"kanal transaksi/kode pembayaran digital serta tanda tangan aplikasi pada {konteks_entitas}, "
            f"dan perketat autentikasi multifaktor (MFA) tahan phishing."
        )
    if any(k in gabung for k in ["deface", "webshell", "judi", "slot", "serangan web"]):
        return (
            f"Audit integritas direktori web pada {konteks_entitas}, bersihkan skrip backdoor/webshell "
            f"yang disusupkan, tutup celah unggah berkas (file upload validation), dan terapkan aturan "
            f"penyaringan ketat pada Web Application Firewall (WAF)."
        )
    if re.search(r'\b(?:celah|rce|exploit|eksploitasi|zero-day|0-day|vulnerability)\b', gabung):
        return (
            f"Terapkan pembaruan keamanan (security patch/virtual patching) pada komponen sistem yang rentan "
            f"di {konteks_entitas}, batasi eksposur antarmuka manajemen dari jaringan publik, dan pantau "
            f"anomali eksekusi perintah pada server."
        )
    if re.search(r'\b(?:ddos|dos)\b', gabung):
        return (
            f"Aktifkan mitigasi penyaringan trafik (traffic scrubbing) dan pembatasan laju permintaan "
            f"(rate-limiting) pada perimeter jaringan/CDN {konteks_entitas}, serta siagakan kapasitas "
            f"redundansi layanan untuk menjaga ketersediaan sistem."
        )
    return (
        f"Cabut sesi aktif dan rotasi paksa kredensial/kunci API yang berpotensi terpapar pada {konteks_entitas}, "
        f"perketat kontrol akses berbasis hak minimum (least privilege), serta lakukan audit log akses basis data "
        f"untuk menghentikan eksfiltrasi lanjutan."
    )


def _parse_urgensi_dan_potensi(teks_llm: str, fallback_urg: str, fallback_pot: str) -> Tuple[str, str]:
    """Mengekstrak alasan urgensi (Fakta & Kronologi) dan potensi ancaman (Dampak & Mitigasi) dari output teks LLM."""
    if not teks_llm or "**None**" in teks_llm:
        return fallback_urg, fallback_pot

    urg = ""
    pot = ""

    parts = re.split(r'(?:\[\s*DAMPAK\s*&\s*MITIGASI\s*SPESIFIK\s*KASUS\s*\]|POTENSI ANCAMAN)[:\s]*', teks_llm, flags=re.IGNORECASE)
    if len(parts) >= 2:
        part_urg = re.sub(
            r'^.*?(?:\[\s*FAKTA\s*&\s*KRONOLOGI\s*KASUS\s*TERAMAI\s*\]|ALASAN URGENSI)[:\s]*',
            '',
            parts[0],
            flags=re.IGNORECASE | re.DOTALL
        ).strip()
        part_pot = re.split(
            r'\[\s*DAFTAR\s*INSIDEN\s*TERAMAI\s*LAINNYA',
            parts[1],
            flags=re.IGNORECASE
        )[0].strip()
        if "- " in part_urg:
            urg = part_urg
        if "- " in part_pot:
            pot = part_pot
    elif "- " in teks_llm:
        lines = [baris.strip() for baris in teks_llm.splitlines() if baris.strip().startswith("- ")]
        if len(lines) >= 3:
            urg = "\n".join(lines[:2])
            pot = "\n".join(lines[2:4])
        elif len(lines) >= 1:
            urg = "\n".join(lines)
            pot = fallback_pot

    return urg or fallback_urg, pot or fallback_pot


def analisis_kasus_insiden_wilayah_ai(
    df_riwayat_or_stat: Any = None,
    kasus_wilayah_cluster: Optional[Dict] = None,
    model: str = None,
    mode: str = "modular_llm",
    df_riwayat: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Menganalisis Kasus Insiden Siber Teramai secara sekuensial dan terisolasi untuk 3 wilayah
    (Internasional, Nasional, Jawa Timur).
    Menjamin narasi utama 100% sinkron dengan Kasus Teratas (#1) beserta tautan rujukannya,
    disertai 3 bagian terstruktur:
    - [ FAKTA & KRONOLOGI KASUS TERAMAI ]
    - [ DAMPAK & MITIGASI SPESIFIK KASUS ]
    - [ DAFTAR INSIDEN TERAMAI LAINNYA DI WILAYAH INI ]
    """
    if isinstance(df_riwayat_or_stat, dict):
        if kasus_wilayah_cluster is None:
            kasus_wilayah_cluster = df_riwayat_or_stat.get("kasus_wilayah", df_riwayat_or_stat)
    elif isinstance(df_riwayat_or_stat, pd.DataFrame) and df_riwayat is None:
        df_riwayat = df_riwayat_or_stat

    def _buat_state_kosong(label_wilayah: str) -> dict:
        fakta_kosong = (
            f"- **Status Pemantauan Wilayah**: Nihil laporan insiden serangan siber aktif yang terkonfirmasi "
            f"di wilayah {label_wilayah} dalam periode 7 hari terakhir."
        )
        dampak_kosong = (
            f"- **Dampak Operasional**: Tidak ditemukan gangguan layanan maupun kompromi data dari insiden aktif pada periode ini.\n"
            f"- **Rekomendasi Mitigasi Preventif**: Pertahankan pemantauan log keamanan, pembaruan patch berkala, dan pengetatan autentikasi multifaktor (MFA)."
        )
        lainnya_kosong = "- Tidak ada insiden teramai lainnya yang tercatat di wilayah ini pada periode 7 hari terakhir."
        narasi_kosong = (
            f"[ FAKTA & KRONOLOGI KASUS TERAMAI ]\n{fakta_kosong}\n\n"
            f"[ DAMPAK & MITIGASI SPESIFIK KASUS ]\n{dampak_kosong}\n\n"
            f"[ DAFTAR INSIDEN TERAMAI LAINNYA DI WILAYAH INI ]\n{lainnya_kosong}"
        )
        return {
            "ada_kejadian": False,
            "ada_insiden": False,
            "isu_utama": "Kondusif",
            "nama_kejadian": "-",
            "jumlah_liputan": 0,
            "ringkasan_kasus": "",
            "kategori": "-",
            "lokasi": label_wilayah,
            "fakta_kronologi": fakta_kosong,
            "dampak_mitigasi": dampak_kosong,
            "daftar_insiden_lainnya": [],
            "teks_insiden_lainnya": lainnya_kosong,
            "narasi_wilayah": narasi_kosong,
            "alasan_urgensi": fakta_kosong,
            "potensi_ancaman": dampak_kosong,
            "sumber": "-",
            "link": "#",
        }

    fallback_kosong = {
        "internasional": _buat_state_kosong("Global"),
        "nasional": _buat_state_kosong("Indonesia"),
        "jawa_timur": _buat_state_kosong("Jawa Timur"),
    }

    if kasus_wilayah_cluster is None:
        if df_riwayat is not None and not df_riwayat.empty:
            kasus_wilayah_cluster = hitung_kasus_insiden_wilayah(df_riwayat, top_n_per_wilayah=20)
        else:
            return fallback_kosong

    from src.analytics.rag_engine import RAGEngine
    rag_engine = RAGEngine(df_riwayat)

    from src.analytics.cti_agents import _deteksi_sektor_spesifik, _deteksi_senjata_spesifik, _deteksi_dampak_spesifik, _call_llm_text
    from src.analytics.trend_analyzer import _bersihkan_judul_dan_publisher

    def _sintesis_wilayah(nama_wilayah: str, label_wilayah: str) -> dict:
        cluster_items = (kasus_wilayah_cluster or {}).get(nama_wilayah, [])
        if not cluster_items:
            return _buat_state_kosong(label_wilayah)

        # 1. Sinkronisasi 100% dengan Kasus Teratas (#1)
        top_art = cluster_items[0]
        raw_nama = top_art.get("judul", "-")
        nama_kejadian, pub_extracted = _bersihkan_judul_dan_publisher(raw_nama, str(top_art.get("sumber", "")))
        ringkasan_kasus = str(top_art.get("ringkasan_atau_narasi", "") or top_art.get("ringkasan", "")).strip()
        sumber = top_art.get("sumber") or pub_extracted or "Media Intelijen"
        link = _bersihkan_link(top_art.get("link", "#"))
        kategori_raw = top_art.get("tag", "Insiden Siber")
        isu_utama = _normalisasi_isu_utama(kategori_raw, "")
        jumlah_liputan = int(top_art.get("jumlah_liputan", 1) or 1)

        # 2. Ekstraksi fakta spesifik murni dari Kasus Teratas (#1) (tanpa mencampur kasus lain)
        teks_top = f"{nama_kejadian} {ringkasan_kasus}".strip()
        fakta_top = rag_engine.extract_structured_rag_facts([top_art], kategori_raw) or {}

        sektor_det = _deteksi_sektor_spesifik(teks_top)
        senjata_det = _deteksi_senjata_spesifik(teks_top)
        dampak_det = _deteksi_dampak_spesifik(teks_top)

        aktor_kasus = (
            fakta_top.get("aktor")
            if fakta_top.get("aktor") and "None" not in str(fakta_top.get("aktor"))
            else "Pelaku peretasan masih dalam penyelidikan / belum dirinci spesifik pada laporan"
        )
        pihak_terdampak = (
            sektor_det
            or (fakta_top.get("pihak_terdampak") if fakta_top.get("pihak_terdampak") and "None" not in str(fakta_top.get("pihak_terdampak")) else None)
            or "Entitas Sistem Terdampak"
        )
        lokasi_kasus = (
            fakta_top.get("lokasi_kejadian")
            if fakta_top.get("lokasi_kejadian") and fakta_top.get("lokasi_kejadian") not in ["Ekosistem Digital Global", "None"]
            else label_wilayah
        )
        senjata_kasus = (
            senjata_det
            or (fakta_top.get("senjata_metode") if fakta_top.get("senjata_metode") and "None" not in str(fakta_top.get("senjata_metode")) else None)
            or kategori_raw
            or "Eksploitasi Sistem Siber"
        )
        dampak_kasus = (
            dampak_det
            or (fakta_top.get("dampak") if fakta_top.get("dampak") and "None" not in str(fakta_top.get("dampak")) else None)
            or "Gangguan integritas layanan dan risiko kompromi data"
        )
        kronologi_kasus = (
            ringkasan_kasus[:280].strip()
            if ringkasan_kasus
            else (fakta_top.get("alur_serangan") or f"Insiden {kategori_raw.lower()} dilaporkan pada {nama_kejadian}.")
        )
        mitigasi_spesifik = _susun_mitigasi_spesifik_kasus(senjata_kasus, pihak_terdampak, kategori_raw)

        # 3. Susun bagian [ FAKTA & KRONOLOGI KASUS TERAMAI ] & [ DAMPAK & MITIGASI SPESIFIK KASUS ]
        fallback_fakta_kronologi = (
            f"- **Kasus Teramai (#1) & Liputan**: **{nama_kejadian}** tercatat sebagai insiden paling disorot di wilayah {label_wilayah} "
            f"(intensitas **{jumlah_liputan} liputan** media, sumber utama: *{sumber}*).\n"
            f"- **Kronologi & Metode Serangan**: Aksi dilancarkan oleh **{aktor_kasus}** yang menyasar **{pihak_terdampak}** "
            f"di **{lokasi_kasus}** menggunakan metode **{senjata_kasus}**. Kronologi kejadian: {kronologi_kasus}"
        )

        fallback_dampak_mitigasi = (
            f"- **Dampak Spesifik Kasus**: Insiden pada **{nama_kejadian}** mengakibatkan **{dampak_kasus}** pada pihak terdampak (**{pihak_terdampak}**).\n"
            f"- **Mitigasi Teknis Spesifik**: {mitigasi_spesifik}"
        )

        # 4. Susun bagian [ DAFTAR INSIDEN TERAMAI LAINNYA DI WILAYAH INI ]
        # Menampilkan artikel yang spesifik selaras dengan hasil klasifikasi tren wilayah ini (misal tren Malware -> list berita malware yang sedang tren)
        def _cocok_kategori_tren(it: dict, hanya_judul: bool = False) -> bool:
            t = str(it.get("tag", "")).strip().lower()
            k = kategori_raw.lower()
            iu = isu_utama.lower()
            if not hanya_judul and t and (t == k or t in iu or k in t):
                return True
            txt = it.get('judul', '').lower() if hanya_judul else f"{it.get('judul', '')} {it.get('ringkasan_atau_narasi', '')} {it.get('kata_kunci', '')}".lower()
            if any(m in iu or m in k for m in ["malware", "trojan", "infostealer"]):
                return bool(re.search(r'\b(malware|trojan|infostealer|stealer|spyware|backdoor|keylogger)\b', txt))
            if any(r in iu or r in k for r in ["ransom", "tebusan"]):
                return bool(re.search(r'\b(ransomware|pemerasan|tebusan)\b', txt))
            if any(b in iu or b in k for b in ["bocor", "leak", "breach", "data"]):
                return bool(re.search(r'\b(bocor|leak|breach|data pribadi|dark web)\b', txt))
            if any(p in iu or p in k for p in ["peretasan", "deface", "web"]):
                return bool(re.search(r'\b(deface|peretasan|diretas|hacker|hacked|web shell)\b', txt))
            if any(c in iu or c in k for c in ["celah", "exploit", "eksploitasi"]):
                return bool(re.search(r'\b(celah|vulnerability|exploit|zero-day|0-day|rce)\b', txt))
            if any(f in iu or f in k for f in ["phish", "penipuan", "fraud"]):
                return bool(re.search(r'\b(phishing|quishing|scam|penipuan)\b', txt))
            return False

        klaster_tag_sama = [c for c in cluster_items[1:] if str(c.get("tag", "")).strip().lower() == kategori_raw.lower()]
        klaster_judul_cocok = [c for c in cluster_items[1:] if c not in klaster_tag_sama and _cocok_kategori_tren(c, hanya_judul=True)]
        klaster_konten_cocok = [c for c in cluster_items[1:] if c not in klaster_tag_sama and c not in klaster_judul_cocok and _cocok_kategori_tren(c)]
        klaster_relevan_tren = klaster_tag_sama + klaster_judul_cocok + klaster_konten_cocok
        klaster_tampil = klaster_relevan_tren[:5] if klaster_relevan_tren else cluster_items[1:6]

        daftar_insiden_lainnya = []
        baris_lainnya = []
        for idx, item in enumerate(klaster_tampil, start=2):
            j_lain, s_ext = _bersihkan_judul_dan_publisher(item.get("judul", "-"), str(item.get("sumber", "")))
            s_lain = item.get("sumber") or s_ext or "Media"
            l_lain = _bersihkan_link(item.get("link", "#"))
            c_lain = int(item.get("jumlah_liputan", 1) or 1)
            t_lain = item.get("tag", "Insiden Siber")
            daftar_insiden_lainnya.append({
                "peringkat": idx,
                "judul": j_lain,
                "jumlah_liputan": c_lain,
                "sumber": s_lain,
                "link": l_lain,
                "kategori": t_lain,
            })
            baris_lainnya.append(
                f"- **#{idx} {j_lain}** ({c_lain} liputan — *{s_lain}*, Kategori: {t_lain})"
            )

        if baris_lainnya:
            teks_insiden_lainnya = "\n".join(baris_lainnya)
        else:
            teks_insiden_lainnya = "- Tidak ada insiden teramai lainnya yang tercatat di wilayah ini pada periode 7 hari terakhir."

        fakta_final = _normalisasi_poin_cti(fallback_fakta_kronologi)
        dampak_final = _normalisasi_poin_cti(fallback_dampak_mitigasi)

        # 5. Mode Modular LLM (tetap terkunci pada Kasus Teratas #1, membaca prompt dari database/SettingsManager)
        if mode != "instant_rag":
            user_prompt = (
                f"KASUS INSIDEN SIBER TERAMAI (#1) DI WILAYAH {label_wilayah.upper()}:\n"
                f"- Judul Kasus: {nama_kejadian}\n"
                f"- Jumlah Liputan: {jumlah_liputan} liputan (Sumber: {sumber})\n"
                f"- Kategori & Metode: {kategori_raw} / {senjata_kasus}\n"
                f"- Aktor Terdeteksi: {aktor_kasus}\n"
                f"- Pihak / Sektor Terdampak: {pihak_terdampak}\n"
                f"- Lokasi Kejadian: {lokasi_kasus}\n"
                f"- Kronologi Berita: {kronologi_kasus}\n"
                f"- Dampak Dilaporkan: {dampak_kasus}\n\n"
                f"Data Konteks Tambahan:\n"
                f"- Nama Kasus: {nama_kejadian}\n"
                f"- Senjata/Metode Serangan: {senjata_kasus}\n"
                f"- Korban/Sektor Terdampak: {pihak_terdampak}\n"
                f"- Lokasi: {lokasi_kasus}\n"
            )

            try:
                from src.utils.settings_manager import SettingsManager
                system_prompt = SettingsManager.get_prompt("kasus_insiden_wilayah")
                if not system_prompt or not system_prompt.strip():
                    system_prompt = (
                        "Kamu adalah Analis Intelijen Ancaman Siber (CTI).\n"
                        "Tugasmu adalah menyusun analisis kasus insiden siber teramai (#1) per wilayah yang objektif, akurat, dan 100% berbasis fakta berita tanpa mengarang entitas di luar korpus.\n\n"
                        "PEDOMAN WAJIB:\n"
                        "1. FOKUS KASUS TERATAS: Analisis HANYA Kasus Teratas (#1) yang diberikan agar 100% sinkron dengan judul dan tautan rujukan berita sumber.\n"
                        "2. NETRALITAS INSTANSI: DILARANG mengaitkan atau memaksakan penyebutan Pemprov Jatim, OPD, atau ASN apabila korban pada kasus tersebut bukan instansi pemerintah.\n"
                        "3. STRUKTUR DAN FORMAT KELUARAN: Format keluaran harus persis 2 bagian berikut:\n\n"
                        "[ FAKTA & KRONOLOGI KASUS TERAMAI ]\n"
                        "- **Kasus Teramai (#1) & Liputan**: [Sebutkan nama kasus, intensitas liputan media, siapa pelaku/aktornya, siapa korban/entitas terdampak, dan lokasi kejadian]\n"
                        "- **Kronologi & Metode Serangan**: [Jelaskan bagaimana alur dan metode serangan berlangsung berdasarkan fakta berita]\n\n"
                        "[ DAMPAK & MITIGASI SPESIFIK KASUS ]\n"
                        "- **Dampak Spesifik Kasus**: [Jelaskan dampak nyata yang dialami korban pada kasus ini]\n"
                        "- **Mitigasi Teknis Spesifik**: [Rekomendasi mitigasi teknis yang spesifik terhadap metode serangan dan sektor korban kasus ini]"
                    )

                if "{" in system_prompt and "}" in system_prompt:
                    try:
                        system_prompt = system_prompt.format(
                            nama_kejadian=nama_kejadian,
                            label_wilayah=label_wilayah,
                            jumlah_liputan=jumlah_liputan,
                            sumber=sumber,
                            kategori_raw=kategori_raw,
                            senjata_kasus=senjata_kasus,
                            aktor_kasus=aktor_kasus,
                            pihak_terdampak=pihak_terdampak,
                            lokasi_kasus=lokasi_kasus,
                            kronologi_kasus=kronologi_kasus,
                            dampak_kasus=dampak_kasus,
                        )
                    except Exception:
                        pass

                cfg_llm = ((ConfigLoader.get_config() or {}).get("cti_analysis") or {}).get("llm") or {}
                num_pred_wil = (cfg_llm.get("num_predict") or {}).get("section_wilayah", 550)
                hasil_teks = _call_llm_text(
                    system_prompt,
                    user_prompt,
                    model=model,
                    num_predict=num_pred_wil
                )
                urg_parsed, pot_parsed = _parse_urgensi_dan_potensi(hasil_teks, fakta_final, dampak_final)
                fakta_final = _normalisasi_poin_cti(urg_parsed)
                dampak_final = _normalisasi_poin_cti(pot_parsed)
            except Exception as err:
                logger.warning(f"Fallback CTI AI wilayah {label_wilayah}: {err}")

        narasi_wilayah = (
            f"[ FAKTA & KRONOLOGI KASUS TERAMAI ]\n{fakta_final}\n\n"
            f"[ DAMPAK & MITIGASI SPESIFIK KASUS ]\n{dampak_final}\n\n"
            f"[ DAFTAR INSIDEN TERAMAI LAINNYA DI WILAYAH INI ]\n{teks_insiden_lainnya}"
        )

        return {
            "ada_kejadian": True,
            "ada_insiden": True,
            "isu_utama": isu_utama,
            "nama_kejadian": nama_kejadian,
            "jumlah_liputan": jumlah_liputan,
            "ringkasan_kasus": ringkasan_kasus,
            "kategori": kategori_raw,
            "lokasi": label_wilayah,
            "fakta_kronologi": fakta_final,
            "dampak_mitigasi": dampak_final,
            "daftar_insiden_lainnya": daftar_insiden_lainnya,
            "teks_insiden_lainnya": teks_insiden_lainnya,
            "narasi_wilayah": narasi_wilayah,
            "alasan_urgensi": fakta_final,
            "potensi_ancaman": dampak_final,
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
    model: str = None,
    mode: Optional[str] = None,
) -> Dict:
    """
    Titik masuk utama: Menjalankan pipeline CTI secara sekuensial dan terisolasi
    (Berita -> Kasus Wilayah), sehingga LLM tidak memproses hal besar bersamaan.
    """
    mode_cti = mode
    if not mode_cti:
        try:
            import yaml
            with open("config/config.yaml", "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
                mode_cti = cfg.get("analytics", {}).get("cti_generation_mode", "modular_llm")
        except Exception:
            mode_cti = "modular_llm"

    logger.info(f"=== MEMULAI PIPELINE CTI SEQUENTIAL ISOLATED ({mode_cti.upper()}) ===")

    logger.info("[TAHAP 1/2] Menyusun prediksi tren berita CTI secara modular...")
    narasi_berita, data_analyst = prediksi_tren_berita(statistik_tren, df_riwayat=df_riwayat, model=model, mode=mode_cti)

    logger.info("[TAHAP 2/2] Menganalisis penilaian CTI makro wilayah secara sekuensial (Intl -> Nas -> Jatim)...")
    kasus_ai = analisis_kasus_insiden_wilayah_ai(df_riwayat=df_riwayat, model=model, mode=mode_cti)

    return {
        "prediksi_berita": narasi_berita,
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