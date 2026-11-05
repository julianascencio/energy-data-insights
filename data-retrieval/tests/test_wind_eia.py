"""Synthetic EIA workbooks: unit scope, identity, units, and immutable replay."""

import copy
import hashlib
import io
import json

import openpyxl
import pytest

from energy_data_retrieval.wind_catalogue.eia import (
    PLANT_COLUMNS,
    WIND_COLUMNS,
    enrich_retired_partition,
    parse_retired_partition,
)


def workbook(sheets):
    book = openpyxl.Workbook()
    book.remove(book.active)
    for name, headers, rows in sheets:
        sheet = book.create_sheet(name)
        sheet.append(["2025 Form EIA-860 Data — SYNTHETIC TEST ONLY"])
        sheet.append(list(headers))
        for row in rows:
            sheet.append([row.get(k) for k in headers])
    stream = io.BytesIO()
    book.save(stream)
    return stream.getvalue()


def fixture(
    *, status="RE", duplicate=False, year=2025, header_missing=False, speed=10, offshore=False
):
    row = {
        "Plant Code": 123,
        "Plant Name": "Test Wind",
        "Generator ID": "OLD",
        "Status": status,
        "Prime Mover": "WT",
        "Technology": "Onshore Wind Turbine",
        "Nameplate Capacity (MW)": 2,
        "Summer Capacity (MW)": 0,
        "Winter Capacity (MW)": " ",
        "Number of Turbines": 2,
        "Operating Month": 1,
        "Operating Year": 2000,
        "Retirement Month": 5,
        "Retirement Year": 2025,
        "Turbine Hub Height (Feet)": 100,
        "Design Wind Speed (mph)": speed,
        "Predominant Turbine Manufacturer": "SYNTHETIC OEM",
        "Predominant Turbine Model Number": "Unknown",
    }
    if offshore:
        row.update({"Prime Mover": "WS", "Technology": "Offshore Wind Turbine"})
    headers = (*WIND_COLUMNS, "Retirement Month", "Retirement Year")
    if header_missing:
        headers = tuple(x for x in headers if x != "Status")
    operating = {**row, "Generator ID": "NEW", "Status": "OP"}
    wind = workbook(
        [
            ("Retired and Canceled", headers, [row, row] if duplicate else [row]),
            ("Operable", WIND_COLUMNS, [operating]),
        ]
    )
    plant = workbook(
        [
            (
                "Plant",
                PLANT_COLUMNS,
                [
                    {
                        "Plant Code": 123,
                        "Plant Name": "Test Wind",
                        "Latitude": 30.00001,
                        "Longitude": -100.00001,
                    }
                ],
            )
        ]
    )
    return (
        wind,
        plant,
        dict(
            year=year,
            wind_sha256=hashlib.sha256(wind).hexdigest(),
            plant_sha256=hashlib.sha256(plant).hexdigest(),
        ),
    )


def test_units_zero_missing_and_partial_fleet():
    wind, plant, kw = fixture()
    item = parse_retired_partition(wind, plant, **kw)[0]
    unit = item["units"][0]
    assert unit["reported_unit_net_summer_mw"] == 0
    assert unit["reported_unit_net_winter_mw"] is None
    assert unit["representative_hub_height_m"] == pytest.approx(30.48)
    assert unit["source_wind_speed_m_s"] == pytest.approx(4.4704)
    assert "predominant" in unit["fleet_completeness"]
    assert unit["original"]["Predominant Turbine Model Number"] == "Unknown"
    assert item["operable_context"][0]["generator_id"] == "NEW"
    assert "not comprehensive" in item["scope"]


@pytest.mark.parametrize(
    "status,expected",
    [
        ("RE", "retired"),
        ("CN", "canceled"),
        ("IP", "indefinitely postponed or no longer in resource plan"),
    ],
)
def test_statuses_stay_distinct(status, expected):
    wind, plant, kw = fixture(status=status)
    assert parse_retired_partition(wind, plant, **kw)[0]["units"][0]["status"] == expected


@pytest.mark.parametrize(
    "kw",
    [
        {"duplicate": True},
        {"status": "NEW_STATUS"},
        {"year": 2024},
        {"header_missing": True},
        {"speed": -1},
    ],
)
def test_bad_source_fails_closed(kw):
    wind, plant, args = fixture(**kw)
    with pytest.raises(ValueError):
        parse_retired_partition(wind, plant, **args)


