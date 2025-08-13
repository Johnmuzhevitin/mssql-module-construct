from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import BASE_DIR


def setup_logging(log_dir: Path | None = None) -> logging.Logger:
    """Настраивает логирование с ротацией файлов."""

    log_dir = log_dir or (BASE_DIR / "logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "app.log"

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    if not any(isinstance(h, RotatingFileHandler) and h.baseFilename == str(log_file) for h in logger.handlers):
        handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=5, encoding="utf-8")
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
