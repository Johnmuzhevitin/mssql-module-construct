from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .module_api import Module


class ModuleRegistry:
    """Реестр модулей приложения."""

    def __init__(self) -> None:
        self._modules: Dict[str, Module] = {}

    def register(self, module: Module) -> None:
        """Регистрирует модуль."""
        if module.id in self._modules:
            logging.warning("Модуль %s уже зарегистрирован", module.id)
            return
        self._modules[module.id] = module

    def get(self, module_id: str) -> Optional[Module]:
        """Возвращает модуль по идентификатору."""
        return self._modules.get(module_id)

    def all(self) -> List[Module]:
        """Возвращает все зарегистрированные модули."""
        return list(self._modules.values())


registry = ModuleRegistry()


def autodiscover_modules(base_path: Optional[Path] = None) -> List[Module]:
    """Импортирует модули из каталога ``modules`` и регистрирует их."""
    modules_dir = base_path or Path(__file__).resolve().parent.parent / "modules"

    if not modules_dir.exists():
        logging.info("Каталог модулей %s не найден", modules_dir)
        return []

    for item in modules_dir.iterdir():
        module_file = item / "module.py"
        if module_file.exists():
            module_name = f"modules.{item.name}.module"
            try:
                importlib.import_module(module_name)
            except Exception:  # pragma: no cover - логирование исключений
                logging.exception("Ошибка загрузки модуля %s", module_name)

    modules = registry.all()
    if modules:
        logging.info("Обнаруженные модули: %s", ", ".join(m.id for m in modules))
    else:
        logging.info("Модули не обнаружены")
    return modules
