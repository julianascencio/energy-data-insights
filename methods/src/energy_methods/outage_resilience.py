"""Minimum battery energy for an islanded critical-load outage scenario.

Reuses the renewable-priority energy balance in :mod:`energy_methods.hybrid_dispatch`.
This is a planning sensitivity, not a grid-forming or black-start model.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from energy_methods.hybrid_dispatch import DispatchResult, simulate_hybrid


def minimum_islanded_capacity(
    wind_mw: Sequence[float],
    solar_mw: Sequence[float],
    critical_load_mw: Sequence[float],
    *,
    inverter_mw: float,
    initial_soc_fraction: float = 0.8,
    roundtrip_efficiency: float = 0.9025,
    timestep_hours: float = 0.05,
    max_capacity_mwh: float = 20.0,
    unserved_tolerance_mwh: float = 1e-9,
) -> float:
    """Find the least modeled usable battery energy (MWh) meeting a load profile.

    Inputs are nonnegative constant-power MW samples, each with the same
    duration `timestep_hours`. Energy capacity excludes any inaccessible
    state-of-charge reserve. Renewable profiles are *conditional* on an
    islanded plant that can operate them independently of the grid.

    The result is a constrained bisection against `simulate_hybrid`, with
    renewable-first dispatch, MW/MWh limits and symmetric charge/discharge
    losses. If even `max_capacity_mwh` cannot serve demand with the given
    power rating, raise ValueError rather than returning a false solution.
    """
    parameters = (
        inverter_mw,
        initial_soc_fraction,
        roundtrip_efficiency,
        timestep_hours,
        max_capacity_mwh,
        unserved_tolerance_mwh,
    )
    if any(not math.isfinite(value) for value in parameters):
        raise ValueError("All battery and timestep parameters must be finite")
    if not (0.0 <= initial_soc_fraction <= 1.0):
        raise ValueError("Initial SOC fraction must be in [0, 1]")
    if max_capacity_mwh <= 0 or inverter_mw < 0 or unserved_tolerance_mwh < 0:
        raise ValueError("Invalid capacity, inverter power or tolerance")

    def dispatch(capacity_mwh: float) -> DispatchResult:
        return simulate_hybrid(
            wind_mw,
            solar_mw,
            critical_load_mw,
            battery_mwh=capacity_mwh,
            battery_mw=inverter_mw,
            efficiency=roundtrip_efficiency,
            initial_soc_mwh=capacity_mwh * initial_soc_fraction,
            timestep_hours=timestep_hours,
        )

    if dispatch(0.0).unserved_mwh <= unserved_tolerance_mwh:
        return 0.0
    if dispatch(max_capacity_mwh).unserved_mwh > unserved_tolerance_mwh:
        raise ValueError("No feasible capacity under the supplied power and energy limits")
    lower, upper = 0.0, max_capacity_mwh
    for _ in range(52):
        midpoint = (lower + upper) / 2.0
        if dispatch(midpoint).unserved_mwh <= unserved_tolerance_mwh:
            upper = midpoint
        else:
            lower = midpoint
    return upper
