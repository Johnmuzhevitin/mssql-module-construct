from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2] / "src"))

from core.module_api import BaseModule


class DummyModule(BaseModule):
    id = "dummy"
    title = "Dummy"
    icon = ""


def test_mount_unmount_no_errors():
    module = DummyModule()
    module.mount(None, None, None)
    module.unmount()


def test_default_widget_methods():
    module = DummyModule()
    assert module.get_sidebar_items() == []
    assert module.get_properties_widget(None) is None
    assert module.get_preview_widget(None) is None
