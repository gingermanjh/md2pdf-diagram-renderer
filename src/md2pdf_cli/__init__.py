from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import time

from .config import RenderConfig, RenderResult
from .diagram_renderers import (
    check_common_dependencies,
    check_mermaid_dependencies,
    check_plantuml_dependencies,
    render_diagram_fragments,
)
from .errors import InputParseError
from .html_builder import build_html_document
from .parser import DiagramBlock, parse_markdown, placeholder_for


__all__ = [
    "DiagramBlock",
    "RenderConfig",
    "RenderResult",
    "render_markdown_to_pdf",
]


def render_markdown_to_pdf(
    input_path: Path,
    output_path: Path,
    config: RenderConfig,
) -> RenderResult:
    start = time.perf_counter()

    try:
        markdown_text = input_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise InputParseError(f"Input file not found: {input_path}") from exc
    except UnicodeDecodeError as exc:
        raise InputParseError(
            f"Input file is not valid UTF-8: {input_path}"
        ) from exc
    except OSError as exc:
        raise InputParseError(f"Failed to read input file: {exc}") from exc

    parsed = parse_markdown(markdown_text)

    has_mermaid = any(b.kind == "mermaid" for b in parsed.diagram_blocks)
    has_plantuml = any(b.kind == "plantuml" for b in parsed.diagram_blocks)

    check_common_dependencies()
    if has_mermaid:
        check_mermaid_dependencies()
    plantuml_jar: Path | None = None
    if has_plantuml:
        plantuml_jar = check_plantuml_dependencies()

    temp_dir = Path(tempfile.mkdtemp(prefix="md2pdf-"))
    try:
        rendered_fragments = render_diagram_fragments(
            parsed.diagram_blocks,
            temp_dir=temp_dir,
            plantuml_jar=plantuml_jar,
            config=config,
        )

        body_html = parsed.html_body
        for index, fragment in rendered_fragments.items():
            body_html = body_html.replace(placeholder_for(index), fragment)

        if "MD2PDF_DIAGRAM_PLACEHOLDER_" in body_html:
            raise InputParseError(
                "Internal placeholder replacement failed while assembling HTML."
            )

        document_html = build_html_document(
            body_html=body_html,
            title=input_path.stem,
        )

        # Lazy import keeps CLI usable even when Playwright is not installed.
        from .pdf_renderer import render_pdf_from_html

        render_pdf_from_html(html=document_html, output_path=output_path, config=config)
    finally:
        if not config.keep_temp:
            shutil.rmtree(temp_dir, ignore_errors=True)

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return RenderResult(
        output_path=output_path,
        rendered_diagram_count=len(parsed.diagram_blocks),
        elapsed_ms=elapsed_ms,
    )
