from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class CheckStatus(Enum):
    """Possible result statuses for environment checks."""

    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True)
class CheckResult:
    """Represents a single environment check outcome."""

    name: str
    status: CheckStatus
    message: str


def _run_odbcinst(args: Iterable[str]) -> subprocess.CompletedProcess[str]:
    """Run `odbcinst` with given arguments."""

    return subprocess.run(
        ["odbcinst", *args],
        check=True,
        capture_output=True,
        text=True,
    )


def check_odbc_driver() -> CheckResult:
    """Verify that MS ODBC Driver 17 or 18 for SQL Server is installed."""

    name = "MS ODBC драйвер"
    try:
        proc = _run_odbcinst(["-q", "-d"])
    except FileNotFoundError:
        return CheckResult(name, CheckStatus.ERROR, "Команда odbcinst не найдена")
    except subprocess.CalledProcessError:
        return CheckResult(name, CheckStatus.ERROR, "Не удалось выполнить проверку драйвера")

    drivers = proc.stdout.lower()
    if "odbc driver 18 for sql server" in drivers or "odbc driver 17 for sql server" in drivers:
        return CheckResult(name, CheckStatus.OK, "Драйвер найден")
    return CheckResult(name, CheckStatus.ERROR, "Драйвер MS ODBC 17/18 не найден")


def check_directory_writable(path: Path) -> CheckResult:
    """Check that directory exists and is writable."""

    name = f"Права на запись: {path}"
    try:
        path.mkdir(parents=True, exist_ok=True)
        test_file = path / ".write_test"
        with open(test_file, "w", encoding="utf-8") as fh:
            fh.write("test")
        test_file.unlink(missing_ok=True)
        return CheckResult(name, CheckStatus.OK, "Доступно")
    except Exception:  # noqa: BLE001
        return CheckResult(name, CheckStatus.ERROR, "Нет прав на запись")


def check_python_version(min_version: tuple[int, int] = (3, 10)) -> CheckResult:
    """Check that current Python version is supported."""

    name = "Версия Python"
    current = sys.version_info
    version_str = f"{current.major}.{current.minor}.{current.micro}"
    if (current.major, current.minor) >= min_version:
        return CheckResult(name, CheckStatus.OK, version_str)
    required = f">= {min_version[0]}.{min_version[1]}"
    return CheckResult(name, CheckStatus.ERROR, f"{version_str} (требуется {required})")


def run_checks() -> list[CheckResult]:
    """Run all environment checks and return their results."""

    base_dir = Path(__file__).resolve().parents[3]
    checks = [
        check_odbc_driver(),
        check_directory_writable(base_dir / "data"),
        check_directory_writable(base_dir / "logs"),
        check_python_version(),
    ]
    return checks
