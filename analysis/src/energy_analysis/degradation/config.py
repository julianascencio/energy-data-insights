"""Explicit, bounded degradation study settings; TOML paths are relative to the file."""

from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from energy_methods.degradation import DegradationParameters


@dataclass(frozen=True, slots=True)
class StudyConfig:
    name: str
    start_year: int
    end_year: int
    latitude_min: float
    latitude_max: float
    longitude_min: float
    longitude_max: float
    step_degrees: float
    parameters_path: Path
    cycles_per_day: float
    aggregation: str = "mean_stress"
    u0: float = 26.9
    u1: float = 6.2
    module_height_m: float = 2.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Study name is required")
        if (
            type(self.start_year) is not int
            or type(self.end_year) is not int
            or not 1940 <= self.start_year <= self.end_year <= 2025
        ):
            raise ValueError("Study years must be ordered integers within 1940..2025")
        bounds = [
            self.latitude_min,
            self.latitude_max,
            self.longitude_min,
            self.longitude_max,
            self.step_degrees,
            self.cycles_per_day,
            self.u0,
            self.u1,
            self.module_height_m,
        ]
        if not np.isfinite(bounds).all():
            raise ValueError("Study settings must be finite")
        if not (
            -90 < self.latitude_min < self.latitude_max < 90
            and -180 <= self.longitude_min < self.longitude_max < 180
        ):
            raise ValueError("Ordered geographic cell centres are required; omit duplicate seams")
        if not 0.25 <= self.step_degrees <= 30 or self.cycles_per_day < 0:
            raise ValueError("Grid step must be 0.25..30 degrees and cycles/day nonnegative")
        if self.aggregation not in {"mean_stress", "mean_rate"}:
            raise ValueError("Unknown aggregation")
        if self.u0 <= 0 or self.u1 < 0 or self.module_height_m <= 0:
            raise ValueError("Invalid Faiman parameters")
        for low, high in (
            (self.latitude_min, self.latitude_max),
            (self.longitude_min, self.longitude_max),
        ):
            if not np.isclose(
                (high - low) / self.step_degrees, round((high - low) / self.step_degrees)
            ):
                raise ValueError("Grid span must be an exact multiple of step_degrees")
        if len(self.latitudes) * len(self.longitudes) > 10_000:
            raise ValueError("Study exceeds 10,000 grid cells; use regional configurations")

    @property
    def latitudes(self) -> NDArray[np.float64]:
        return np.linspace(
            self.latitude_min,
            self.latitude_max,
            round((self.latitude_max - self.latitude_min) / self.step_degrees) + 1,
        )

    @property
    def longitudes(self) -> NDArray[np.float64]:
        return np.linspace(
            self.longitude_min,
            self.longitude_max,
            round((self.longitude_max - self.longitude_min) / self.step_degrees) + 1,
        )

    def parameters(self) -> DegradationParameters:
        return DegradationParameters(**json.loads(self.parameters_path.read_text(encoding="utf-8")))


def load_config(path: Path) -> StudyConfig:
    """Read the study section and reject unknown/missing settings via the dataclass."""
    record = tomllib.loads(path.read_text(encoding="utf-8"))["study"]
    record["parameters_path"] = (path.parent / record["parameters_path"]).resolve()
    return StudyConfig(**record)
