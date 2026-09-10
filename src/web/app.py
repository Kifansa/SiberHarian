"""
Web demo interface untuk pipeline cyber news digest. Endpoint untuk
memicu pipeline lengkap (scraping -> summarization -> arsip & tren)
dengan progress log real-time (SSE), dan endpoint terpisah untuk 3 tab
dashboard (Beranda, Arsip, Tren Siber) yang membaca langsung dari
database - source kebenaran tunggal, jadi data tetap ada untuk demo
walau server di-restart tanpa perlu scraping ulang.
"""
import asyncio
import json
import logging
import queue
import threading
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.analytics.pasca_proses import proses_arsip_dan_tren
from src.analytics.trend_analyzer import susun_ringkasan_statistik_tren
from src.pipeline_harian import jalankan_pipeline_harian
from src.storage.db import (
    ambil_prediksi_tren_terakhir,
    ambil_riwayat_dikelompokkan_per_hari,
    ambil_riwayat_tren,
)
from src.storage.db import (
    ambil_data_terbaru_per_kategori,
    ambil_prediksi_tren_terakhir,
    ambil_riwayat_dikelompokkan_per_hari,
)
from src.summarizer.llm_summarizer import proses_summarization_harian

BASE_DIR = Path(__file__).parent

app = FastAPI(title="Cyber News Digest - Demo")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

log_queue: "queue.Queue[dict]" = queue.Queue()
sedang_berjalan = False


class QueueLogHandler(logging.Handler):
    """Tiap log record didorong ke queue supaya bisa di-stream real-time ke frontend."""

    def emit(self, record: logging.LogRecord) -> None:
        log_queue.put({"type": "log", "level": record.levelname, "message": self.format(record)})


def _pasang_handler_global() -> None:
    handler = QueueLogHandler()
    handler.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s", datefmt="%H:%M:%S"))
    root_logger = logging.getLogger()
    if not any(isinstance(h, QueueLogHandler) for h in root_logger.handlers):
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


_pasang_handler_global()


def _jalankan_pipeline_di_thread() -> None:
    """
    Menjalankan pipeline lengkap secara sinkron di thread terpisah. Hasil
    akhir langsung tersimpan ke database lewat proses_arsip_dan_tren() -
    tidak ada lagi cache JSON manual, database adalah sumber kebenarannya.
    """
    global sedang_berjalan
    try:
        log_queue.put({"type": "log", "level": "INFO", "message": "Memulai pipeline harian..."})
        hasil_mentah = jalankan_pipeline_harian()
        hasil_ringkas = proses_summarization_harian(hasil_mentah)
        proses_arsip_dan_tren(hasil_ringkas)
        log_queue.put({"type": "selesai", "sukses": True})
    except Exception as e:
        log_queue.put({"type": "log", "level": "ERROR", "message": f"Pipeline gagal: {e}"})
        log_queue.put({"type": "selesai", "sukses": False, "error": str(e)})
    finally:
        sedang_berjalan = False


@app.post("/api/run")
async def mulai_pipeline():
    """Memicu pipeline di background thread. Progres dipantau lewat /api/stream."""
    global sedang_berjalan
    if sedang_berjalan:
        return {"status": "sudah_berjalan"}
    sedang_berjalan = True
    while not log_queue.empty():
        log_queue.get()
    threading.Thread(target=_jalankan_pipeline_di_thread, daemon=True).start()
    return {"status": "dimulai"}


@app.get("/api/stream")
async def stream_log():
    """SSE - mengalirkan log real-time selama pipeline berjalan."""
    async def generator():
        while True:
            try:
                item = await asyncio.get_event_loop().run_in_executor(None, log_queue.get, True, 1.0)
                yield f"data: {json.dumps(item)}\n\n"
                if item.get("type") == "selesai":
                    break
            except queue.Empty:
                yield ": keep-alive\n\n"
    return StreamingResponse(generator(), media_type="text/event-stream")


@app.post("/api/cancel")
async def batalkan_pipeline():
    """Menandai pipeline sebagai tidak berjalan lagi dari sisi status server (lihat
    docstring versi sebelumnya soal keterbatasan pembatalan paksa thread Python)."""
    global sedang_berjalan
    sedang_berjalan = False
    log_queue.put({"type": "log", "level": "WARNING", "message": "Pipeline dibatalkan oleh pengguna."})
    log_queue.put({"type": "selesai", "sukses": False, "error": "dibatalkan"})
    return {"status": "dibatalkan"}


@app.get("/api/beranda")
async def ambil_beranda():
    """Tab Beranda: berita & CVE, MASING-MASING dari tanggal terbarunya sendiri."""
    data = ambil_data_terbaru_per_kategori(hari=7)
    ada_data = bool(data["berita"]) or bool(data["cve"])
    return {
        "status": "ok" if ada_data else "kosong",
        "tanggal_berita": data["tanggal_berita"],
        "tanggal_cve": data["tanggal_cve"],
        "waktu_terakhir_scraping": data.get("waktu_terakhir_scraping"),
        "berita": data["berita"],
        "cve": data["cve"],
    }


