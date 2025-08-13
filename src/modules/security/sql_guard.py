"""Simple SQL validator enforcing read-only (SELECT) policy.

The validator checks that the query contains only a limited set of characters
and does not include any blacklisted SQL keywords or comment tokens.
"""

from __future__ import annotations

import re
from typing import Iterable

__all__ = ["SQLSecurityError", "validate_sql"]


class SQLSecurityError(ValueError):
    """Raised when a SQL statement violates the security policy."""


# Disallowed keywords that could modify database state or execute code
BLACKLIST_KEYWORDS: set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "MERGE",
    "EXEC",
    "CREATE",
    "ALTER",
    "DROP",
}

# Allowed characters (case insensitive). The pattern intentionally permits
# common SQL syntax while excluding dangerous symbols like ';'.
_ALLOWED_CHARS_RE = re.compile(r"^[A-Za-z0-9_\s,.*=<>!+\-/()%@'\"]*$")


def _tokenize(query: str) -> Iterable[str]:
    """Return alphanumeric tokens from *query* in upper-case."""

    return re.findall(r"[A-Za-z_]+", query.upper())


def validate_sql(query: str) -> None:
    """Validate *query* to ensure it is safe to execute.

    The function raises :class:`SQLSecurityError` if the query contains
    disallowed characters, comments, statement separators or any of the
    blacklisted keywords defined in :data:`BLACKLIST_KEYWORDS`.
    """

    if not isinstance(query, str):
        raise SQLSecurityError("SQL query must be a string")

    if ";" in query:
        raise SQLSecurityError("Символ ';' запрещён")
    if "--" in query or "/*" in query or "*/" in query:
        raise SQLSecurityError("Комментарии запрещены")

    if not _ALLOWED_CHARS_RE.fullmatch(query):
        raise SQLSecurityError("Обнаружены недопустимые символы")

    tokens = _tokenize(query)
    for token in tokens:
        if token in BLACKLIST_KEYWORDS:
            raise SQLSecurityError(f"Токен '{token}' запрещён")
