from __future__ import annotations

import argparse
from pathlib import Path
import urllib.request

from ._paths import plantuml_jar_path

DEFAULT_PLANTUML_URL = "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"


def download_plantuml_jar(target_path: Path, url: str, force: bool) -> None:
    if target_path.exists() and not force:
        print(f"PlantUML jar already exists: {target_path}")
        print("Use --force to re-download.")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Downloading PlantUML jar from {url}")
    urllib.request.urlretrieve(url, target_path)
    print(f"Saved: {target_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="md2pdf-bootstrap",
        description="Download PlantUML jar for md2pdf",
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
    args = parser.parse_args()

    jar_path = plantuml_jar_path()
    download_plantuml_jar(jar_path, args.plantuml_url, args.force)

    print("\nNext steps:")
    print("  python -m playwright install chromium")
