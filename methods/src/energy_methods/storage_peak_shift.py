"""Auditable renewable-surplus-to-evening-peak battery dispatch.

This energy-balance screening method does not optimize prices, guarantee firm
capacity, or calculate storage obligations under any country's regulation.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class StorageStep:
    """Energy accounting for one timestep (all energy fields in MWh)."""

    charged_input_mwh: float
    delivered_mwh: float
    curtailed_mwh: float
    unmet_peak_mwh: float
    soc_mwh: float


@dataclass(frozen=True)
class StorageShiftResult:
    """Storage shift output with an audit-ready energy-balance trace."""

    steps: tuple[StorageStep, ...]
    peak_shortfall_mwh: float
    peak_delivered_mwh: float
    peak_coverage: float
    curtailed_mwh: float
    final_soc_mwh: float


def simulate_storage_peak_shift(
    surplus_mw: Sequence[float],
    peak_shortfall_mw: Sequence[float],
    *,
    battery_power_mw: float,
    battery_energy_mwh: float,
    round_trip_efficiency: float = 0.9,
    timestep_hours: float = 1.0,
    initial_soc_mwh: float = 0.0,
) -> StorageShiftResult:
    """Charge only from renewable surplus and discharge only into peak shortfall.

    ``surplus_mw`` is renewable generation *remaining after serving contemporaneous
    load*, not total PV generation. ``peak_shortfall_mw`` is the remaining
    evening/peak demand to be covered by storage. Both must be nonnegative, and
    cannot simultaneously be positive. The battery never charges from the grid.

    A greedy sequential schedule is calculated without look-ahead. A single
    symmetric charge/discharge efficiency sqrt(round_trip_efficiency) is used.
    Storage energy capacity represents usable SOC range. Self-discharge,
    degradation, grid export limits, operating reserves and costs are omitted.
    """
    if len(surplus_mw) != len(peak_shortfall_mw) or not surplus_mw:
        raise ValueError("Profiles must be nonempty and have identical lengths")
    params = (battery_power_mw, battery_energy_mwh, initial_soc_mwh)
    if any(not math.isfinite(x) or x < 0 for x in params):
        raise ValueError("Power, energy and initial SOC must be finite and nonnegative")
    if initial_soc_mwh > battery_energy_mwh:
        raise ValueError("Initial SOC cannot exceed storage capacity")
    if not math.isfinite(timestep_hours) or timestep_hours <= 0:
        raise ValueError("Timestep must be finite and positive")
    if not math.isfinite(round_trip_efficiency) or not 0 < round_trip_efficiency <= 1:
        raise ValueError("Round-trip efficiency must be in (0, 1]")
    for surplus, shortfall in zip(surplus_mw, peak_shortfall_mw, strict=True):
        if (
            not math.isfinite(surplus)
            or not math.isfinite(shortfall)
            or surplus < 0
            or shortfall < 0
            or (surplus > 0 and shortfall > 0)
        ):
            raise ValueError("Profiles must be finite, nonnegative and mutually exclusive")

    eta = math.sqrt(round_trip_efficiency)
    soc = initial_soc_mwh
    steps: list[StorageStep] = []
    for surplus, shortfall in zip(surplus_mw, peak_shortfall_mw, strict=True):
        incoming = surplus * timestep_hours
        required = shortfall * timestep_hours
        input_charge = min(
            incoming,
            battery_power_mw * timestep_hours,
            (battery_energy_mwh - soc) / eta,
        )
        soc += input_charge * eta
        delivered = min(required, battery_power_mw * timestep_hours, soc * eta)
        soc -= delivered / eta
        # Remove harmless floating point roundoff near zero and the SOC ceiling.
        soc = min(battery_energy_mwh, max(0.0, soc))
        steps.append(
            StorageStep(
                charged_input_mwh=input_charge,
                delivered_mwh=delivered,
                curtailed_mwh=incoming - input_charge,
                unmet_peak_mwh=required - delivered,
                soc_mwh=soc,
            )
        )
    total_peak = sum(peak_shortfall_mw) * timestep_hours
    total_delivered = sum(step.delivered_mwh for step in steps)
    return StorageShiftResult(
        steps=tuple(steps),
        peak_shortfall_mwh=total_peak,
        peak_delivered_mwh=total_delivered,
        peak_coverage=total_delivered / total_peak if total_peak else 1.0,
        curtailed_mwh=sum(step.curtailed_mwh for step in steps),
        final_soc_mwh=soc,
    )
