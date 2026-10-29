"""Explicit inputs and study settings; scenario names are never probabilities."""

from __future__ import annotations

import math
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    label: str
    historical_path: Path
    projection_path: Path
    source: str

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", self.id):
            raise ValueError("Scenario id requires 1..64 lowercase letters, digits, _ or -")
        if not self.label.strip() or not self.source.strip():
            raise ValueError("Scenario label and model/member/dataset source must be explicit")


@dataclass(frozen=True, slots=True)
class CaseConfig:
    title: str
    data_kind: Literal["synthetic", "observed_and_projected"]
    measured_path: Path
    measured_source: str
    output_path: Path
    scenarios: tuple[Scenario, ...]
    degradation_rates: tuple[float, ...] = (0.0, 0.0025, 0.005, 0.01)
    report_years: tuple[int, ...] = (25, 50)
    plot_degradation_rate: float = 0.005

    def __post_init__(self) -> None:
        if self.data_kind not in {"synthetic", "observed_and_projected"}:
            raise ValueError("data_kind must be synthetic or observed_and_projected")
        if not self.title.strip() or not self.measured_source.strip():
            raise ValueError("Study title and measured_source are required")
        if not 1 <= len(self.scenarios) <= 16:
            raise ValueError("Use 1..16 explicit scenario/member cases")
        if len({s.id for s in self.scenarios}) != len(self.scenarios):
            raise ValueError("Scenario identifiers must be unique")
        rates = self.degradation_rates
        if not 1 <= len(rates) <= 8 or len(set(rates)) != len(rates):
            raise ValueError("Use 1..8 unique degradation rates")
        if any(not math.isfinite(r) or not 0 <= r <= 1 for r in rates):
            raise ValueError("Degradation rates must be finite fractions in [0, 1]")
        if self.plot_degradation_rate not in rates:
            raise ValueError("plot_degradation_rate must be one of degradation_rates")
        if not self.report_years or len(set(self.report_years)) != len(self.report_years):
            raise ValueError("report_years must contain unique operating years")
        if any(isinstance(y, bool) or not isinstance(y, int) or y < 1 for y in self.report_years):
            raise ValueError("report_years must contain positive integer operating years")


def load_config(path: Path) -> CaseConfig:
    """Load strict TOML; resolve local CSV and output paths beside the config."""
    document = tomllib.loads(path.read_text(encoding="utf-8"))
    if set(document) != {"ccya", "scenarios"}:
        raise ValueError("Configuration must contain [ccya] and [[scenarios]] only")
    values, scenarios = document["ccya"], document["scenarios"]
    if not isinstance(values, dict) or not isinstance(scenarios, list):
        raise ValueError("Invalid CCYA configuration structure")
    if set(values) - (set(CaseConfig.__dataclass_fields__) - {"scenarios"}):
        raise ValueError("Unknown [ccya] configuration key")
    base = path.resolve().parent

    def string(row: dict, key: str) -> str:
        value = row.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{key} must be a nonempty string")
        return value

    parsed = []
    for row in scenarios:
        if not isinstance(row, dict) or set(row) != set(Scenario.__dataclass_fields__):
            raise ValueError("Each scenario must provide id, label, paths and source")
        parsed.append(
            Scenario(
                string(row, "id"),
                string(row, "label"),
                (base / string(row, "historical_path")).resolve(),
                (base / string(row, "projection_path")).resolve(),
                string(row, "source"),
            )
        )
    kind = string(values, "data_kind")
    if kind not in {"synthetic", "observed_and_projected"}:
        raise ValueError("data_kind must be synthetic or observed_and_projected")
    rates = values.get("degradation_rates", [0.0, 0.0025, 0.005, 0.01])
    if not isinstance(rates, list) or any(type(v) not in (int, float) for v in rates):
        raise ValueError("degradation_rates must be a numeric array")
    years = values.get("report_years", [25, 50])
    if not isinstance(years, list):
        raise ValueError("report_years must be an integer array")
    plot_rate = values.get("plot_degradation_rate", 0.005)
    if type(plot_rate) not in (int, float):
        raise ValueError("plot_degradation_rate must be numeric")
    return CaseConfig(
        title=string(values, "title"),
        data_kind="synthetic" if kind == "synthetic" else "observed_and_projected",
        measured_path=(base / string(values, "measured_path")).resolve(),
        measured_source=string(values, "measured_source"),
        output_path=(base / string(values, "output_path")).resolve(),
        scenarios=tuple(parsed),
        degradation_rates=tuple(float(v) for v in rates),
        report_years=tuple(years),
        plot_degradation_rate=float(plot_rate),
    )
