"""Deterministic synthetic examples, explicitly separate from measured Chile data."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

from energy_methods.poa import Geometry, transpose_ghi

from .config import FleetConfig
from .io import write_json


def create_demo(
    output: Path, *, algorithm: Literal["physics", "lightgbm"] = "physics"
) -> FleetConfig:
    """Generate two artificial PV sites and one empty registry record.

    The event response is deliberately imposed to test workflow accounting; it
    is not evidence of any real site's performance or storm impact.
    """
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite demo directory: {output}")
    output.mkdir(parents=True)
    timestamps = pd.date_range(
        "2026-07-28T03:00:00Z", "2026-10-28T03:00:00Z", freq="h", inclusive="left"
    )
    rng = np.random.default_rng(86261)
    local_hour = timestamps.hour.to_numpy() - 4 + 0.5
    clear_shape = np.maximum(np.sin(np.pi * (local_hour - 6) / 12), 0)
    days = np.arange(len(timestamps)) // 24
    cloud = 0.65 + 0.35 * (0.5 + 0.5 * np.sin(days * 0.51))
    ghi = 1050 * clear_shape * cloud * (0.96 + 0.04 * rng.random(len(timestamps)))
    temperature = 18 + 8 * np.sin(2 * np.pi * (local_hour - 8) / 24) + 2 * np.sin(days * 0.25)
    wind = 2.5 + 1.2 * rng.random(len(timestamps))
    event = pd.Timestamp("2026-10-26T03:00:00Z")
    frames = []
    sites = []
    for identifier, scale, event_factor in (("synthetic-a", 10.0, 0.6), ("synthetic-b", 5.0, 1.25)):
        latitude, longitude = -33.5, -70.7
        poa = transpose_ghi(timestamps, ghi, latitude, longitude, Geometry(tilt_deg=25))
        irradiance = poa.poa_wm2 / 1000
        actual = scale * (0.84 * irradiance - 0.05 * irradiance**2)
        actual *= 1 - 0.003 * (temperature - 25)
        actual *= 1 + rng.normal(0, 0.012, len(timestamps))
        actual = np.maximum(actual, 0)
        actual[timestamps >= event] *= event_factor
        if identifier == "synthetic-a":
            actual[100] = np.nan
            actual[-7:-5] = 0.0
        frames.append(
            pd.DataFrame(
                {
                    "site_id": identifier,
                    "timestamp": timestamps,
                    "actual_mwh": actual,
                    "ghi_wm2": ghi,
                    "temperature_c": temperature,
                    "wind_speed_ms": wind,
                    "gust_ms": wind + 2.5,
                    "duration_hours": 1.0,
                }
            )
        )
        sites.append(
            {
                "site_id": identifier,
                "name": f"SYNTHETIC EXAMPLE {identifier[-1].upper()}",
                "region": "SYNTHETIC",
                "latitude": latitude,
                "longitude": longitude,
                "dc_capacity_mw": scale,
                "ac_capacity_mw": scale * 0.85,
                "dc_capacity_qualified": True,
                "racking_type": "fixed",
                "tilt_deg": 25.0,
                "azimuth_deg": 0.0,
            }
        )
    sites.append(
        {
            "site_id": "synthetic-empty",
            "name": "SYNTHETIC EMPTY RECORD",
            "region": "SYNTHETIC",
            "dc_capacity_qualified": False,
        }
    )
    pd.concat(frames, ignore_index=True).to_parquet(output / "hourly.parquet", index=False)
    pd.DataFrame(sites).to_csv(output / "sites.csv", index=False)
    write_json(
        output / "SYNTHETIC_DATA.json",
        {
            "synthetic": True,
            "seed": 86261,
            "scope": (
                "Artificial testing inputs only; no actual Chile farm measurements "
                "or damage claims."
            ),
        },
    )
    configuration = (
        "[chile_fleet]\n"
        'hourly_path = "hourly.parquet"\n'
        'sites_path = "sites.csv"\n'
        'output_path = "results"\n'
        'event_start = "2026-10-26T03:00:00Z"\n'
        'report_start = "2026-10-26T03:00:00Z"\n'
        'report_end = "2026-10-28T03:00:00Z"\n'
        f'algorithm = "{algorithm}"\n'
        "fit_geometry = false\n"
        "lag_hours = [0]\n"
    )
    (output / "config.toml").write_text(configuration, encoding="utf-8")
    return FleetConfig(
        hourly_path=output / "hourly.parquet",
        sites_path=output / "sites.csv",
        output_path=output / "results",
        event_start=datetime(2026, 10, 26, 3, tzinfo=UTC),
        report_start=datetime(2026, 10, 26, 3, tzinfo=UTC),
        report_end=datetime(2026, 10, 28, 3, tzinfo=UTC),
        algorithm=algorithm,
        fit_geometry=False,
        lag_hours=(0,),
    )
