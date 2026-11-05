"""Offline exact Neata LFP48V and industrial ESS table staging.

Native labels retain unit and boundary distinctions. This parser does not infer
energy from Ah, active watts from current, or round-trip efficiency.
"""

from __future__ import annotations

import re

from energy_data_retrieval.bess_catalogue.pib import _Tables

LFP_MODELS = [
    "LFP4810",
    "LFP4820",
    "LFP4850",
    "LFP48100",
    "LFP48150",
    "LFP48180",
    "LFP48200",
    "LFP48240",
]
LFP_HEADER = [
    "Model",
    "Nominal voltage (V)",
    "Typical capacity (Ah)",
    "Charge current (A)",
    "Constant discharge current/ Peak current (3S)",
    "Weight (Kg)",
    "Dimension（mm)",  # noqa: RUF001 -- exact publisher table syntax
    "Remark",
    "Cycle life",
    "Warranty",
    "Communication",
]
ESS_FIELDS = [
    "Cell specification",
    "Battery rated energy",
    "Battery temperature control mode",
    "Rated power at AC side",
    "Maximum power at AC side",
    "Rated voltage at AC side",
    "Access mode",
    "Operating voltage range at AC side",
    "Power factor",
    "Adjustable range of power factor",
    "Rated grid frequency",
    "Grid frequency range",
    "Maximum total harmonic distortion",
    "DC component",
    "Cooling method",
    "Isolation mode",
    "System communication interface (external)",
    "System communication protocol (external)",
    "System efficiency",
    "Charge and discharge rate",
    "Depth of discharge",
    "Number of cycles",
    "Degree of protection",
    "Operating temperature range",
    "Operating humidity range",
    "Operating altitude",
    "Dimensions (W × D × H)",  # noqa: RUF001 -- exact publisher table syntax
    "Equipment weight (including battery)",
    "Fire protection system configuration",
]


def parse_neata_html(content: bytes, *, series: str) -> list[dict[str, str]]:
    """Stage a complete reviewed table, failing on identity/layout/unit changes."""
    parser = _Tables()
    parser.feed(content.decode("utf-8-sig"))
    parser.close()
    if parser.stack or len(parser.tables) != 1:
        raise ValueError("Expected one complete product table")
    table = parser.tables[0]
    if series == "lfp48":
        if len(table) != 10 or table[1] != LFP_HEADER:
            raise ValueError("LFP header/row count changed")
        if [r[0] for r in table[2:]] != LFP_MODELS:
            raise ValueError("Exact LFP model identity/order changed")
        out = []
        for row in table[2:]:
            if len(row) != 11 or any(not v for v in row):
                raise ValueError("Incomplete LFP row")
            if any(not re.fullmatch(r"\d+(?:\.\d+)?", row[i]) for i in [1, 2, 3, 5, 8]):
                raise ValueError("Numeric LFP field changed")
            if not re.fullmatch(r"\d+A/\d+A", row[4]):
                raise ValueError("Continuous/3-second current units changed")
            if not re.fullmatch(r"\d+\*\s*\d+\*\s*\d+", row[6]):
                raise ValueError("Dimension units/layout changed")
            out.append(dict(zip(LFP_HEADER, row, strict=True)))
        return out
    if series != "ess":
        raise ValueError("Unknown reviewed series")
    if table[0] != ["Product model", "ES100-2", "ES185-2"]:
        raise ValueError("Exact ESS model order changed")
    sections = {
        "Battery system parameters",
        "AC system parameters",
        "Communication parameters",
        "System parameters",
    }
    rows = []
    seen_sections = []
    for row in table[1:]:
        if row[0] in sections:
            if row != [row[0], ""]:
                raise ValueError("Section layout changed")
            seen_sections.append(row[0])
        else:
            if len(row) != 3 or not all(row):
                raise ValueError("Incomplete ESS row")
            rows.append(row)
    if (
        [r[0] for r in rows] != ESS_FIELDS
        or len(seen_sections) != 4
        or set(seen_sections) != sections
    ):
        raise ValueError("ESS fields changed or duplicated")
    units = {
        "Battery rated energy": r"\d+(?:\.\d+)?kWh",
        "Rated power at AC side": r"\d+kW",
        "Maximum power at AC side": r"\d+kW",
        "Rated voltage at AC side": r"\d+Vac",
        "Dimensions (W × D × H)": r"\d+×\d+×\d+mm",  # noqa: RUF001 -- exact publisher table syntax
        "Equipment weight (including battery)": r"\d+kg",
    }
    for key, pattern in units.items():
        row = next(r for r in rows if r[0] == key)
        if any(not re.fullmatch(pattern, v) for v in row[1:]):
            raise ValueError(f"Changed units for {key}")
    return [
        {"Model": model, **{r[0]: r[i] for r in rows}} for i, model in enumerate(table[0][1:], 1)
    ]
