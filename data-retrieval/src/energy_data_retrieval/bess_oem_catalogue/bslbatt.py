"""Stage the reviewed seven-column BSLBATT S205/S314 station tables offline.

Input is local ``pdftotext -layout`` output. No fetching, canonical identity,
power calculation, conflict resolution or automatic import is performed.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

SOURCE_URLS = {
    "S205": "https://bslbatt.com/wp-content/uploads/2025/05/ESS-GRID-S205-250508.pdf",
    "S314": "https://bslbatt.com/wp-content/uploads/2025/10/ESS-GRID-S314-250508.pdf",
}


def parse_station_table(content: bytes, *, family: str, source_url: str) -> list[dict[str, Any]]:
    """Fail closed on changed headers/units, missing rows and ambiguous column scope.

    The source calls an energy row ``Rate Power(kWh)``. Its original label and
    units are preserved: this parser never interprets that row as active power.
    Maximum currents remain observations; S205's conflicting 0.5C claim is flagged.
    """
    if family not in SOURCE_URLS or source_url != SOURCE_URLS[family]:
        raise ValueError("Expected reviewed family and official source URL")
    text = content.decode("utf-8-sig")
    lines = [" ".join(line.split()) for line in text.splitlines()]
    expected = "ESS-GRID " + " ".join(f"{family}-{i}" for i in range(10, 17))
    headers = [line for line in lines if line.startswith("ESS-GRID ") and f"{family}-10" in line]
    if headers != [expected]:
        raise ValueError("Expected one exact ordered seven-model header")
    lines = lines[lines.index(expected) + 1 :]

    def numbers(label: str, count: int) -> list[float]:
        matches = [line[len(label) :].strip() for line in lines if line.startswith(label)]
        if len(matches) != 1:
            raise ValueError(f"Missing or duplicate row: {label}")
        tokens = matches[0].split()
        if len(tokens) != count or any(not re.fullmatch(r"\d+(?:\.\d+)?", t) for t in tokens):
            raise ValueError(f"Unexpected numeric scope or units: {label}")
        values = list(map(float, tokens))
        if min(values) <= 0:
            raise ValueError(f"Nonpositive rating: {label}")
        return values

    voltage = numbers("Rated Voltage(V)", 7)
    energy = numbers("Rate Power(kWh)", 7)
    high = numbers("Charge Upper Voltage(V)", 7)
    low = numbers("Discharge Lower Voltage(V)", 7)
    packs = numbers("Number of Series", 7)
    if packs != list(range(10, 17)):
        raise ValueError("Unexpected series-pack counts")
    ah = numbers("Rated Capacity(Ah)", 1)[0]
    cell_ah = numbers("Cell Model(LFP-3.2V)(Ah)", 1)[0]
    recommended = numbers("Recommended Current(A)", 1)[0]
    charge = numbers("Max. Charging Current(A)", 1)[0]
    discharge = numbers("Max. Discharging Current(A)", 1)[0]
    if ah != cell_ah or not all(lo < v < hi for lo, v, hi in zip(low, voltage, high, strict=True)):
        raise ValueError("Inconsistent cell capacity or voltage envelope")
    rows = []
    for i in range(7):
        rows.append(
            {
                "model": f"ESS-GRID {family}-{i + 10}",
                "family": family,
                "rated_voltage_v": voltage[i],
                "rated_capacity_ah": ah,
                "cell_capacity_ah": cell_ah,
                "reported_energy_kwh": energy[i],
                "original_energy_label": "Rate Power(kWh)",
                "active_power_kw": None,
                "charge_upper_voltage_v": high[i],
                "discharge_lower_voltage_v": low[i],
                "series_pack_count": int(packs[i]),
                "recommended_current_a": recommended,
                "reported_max_charge_current_a": charge,
                "reported_max_discharge_current_a": discharge,
                "current_review_required": family == "S205",
                "current_review_reason": (
                    "Page 1 maximum 0.5C versus page 2 maximum current; "
                    "do not resolve automatically"
                    if family == "S205"
                    else None
                ),
                "source_url": source_url,
                "locator": f"PDF page 2 technical specification, column {family}-{i + 10}",
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return rows
