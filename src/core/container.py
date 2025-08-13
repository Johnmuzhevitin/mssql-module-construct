from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

from .config import load_config


class ServiceNotRegisteredError(KeyError):
    """Raised when requesting an unregistered service."""


class Container:
    """Simple service locator with lazy initialization and scopes."""

    def __init__(self) -> None:
        self._providers: Dict[str, Dict[str, Callable[[], Any]]] = {}
        self._instances: Dict[str, Dict[str, Any]] = {}

    def register(
        self, name: str, provider: Callable[[], Any], *, scope: str = "app"
    ) -> None:
        """Register a provider for a service within a scope."""

        self._providers.setdefault(scope, {})[name] = provider

    def get(self, name: str, *, scope: str = "app") -> Any:
        """Retrieve a service instance, creating it lazily."""

        if scope not in self._instances:
            self._instances[scope] = {}
        if name in self._instances[scope]:
            return self._instances[scope][name]
        try:
            provider = self._providers[scope][name]
        except KeyError as exc:
            raise ServiceNotRegisteredError(
                f"Service '{name}' is not registered in scope '{scope}'"
            ) from exc
        instance = provider()
        self._instances[scope][name] = instance
        return instance

    def clear(self, *, scope: Optional[str] = None) -> None:
        """Clear cached instances for a specific scope or all scopes."""

        if scope is None:
            self._instances.clear()
        else:
            self._instances.pop(scope, None)


class EncryptionManager:
    """Placeholder encryption manager."""

    def encrypt(self, data: bytes) -> bytes:
        return data

    def decrypt(self, data: bytes) -> bytes:
        return data


class LocalDBManager:
    """Placeholder local database manager."""

    def connect(self) -> None:
        pass


def create_logger() -> logging.Logger:
    """Create and configure application logger."""

    logger = logging.getLogger("app")
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


container = Container()
container.register("config", load_config)
container.register("logger", create_logger)
container.register("encryption_manager", EncryptionManager)
container.register("local_db_manager", LocalDBManager)
