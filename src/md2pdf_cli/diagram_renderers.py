from __future__ import annotations

from html import escape
from pathlib import Path
import shutil
import subprocess

from ._paths import plantuml_jar_path
from .config import RenderConfig
from .errors import DependencyError, DiagramRenderError
from .parser import DiagramBlock


def check_common_dependencies() -> None:
    messages: list[str] = []

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        messages.append(
            "Python dependency `playwright` is missing. Run `pip install playwright`."
        )
    else:
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                browser.close()
        except Exception:
            messages.append(
                "Playwright Chromium is not available. "
                "Run `python -m playwright install chromium`."
            )

    if messages:
        raise DependencyError(messages)


def check_mermaid_dependencies() -> None:
    messages: list[str] = []

    if shutil.which("node") is None:
        messages.append("`node` is missing. Install Node.js 18+.")

    if shutil.which("npx") is None:
        messages.append("`npx` is missing. Install npm (npx is bundled with npm).")

    if messages:
        raise DependencyError(messages)


def check_plantuml_dependencies(jar: Path | None = None) -> Path:
    messages: list[str] = []

    if shutil.which("java") is None:
        messages.append("`java` is missing. Install Java 17+.")

    jar = jar or plantuml_jar_path()
    if not jar.exists():
        messages.append(
            f"PlantUML jar not found at {jar}. "
            "Run `md2pdf-bootstrap` to download it."
        )

    if messages:
        raise DependencyError(messages)

    return jar


def check_runtime_dependencies(project_root: Path) -> Path:
    """Backward-compatible wrapper that checks all dependencies at once."""
    check_common_dependencies()
    check_mermaid_dependencies()
    jar = project_root / ".tools" / "plantuml.jar"
    return check_plantuml_dependencies(jar=jar)


def render_diagram_fragments(
    blocks: list[DiagramBlock],
    *,
    temp_dir: Path,
    plantuml_jar: Path | None,
    config: RenderConfig,
) -> dict[int, str]:
    rendered: dict[int, str] = {}

    for block in blocks:
        if block.kind == "ascii":
            rendered[block.index] = render_ascii_block(block)
            continue

        if block.kind == "mermaid":
            svg = _render_mermaid_svg(block=block, temp_dir=temp_dir, timeout=config.timeout_seconds)
            rendered[block.index] = _wrap_svg(svg, css_class="diagram-mermaid")
            continue

        if block.kind == "plantuml":
            if plantuml_jar is None:
                raise DiagramRenderError(
                    kind="plantuml",
                    index=block.index,
                    source_line=block.source_line,
                    command="java -jar plantuml.jar",
                    stderr="PlantUML jar path was not provided.",
                )
            svg = _render_plantuml_svg(
                block=block,
                plantuml_jar=plantuml_jar,
                timeout=config.timeout_seconds,
            )
            rendered[block.index] = _wrap_svg(svg, css_class="diagram-plantuml")
            continue

        raise DiagramRenderError(
            kind=block.kind,
            index=block.index,
            source_line=block.source_line,
            command="unsupported",
            stderr="Unsupported diagram kind",
        )

    return rendered


def render_ascii_block(block: DiagramBlock) -> str:
    content = escape(block.code.rstrip("\n"))
    return f'<pre class="ascii-diagram">{content}</pre>'


def _render_mermaid_svg(*, block: DiagramBlock, temp_dir: Path, timeout: int) -> str:
    input_path = temp_dir / f"diagram-{block.index}.mmd"
    output_path = temp_dir / f"diagram-{block.index}.svg"
    input_path.write_text(block.code, encoding="utf-8")

    command = [
        "npx",
        "--yes",
        "@mermaid-js/mermaid-cli",
        "-i",
        str(input_path),
        "-o",
        str(output_path),
        "-b",
        "transparent",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=timeout,
            cwd=str(temp_dir),
        )
    except subprocess.TimeoutExpired as exc:
        raise DiagramRenderError(
            kind="mermaid",
            index=block.index,
            source_line=block.source_line,
            command=" ".join(command),
            stderr=f"Timed out after {timeout} seconds",
        ) from exc

    if result.returncode != 0:
        raise DiagramRenderError(
            kind="mermaid",
            index=block.index,
            source_line=block.source_line,
            command=" ".join(command),
            stderr=result.stderr or result.stdout,
        )

    if not output_path.exists():
        raise DiagramRenderError(
            kind="mermaid",
            index=block.index,
            source_line=block.source_line,
            command=" ".join(command),
            stderr="Mermaid CLI did not produce an SVG file.",
        )

    svg = output_path.read_text(encoding="utf-8")
    if "<svg" not in svg or "</svg>" not in svg:
        raise DiagramRenderError(
            kind="mermaid",
            index=block.index,
            source_line=block.source_line,
            command=" ".join(command),
            stderr="Mermaid output is not a valid SVG payload.",
        )

    return svg


def _render_plantuml_svg(*, block: DiagramBlock, plantuml_jar: Path, timeout: int) -> str:
    command = [
        "java",
        "-jar",
        str(plantuml_jar),
        "-tsvg",
        "-pipe",
        "-charset",
        "UTF-8",
    ]

    try:
        result = subprocess.run(
            command,
            input=block.code,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        raise DiagramRenderError(
            kind="plantuml",
            index=block.index,
            source_line=block.source_line,
            command=" ".join(command),
            stderr=f"Timed out after {timeout} seconds",
        ) from exc

    if result.returncode != 0:
        raise DiagramRenderError(
            kind="plantuml",
            index=block.index,
            source_line=block.source_line,
            command=" ".join(command),
            stderr=result.stderr or result.stdout,
        )

    svg = result.stdout
    if "<svg" not in svg or "</svg>" not in svg:
        raise DiagramRenderError(
            kind="plantuml",
            index=block.index,
            source_line=block.source_line,
            command=" ".join(command),
            stderr=result.stderr or "PlantUML output is not SVG.",
        )

    return svg


def _wrap_svg(svg: str, *, css_class: str) -> str:
    return f'<figure class="diagram {css_class}">{svg}</figure>'
