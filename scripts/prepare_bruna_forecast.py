"""Freeze an Open-Meteo IFS forecast for the Bruna gallery (explicit network step)."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import numpy as np
import pandas as pd
from pvlib.location import Location

SITES = {"Arico": (28.15, -16.43), "Granadilla": (28.12, -16.58), "Buenavista": (28.37, -16.85)}
OUT = Path(__file__).resolve().parents[1] / "examples/analysis/data/bruna"


def main() -> None:
    """Fetch a fixed event window, retaining retrieval time and response digests."""
    if datetime.now(UTC) >= datetime(2026, 11, 7, tzinfo=UTC):
        raise ValueError(
            "Pre-event snapshot expired: use a pinned historical single run, not live forecasts"
        )
    frames = []
    records = []
    for name, (lat, lon) in SITES.items():
        params = dict(
            latitude=lat,
            longitude=lon,
            start_date="2026-11-07",
            end_date="2026-11-11",
            hourly="shortwave_radiation,wind_speed_120m",
            models="ecmwf_ifs",
            timezone="UTC",
            wind_speed_unit="ms",
        )
        url = "https://api.open-meteo.com/v1/forecast?" + urlencode(params)
        with urlopen(url, timeout=60) as response:
            raw = response.read()
        payload = json.loads(raw)
        units = payload["hourly_units"]
        if (
            payload["utc_offset_seconds"] != 0
            or units["wind_speed_120m"] != "m/s"
            or units["shortwave_radiation"] != "W/m²"
        ):
            raise ValueError("Unexpected forecast units or clock")
        hourly = payload["hourly"]
        times = pd.DatetimeIndex(pd.to_datetime(hourly["time"], utc=True))
        if len(times) != 120 or not np.all((times[1:] - times[:-1]) == pd.Timedelta(hours=1)):
            raise ValueError("Incomplete hourly forecast window")
        if times[0] != pd.Timestamp("2026-11-07", tz="UTC"):
            raise ValueError("Unexpected forecast start")
        # Radiation is a preceding-hour mean; wind is instantaneous at endpoints.
        wind = np.asarray(hourly["wind_speed_120m"], dtype=float)
        start = times[:96]
        # Integrate clear-sky reference over 12 five-minute midpoints per hour.
        samples = pd.date_range(start[0] + pd.Timedelta(minutes=2.5), periods=96 * 12, freq="5min")
        clear = (
            Location(lat, lon, altitude=0)
            .get_clearsky(samples)["ghi"]
            .to_numpy()
            .reshape(96, 12)
            .mean(axis=1)
        )
        frame = pd.DataFrame(
            dict(
                site=name,
                timestamp=start,
                ghi_wm2=hourly["shortwave_radiation"][1:97],
                clear_ghi_wm2=clear,
                wind_ms=(wind[:96] + wind[1:97]) / 2,
            )
        )
        if not np.isfinite(frame[["ghi_wm2", "clear_ghi_wm2", "wind_ms"]].to_numpy()).all():
            raise ValueError("Missing forecast values")
        frame["ghi_raw_wm2"] = frame["ghi_wm2"]
        if (frame["ghi_wm2"] < -1).any():
            raise ValueError("Radiation below -1 W/m2 requires investigation")
        frame["ghi_wm2"] = frame["ghi_wm2"].clip(lower=0)
        frames.append(frame)
        records.append(
            dict(
                site=name,
                url=url,
                requested_latitude=lat,
                requested_longitude=lon,
                grid_latitude=payload["latitude"],
                grid_longitude=payload["longitude"],
                retrieved_at_utc=datetime.now(UTC).isoformat(),
                sha256=hashlib.sha256(raw).hexdigest(),
            )
        )
    OUT.mkdir(parents=True, exist_ok=True)
    pd.concat(frames).to_csv(OUT / "bruna_forecast.csv", index=False)
    (OUT / "bruna_provenance.json").write_text(
        json.dumps(
            dict(
                source="Open-Meteo / ECMWF IFS",
                model="ecmwf_ifs",
                records=records,
                model_initialization="Not exposed by live API; retrieval time is NOT issue time",
                interval="UTC start, one hour",
                event="2026-11-07 through 2026-11-10 inclusive",
                reference="pvlib Ineichen clear sky, sea level; steady 8 m/s hub-height wind",
                scope="Representative locations, not measured production or island-wide totals",
            ),
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
