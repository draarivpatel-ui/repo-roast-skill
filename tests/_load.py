"""Load helper scripts from skill folders (which have hyphens, so they are not packages)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(skill: str, script: str):
    """Import skills/<skill>/<script>.py as a module named <script>_under_test."""
    path = ROOT / "skills" / skill / f"{script}.py"
    name = f"{script}_under_test"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module
