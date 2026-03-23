from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    SUCCESS = 0
    UNEXPECTED_ERROR = 1
    DEPENDENCY_ERROR = 2
    DIAGRAM_RENDER_ERROR = 3
    INPUT_PARSE_ERROR = 4
    PDF_RENDER_ERROR = 5


class Md2PdfError(Exception):
    exit_code: ExitCode = ExitCode.PDF_RENDER_ERROR


class DependencyError(Md2PdfError):
    exit_code = ExitCode.DEPENDENCY_ERROR

    def __init__(self, messages: list[str]) -> None:
        self.messages = messages
        joined = "\n".join(f"- {item}" for item in messages)
        super().__init__(f"Missing or invalid runtime dependencies:\n{joined}")


class InputParseError(Md2PdfError):
    exit_code = ExitCode.INPUT_PARSE_ERROR


class DiagramRenderError(Md2PdfError):
    exit_code = ExitCode.DIAGRAM_RENDER_ERROR

    def __init__(
        self,
        *,
        kind: str,
        index: int,
        source_line: int | None,
        command: str,
        stderr: str,
    ) -> None:
        location = f"line {source_line}" if source_line else "unknown line"
        message = (
            f"Failed to render {kind} diagram #{index} ({location}).\n"
            f"Command: {command}\n"
            f"Details: {stderr.strip() or 'No additional error output'}"
        )
        super().__init__(message)


class PdfRenderError(Md2PdfError):
    exit_code = ExitCode.PDF_RENDER_ERROR
