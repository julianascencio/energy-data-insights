"""Offline wind comparisons with explicit specification and performance boundaries."""

from __future__ import annotations

import json
import math
from typing import Any


def specific_power_w_m2(
    rated_power_kw: float | None, rotor_diameter_m: float | None
) -> float | None:
    """Derive nameplate W/m², never operational performance; unknown inputs stay null."""
    if rated_power_kw is None or rotor_diameter_m is None:
        return None
    if any(not math.isfinite(x) or x <= 0 for x in (rated_power_kw, rotor_diameter_m)):
        raise ValueError("Require finite positive rated power and rotor diameter")
    return rated_power_kw * 1000 / (math.pi * (rotor_diameter_m / 2) ** 2)


def compatible_curves(rows: list[dict[str, Any]]) -> bool:
    """Require original numerical tables with identical, disclosed comparison conditions.

    Matching curves can still be manufacturer calculations, not measured performance.
    Source revisions and operating modes remain attached to each returned dataset.
    """
    if not rows:
        return False
    reference = None
    for row in rows:
        conditions = json.loads(row.get("curve_conditions") or "{}")
        required = ("air_density_kg_m3", "operating_mode", "wind_speed_unit", "performance_kind")
        if row.get("curve_origin") != "original_numeric" or any(
            conditions.get(k) is None for k in required
        ):
            return False
        key = (row.get("curve_kind"), row.get("curve_value_unit"), conditions)
        if reference is not None and key != reference:
            return False
        reference = key
    return True
