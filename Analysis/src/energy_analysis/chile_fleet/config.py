"""Explicit time, input and scientific settings for a reproducible fleet run."""

from __future__ import annotations

import math
import tomllib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Literal


def utc_datetime(value: str | datetime) -> datetime:
    """Parse an explicitly offset timestamp; never guess a civil-clock timezone."""
    result = (
        datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else value
    )
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError(
            "Timestamps require an explicit UTC offset, for example 2026-10-26T03:00:00Z"
        )
    return result.astimezone(UTC)


@dataclass(frozen=True, slots=True)
class FleetConfig:
    """Half-open UTC periods; the event boundary never belongs to training."""

    hourly_path: Path
    sites_path: Path
    output_path: Path
    event_start: datetime
    report_start: datetime
    report_end: datetime
    baseline_days: int = 90
    holdout_days: int = 14
    algorithm: Literal["physics", "lightgbm"] = "physics"
    reference: Literal["final", "heldout"] = "final"
    minimum_training_hours: int = 48
    minimum_reference_coverage: float = 0.8
    relative_tolerance: float = 0.2
    fit_geometry: bool = True
    lag_hours: tuple[int, ...] = (-2, -1, 0, 1, 2)
    model_threads: int = 1
    tdp: bool = True
    tdp_minimum_useful_days: int = 15
    tdp_minimum_hours_per_day: int = 24
    tdp_minimum_bin_observations: int = 10
    hash_inputs: bool = True

    def __post_init__(self) -> None:
        for name in ("event_start", "report_start", "report_end"):
            object.__setattr__(self, name, utc_datetime(getattr(self, name)))
        if any(
            value.minute or value.second or value.microsecond
            for value in (
                self.event_start,
                self.report_start,
                self.report_end,
            )
        ):
            raise ValueError("Time boundaries must fall exactly on elapsed-hour boundaries")
        if self.report_start >= self.report_end:
            raise ValueError("report_start must precede the exclusive report_end")
        if not 0 < self.holdout_days < self.baseline_days:
            raise ValueError("Require 0 < holdout_days < baseline_days")
        if (
            not math.isfinite(self.minimum_reference_coverage)
            or not 0 <= self.minimum_reference_coverage <= 1
        ):
            raise ValueError("minimum_reference_coverage must be in [0, 1]")
        if not math.isfinite(self.relative_tolerance) or not 0 <= self.relative_tolerance < 1:
            raise ValueError("relative_tolerance must be in [0, 1)")
        if self.algorithm not in {"physics", "lightgbm"} or self.reference not in {
            "final",
            "heldout",
        }:
            raise ValueError("Unsupported model algorithm or reference")
        if self.minimum_training_hours < 8 or not 1 <= self.model_threads <= 32:
            raise ValueError("Use at least eight training hours and 1..32 model threads")
        if not self.lag_hours or any(abs(lag) > 6 for lag in self.lag_hours):
            raise ValueError("lag_hours must contain integer shifts between -6 and 6")
        if any(not isinstance(lag, int) or isinstance(lag, bool) for lag in self.lag_hours):
            raise ValueError("lag_hours must contain integer shifts")
        if self.report_start < self.training_start:
            raise ValueError("The report cannot precede the configured baseline window")

    @property
    def training_start(self) -> datetime:
        return self.event_start - timedelta(days=self.baseline_days)

    @property
    def holdout_start(self) -> datetime:
        return self.event_start - timedelta(days=self.holdout_days)


def load_config(path: Path) -> FleetConfig:
    """Read a TOML ``[chile_fleet]`` table, resolving file paths beside it."""
    with path.open("rb") as stream:
        document = tomllib.load(stream)
    values = document.get("chile_fleet", {})
    if not isinstance(values, dict):
        raise ValueError("Expected a [chile_fleet] table")
    valid = set(FleetConfig.__dataclass_fields__)
    unknown = set(values) - valid
    if unknown:
        raise ValueError(f"Unknown configuration keys: {', '.join(sorted(unknown))}")
    base = path.resolve().parent
    for name in ("hourly_path", "sites_path", "output_path"):
        value = values.get(name)
        if not isinstance(value, str):
            raise ValueError(f"{name} must be a path string")
        values[name] = (base / value).resolve()
    for name in ("event_start", "report_start", "report_end"):
        value = values.get(name)
        if not isinstance(value, (str, datetime)):
            raise ValueError(f"{name} requires an offset-aware ISO timestamp")
        values[name] = utc_datetime(value)
    if "lag_hours" in values:
        values["lag_hours"] = tuple(values["lag_hours"])

    def integer(name: str, default: int) -> int:
        value = values.get(name, default)
        if not isinstance(value, int) or isinstance(value, bool):
            raise ValueError(f"{name} must be an integer")
        return value

    def number(name: str, default: float) -> float:
        value = values.get(name, default)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"{name} must be numeric")
        return float(value)

    def boolean(name: str, default: bool) -> bool:
        value = values.get(name, default)
        if not isinstance(value, bool):
            raise ValueError(f"{name} must be true or false")
        return value

    algorithm = values.get("algorithm", "physics")
    reference = values.get("reference", "final")
    if algorithm not in {"physics", "lightgbm"} or reference not in {"final", "heldout"}:
        raise ValueError("Invalid algorithm or reference")
    lags = values.get("lag_hours", (-2, -1, 0, 1, 2))
    if not isinstance(lags, tuple) or not all(isinstance(v, int) for v in lags):
        raise ValueError("lag_hours must contain integers")
    return FleetConfig(
        hourly_path=values["hourly_path"],
        sites_path=values["sites_path"],
        output_path=values["output_path"],
        event_start=values["event_start"],
        report_start=values["report_start"],
        report_end=values["report_end"],
        baseline_days=integer("baseline_days", 90),
        holdout_days=integer("holdout_days", 14),
        algorithm="lightgbm" if algorithm == "lightgbm" else "physics",
        reference="heldout" if reference == "heldout" else "final",
        minimum_training_hours=integer("minimum_training_hours", 48),
        minimum_reference_coverage=number("minimum_reference_coverage", 0.8),
        relative_tolerance=number("relative_tolerance", 0.2),
        fit_geometry=boolean("fit_geometry", True),
        lag_hours=lags,
        model_threads=integer("model_threads", 1),
        tdp=boolean("tdp", True),
        tdp_minimum_useful_days=integer("tdp_minimum_useful_days", 15),
        tdp_minimum_hours_per_day=integer("tdp_minimum_hours_per_day", 24),
        tdp_minimum_bin_observations=integer("tdp_minimum_bin_observations", 10),
        hash_inputs=boolean("hash_inputs", True),
    )
