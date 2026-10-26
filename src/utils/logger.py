"""
Modul logging terpusat untuk seluruh pipeline.
Berfungsi agar format log konsisten dan mudah ditelusuri 
saat pipeline jalan otomatis tanpa pengawasan.
"""
import logging
import sys
from datetime import datetime
from pathlib import Path


def setup_logger(name: str = "cyber_news_digest", log_dir: str = "logs") -> logging.Logger:
    """
    Membuat logger dengan output ganda: ke console (stdout) 
    dan ke file harian di folder logs/. 
    File log per-hari membantu audit ketika pipeline gagal.
    """
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
    log_file = Path(log_dir) / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except PermissionError:
        pass

    return logger
