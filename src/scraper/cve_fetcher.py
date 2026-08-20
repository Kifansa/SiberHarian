"""
Pengambilan data kerentanan (CVE) dari NVD (National Vulnerability
Database) REST API v2.0. Berbeda dari sumber RSS lainnya, modul ini
melakukan query terstruktur berdasarkan rentang tanggal publikasi dan
skor CVSS minimum.
"""
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional

import pandas as pd
import requests

from src.utils.http_client import buat_session_retry
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def _ekstrak_skor_cvss(metrics: dict) -> Optional[float]:
    """
    Mengambil skor CVSS tertinggi yang tersedia dari objek 'metrics'
    NVD. NVD bisa punya beberapa versi CVSS sekaligus (v4, v3.1, v3.0,
    v2) tergantung kapan CVE tersebut dipublikasikan/diupdate; kita
    prioritaskan versi terbaru karena lebih akurat merefleksikan
    tingkat keparahan saat ini.
    """
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entri = metrics.get(key)
        if entri:
            return entri[0]["cvssData"]["baseScore"]
    return None


def _ekstrak_severity(metrics: dict) -> Optional[str]:
    """Mengambil label severity (LOW/MEDIUM/HIGH/CRITICAL) yang selaras dengan skor di atas."""
    for key in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30"):
        entri = metrics.get(key)
        if entri:
            return entri[0]["cvssData"].get("baseSeverity")
    entri = metrics.get("cvssMetricV2")
    if entri:
        return entri[0].get("baseSeverity")
    return None

def _ekstrak_vendor_dari_cpe(cve: dict) -> Optional[tuple]:
    """
    Mencoba ambil vendor & produk dari data CPE terstruktur. Mengembalikan
    None jika tidak tersedia — kondisi UMUM untuk CVE yang baru saja
    dipublikasikan dan belum sempat dianalisis NVD (status 'Awaiting
    Analysis'; per pertengahan 2026 mayoritas CVE baru mengalami ini).
    """
    for node_config in cve.get("configurations", []):
        for node in node_config.get("nodes", []):
            for cpe_match in node.get("cpeMatch", []):
                bagian = cpe_match.get("criteria", "").split(":")
                if len(bagian) >= 5:
                    vendor = bagian[3].replace("_", " ").title()
                    produk = bagian[4].replace("_", " ").title()
                    return vendor, produk
    return None

def _ekstrak_vendor_dari_deskripsi(deskripsi: str, daftar_vendor_dikenal: List[str]) -> Optional[str]:
    """
    Fallback saat CPE kosong: mencari nama vendor yang dikenal di dalam
    teks deskripsi CVE. NVD hampir selalu menyebut nama produk/vendor
    di deskripsi walau data CPE terstruktur belum diisi.
    """
    deskripsi_lower = deskripsi.lower()
    for vendor in daftar_vendor_dikenal:
        if vendor.lower() in deskripsi_lower:
            return vendor
    return None


def _ekstrak_vendor_produk(cve: dict, daftar_vendor_dikenal: List[str]) -> tuple:
    """
    Prioritas penentuan vendor & produk:
    1. Data CPE terstruktur (paling akurat, tapi sering kosong).
    2. Pencarian nama vendor dikenal di teks deskripsi (fallback).
    3. Label "Lainnya" jika keduanya gagal.
    """
    hasil_cpe = _ekstrak_vendor_dari_cpe(cve)
    if hasil_cpe:
        return hasil_cpe[0], hasil_cpe[1]

    deskripsi_list = cve.get("descriptions", [])
    deskripsi_en = next((d["value"] for d in deskripsi_list if d.get("lang") == "en"), "")
    vendor_dari_teks = _ekstrak_vendor_dari_deskripsi(deskripsi_en, daftar_vendor_dikenal)
    if vendor_dari_teks:
        return vendor_dari_teks, "(lihat deskripsi)"

    return "Lainnya / Belum Teridentifikasi", "-"


def _parse_item_cve(item: dict, daftar_vendor_dikenal: List[str]) -> Optional[dict]:
    """Mengubah satu objek 'vulnerability' dari respons NVD menjadi dict ringkas."""
    cve = item.get("cve", {})
    cve_id = cve.get("id")
    if not cve_id:
        return None

    deskripsi_list = cve.get("descriptions", [])
    deskripsi_en = next((d["value"] for d in deskripsi_list if d.get("lang") == "en"), "")

    metrics = cve.get("metrics", {})
    skor = _ekstrak_skor_cvss(metrics)
    severity = _ekstrak_severity(metrics)
    vendor, produk = _ekstrak_vendor_produk(cve, daftar_vendor_dikenal)

    return {
        "cve_id": cve_id,
        "deskripsi": deskripsi_en,
        "skor_cvss": skor,
        "severity": severity,
        "vendor": vendor,
        "produk": produk,
        "tanggal_publish": cve.get("published", "")[:19].replace("T", " "),
        "link": f"https://nvd.nist.gov/vuln/detail/{cve_id}",
    }

