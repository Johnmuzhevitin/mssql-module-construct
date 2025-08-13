from __future__ import annotations

import sqlite3
from pathlib import Path

from .config import BASE_DIR
from .migrations import apply_migrations

DB_PATH = BASE_DIR / "data" / "app.db"


def get_connection() -> sqlite3.Connection:
    """Return a connection to the local SQLite database, applying migrations."""

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    apply_migrations(conn)
    return conn


def init_db() -> None:
    """Ensure the database file exists and schema is up to date."""

    conn = get_connection()
    conn.close()

