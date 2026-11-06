"""Deterministic offshore-wind export cable outage exposure, with explicit units.

All generation inputs are MW average power per interval. A cable outage changes
export transfer capacity; it does not change generation available at the farm.
The method is a scenario calculation, NOT an observed or predicted outage.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class CableExposure:
    """Energy-balance outputs in MWh over the complete supplied timeline."""

    available_wind_mwh: float
    baseline_export_mwh: float
    outage_export_mwh: float
    baseline_curtailed_mwh: float
    outage_curtailed_mwh: float
    incremental_lost_export_mwh: float
    outage_hours: float


def calculate_cable_exposure(
    wind_power_mw: Sequence[float],
    *,
    export_capacity_mw: float,
    outage_start_interval: int,
    outage_intervals: int,
    outage_export_capacity_mw: float,
    timestep_hours: float = 1.0,
) -> CableExposure:
    """Compare constrained transfer with and without a hypothetical cable outage.

    At each interval, exported MW = min(available wind MW, available export MW).
    The outage changes network transfer capacity only during the specified
    interval window. Values represent interval-AVERAGE powers in MW, and output
    MWh is power multiplied by `timestep_hours`. No prices, topology inference,
    electrical losses, storage, reactive constraints or reliability probabilities
    are modeled. Baseline curtailment is explicitly preserved.

    The requested outage window must fit wholly inside the input, rather than
    being silently truncated. Both end-points of the interval window are counted
    using the Python half-open convention [start, start + count).
    """
    if len(wind_power_mw) == 0:
        raise ValueError("wind_power_mw must contain at least one interval")
    for name, value in (
        ("export_capacity_mw", export_capacity_mw),
        ("outage_export_capacity_mw", outage_export_capacity_mw),
        ("timestep_hours", timestep_hours),
    ):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
    if export_capacity_mw < 0:
        raise ValueError("export_capacity_mw must be nonnegative")
    if not 0 <= outage_export_capacity_mw <= export_capacity_mw:
        raise ValueError("outage export capacity must be between zero and baseline")
    if timestep_hours <= 0:
        raise ValueError("timestep_hours must be positive")
    if (
        not isinstance(outage_start_interval, int)
        or isinstance(outage_start_interval, bool)
        or not isinstance(outage_intervals, int)
        or isinstance(outage_intervals, bool)
        or outage_start_interval < 0
        or outage_intervals < 0
        or outage_start_interval + outage_intervals > len(wind_power_mw)
    ):
        raise ValueError("outage must be a whole nonnegative interval window within input")

    wind_energy = normal_export = reduced_export = 0.0
    stop = outage_start_interval + outage_intervals
    for index, available_mw in enumerate(wind_power_mw):
        if not math.isfinite(available_mw) or available_mw < 0:
            raise ValueError("wind power must be finite and nonnegative")
        baseline_mw = min(available_mw, export_capacity_mw)
        transfer_mw = (
            outage_export_capacity_mw
            if outage_start_interval <= index < stop
            else export_capacity_mw
        )
        delivered_mw = min(available_mw, transfer_mw)
        wind_energy += available_mw * timestep_hours
        normal_export += baseline_mw * timestep_hours
        reduced_export += delivered_mw * timestep_hours
    return CableExposure(
        available_wind_mwh=wind_energy,
        baseline_export_mwh=normal_export,
        outage_export_mwh=reduced_export,
        baseline_curtailed_mwh=wind_energy - normal_export,
        outage_curtailed_mwh=wind_energy - reduced_export,
        incremental_lost_export_mwh=normal_export - reduced_export,
        outage_hours=outage_intervals * timestep_hours,
    )
