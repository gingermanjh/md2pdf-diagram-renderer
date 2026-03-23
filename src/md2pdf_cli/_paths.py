from __future__ import annotations

import os
import platform
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent


def package_dir() -> Path:
    return _PACKAGE_DIR


def data_dir() -> Path:
    """~/.local/share/md2pdf on Linux/macOS, ~/AppData/Local/md2pdf on Windows."""
    if platform.system() == "Windows":
        base = Path.home() / "AppData" / "Local"
    else:
        base = Path(
            os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
        )
    return base / "md2pdf"


def plantuml_jar_path() -> Path:
    return data_dir() / "plantuml.jar"


def template_dir() -> Path:
    return _PACKAGE_DIR / "templates"


def css_path() -> Path:
    return _PACKAGE_DIR / "assets" / "default.css"
