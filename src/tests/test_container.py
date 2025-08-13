from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))


import pytest

from core.container import (
    Container,
    EncryptionManager,
    LocalDBManager,
    container,
)
from core.config import AppConfig


def test_register_and_get():
    """Services can be registered and retrieved lazily."""

    calls = {"count": 0}

    def provider() -> object:
        calls["count"] += 1
        return object()

    c = Container()
    c.register("service", provider)

    assert calls["count"] == 0
    first = c.get("service")
    assert calls["count"] == 1
    second = c.get("service")
    assert first is second
    assert calls["count"] == 1


def test_scopes_isolate_instances():
    c = Container()
    c.register("value", lambda: object())
    c.register("value", lambda: object(), scope="test")

    app_obj = c.get("value")
    test_obj = c.get("value", scope="test")

    assert app_obj is not test_obj


def test_default_services_registered():
    cfg = container.get("config")
    log = container.get("logger")
    enc = container.get("encryption_manager")
    db = container.get("local_db_manager")

    assert isinstance(cfg, AppConfig)
    assert isinstance(log, logging.Logger)
    assert isinstance(enc, EncryptionManager)
    assert isinstance(db, LocalDBManager)
