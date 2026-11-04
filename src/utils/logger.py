"""
Modul logging terpusat untuk seluruh pipeline.
Berfungsi agar format log konsisten dan mudah ditelusuri 
saat pipeline jalan otomatis tanpa pengawasan.
"""
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Penanda agar pembersihan log kedaluwarsa hanya dieksekusi satu kali per siklus runtime
_SUDAH_DIBERSIHKAN = False


def bersihkan_log_kedaluwarsa(log_dir: str = "logs", retensi_hari: int = 14) -> int:
    """
    Menghapus berkas log lama yang berusia lebih dari retensi_hari (default 14 hari).
    Mencegah penumpukan berkas log yang dapat memenuhi kapasitas penyimpanan server.
    """
    path_dir = Path(log_dir)
    if not path_dir.exists():
        return 0

    sekarang = datetime.now()
    batas_waktu = sekarang - timedelta(days=retensi_hari)
    terhapus = 0

    for berkas in path_dir.glob("*.log"):
        try:
            # Coba parsing tanggal dari format nama berkas YYYY-MM-DD.log
            nama_dasar = berkas.stem
            try:
                tgl_berkas = datetime.strptime(nama_dasar, "%Y-%m-%d")
            except ValueError:
                # Fallback ke waktu modifikasi berkas (mtime)
                tgl_berkas = datetime.fromtimestamp(berkas.stat().st_mtime)

            if tgl_berkas < batas_waktu:
                berkas.unlink(missing_ok=True)
                terhapus += 1
        except Exception:
            # Lewati bila berkas sedang digunakan oleh proses lain
            pass

    return terhapus


def setup_logger(
    name: str = "cyber_news_digest",
    log_dir: str = "logs",
    retensi_hari: int = 14
) -> logging.Logger:
    """
    Membuat logger dengan output ganda: ke console (stdout) 
    dan ke file harian di folder logs/. 
    File log per-hari membantu audit ketika pipeline gagal.
    Dilengkapi retensi otomatis untuk membersihkan log berusia > 14 hari.
    """
    global _SUDAH_DIBERSIHKAN

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Jalankan retensi pembersihan log kedaluwarsa satu kali per lifecycle aplikasi
    if not _SUDAH_DIBERSIHKAN:
        bersihkan_log_kedaluwarsa(log_dir=log_dir, retensi_hari=retensi_hari)
        _SUDAH_DIBERSIHKAN = True

    log_file = Path(log_dir) / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        pass

    return logger
