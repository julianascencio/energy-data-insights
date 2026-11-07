"""Transparent daily turbine-installation and commissioning opportunity scenarios.

This is a project-planning sensitivity model, not offshore weather forecasting,
asset dispatch, or a claim about any named project's actual construction plan.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class InstallationSchedule:
    """Daily-installation events; day 0 is the first illustrative campaign day."""

    completion_days: tuple[int, ...]
    duration_days: int
    charter_vessel_days: int


def simulate_installation(
    turbines: int,
    *,
    vessel_start_days: Sequence[int],
    workable_days: Sequence[bool],
    workable_days_per_turbine: float,
) -> InstallationSchedule:
    """Install turbines with independent vessel crews and site-wide weather.

    Each vessel accrues one unit of work on a workable day once available.
    Each turbine requires ``workable_days_per_turbine`` accumulated units on
    *one* vessel. Progress survives bad-weather days; vessels do not transfer
    partially completed turbine jobs. At most one turbine per vessel per day.

    These simplified constraints ignore foundations, port loading, lifting,
    maintenance, cable laying and crew shifts; workload and site-wide weather
    are declared *scenario inputs*, not observed Dogger Bank conditions.
    """
    if not isinstance(turbines, int) or isinstance(turbines, bool) or turbines <= 0:
        raise ValueError("turbines must be a positive integer")
    if not math.isfinite(workable_days_per_turbine) or workable_days_per_turbine < 1:
        raise ValueError("workable_days_per_turbine must be finite and at least one")
    starts = tuple(vessel_start_days)
    if not starts or any(
        not isinstance(day, int) or isinstance(day, bool) or day < 0 for day in starts
    ):
        raise ValueError("vessel start days must be nonnegative integers")
    if not workable_days or any(not isinstance(day, bool) for day in workable_days):
        raise ValueError("workable_days must be a nonempty sequence of booleans")

    work_done = [0.0] * len(starts)
    completions: list[int] = []
    for day, workable in enumerate(workable_days):
        if workable:
            for index, start in enumerate(starts):
                if day < start or len(completions) == turbines:
                    continue
                work_done[index] += 1.0
                if work_done[index] + 1e-12 >= workable_days_per_turbine:
                    completions.append(day)
                    work_done[index] -= workable_days_per_turbine
        if len(completions) == turbines:
            duration = day + 1
            return InstallationSchedule(
                completion_days=tuple(sorted(completions)),
                duration_days=duration,
                charter_vessel_days=sum(max(0, duration - start) for start in starts),
            )
    raise ValueError("The supplied weather horizon does not complete the installations")


def commissioning_opportunity_mwh(
    schedule: InstallationSchedule,
    *,
    project_capacity_mw: float,
    net_capacity_factor: float,
    horizon_days: int,
    grid_ready_day: int = 0,
    commissioning_lag_days: int = 0,
) -> float:
    """Conditional energy opportunity under progressive per-turbine commissioning.

    Identical turbine AC ratings are assumed. A completed installation can
    generate no earlier than the next day, a uniform commissioning lag, and
    the common grid-ready day. This is an *opportunity envelope*, NOT measured
    generation, lost energy, contractual revenue or confirmed access to grid.
    """
    if (
        not isinstance(horizon_days, int)
        or isinstance(horizon_days, bool)
        or horizon_days <= 0
        or not isinstance(grid_ready_day, int)
        or isinstance(grid_ready_day, bool)
        or grid_ready_day < 0
        or not isinstance(commissioning_lag_days, int)
        or isinstance(commissioning_lag_days, bool)
        or commissioning_lag_days < 0
    ):
        raise ValueError("Horizon, grid-ready day and commissioning lag must be valid days")
    if (
        not math.isfinite(project_capacity_mw)
        or project_capacity_mw <= 0
        or not math.isfinite(net_capacity_factor)
        or not 0 < net_capacity_factor <= 1
    ):
        raise ValueError("Project capacity and capacity factor must be valid")
    if not schedule.completion_days:
        raise ValueError("At least one installed turbine is required")
    if any(day < 0 or day >= schedule.duration_days for day in schedule.completion_days):
        raise ValueError("Invalid completion day in installation schedule")
    turbine_mw = project_capacity_mw / len(schedule.completion_days)
    turbine_days = sum(
        max(0, horizon_days - max(grid_ready_day, day + 1 + commissioning_lag_days))
        for day in schedule.completion_days
    )
    return turbine_days * 24.0 * turbine_mw * net_capacity_factor
