from __future__ import annotations

import argparse
from pathlib import Path
import urllib.request

DEFAULT_PLANTUML_URL = "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"


def _default_jar_path() -> Path:
    import platform
    import os

    if platform.system() == "Windows":
        base = Path.home() / "AppData" / "Local"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))
    return base / "md2pdf" / "plantuml.jar"


def download_plantuml_jar(target_path: Path, url: str, force: bool) -> None:
    if target_path.exists() and not force:
        print(f"PlantUML jar already exists: {target_path}")
        print("Use --force to re-download.")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading PlantUML jar from {url}")
    urllib.request.urlretrieve(url, target_path)
    print(f"Saved: {target_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bootstrap external tools used by md2pdf"
    )
    parser.add_argument(
        "--plantuml-url",
        default=DEFAULT_PLANTUML_URL,
        help="PlantUML jar URL",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download files even if they already exist",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    jar_path = _default_jar_path()
    download_plantuml_jar(jar_path, args.plantuml_url, args.force)

    print("\nNext steps:")
    print("  python -m playwright install chromium")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())