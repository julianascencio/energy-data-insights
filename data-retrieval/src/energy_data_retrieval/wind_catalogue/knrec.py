"""Checksum-pinned Korean certification register extraction; no validity inference."""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser


class _Rows(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.row: list[str] = []
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"}:
            self.cell = []
        if tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row:
            self.rows.append(self.row)


def certification_rows(original: bytes, *, sha256: str) -> dict[str, list[str]]:
    """Return exact register cells by certificate ID; keep ranges and conflicts raw.

    A listing is a dated registry observation, not an independently verified
    certificate or evidence of current eligibility. No power/hub Cartesian expansion.
    """
    if hashlib.sha256(original).hexdigest() != sha256:
        raise ValueError("Register checksum mismatch")
    parser = _Rows()
    parser.feed(original.decode("utf-8"))
    result: dict[str, list[str]] = {}
    for row in parser.rows:
        if len(row) > 1 and row[1].startswith("WT-"):
            if len(row) != 14 or row[1] in result:
                raise ValueError("Changed register shape or duplicate certificate ID")
            result[row[1]] = row
    if not result:
        raise ValueError("No certification rows")
    return result
