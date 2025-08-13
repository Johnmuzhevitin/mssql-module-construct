from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List


class Module(ABC):
    """Контракт для модулей приложения."""

    id: str
    title: str
    icon: str

    @abstractmethod
    def mount(self, ui: Any, app: Any, bus: Any) -> None:
        """Инициализирует модуль и добавляет его в интерфейс."""

    @abstractmethod
    def unmount(self) -> None:
        """Удаляет модуль из интерфейса."""

    @abstractmethod
    def get_sidebar_items(self) -> List[Any]:
        """Возвращает элементы боковой панели."""

    @abstractmethod
    def get_properties_widget(self, ui: Any) -> Any:
        """Создаёт виджет свойств."""

    @abstractmethod
    def get_preview_widget(self, ui: Any) -> Any:
        """Создаёт виджет предпросмотра."""


class BaseModule(Module):
    """Базовый модуль с пустыми реализациями по умолчанию."""

    id = ""
    title = ""
    icon = ""

    def mount(self, ui: Any, app: Any, bus: Any) -> None:
        pass

    def unmount(self) -> None:
        pass

    def get_sidebar_items(self) -> List[Any]:
        return []

    def get_properties_widget(self, ui: Any) -> Any:
        return None

    def get_preview_widget(self, ui: Any) -> Any:
        return None
