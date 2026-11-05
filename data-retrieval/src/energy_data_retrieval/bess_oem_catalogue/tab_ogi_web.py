"""Stage the reviewed TAB OGi live-table partition without filling blank cells."""

from __future__ import annotations

import re

from .tab_ogi import MODELS

EXTRA_MODELS = ("2V 30 OGi 750", "2V 36 OGi 900", *(f"{n} OGi {n * 80}" for n in range(5, 19)))


def parse_table_cells(cells: list[str]) -> list[dict]:
    """Accept flattened HTML td/th text, preserving the empty seventh Ah column.

    HTML uses malformed row boundaries, so callers must not group by tr.
    This returns observations only, never canonical rows or inferred temperatures.
    """
    start = cells.index("Type") if "Type" in cells else -1
    expected = ["Type"] + ["Ah"] * 7 + ["mΩ", "kA", "mm", "mm", "mm", "kg", "kg"]
    if start < 0 or cells[start : start + 15] != expected:
        raise ValueError("Changed table units")
    if "with acid" not in cells[:start] or "dry" not in cells[:start]:
        raise ValueError("Missing mass basis")
    if cells.index("with acid") > cells.index("dry"):
        raise ValueError("Changed mass order")
    prefix = [
        "UF_V/Cell",
        "1,80",
        "1,75",
        "1,75",
        "1,70",
        "1,65",
        "1,65",
        "1,60",
        "EN/IEC 60896-11",
        "Dimensions",
        "Weight",
        "Discharging time  (h)",
        "10",
        "5",
        "3",
        "1",
        "1/2",
        "1/6",
        "1/12",
        "Ri",
        "Isc",
        "L",
        "W",
        "H",
        "with acid",
        "dry",
    ]
    if cells[:start] != prefix:
        raise ValueError("Changed rate, voltage or dimension headers")
    rows = []
    for i, cell in enumerate(cells):
        if not re.fullmatch(r"(?:\d+V )?\d+ OGi \d+", cell):
            continue
        tokens = cells[i + 1 : i + 15]
        if len(tokens) != 14:
            raise ValueError("Partial row")
        values = []
        for j, token in enumerate(tokens):
            if token == "" and j == 6 and cell in EXTRA_MODELS[2:]:
                values.append(None)
            elif re.fullmatch(r"\d+(?:\.\d+)?", token):
                values.append(float(token))
            else:
                raise ValueError("Unexpected blank or nonnumeric observation")
        known = [v for v in values if v is not None]
        capacities = [v for v in values[:7] if v is not None]
        if min(known) <= 0 or capacities != sorted(capacities, reverse=True):
            raise ValueError("Invalid observations")
        wet, dry = values[12], values[13]
        if wet is None or dry is None or wet <= dry:
            raise ValueError("Wet mass must exceed dry mass")
        rows.append({"model": cell, "values": values})
    if tuple(r["model"] for r in rows) != MODELS + EXTRA_MODELS:
        raise ValueError("Changed, missing or duplicate model partition")
    return rows
