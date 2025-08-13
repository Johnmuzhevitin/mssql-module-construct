from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
DEFAULT_CONFIG_PATH = ASSETS_DIR / "config.default.json"
USER_CONFIG_PATH = ASSETS_DIR / "config.json"


class AppConfig(BaseModel, extra="allow"):
    """Модель конфигурации приложения."""

    app_name: str = "mssql-module-construct"
    version: str = "0.1.0"


def load_config() -> AppConfig:
    """Загружает конфигурацию, объединяя пользовательскую и дефолтную."""

    if not DEFAULT_CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Не найден файл конфигурации по умолчанию: {DEFAULT_CONFIG_PATH}"
        )
    with DEFAULT_CONFIG_PATH.open(encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)
    if USER_CONFIG_PATH.exists():
        with USER_CONFIG_PATH.open(encoding="utf-8") as f:
            user_data = json.load(f)
        data.update(user_data)
    return AppConfig(**data)
