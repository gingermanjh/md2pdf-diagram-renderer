"""Edge case tests for diagram rendering, SVG validation, error handling, and logging."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from md2pdf_cli._bootstrap import _progress_hook, download_plantuml_jar
from md2pdf_cli.config import RenderConfig
from md2pdf_cli.diagram_renderers import (
    _render_mermaid_svg,
    _render_plantuml_svg,
    render_diagram_fragments,
)
from md2pdf_cli.errors import (
    DiagramRenderError,
    ExitCode,
    PdfRenderError,
)
from md2pdf_cli.html_builder import build_html_document
from md2pdf_cli.logging_utils import configure_logging
from md2pdf_cli.parser import DiagramBlock


# --- SVG validation edge cases ---


class TestMermaidSvgValidation:
    def test_truncated_svg_missing_closing_tag(self, tmp_path: Path) -> None:
        """SVG with opening tag but no closing tag should be rejected."""
        block = DiagramBlock(kind="mermaid", code="graph TD\n  A-->B", index=0, source_line=1)

        svg_file = tmp_path / "diagram-0.svg"
        truncated_svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="10" height="10"/>'
        svg_file.write_text(truncated_svg, encoding="utf-8")

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            with pytest.raises(DiagramRenderError, match="not a valid SVG"):
                _render_mermaid_svg(block=block, temp_dir=tmp_path, timeout=30)

    def test_valid_svg_passes(self, tmp_path: Path) -> None:
        """A complete SVG should pass validation."""
        block = DiagramBlock(kind="mermaid", code="graph TD\n  A-->B", index=0, source_line=1)

        svg_file = tmp_path / "diagram-0.svg"
        valid_svg = '<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>'
        svg_file.write_text(valid_svg, encoding="utf-8")

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            result = _render_mermaid_svg(block=block, temp_dir=tmp_path, timeout=30)

        assert "<svg" in result
        assert "</svg>" in result

    def test_empty_output_file(self, tmp_path: Path) -> None:
        """Empty SVG output file should be rejected."""
        block = DiagramBlock(kind="mermaid", code="graph TD\n  A-->B", index=0, source_line=1)

        svg_file = tmp_path / "diagram-0.svg"
        svg_file.write_text("", encoding="utf-8")

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

            with pytest.raises(DiagramRenderError, match="not a valid SVG"):
                _render_mermaid_svg(block=block, temp_dir=tmp_path, timeout=30)


class TestPlantumlSvgValidation:
    def test_truncated_svg_missing_closing_tag(self, tmp_path: Path) -> None:
        """PlantUML output with opening tag but no closing tag should be rejected."""
        block = DiagramBlock(kind="plantuml", code="@startuml\nA->B\n@enduml", index=0, source_line=1)
        jar = tmp_path / "plantuml.jar"
        jar.write_bytes(b"fake")

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='<svg xmlns="http://www.w3.org/2000/svg"><rect/>',
                stderr="",
            )

            with pytest.raises(DiagramRenderError, match="not SVG"):
                _render_plantuml_svg(block=block, plantuml_jar=jar, timeout=30)

    def test_valid_svg_passes(self, tmp_path: Path) -> None:
        block = DiagramBlock(kind="plantuml", code="@startuml\nA->B\n@enduml", index=0, source_line=1)
        jar = tmp_path / "plantuml.jar"
        jar.write_bytes(b"fake")

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout='<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>',
                stderr="",
            )
            result = _render_plantuml_svg(block=block, plantuml_jar=jar, timeout=30)

        assert "<svg" in result
        assert "</svg>" in result


# --- Timeout edge cases ---


class TestTimeoutHandling:
    def test_mermaid_timeout_raises(self, tmp_path: Path) -> None:
        block = DiagramBlock(kind="mermaid", code="graph TD\n  A-->B", index=0, source_line=5)

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="npx", timeout=10)

            with pytest.raises(DiagramRenderError, match="Timed out after 10 seconds"):
                _render_mermaid_svg(block=block, temp_dir=tmp_path, timeout=10)

    def test_plantuml_timeout_raises(self, tmp_path: Path) -> None:
        block = DiagramBlock(kind="plantuml", code="@startuml\nA->B\n@enduml", index=0, source_line=3)
        jar = tmp_path / "plantuml.jar"
        jar.write_bytes(b"fake")

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="java", timeout=30)

            with pytest.raises(DiagramRenderError, match="Timed out after 30 seconds"):
                _render_plantuml_svg(block=block, plantuml_jar=jar, timeout=30)


# --- Unsupported diagram kind ---


class TestUnsupportedDiagramKind:
    def test_unsupported_kind_raises(self, tmp_path: Path) -> None:
        block = DiagramBlock(kind="unknown", code="stuff", index=0, source_line=1)  # type: ignore[arg-type]
        config = RenderConfig(timeout_seconds=10)

        with pytest.raises(DiagramRenderError, match="Unsupported diagram kind"):
            render_diagram_fragments(
                [block], temp_dir=tmp_path, plantuml_jar=None, config=config,
            )


# --- PDF renderer error handling ---


class TestPdfRendererErrors:
    def test_os_error_wrapped_in_pdf_render_error(self, tmp_path: Path) -> None:
        from md2pdf_cli.pdf_renderer import render_pdf_from_html

        config = RenderConfig(timeout_seconds=10)
        with patch("md2pdf_cli.pdf_renderer.sync_playwright") as mock_pw:
            mock_browser = MagicMock()
            mock_page = MagicMock()
            mock_page.pdf.side_effect = OSError("disk full")
            mock_browser.new_page.return_value = mock_page
            mock_pw.return_value.__enter__ = MagicMock(return_value=MagicMock(chromium=MagicMock(launch=MagicMock(return_value=mock_browser))))
            mock_pw.return_value.__exit__ = MagicMock(return_value=False)

            with pytest.raises(PdfRenderError, match="Failed to write PDF"):
                render_pdf_from_html(
                    html="<html></html>",
                    output_path=tmp_path / "out.pdf",
                    config=config,
                )


# --- Exit code improvements ---


class TestExitCodes:
    def test_unexpected_error_code_exists(self) -> None:
        assert ExitCode.UNEXPECTED_ERROR == 1

    def test_all_exit_codes_unique(self) -> None:
        values = [e.value for e in ExitCode]
        assert len(values) == len(set(values))


# --- Logging ---


class TestLoggingNoDuplicates:
    def test_repeated_configure_does_not_duplicate_handlers(self) -> None:
        logger = configure_logging(verbose=False)
        initial_count = len(logger.handlers)

        configure_logging(verbose=True)
        configure_logging(verbose=False)

        assert len(logger.handlers) == initial_count

    def test_propagation_disabled(self) -> None:
        logger = configure_logging(verbose=False)
        assert logger.propagate is False


# --- HTML builder lang parameterization ---


class TestHtmlLangParam:
    def test_default_lang_is_ko(self) -> None:
        html = build_html_document(body_html="<p>test</p>", title="t")
        assert 'lang="ko"' in html

    def test_custom_lang(self) -> None:
        html = build_html_document(body_html="<p>test</p>", title="t", lang="en")
        assert 'lang="en"' in html

    def test_japanese_lang(self) -> None:
        html = build_html_document(body_html="<p>test</p>", title="t", lang="ja")
        assert 'lang="ja"' in html


# --- PlantUML jar not provided ---


class TestPlantumlJarMissing:
    def test_plantuml_without_jar_raises(self, tmp_path: Path) -> None:
        block = DiagramBlock(kind="plantuml", code="@startuml\nA->B\n@enduml", index=0, source_line=1)
        config = RenderConfig(timeout_seconds=10)

        with pytest.raises(DiagramRenderError, match="PlantUML jar path was not provided"):
            render_diagram_fragments(
                [block], temp_dir=tmp_path, plantuml_jar=None, config=config,
            )


# --- Mermaid non-zero exit code ---


class TestMermaidNonZeroExit:
    def test_non_zero_exit_raises(self, tmp_path: Path) -> None:
        block = DiagramBlock(kind="mermaid", code="invalid diagram", index=0, source_line=1)

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="Parse error"
            )

            with pytest.raises(DiagramRenderError, match="Parse error"):
                _render_mermaid_svg(block=block, temp_dir=tmp_path, timeout=30)

    def test_no_output_file_raises(self, tmp_path: Path) -> None:
        block = DiagramBlock(kind="mermaid", code="graph TD\n  A-->B", index=0, source_line=1)

        with patch("md2pdf_cli.diagram_renderers.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            # Don't create the SVG file

            with pytest.raises(DiagramRenderError, match="did not produce an SVG"):
                _render_mermaid_svg(block=block, temp_dir=tmp_path, timeout=30)


# --- Config validation ---


class TestConfigValidation:
    def test_invalid_page_size_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid page size"):
            RenderConfig(page_size="B5")

    def test_invalid_margin_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid top margin"):
            RenderConfig(margin_top="bad")

    def test_zero_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds must be greater than 0"):
            RenderConfig(timeout_seconds=0)

    def test_negative_timeout_raises(self) -> None:
        with pytest.raises(ValueError, match="timeout_seconds must be greater than 0"):
            RenderConfig(timeout_seconds=-5)


# --- Bootstrap ---


class TestBootstrapDownload:
    def test_skip_if_exists(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        jar = tmp_path / "plantuml.jar"
        jar.write_bytes(b"existing")
        download_plantuml_jar(jar, "http://example.com/plantuml.jar", force=False)
        captured = capsys.readouterr()
        assert "already exists" in captured.out

    def test_force_redownload(self, tmp_path: Path) -> None:
        jar = tmp_path / "plantuml.jar"
        jar.write_bytes(b"old")

        with patch("md2pdf_cli._bootstrap.urllib.request.urlretrieve") as mock_dl:
            def fake_download(url, path, reporthook=None):
                Path(path).write_bytes(b"new jar content")

            mock_dl.side_effect = fake_download
            download_plantuml_jar(jar, "http://example.com/plantuml.jar", force=True)

        assert jar.read_bytes() == b"new jar content"

    def test_partial_file_cleaned_on_failure(self, tmp_path: Path) -> None:
        jar = tmp_path / "plantuml.jar"

        with patch("md2pdf_cli._bootstrap.urllib.request.urlretrieve") as mock_dl:
            mock_dl.side_effect = ConnectionError("network error")

            with pytest.raises(ConnectionError):
                download_plantuml_jar(jar, "http://example.com/plantuml.jar", force=True)

        partial = tmp_path / "plantuml.jar.partial"
        assert not partial.exists()
        assert not jar.exists()

    def test_progress_hook_with_known_size(self, capsys: pytest.CaptureFixture[str]) -> None:
        _progress_hook(5, 1024, 10240)
        captured = capsys.readouterr()
        assert "50%" in captured.out

    def test_progress_hook_with_unknown_size(self, capsys: pytest.CaptureFixture[str]) -> None:
        _progress_hook(3, 8192, -1)
        captured = capsys.readouterr()
        assert "KB" in captured.out


# --- Logging verbose level ---


class TestLoggingLevels:
    def test_verbose_sets_debug(self) -> None:
        logger = configure_logging(verbose=True)
        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_non_verbose_sets_info(self) -> None:
        logger = configure_logging(verbose=False)
        assert logger.level == logging.INFO
        assert logger.handlers[0].level == logging.INFO
