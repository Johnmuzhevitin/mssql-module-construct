from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from modules.envcheck import (
    CheckStatus,
    check_directory_writable,
    check_odbc_driver,
    check_python_version,
)


class DummyProcess:
    def __init__(self, stdout: str) -> None:
        self.stdout = stdout


def test_check_odbc_driver_found(monkeypatch):
    def fake_run(args):
        return DummyProcess("ODBC Driver 17 for SQL Server")

    monkeypatch.setattr("modules.envcheck.checks._run_odbcinst", fake_run)
    result = check_odbc_driver()
    assert result.status is CheckStatus.OK


def test_check_odbc_driver_missing(monkeypatch):
    def fake_run(args):
        return DummyProcess("Some Other Driver")

    monkeypatch.setattr("modules.envcheck.checks._run_odbcinst", fake_run)
    result = check_odbc_driver()
    assert result.status is CheckStatus.ERROR
    assert "не найден" in result.message.lower()


def test_check_directory_writable(tmp_path):
    result = check_directory_writable(tmp_path)
    assert result.status is CheckStatus.OK


def test_check_python_version(monkeypatch):
    class V:
        major, minor, micro = 3, 9, 0

    monkeypatch.setattr(sys, "version_info", V())
    result = check_python_version()
    assert result.status is CheckStatus.ERROR
