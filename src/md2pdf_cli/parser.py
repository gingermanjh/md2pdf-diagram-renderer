from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from markdown_it import MarkdownIt

from .errors import InputParseError

DiagramKind = Literal["mermaid", "plantuml", "ascii"]
_DIAGRAM_KINDS = {"mermaid", "plantuml", "ascii"}
_PLACEHOLDER_PREFIX = "MD2PDF_DIAGRAM_PLACEHOLDER_"


@dataclass(frozen=True, slots=True)
class DiagramBlock:
    kind: DiagramKind
    code: str
    index: int
    source_line: int | None


@dataclass(frozen=True, slots=True)
class ParsedMarkdown:
    html_body: str
    diagram_blocks: list[DiagramBlock]


def placeholder_for(index: int) -> str:
    return f"<!--{_PLACEHOLDER_PREFIX}{index}-->"


def parse_markdown(markdown_text: str) -> ParsedMarkdown:
    try:
        parser = MarkdownIt("default")
        tokens = parser.parse(markdown_text)
    except Exception as exc:  # pragma: no cover - defensive
        raise InputParseError(f"Failed to parse Markdown: {exc}") from exc

    lines = markdown_text.splitlines(keepends=True)
    diagram_blocks: list[DiagramBlock] = []
    replacements: list[tuple[int, int, str]] = []

    index = 0
    for token in tokens:
        if token.type != "fence":
            continue

        info = token.info.strip().split(maxsplit=1)
        language = info[0].lower() if info else ""
        if language not in _DIAGRAM_KINDS:
            continue

        start_line, end_line = _token_line_span(token)
        source_line = start_line + 1 if start_line is not None else None

        diagram_blocks.append(
            DiagramBlock(
                kind=language,  # type: ignore[arg-type]
                code=token.content,
                index=index,
                source_line=source_line,
            )
        )

        if start_line is None or end_line is None:
            raise InputParseError(
                f"Unable to calculate source range for {language} diagram #{index}."
            )

        replacements.append((start_line, end_line, placeholder_for(index)))
        index += 1

    transformed_markdown = _apply_replacements(lines, replacements)

    try:
        renderer = MarkdownIt("default", {"html": True})
        html_body = renderer.render(transformed_markdown)
    except Exception as exc:  # pragma: no cover - defensive
        raise InputParseError(f"Failed to render Markdown to HTML: {exc}") from exc

    return ParsedMarkdown(html_body=html_body, diagram_blocks=diagram_blocks)


def _token_line_span(token: object) -> tuple[int | None, int | None]:
    token_map = getattr(token, "map", None)
    if not token_map:
        return None, None
    if len(token_map) != 2:
        return None, None
    return int(token_map[0]), int(token_map[1])


def _apply_replacements(
    lines: list[str], replacements: list[tuple[int, int, str]]
) -> str:
    if not replacements:
        return "".join(lines)

    output_chunks: list[str] = []
    cursor = 0

    for start, end, replacement in sorted(replacements, key=lambda item: item[0]):
        output_chunks.extend(lines[cursor:start])
        output_chunks.append(f"{replacement}\n")
        cursor = end

    output_chunks.extend(lines[cursor:])
    return "".join(output_chunks)
