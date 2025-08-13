from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from .config import BASE_DIR


@dataclass
class AppContext:
    """Глобальный контекст приложения.

    Хранит пути к основным каталогам, активный модуль и произвольное
    состояние в простом ``store``.
    """

    base_dir: Path = BASE_DIR
    data_dir: Path = field(default_factory=lambda: BASE_DIR / "data")
    logs_dir: Path = field(default_factory=lambda: BASE_DIR / "logs")
    cache_dir: Path = field(default_factory=lambda: BASE_DIR / "cache")
    active_module: Optional[str] = None
    store: Dict[str, Any] = field(default_factory=dict)

    def ensure_dirs(self) -> None:
        """Создаёт необходимые каталоги, если их нет."""

        for path in (self.data_dir, self.logs_dir, self.cache_dir):
            path.mkdir(parents=True, exist_ok=True)

    def set_active_module(self, name: str) -> None:
        """Задаёт имя активного модуля."""

        self.active_module = name

    def get(self, key: str, default: Any | None = None) -> Any | None:
        """Получает значение из ``store``."""

        return self.store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Сохраняет значение в ``store``."""

        self.store[key] = value
