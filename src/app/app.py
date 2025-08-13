from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from core.config import load_config
from ui.main_window import MainWindow

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def ensure_dirs() -> None:
    """Создаёт необходимые каталоги."""
    for name in ("data", "logs", "cache"):
        (BASE_DIR / name).mkdir(parents=True, exist_ok=True)


def setup_logging() -> None:
    """Настраивает логирование с ротацией файлов."""
    log_dir = BASE_DIR / "logs"
    handler = RotatingFileHandler(
        log_dir / "app.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        format="%(asctime)s - %(levelname)s - %(message)s",
    )


def main() -> None:
    """Точка входа в приложение."""
    ensure_dirs()
    setup_logging()
    config = load_config()
    logging.info("Приложение запущено")

    app = QApplication(sys.argv)
    app.setOrganizationName("mssql-module-construct")
    app.setApplicationName(config.app_name)

    window = MainWindow(config)
    window.resize(800, 600)
    window.show()

    delay = os.getenv("APP_AUTOSTOP_DELAY")
    if delay:
        QTimer.singleShot(int(delay), app.quit)

    def on_exit() -> None:
        logging.info("Приложение остановлено")

    import atexit

    atexit.register(on_exit)
    sys.exit(app.exec())
