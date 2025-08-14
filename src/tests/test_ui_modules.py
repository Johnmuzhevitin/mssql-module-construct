from __future__ import annotations

import os
import sys
from types import SimpleNamespace
from pathlib import Path

from PySide6.QtWidgets import QApplication, QLabel

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.core.events import EventBus
from src.core.registry import registry
from src.core.module_api import BaseModule
from src.ui.main_window import MainWindow


class DummyModule(BaseModule):
    def __init__(self, mid: str, title: str, prop: str, prev: str) -> None:
        self.id = mid
        self.title = title
        self.icon = ""
        self.prop = prop
        self.prev = prev
        self.mounted = False
        self.unmounted = False

    def mount(self, ui, app, bus) -> None:  # noqa: D401, ANN001
        layout = ui.layout()
        layout.addWidget(QLabel(self.title))
        self.mounted = True

    def unmount(self) -> None:  # noqa: D401
        self.unmounted = True

    def get_properties_widget(self, ui):  # noqa: D401, ANN001
        return QLabel(self.prop)

    def get_preview_widget(self, ui):  # noqa: D401, ANN001
        return QLabel(self.prev)


def test_switching_modules_updates_ui():
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication([])
    bus = EventBus()

    registry._modules.clear()
    m1 = DummyModule("m1", "Module 1", "Props1", "Prev1")
    m2 = DummyModule("m2", "Module 2", "Props2", "Prev2")
    registry.register(m1)
    registry.register(m2)

    config = SimpleNamespace(app_name="test")
    window = MainWindow(config, bus)

    assert window.nav_list.count() == 2

    window.nav_list.setCurrentRow(0)
    assert window.active_module is m1
    assert window.canvas_layout.itemAt(0).widget().text() == "Module 1"
    assert window.props_layout.itemAt(0).widget().text() == "Props1"
    assert window.preview_layout.itemAt(0).widget().text() == "Prev1"

    window.nav_list.setCurrentRow(1)
    assert m1.unmounted
    assert window.active_module is m2
    assert window.canvas_layout.itemAt(0).widget().text() == "Module 2"
    assert window.props_layout.itemAt(0).widget().text() == "Props2"
    assert window.preview_layout.itemAt(0).widget().text() == "Prev2"

    app.quit()
