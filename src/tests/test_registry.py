from pathlib import Path

from core.module_api import BaseModule
from core.registry import autodiscover_modules, registry


class DummyModule(BaseModule):
    id = "dummy"
    title = "Dummy"


def test_register_and_get():
    registry._modules.clear()
    module = DummyModule()
    registry.register(module)
    assert registry.get("dummy") is module
    assert module in registry.all()


def test_autodiscover(tmp_path):
    registry._modules.clear()
    modules_dir = Path("src/modules/testmod")
    modules_dir.mkdir(parents=True, exist_ok=True)
    (modules_dir / "__init__.py").write_text("")
    (modules_dir / "module.py").write_text(
        "from core.module_api import BaseModule\n"
        "from core.registry import registry\n"
        "class TestModule(BaseModule):\n"
        "    id='test'\n"
        "module=TestModule()\n"
        "registry.register(module)\n"
    )

    try:
        autodiscover_modules()
        assert registry.get("test") is not None
    finally:
        for file in modules_dir.glob("**/*"):
            if file.is_file():
                file.unlink()
        for directory in sorted(modules_dir.glob("**"), reverse=True):
            if directory.is_dir():
                directory.rmdir()
        registry._modules.clear()
