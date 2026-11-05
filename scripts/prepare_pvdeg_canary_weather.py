"""Acquire real PVGIS TMY weather for the Canary mechanism comparison.

Run from repository root. Raw responses stay under outputs; compact, hashed
hourly inputs are published for offline gallery execution. TMY is assembled
from different years, so 2023 timestamps are a calendar axis, not observations.
"""

from __future__ import annotations

import hashlib
import json
import os
import ssl
from pathlib import Path

import httpx
import pandas as pd

from energy_data_retrieval.pvdeg import to_pvdeg_weather
from energy_data_retrieval.sources.pvgis.client import PVGIS_HOSTS, PVGISClient
from energy_data_retrieval.transport import HTTPClient


def main() -> None:
    """Fetch eleven established climate sampling locations across eight islands."""
    root = Path(__file__).resolve().parents[1]
    target = root / "examples/analysis/pvdeg_canary_weather"
    raw = root / "outputs/pvdeg_canary_weather"
    target.mkdir(parents=True, exist_ok=True)
    raw.mkdir(parents=True, exist_ok=True)
    samples = pd.read_csv(root / "examples/analysis/kgpv_canary_samples.csv")
    transport = httpx.HTTPTransport(
        proxy=os.environ.get("HTTPS_PROXY"),
        verify=ssl.create_default_context(cafile=os.environ.get("SSL_CERT_FILE")),
    )
    client = PVGISClient(HTTPClient(PVGIS_HOSTS, transport=transport))
    records = []
    for sample in samples.itertuples():
        slug = str(sample.name).lower().replace(" ", "_")
        path = raw / f"{slug}.json"
        if not path.exists():
            response = client.request(
                "tmy",
                lat=sample.requested_lat,
                lon=sample.requested_lon,
                startyear=2005,
                endyear=2023,
                outputformat="json",
            )
            response.save(path)
        data = json.loads(path.read_text())
        frame = pd.DataFrame(data["outputs"]["tmy_hourly"])
        original = pd.to_datetime(frame.pop("time(UTC)"), format="%Y%m%d:%H%M", utc=True)
        frame.index = pd.DatetimeIndex([t.replace(year=2023) for t in original])
        frame = frame.rename(
            columns={
                "T2m": "temp_air",
                "RH": "relative_humidity",
                "WS10m": "wind_speed",
                "G(h)": "ghi",
                "Gb(n)": "dni",
                "Gd(h)": "dhi",
            }
        )
        negative_wind = frame.wind_speed < 0
        quality = {
            "negative_wind_hours_clipped_to_zero": int(negative_wind.sum()),
            "minimum_provider_wind_m_s": float(frame.wind_speed.min()),
        }
        # PVGIS TMY joins can return a small negative speed. Preserve raw bytes
        # and report each correction; reject larger invalid values.
        if frame.wind_speed.min() < -0.5:
            raise ValueError("Provider wind below -0.5 m/s requires review")
        frame["wind_speed"] = frame.wind_speed.clip(lower=0)
        weather = to_pvdeg_weather(frame)
        if len(weather) != 8760:
            raise ValueError("Expected a complete non-leap hourly TMY")
        payload = weather.to_csv(index_label="time").encode()
        filename = f"{slug}.csv"
        (target / filename).write_bytes(payload)
        records.append(
            {
                "name": sample.name,
                "file": filename,
                "quality": quality,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "inputs": data["inputs"],
                "months_selected": data["outputs"]["months_selected"],
                "request_provenance": json.loads(
                    path.with_suffix(path.suffix + ".provenance.json").read_text()
                ),
            }
        )
        print(sample.name, len(weather), flush=True)
    (target / "manifest.json").write_text(
        json.dumps(
            {
                "evidence": (
                    "PVGIS modeled TMY; 2005-2023 selection window; not measured degradation"
                ),
                "calendar": (
                    "2023 UTC, retaining original month/day/hour; not a historical 2023 series"
                ),
                "processing": (
                    "Provider precision retained; negative wind in [-0.5,0) clipped to zero "
                    "with per-site counts; no interpolation, downscaling or gap filling"
                ),
                "reference_ids": ["pvgis_5_api", "pvdeg_software"],
                "sites": records,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
