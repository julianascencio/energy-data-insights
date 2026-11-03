"""Offline staging of the reviewed Crown SB-CRP-G0720 specification table.

Accept pdftotext -layout output, not arbitrary PDFs. No network, canonical IDs,
energy inference or automatic import. The ambiguous energy footnote is retained
for human review; kWh observations are never promoted to nominal/usable MWh.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

SOURCE_URL = "https://www.crownbattery.com/hubfs/Downloads/Renewable-Energy-Batteries.pdf"
_HEADERS = {
    "2, 6 & 12 VOLT CRP MONOBLOC SERIES — LOW MAINTENANCE FLA": "flooded_monobloc",
    "2, 6 & 12 VOLT CRV MONOBLOC SERIES — MAINTENANCE FREE AGM": "agm_monobloc",
    "2 & 6 VOLT CRP POWER MODULE SERIES — LOW MAINTENANCE FLA": "flooded_module",
    "FREEDOMBLOC ESS": "battery_system",
}
_MODEL = r"(?:\d+CR[PV]\d+|FB-(?:LM|MF)48V\d+)"


def parse_crown_table(content: bytes, *, source_url: str) -> list[dict[str, Any]]:
    """Stage exact rows; fail closed on changed edition, layout or duplicate models."""
    if source_url != SOURCE_URL:
        raise ValueError("Expected reviewed official Crown URL")
    text = content.decode("utf-8-sig")
    for marker in (
        "SB-CRP-G0720",
        "Specifications effective as of July 1, 2020.",
        "Depth-of-Discharge (DoD) of 50%, or 1.94 VPC.",
        "100-Hr",
    ):
        if marker not in text:
            raise ValueError(f"Missing reviewed edition/header/condition: {marker}")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    section = None
    for line in text.splitlines():
        line = " ".join(line.split())
        if line in _HEADERS:
            section = _HEADERS[line]
            continue
        if not section or not re.search(r"\b" + _MODEL + r"\b", line):
            continue
        match = re.fullmatch(r"(\S+) (" + _MODEL + r") (.+) (STD|Insert|HD SS)", line)
        if not match:
            raise ValueError("Unrecognized model row layout")
        bci, model, numbers, terminal = match.groups()
        if model in seen:
            raise ValueError(f"Duplicate exact model: {model}")
        seen.add(model)
        tokens = numbers.split()
        if len(tokens) != 13 or any(not re.fullmatch(r"\d+(?:\.\d+)?", v) for v in tokens):
            raise ValueError(f"Expected 13 positive numeric columns: {model}")
        v, ah20, ah100, kwh20, kwh100, li, lm, wi, wm, hi, hm, lb, kg = map(float, tokens)
        if min(map(float, tokens)) <= 0:
            raise ValueError(f"Nonpositive specification: {model}")
        rows.append(
            {
                "model": model,
                "product_level": section,
                "bci_group": None if bci == "—" else bci,
                "voltage_v": v,
                "capacity_ah": {"C20": ah20, "C100": ah100},
                "reported_energy_kwh": {"C20": kwh20, "C100": kwh100},
                "energy_disposition": "withheld_from_canonical_energy_ambiguous_footnote",
                "energy_condition": "OEM footnote: 50% DoD, or 1.94 VPC; no rescaling",
                "dimensions_mm": {"length": lm, "width": wm, "height": hm},
                "dimensions_inches": {"length": li, "width": wi, "height": hi},
                "weight_kg": kg,
                "weight_lb": lb,
                "terminal": terminal,
                "source_url": source_url,
                "locator": "PDF page 7, exact row " + model,
                "document_revision": "SB-CRP-G0720; effective 2020-07-01",
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    if not rows:
        raise ValueError("No reviewed model rows found")
    return rows
