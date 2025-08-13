from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from core.storage import DB_PATH, init_db


@pytest.fixture(autouse=True)
def clean_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


def test_initialization_creates_db_and_tables():
    """Database file is created and contains all expected tables."""

    init_db()
    assert DB_PATH.exists()

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    expected = {
        "connections",
        "secrets",
        "schema_cache",
        "datasets",
        "exports",
        "audit",
        "settings",
    }
    assert expected.issubset(tables)
    conn.close()
