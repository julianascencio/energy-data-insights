"""Hourly export clipping and decision-date cash flows for lifetime scenarios."""

import numpy as np
import pandas as pd
from numpy.typing import ArrayLike


def lifetime_intervention(
    dc_profile_mw: ArrayLike,
    retention: ArrayLike,
    *,
    ac_limit_mw: float,
    availability: ArrayLike,
    price_per_mwh: float,
    annual_opex: float,
    upfront_cost: float,
    discount_rate: float,
) -> pd.DataFrame:
    """Repeat 8760 hourly DC powers for each annual mean retention multiplier.

    Availability uniformly derates energy after hourly clipping. Operating cash
    arrives at year end; upfront expenditure occurs at decision time zero.
    Prices and discount rates must share a real or nominal convention.
    """
    profile = np.asarray(dc_profile_mw, dtype=float)
    power = np.asarray(retention, dtype=float)
    uptime = np.asarray(availability, dtype=float)
    scalars = np.array([ac_limit_mw, price_per_mwh, annual_opex, upfront_cost, discount_rate])
    if profile.shape != (8760,) or power.ndim != 1 or not power.size:
        raise ValueError("Supply 8760 powers and a nonempty annual retention vector")
    if uptime.shape != power.shape:
        raise ValueError("Availability must match retention")
    if not all(np.isfinite(x).all() for x in (profile, power, uptime, scalars)):
        raise ValueError("Inputs must be finite")
    if np.any(profile < 0) or np.any(power < 0) or np.any((uptime < 0) | (uptime > 1)):
        raise ValueError("Power must be nonnegative and availability within [0, 1]")
    if ac_limit_mw <= 0 or annual_opex < 0 or upfront_cost < 0 or discount_rate <= -1:
        raise ValueError("Invalid limit, costs or discount rate")
    energy = np.minimum(profile[:, None] * power, ac_limit_mw).sum(axis=0) * uptime
    year = np.arange(1, len(power) + 1)
    discounted = (energy * price_per_mwh - annual_opex) / (1 + discount_rate) ** year
    return pd.DataFrame(
        {
            "year": year,
            "energy_mwh": energy,
            "cumulative_energy_mwh": energy.cumsum(),
            "discounted_operating_cash": discounted,
            "cumulative_discounted_cash": discounted.cumsum() - upfront_cost,
        }
    )
