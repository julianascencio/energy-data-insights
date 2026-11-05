"""Stage exact Microcare manual configurations from local PDF layout text.

No network, canonical writes, inferred voltage variants, battery capacities or
AC-throughput multipliers. Datasheet/manual disagreements require human review.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

EDITIONS = {
    "1-5": (
        "INV-1-5kW-LION- 2018-4-V10R5/6",
        [
            ["1kW12V", "2kW12V"],
            ["1kW24V", "2kW24V", "3kW24V", "5kW24V"],
            ["1kW36V", "2kW36V", "3kW36V", "5kW36V"],
            ["1kW48V", "2kW48V", "3kW48V", "5kW48V"],
        ],
    ),
    "5-8": ("INV-5-8kW-LION- 2021-1-V21R1", [["5kW48V"], ["8kW48V"]]),
    "10-15": ("INV-10&15kW- LION- 2021-1-V21R1", [["10kW48V", "15kW48V"]]),
}


def _row(block: str, label: str, unit: str, count: int) -> list[float]:
    lines = re.findall(r"^\s*" + label + r"\s+(.+)$", block, re.MULTILINE)
    if len(lines) != 1:
        raise ValueError(f"Expected one {label} row")
    raw = lines[0].strip()
    if unit:
        values = re.findall(r"(\d+(?:\.\d+)?)\s*" + unit + r"\b", raw)
        residual = re.sub(r"\d+(?:\.\d+)?\s*" + unit + r"\b", "", raw)
    else:
        values = raw.split()
        residual = "" if all(re.fullmatch(r"\d+(?:\.\d+)?", x) for x in values) else raw
    if residual.strip() or len(values) != count:
        raise ValueError(f"Changed units or column count in {label}")
    return [float(v) for v in values]


def parse_manual(text: str, series: str) -> dict[str, Any]:
    """Return reviewed model columns and native rating bases, never imported rows."""
    if series not in EDITIONS:
        raise ValueError("Unsupported Microcare series")
    revision, expected = EDITIONS[series]
    if f"Manual Version: {revision}" not in text:
        raise ValueError("Unreviewed manual revision")
    heads = list(re.finditer(r"^\s*Model\s+((?:\d+kW\d+V\s*)+)$", text, re.MULTILINE))
    if [h.group(1).split() for h in heads] != expected:
        raise ValueError("Changed or repeated model columns")
    candidates = []
    for index, head in enumerate(heads):
        models = head.group(1).split()
        block = text[head.end() : heads[index + 1].start() if index + 1 < len(heads) else len(text)]
        block = block.split("\f")[0]
        n = len(models)
        power = _row(block, r"Capacity\s+Watt", "", n)
        nominal = _row(block, "Nominal Voltage", "VDC", n)
        current = _row(block, "Maxi Input Amps", "A", n)
        standby = _row(block, "Standby Power", "W", n)
        charging = _row(block, "Maximum Current", "A", n)
        limits = re.findall(r"^\s*Acceptable Voltage(?: Range)?\s+(.+)$", block, re.MULTILINE)
        if len(limits) != 1:
            raise ValueError("Missing voltage envelope")
        ranges = re.findall(r"(\d+)-(\d+)\s*VDC", limits[0])
        if len(ranges) != n or re.sub(r"\d+-\d+\s*VDC", "", limits[0]).strip():
            raise ValueError("Changed voltage range units or columns")
        for j, model in enumerate(models):
            low, high = map(float, ranges[j])
            if not low <= nominal[j] <= high or power[j] <= 0:
                raise ValueError("Invalid voltage envelope or active power")
            candidates.append(
                {
                    "model": model,
                    "power_w": power[j],
                    "dc_nominal_v": nominal[j],
                    "dc_min_v": low,
                    "dc_max_v": high,
                    "maximum_dc_input_a": current[j],
                    "standby_w": standby[j],
                    "maximum_charge_a": charging[j],
                    "rating_condition": "AC Output = Normal; not grid-assisted 200% throughput",
                }
            )
    return {
        "revision": revision,
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "candidates": candidates,
    }
