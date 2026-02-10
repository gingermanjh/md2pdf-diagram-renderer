from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

_ALLOWED_PAGE_SIZES = {"Letter", "A4"}
_MARGIN_RE = re.compile(r"^\d+(?:\.\d+)?(?:in|cm|mm|px)$")


@dataclass(frozen=True, slots=True)
class RenderConfig:
    page_size: str = "Letter"
    margin_top: str = "0.5in"
    margin_right: str = "0.5in"
    margin_bottom: str = "0.5in"
    margin_left: str = "0.5in"
    timeout_seconds: int = 60
    keep_temp: bool = False
    verbose: bool = False

    def __post_init__(self) -> None:
        if self.page_size not in _ALLOWED_PAGE_SIZES:
            raise ValueError(
                f"Invalid page size: {self.page_size}. Allowed values: Letter, A4"
            )

        for value, label in (
            (self.margin_top, "top"),
            (self.margin_right, "right"),
            (self.margin_bottom, "bottom"),
            (self.margin_left, "left"),
        ):
            if not _MARGIN_RE.match(value):
                raise ValueError(
                    f"Invalid {label} margin '{value}'. Use values like 0.5in, 12mm, 24px."
                )

        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be greater than 0")


@dataclass(frozen=True, slots=True)
class RenderResult:
    output_path: Path
    rendered_diagram_count: int
    elapsed_ms: int