def ambil_cve_terbaru(
    base_url: str,
    window_hours: int = 24,
    min_cvss_score: float = 7.0,
    daftar_vendor_dikenal: Optional[List[str]] = None,
    api_key: Optional[str] = None,
    timeout: int = 20,
) -> pd.DataFrame:
    """
    Mengambil CVE yang dipublikasikan dalam N jam terakhir dari NVD API,
    difilter berdasarkan skor CVSS minimum.

    NVD API membatasi rentang query maksimal 120 hari per request dan
    menggunakan pagination (default 2000 hasil/halaman), jadi loop
    pagination tetap disiapkan meskipun untuk window 24 jam biasanya
    hasilnya jauh di bawah itu.
    """
    daftar_vendor_dikenal = daftar_vendor_dikenal or []
    batas_akhir = datetime.now(timezone.utc)
    batas_awal = batas_akhir - timedelta(hours=window_hours)

    headers = {"apiKey": api_key} if api_key else {}
    jeda_request = 6 if not api_key else 0.6  # patuhi rate limit resmi NVD
    session = buat_session_retry(max_retry=3, backoff_factor=2.0)

    hasil_semua = []
    start_index = 0
    total_hasil = None
    data_lengkap = True

    while total_hasil is None or start_index < total_hasil:
        params = {
            "pubStartDate": batas_awal.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "pubEndDate": batas_akhir.strftime("%Y-%m-%dT%H:%M:%S.000"),
            "startIndex": start_index,
            "resultsPerPage": 500,  # diperkecil dari default 2000 - request lebih ringan,
                                     # lebih kecil kemungkinan timeout per halaman
        }
        try:
            resp = session.get(base_url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.error(
                f"GAGAL mengambil halaman CVE (startIndex={start_index}): {e}. "
                f"Data CVE untuk run ini TIDAK LENGKAP - kemungkinan ada CVE Critical "
                f"yang terlewat di halaman ini dan seterusnya."
            )
            data_lengkap = False
            break

        data = resp.json()
        total_hasil = data.get("totalResults", 0)
        vulnerabilities = data.get("vulnerabilities", [])

        for item in vulnerabilities:
            parsed = _parse_item_cve(item, daftar_vendor_dikenal)
            if parsed:
                hasil_semua.append(parsed)

        start_index += len(vulnerabilities)
        if start_index < total_hasil:
            time.sleep(jeda_request)

    if data_lengkap:
        logger.info(f"Total CVE dipublikasikan dalam {window_hours} jam terakhir: {len(hasil_semua)} (LENGKAP).")
    else:
        logger.warning(
            f"Total CVE berhasil diambil: {len(hasil_semua)} dari total {total_hasil or '?'} "
            f"yang seharusnya ada (TIDAK LENGKAP, ada halaman yang gagal)."
        )

    df = pd.DataFrame(hasil_semua)
    if df.empty:
        return df
    
    # Filter berdasarkan skor CVSS minimum DAN severity CRITICAL saja
    df_filtered = df[
        (df["skor_cvss"].fillna(0) >= min_cvss_score) & (df["severity"] == "CRITICAL")
    ].reset_index(drop=True)
    logger.info(
        f"Setelah filter CVSS >= {min_cvss_score} DAN severity CRITICAL: "
        f"{len(df_filtered)} CVE (dari {len(df)} total)."
    )
    return df_filtered

def kelompokkan_cve_per_vendor(df: pd.DataFrame) -> List[dict]:
    """
    Mengelompokkan CVE CRITICAL per vendor, diurutkan: vendor dengan
    jumlah CVE terbanyak di atas. Di dalam grup, skor CVSS tertinggi
    diutamakan.
    """
    if df.empty:
        return []

    grup_hasil = []
    for vendor, grup in df.groupby("vendor"):
        grup_terurut = grup.sort_values(by="skor_cvss", ascending=False)
        grup_hasil.append({
            "vendor": vendor,
            "jumlah_critical": len(grup_terurut),
            "cve_list": grup_terurut.to_dict("records"),
        })

    grup_hasil.sort(key=lambda g: (-g["jumlah_critical"], g["vendor"]))
    return grup_hasil

def susun_struktur_digest_cve(df: pd.DataFrame) -> dict:
    """
    Menyusun struktur akhir CVE untuk kebutuhan digest. Karena sumber CVE
    sudah difilter CRITICAL-only sejak ambil_cve_terbaru(), fungsi ini
    cuma punya 2 mode:
    - Tidak ada CVE CRITICAL sama sekali -> mode 'kosong'
    - Ada CVE CRITICAL                   -> mode 'ada_critical': semua
      dikelompokkan per vendor & dinarasikan lengkap oleh LLM.
    """
    if df.empty:
        return {"mode": "kosong"}

    grup_vendor_critical = kelompokkan_cve_per_vendor(df)

    return {
        "mode": "ada_critical",
        "grup_critical": grup_vendor_critical,
        "jumlah_critical_total": len(df),
    }