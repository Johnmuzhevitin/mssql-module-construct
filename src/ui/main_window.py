from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QListWidget,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QTextEdit,
    QWidget,
)

from qt_material import apply_stylesheet


class MainWindow(QMainWindow):
    """Main application window with basic layout and theme switching."""

    def __init__(self, config) -> None:
        super().__init__()
        self.config = config
        self.setWindowTitle(config.app_name)

        self.settings = QSettings("mssql-module-construct", "main_window")

        self._create_widgets()
        self._create_actions()
        self._create_menu()
        self._load_settings()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _create_widgets(self) -> None:
        """Create main layout with splitters."""

        self.nav_list = QListWidget()
        self.nav_list.addItem("Навигация")

        self.canvas = QLabel("Canvas")
        self.canvas.setAlignment(Qt.AlignCenter)

        self.props_panel = QTextEdit()
        self.props_panel.setPlainText("Свойства")

        self.preview = QTextEdit()
        self.preview.setPlainText("Превью")

        self.h_splitter = QSplitter(Qt.Horizontal)
        self.h_splitter.addWidget(self.nav_list)
        self.h_splitter.addWidget(self.canvas)
        self.h_splitter.addWidget(self.props_panel)
        self.h_splitter.setSizes([150, 400, 200])

        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.addWidget(self.h_splitter)
        self.v_splitter.addWidget(self.preview)
        self.v_splitter.setSizes([450, 150])

        self.setCentralWidget(self.v_splitter)

    def _create_actions(self) -> None:
        """Create actions and shortcuts."""

        self.new_action = QAction("Новый", self)
        self.new_action.setShortcut("Ctrl+N")
        self.new_action.triggered.connect(self._new_project)

        self.save_action = QAction("Сохранить", self)
        self.save_action.setShortcut("Ctrl+S")

        self.undo_action = QAction("Отменить", self)
        self.undo_action.setShortcut("Ctrl+Z")

        self.redo_action = QAction("Повторить", self)
        self.redo_action.setShortcut("Ctrl+Y")

        self.run_action = QAction("Запустить", self)
        self.run_action.setShortcut("F5")

        self.dark_theme_action = QAction("Тёмная тема", self, checkable=True)
        self.dark_theme_action.triggered.connect(self._toggle_theme)

    def _create_menu(self) -> None:
        """Populate menu bar with actions."""

        menu_bar = QMenuBar(self)
        self.setMenuBar(menu_bar)

        file_menu = menu_bar.addMenu("Файл")
        file_menu.addAction(self.new_action)
        file_menu.addAction(self.save_action)

        edit_menu = menu_bar.addMenu("Правка")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)

        view_menu = menu_bar.addMenu("Вид")
        view_menu.addAction(self.run_action)
        view_menu.addSeparator()
        view_menu.addAction(self.dark_theme_action)

    # ------------------------------------------------------------------
    # Project management
    # ------------------------------------------------------------------
    def _new_project(self) -> None:
        """Initialize a new project by clearing UI elements."""

        reply = QMessageBox.question(
            self,
            "Новый проект",
            "Очистить текущий проект?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.nav_list.clear()
        self.nav_list.addItem("Навигация")

        self.canvas.setText("Canvas")

        self.props_panel.clear()
        self.props_panel.setPlainText("Свойства")

        self.preview.clear()
        self.preview.setPlainText("Превью")

    # ------------------------------------------------------------------
    # Theme management
    # ------------------------------------------------------------------
    def _apply_theme(self) -> None:
        theme = "dark_teal_500" if self.dark_theme_action.isChecked() else "light_teal_500"
        apply_stylesheet(QApplication.instance(), theme=theme)

    def _toggle_theme(self, checked: bool) -> None:  # noqa: ARG002
        self._apply_theme()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------
    def _load_settings(self) -> None:
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("window_state"):
            self.restoreState(self.settings.value("window_state"))
        if self.settings.contains("h_splitter"):
            self.h_splitter.restoreState(self.settings.value("h_splitter"))
        if self.settings.contains("v_splitter"):
            self.v_splitter.restoreState(self.settings.value("v_splitter"))
        dark = self.settings.value("theme", "light") == "dark"
        self.dark_theme_action.setChecked(dark)
        self._apply_theme()

    def _save_settings(self) -> None:
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())
        self.settings.setValue("h_splitter", self.h_splitter.saveState())
        self.settings.setValue("v_splitter", self.v_splitter.saveState())
        theme = "dark" if self.dark_theme_action.isChecked() else "light"
        self.settings.setValue("theme", theme)

    def closeEvent(self, event) -> None:  # noqa: N802
        self._save_settings()
        super().closeEvent(event)
