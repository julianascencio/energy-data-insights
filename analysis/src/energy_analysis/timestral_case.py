"""Reproducible 24-hour Timestral demonstration on an attributed EIA capture.

Input: hourly CISO system generation, not individual plant SCADA. Method:
joint solar/wind prediction using history and known calendar covariates only.
Analysis: one chronological holdout against persistence and daily persistence.
This is a small software demonstration, not a validated forecasting benchmark.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from energy_data_retrieval.sources.eia import parse_balance_csv
from energy_methods._arrays import FloatArray, utc_index
from energy_methods.timestral import TimestralConnector, TimestralForecast

HORIZON = 24
FUEL_TYPES = ("SUN", "WND")
SAMPLE_NAME = "generation_eia_ciso_2024.csv"
SNAPSHOT_NAME = "timestral_ciso_forecast.json"
PROVENANCE_NAME = "timestral_ciso_provenance.json"


@dataclass(frozen=True)
class TimestralCase:
    """Audited observations and disjoint model context/verification arrays."""

    profiles: pd.DataFrame
    context: FloatArray
    actual: FloatArray
    known_covariates: FloatArray
    source_sha256: str

    @property
    def context_sha256(self) -> str:
        """Stable little-endian float64 digest of the target context."""
        return hashlib.sha256(self.context.astype("<f8").tobytes()).hexdigest()

    @property
    def covariates_sha256(self) -> str:
        """Digest of calendar inputs including the known forecast horizon."""
        return hashlib.sha256(self.known_covariates.astype("<f8").tobytes()).hexdigest()


def load_timestral_case(data_directory: str | Path) -> TimestralCase:
    """Verify the existing EIA source checksum and enforce consecutive UTC hours."""
    directory = Path(data_directory)
    raw = (directory / SAMPLE_NAME).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    source = json.loads(
        (directory / f"{SAMPLE_NAME.removesuffix('.csv')}.provenance.json").read_text()
    )
    if digest != source["sample_sha256"]:
        raise ValueError("EIA source checksum does not match provenance")
    frame = parse_balance_csv(raw.decode(), respondents=["CISO"], fuel_types=list(FUEL_TYPES))
    profiles = frame.pivot(index="timestamp", columns="fueltype", values="value")
    profiles = profiles.loc[:, list(FUEL_TYPES)].sort_index()
    profiles.index = utc_index(pd.DatetimeIndex(profiles.index), regular_hourly=True)
    if len(profiles) != 168 or not np.isfinite(profiles.to_numpy()).all():
        raise ValueError("This case requires 168 complete hours of solar and wind observations")
    values = profiles.to_numpy(dtype=np.float64).T
    # Daily UTC clock harmonics are known in advance; no future generation or
    # subsequently observed weather is used as a covariate.
    phase = 2 * np.pi * pd.DatetimeIndex(profiles.index).hour.to_numpy() / 24
    known = np.stack([np.sin(phase), np.cos(phase)])[None, ...]
    return TimestralCase(
        profiles, values[None, :, :-HORIZON].copy(), values[:, -HORIZON:].copy(), known, digest
    )


def forecast_timestral_case(
    case: TimestralCase, connector: TimestralConnector
) -> TimestralForecast:
    """Run real model inference on history only; verification data never enter it."""
    return connector.forecast(case.context, HORIZON, known_covariates=case.known_covariates)


def load_timestral_snapshot(data_directory: str | Path, case: TimestralCase) -> TimestralForecast:
    """Read saved real inference, checking the output and all model-input digests."""
    directory = Path(data_directory)
    manifest = json.loads((directory / PROVENANCE_NAME).read_text())
    raw = (directory / SNAPSHOT_NAME).read_bytes()
    expected = {
        "source_sha256": case.source_sha256,
        "context_sha256": case.context_sha256,
        "known_covariates_sha256": case.covariates_sha256,
        "forecast_sha256": hashlib.sha256(raw).hexdigest(),
    }
    if any(manifest.get(key) != digest for key, digest in expected.items()):
        raise ValueError(
            "Timestral snapshot/input checksums differ; explicitly regenerate the example"
        )
    snapshot = json.loads(raw)
    result = TimestralForecast(
        np.asarray(snapshot["quantiles"]), tuple(snapshot["quantile_levels"])
    )
    if result.quantiles.shape[:3] != (1, len(FUEL_TYPES), HORIZON):
        raise ValueError("Timestral snapshot has an unexpected batch, target or horizon")
    return result


def evaluate_timestral_case(case: TimestralCase, forecast: TimestralForecast) -> pd.DataFrame:
    """MAE/RMSE/WAPE plus empirical 80% interval coverage, independently per fuel."""
    if forecast.median.shape != (1, len(FUEL_TYPES), HORIZON):
        raise ValueError("Forecast does not match the case targets and horizon")
    predictions = {
        "Timestral median": forecast.median[0],
        "Previous day": case.context[0, :, -HORIZON:],
        "Last observation": np.repeat(case.context[0, :, -1:], HORIZON, axis=-1),
    }
    rows = []
    for name, prediction in predictions.items():
        for i, fuel in enumerate(FUEL_TYPES):
            # EIA reports signed net generation (including negative solar at
            # night). Evaluate the same complete holdout for every model; the
            # PV-specific energy_metrics helper intentionally excludes negatives
            # and would produce different, unfair subsets here.
            residual = prediction[i] - case.actual[i]
            denominator = float(np.abs(case.actual[i]).sum())
            coverage = np.nan
            if name == "Timestral median":
                coverage = float(
                    np.mean(
                        (case.actual[i] >= forecast.quantile(0.1)[0, i])
                        & (case.actual[i] <= forecast.quantile(0.9)[0, i])
                    )
                )
            rows.append(
                {
                    "model": name,
                    "fuel": fuel,
                    "hours": HORIZON,
                    "mae_mwh": float(np.abs(residual).mean()),
                    "rmse_mwh": float(np.sqrt(np.mean(residual**2))),
                    "wape_pct": (
                        None
                        if denominator == 0
                        else float(np.abs(residual).sum()) / denominator * 100
                    ),
                    "p10_p90_coverage": coverage,
                }
            )
    return pd.DataFrame(rows)
