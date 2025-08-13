from __future__ import annotations

import sqlite3
from typing import List, Optional, Tuple

import pyodbc
from pydantic import BaseModel, field_validator

# Import ``core`` in a way that works whether the project is installed or run
# directly with ``python -m src.app``.
try:
    # When tests or an installed package import ``modules.datasource``, ``core``
    # is available as a top-level package.
    from core.crypto import CryptoManager
    from core.storage import get_connection
except ImportError:  # pragma: no cover - fallback for running from source
    # When executing directly from the source tree, ``modules`` is imported as
    # ``src.modules`` and we need a relative import to reach ``src.core``.
    from ...core.crypto import CryptoManager
    from ...core.storage import get_connection


class ConnectionProfile(BaseModel):
    """Model representing a single connection profile."""

    id: int | None = None
    name: str
    server: str
    database: str
    auth: str = "sql"  # 'sql' or 'windows'
    username: str | None = None
    password: str | None = None
    connect_timeout: int = 5
    query_timeout: int = 30

    @field_validator("auth")
    @classmethod
    def _validate_auth(cls, v: str) -> str:  # noqa: D401
        """Ensure ``auth`` is either ``sql`` or ``windows"."""

        if v not in {"sql", "windows"}:
            raise ValueError("auth must be 'sql' or 'windows'")
        return v


class ConnectionManager:
    """CRUD operations and connection testing for MSSQL profiles."""

    def __init__(self, conn: sqlite3.Connection | None = None, crypto: CryptoManager | None = None) -> None:
        self.conn = conn or get_connection()
        self.crypto = crypto or CryptoManager(self.conn)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    def create(self, profile: ConnectionProfile) -> ConnectionProfile:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO connections (name, server, database, auth, conn_timeout, query_timeout)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                profile.name,
                profile.server,
                profile.database,
                profile.auth,
                profile.connect_timeout,
                profile.query_timeout,
            ),
        )
        profile.id = cur.lastrowid
        self.conn.commit()
        self._store_secrets(profile)
        return profile

    def list(self) -> List[ConnectionProfile]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name, server, database, auth, conn_timeout, query_timeout FROM connections ORDER BY id"
        )
        rows = cur.fetchall()
        profiles: List[ConnectionProfile] = []
        for row in rows:
            pid, name, server, db, auth, c_to, q_to = row
            username = password = None
            if auth == "sql":
                username = self.crypto.get_secret(f"connection:{pid}:username")
                password = self.crypto.get_secret(f"connection:{pid}:password")
            profiles.append(
                ConnectionProfile(
                    id=pid,
                    name=name,
                    server=server,
                    database=db,
                    auth=auth,
                    username=username,
                    password=password,
                    connect_timeout=c_to,
                    query_timeout=q_to,
                )
            )
        return profiles

    def get(self, profile_id: int) -> Optional[ConnectionProfile]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT id, name, server, database, auth, conn_timeout, query_timeout FROM connections WHERE id=?",
            (profile_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        pid, name, server, db, auth, c_to, q_to = row
        username = password = None
        if auth == "sql":
            username = self.crypto.get_secret(f"connection:{pid}:username")
            password = self.crypto.get_secret(f"connection:{pid}:password")
        return ConnectionProfile(
            id=pid,
            name=name,
            server=server,
            database=db,
            auth=auth,
            username=username,
            password=password,
            connect_timeout=c_to,
            query_timeout=q_to,
        )

    def update(self, profile: ConnectionProfile) -> None:
        if profile.id is None:
            raise ValueError("profile id required for update")
        cur = self.conn.cursor()
        cur.execute(
            """
            UPDATE connections
            SET name=?, server=?, database=?, auth=?, conn_timeout=?, query_timeout=?
            WHERE id=?
            """,
            (
                profile.name,
                profile.server,
                profile.database,
                profile.auth,
                profile.connect_timeout,
                profile.query_timeout,
                profile.id,
            ),
        )
        self.conn.commit()
        self._store_secrets(profile)

    def delete(self, profile_id: int) -> None:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM connections WHERE id=?", (profile_id,))
        for key in [f"connection:{profile_id}:username", f"connection:{profile_id}:password"]:
            cur.execute("DELETE FROM secrets WHERE key=?", (key,))
        self.conn.commit()

    # ------------------------------------------------------------------
    # Secret handling
    # ------------------------------------------------------------------
    def _store_secrets(self, profile: ConnectionProfile) -> None:
        if profile.id is None:
            return
        if profile.auth == "sql":
            if profile.username is not None:
                self.crypto.set_secret(f"connection:{profile.id}:username", profile.username)
            if profile.password is not None:
                self.crypto.set_secret(f"connection:{profile.id}:password", profile.password)

    # ------------------------------------------------------------------
    # Connection testing
    # ------------------------------------------------------------------
    def _build_conn_string(self, profile: ConnectionProfile) -> str:
        base = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={profile.server};"
            f"DATABASE={profile.database};TrustServerCertificate=yes;"
        )
        if profile.auth == "windows":
            return base + "Trusted_Connection=yes;"
        return base + f"UID={profile.username};PWD={profile.password};"

    def test_connection(self, profile: ConnectionProfile) -> Tuple[bool, Optional[str]]:
        conn_str = self._build_conn_string(profile)
        try:
            connection = pyodbc.connect(conn_str, timeout=profile.connect_timeout)
            cursor = connection.cursor()
            cursor.timeout = profile.query_timeout
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            connection.close()
            return True, None
        except pyodbc.Error as exc:  # pragma: no cover - error path
            return False, str(exc)
