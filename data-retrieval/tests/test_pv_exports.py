"""Native NIST/DKASC file imports, missing measurements and local-file provenance."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TypedDict

import pandas as pd
import pytest

from energy_data_retrieval.sources.dkasc import DKASCClient
from energy_data_retrieval.sources.dkasc import parse_generation_csv as parse_dkasc
from energy_data_retrieval.sources.nist import NISTClient
from energy_data_retrieval.sources.nist import parse_generation_csv as parse_nist
from energy_data_retrieval.transport import RetrievalError

# Deliberate parser fixtures, not published measurements or gallery captures.
NIST_CSV = (
    "TIMESTAMP,InvPAC_kW_Avg,InvEtot_kWh\n"
    "2016-07-01 12:00:00,12.4,12345\n2016-07-01 12:01:00,NAN,12345\n"
)
DKASC_CSV = (
    "Date,Array 1 - 5-Min-Avg kW,Array 1 - kWh Del-Rec\n"
    "01/07/2024 12:00,5.2,9000\n01/07/2024 12:05,-0.01,9000\n"
)


class DKASCOptions(TypedDict):
    system_id: str
    timestamp_column: str
    timestamp_format: str
    power_column: str


DKASC_OPTIONS: DKASCOptions = {
    "system_id": "Array 1",
    "timestamp_column": "Date",
    "timestamp_format": "%d/%m/%Y %H:%M",
    "power_column": "Array 1 - 5-Min-Avg kW",
}


def test_nist_summer_uses_standard_time_not_daylight_saving() -> None:
    frame = parse_nist(NIST_CSV, array="Ground")
    assert frame.timestamp.iloc[0] == pd.Timestamp("2016-07-01T17:00Z")
    assert frame.value.iloc[0] == 12.4
    assert pd.isna(frame.value.iloc[1])
    assert frame.measurement_kind.unique().tolist() == ["interval_average_power"]
    assert frame.InvEtot_kWh.tolist() == [12345, 12345]


def test_nist_one_second_sample_is_explicit() -> None:
    csv = NIST_CSV.replace("InvPAC_kW_Avg", "InvPAC_kW")
    with pytest.raises(ValueError, match="_Avg"):
        parse_nist(csv, array="ground", power_column="InvPAC_kW")
    frame = parse_nist(csv, array="ground", power_column="InvPAC_kW", resolution="one-second")
    assert frame.measurement_kind.unique().tolist() == ["instantaneous_power"]
    with pytest.raises(ValueError, match="instantaneous"):
        parse_nist(NIST_CSV, array="ground", resolution="one-second")


def test_nist_missing_only_channel_stays_missing_without_dtype_warnings() -> None:
    frame = parse_nist(NIST_CSV.replace(",12.4,", ",NAN,"), array="ground")
    assert frame.value.isna().all()
    assert len(frame) == 2


def test_nist_toa5_units_and_aggregation_are_checked() -> None:
    toa5 = (
        '"TOA5","test fixture"\n"TIMESTAMP","InvPAC_kW_Avg"\n'
        '"TS","kW"\n"","Avg"\n"2016-01-01 12:00:00",-0.2\n'
    )
    assert parse_nist(toa5, array="roof").value.tolist() == [-0.2]
    with pytest.raises(RetrievalError, match="kW"):
        parse_nist(toa5.replace('"kW"', '"W"'), array="roof")
    with pytest.raises(RetrievalError, match="Avg"):
        parse_nist(toa5.replace('"Avg"', '"Max"'), array="roof")


def test_nist_no_cumulative_energy_as_generation() -> None:
    with pytest.raises(ValueError, match="AC real-power"):
        parse_nist(NIST_CSV, array="ground", power_column="InvEtot_kWh")
    with pytest.raises(ValueError, match="array"):
        parse_nist(NIST_CSV, array="unknown")


def test_dkasc_exact_date_format_and_northern_territory_offset() -> None:
    frame = parse_dkasc(DKASC_CSV, **DKASC_OPTIONS)
    assert frame.timestamp.iloc[0] == pd.Timestamp("2024-07-01T02:30Z")
    assert frame.value.tolist() == [5.2, -0.01]
    assert frame.unit.unique().tolist() == ["kW"]
    assert frame.interval_minutes.unique().tolist() == [5]
    assert frame["Array 1 - kWh Del-Rec"].tolist() == [9000, 9000]


def test_dkasc_cumulative_energy_and_missing_columns_are_rejected() -> None:
    options = DKASC_OPTIONS.copy()
    options["power_column"] = "Array 1 - kWh Del-Rec"
    with pytest.raises(ValueError, match="cumulative"):
        parse_dkasc(DKASC_CSV, **options)
    with pytest.raises(RetrievalError, match="lacks"):
        parse_dkasc(DKASC_CSV.replace("Date,", "Other,"), **DKASC_OPTIONS)
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_dkasc(DKASC_CSV, maximum_rows=1, **DKASC_OPTIONS)


@pytest.mark.parametrize("provider", ["nist", "dkasc"])
def test_local_file_input_hash_is_retained_without_absolute_path(
    tmp_path: Path, provider: str
) -> None:
    path = tmp_path / "private-location" / "export.csv"
    path.parent.mkdir()
    content = NIST_CSV if provider == "nist" else DKASC_CSV
    path.write_text(content)
    if provider == "nist":
        result = NISTClient().read_export(path, array="canopy")
    else:
        result = DKASCClient().read_export(path, **DKASC_OPTIONS)
    assert result.requests == ()
    assert result.frame.attrs["input_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert result.frame.attrs["input_filename"] == "export.csv"
    assert str(tmp_path) not in str(result.frame.attrs)


def test_markup_and_conflicting_observations_fail() -> None:
    with pytest.raises(RetrievalError, match="markup"):
        parse_dkasc("<html>login page</html>", **DKASC_OPTIONS)
    row = NIST_CSV.splitlines()[1].replace(",12.4,", ",99,")
    with pytest.raises(RetrievalError, match="conflicting"):
        parse_nist(NIST_CSV + row + "\n", array="ground")
