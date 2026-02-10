from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from ._paths import css_path as _package_css_path
from ._paths import template_dir as _package_template_dir

_DEFAULT_TEMPLATE = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{{ title }}</title>
  <style>{{ css }}</style>
</head>
<body>
  <main class="doc-body">
    {{ body_html | safe }}
  </main>
</body>
</html>
"""

_DEFAULT_CSS = """
:root {
  color-scheme: light;
}
body {
  margin: 0;
  color: #111827;
  background: #ffffff;
  font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
  line-height: 1.55;
}
.doc-body {
  padding: 0;
}
h1, h2, h3, h4 {
  line-height: 1.25;
  margin-top: 1.6em;
}
pre, code {
  font-family: "SFMono-Regular", Consolas, Menlo, monospace;
}
pre {
  padding: 12px;
  border-radius: 6px;
  background: #f3f4f6;
  overflow-x: auto;
}
figure.diagram {
  margin: 1.2em 0;
}
figure.diagram svg {
  max-width: 100%;
  height: auto;
}
pre.ascii-diagram {
  white-space: pre;
}
table {
  border-collapse: collapse;
}
th, td {
  border: 1px solid #d1d5db;
  padding: 0.35em 0.6em;
}
"""


def build_html_document(
    *, body_html: str, title: str, project_root: Path | None = None
) -> str:
    css_text = _load_css(project_root)
    template = _load_template(project_root)
    return template.render(title=title, css=css_text, body_html=body_html)


def _load_template(project_root: Path | None):
    # 1. Explicit override
    if project_root is not None:
        template_path = project_root / "templates" / "base.html"
        if template_path.exists():
            env = Environment(loader=FileSystemLoader(str(template_path.parent)), autoescape=True)
            return env.get_template(template_path.name)

    # 2. Bundled package resource
    pkg_template = _package_template_dir() / "base.html"
    if pkg_template.exists():
        env = Environment(loader=FileSystemLoader(str(pkg_template.parent)), autoescape=True)
        return env.get_template(pkg_template.name)

    # 3. Inline fallback
    env = Environment(autoescape=True)
    return env.from_string(_DEFAULT_TEMPLATE)


def _load_css(project_root: Path | None) -> str:
    # 1. Explicit override
    if project_root is not None:
        css_file = project_root / "assets" / "default.css"
        if css_file.exists():
            return css_file.read_text(encoding="utf-8")

    # 2. Bundled package resource
    pkg_css = _package_css_path()
    if pkg_css.exists():
        return pkg_css.read_text(encoding="utf-8")

    # 3. Inline fallback
    return _DEFAULT_CSS
