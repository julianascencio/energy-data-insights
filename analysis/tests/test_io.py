"""Input identity, unit aggregation and timezone controls."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.chile_fleet.io import SiteDataSource, load_sites, validate_hourly
from energy_analysis.chile_fleet.prepare import prepare_inputs


def test_naive_duplicate_and_subhourly_timestamps_rejected() -> None:
    for times in [["2026-01-01T01:00:00"], ["2026-01-01T01:00:00Z"] * 2, ["2026-01-01T01:30:00Z"]]:
        frame = pd.DataFrame({"site_id": ["a"] * len(times), "timestamp": times, "actual_mwh": 0})
        with pytest.raises(ValueError):
            validate_hourly(frame)


def test_dst_offsets_retain_distinct_elapsed_hours() -> None:
    frame = pd.DataFrame(
        {
            "site_id": ["a", "a"],
            "timestamp": ["2026-04-04T23:00:00-03:00", "2026-04-04T23:00:00-04:00"],
            "actual_mwh": [0, np.nan],
        }
    )
    result = validate_hourly(frame)
    assert result["timestamp"].iloc[1] - result["timestamp"].iloc[0] == pd.Timedelta(hours=1)
    assert result["actual_mwh"].iloc[0] == 0
    assert pd.isna(result["actual_mwh"].iloc[1])


def test_unit_level_data_rejected_and_incomplete_aggregate_withheld() -> None:
    base = pd.DataFrame(
        {"site_id": ["a"], "timestamp": ["2026-01-01T01:00:00Z"], "actual_mwh": [5]}
    )
    with pytest.raises(ValueError, match="Unit-level"):
        validate_hourly(base.assign(unit_id="x"))
    result = validate_hourly(base.assign(generation_complete=False))
    assert pd.isna(result["actual_mwh"].iloc[0])


def test_registry_never_infers_qualified_dc_from_ac(tmp_path: Path) -> None:
    sites = tmp_path / "sites.csv"
    pd.DataFrame({"site_id": ["a"], "ac_capacity_mw": [10]}).to_csv(sites, index=False)
    result = load_sites(sites)
    assert not result["dc_capacity_qualified"].iloc[0]
    assert pd.isna(result["dc_capacity_mw"].iloc[0])
    pd.DataFrame({"site_id": ["a"], "dc_capacity_qualified": ["false"]}).to_csv(sites, index=False)
    assert not load_sites(sites)["dc_capacity_qualified"].iloc[0]


def test_prepare_outer_join_preserves_weather_only_and_empty_registry_sites(tmp_path: Path) -> None:
    sites, generation, weather = (
        tmp_path / name for name in ("sites.csv", "gen.parquet", "weather.parquet")
    )
    pd.DataFrame({"site_id": ["a", "empty"]}).to_csv(sites, index=False)
    pd.DataFrame(
        {"site_id": ["a"], "timestamp": ["2026-01-01T01:00:00Z"], "actual_mwh": [0]}
    ).to_parquet(generation)
    pd.DataFrame(
        {
            "site_id": ["a", "a"],
            "timestamp": ["2026-01-01T01:00:00Z", "2026-01-01T02:00:00Z"],
            "ghi_wm2": [1, 200],
        }
    ).to_parquet(weather)
    output = tmp_path / "prepared"
    manifest = prepare_inputs(generation, weather, sites, output)
    assert manifest["complete"] is True
    source = SiteDataSource(output)
    frame = source.site("a")
    assert len(frame) == 2
    assert frame["actual_mwh"].iloc[0] == 0
    assert pd.isna(frame["actual_mwh"].iloc[1])
    assert source.site("empty").empty
    with pytest.raises(FileExistsError):
        prepare_inputs(generation, weather, sites, output)
