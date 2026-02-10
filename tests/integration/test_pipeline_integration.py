from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

from md2pdf_cli.cli import main
from md2pdf_cli.errors import ExitCode

pytestmark = pytest.mark.integration


RUN_INTEGRATION = os.getenv("RUN_MD2PDF_INTEGRATION") == "1"


def _integration_ready() -> tuple[bool, str]:
    if not RUN_INTEGRATION:
        return False, "Set RUN_MD2PDF_INTEGRATION=1 to run integration tests"

    required_bins = ["node", "npx", "java"]
    missing_bins = [name for name in required_bins if shutil.which(name) is None]
    if missing_bins:
        return False, f"Missing command(s): {', '.join(missing_bins)}"

    repo_root = Path(__file__).resolve().parents[2]
    if not (repo_root / ".tools" / "plantuml.jar").exists():
        return False, "Missing .tools/plantuml.jar"

    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            browser.close()
    except Exception as exc:  # pragma: no cover - env specific
        return False, f"Playwright chromium unavailable: {exc}"

    return True, ""


_READY, _REASON = _integration_ready()


@pytest.mark.skipif(not _READY, reason=_REASON)
def test_mermaid_only_to_pdf(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[1] / "fixtures" / "mermaid.md"
    out = tmp_path / "mermaid.pdf"

    code = main([str(src), "-o", str(out)])

    assert code == int(ExitCode.SUCCESS)
    assert out.exists()
    assert out.stat().st_size > 0


@pytest.mark.skipif(not _READY, reason=_REASON)
def test_plantuml_only_to_pdf(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[1] / "fixtures" / "plantuml.md"
    out = tmp_path / "plantuml.pdf"

    code = main([str(src), "-o", str(out)])

    assert code == int(ExitCode.SUCCESS)
    assert out.exists()


@pytest.mark.skipif(not _READY, reason=_REASON)
def test_mixed_diagrams_to_pdf(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[1] / "fixtures" / "mixed.md"
    out = tmp_path / "mixed.pdf"

    code = main([str(src), "-o", str(out)])

    assert code == int(ExitCode.SUCCESS)
    assert out.exists()


@pytest.mark.skipif(not _READY, reason=_REASON)
def test_invalid_mermaid_returns_diagram_error(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[1] / "fixtures" / "invalid_mermaid.md"
    out = tmp_path / "invalid.pdf"

    code = main([str(src), "-o", str(out)])

    assert code == int(ExitCode.DIAGRAM_RENDER_ERROR)
    assert not out.exists()


@pytest.mark.skipif(not _READY, reason=_REASON)
def test_utf8_korean_document(tmp_path: Path) -> None:
    src = Path(__file__).resolve().parents[1] / "fixtures" / "utf8_korean.md"
    out = tmp_path / "utf8.pdf"

    code = main([str(src), "-o", str(out)])

    assert code == int(ExitCode.SUCCESS)
    assert out.exists()
