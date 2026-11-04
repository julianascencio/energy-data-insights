"""Stage exact Elum ES controller limits from local PDF layout text.

No automatic import. Controlled plant capacity is not installed battery energy.
Common merged rows require separate visual review before canonical acceptance.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


def parse_es_text(content: bytes) -> list[dict[str, Any]]:
    """Read the reviewed three-column ES sheet, rejecting changed layouts."""
    pages = content.decode("utf-8-sig").split("\f")
    if len(pages) < 2 or "TECHNICAL SPECIFICATIONS" not in pages[1]:
        raise ValueError("Expected technical specifications on page 2")
    table = pages[1]
    if not re.search(r"GENERAL INFORMATION\s+ES Compact\s+ES\s+ES \+\s*\n", table):
        raise ValueError("Unexpected exact model columns")
    labels = (
        "Weight (without accessories)",
        "Maximum capacity (indicative solar kWp)",
        "Maximum BESS capacity (KWh)",
        "Max. number of devices",
        "PV inverters",
        "BESS",
        "Genset",
        "Meters",
        "Grid Connections (point of injection)",
    )
    fields = {}
    for label in labels:
        matches = re.findall(r"^\s*" + re.escape(label) + r"[ \t]+([^\n]+)$", table, re.M)
        if len(matches) != 1:
            raise ValueError(f"Missing or duplicate row: {label}")
        values = re.split(r"[ \t]{2,}", matches[0].strip())
        if len(values) != 3:
            raise ValueError(f"Ambiguous column count: {label}")
        fields[label] = values
    out = []
    for i, model in enumerate(
        ["ePowerControl ES Compact", "ePowerControl ES", "ePowerControl ES +"]
    ):
        observed = {k: v[i] for k, v in fields.items()}
        limits = {}
        for label, key in zip(
            labels[3:],
            ["devices", "pv_inverters", "bess", "gensets", "meters", "grid_connections"],
            strict=True,
        ):
            value = observed[label]
            if value == "N/A" and key == "gensets":
                limits[key] = None
            elif re.fullmatch(r"\d+", value):
                limits[key] = int(value)
            else:
                raise ValueError(f"Invalid device count: {label}")
        for label, units in [
            (labels[0], "kg"),
            (labels[1], "(?:kWp|MWp)"),
            (labels[2], "(?:kWh|MWh)"),
        ]:
            if not re.fullmatch(r"\d+(?:\.\d+)? " + units, observed[label]):
                raise ValueError(f"Invalid unit: {label}")
        out.append(
            {
                "model": model,
                "limits": limits,
                "reported_fields": observed,
                "locator": f"PDF page 2, exact column {i + 1}",
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return out
