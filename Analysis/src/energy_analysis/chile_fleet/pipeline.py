"""Leakage-safe per-site fitting, hourly screens and fleet accounting."""

from __future__ import annotations

import importlib.metadata
import math
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from energy_methods.acceptance_band import (
    FittedAcceptanceBand,
    fit_acceptance_band,
    performance_ratio,
    pr_acceptance_mask,
)
from energy_methods.lightgbm import LightGBMConfig, fit_lightgbm
from energy_methods.metrics import energy_metrics
from energy_methods.physics import PhysicsConfig, fit_physics_model
from energy_methods.poa import Geometry, fit_effective_poa, shift_weather, solar_elevation_midpoint
from energy_methods.status import classify_status
from energy_methods.tdp import TDPConfig, analyze_tdp

from .config import FleetConfig
from .fleet import ComparisonConfig, compare_site, summarize_fleet
from .io import (
    SiteDataSource,
    fingerprint,
    load_sites,
    row_mapping,
    validate_output_location,
    write_fleet_csv,
    write_json,
)

FloatArray = NDArray[np.float64]


class PredictiveModel(Protocol):
    @property
    def training_scale_mwh(self) -> float: ...

    def predict(self, poa_wm2: FloatArray, temperature_c: FloatArray) -> FloatArray: ...

    def weather_support(
        self, poa_wm2: FloatArray, temperature_c: FloatArray
    ) -> NDArray[np.bool_]: ...

    def to_dict(self) -> dict[str, object]: ...


@dataclass(slots=True)
class StageResult:
    expected: FloatArray
    poa: FloatArray
    elevation: FloatArray
    temperature: FloatArray
    accepted: NDArray[np.bool_]
    supported: NDArray[np.bool_]
    model: PredictiveModel | None
    band: FittedAcceptanceBand | None
    provenance: dict[str, object]


def _number(metadata: dict[str, object], key: str) -> float:
    value = metadata.get(key)
    return float(value) if isinstance(value, (int, float, np.number)) else math.nan


def _geometry_candidates(metadata: dict[str, object]) -> tuple[Geometry, ...]:
    rack = str(metadata.get("racking_type", "")).lower()
    tilt = _number(metadata, "tilt_deg")
    azimuth = _number(metadata, "azimuth_deg")
    azimuth = azimuth if math.isfinite(azimuth) else 0.0
    if "track" in rack or "single_axis" in rack:
        return (Geometry(kind="single_axis", axis_azimuth_deg=azimuth),)
    if math.isfinite(tilt):
        return (Geometry(kind="fixed", tilt_deg=tilt, azimuth_deg=azimuth),)
    fixed = tuple(
        Geometry(kind="fixed", tilt_deg=t, azimuth_deg=azimuth) for t in (10.0, 25.0, 40.0)
    )
    return fixed if "fixed" in rack else (*fixed, Geometry(kind="single_axis"))


def _empty_stage(length: int, reason: str) -> StageResult:
    missing = np.full(length, np.nan)
    return StageResult(
        missing.copy(),
        missing.copy(),
        missing.copy(),
        missing.copy(),
        np.zeros(length, dtype=bool),
        np.zeros(length, dtype=bool),
        None,
        None,
        {"status": "withheld", "reason": reason},
    )


