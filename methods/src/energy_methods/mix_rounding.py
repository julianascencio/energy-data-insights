"""Reconcile rounded energy-consumption shares across nested reporting periods.

Shares are percentages of consumption, not of domestic generation.
Reported-precision envelopes are not probabilistic confidence intervals.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass


@dataclass(frozen=True)
class MonthlyShareInterval:
    """Incremental-month percentage and conservative rounding envelope."""

    central_pct: float
    minimum_pct: float
    maximum_pct: float

    def contains_reported(self, reported_pct: float, *, rounding_pp: float = 0.5) -> bool:
        """Check compatibility with a separately rounded monthly percentage."""
        if not math.isfinite(reported_pct) or not math.isfinite(rounding_pp) or rounding_pp < 0:
            raise ValueError("Reported share and rounding width must be finite and valid")
        return self.minimum_pct <= reported_pct + rounding_pp and (
            self.maximum_pct >= reported_pct - rounding_pp
        )


def infer_incremental_month_share(
    *,
    preceding_demand_twh: float,
    new_month_demand_twh: float,
    preceding_share_pct: float,
    cumulative_share_pct: float,
    share_rounding_pp: float = 0.5,
    preceding_demand_rounding_twh: float = 0.0,
) -> MonthlyShareInterval:
    """Infer monthly share from preceding and updated cumulative shares.

    For preceding demand P, month demand M, preceding share p and cumulative
    share c, the incremental month's percentage is c + (P/M) * (c-p).
    All corner combinations of reported rounding intervals are evaluated.
    Results are marginal bounds, not jointly attainable category balances.
    """
    values = (
        preceding_demand_twh,
        new_month_demand_twh,
        preceding_share_pct,
        cumulative_share_pct,
        share_rounding_pp,
        preceding_demand_rounding_twh,
    )
    if any(not math.isfinite(value) for value in values):
        raise ValueError("Every input must be finite")
    if preceding_demand_twh <= 0 or new_month_demand_twh <= 0:
        raise ValueError("Demand must be positive")
    if (
        preceding_demand_rounding_twh < 0
        or preceding_demand_rounding_twh >= preceding_demand_twh
    ):
        raise ValueError("Invalid preceding demand uncertainty")
    if share_rounding_pp < 0:
        raise ValueError("Rounding width cannot be negative")
    for share in (preceding_share_pct, cumulative_share_pct):
        if (
            not 0 <= share <= 100
            or share - share_rounding_pp < 0
            or share + share_rounding_pp > 100
        ):
            raise ValueError("Shares and rounding intervals must remain inside 0-100%")

    def estimate(demand: float, prior: float, cumulative: float) -> float:
        return cumulative + (demand / new_month_demand_twh) * (cumulative - prior)

    central = estimate(preceding_demand_twh, preceding_share_pct, cumulative_share_pct)
    endpoints = [
        estimate(demand, prior, cumulative)
        for demand, prior, cumulative in itertools.product(
            (
                preceding_demand_twh - preceding_demand_rounding_twh,
                preceding_demand_twh + preceding_demand_rounding_twh,
            ),
            (
                preceding_share_pct - share_rounding_pp,
                preceding_share_pct + share_rounding_pp,
            ),
            (
                cumulative_share_pct - share_rounding_pp,
                cumulative_share_pct + share_rounding_pp,
            ),
        )
    ]
    low, high = min(endpoints), max(endpoints)
    if high < 0 or low > 100:
        raise ValueError("Reported cumulative shares are incompatible with a valid month")
    return MonthlyShareInterval(central, max(0.0, low), min(100.0, high))