def test_checksum():
    wind, plant, kw = fixture()
    kw["wind_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="checksum"):
        parse_retired_partition(wind, plant, **kw)


def existing():
    return {
        "record_id": "test",
        "country_code": "USA",
        "name": "Test Wind",
        "latitude": 30.0,
        "longitude": -100.0,
        "external_ids_json": '{"wri_gppd":"USA0000123"}',
        "extensions_json": '{"old":123}',
        "evidence_json": '{"extensions_json":{"original":123}}',
        "field_sources_json": '{"extensions_json":["old"]}',
        "sources": ["old"],
        "created_at": "2000-01-01T00:00:00Z",
        "status": "unknown",
        "aggregation_role": "unresolved",
        "historical_capacity_mw": 30,
        "observations_json": "[]",
    }


def apply(candidates, row):
    return enrich_retired_partition(
        candidates,
        [row],
        {123: "test"},
        source_id="eia2025",
        identity_source_id="wri",
        now="2026-11-04T23:00:00Z",
    )


def test_preservation_idempotence_and_revision_change():
    wind, plant, kw = fixture()
    candidates = parse_retired_partition(wind, plant, **kw)
    old = existing()
    new = apply(candidates, old)[0]
    for k in (
        "created_at",
        "status",
        "aggregation_role",
        "historical_capacity_mw",
        "observations_json",
    ):
        assert new[k] == old[k]
    assert json.loads(new["external_ids_json"])["eia_plant_code"] == "123"
    assert json.loads(new["extensions_json"])["old"] == 123
    assert apply(candidates, new) == [new]
    changed = copy.deepcopy(candidates)
    changed[0]["units"][0]["reported_unit_nameplate_mw"] = 3
    with pytest.raises(ValueError, match="Immutable"):
        apply(changed, new)


@pytest.mark.parametrize(
    "key,value",
    [
        ("name", "Other Wind"),
        ("longitude", -101),
        ("external_ids_json", '{"wri_gppd":"USA0000124"}'),
    ],
)
def test_identity_requires_code_name_and_coordinates(key, value):
    wind, plant, kw = fixture()
    row = existing()
    row[key] = value
    with pytest.raises(ValueError):
        apply(parse_retired_partition(wind, plant, **kw), row)


def test_offshore_prime_mover_is_ws():
    wind, plant, kw = fixture(offshore=True)
    item = parse_retired_partition(wind, plant, **kw)[0]
    assert item["units"][0]["original"]["Prime Mover"] == "WS"


def test_operable_range_keeps_unit_state_and_bounds():
    wind, plant, kw = fixture()
    rows = parse_retired_partition(wind, plant, **kw, operable_range=(123, 123))
    assert rows[0]["units"][0]["status"] == "operating"
    assert rows[0]["units"][0]["generator_id"] == "NEW"
    assert "/ Operable /" in rows[0]["units"][0]["locator"]
    assert rows[0]["plant_code_range"] == [123, 123]
    assert parse_retired_partition(wind, plant, **kw, operable_range=(124, 130)) == []
    with pytest.raises(ValueError, match="range"):
        parse_retired_partition(wind, plant, **kw, operable_range=(130, 124))


def test_overlapping_source_alias_rejected_but_disjoint_tab_accepted():
    wind, plant, kw = fixture()
    retired = parse_retired_partition(wind, plant, **kw)
    old = apply(retired, existing())[0]
    with pytest.raises(ValueError, match="Overlapping"):
        enrich_retired_partition(
            retired,
            [old],
            {123: "test"},
            source_id="different_alias",
            identity_source_id="wri",
            now="2026-11-05T00:00:00Z",
        )
    operable = parse_retired_partition(wind, plant, **kw, operable_range=(123, 123))
    new = enrich_retired_partition(
        operable,
        [old],
        {123: "test"},
        source_id="operable",
        identity_source_id="wri",
        now="2026-11-05T00:00:00Z",
    )[0]
    history = json.loads(new["extensions_json"])["eia_annual_wind_partitions"]
    assert len(history) == 2
    assert [x["units"][0]["generator_id"] for x in history] == ["OLD", "NEW"]
    assert new["status"] == "unknown"
    assert new["historical_capacity_mw"] == 30
