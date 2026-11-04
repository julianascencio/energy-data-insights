"""Stage the European Commission Innovation Fund project inventory offline.

Grant status is not plant lifecycle status. Category alone is not technology:
manufacturing, thermal, hydrogen, carbon storage and transport must be reviewed.
"""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
from typing import Any


class _Inventory(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[tuple[list[str], list[str]]] = []
        self.cells: list[str] | None = None
        self.cell: list[str] | None = None
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.cells, self.links = [], []
        elif self.cells is not None:
            if tag in {"td", "th"}:
                self.cell = []
            elif tag == "a":
                href = dict(attrs).get("href")
                if href:
                    self.links.append(href)
            elif tag in {"br", "p"} and self.cell is not None:
                self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None and self.cells is not None:
            self.cells.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.cells is not None:
            self.rows.append((self.cells, list(dict.fromkeys(self.links))))
            self.cells = None
        elif tag == "p" and self.cell is not None:
            self.cell.append(" ")


def parse_innovation_fund_html(content: bytes) -> list[dict[str, Any]]:
    """Return attributed candidate rows, never canonical records or inferred status.

    Retain all rows so screening cannot silently omit a battery project filed
    under another category. Conflicting repeated identities fail closed. Reused
    factsheet URLs are flagged because distinct projects can have a bad link.
    """
    parser = _Inventory()
    parser.feed(content.decode("utf-8-sig"))
    header = ["Project", "Type", "Category", "Sector", "Location", "Technology pathways", "Status"]
    if not parser.rows or parser.rows[0][0] != header:
        raise ValueError("Changed Innovation Fund header")
    out: list[dict[str, Any]] = []
    identities: set[tuple[str, str]] = set()
    url_counts: dict[str, int] = {}
    for i, (cells, urls) in enumerate(parser.rows[1:], 1):
        if len(cells) != 7 or not all(cells):
            raise ValueError("Incomplete or changed inventory row")
        identity = (cells[0], cells[1])
        if identity in identities:
            raise ValueError("Duplicate project/call identity")
        identities.add(identity)
        for url in urls:
            url_counts[url] = url_counts.get(url, 0) + 1
        out.append(
            dict(
                source_row=i,
                project_label=cells[0],
                call=cells[1],
                category=cells[2],
                sector=cells[3],
                location=cells[4],
                technology=cells[5],
                grant_status=cells[6],
                factsheet_urls=urls,
                review_required=True,
                source_sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    if not out:
        raise ValueError("Empty project inventory")
    for row in out:
        row["shared_factsheet_url"] = any(url_counts[u] > 1 for u in row["factsheet_urls"])
    return out
