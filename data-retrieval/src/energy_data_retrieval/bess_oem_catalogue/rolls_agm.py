"""Offline staging of exact Rolls AGM-S tables from reader-extracted text.

The input is extracted text, not original HTML. Its checksum must never be
reported as a checksum of the publisher's bytes. No network or canonical upsert.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any
from urllib.parse import urlsplit


def parse_rolls_agm_text(content: bytes, *, source_url: str, expected_model: str) -> dict[str, Any]:
    """Preserve exact unit/rate observations and flag inconsistent Ah/current pairs.

    Accept one individually reviewed AGM-S model. Blank discharge currents stay
    missing. Charge voltage strings retain per-cell and temperature boundaries.
    """
    url = urlsplit(source_url)
    if url.scheme != "https" or url.hostname not in {
        "rollsbattery.com",
        "www.rollsbattery.com",
    }:
        raise ValueError("Expected official Rolls URL")
    if url.path != f"/battery/{expected_model.lower()}/":
        raise ValueError("URL/model identity mismatch")
    text = content.decode("utf-8-sig")
    lines = [" ".join(x.split()) for x in text.splitlines()]
    if lines.count(f"# {expected_model}") not in {1, 2}:
        raise ValueError("Missing or duplicate exact AGM model")
    labels = {
        "Series",
        "Volts",
        "Cells",
        "Terminal Type",
        "Charge Voltage Range",
        "Float Voltage Range",
        "Recommended Charge Current",
        "Maximum Charge Current",
        "Internal Resistance",
        "Weight",
        "Length",
        "Width",
        "Height Incl. Term.",
    }
    fields: dict[str, list[str]] = {}
    rates: list[dict[str, Any]] = []
    for line in lines:
        cells = [x.strip() for x in line.split("|")]
        if cells[0] in labels:
            if cells[0] in fields:
                raise ValueError("Duplicate technical label")
            fields[cells[0]] = cells[1:]
        if line.startswith("@ "):
            match = re.fullmatch(r"@ (\d+) Hour Rate \| ([\d.]+) AH \|(?: ([\d.]+) A)?", line)
            if not match:
                raise ValueError("Changed discharge-rate units or shape")
            hours, ah = int(match[1]), float(match[2])
            current = float(match[3]) if match[3] else None
            if hours <= 0 or ah <= 0 or (current is not None and current <= 0):
                raise ValueError("Invalid discharge rate")
            rates.append(dict(hours=hours, capacity_ah=ah, current_a=current))
    if not labels <= fields.keys() or fields["Series"][0] != "VRLA AGM-S":
        raise ValueError("Missing technical fields or unsupported series")
    hours = [r["hours"] for r in rates]
    if len(hours) != len(set(hours)) or not {5, 10, 20} <= set(hours):
        raise ValueError("Missing or duplicated discharge rates")
    revision = [x for x in lines if re.fullmatch(r"Rev\.#\d+ \| [A-Za-z]+ \d{4}", x)]
    if len(revision) != 1:
        raise ValueError("Missing or duplicated printed revision")
    numeric = {}
    for key, unit in [
        ("Volts", ""),
        ("Cells", ""),
        ("Weight", "kg"),
        ("Length", "mm"),
        ("Width", "mm"),
        ("Height Incl. Term.", "mm"),
        ("Recommended Charge Current", "A"),
        ("Maximum Charge Current", "A"),
    ]:
        match = re.fullmatch(r"([\d.]+)\s*" + unit, fields[key][0])
        if not match or float(match[1]) <= 0:
            raise ValueError(f"Changed or invalid units for {key}")
        numeric[key] = float(match[1])
    conflicts = [
        r
        for r in rates
        if r["current_a"] is not None
        and abs(r["hours"] * r["current_a"] - r["capacity_ah"]) / r["capacity_ah"] > 0.01
    ]
    return dict(
        model=expected_model,
        source_url=source_url,
        extracted_text_sha256=hashlib.sha256(content).hexdigest(),
        document_revision=revision[0],
        reported_fields=fields,
        numeric=numeric,
        discharge_rates=rates,
        rate_conflicts=conflicts,
        review_required=True,
    )
