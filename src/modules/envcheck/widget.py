from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .checks import CheckResult, CheckStatus, run_checks


class EnvCheckWidget(QWidget):
    """Widget displaying environment check results."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._create_ui()
        self.run_checks()

    # ------------------------------------------------------------------
    # UI creation
    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        self.layout = QVBoxLayout(self)
        self.status_labels: Dict[str, QLabel] = {}

        items = {
            "odbc": "ODBC драйвер",
            "data": "Каталог data",
            "logs": "Каталог logs",
            "python": "Версия Python",
        }

        for key, title in items.items():
            label = QLabel(f"{title}: ...")
            self.layout.addWidget(label)
            self.status_labels[key] = label

        btn_layout = QHBoxLayout()
        self.repeat_btn = QPushButton("Повторить проверку")
        self.continue_btn = QPushButton("Продолжить")
        self.continue_btn.setEnabled(False)
        btn_layout.addWidget(self.repeat_btn)
        btn_layout.addWidget(self.continue_btn)
        self.layout.addLayout(btn_layout)

        self.repeat_btn.clicked.connect(self.run_checks)

    # ------------------------------------------------------------------
    # Checks
    # ------------------------------------------------------------------
    def run_checks(self) -> None:
        """Execute all checks and update UI."""

        results = run_checks()
        mapping = {
            "odbc": results[0],
            "data": results[1],
            "logs": results[2],
            "python": results[3],
        }

        all_ok = True
        for key, result in mapping.items():
            self._apply_result(key, result)
            if result.status is not CheckStatus.OK:
                all_ok = False

        self.continue_btn.setEnabled(all_ok)

    def _apply_result(self, key: str, result: CheckResult) -> None:
        label = self.status_labels[key]
        label.setText(f"{label.text().split(':')[0]}: {result.message}")
        color = {
            CheckStatus.OK: "green",
            CheckStatus.WARNING: "orange",
            CheckStatus.ERROR: "red",
        }[result.status]
        label.setStyleSheet(f"color: {color}")
