from __future__ import annotations

from pathlib import Path
from typing import Annotated, Optional

import typer

from . import RenderConfig, render_markdown_to_pdf
from .errors import ExitCode, InputParseError, Md2PdfError
from .logging_utils import configure_logging

app = typer.Typer(
    name="md2pdf",
    help="Render Markdown with mermaid/plantuml/ascii fenced blocks to a PDF file.",
    add_completion=False,
)


@app.command()
def main(
    input_md: Annotated[Path, typer.Argument(help="Path to input Markdown file")],
    output: Annotated[
        Optional[Path],
        typer.Option("-o", "--output", help="Output PDF path"),
    ] = None,
    page_size: Annotated[
        str,
        typer.Option(help="PDF page size"),
    ] = "Letter",
    margin_top: Annotated[str, typer.Option(help="Top page margin")] = "0.5in",
    margin_right: Annotated[str, typer.Option(help="Right page margin")] = "0.5in",
    margin_bottom: Annotated[str, typer.Option(help="Bottom page margin")] = "0.5in",
    margin_left: Annotated[str, typer.Option(help="Left page margin")] = "0.5in",
    timeout_seconds: Annotated[
        int,
        typer.Option(help="Per-step timeout in seconds"),
    ] = 60,
    keep_temp: Annotated[
        bool,
        typer.Option("--keep-temp", help="Keep temporary render artifacts"),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", help="Enable verbose logging"),
    ] = False,
) -> None:
    logger = configure_logging(verbose)

    try:
        input_path = input_md.expanduser().resolve()

        if output is not None:
            output_path = output.expanduser().resolve()
        else:
            output_path = input_path.with_suffix(".pdf")

        if not input_path.exists() or not input_path.is_file():
            raise InputParseError(f"Input Markdown file not found: {input_path}")

        config = RenderConfig(
            page_size=page_size,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            timeout_seconds=timeout_seconds,
            keep_temp=keep_temp,
            verbose=verbose,
        )

        result = render_markdown_to_pdf(
            input_path=input_path,
            output_path=output_path,
            config=config,
        )
        logger.info(
            "Rendered %s (%d diagrams, %dms)",
            result.output_path,
            result.rendered_diagram_count,
            result.elapsed_ms,
        )
        raise typer.Exit(code=int(ExitCode.SUCCESS))

    except Md2PdfError as exc:
        logger.error(str(exc))
        raise typer.Exit(code=int(exc.exit_code)) from exc
    except ValueError as exc:
        logger.error(str(exc))
        raise typer.Exit(code=int(ExitCode.INPUT_PARSE_ERROR)) from exc
    except typer.Exit:
        raise
    except Exception as exc:  # pragma: no cover - unexpected failures
        logger.exception("Unexpected error: %s", exc)
        raise typer.Exit(code=int(ExitCode.UNEXPECTED_ERROR)) from exc
