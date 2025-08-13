from __future__ import annotations

import time

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from core.crypto import CryptoManager


class MasterKeyDialog(QDialog):
    """Dialog for entering or setting the master password.

    Users have three attempts to enter the correct password. After the third
    failed attempt the dialog locks for five minutes.
    """

    def __init__(self, crypto: CryptoManager, parent=None) -> None:
        super().__init__(parent)
        self.crypto = crypto
        self.setWindowTitle("Мастер-пароль")
        self.attempts = 0
        self.lock_until: float | None = None

        self.label = QLabel()
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)

        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        layout.addWidget(self.password_edit)

        self.confirm_edit: QLineEdit | None = None
        if not self.crypto.is_configured():
            self.label.setText("Задайте мастер-пароль")
            self.confirm_edit = QLineEdit()
            self.confirm_edit.setEchoMode(QLineEdit.Password)
            self.confirm_edit.setPlaceholderText("Повторите пароль")
            layout.addWidget(self.confirm_edit)
        else:
            self.label.setText("Введите мастер-пароль")

        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttons.accepted.connect(self._handle_accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _handle_accept(self) -> None:
        if self.lock_until and time.time() < self.lock_until:
            QMessageBox.warning(self, "Блокировка", "Повторите попытку позже.")
            return

        password = self.password_edit.text()
        if not self.crypto.is_configured():
            assert self.confirm_edit is not None  # for type checkers
            if not password or password != self.confirm_edit.text():
                QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
                return
            self.crypto.set_master_password(password)
            self.accept()
            return

        if not self.crypto.verify_master_password(password):
            self.attempts += 1
            QMessageBox.warning(self, "Ошибка", "Неверный пароль.")
            if self.attempts >= 3:
                self.lock_until = time.time() + 300
                self.password_edit.setEnabled(False)
                QTimer.singleShot(300_000, self._unlock)
            return

        self.accept()

    def _unlock(self) -> None:
        self.attempts = 0
        self.lock_until = None
        self.password_edit.setEnabled(True)
