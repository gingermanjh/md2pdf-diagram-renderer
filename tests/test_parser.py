from md2pdf_cli.parser import parse_markdown, placeholder_for


def test_parser_detects_supported_diagrams() -> None:
    markdown = """# Title

```mermaid
graph TD
  A --> B
```

```python
print('keep me')
```

```plantuml
@startuml
Alice -> Bob : Hello
@enduml
```

```ascii
+---+
| A |
+---+
```
"""

    parsed = parse_markdown(markdown)

    assert [block.kind for block in parsed.diagram_blocks] == [
        "mermaid",
        "plantuml",
        "ascii",
    ]
    assert parsed.diagram_blocks[0].source_line == 3
    assert placeholder_for(0) in parsed.html_body
    assert placeholder_for(1) in parsed.html_body
    assert placeholder_for(2) in parsed.html_body
    assert "language-python" in parsed.html_body


def test_parser_renders_table_markdown() -> None:
    markdown = """| A | B |
|---|---|
| 1 | 2 |
"""

    parsed = parse_markdown(markdown)

    assert "<table>" in parsed.html_body
    assert parsed.diagram_blocks == []