def fit_stage(
    frame: pd.DataFrame, metadata: dict[str, object], config: FleetConfig, *, cutoff: pd.Timestamp
) -> StageResult:
    """Fit geometry, acceptance band and generation model strictly before cutoff."""
    timestamps = pd.DatetimeIndex(frame["timestamp"])
    actual = frame["actual_mwh"].to_numpy(dtype=float)
    ghi = frame["ghi_wm2"].to_numpy(dtype=float)
    temperature = frame["temperature_c"].to_numpy(dtype=float)
    latitude, longitude = _number(metadata, "latitude"), _number(metadata, "longitude")
    if (
        not math.isfinite(latitude)
        or not math.isfinite(longitude)
        or not -90 <= latitude <= 90
        or not -180 <= longitude <= 180
    ):
        return _empty_stage(
            len(frame), "Missing or invalid site coordinates; geometry is not guessed"
        )
    train_time = (timestamps >= pd.Timestamp(config.training_start)) & (timestamps < cutoff)
    initial = (
        train_time
        & np.isfinite(actual)
        & (actual >= 0)
        & np.isfinite(ghi)
        & (ghi >= 100)
        & np.isfinite(temperature)
    )
    if initial.sum() < config.minimum_training_hours:
        return _empty_stage(len(frame), "Insufficient reported daylight baseline hours")
    candidates = _geometry_candidates(metadata)
    if not config.fit_geometry:
        candidates = candidates[:1]
    try:
        poa_fit = fit_effective_poa(
            timestamps,
            ghi,
            np.where(train_time, actual, np.nan),
            latitude,
            longitude,
            training_end=cutoff - pd.Timedelta(1, "ns"),
            candidates=candidates,
            lag_hours=config.lag_hours if config.fit_geometry else (0,),
            min_samples=config.minimum_training_hours,
        )
        poa = np.asarray(poa_fit.poa_wm2, dtype=float)
        shifted_temperature = shift_weather(temperature, poa_fit.lag_hours)
        source_time = timestamps - pd.Timedelta(hours=poa_fit.lag_hours)
        source_within_training = (source_time >= pd.Timestamp(config.training_start)) & (
            source_time < cutoff
        )
        eligible = (
            train_time
            & source_within_training
            & np.isfinite(actual)
            & (actual >= 0)
            & np.isfinite(poa)
            & (poa >= 100)
            & np.isfinite(shifted_temperature)
        )
        band = fit_acceptance_band(poa[eligible], actual[eligible])
        accepted = eligible & band.mask(poa, actual)
        qualified_dc = bool(metadata.get("dc_capacity_qualified", False))
        if qualified_dc:
            pr = performance_ratio(actual, poa, _number(metadata, "dc_capacity_mw"))
            accepted &= pr_acceptance_mask(pr)
        if accepted.sum() < config.minimum_training_hours:
            return _empty_stage(
                len(frame),
                "Insufficient training hours after acceptance-band and applicable PR gates",
            )
        if config.algorithm == "lightgbm":
            model: PredictiveModel = fit_lightgbm(
                poa[accepted],
                shifted_temperature[accepted],
                actual[accepted],
                config=LightGBMConfig(
                    n_jobs=config.model_threads, min_samples=config.minimum_training_hours
                ),
            )
        else:
            model = fit_physics_model(
                poa[accepted],
                shifted_temperature[accepted],
                actual[accepted],
                config=PhysicsConfig(min_samples=config.minimum_training_hours),
            )
        expected = np.asarray(model.predict(poa, shifted_temperature), dtype=float)
        supported = np.asarray(model.weather_support(poa, shifted_temperature), dtype=bool)
        provenance: dict[str, object] = {
            "status": "fitted",
            "algorithm": config.algorithm,
            "training_start_inclusive": config.training_start,
            "training_end_exclusive": cutoff.isoformat(),
            "initial_reported_daylight_hours": int(initial.sum()),
            "eligible_transposed_hours": int(eligible.sum()),
            "accepted_training_hours": int(accepted.sum()),
            "geometry": asdict(poa_fit.geometry),
            "lag_hours": poa_fit.lag_hours,
            "geometry_fit_correlation": poa_fit.training_correlation,
            "geometry_fit_rows": poa_fit.training_rows,
            "qualified_dc_pr_filter_applied": qualified_dc,
            "pr_range_inclusive": [0.5, 1.0] if qualified_dc else None,
            "acceptance_band": band.to_dict(),
            "model": model.to_dict(),
        }
        return StageResult(
            expected,
            poa,
            np.asarray(poa_fit.solar_elevation_deg, dtype=float),
            shifted_temperature,
            accepted,
            supported,
            model,
            band,
            provenance,
        )
    except ValueError as error:
        return _empty_stage(len(frame), f"Scientific fit withheld: {error}")


def _hourly_screen(
    frame: pd.DataFrame, stage: StageResult, expected: FloatArray, prefix: str
) -> None:
    bounds = stage.band.bounds(stage.poa) if stage.band is not None else (None, None)
    result = classify_status(
        frame["actual_mwh"].to_numpy(dtype=float),
        expected,
        frame["ghi_wm2"].to_numpy(dtype=float),
        stage.elevation,
        poa_wm2=stage.poa,
        training_scale_mwh=stage.model.training_scale_mwh if stage.model is not None else None,
        weather_supported=stage.supported,
        band_lower_mwh=bounds[0],
        band_upper_mwh=bounds[1],
        timestamps=pd.DatetimeIndex(frame["timestamp"]),
    )
    frame[f"{prefix}_status_code"] = result.codes
    frame[f"{prefix}_status"] = result.labels
    frame[f"{prefix}_envelope_lower_mwh"] = result.envelope_lower_mwh
    frame[f"{prefix}_envelope_upper_mwh"] = result.envelope_upper_mwh
    frame[f"{prefix}_band_state"] = result.band_state
    frame[f"{prefix}_model_band_disagree"] = result.model_band_disagree
    frame[f"{prefix}_near_zero"] = result.near_zero
    frame[f"{prefix}_persistent"] = result.persistent
    frame[f"{prefix}_same_status_run_hours"] = result.run_hours


