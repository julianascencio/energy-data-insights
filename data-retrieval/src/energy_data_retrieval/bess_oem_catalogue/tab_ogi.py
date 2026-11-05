"""Stage the reviewed TAB OGi cell/monobloc table; no canonical writes."""

from __future__ import annotations

import hashlib
import re

MODELS = (
    "12V 1 OGi 25",
    "12V 2 OGi 50",
    "12V 3 OGi 75",
    "12V 4 OGi 100",
    "12V 5 OGi 125",
    "12V 6 OGi 150",
    "6V 7 OGi 175",
    "6V 8 OGi 200",
    "6V 9 OGi 225",
    "6V 10 OGi 250",
    "6V 11 OGi 275",
    "6V 12 OGi 300",
    "2V 3 OGi 75",
    "2V 4 OGi 100",
    "2V 5 OGi 125",
    "2V 6 OGi 150",
    "2V 7 OGi 175",
    "2V 8 OGi 200",
    "2V 9 OGi 225",
    "2V 10 OGi 250",
    "2V 11 OGi 275",
    "2V 12 OGi 300",
    "2V 13 OGi 325",
    "2V 14 OGi 350",
    "2V 24 OGi 600",
)


def parse_models(text: str) -> list[dict]:
    """Preserve rate capacities, fault-current units and dry/wet mass boundaries."""
    pages = [p for p in text.split("\f") if p.startswith("TAB OGi BATTERIES")]
    if len(pages) != 1:
        raise ValueError("Expected one OGi table page")
    page = pages[0]
    required = [
        "Uf (V/cell) 1,80 1,75 1,75 1,70 1,65 1,65 1,60",
        "Discharging time (h) 10 5 3 1 1/2 1/6 1/12 Ri Isc L W H Dry Wet",
        "Type Ah Ah Ah Ah Ah Ah Ah mΩ (kA) mm mm mm kg kg",
    ]
    if "V15-03-01-2022" not in text or any(s not in " ".join(page.split()) for s in required):
        raise ValueError("Unreviewed revision, units, mass order or discharge basis")
    rows = []
    for line in page.splitlines():
        m = re.match(r"^\s*(\d+V \d+ OGi \d+)\s+(.+)$", line)
        if not m:
            continue
        tokens = m[2].split()
        if len(tokens) != 14 or any(not re.fullmatch(r"\d+(?:,\d+)?", x) for x in tokens):
            raise ValueError("Malformed model observation")
        v = [float(x.replace(",", ".")) for x in tokens]
        if min(v) <= 0 or v[:7] != sorted(v[:7], reverse=True) or v[12] >= v[13]:
            raise ValueError("Invalid capacity ordering or wet/dry mass")
        voltage = int(m[1].split("V")[0])
        rows.append(
            {
                "model": m[1],
                "rated_voltage_v": voltage,
                "product_level": "cell" if voltage == 2 else "monobloc",
                "capacity_observations": [
                    {
                        "hours": h,
                        "end_voltage_v_per_cell": u,
                        "capacity_ah": a,
                        "reference_temperature_c": 20,
                    }
                    for h, u, a in zip(
                        (10, 5, 3, 1, 0.5, 1 / 6, 1 / 12),
                        (1.8, 1.75, 1.75, 1.7, 1.65, 1.65, 1.6),
                        v[:7],
                        strict=True,
                    )
                ],
                "internal_resistance_milliohm": v[7],
                "short_circuit_current_ka": v[8],
                "length_mm": v[9],
                "width_mm": v[10],
                "height_mm": v[11],
                "dry_mass_kg": v[12],
                "wet_mass_kg": v[13],
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
        )
    if tuple(r["model"] for r in rows) != MODELS:
        raise ValueError("Changed, partial or duplicate exact-model partition")
    return rows
