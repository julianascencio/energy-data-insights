"""Offline staging of Studer XTH/XTM/XTS English product tables.

Apparent power is never converted to active power. The two responsive renderings
must agree. A cooling option is an operating condition, not another model.
"""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from typing import Any


class _ProductHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self.titles: list[str] = []
        self.blocks: list[str] = []
        self.depth = 0
        self.title = False
        self.cell: list[str] | None = None
        self.row: list[str] = []
        self.table: list[list[str]] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = (dict(attrs).get("class") or "").split()
        if tag == "div":
            if "elementor-toggle-item" in classes:
                if self.depth:
                    raise ValueError("Nested product block")
                self.blocks.append("")
                self.depth = 1
            elif self.depth:
                self.depth += 1
        if tag == "a" and "elementor-toggle-title" in classes:
            self.titles.append("")
            self.title = True
        if tag == "table":
            if self.table is not None:
                raise ValueError("Nested table")
            self.table = []
        if tag == "tr":
            self.row = []
        if tag == "td":
            self.cell = []
        if tag in {"br", "sup"}:
            self.handle_data(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.depth:
            self.depth -= 1
        if tag == "a":
            self.title = False
        if tag == "td" and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.table is not None:
            self.table.append(self.row)
        if tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None
        if tag in {"p", "div", "sup"}:
            self.handle_data(" ")

    def handle_data(self, data: str) -> None:
        if self.title:
            self.titles[-1] += data
        if self.depth:
            self.blocks[-1] += data
        if self.cell is not None:
            self.cell.append(data)


def _match(pattern: str, value: str) -> tuple[str, ...]:
    result = re.fullmatch(pattern, value)
    if result is None:
        raise ValueError(f"Changed units or value shape: {value}")
    return result.groups()


def parse_studer_html(content: bytes, series: str) -> list[dict[str, Any]]:
    """Stage reviewed model tables; fail on changed identities, units or layout."""
    models = {
        "xtm": ["1500-12", "2000-12", "2400-24", "2600-48", "3500-24", "4000-48"],
        "xth": ["3000-12", "5000-24", "6000-48", "8000-48"],
        "xts": ["900-12", "1200-24", "1400-48"],
    }
    if series not in models:
        raise ValueError("Unreviewed Studer series")
    parser = _ProductHTML()
    parser.feed(content.decode("utf-8-sig"))
    expected = [f"{series} {model}" for model in models[series]]
    if parser.titles != expected or len(parser.blocks) != len(expected):
        raise ValueError("Changed, missing or duplicate exact model headings")
    count = 4 * len(expected)
    if len(parser.tables) != 2 * count or parser.tables[:count] != parser.tables[count:]:
        raise ValueError("Responsive tables disagree or table count changed")
    out: list[dict[str, Any]] = []
    number = r"([0-9]+(?:\.[0-9]+)?)"
    for i, model in enumerate(expected):
        pairs = [r for table in parser.tables[i * 4 : i * 4 + 4] for r in table]
        if len(pairs) != 13 or any(len(r) != 2 for r in pairs):
            raise ValueError("Changed model table shape")
        data = dict(pairs)
        if len(data) != 13:
            raise ValueError("Duplicate specification heading")
        try:
            dc = _match(
                number + r"\s*Vdc \(" + number + r" \u2013 " + number + r" Vdc\)",
                data["Nominal battery voltage (Input range)"],
            )
            raw_power = data["Continuous power 25°C"]
            raw_30min = data["Power 30 min. 25°C"]
            if series == "xts":
                if (
                    "These features are valid only when using the cooling module ecf 01"
                    not in parser.blocks[i]
                ):
                    raise ValueError("Missing cooling footnote")
                power = _match(number + r" \(1\) / " + number + " VA", raw_power)
                minute = _match(number + r" \(1\) / " + number + " VA", raw_30min)
            else:
                power = _match(number + " VA", raw_power)
                minute = _match(number + " VA", raw_30min)
            peak = _match(number + " kVA", data["Power 5 sec. 25°C"])
            idle = _match(
                number + "/" + number + "/" + number + " W", data["Consumption OFF/Stand-by/ON"]
            )
            charge = _match(number + " A", data["Maximum charging current (2)"])
            currents = _match(
                number + " Aac / " + number + " Aac",
                data["Input current max. (transfer relay) / Output current max."],
            )
            dims = _match(
                number + r"\s*/\s*" + number + r"\s*/\s*" + number + " mm",
                data["Dimensions h/w/l [mm]"],
            )
            weight = _match(number + " kg", data["Weight"])
            if data["Transfer time"] != "< 15 ms":
                raise ValueError("Changed transfer-time bound")
            if "230 Vac" not in data["Output voltage and frequency (2)"]:
                raise ValueError("Unreviewed AC voltage")
        except KeyError as exc:
            raise ValueError(f"Missing expected heading: {exc}") from exc
        if not float(dc[1]) < float(dc[0]) < float(dc[2]):
            raise ValueError("Invalid voltage range")
        if any(
            float(v) <= 0
            for values in [power, minute, peak, charge, currents, dims, weight]
            for v in values
        ):
            raise ValueError("Nonpositive equipment rating")
        out.append(
            dict(
                model=model,
                dc_nominal_v=float(dc[0]),
                dc_min_v=float(dc[1]),
                dc_max_v=float(dc[2]),
                continuous_va=float(power[-1]),
                overload_30min_va=float(minute[-1]),
                continuous_with_ecf01_va=float(power[0]) if series == "xts" else None,
                overload_30min_with_ecf01_va=float(minute[0]) if series == "xts" else None,
                overload_5sec_kva=float(peak[0]),
                consumption_off_standby_on_w=list(map(float, idle)),
                charge_current_max_a=float(charge[0]),
                transfer_current_max_a=float(currents[0]),
                output_current_max_a=float(currents[1]),
                dimensions_h_w_l_mm=list(map(float, dims)),
                weight_kg=float(weight[0]),
                source_sha256=hashlib.sha256(content).hexdigest(),
                locator=(
                    f"Technical specifications > {model}; four tables and footnotes; "
                    "responsive duplicates checked"
                ),
            )
        )
    return out
