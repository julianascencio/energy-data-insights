"""Stage the reviewed TAB OPzV PDF table without inferring power or energy."""

from __future__ import annotations

import hashlib
import re

MODELS = (
    "4 OPzV 200",
    "5 OPzV 250",
    "6 OPzV 300",
    "5 OPzV 350",
    "6 OPzV 420",
    "7 OPzV 490",
    "6 OPzV 600",
    "8 OPzV 800",
    "10 OPzV 1000",
    "12 OPzV 1200",
    "12 OPzV 1500",
    "16 OPzV 2000",
    "20 OPzV 2500",
    "24 OPzV 3000",
)


def parse_cells(text: str) -> list[dict]:
    """Keep nominal and measured Ah, two heights, and fault current separate.

    This parser stages observations, including values requiring cross-source
    review. It does not select between conflicting PDF and website observations.
    """
    pages = [p for p in text.split("\f") if p.startswith("TAB OPzV BATTERIES")]
    if len(pages) != 1:
        raise ValueError("Expected one TAB OPzV BATTERIES PDF page")
    page = pages[0]
    compact = " ".join(page.split())
    required = [
        "V15-03-01-2022",
        "Uf (V/cell) 1,8 1,8 1,77 1,75 1,67",
        "Discharging time (h) 10 10 5 3 1 Ri Isc L W H1/H2 Wet Poles",
        "Type Nom. Cap. (Ah) Capacity (Ah) at 20°C mΩ A mm mm mm kg Nr.",
        "Weight tolerance is ± 5 %",
        "Electrical values are approximative.",
    ]
    if any(s not in compact for s in required):
        raise ValueError("Unreviewed revision, units or discharge basis")
    rows = []
    for line in page.splitlines():
        match = re.match(r"^\s*(\d+ OPzV \d+)\s+(.+)$", line)
        if not match:
            continue
        tokens = match[2].split()
        if len(tokens) != 12 or not re.fullmatch(r"\d+/\d+", tokens[9]):
            raise ValueError("Malformed exact-model row or paired heights")
        flat = tokens[:9] + tokens[9].split("/") + tokens[10:]
        if any(not re.fullmatch(r"\d+(?:,\d+)?", t) for t in flat):
            raise ValueError("Malformed numeric observation")
        v = [float(t.replace(",", ".")) for t in flat]
        if min(v) <= 0 or not v[1] >= v[2] >= v[3] >= v[4] or v[9] >= v[10]:
            raise ValueError("Invalid capacities or paired heights")
        if v[12] not in {2, 4, 6, 8}:
            raise ValueError("Unreviewed terminal-pole count")
        rows.append(
            {
                "model": match[1],
                "nominal_capacity_ah": v[0],
                "nominal_capacity_basis": {"hours": 10, "end_voltage_v_per_cell": 1.8},
                "capacity_observations": [
                    {
                        "hours": h,
                        "end_voltage_v_per_cell": u,
                        "capacity_ah": a,
                        "reference_temperature_c": 20,
                    }
                    for h, u, a in zip((10, 5, 3, 1), (1.8, 1.77, 1.75, 1.67), v[1:5], strict=True)
                ],
                "internal_resistance_milliohm": v[5],
                "short_circuit_current_a": v[6],
                "length_mm": v[7],
                "width_mm": v[8],
                "height_h1_mm": v[9],
                "height_h2_mm": v[10],
                "wet_mass_kg": v[11],
                "terminal_poles": int(v[12]),
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
        )
    if tuple(r["model"] for r in rows) != MODELS:
        raise ValueError("Changed, incomplete or duplicate model partition")
    return rows
