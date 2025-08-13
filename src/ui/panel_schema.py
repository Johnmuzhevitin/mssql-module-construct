from __future__ import annotations

from PySide6.QtWidgets import (
    QMessageBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..modules.schema import SchemaCache

try:
    import pyodbc
except ImportError:  # pragma: no cover - used only when MSSQL available
    pyodbc = None  # type: ignore


class SchemaPanel(QWidget):
    """Left panel widget displaying cached schema information."""

    def __init__(self, cache: SchemaCache, parent=None) -> None:
        super().__init__(parent)
        self.cache = cache
        self.connection: pyodbc.Connection | None = None
        self.cache_name: str | None = None

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Объект", "Тип"])

        self.refresh_button = QPushButton("Обновить схему")
        self.refresh_button.clicked.connect(self._refresh)

        layout = QVBoxLayout(self)
        layout.addWidget(self.tree)
        layout.addWidget(self.refresh_button)

    # ------------------------------------------------------------------
    def set_connection(self, name: str, conn: pyodbc.Connection) -> None:
        """Attach active database connection used for refresh."""

        self.cache_name = name
        self.connection = conn
        cached = self.cache.get(name)
        if cached:
            self._populate_tree(cached)

    # ------------------------------------------------------------------
    def _refresh(self) -> None:
        if not self.connection or not self.cache_name:
            QMessageBox.warning(self, "Нет соединения", "Сначала подключитесь к БД")
            return
        data = self.cache.update(self.cache_name, self.connection)
        self._populate_tree(data)

    # ------------------------------------------------------------------
    def _populate_tree(self, schema_data) -> None:
        self.tree.clear()
        for item in schema_data.get("tables", []):
            t_item = QTreeWidgetItem([item["name"], item["type"]])
            self.tree.addTopLevelItem(t_item)