def _window(frame: pd.DataFrame, site_id: str, config: FleetConfig) -> pd.DataFrame:
    end = max(config.event_start, config.report_end)
    axis = pd.date_range(config.training_start, end, freq="h", inclusive="left", tz="UTC")
    window = frame.set_index("timestamp").reindex(axis).rename_axis("timestamp").reset_index()
    window["site_id"] = site_id
    window["local_date"] = window["timestamp"].dt.tz_convert("America/Santiago").dt.date.astype(str)
    return window


def analyze_site(
    frame: pd.DataFrame, metadata: dict[str, object], config: FleetConfig
) -> tuple[pd.DataFrame, dict[str, object], dict[str, object]]:
    site_id = str(metadata["site_id"])
    hourly = _window(frame, site_id, config)
    test = fit_stage(hourly, metadata, config, cutoff=pd.Timestamp(config.holdout_start))
    final = fit_stage(hourly, metadata, config, cutoff=pd.Timestamp(config.event_start))
    latitude, longitude = _number(metadata, "latitude"), _number(metadata, "longitude")
    if (
        math.isfinite(latitude)
        and math.isfinite(longitude)
        and -90 <= latitude <= 90
        and -180 <= longitude <= 180
    ):
        elevation = solar_elevation_midpoint(
            pd.DatetimeIndex(hourly["timestamp"]), latitude, longitude
        )
        test.elevation = elevation
        final.elevation = elevation
    test_period = (hourly["timestamp"] >= config.holdout_start) & (
        hourly["timestamp"] < config.event_start
    )
    test_expected = np.where(test_period.to_numpy(), test.expected, np.nan)
    hourly["expected_final_mwh"] = final.expected
    hourly["expected_heldout_mwh"] = test_expected
    hourly["expected_mwh"] = final.expected if config.reference == "final" else test_expected
    hourly["final_poa_wm2"] = final.poa
    hourly["heldout_poa_wm2"] = test.poa
    hourly["solar_elevation_deg"] = final.elevation
    hourly["final_training_accepted"] = final.accepted
    hourly["heldout_training_accepted"] = test.accepted
    hourly["final_weather_supported"] = final.supported
    hourly["heldout_weather_supported"] = test.supported
    hourly["final_reference_in_sample"] = hourly["timestamp"] < config.event_start
    _hourly_screen(hourly, final, final.expected, "final")
    _hourly_screen(hourly, test, test_expected, "heldout")
    hourly["iec_operating_cause_confirmed"] = False
    hourly["iec_information_category"] = "INFORMATION UNAVAILABLE (IEC TS 63019:2019 §5.18)"
    report = (hourly["timestamp"] >= config.report_start) & (
        hourly["timestamp"] < config.report_end
    )
    comparison = compare_site(
        hourly.loc[report],
        ComparisonConfig(config.minimum_reference_coverage, config.relative_tolerance),
    )
    validation = energy_metrics(
        hourly.loc[test_period, "actual_mwh"].to_numpy(dtype=float),
        test_expected[test_period.to_numpy()],
    )
    comparison.update(
        {
            "site_id": site_id,
            "name": metadata.get("name", ""),
            "region": metadata.get("region", ""),
            "test_score_pct": validation.score_pct,
            "test_matched_hours": validation.matched_hours,
            "final_fit_status": final.provenance["status"],
            "heldout_fit_status": test.provenance["status"],
        }
    )
    provenance: dict[str, object] = {
        "site_id": site_id,
        "metadata": metadata,
        "final": final.provenance,
        "heldout": test.provenance,
        "heldout_metrics": asdict(validation),
    }
    return hourly, comparison, provenance