@app.get("/api/arsip")
async def ambil_arsip():
    """Tab Arsip: seluruh grup tanggal (7 hari terakhir), terurut terbaru -> terlama."""
    grup_per_tanggal = ambil_riwayat_dikelompokkan_per_hari(hari=7)
    daftar_hari = [
        {"tanggal": tanggal, "berita": isi["berita"], "cve": isi["cve"]}
        for tanggal, isi in grup_per_tanggal.items()
    ]
    return {"status": "ok" if daftar_hari else "kosong", "hari": daftar_hari}


# Klasifikasi sumber berita: Internasional vs Nasional (sisanya = Nasional)
_SUMBER_INTERNASIONAL = {
    "The Hacker News", "BleepingComputer", "Krebs on Security",
    "Dark Reading", "SecurityWeek", "CISA News",
}

# Pemetaan kata kunci ke 6 kategori vektor serangan untuk radar chart
_VEKTOR_MAP = {
    "Ransomware": {"ransomware"},
    "Phishing": {
        "phishing", "penipuan online", "penipuan digital",
        "social engineering", "rekayasa sosial", "situs palsu",
        "website palsu", "spoofing",
    },
    "Kebocoran Data": {
        "kebocoran data", "data bocor", "pencurian data", "data dicuri",
        "data dijual", "data diperjualbelikan", "bocor", "dicuri",
        "tersebar", "dijual", "data pribadi", "data nasabah",
        "dark web", "data breach", "data leak", "kebocoran data pribadi",
    },
    "Malware": {"malware", "spyware", "trojan", "keylogger"},
    "Peretasan": {
        "peretas", "peretasan", "hacker", "diretas", "celah keamanan",
        "kerentanan sistem", "eksploitasi celah", "sql injection",
        "brute force", "serangan siber", "serangan hacker",
        "cyberattack", "cyber attack", "vulnerability", "exploit",
        "hacked", "zero-day",
    },
    "Pembajakan Aset": {
        "akun dibajak", "dibobol", "pembobolan sistem", "pembobolan akun",
        "pembobolan rekening", "defacement", "deface", "bobol sistem",
        "skimming", "carding", "ddos",
    },
}

_STATISTIK_KOSONG = {
    "total_berita": 0, "total_cve": 0, "total_vendor_cve": 0, "avg_cvss": 0,
    "kata_kunci_naik": [], "vendor_naik": [], "sampel_judul_insiden": [],
    "tren_kategori": {}, "severity_breakdown": {}, "harian": [],
    "distribusi_cvss": [], "distribusi_sumber": [],
    "nasional_vs_internasional": {"nasional": 0, "internasional": 0},
    "komposisi_jenis": {}, "harian_sumber": [], "vektor_serangan": [],
}


