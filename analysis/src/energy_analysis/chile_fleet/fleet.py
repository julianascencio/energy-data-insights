"""Matched-energy accounting independent of training and status filters."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class ComparisonConfig:
    minimum_reference_coverage: float = 0.8
    relative_tolerance: float = 0.2

    def __post_init__(self) -> None:
        if not 0 <= self.minimum_reference_coverage <= 1:
            raise ValueError("minimum_reference_coverage must be in [0,1]")
        if not 0 <= self.relative_tolerance < 1:
            raise ValueError("relative_tolerance must be in [0,1)")


DEFAULT_COMPARISON = ComparisonConfig()


def compare_site(
    frame: pd.DataFrame, config: ComparisonConfig = DEFAULT_COMPARISON
) -> dict[str, object]:
    """Sum actual and reference on exactly identical valid nonnegative intervals.

    Acceptance, PR and operational-status masks must never be applied here.
    Coverage measures the available reference-energy denominator, not 24-hour
    observational completeness. Missing expected energy is not inferred.
    """
    actual = frame["actual_mwh"].to_numpy(dtype=float)
    expected = frame["expected_mwh"].to_numpy(dtype=float)
    valid_actual = np.isfinite(actual) & (actual >= 0)
    valid_expected = np.isfinite(expected) & (expected >= 0)
    paired = valid_actual & valid_expected
    actual_sum = float(actual[paired].sum())
    expected_sum = float(expected[paired].sum())
    all_expected = float(expected[valid_expected].sum())
    coverage = expected_sum / all_expected if all_expected > 0 else None
    supported = (
        coverage is not None and coverage >= config.minimum_reference_coverage and expected_sum > 0
    )
    deviation = actual_sum - expected_sum
    percentage = 100 * deviation / expected_sum if supported else None
    group = "insufficient_comparison"
    if supported:
        ratio = actual_sum / expected_sum
        group = (
            "underperforming"
            if ratio < 1 - config.relative_tolerance
            else ("overperforming" if ratio > 1 + config.relative_tolerance else "within_tolerance")
        )
    result: dict[str, object] = {
        "hours_in_window": len(frame),
        "reported_valid_hours": int(valid_actual.sum()),
        "reported_zero_hours": int((valid_actual & (actual == 0)).sum()),
        "negative_or_infinite_actual_hours": int(
            (~np.isnan(actual) & (~np.isfinite(actual) | (actual < 0))).sum()
        ),
        "reference_hours": int(valid_expected.sum()),
        "matched_hours": int(paired.sum()),
        "reported_actual_mwh": float(actual[valid_actual].sum()),
        "available_reference_mwh": all_expected,
        "matched_actual_mwh": actual_sum,
        "matched_expected_mwh": expected_sum,
        "reference_energy_coverage": coverage,
        "comparison_supported": supported,
        "performance_group": group,
        "matched_deviation_mwh": deviation,
        "deviation_pct": percentage,
        "site_shortfall_mwh": max(-deviation, 0.0) if supported else None,
        "site_excess_mwh": max(deviation, 0.0) if supported else None,
        "hourly_shortfall_mwh": float(np.maximum(expected[paired] - actual[paired], 0).sum()),
        "hourly_excess_mwh": float(np.maximum(actual[paired] - expected[paired], 0).sum()),
    }
    for column in ("ghi_wm2", "temperature_c", "wind_speed_ms", "gust_ms"):
        values = (
            frame[column].to_numpy(dtype=float) if column in frame else np.array([], dtype=float)
        )
        valid = np.isfinite(values)
        if column != "temperature_c":
            valid &= values >= 0
        subset = values[valid]
        result[f"{column}_valid_hours"] = int(valid.sum())
        result[f"{column}_minimum"] = float(subset.min()) if len(subset) else None
        result[f"{column}_maximum"] = float(subset.max()) if len(subset) else None
        result[f"{column}_average"] = float(subset.mean()) if len(subset) else None
    return result


def summarize_fleet(sites: pd.DataFrame) -> dict[str, object]:
    """Keep incomplete registry rows in the denominator but out of energy claims."""
    supported = sites.loc[sites["comparison_supported"].eq(True)]
    actual = float(supported["matched_actual_mwh"].sum())
    expected = float(supported["matched_expected_mwh"].sum())
    return {
        "registry_records": len(sites),
        "comparable_records": len(supported),
        "underperforming_records": int(supported["performance_group"].eq("underperforming").sum()),
        "overperforming_records": int(supported["performance_group"].eq("overperforming").sum()),
        "within_tolerance_records": int(
            supported["performance_group"].eq("within_tolerance").sum()
        ),
        "insufficient_comparison_records": len(sites) - len(supported),
        "matched_actual_mwh": actual,
        "matched_expected_mwh": expected,
        "net_deviation_mwh": actual - expected,
        "net_deviation_pct": 100 * (actual / expected - 1) if expected > 0 else None,
        "site_shortfall_mwh": float(supported["site_shortfall_mwh"].sum()),
        "site_excess_mwh": float(supported["site_excess_mwh"].sum()),
        "hourly_shortfall_mwh": float(supported["hourly_shortfall_mwh"].sum()),
        "hourly_excess_mwh": float(supported["hourly_excess_mwh"].sum()),
        "scope": (
            "Matched intervals of comparable registry records only; gaps do not establish "
            "recoverable loss or storm damage."
        ),
    }
