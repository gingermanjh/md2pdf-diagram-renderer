from pathlib import Path

import pytest
from typer.testing import CliRunner

from md2pdf_cli import RenderResult
from md2pdf_cli.cli import app
from md2pdf_cli.errors import (
    DependencyError,
    DiagramRenderError,
    ExitCode,
    PdfRenderError,
)

runner = CliRunner()


def test_missing_file_returns_input_error(tmp_path: Path) -> None:
    result = runner.invoke(
        app, [str(tmp_path / "missing.md"), "-o", str(tmp_path / "out.pdf")]
    )
    assert result.exit_code == int(ExitCode.INPUT_PARSE_ERROR)


def test_maps_dependency_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    src = tmp_path / "doc.md"
    src.write_text("# x\n", encoding="utf-8")

    def _raise(*_args, **_kwargs):
        raise DependencyError(["node missing"])

    monkeypatch.setattr("md2pdf_cli.cli.render_markdown_to_pdf", _raise)

    result = runner.invoke(app, [str(src), "-o", str(tmp_path / "out.pdf")])
    assert result.exit_code == int(ExitCode.DEPENDENCY_ERROR)


def test_maps_diagram_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    src = tmp_path / "doc.md"
    src.write_text("# x\n", encoding="utf-8")

    def _raise(*_args, **_kwargs):
        raise DiagramRenderError(
            kind="mermaid",
            index=0,
            source_line=3,
            command="npx ...",
            stderr="parse error",
        )

    monkeypatch.setattr("md2pdf_cli.cli.render_markdown_to_pdf", _raise)

    result = runner.invoke(app, [str(src), "-o", str(tmp_path / "out.pdf")])
    assert result.exit_code == int(ExitCode.DIAGRAM_RENDER_ERROR)


def test_maps_pdf_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    src = tmp_path / "doc.md"
    src.write_text("# x\n", encoding="utf-8")

    def _raise(*_args, **_kwargs):
        raise PdfRenderError("playwright failure")

    monkeypatch.setattr("md2pdf_cli.cli.render_markdown_to_pdf", _raise)

    result = runner.invoke(app, [str(src), "-o", str(tmp_path / "out.pdf")])
    assert result.exit_code == int(ExitCode.PDF_RENDER_ERROR)


def test_returns_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    src = tmp_path / "doc.md"
    out = tmp_path / "out.pdf"
    src.write_text("# x\n", encoding="utf-8")

    def _ok(*_args, **_kwargs):
        return RenderResult(output_path=out, rendered_diagram_count=1, elapsed_ms=10)

    monkeypatch.setattr("md2pdf_cli.cli.render_markdown_to_pdf", _ok)

    result = runner.invoke(app, [str(src), "-o", str(out)])
    assert result.exit_code == int(ExitCode.SUCCESS)


def test_invalid_margin_returns_input_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    src = tmp_path / "doc.md"
    src.write_text("# x\n", encoding="utf-8")

    result = runner.invoke(
        app,
        [str(src), "-o", str(tmp_path / "out.pdf"), "--margin-top", "bad-margin"],
    )
    assert result.exit_code == int(ExitCode.INPUT_PARSE_ERROR)


def test_default_output_uses_input_stem(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    src = tmp_path / "document.md"
    src.write_text("# x\n", encoding="utf-8")

    def _ok(*_args, **kwargs):
        return RenderResult(
            output_path=kwargs.get("output_path", tmp_path / "document.pdf"),
            rendered_diagram_count=0,
            elapsed_ms=5,
        )

    monkeypatch.setattr("md2pdf_cli.cli.render_markdown_to_pdf", _ok)

    result = runner.invoke(app, [str(src)])
    assert result.exit_code == int(ExitCode.SUCCESS)


def test_help_exits_zero() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "input_md" in result.output.lower()