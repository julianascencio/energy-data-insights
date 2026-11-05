"""AEMET seasonal bias adjustment and explicit mono-Si degradation scenarios.

Meteorological calibration is distinct from module degradation calibration.
No fitted irradiance/UV or measured field degradation is claimed.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import transform

from energy_methods.degradation import DegradationParameters, degradation_rates
from energy_methods.degradation_weather import faiman_from_ghi
from energy_methods.weather_calibration import (
    VARIABLES,
    correct_hourly,
    fit_monthly_bias,
    spatial_weights,
)

RATE_NAMES = ("hydrolysis", "photodegradation", "thermomechanical", "total")


def weather_node(latitude: float, longitude: float) -> str:
    """Match acquisition's explicitly requested 0.25-degree nodes."""
    return f"{np.round(latitude * 4) / 4:.2f}_{np.round(longitude * 4) / 4:.2f}"


def read_weather(folder: Path, slug: str) -> pd.DataFrame:
    """Read captured, checksum-verified aligned hourly weather."""
    meta = json.loads((folder / "weather" / f"{slug}.json").read_text())
    frames = []
    for item in meta["files"]:
        path = folder / "weather" / item["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("ERA5 weather checksum mismatch")
        frames.append(pd.read_csv(path, parse_dates=["timestamp"]))
    frame = pd.concat(frames, ignore_index=True).set_index("timestamp")
    frame.index = pd.to_datetime(frame.index, utc=True)
    expected = pd.date_range("2022-01-01", "2024-01-01", inclusive="left", freq="h", tz="UTC")
    if not frame.index.equals(expected):
        raise ValueError("Two complete hourly years required")
    required = [*VARIABLES, "ghi_wm2"]
    if not np.isfinite(frame[required].to_numpy(dtype=float)).all():
        raise ValueError("Missing hourly drivers; no gap filling")
    if ((frame.relative_humidity_percent < 0) | (frame.relative_humidity_percent > 100)).any():
        raise ValueError("Invalid relative humidity")
    if (frame[["ghi_wm2", "wind_speed_ms"]] < 0).any().any():
        raise ValueError("Negative irradiance or wind")
    return frame


def daily_pairs(observations: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Pair native daily date labels with declared UTC-day model aggregates.

    AEMET tmed is matched to model (daily Tmin+Tmax)/2, not hourly mean T.
    Daily sampling/period differences remain a limitation; validation is also
    reported on monthly averages, rather than claiming hourly validation.
    """
    model = weather[list(VARIABLES)].resample("D").mean()
    daily_t = weather.temperature_c.resample("D")
    model["temperature_c"] = (daily_t.min() + daily_t.max()) / 2
    model.index = pd.DatetimeIndex(model.index).strftime("%Y-%m-%d")
    records = []
    aliases = {
        "tmed": "temperature_c",
        "hrMedia": "relative_humidity_percent",
        "velmedia": "wind_speed_ms",
    }
    for source, variable in aliases.items():
        if source not in observations:
            continue
        values = pd.to_numeric(
            observations[source].astype(str).str.replace(",", "."), errors="coerce"
        )
        observed = pd.Series(values.to_numpy(), index=observations.fecha.astype(str))
        if not observed.index.is_unique:
            raise ValueError("Duplicate daily observations")
        joined = pd.DataFrame({"observed": observed, "modelled": model[variable]})
        joined["variable"] = variable
        joined.index.name = "date"
        records.append(joined.reset_index())
    return pd.concat(records, ignore_index=True)


def validate(
    pairs: pd.DataFrame,
    monthly: dict[str, np.ndarray],
    *,
    year: int = 2023,
    hourly_weather: pd.DataFrame | None = None,
) -> list[dict]:
    """Holdout monthly RMSE and paired-day count, never used for fitting."""
    dates = pd.to_datetime(pairs.date)
    data = pairs.loc[dates.dt.year == year].copy()
    data["month"] = pd.to_datetime(data.date).dt.month
    metrics = []
    for variable, correction in monthly.items():
        sample = data.loc[data.variable == variable].dropna(subset=["observed", "modelled"]).copy()
        sample["corrected"] = (
            sample.modelled.to_numpy() * correction[sample.month.to_numpy() - 1]
            if variable == "wind_speed_ms"
            else sample.modelled.to_numpy() + correction[sample.month.to_numpy() - 1]
        )
        if variable == "relative_humidity_percent":
            sample["corrected"] = sample.corrected.clip(0, 100)
            if hourly_weather is not None:
                hourly_month = pd.DatetimeIndex(hourly_weather.index).month.to_numpy() - 1
                corrected_rh = (
                    (hourly_weather.relative_humidity_percent + correction[hourly_month])
                    .clip(0, 100)
                    .resample("D")
                    .mean()
                )
                corrected_rh.index = pd.DatetimeIndex(corrected_rh.index).strftime("%Y-%m-%d")
                sample["corrected"] = sample.date.map(corrected_rh)
        counts = sample.groupby("month").size()
        means = sample.groupby("month")[["observed", "modelled", "corrected"]].mean()
        means = means.loc[counts >= 20]
        if len(means) != 12:
            continue
        raw = means.modelled - means.observed
        adjusted = means.corrected - means.observed
        metrics.append(
            {
                "variable": variable,
                "validation_year": year,
                "paired_days": len(sample),
                "months": len(means),
                "raw_monthly_rmse": float(np.sqrt(np.mean(raw**2))),
                "corrected_monthly_rmse": float(np.sqrt(np.mean(adjusted**2))),
                "raw_mean_bias": float(raw.mean()),
                "corrected_mean_bias": float(adjusted.mean()),
            }
        )
    return metrics


def annual_drivers(weather: pd.DataFrame, *, uv_fraction: float = 0.05) -> dict[str, float]:
    """Full 2023; annual means and mean daily module extrema; explicit UV proxy."""
    expected = pd.date_range("2023-01-01", "2024-01-01", freq="h", inclusive="left", tz="UTC")
    if not weather.index.equals(expected) or not 0 < uv_fraction < 1:
        raise ValueError("Complete 2023 and a physical explicit UV fraction required")
    if not np.isfinite(weather[[*VARIABLES, "ghi_wm2"]].to_numpy(float)).all():
        raise ValueError("Finite full-year weather required")
    t = pd.Series(
        faiman_from_ghi(
            weather.temperature_c.to_numpy(),
            weather.ghi_wm2.to_numpy(),
            weather.wind_speed_ms.to_numpy(),
        ),
        index=weather.index,
    )
    # Preserve mathematical extrema bounds against floating-point reduction noise.
    return {
        "module_temperature_mean_c": float(t.mean()),
        "module_temperature_upper_c": float(max(t.mean(), t.resample("D").max().mean())),
        "module_temperature_lower_c": float(min(t.mean(), t.resample("D").min().mean())),
        "relative_humidity_percent": float(weather.relative_humidity_percent.mean()),
        "uv_dose_kwh_m2": float(weather.ghi_wm2.sum() * uv_fraction / 1000),
        "cycles_per_year": 365.0,
    }


def rate_scenario(
    weather: pd.DataFrame, parameters: DegradationParameters, *, uv_fraction: float = 0.05
) -> dict[str, float]:
    """Published mono-Si scenario; not new field calibration."""
    rates = degradation_rates(
        **annual_drivers(weather, uv_fraction=uv_fraction), parameters=parameters
    )
    return {name: float(getattr(rates, name)) for name in RATE_NAMES}


def run_study(folder: Path, parameter_path: Path) -> dict:
    """Fit station biases, test temporal/spatial transfer, and calculate raster cells."""
    provenance = json.loads((folder / "aemet_provenance.json").read_text())
    station_path = folder / "stations.csv"
    if hashlib.sha256(station_path.read_bytes()).hexdigest() != provenance["station_sha256"]:
        raise ValueError("Station checksum mismatch")
    stations = pd.read_csv(station_path)
    frames = []
    for item in provenance["daily_files"]:
        path = folder / item["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("AEMET daily partition checksum mismatch")
        frames.append(pd.read_csv(path, dtype=str))
    observations = pd.concat(frames, ignore_index=True)
    grid = pd.read_csv(folder / "grid.csv")
    sx, sy = transform("EPSG:4326", "EPSG:32628", stations.longitude, stations.latitude)
    stations["easting"], stations["northing"] = sx, sy
    params = DegradationParameters(**json.loads(parameter_path.read_text()))
    cache = {}
    pairs_by_station = {}
    coefficients = []
    failed = []
    for station in stations.to_dict("records"):
        sid = station["station_id"]
        slug = weather_node(station["latitude"], station["longitude"])
        if slug not in cache:
            cache[slug] = read_weather(folder, slug)
        pairs = daily_pairs(observations.loc[observations.indicativo == sid], cache[slug])
        pairs_by_station[sid] = pairs
        fitted = fit_monthly_bias(pairs, year=2022)
        if fitted.empty:
            failed.append(sid)
            continue
        fitted["station_id"] = sid
        coefficients.append(fitted)
    if not coefficients:
        raise ValueError("No station has twelve supported training months")
    coeff = pd.concat(coefficients, ignore_index=True)
    coeff.to_csv(folder / "calibration_parameters.csv", index=False)
    station_by_id = stations.set_index("station_id")

    def transfer(xy: np.ndarray, *, exclude: str | None = None) -> dict[str, np.ndarray]:
        result = {}
        for variable in VARIABLES:
            rows = coeff.loc[(coeff.variable == variable) & (coeff.station_id != exclude)]
            pivot = rows.pivot(index="station_id", columns="month", values="value")
            if pivot.empty:
                continue
            coordinates = station_by_id.loc[pivot.index, ["easting", "northing"]].to_numpy(float)
            weights = spatial_weights(coordinates, xy)
            values = weights @ pivot.to_numpy(float)
            values[weights.sum(axis=1) == 0] = np.nan
            result[variable] = values
        return result

    validations = []
    for station in stations.to_dict("records"):
        sid = station["station_id"]
        subset = coeff.loc[coeff.station_id == sid]
        own = {
            str(v): g.sort_values("month").value.to_numpy(float)
            for v, g in subset.groupby("variable")
        }
        slug = weather_node(station["latitude"], station["longitude"])
        for metric in validate(pairs_by_station[sid], own, hourly_weather=cache[slug]):
            validations.append({"station_id": sid, "validation": "temporal_holdout", **metric})
        transferred = transfer(np.array([[station["easting"], station["northing"]]]), exclude=sid)
        other = {v: a[0] for v, a in transferred.items() if np.isfinite(a[0]).all()}
        for metric in validate(pairs_by_station[sid], other, hourly_weather=cache[slug]):
            validations.append(
                {"station_id": sid, "validation": "spatial_and_temporal_holdout", **metric}
            )
    validation = pd.DataFrame(validations)
    validation.to_csv(folder / "validation.csv", index=False)
    fields = transfer(grid[["easting", "northing"]].to_numpy(float))
    results = []
    for i, point in enumerate(grid.to_dict("records")):
        monthly = {v: a[i] for v, a in fields.items()}
        supported = len(monthly) == 3 and all(np.isfinite(a).all() for a in monthly.values())
        slug = weather_node(point["latitude"], point["longitude"])
        if slug not in cache:
            cache[slug] = read_weather(folder, slug)
        weather = cache[slug].loc[pd.DatetimeIndex(cache[slug].index).year == 2023].copy()
        record = {**point, "weather_node": slug, "calibration_supported": supported}
        record.update({f"raw_driver_{k}": v for k, v in annual_drivers(weather).items()})
        raw = rate_scenario(weather, params)
        record.update({f"raw_{k}": v for k, v in raw.items()})
        if supported:
            corrected = correct_hourly(weather, monthly)
            record.update(
                {f"corrected_driver_{k}": v for k, v in annual_drivers(corrected).items()}
            )
            rates = rate_scenario(corrected, params)
            record.update({f"corrected_{k}": v for k, v in rates.items()})
            record.update({f"delta_{k}": rates[k] - raw[k] for k in RATE_NAMES})
            record["rh_clipped_hours"] = corrected.attrs["rh_clipped_hours"]
            # Scenario spread, explicitly NOT a statistical confidence interval.
            for fraction in (0.04, 0.06):
                record[f"total_uv_{fraction:.2f}"] = rate_scenario(
                    corrected, params, uv_fraction=fraction
                )["total"]
        results.append(record)
    result = pd.DataFrame(results)
    result.to_csv(folder / "rates.csv", index=False)
    for prefix in ("raw", "corrected", "delta"):
        array = np.full((4, 50, 106), np.nan, dtype="float32")
        for band, name in enumerate(RATE_NAMES):
            if f"{prefix}_{name}" in result:
                array[band, result.row.to_numpy(int), result.col.to_numpy(int)] = result[
                    f"{prefix}_{name}"
                ].to_numpy(float)
        with rasterio.open(
            folder / f"{prefix}_rates.tif",
            "w",
            driver="GTiff",
            height=50,
            width=106,
            count=4,
            dtype="float32",
            crs="EPSG:32628",
            transform=from_origin(160000, 3290000, 5000, 5000),
            nodata=np.nan,
            compress="deflate",
        ) as dst:
            dst.write(array)
            for band, name in enumerate(RATE_NAMES, 1):
                dst.set_band_description(band, f"{prefix}_{name}_percent_per_year")
            dst.update_tags(
                evidence="Published mono-Si scenario; weather bias adjusted",
                accuracy="5 km display; native ERA5 0.25 degrees; not field loss",
            )
    summary = {
        "training_year": 2022,
        "validation_and_map_year": 2023,
        "station_inventory": len(stations),
        "stations_with_coefficients": coeff.station_id.nunique(),
        "station_support_by_variable": coeff.groupby("variable").station_id.nunique().to_dict(),
        "unsupported_stations": failed,
        "grid_cells": len(result),
        "supported_grid_cells": int(result.calibration_supported.sum()),
        "degradation_parameters": params.to_dict(),
        "weather_calibration": "Monthly additive temperature/RH and wind multiplier, 2022 only",
        "spatial_transfer": "IDW nearest four stations within 75 km; no elevation downscaling",
        "radiation": "Uncorrected ERA5 GHI; UV=5% GHI proxy; 4-6% sensitivity is not confidence",
        "module": "GHI-based Faiman, U0=26.9, U1=6.2, 2 m height, open-rack scenario",
        "stress": "Annual mean T/RH, mean daily module extrema, 365 cycles/year; A_N=1",
        "limits": [
            "Daily date/period and station sampling differences remain",
            "Only two years; seasonal means corrected, hourly/extreme skill not established",
            "Spatial transfer may fail at mountains/coasts; inspect spatial holdout validation",
            "Weather correction is not a new module/material calibration",
            "No PID, LID, LeTID, salt corrosion, hail or field-loss measurement inferred",
        ],
        "ranges_percent_per_year": {
            name: [
                float(result[f"corrected_{name}"].min()),
                float(result[f"corrected_{name}"].max()),
            ]
            for name in RATE_NAMES
        },
        "validation": validation.groupby(["validation", "variable"])[
            ["raw_monthly_rmse", "corrected_monthly_rmse"]
        ]
        .mean()
        .reset_index()
        .to_dict("records"),
        "reference_ids": [
            "aemet_opendata_specification",
            "kaaya_2019_degradation",
            "ascencio_vasquez_2019_degradation_mapping",
        ],
    }
    (folder / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
