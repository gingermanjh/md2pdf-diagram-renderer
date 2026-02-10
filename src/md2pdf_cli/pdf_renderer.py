from __future__ import annotations

from pathlib import Path

from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from .config import RenderConfig
from .errors import PdfRenderError


def render_pdf_from_html(*, html: str, output_path: Path, config: RenderConfig) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                page.set_default_timeout(config.timeout_seconds * 1000)
                page.set_content(html, wait_until="networkidle")
                page.emulate_media(media="screen")
                page.pdf(
                    path=str(output_path),
                    format=config.page_size,
                    print_background=True,
                    margin={
                        "top": config.margin_top,
                        "right": config.margin_right,
                        "bottom": config.margin_bottom,
                        "left": config.margin_left,
                    },
                )
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise PdfRenderError(f"Failed to render PDF via Playwright: {exc}") from exc
