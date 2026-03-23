from __future__ import annotations

import types

import pytest

from md2pdf_cli.diagram_renderers import (
    check_common_dependencies,
    check_mermaid_dependencies,
    check_plantuml_dependencies,
    check_runtime_dependencies,
)
from md2pdf_cli.errors import DependencyError


def _install_fake_playwright(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_sync_api = types.ModuleType("playwright.sync_api")

    class FakeError(Exception):
        pass

    class _Browser:
        def close(self) -> None:
            return None

    class _Chromium:
        def launch(self, *, headless: bool) -> _Browser:  # noqa: ARG002
            return _Browser()

    class _PlaywrightContext:
        chromium = _Chromium()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
            return False

    def _sync_playwright() -> _PlaywrightContext:
        return _PlaywrightContext()

    fake_sync_api.Error = FakeError
    fake_sync_api.sync_playwright = _sync_playwright

    fake_pkg = types.ModuleType("playwright")
    fake_pkg.sync_api = fake_sync_api

    monkeypatch.setitem(__import__("sys").modules, "playwright", fake_pkg)
    monkeypatch.setitem(__import__("sys").modules, "playwright.sync_api", fake_sync_api)


# --- Backward-compatible wrapper tests ---


def test_dependency_check_fails_when_plantuml_jar_missing(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    _install_fake_playwright(monkeypatch)

    monkeypatch.setattr("md2pdf_cli.diagram_renderers.shutil.which", lambda _name: "/bin/mock")

    with pytest.raises(DependencyError) as exc_info:
        check_runtime_dependencies(tmp_path)

    assert "PlantUML jar not found" in str(exc_info.value)


def test_dependency_check_reports_missing_commands(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    _install_fake_playwright(monkeypatch)

    def _which(name: str) -> str | None:
        if name == "java":
            return None
        return "/bin/mock"

    monkeypatch.setattr("md2pdf_cli.diagram_renderers.shutil.which", _which)

    tools_dir = tmp_path / ".tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    (tools_dir / "plantuml.jar").write_bytes(b"jar")

    with pytest.raises(DependencyError) as exc_info:
        check_runtime_dependencies(tmp_path)

    assert "`java` is missing" in str(exc_info.value)


def test_runtime_dependencies_succeeds(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    _install_fake_playwright(monkeypatch)
    monkeypatch.setattr("md2pdf_cli.diagram_renderers.shutil.which", lambda _name: "/bin/mock")

    tools_dir = tmp_path / ".tools"
    tools_dir.mkdir(parents=True, exist_ok=True)
    jar = tools_dir / "plantuml.jar"
    jar.write_bytes(b"jar")

    result = check_runtime_dependencies(tmp_path)
    assert result == jar


# --- Split function tests ---


def test_check_common_dependencies_succeeds_with_playwright(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_playwright(monkeypatch)
    # Should not raise
    check_common_dependencies()


def test_check_mermaid_dependencies_reports_missing_node(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _which(name: str) -> str | None:
        if name == "node":
            return None
        return "/bin/mock"

    monkeypatch.setattr("md2pdf_cli.diagram_renderers.shutil.which", _which)

    with pytest.raises(DependencyError) as exc_info:
        check_mermaid_dependencies()

    assert "`node` is missing" in str(exc_info.value)


def test_check_mermaid_dependencies_reports_missing_npx(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _which(name: str) -> str | None:
        if name == "npx":
            return None
        return "/bin/mock"

    monkeypatch.setattr("md2pdf_cli.diagram_renderers.shutil.which", _which)

    with pytest.raises(DependencyError) as exc_info:
        check_mermaid_dependencies()

    assert "`npx` is missing" in str(exc_info.value)


def test_check_mermaid_dependencies_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("md2pdf_cli.diagram_renderers.shutil.which", lambda _name: "/bin/mock")
    # Should not raise
    check_mermaid_dependencies()


def test_check_plantuml_dependencies_missing_jar(tmp_path) -> None:
    jar = tmp_path / "nonexistent.jar"
    with pytest.raises(DependencyError) as exc_info:
        check_plantuml_dependencies(jar=jar)

    assert "PlantUML jar not found" in str(exc_info.value)


def test_check_plantuml_dependencies_missing_java(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setattr("md2pdf_cli.diagram_renderers.shutil.which", lambda _name: None)
    jar = tmp_path / "plantuml.jar"
    jar.write_bytes(b"jar")

    with pytest.raises(DependencyError) as exc_info:
        check_plantuml_dependencies(jar=jar)

    assert "`java` is missing" in str(exc_info.value)


def test_check_plantuml_dependencies_returns_jar(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    monkeypatch.setattr("md2pdf_cli.diagram_renderers.shutil.which", lambda _name: "/bin/mock")
    jar = tmp_path / "plantuml.jar"
    jar.write_bytes(b"jar")

    result = check_plantuml_dependencies(jar=jar)
    assert result == jar