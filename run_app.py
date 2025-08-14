"""Точка входа для запуска приложения.

Запускает графический интерфейс, предварительно инициализируя
глобальный контекст, шину событий и обнаруживая доступные модули.
"""

from __future__ import annotations

import atexit
import logging
import os
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from src.core.app import AppContext
from src.core.config import load_config
from src.core.events import EventBus
from src.core.logger import setup_logging
from src.core.registry import autodiscover_modules
from src.ui.main_window import MainWindow


def main() -> None:
    """Инициализация зависимостей и запуск главного окна."""

    context = AppContext()
    context.ensure_dirs()
    setup_logging(context.logs_dir)

    event_bus = EventBus()
    context.set("event_bus", event_bus)

    config = load_config()
    autodiscover_modules()
    logging.info("Приложение запущено")

    app = QApplication(sys.argv)
    app.setOrganizationName("mssql-module-construct")
    app.setApplicationName(config.app_name)

    window = MainWindow(config, event_bus)
    window.resize(800, 600)
    window.show()

    delay = os.getenv("APP_AUTOSTOP_DELAY")
    if delay:
        QTimer.singleShot(int(delay), app.quit)

    def on_exit() -> None:
        logging.info("Приложение остановлено")

    atexit.register(on_exit)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

