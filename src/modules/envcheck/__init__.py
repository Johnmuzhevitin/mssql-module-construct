"""Environment checking utilities and widget."""

from .checks import (
    CheckResult,
    CheckStatus,
    check_directory_writable,
    check_odbc_driver,
    check_python_version,
    run_checks,
)

try:  # pragma: no cover - optional GUI dependency
    from .widget import EnvCheckWidget
except Exception:  # noqa: BLE001
    EnvCheckWidget = None  # type: ignore[assignment]

__all__ = [
    "CheckResult",
    "CheckStatus",
    "check_directory_writable",
    "check_odbc_driver",
    "check_python_version",
    "run_checks",
    "EnvCheckWidget",
]
