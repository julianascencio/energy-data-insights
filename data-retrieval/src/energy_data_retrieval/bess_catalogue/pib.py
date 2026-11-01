"""Offline staging of PIB's Indian BESS deployment table, never automatic imports.

The July 2026 table includes portfolio aggregates, ambiguous identities and
description/rating disagreements. Return reported columns separately from the
description; reviewed site identities and lifecycle evidence are still required.
"""

from __future__ import annotations

import math
import re
from html.parser import HTMLParser
from typing import Any


class _Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.stack.append({"rows": [], "row": None, "cell": None})
        elif self.stack:
            table = self.stack[-1]
            if tag == "tr":
                table["row"] = []
            elif tag in {"td", "th"}:
                table["cell"] = []
            elif tag in {"br", "p"} and table["cell"] is not None:
                table["cell"].append(" ")

    def handle_data(self, data: str) -> None:
        if self.stack and self.stack[-1]["cell"] is not None:
            self.stack[-1]["cell"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        table = self.stack[-1]
        if tag in {"td", "th"} and table["cell"] is not None:
            if table["row"] is not None:
                table["row"].append(" ".join("".join(table["cell"]).split()))
            table["cell"] = None
        elif tag == "tr" and table["row"] is not None:
            table["rows"].append(table["row"])
            table["row"] = None
        elif tag == "table":
            self.tables.append(table["rows"])
            self.stack.pop()


def _capacity(text: str) -> float:
    value = text.strip()
    if not re.fullmatch(r"(?:\d+|\d{1,3}(?:,\d{3})+)(?:\.\d+)?", value):
        raise ValueError(f"Invalid reported capacity: {text!r}")
    number = float(value.replace(",", ""))
    if not math.isfinite(number):
        raise ValueError("Non-finite capacity")
    return number


def parse_pib_bess_html(content: bytes) -> list[dict[str, Any]]:
    """Extract Table-II candidates, preserving MW/MWh and mixed project scopes.

    Supports identical mobile/desktop table copies without double counting. A
    changed header, conflicting duplicate, missing row or inconsistent total
    fails closed. No power is extracted from free text or hybrid solar ratings.
    """
    parser = _Tables()
    parser.feed(content.decode("utf-8-sig"))
    header = ["Sl. No.", "Details of BESS Deployment", "State", "Capacity"]
    tables = [rows for rows in parser.tables if rows and rows[0] == header]
    if not tables:
        raise ValueError("PIB BESS table header not found; review source revision")
    accepted: list[dict[str, Any]] | None = None
    for table in tables:
        if len(table) < 4 or table[1] != ["MW", "MWh"]:
            raise ValueError("PIB capacity units changed")
        candidates: list[dict[str, Any]] = []
        totals = None
        for cells in table[2:]:
            if "Total" in cells:
                if totals is not None:
                    raise ValueError("Duplicate total")
                totals = [_capacity(v) for v in cells[-2:]]
                continue
            if len(cells) != 5 or not re.fullmatch(r"\d+\.", cells[0]):
                raise ValueError("Unexpected PIB row shape")
            row_number = int(cells[0][:-1])
            if row_number != len(candidates) + 1 or not cells[1] or not cells[2]:
                raise ValueError("Missing/duplicate row number or identity text")
            candidates.append(
                {
                    "source_row": row_number,
                    "reported_description": cells[1],
                    "reported_state": cells[2],
                    "reported_power_mw": _capacity(cells[3]),
                    "reported_energy_mwh": _capacity(cells[4]),
                    "review_required": True,
                }
            )
        if totals is None or any(
            not math.isclose(sum(r[key] for r in candidates), total, abs_tol=0.005)
            for key, total in zip(("reported_power_mw", "reported_energy_mwh"), totals, strict=True)
        ):
            raise ValueError("Missing or inconsistent PIB table totals")
        if accepted is not None and candidates != accepted:
            raise ValueError("Conflicting desktop/mobile PIB table copies")
        accepted = candidates
    assert accepted is not None
    return accepted
