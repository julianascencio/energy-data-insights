"""Typical Daily Profiles, DOI 10.1016/j.solener.2021.07.007.

AVG pools original observations by month/hour across eligible year-months;
Y2Y preserves year/month/hour. P90 is the empirical 90th percentile of hourly
observations, not an annual-energy 90% exceedance estimate.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

from energy_methods._arrays import FloatArray, IntArray, epoch_ns, utc_index


@dataclass(frozen=True, slots=True)
class TDPConfig:
    value_column: str = "actual_mwh"
    utc_offset_hours: float = 0.0
    min_useful_days: int = 15
    min_hours_per_day: int = 24
    min_bin_observations: int = 10
    nonnegative: bool = True
    screen_positive_flat: bool = True
    flat_tolerance: float = 1e-9

    def __post_init__(self) -> None:
        if not -14 <= self.utc_offset_hours <= 14:
            raise ValueError("Fixed UTC offset must lie in [-14,14] hours")
        if not 1 <= self.min_hours_per_day <= 24:
            raise ValueError("Useful-day coverage must lie in [1,24]")
        if self.min_useful_days < 1 or self.min_bin_observations < 1:
            raise ValueError("Coverage thresholds must be positive")
        if not np.isfinite(self.flat_tolerance) or self.flat_tolerance < 0:
            raise ValueError("Flat-day tolerance must be finite and nonnegative")


@dataclass(frozen=True, slots=True)
class TDPResult:
    avg: pd.DataFrame
    y2y: pd.DataFrame
    coverage: pd.DataFrame
    config: TDPConfig


PROFILE_COLUMNS = [
    "site_id",
    "year",
    "month",
    "hour",
    "n",
    "p50",
    "p90",
    "raw_n",
    "raw_p50",
    "raw_p90",
    "eligible_month",
    "useful_days",
]


def _quantiles(matrix: FloatArray, minimum: int) -> tuple[IntArray, FloatArray]:
    counts = np.isfinite(matrix).sum(axis=0).astype(np.int64)
    quantiles = np.full((2, 24), np.nan)
    if len(matrix):
        with warnings.catch_warnings():
            warnings.filterwarnings(
                "ignore", message="All-NaN slice encountered", category=RuntimeWarning
            )
            quantiles = np.nanquantile(matrix, (0.5, 0.9), axis=0, method="linear")
        quantiles[:, counts < minimum] = np.nan
    return counts, quantiles


def _profile_rows(
    site_id: str,
    year: int | None,
    month: int,
    selected: FloatArray,
    raw: FloatArray,
    useful_days: int,
    config: TDPConfig,
) -> list[dict[str, object]]:
    count, quantiles = _quantiles(selected, config.min_bin_observations)
    raw_count, raw_quantiles = _quantiles(raw, config.min_bin_observations)
    return [
        {
            "site_id": site_id,
            "year": year,
            "month": month,
            "hour": hour,
            "n": int(count[hour]),
            "p50": float(quantiles[0, hour]),
            "p90": float(quantiles[1, hour]),
            "raw_n": int(raw_count[hour]),
            "raw_p50": float(raw_quantiles[0, hour]),
            "raw_p90": float(raw_quantiles[1, hour]),
            "eligible_month": bool(len(selected)),
            "useful_days": useful_days,
        }
        for hour in range(24)
    ]


DEFAULT_CONFIG = TDPConfig()


def analyze_tdp(hourly: pd.DataFrame, config: TDPConfig = DEFAULT_CONFIG) -> TDPResult:
    """Compute full-precision TDPs independently per site without imputing energy.

    Input requires site_id, timezone-aware timestamp and config.value_column.
    Each observation is one elapsed-hour mean or energy interval. Positive-flat
    screening additionally requires solar_elevation_deg for all 24 day slots;
    without it the screen is explicitly unavailable. Historical net-capacity and
    PR gates are not inferred from undated present-day capacity.
    """
    required = {"site_id", "timestamp", config.value_column}
    if not required.issubset(hourly.columns):
        raise ValueError(f"Missing TDP columns: {sorted(required - set(hourly.columns))}")
    if hourly["site_id"].isna().any():
        raise ValueError("TDP site identifiers must not be missing")
    avg_rows: list[dict[str, object]] = []
    year_rows: list[dict[str, object]] = []
    audits: list[dict[str, object]] = []
    for site_key, group in hourly.groupby("site_id", sort=True, observed=True):
        site_id = str(site_key)
        group = group.sort_values("timestamp")
        times = utc_index(pd.DatetimeIndex(group["timestamp"]))
        if np.any(epoch_ns(times) % 3_600_000_000_000):
            raise ValueError("TDP input timestamps must be UTC-aligned hourly interval starts")
        values = np.asarray(group[config.value_column], dtype=np.float64)
        valid = np.isfinite(values)
        if config.nonnegative:
            valid &= values >= 0
        local = (times + pd.Timedelta(hours=config.utc_offset_hours)).tz_localize(None)
        days = pd.date_range(local[0].normalize(), local[-1].normalize(), freq="D")
        day_index = np.asarray((local.normalize() - days[0]).days, dtype=np.int64)
        slots = day_index * 24 + np.asarray(local.hour, dtype=np.int64)
        if len(np.unique(slots)) != len(slots):
            raise ValueError("Duplicate site/hour input after applying the fixed profile clock")
        dense = np.full((len(days), 24), np.nan)
        dense.ravel()[slots[valid]] = values[valid]
        observed = np.zeros((len(days), 24), dtype=np.bool_)
        observed.ravel()[slots] = True
        finite = np.isfinite(dense)
        useful = finite.sum(axis=1) >= config.min_hours_per_day
        flat_positive = np.zeros(len(days), dtype=np.bool_)
        flat_zero = np.zeros(len(days), dtype=np.bool_)
        flat_status = "disabled_for_this_variable"
        if config.screen_positive_flat:
            flat_status = "unavailable_no_complete_solar_elevation"
            if "solar_elevation_deg" in group:
                elevation = np.full_like(dense, np.nan)
                elevation.ravel()[slots] = np.asarray(
                    group["solar_elevation_deg"], dtype=np.float64
                )
                known = np.isfinite(elevation).all(axis=1)
                daylight = elevation > 0
                daytime = daylight & finite
                expected, seen = daylight.sum(axis=1), daytime.sum(axis=1)
                enough = known & (seen >= 4) & (seen >= np.ceil(expected * 0.75))
                low = np.where(daytime, dense, np.inf).min(axis=1)
                high = np.where(daytime, dense, -np.inf).max(axis=1)
                flat_positive = enough & (high > 0) & ((high - low) <= config.flat_tolerance)
                flat_zero = enough & (high == 0) & (low == 0)
                if known.any():
                    flat_status = "applied_where_solar_elevation_complete"
        useful &= ~flat_positive
        year, month = np.asarray(days.year), np.asarray(days.month)
        tokens = year * 100 + month
        accepted = np.zeros(len(days), dtype=np.bool_)
        eligible_months = 0
        source_days = observed.any(axis=1)
        for token in np.unique(tokens[source_days]):
            where = tokens == token
            selected = where & useful
            useful_days = int(selected.sum())
            eligible = useful_days >= config.min_useful_days
            if eligible:
                accepted |= selected
                eligible_months += 1
            selected_matrix = dense[selected] if eligible else np.empty((0, 24), dtype=np.float64)
            yy, mm = divmod(int(token), 100)
            year_rows.extend(
                _profile_rows(site_id, yy, mm, selected_matrix, dense[where], useful_days, config)
            )
        for mm in np.unique(month[source_days]):
            where = month == mm
            selected = where & accepted
            avg_rows.extend(
                _profile_rows(
                    site_id,
                    None,
                    int(mm),
                    dense[selected],
                    dense[where],
                    int(selected.sum()),
                    config,
                )
            )
        audits.append(
            {
                "site_id": site_id,
                "source_hours": len(values),
                "valid_hours": int(valid.sum()),
                "reported_zero_hours": int(np.sum(valid & (values == 0))),
                "invalid_or_missing_hours": int((~valid).sum()),
                "useful_days": int(useful.sum()),
                "qualified_days": int(accepted.sum()),
                "qualified_hours": int(finite[accepted].sum()),
                "eligible_year_months": eligible_months,
                "positive_flat_days_removed": int(flat_positive.sum()),
                "flat_zero_days_retained": int(flat_zero.sum()),
                "positive_flat_screen": flat_status,
                "utc_offset_hours": config.utc_offset_hours,
                "historical_net_capacity_filter": "unavailable_without_verified_dated_capacity",
                "net_pr": "not_established_by_this_hourly_profile_method",
            }
        )
    return TDPResult(
        pd.DataFrame(avg_rows, columns=PROFILE_COLUMNS).drop(columns="year"),
        pd.DataFrame(year_rows, columns=PROFILE_COLUMNS),
        pd.DataFrame(audits),
        config,
    )
