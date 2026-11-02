"""Stage exact Rolls flooded-battery specifications from downloaded HTML.

Offline, bounded factual extraction only. No crawling, inferred energy/power,
canonical IDs, warranty adjudication or automatic family/variant merging.
"""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urlsplit


class _Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.text: list[str] = []
        self.models: list[str] = []
        self.model_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        elif tag in {"th", "td"} and self.row is not None:
            self.cell = []
            self.model_cell = "battery-title-model" in (dict(attrs).get("class") or "").split()
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"} and self.cell is not None and self.row is not None:
            value = " ".join("".join(self.cell).split())
            self.row.append(value)
            if self.model_cell:
                self.models.append(value)
            self.cell = None
            self.model_cell = False
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def _number(text: str, unit: str) -> float:
    match = re.fullmatch(r"([0-9]+(?:[.][0-9]+)?)\s*" + re.escape(unit), text)
    if not match or float(match[1]) <= 0:
        raise ValueError(f"Expected positive {unit!r} value, got {text!r}")
    return float(match[1])


def parse_rolls_flooded_html(
    content: bytes, *, source_url: str, expected_model: str
) -> dict[str, Any]:
    """Stage one reviewed model, preserving rate-dependent Ah and charge units.

    The caller must choose a renewable-energy model from the OEM index and review
    identity, revision and conditions. Fail on renamed models, duplicate labels,
    absent core rows or changed units; never repair units from magnitude.
    """
    url = urlsplit(source_url)
    if (
        url.scheme != "https"
        or url.hostname not in {"rollsbattery.com", "www.rollsbattery.com"}
        or not url.path.startswith("/battery/")
    ):
        raise ValueError("Expected an official Rolls battery product URL")
    parser = _Tables()
    parser.feed(content.decode("utf-8-sig"))
    if parser.models != [expected_model]:
        raise ValueError("Exact model identity changed or duplicated")
    text = " ".join(" ".join(parser.text).split())
    if "FLOODED DEEP CYCLE BATTERY" not in text:
        raise ValueError("Unsupported battery technology")
    labels = {
        "Series",
        "Warranty",
        "Volts",
        "Cells",
        "Plates/Cell",
        "Design",
        "Terminal Type",
        "Size & Thread",
        "Charge Voltage Range",
        "Float Voltage Range",
        "Recommended Charge Current",
        "Maximum Charge Current",
        "Self-Discharge Rate",
        "Weight",
        "Length",
        "Width",
        "Height Incl. Term.",
        "Container",
        "Cover",
        "Electrolyte Reserve",
    }
    values: dict[str, str] = {}
    rates = []
    seen_rates = set()
    for row_number, row in enumerate(parser.rows, 1):
        for i, cell in enumerate(row[:-1]):
            if cell in labels:
                if cell in values:
                    raise ValueError(f"Duplicate label: {cell}")
                values[cell] = row[i + 1]
        if row and row[0].startswith("@ "):
            match = re.fullmatch(r"@ ([0-9]+) Hour Rate", row[0])
            if not match or len(row) != 3:
                raise ValueError("Changed hour-rate row")
            hours = int(match[1])
            if hours in seen_rates or hours <= 0:
                raise ValueError("Duplicate or invalid hour rate")
            seen_rates.add(hours)
            rates.append(
                {
                    "hours": hours,
                    "capacity_ah": _number(row[1], "AH"),
                    "current_a": _number(row[2], "A"),
                    "table_row": row_number,
                }
            )
    required = {
        "Series",
        "Volts",
        "Cells",
        "Charge Voltage Range",
        "Weight",
        "Length",
        "Width",
        "Height Incl. Term.",
    }
    if not required <= values.keys() or not {20, 100} <= seen_rates:
        raise ValueError("Missing required technical facts or rate conditions")
    revision = re.search(r"Rev\.#\d+\s*\|\s*[A-Za-z]+ \d{4}", text)
    if not revision:
        raise ValueError("Missing printed revision")
    return {
        "model": expected_model,
        "source_url": source_url,
        "source_sha256": hashlib.sha256(content).hexdigest(),
        "document_revision": revision[0],
        "reported_fields": values,
        "voltage_v": _number(values["Volts"], ""),
        "cells": _number(values["Cells"], ""),
        "length_mm": _number(values["Length"], "mm"),
        "width_mm": _number(values["Width"], "mm"),
        "height_including_terminals_mm": _number(values["Height Incl. Term."], "mm"),
        "sample_mass_kg": _number(values["Weight"], "kg"),
        "recommended_charge_current_a": (
            _number(values["Recommended Charge Current"], "A")
            if "Recommended Charge Current" in values
            else None
        ),
        "maximum_charge_current_a": (
            _number(values["Maximum Charge Current"], "A")
            if "Maximum Charge Current" in values
            else None
        ),
        "discharge_rates": rates,
        "review_required": True,
    }
