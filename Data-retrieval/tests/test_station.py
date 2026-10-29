"""Synthetic measured-station tests protect units, UTC keys and source separation."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pandas as pd
import pytest

from energy_data_retrieval.sources.station import StationSchema, import_station, normalize_station


def contract() -> StationSchema:
    return StationSchema(
        station_column="id",
        timestamp_column="time",
        timezone="UTC",
        timestamp_label="end",
        ghi_column="sun",
        ghi_unit="kWh/m2",
        temperature_column="temperature",
        temperature_unit="K",
        wind_speed_column="wind",
        wind_speed_unit="km/h",
        gust_column="gust",
        gust_unit="km/h",
    )


def samples() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "id": ["station-1", "station-1"],
            "time": ["2026-01-01T01:00Z", "2026-01-01T02:00Z"],
            "sun": ["0.8", "0"],
            "temperature": ["293.15", ""],
            "wind": ["36", ""],
            "gust": ["72", ""],
        }
    )


def mapping() -> pd.DataFrame:
    return pd.DataFrame({"station_id": ["station-1", "station-1"], "site_id": ["A", "B"]})


def test_station_units_hour_labels_mapping_and_missing() -> None:
    output = normalize_station(samples(), mapping(), contract())
    assert output["site_id"].tolist() == ["A", "A", "B", "B"]
    assert output["timestamp"].dt.hour.tolist() == [0, 1, 0, 1]
    assert output["ghi_wm2"].tolist() == [800, 0, 800, 0]
    assert output["temperature_c"].iloc[0] == pytest.approx(20)
    assert output["wind_speed_ms"].iloc[0] == 10
    assert output["gust_ms"].iloc[0] == 20
    assert pd.isna(output["wind_speed_ms"].iloc[1])
    assert output.attrs["station_observations"] is True
    assert output.attrs["sensor_quality_confirmed"] is False


def test_missing_optional_fields_remain_null_and_no_poa_relabeling() -> None:
    config = replace(contract(), temperature_column=None, wind_speed_column=None, gust_column=None)
    output = normalize_station(samples(), mapping(), config)
    assert output[["temperature_c", "wind_speed_ms", "gust_ms"]].isna().all().all()
    with pytest.raises(ValueError, match="POA"):
        replace(config, irradiance_kind="POA")
    with pytest.raises(ValueError, match="hourly means"):
        replace(config, sampling="instantaneous")


def test_duplicate_station_samples_must_agree() -> None:
    data = pd.concat([samples(), samples().iloc[:1]], ignore_index=True)
    assert len(normalize_station(data, mapping(), contract())) == 4
    data.loc[2, "sun"] = "0.9"
    with pytest.raises(ValueError, match="Conflicting"):
        normalize_station(data, mapping(), contract())


def test_multiple_stations_for_one_site_require_separate_regimes() -> None:
    maps = pd.DataFrame({"station_id": ["station-1", "station-2"], "site_id": ["A", "A"]})
    with pytest.raises(ValueError, match="exactly one"):
        normalize_station(samples(), maps, contract())


def test_nonfinite_values_and_unknown_station_fail() -> None:
    data = samples()
    data.loc[0, "wind"] = "inf"
    with pytest.raises(ValueError, match="infinite"):
        normalize_station(data, mapping(), contract())
    with pytest.raises(ValueError, match="unmapped"):
        normalize_station(samples(), mapping().assign(station_id="unknown"), contract())


def test_station_import_keeps_sensor_provenance(tmp_path: Path) -> None:
    source, maps, target = (
        tmp_path / "station.csv",
        tmp_path / "map.csv",
        tmp_path / "weather.parquet",
    )
    samples().to_csv(source, index=False)
    mapping().to_csv(maps, index=False)
    first = import_station(source, maps, target, contract())
    assert import_station(source, maps, target, contract()) == first
    manifest = json.loads(target.with_suffix(".parquet.json").read_text())
    assert manifest["provenance"]["station_observations"] is True
    assert manifest["provenance"]["schema"]["gust_statistic"] == "hourly_maximum"
    assert pd.read_parquet(target)["weather_source"].unique().tolist() == ["measured-station"]
