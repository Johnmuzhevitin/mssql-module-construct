from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QSpinBox,
)

from ..modules.datasource import ConnectionManager, ConnectionProfile


class ConnectionDialog(QDialog):
    """Dialog for creating or editing a connection profile."""

    def __init__(
        self,
        manager: ConnectionManager,
        profile: ConnectionProfile | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.manager = manager
        self.profile = profile
        self.setWindowTitle("Профиль подключения")

        layout = QFormLayout(self)

        self.name_edit = QLineEdit()
        self.server_edit = QLineEdit()
        self.db_edit = QLineEdit()
        self.auth_combo = QComboBox()
        self.auth_combo.addItems(["sql", "windows"])
        self.user_edit = QLineEdit()
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.Password)
        self.conn_timeout = QSpinBox()
        self.conn_timeout.setRange(1, 60)
        self.conn_timeout.setValue(5)
        self.query_timeout = QSpinBox()
        self.query_timeout.setRange(1, 600)
        self.query_timeout.setValue(30)

        layout.addRow("Имя", self.name_edit)
        layout.addRow("Сервер", self.server_edit)
        layout.addRow("База", self.db_edit)
        layout.addRow("Аутентификация", self.auth_combo)
        layout.addRow("Логин", self.user_edit)
        layout.addRow("Пароль", self.pass_edit)
        layout.addRow("Таймаут соединения", self.conn_timeout)
        layout.addRow("Таймаут запроса", self.query_timeout)

        self.buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.test_button = self.buttons.addButton("Тест", QDialogButtonBox.ActionRole)
        self.buttons.accepted.connect(self._save)
        self.buttons.rejected.connect(self.reject)
        self.test_button.clicked.connect(self._test_connection)
        layout.addRow(self.buttons)

        if profile:
            self._load_profile(profile)

    # ------------------------------------------------------------------
    def _load_profile(self, profile: ConnectionProfile) -> None:
        self.name_edit.setText(profile.name)
        self.server_edit.setText(profile.server)
        self.db_edit.setText(profile.database)
        self.auth_combo.setCurrentText(profile.auth)
        if profile.username:
            self.user_edit.setText(profile.username)
        if profile.password:
            self.pass_edit.setText(profile.password)
        self.conn_timeout.setValue(profile.connect_timeout)
        self.query_timeout.setValue(profile.query_timeout)

    def _gather_profile(self) -> ConnectionProfile:
        data = dict(
            id=self.profile.id if self.profile else None,
            name=self.name_edit.text(),
            server=self.server_edit.text(),
            database=self.db_edit.text(),
            auth=self.auth_combo.currentText(),
            username=self.user_edit.text() or None,
            password=self.pass_edit.text() or None,
            connect_timeout=self.conn_timeout.value(),
            query_timeout=self.query_timeout.value(),
        )
        return ConnectionProfile(**data)

    def _save(self) -> None:
        profile = self._gather_profile()
        if profile.id:
            self.manager.update(profile)
        else:
            self.manager.create(profile)
        self.accept()

    def _test_connection(self) -> None:
        profile = self._gather_profile()
        ok, error = self.manager.test_connection(profile)
        if ok:
            QMessageBox.information(self, "Успех", "Соединение установлено")
        else:
            QMessageBox.warning(self, "Ошибка", error or "Не удалось подключиться")
