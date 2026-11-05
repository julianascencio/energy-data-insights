"""Stage Taiwan Energy Administration's licensed private-PV inventory.

Rows may be repeated equipment blocks or phases, not whole plants. No canonical
records, present status, AC/DC basis, owner roles or commissioning dates are inferred.
"""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from typing import Any

CAPTION = "民營太陽能發電系統發電業裝置容量資料"
HEADERS = ["公司名稱", "發電廠名稱", "所在縣市", "裝置容量(瓩)", "商轉年度"]


class _Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[dict[str, Any]] = []
        self.table: dict[str, Any] | None = None
        self.row: list[tuple[str, int, int]] | None = None
        self.cell: list[str] | None = None
        self.span = (1, 1)
        self.caption = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            if self.table is not None:
                raise ValueError("Nested inventory tables")
            self.table = {"caption": "", "rows": []}
        elif self.table is not None:
            if tag == "caption":
                self.caption = True
            elif tag == "tr":
                self.row = []
            elif tag in {"td", "th"}:
                a = dict(attrs)
                self.span = (int(a.get("rowspan") or "1"), int(a.get("colspan") or "1"))
                if not all(1 <= n <= 1000 for n in self.span):
                    raise ValueError("Invalid inventory cell span")
                self.cell = []
            elif tag == "br" and self.cell is not None:
                self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self.table is not None:
            if self.caption:
                self.table["caption"] += data
            elif self.cell is not None:
                self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.table is None:
            return
        if tag == "caption":
            self.caption = False
        elif tag in {"td", "th"} and self.cell is not None:
            if self.row is None:
                raise ValueError("Cell outside inventory row")
            self.row.append((" ".join("".join(self.cell).split()), *self.span))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.table["rows"].append(self.row)
            self.row = None
        elif tag == "table":
            self.tables.append(self.table)
            self.table = None


def read_taiwan_private_pv(
    content: bytes, *, sha256: str, after_row: int = 0, limit: int = 100
) -> dict[str, Any]:
    """Validate full table, then return a bounded physical-row candidate partition.

    Row locators are snapshot cursors, never persistent registry IDs. Rowspans are
    expanded only within the labelled PV table and their source origins retained.
    ROC year text is retained without interpreting it as a precise operating date.
    """
    if hashlib.sha256(content).hexdigest() != sha256:
        raise ValueError("Taiwan private PV source checksum changed")
    if (
        len(content) > 5_000_000
        or type(after_row) is not int
        or after_row < 0
        or type(limit) is not int
        or not 1 <= limit <= 200
    ):
        raise ValueError("Inventory size or partition bound")
    parser = _Tables()
    parser.feed(content.decode("utf-8-sig"))
    tables = [t for t in parser.tables if t["caption"].strip() == CAPTION]
    if len(tables) != 1:
        raise ValueError("Expected one explicitly labelled solar inventory")
    raw = tables[0]["rows"]
    if not raw or raw[0] != [(h, 1, 1) for h in HEADERS]:
        raise ValueError("Private PV public schema changed")
    active: dict[int, tuple[str, int, int]] = {}
    result: list[dict[str, Any]] = []
    footer = None
    for index, cells in enumerate(raw[1:], start=1):
        if cells and re.sub(r"\s", "", cells[0][0]) == "合計":
            if active or index != len(raw) - 1 or [x[2] for x in cells] != [3, 1, 1]:
                raise ValueError("Invalid total row or unfinished rowspan")
            footer = cells[1][0]
            continue
        values = {c: (text, origin) for c, (text, _, origin) in active.items()}
        next_active = {
            c: (text, left - 1, origin) for c, (text, left, origin) in active.items() if left > 1
        }
        column = 0
        for text, span, colspan in cells:
            while column in values:
                column += 1
            if column >= 5 or colspan != 1 or not text:
                raise ValueError("Ambiguous/private columns or empty inventory cell")
            values[column] = (text, index)
            if span > 1:
                next_active[column] = (text, span - 1, index)
            column += 1
        if set(values) != set(range(5)):
            raise ValueError("Incomplete inventory row")
        company, name, locality, power, year = [values[c][0] for c in range(5)]
        if not re.fullmatch(r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?", power):
            raise ValueError("Ambiguous native installed kW")
        if float(power.replace(",", "")) <= 0 or not re.fullmatch(
            r"\d{2,3}(?:[、,]\d{2,3})*", year
        ):
            raise ValueError("Invalid installed kW or ROC year text")
        result.append(
            {
                "source_row": index,
                "company_native": company,
                "plant_name_native": name,
                "locality_native": locality,
                "installed_kw_native": power,
                "commercial_year_roc_native": year,
                "cell_origin_rows": [values[c][1] for c in range(5)],
                "review_flags": [
                    "Company role, whole-plant and phase identity require review",
                    "Native installed kW has no established AC/DC basis",
                    "Historical ROC year is not current status or exact commissioning",
                    "Solar inventory alone does not establish PV technology for every row",
                ],
            }
        )
        active = next_active
    if active or footer is None or not result or after_row > len(result):
        raise ValueError("Missing total, unfinished rowspan or invalid cursor")
    selected = [r for r in result if r["source_row"] > after_row][:limit]
    return {
        "candidates": selected,
        "source_rows": len(result),
        "accepted_records": 0,
        "reported_total_kw_native": footer,
        "cursor_after_row": after_row,
        "next_after_row": selected[-1]["source_row"] if selected else after_row,
        "remaining_rows": len(result) - after_row - len(selected),
        "cursor_scope": "Physical PV data row in checksum-pinned HTML; not plant ID",
    }
