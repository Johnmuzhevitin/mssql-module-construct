from __future__ import annotations

import sys
from pathlib import Path

import pyodbc
import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from core.crypto import CryptoManager
from core.storage import DB_PATH, get_connection, init_db
from modules.datasource import ConnectionManager, ConnectionProfile


@pytest.fixture(autouse=True)
def clean_db():
    if DB_PATH.exists():
        DB_PATH.unlink()
    yield
    if DB_PATH.exists():
        DB_PATH.unlink()


def _prepare_manager() -> ConnectionManager:
    init_db()
    conn = get_connection()
    crypto = CryptoManager(conn)
    crypto.set_master_password("pwd")
    return ConnectionManager(conn, crypto)


def test_create_and_reload_profile():
    manager = _prepare_manager()
    profile = ConnectionProfile(
        name="p1",
        server="srv",
        database="db",
        auth="sql",
        username="user",
        password="secret",
    )
    manager.create(profile)
    assert profile.id is not None
    manager.conn.close()

    # Reload
    conn2 = get_connection()
    crypto2 = CryptoManager(conn2)
    assert crypto2.verify_master_password("pwd")
    manager2 = ConnectionManager(conn2, crypto2)
    profiles = manager2.list()
    assert len(profiles) == 1
    loaded = profiles[0]
    assert loaded.name == "p1"
    assert loaded.username == "user"
    assert loaded.password == "secret"
    manager2.conn.close()


def test_delete_profile_removes_secrets():
    manager = _prepare_manager()
    profile = ConnectionProfile(
        name="p2",
        server="srv",
        database="db",
        auth="sql",
        username="u",
        password="p",
    )
    manager.create(profile)
    pid = profile.id
    assert pid is not None
    manager.delete(pid)
    cur = manager.conn.cursor()
    cur.execute("SELECT COUNT(*) FROM connections")
    assert cur.fetchone()[0] == 0
    cur.execute("SELECT COUNT(*) FROM secrets")
    assert cur.fetchone()[0] == 0
    manager.conn.close()


def test_test_connection_handles_error(monkeypatch):
    manager = _prepare_manager()
    profile = ConnectionProfile(
        name="p3",
        server="srv",
        database="db",
        auth="sql",
        username="u",
        password="p",
    )

    def fake_connect(*args, **kwargs):  # noqa: D401
        raise pyodbc.Error("fail")

    monkeypatch.setattr(pyodbc, "connect", fake_connect)
    ok, error = manager.test_connection(profile)
    assert not ok
    assert "fail" in (error or "").lower()
    manager.conn.close()


def test_test_connection_success(monkeypatch):
    manager = _prepare_manager()
    profile = ConnectionProfile(
        name="p4",
        server="srv",
        database="db",
        auth="sql",
        username="u",
        password="p",
    )

    class DummyCursor:
        timeout = 0

        def execute(self, *args, **kwargs):
            return None

        def fetchone(self):
            return [1]

        def close(self):
            return None

    class DummyConn:
        def cursor(self):
            return DummyCursor()

        def close(self):
            return None

    monkeypatch.setattr(pyodbc, "connect", lambda *a, **k: DummyConn())
    ok, error = manager.test_connection(profile)
    assert ok
    assert error is None
    manager.conn.close()
