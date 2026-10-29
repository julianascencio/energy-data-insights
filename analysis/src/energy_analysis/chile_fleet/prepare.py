"""Join normalized site-level retrieval products without inventing observations."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from .io import (
    OPTIONAL_WEATHER,
    SiteDataSource,
    fingerprint,
    load_sites,
    validate_output_location,
    write_json,
)


def prepare_inputs(generation: Path, weather: Path, sites: Path, output: Path) -> dict[str, object]:
    """Create one complete joined Parquet file per registry site.

    UTC keys must already describe interval starts with one-hour MWh and weather
    in W/m2, degrees Celsius and m/s. Units are a contract; they are not guessed.
    The join is outer: a missing generation observation remains NaN when its
    weather exists, allowing reference-energy coverage to expose the gap.
    """
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite existing prepared data: {output}")
    validate_output_location(output, generation, weather)
    output.parent.mkdir(parents=True, exist_ok=True)
    registry = load_sites(sites)
    generation_source = SiteDataSource(generation)
    weather_source = SiteDataSource(weather, require_actual=False)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        files: list[dict[str, object]] = []
        for index, site_id in enumerate(registry["site_id"].astype(str)):
            left = generation_source.site(site_id)
            right = weather_source.site(site_id)
            left = left.drop(columns=list(OPTIONAL_WEATHER), errors="ignore")
            right = right[["site_id", "timestamp", *OPTIONAL_WEATHER]]
            joined = left.merge(
                right, on=["site_id", "timestamp"], how="outer", validate="one_to_one"
            )
            joined = joined.sort_values("timestamp", kind="stable")
            filename = f"site-{index:06d}.parquet"
            joined.to_parquet(temporary / filename, index=False, compression="zstd")
            files.append({"site_id": site_id, "file": filename, "rows": len(joined)})
        manifest: dict[str, object] = {
            "schema": "energy-data-insights-prepared-hourly-v1",
            "complete": True,
            "units": {
                "actual_mwh": "MWh",
                "ghi_wm2": "W/m2",
                "temperature_c": "degC",
                "wind_speed_ms": "m/s",
                "gust_ms": "m/s",
            },
            "time": "UTC interval start; one elapsed hour; no interpolation or forward fill",
            "registry_scope": (
                "Only registry site IDs are processed; all registry IDs are retained, "
                "including empty sites."
            ),
            "sources": {
                "generation": fingerprint(generation),
                "weather": fingerprint(weather),
                "sites": fingerprint(sites),
            },
            "site_files": files,
        }
        write_json(temporary / "manifest.json", manifest)
        temporary.rename(output)
        return manifest
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