def _susun_statistik_dashboard_tren() -> dict:
    """Menyusun agregat statistik tren untuk visualisasi dashboard."""
    try:
        # 1. Ambil 14 hari penuh untuk komputasi analitik tren & perbandingan baseline
        df_14 = ambil_riwayat_tren(hari=14)
        if df_14.empty:
            return dict(_STATISTIK_KOSONG)

        statistik = susun_ringkasan_statistik_tren(df_14)

        # 2. Untuk visualisasi dashboard (KPI, grafik, distribusi): HANYA gunakan 7 hari terkini
        df_temp = df_14.copy()
        df_temp["tgl"] = df_temp["tanggal_publish"].fillna("").astype(str).str.slice(0, 10)
        tanggal_unik_terbaru = sorted(df_temp[df_temp["tgl"].str.match(r"^\d{4}-\d{2}-\d{2}$")]["tgl"].unique(), reverse=True)[:7]
        tanggal_urut = sorted(tanggal_unik_terbaru)

        df_7 = df_temp[df_temp["tgl"].isin(tanggal_unik_terbaru)].copy()
        df_berita = df_7[df_7["kategori"] == "berita"]
        df_cve = df_7[df_7["kategori"] == "cve"]

        total_berita = len(df_berita)
        total_cve = len(df_cve)
        total_vendor_cve = len(df_cve["vendor"].dropna().unique()) if not df_cve.empty and "vendor" in df_cve.columns else 0
        avg_cvss = round(float(df_cve["skor_cvss"].dropna().mean()), 1) if not df_cve.empty and df_cve["skor_cvss"].notna().any() else 0.0

        severity_counts = df_cve["severity"].dropna().value_counts().to_dict() if not df_cve.empty else {}

        # --- Chart Harian (7 Hari Terkini) ---
        harian_list = []
        for tgl in tanggal_urut:
            df_tgl = df_7[df_7["tgl"] == tgl]
            harian_list.append({
                "tanggal": tgl,
                "berita": int((df_tgl["kategori"] == "berita").sum()),
                "cve": int((df_tgl["kategori"] == "cve").sum()),
            })

        # --- Chart 1: Distribusi CVSS Score (7 Hari Terkini) ---
        cvss_bins = []
        if not df_cve.empty:
            cvss_vals = df_cve["skor_cvss"].dropna()
            cvss_bins = [
                {"label": "10.0", "jumlah": int((cvss_vals == 10.0).sum())},
                {"label": "9.5 - 9.9", "jumlah": int(((cvss_vals >= 9.5) & (cvss_vals < 10.0)).sum())},
                {"label": "9.0 - 9.4", "jumlah": int(((cvss_vals >= 9.0) & (cvss_vals < 9.5)).sum())},
            ]

        # --- Chart 2: Distribusi Sumber Berita (7 Hari Terkini) ---
        sumber_counts = df_berita["sumber"].value_counts().to_dict() if not df_berita.empty else {}
        distribusi_sumber = [{"sumber": s, "jumlah": int(c)} for s, c in sorted(sumber_counts.items(), key=lambda x: -x[1])]

        # --- Chart 3: Nasional vs Internasional (7 Hari Terkini) ---
        nasional_count = sum(int(c) for s, c in sumber_counts.items() if s not in _SUMBER_INTERNASIONAL)
        internasional_count = sum(int(c) for s, c in sumber_counts.items() if s in _SUMBER_INTERNASIONAL)

        # --- Chart 4: Komposisi Jenis Berita (7 Hari Terkini) ---
        jenis_raw = df_berita["kategori_relevansi"].value_counts().to_dict() if not df_berita.empty else {}
        komposisi_jenis = {k: int(v) for k, v in jenis_raw.items()}

        # --- Chart 5: Harian Sumber (7 Hari Terkini) ---
        harian_sumber = []
        for tgl in tanggal_urut:
            df_tgl_b = df_7[(df_7["tgl"] == tgl) & (df_7["kategori"] == "berita")]
            nas = int((~df_tgl_b["sumber"].isin(_SUMBER_INTERNASIONAL)).sum())
            intl = int(df_tgl_b["sumber"].isin(_SUMBER_INTERNASIONAL).sum())
            harian_sumber.append({"tanggal": tgl, "nasional": nas, "internasional": intl})

        # --- Chart 6: Vektor Serangan (7 Hari Terkini) ---
        vektor_counts = {v: 0 for v in _VEKTOR_MAP}
        if not df_berita.empty:
            for kw_str in df_berita["kata_kunci"].dropna():
                kw_list = [k.strip().lower() for k in str(kw_str).split(",") if k.strip()]
                for vektor, keywords in _VEKTOR_MAP.items():
                    if any(kw in keywords for kw in kw_list):
                        vektor_counts[vektor] += 1
        vektor_serangan = [{"vektor": v, "jumlah": c} for v, c in vektor_counts.items()]

        return {
            "total_berita": total_berita,
            "total_cve": total_cve,
            "total_vendor_cve": total_vendor_cve,
            "avg_cvss": avg_cvss,
            "kata_kunci_naik": statistik.get("berita", {}).get("kata_kunci_naik", []),
            "vendor_naik": statistik.get("cve", {}).get("vendor_naik", []),
            "sampel_judul_insiden": statistik.get("berita", {}).get("sampel_judul_insiden", []),
            "tren_kategori": statistik.get("berita", {}).get("tren_kategori", {}),
            "threat_posture": statistik.get("threat_posture", {"skor": 1.0, "level": "RENDAH", "level_label": "RENDAH (Low)", "warna": "green"}),
            "sektor_target": statistik.get("sektor_target", []),
            "vektor_serangan_kategori": statistik.get("vektor_serangan", []),
            "severity_breakdown": severity_counts,
            "harian": harian_list,
            "distribusi_cvss": cvss_bins,
            "distribusi_sumber": distribusi_sumber,
            "nasional_vs_internasional": {"nasional": nasional_count, "internasional": internasional_count},
            "komposisi_jenis": komposisi_jenis,
            "harian_sumber": harian_sumber,
            "vektor_serangan": vektor_serangan,
        }
    except Exception as e:
        logging.getLogger().error(f"Gagal menyusun statistik dashboard tren: {e}")
        return dict(_STATISTIK_KOSONG)


@app.get("/api/tren")
async def ambil_tren():
    """Tab Tren Siber: prediksi tren dan agregat statistik dari run pipeline terakhir."""
    prediksi = ambil_prediksi_tren_terakhir()
    if not prediksi:
        return {"status": "kosong", "prediksi_berita": "", "prediksi_cve": "", "tanggal_dihitung": None, "statistik": None}
    
    statistik = _susun_statistik_dashboard_tren()
    return {
        "status": "ok",
        "prediksi_berita": prediksi["prediksi_berita"],
        "prediksi_cve": prediksi["prediksi_cve"],
        "tanggal_dihitung": prediksi["tanggal_dihitung"],
        "statistik": statistik,
    }


@app.get("/")
async def halaman_utama(request: Request):
    return templates.TemplateResponse(request, "index.html")