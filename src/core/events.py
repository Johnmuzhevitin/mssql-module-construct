from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, List


class EventBus:
    """Простая шина событий."""

    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[..., Any]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Callable[..., Any]) -> None:
        """Подписывает обработчик на событие."""

        self._subscribers[event].append(handler)

    def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """Вызывает все обработчики, подписанные на событие."""

        for handler in list(self._subscribers.get(event, [])):
            handler(*args, **kwargs)
