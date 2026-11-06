"""Normalize reviewed exact-model OEM cells without repairing printed errors.

The caller supplies a bounded, individually reviewed table partition, including
units and locators. This adapter does not infer ratings from model identifiers,
expand platform ranges, establish installed compatibility, or validate performance.
"""

from __future__ import annotations

import math
from typing import Any

NUMERIC_CELLS = {
    "rated_power_kw": ("MW", 1000.0),
    "rotor_diameter_m": ("m", 1.0),
    "swept_area_m2": ("m2", 1.0),
    "cut_in_m_s": ("m/s", 1.0),
    "rated_wind_speed_m_s": ("m/s", 1.0),
    "cut_out_m_s": ("m/s", 1.0),
    "design_life_years": ("year", 1.0),
    "temperature_min_c": ("degC", 1.0),
    "temperature_max_c": ("degC", 1.0),
}


def normalize_oem_partition(
    reviews: list[dict[str, Any]], *, expected_models: list[str]
) -> list[dict[str, Any]]:
    """Require exact partition identity and units; quarantine inconsistent cells.

    A diameter/area discrepancy above 0.5% triggers review, not replacement by
    calculated area. Cut-out at/below cut-in or rated speed is also held. Blank
    cells stay null; zero is distinct and remains available for boundary checks.
    These are consistency screens, not a certification or measurement result.
    """
    models = [r["model"] for r in reviews]
    if (
        len(models) != len(set(models))
        or len(expected_models) != len(set(expected_models))
        or set(models) != set(expected_models)
    ):
        raise ValueError("Incomplete or duplicate exact-model partition")
    result = []
    for review in reviews:
        if not review.get("source_id") or not review.get("locator"):
            raise ValueError("Source and table locator required")
        cells = review["cells"]
        if set(cells) != set(NUMERIC_CELLS):
            raise ValueError("Every supported numeric cell must be explicit, including nulls")
        values, provenance, conflicts = {}, {}, {}
        for field, (unit, factor) in NUMERIC_CELLS.items():
            cell = cells[field]
            if cell["unit"] != unit:
                raise ValueError(f"Unexpected source unit for {field}")
            raw = cell["value"]
            if raw is not None and (type(raw) not in (int, float) or not math.isfinite(raw)):
                raise ValueError("Finite numeric cells or null required")
            if (
                raw is not None
                and field not in {"temperature_min_c", "temperature_max_c"}
                and raw < 0
            ):
                raise ValueError("Negative physical magnitude")
            values[field] = None if raw is None else raw * factor
            provenance[field] = {
                "original_value": raw,
                "unit": unit,
                "normalization": f"multiply by {factor:g}",
                "locator": review["locator"],
                "source_id": review["source_id"],
            }
        diameter, area = values["rotor_diameter_m"], values["swept_area_m2"]
        if diameter is not None and diameter > 0 and area is not None:
            check = math.pi * diameter**2 / 4
            if abs(area - check) / check > 0.005:
                conflicts["swept_area_m2"] = {
                    **provenance["swept_area_m2"],
                    "diameter_check_m2": check,
                    "reason": (
                        "Printed area differs from circular diameter check by more than 0.5%; "
                        "no replacement inferred"
                    ),
                }
                values["swept_area_m2"] = None
        cut_out = values["cut_out_m_s"]
        if cut_out is not None and any(
            values[f] is not None and cut_out <= values[f]
            for f in ("cut_in_m_s", "rated_wind_speed_m_s")
        ):
            conflicts["cut_out_m_s"] = {
                **provenance["cut_out_m_s"],
                "reason": "Printed cut-out does not exceed cut-in/rated speed; correction unknown",
            }
            values["cut_out_m_s"] = None
        low, high = values["temperature_min_c"], values["temperature_max_c"]
        if low is not None and high is not None and low > high:
            raise ValueError("Reversed operating temperature range")
        result.append(
            {
                "model": review["model"],
                "values": values,
                "provenance": provenance,
                "conflicts": conflicts,
            }
        )
    return result
