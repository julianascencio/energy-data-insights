"""Annual PV operation scenarios with independent, repairable component failures.

A Bernoulli event per component and year represents at most one replacement.
Failure timing is represented by a caller-supplied fractional annual outage.
These are explicit engineering scenarios, not calibrated field failure models.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from energy_methods.pv_reliability import ReliabilityCurve


@dataclass(frozen=True)
class ComponentScenario:
    """Annual failure probability, outage fraction and constant-real replacement cost.

    Replacements restore service but do not reset module degradation. Cost is
    in the caller's declared currency. Failures are independent across years,
    components and simulated plants. Multiple same-year failures are excluded.
    """

    name: str
    annual_failure_probability: float
    outage_fraction: float
    replacement_cost: float

    def __post_init__(self) -> None:
        values = [self.annual_failure_probability, self.outage_fraction, self.replacement_cost]
        if not self.name.strip() or not np.isfinite(values).all():
            raise ValueError("A component name and finite parameters are required")
        if not 0 <= self.annual_failure_probability <= 1 or not 0 <= self.outage_fraction <= 1:
            raise ValueError("Probability and outage fraction must be in [0, 1]")
        if self.replacement_cost < 0:
            raise ValueError("Replacement cost must be nonnegative")


def simulate_operation(
    *,
    curve: ReliabilityCurve,
    initial_annual_energy_mwh: float,
    components: tuple[ComponentScenario, ...],
    years: int = 50,
    trials: int = 1000,
    seed: int = 0,
) -> pd.DataFrame:
    """Return one row per trial/year, using midpoint annual power retention.

    Concurrent component outages are conservatively added and capped at one
    year. No repair queue, seasonality, weather variability or cost discounting
    is modeled. ``original_components_survive`` concerns the original set,
    while replacement permits subsequent operation. Cumulative quantities are
    computed independently for each trial. Zero energy is valid.
    """
    if any(isinstance(v, bool) or not isinstance(v, int) or v < 1 for v in (years, trials)):
        raise ValueError("years and trials must be positive integers")
    if not np.isfinite(initial_annual_energy_mwh) or initial_annual_energy_mwh < 0:
        raise ValueError("initial_annual_energy_mwh must be finite and nonnegative")
    if len({c.name for c in components}) != len(components):
        raise ValueError("Component names must be unique")
    retention = curve.power(np.arange(years) + 0.5)
    if np.any((retention < 0) | (retention > 1)):
        raise ValueError("Power retention must stay in [0, 1] throughout the horizon")
    rng = np.random.default_rng(seed)
    outages = np.zeros((trials, years))
    costs = np.zeros_like(outages)
    counts = np.zeros_like(outages, dtype=int)
    for component in components:
        events = rng.random((trials, years)) < component.annual_failure_probability
        outages += events * component.outage_fraction
        costs += events * component.replacement_cost
        counts += events
    availability = 1 - np.minimum(outages, 1)
    energy = initial_annual_energy_mwh * retention * availability
    cumulative_counts = np.cumsum(counts, axis=1)
    return pd.DataFrame(
        {
            "trial": np.repeat(np.arange(trials), years),
            "year": np.tile(np.arange(1, years + 1), trials),
            "energy_mwh": energy.ravel(),
            "availability": availability.ravel(),
            "replacement_count": counts.ravel(),
            "replacement_cost": costs.ravel(),
            "cumulative_energy_mwh": np.cumsum(energy, axis=1).ravel(),
            "cumulative_replacement_cost": np.cumsum(costs, axis=1).ravel(),
            "original_components_survive": (cumulative_counts == 0).ravel(),
        }
    )
