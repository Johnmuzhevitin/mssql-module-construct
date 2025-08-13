from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from modules.security.sql_guard import SQLSecurityError, validate_sql


def test_valid_select_passes():
    validate_sql("SELECT * FROM users WHERE id = 1")


@pytest.mark.parametrize(
    "query",
    [
        "INSERT INTO users VALUES (1)",
        "UPDATE users SET name='x'",
        "DELETE FROM users",
        "MERGE INTO users AS t",
        "EXEC sp_who",
        "CREATE TABLE t(id INT)",
        "ALTER TABLE t ADD c INT",
        "DROP TABLE t",
        "SELECT * FROM users; DROP TABLE users",
        "SELECT * FROM users -- comment",
        "SELECT /* comment */ * FROM users",
    ],
)
def test_invalid_queries(query: str):
    with pytest.raises(SQLSecurityError):
        validate_sql(query)
