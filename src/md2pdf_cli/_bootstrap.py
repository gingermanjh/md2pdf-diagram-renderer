from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys
import urllib.request

from ._paths import plantuml_jar_path

DEFAULT_PLANTUML_URL = "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"


def _progress_hook(block_num: int, block_size: int, total_size: int) -> None:
    if total_size > 0:
        downloaded = block_num * block_size
        percent = min(100, downloaded * 100 // total_size)
        bar_len = 40
        filled = bar_len * percent // 100
        bar = "█" * filled + "░" * (bar_len - filled)
        sys.stdout.write(f"\r  [{bar}] {percent}%")
        sys.stdout.flush()
        if percent >= 100:
            sys.stdout.write("\n")
    else:
        downloaded = block_num * block_size
        sys.stdout.write(f"\r  Downloaded {downloaded // 1024} KB...")
        sys.stdout.flush()


def download_plantuml_jar(target_path: Path, url: str, force: bool) -> None:
    if target_path.exists() and not force:
        print(f"PlantUML jar already exists: {target_path}")
        print("Use --force to re-download.")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)

    partial_path = target_path.parent / (target_path.name + ".partial")
    print(f"Downloading PlantUML jar from {url}")
    try:
        urllib.request.urlretrieve(url, partial_path, reporthook=_progress_hook)
        shutil.move(str(partial_path), str(target_path))
    except Exception:
        partial_path.unlink(missing_ok=True)
        raise
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
