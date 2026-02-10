from pathlib import Path

from md2pdf_cli._paths import (
    css_path,
    data_dir,
    package_dir,
    plantuml_jar_path,
    template_dir,
)


def test_package_dir_points_to_md2pdf_cli() -> None:
    d = package_dir()
    assert d.name == "md2pdf_cli"
    assert d.is_dir()


def test_data_dir_is_under_home() -> None:
    d = data_dir()
    assert "md2pdf" in str(d)


def test_plantuml_jar_path_is_under_data_dir() -> None:
    jar = plantuml_jar_path()
    assert jar.parent == data_dir()
    assert jar.name == "plantuml.jar"


def test_template_dir_is_inside_package() -> None:
    d = template_dir()
    assert d.parent == package_dir()
    assert d.name == "templates"


def test_css_path_is_inside_package() -> None:
    p = css_path()
    assert p.parent.parent == package_dir()
    assert p.parent.name == "assets"
    assert p.name == "default.css"
    assert p.exists()