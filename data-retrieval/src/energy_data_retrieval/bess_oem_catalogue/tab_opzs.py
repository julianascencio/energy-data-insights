"""Stage the reviewed TAB OPzS cell table; no network or canonical writes."""

from __future__ import annotations

import hashlib
import re


def parse_cells(text: str) -> list[dict]:
    """Keep rate-specific Ah, dry/wet mass and short-circuit current distinct.

    Only the 22-row PDF cell partition is supported. HTML has a different mass
    order and extra models; blocks and other families must not enter this parser.
    A changed heading, partial table or duplicate model fails closed.
    """
    pages = [p for p in text.split("\f") if p.startswith("TAB OPzS CELLS")]
    if len(pages) != 1:
        raise ValueError("Expected one TAB OPzS CELLS PDF page")
    page = pages[0]
    compact = " ".join(page.split())
    required = [
        "Uf (V/cell) 1,80 1,77 1,75 1,67",
        "Discharging time (h) 10 5 3 1 Ri Isc L W H Dry Wet Poles",
        "Type Ah Ah Ah Ah mΩ A mm mm mm kg kg Nr.",
        "REFERENCE TEMPERATURE",
        "Weight tolerance is ± 5 %",
        "Electrical values are approximative.",
    ]
    if any(s not in compact for s in required) or not re.search(
        r"(?:^|\n|TEMPERATURE )· 20 °C(?:\s|$)", page
    ):
        raise ValueError("Unreviewed table units, mass order or discharge basis")
    rows = []
    for line in page.splitlines():
        match = re.match(r"^\s*(\d+ OPzS \d+)\s+(.*)$", line)
        if not match:
            continue
        tokens = match[2].split()
        if len(tokens) != 12 or any(not re.fullmatch(r"\d+(?:,\d+)?", t) for t in tokens):
            raise ValueError("Malformed exact-model row")
        v = [float(t.replace(",", ".")) for t in tokens]
        if min(v) <= 0 or not (v[0] >= v[1] >= v[2] >= v[3]) or v[9] >= v[10]:
            raise ValueError("Invalid capacity ordering or dry/wet mass")
        if v[11] not in {2, 4, 6, 8}:
            raise ValueError("Unreviewed terminal-pole count")
        rows.append(
            {
                "model": match[1],
                "capacity_observations": [
                    {
                        "hours": h,
                        "end_voltage_v_per_cell": u,
                        "capacity_ah": a,
                        "reference_temperature_c": 20,
                    }
                    for h, u, a in zip((10, 5, 3, 1), (1.80, 1.77, 1.75, 1.67), v[:4], strict=True)
                ],
                "internal_resistance_milliohm": v[4],
                "short_circuit_current_a": v[5],
                "length_mm": v[6],
                "width_mm": v[7],
                "height_mm": v[8],
                "dry_mass_kg": v[9],
                "wet_mass_kg": v[10],
                "terminal_poles": int(v[11]),
                "electrical_qualifier": "approximate",
                "weight_tolerance_pct": 5,
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
        )
    models = [r["model"] for r in rows]
    if len(models) != 22 or len(set(models)) != 22:
        raise ValueError("Incomplete or duplicate 22-row cell partition")
    if models[0] != "2 OPzS 100" or models[-1] != "24 OPzS 3000":
        raise ValueError("Changed partition boundaries")
    return rows


def parse_blocks(text: str) -> list[dict]:
    """Stage six OPzS monoblocs without mistaking block Ah for cell Ah."""
    pages = [p for p in text.split("\f") if p.startswith("TAB OPzS BLOCKS")]
    if len(pages) != 1:
        raise ValueError("Expected one TAB OPzS BLOCKS PDF page")
    page = pages[0]
    compact = " ".join(page.split())
    required = [
        "Uf (V/cell) 1,80 1,77 1,75 1,67",
        "Discharging time (h) 10 5 3 1 Ri Isc L W H Dry Wet",
        "Type Ah Ah Ah Ah mΩ A mm mm mm kg kg",
        "Weight tolerance is ± 5 %",
        "Electrical values are approximative.",
    ]
    if any(s not in compact for s in required):
        raise ValueError("Unreviewed block units or mass order")
    rows = []
    for line in page.splitlines():
        match = re.match(r"^\s*((6|12)V \d+ OPzS \d+)\s+(.+)$", line)
        if not match:
            continue
        tokens = match[3].split()
        if len(tokens) != 11 or any(not re.fullmatch(r"\d+(?:,\d+)?", t) for t in tokens):
            raise ValueError("Malformed exact block row")
        v = [float(t.replace(",", ".")) for t in tokens]
        if min(v) <= 0 or not (v[0] >= v[1] >= v[2] >= v[3]) or v[9] >= v[10]:
            raise ValueError("Invalid block capacity or mass ordering")
        rows.append(
            {
                "model": match[1],
                "nominal_block_voltage_v": int(match[2]),
                "capacity_observations": [
                    {"hours": h, "end_voltage_v_per_cell": u, "block_capacity_ah": a}
                    for h, u, a in zip((10, 5, 3, 1), (1.80, 1.77, 1.75, 1.67), v[:4], strict=True)
                ],
                "internal_resistance_milliohm": v[4],
                "short_circuit_current_a": v[5],
                "length_mm": v[6],
                "width_mm": v[7],
                "height_mm": v[8],
                "dry_mass_kg": v[9],
                "wet_mass_kg": v[10],
                "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            }
        )
    expected = [
        "12V 1 OPzS 50",
        "12V 2 OPzS 100",
        "12V 3 OPzS 150",
        "6V 4 OPzS 200",
        "6V 5 OPzS 250",
        "6V 6 OPzS 300",
    ]
    if [r["model"] for r in rows] != expected:
        raise ValueError("Changed, duplicate or incomplete block identities")
    return rows
