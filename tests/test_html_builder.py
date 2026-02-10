from pathlib import Path

from md2pdf_cli.html_builder import build_html_document


def test_build_html_without_project_root() -> None:
    html = build_html_document(
        body_html="<p>Hello</p>",
        title="test",
        project_root=None,
    )
    assert "<p>Hello</p>" in html
    assert "<title>test</title>" in html
    # Should use the package CSS (assets/default.css exists)
    assert "Apple SD Gothic Neo" in html


def test_build_html_with_explicit_project_root(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "default.css").write_text(
        "body { color: red; }", encoding="utf-8"
    )
    html = build_html_document(
        body_html="<p>Custom</p>",
        title="custom",
        project_root=tmp_path,
    )
    assert "color: red" in html


def test_build_html_falls_back_to_package_css_when_project_root_has_no_css(
    tmp_path: Path,
) -> None:
    # project_root exists but has no assets/ dir
    html = build_html_document(
        body_html="<p>Fallback</p>",
        title="fallback",
        project_root=tmp_path,
    )
    # Should fall back to package CSS
    assert "Apple SD Gothic Neo" in html


def test_html_uses_korean_lang() -> None:
    html = build_html_document(
        body_html="<p>한글</p>",
        title="ko-test",
    )
    assert 'lang="ko"' in html