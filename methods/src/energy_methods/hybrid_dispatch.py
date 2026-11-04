"""Deterministic hourly hybrid renewable and battery dispatch (MW, MWh).

This is an illustrative energy-balance model, not a market or network optimizer.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Sequence


@dataclass(frozen=True)
class DispatchResult:
    renewable_mwh: float
    served_mwh: float
    demand_mwh: float
    curtailed_mwh: float
    discharged_mwh: float
    unserved_mwh: float
    coverage: float


def simulate_hybrid(
    wind_mw: Sequence[float],
    solar_mw: Sequence[float],
    demand_mw: Sequence[float],
    *,
    battery_mwh: float,
    battery_mw: float,
    efficiency: float = 0.9,
    initial_soc_mwh: float = 0.0,
    timestep_hours: float = 1.0,
) -> DispatchResult:
    """Serve demand from wind/solar, then charge/discharge a constrained battery.

    Round-trip efficiency is split symmetrically across charge and discharge.
    The battery is charged only from renewable surplus. No grid imports.
    """
    import math

    if not wind_mw or len(wind_mw) != len(solar_mw) or len(wind_mw) != len(demand_mw):
        raise ValueError("Nonempty wind, solar and demand arrays must have equal lengths")
    if not (0 < efficiency <= 1) or timestep_hours <= 0:
        raise ValueError("Efficiency must be in (0,1] and timestep positive")
    if battery_mwh < 0 or battery_mw < 0 or not 0 <= initial_soc_mwh <= battery_mwh:
        raise ValueError("Invalid battery capacity, power or initial state of charge")
    values = (*wind_mw, *solar_mw, *demand_mw)
    if any(not math.isfinite(x) or x < 0 for x in values):
        raise ValueError("All power values must be finite and nonnegative")

    soc = initial_soc_mwh
    eta = math.sqrt(efficiency)
    served = curtailed = discharged = renewable = demand_total = 0.0
    for w, s, d in zip(wind_mw, solar_mw, demand_mw, strict=True):
        supply = (w + s) * timestep_hours
        need = d * timestep_hours
        renewable += supply
        demand_total += need
        direct = min(supply, need)
        served += direct
        surplus = supply - direct
        charge_input = min(surplus, battery_mw * timestep_hours, (battery_mwh - soc) / eta)
        soc += charge_input * eta
        curtailed += surplus - charge_input
        deficit = need - direct
        delivered = min(deficit, battery_mw * timestep_hours, soc * eta)
        soc -= delivered / eta
        discharged += delivered
        served += delivered
    return DispatchResult(
        renewable_mwh=renewable,
        served_mwh=served,
        demand_mwh=demand_total,
        curtailed_mwh=curtailed,
        discharged_mwh=discharged,
        unserved_mwh=demand_total - served,
        coverage=served / demand_total if demand_total else 1.0,
    )
