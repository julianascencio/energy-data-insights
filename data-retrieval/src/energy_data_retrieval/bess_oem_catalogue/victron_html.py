"""Stage bounded technical facts from two reviewed Victron HTML manual tables.

Offline only. Preserve model-column identity, explicit colspan scope and units.
This does not infer active power from VA, choose between documents, assign stable
IDs or import canonical records. A reviewer must check footnotes and revisions.
"""

from __future__ import annotations

import hashlib
from html.parser import HTMLParser
from typing import Any

_TABLES = {
    (
        "https://www.victronenergy.com/media/pg/MultiPlus_12V_500-1200VA_120Vac/"
        "en/technical-data.html"
    ): (
        "MultiPlus",
        "12/500/20 - 120V",
        "12/800/35 - 120V",
        "12/1200/50 - 120V",
    ),
    "https://www.victronenergy.com/media/pg/MultiPlus_2kVA_230V/en/technical-data-2kva.html": (
        "",
        "MultiPlus 12/2000/80",
        "MultiPlus 24/2000/50",
        "MultiPlus 48/2000/25",
    ),
}
_PREFIXES = (
    "DC Input voltage range",
    "Input voltage range",
    "AC output voltage",
    "Output voltage",
    "Cont. output power at",
    "Peak power",
    "Maximum efficiency",
    "Zero-load power",
    "Charge current house battery",
    "Transfer switch",
    "Weight",
    "Dimensions (h x w x d)",
)


class _ManualTables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[tuple[str, int, int]]]] = []
        self.table: list[list[tuple[str, int, int]]] | None = None
        self.row: list[tuple[str, int, int]] | None = None
        self.cell: list[str] | None = None
        self.span: tuple[int, int] = (1, 1)
        self.stack: list[Any] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.stack.append((self.table, self.row, self.cell, self.span))
            self.table, self.row, self.cell = [], None, None
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            a = dict(attrs)
            self.span = (int(a.get("colspan") or 1), int(a.get("rowspan") or 1))
            self.cell = []
        elif self.cell is not None and tag in {"p", "br", "sup"}:
            self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append((" ".join("".join(self.cell).split()), self.span[0], self.span[1]))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table, self.row, self.cell, self.span = self.stack.pop()


def parse_victron_manual_html(content: bytes, *, source_url: str) -> list[dict[str, Any]]:
    """Return three explicitly named model candidates from a supported manual.

    Fail closed on changed model order, missing power rows, ambiguous spans or
    duplicate tables/labels. Shared values are propagated only when an explicit
    HTML colspan covers all three model columns. Numerical text is not repaired.
    """
    if source_url not in _TABLES:
        raise ValueError("Unsupported Victron manual URL")
    expected = _TABLES[source_url]
    parser = _ManualTables()
    parser.feed(content.decode("utf-8-sig"))
    matches = [t for t in parser.tables if t and tuple(c[0] for c in t[0]) == expected]
    if len(matches) != 1:
        raise ValueError("Expected one exact model header; source layout or identity changed")
    table = matches[0]
    if any(c[1:] != (1, 1) for c in table[0]):
        raise ValueError("Spanned model headers require review")
    models: list[dict[str, Any]] = [
        {
            "model_header": model,
            "source_url": source_url,
            "source_sha256": hashlib.sha256(content).hexdigest(),
            "observations": [],
            "review_required": True,
        }
        for model in expected[1:]
    ]
    seen = set()
    for row_number, cells in enumerate(table[1:], start=2):
        if not cells or not cells[0][0].startswith(_PREFIXES):
            continue
        label, span, rowspan = cells[0]
        if label in seen:
            raise ValueError("Duplicate technical label; no silent overwrite")
        seen.add(label)
        if span != 1 or rowspan != 1:
            raise ValueError("Spanned technical label requires review")
        values = cells[1:]
        if not (
            (len(values) == 3 and all(c[1:] == (1, 1) for c in values))
            or (len(values) == 1 and values[0][1:] == (3, 1))
        ):
            raise ValueError("Ambiguous model-value span; no implicit family propagation")
        shared = len(values) == 1
        for i, model in enumerate(models):
            value = values[0 if shared else i][0]
            if not value:
                raise ValueError("Empty technical value requires review")
            model["observations"].append(
                {
                    "label": label,
                    "reported_value": value,
                    "shared_colspan": shared,
                    "table_row": row_number,
                }
            )
    for model in models:
        power = [
            o["reported_value"]
            for o in model["observations"]
            if o["label"].startswith("Cont. output power at 25")
        ]
        if (
            len(power) != 2
            or not any(v.endswith("VA") for v in power)
            or not any(v.endswith("W") for v in power)
        ):
            raise ValueError("Separate apparent and active 25 C power rows required")
        if not {"Peak power", "Maximum efficiency", "Transfer switch"} <= seen:
            raise ValueError("Mandatory technical rows missing")
    return models