def run_fleet(
    config: FleetConfig, *, progress: Callable[[str], None] | None = None
) -> dict[str, object]:
    """Process the entire supplied registry with one site's arrays resident at a time."""
    if config.output_path.exists():
        raise FileExistsError(f"Refusing to overwrite existing run: {config.output_path}")
    validate_output_location(config.output_path, config.hourly_path)
    registry = load_sites(config.sites_path)
    if registry.empty:
        raise ValueError("The site registry is empty")
    source = SiteDataSource(config.hourly_path)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{config.output_path.name}-", dir=config.output_path.parent)
    )
    try:
        for subdirectory in ("hourly", "models", "tdp"):
            (temporary / subdirectory).mkdir()
        comparisons: list[dict[str, object]] = []
        site_outputs: list[dict[str, object]] = []
        for index, metadata in enumerate(row_mapping(registry)):
            site_id = str(metadata["site_id"])
            frame = source.site(site_id)
            hourly, comparison, provenance = analyze_site(frame, metadata, config)
            key = f"site-{index:06d}"
            hourly.to_parquet(
                temporary / "hourly" / f"{key}.parquet", index=False, compression="zstd"
            )
            write_json(temporary / "models" / f"{key}.json", provenance)
            if config.tdp and not frame.empty:
                profiles = analyze_tdp(
                    frame,
                    TDPConfig(
                        utc_offset_hours=-4,
                        min_useful_days=config.tdp_minimum_useful_days,
                        min_hours_per_day=config.tdp_minimum_hours_per_day,
                        min_bin_observations=config.tdp_minimum_bin_observations,
                    ),
                )
                for label, table in (
                    ("avg", profiles.avg),
                    ("y2y", profiles.y2y),
                    ("coverage", profiles.coverage),
                ):
                    table.to_parquet(
                        temporary / "tdp" / f"{key}-{label}.parquet",
                        index=False,
                        compression="zstd",
                    )
            comparisons.append(comparison)
            site_outputs.append(
                {
                    "site_id": site_id,
                    "key": key,
                    "input_hours": len(frame),
                    "classified_hours_per_reference": len(hourly),
                }
            )
            if progress is not None:
                progress(f"Processed {index + 1}/{len(registry)}: {site_id}")
        fleet = pd.DataFrame(comparisons)
        write_fleet_csv(fleet, temporary / "fleet.csv")
        fleet.to_parquet(temporary / "fleet.parquet", index=False, compression="zstd")
        summary = summarize_fleet(fleet)
        write_json(temporary / "summary.json", summary)
        versions = {
            name: importlib.metadata.version(name)
            for name in (
                "energy-analysis",
                "energy-methods",
                "energy-data-retrieval",
                "numpy",
                "pandas",
                "pvlib",
                "lightgbm",
            )
        }
        manifest: dict[str, object] = {
            "schema": "energy-data-insights-chile-fleet-run-v1",
            "complete": True,
            "configuration": asdict(config),
            "versions": versions,
            "inputs": {
                "hourly": fingerprint(config.hourly_path, contents=config.hash_inputs),
                "sites": fingerprint(config.sites_path, contents=config.hash_inputs),
            },
            "site_outputs": site_outputs,
            "summary": summary,
            "outputs": [
                {"path": file.relative_to(temporary).as_posix(), **fingerprint(file)}
                for file in sorted(temporary.rglob("*"))
                if file.is_file()
            ],
            "time_conventions": {
                "hourly": "UTC interval start, one elapsed hour",
                "fleet_calendar": "America/Santiago",
                "tdp_clock": "fixed UTC-04",
                "training": (
                    "[event_start - baseline_days*24h, cutoff), "
                    "holdout strictly follows its training cutoff"
                ),
            },
            "interpretation": [
                "Missing observations remain missing; reported zeros remain in energy accounting.",
                "Fleet ratios use matched observations and available reference energy coverage.",
                "Final-model baseline predictions are in-sample; heldout predictions exist only "
                "inside the chronological test interval.",
                "Geometry, lag, acceptance band and generation models are fitted independently "
                "before each cutoff.",
                "LightGBM is explicitly selected; no minimum predictive score is promised.",
                "Operational causes remain unconfirmed; these are IEC-informed screening states, "
                "not verified outages or storm-damage diagnoses.",
                "This workflow refits models and does not assert bit-for-bit reproduction of a "
                "frozen historical model.",
            ],
        }
        write_json(temporary / "manifest.json", manifest)
        temporary.rename(config.output_path)
        return manifest
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
