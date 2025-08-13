from __future__ import annotations

import sqlite3
from typing import Callable, List


def migration_1(conn: sqlite3.Connection) -> None:
    """Initial schema with all application tables."""

    cursor = conn.cursor()
    # Connections information
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            server TEXT NOT NULL,
            database TEXT NOT NULL,
            auth TEXT NOT NULL,
            conn_timeout INTEGER NOT NULL DEFAULT 5,
            query_timeout INTEGER NOT NULL DEFAULT 30
        )
        """
    )

    # Stored secrets
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS secrets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value BLOB NOT NULL
        )
        """
    )

    # Cached database schemas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            schema TEXT NOT NULL
        )
        """
    )

    # Dataset definitions
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            query TEXT NOT NULL
        )
        """
    )

    # Export history
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS exports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            path TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )

    # Audit log
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            action TEXT NOT NULL,
            created_at TEXT NOT NULL,
            details TEXT
        )
        """
    )

    # Application settings
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    conn.commit()


MIGRATIONS: List[Callable[[sqlite3.Connection], None]] = [migration_1]


def apply_migrations(conn: sqlite3.Connection) -> None:
    """Apply any pending migrations to the connected database."""

    cursor = conn.cursor()
    cursor.execute("PRAGMA user_version")
    row = cursor.fetchone()
    current_version = int(row[0]) if row else 0

    for version, migration in enumerate(MIGRATIONS, start=1):
        if current_version < version:
            migration(conn)
            cursor.execute(f"PRAGMA user_version = {version}")
            conn.commit()

