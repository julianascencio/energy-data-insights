"""AHA historical scope, bounded parsing and explicit identity controls."""

import copy
import io
import json

import openpyxl
import pytest

from energy_data_retrieval.hydro_catalogue.aha import SHEET, enrich, parse_inventory
from energy_data_retrieval.hydro_catalogue.gppd import parse_gppd


def sample():
    old = parse_gppd(
        "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude\n"
        "AGO,Synthetic,AGO1,Hydro,10,-10,15\n",
        source_id="wri",
        now="2026-01-01T00:00:00Z",
    )[0][0]
    item = {
        "row": 4,
        "raw": {
            "Country": "ANGOLA",
            "Unit Name": "Synthetic",
            "Status": "Committed",
            "Latitude": -10,
            "Longitude": 15,
            "Capacity": 10,
            "River Name": "River",
            "River Basin": "Basin",
            "SharedPlant": None,
            "SharedPlantSplit": None,
        },
    }
    return (
        old,
        item,
        dict(
            source_id="aha",
            reviewed_record_id=old["record_id"],
            reviewed_country_code="AGO",
            now="2026-11-05T00:00:00Z",
        ),
    )


def test_historical_enrichment_does_not_establish_current_operation_or_storage():
    old, item, kw = sample()
    new = enrich(old, item, **kw)
    for field in [
        "status",
        "status_as_of",
        "historical_capacity_mw",
        "latitude",
        "longitude",
        "created_at",
        "aggregation_role",
        "external_ids_json",
    ]:
        assert new[field] == old[field]
    assert new["river"] == "River"
    assert new["basin"] == "Basin"
    assert new.get("installed_capacity_mw") is None
    assert enrich(new, item, **kw) == new
    assert json.loads(new["extensions_json"])["aha_historical_inventory"][0]["row"] == 4


@pytest.mark.parametrize(
    "field,value",
    [
        ("SharedPlant", "Yes"),
        ("SharedPlantSplit", 0.5),
        ("Unit Name", "Other"),
        ("Latitude", float("nan")),
        ("Longitude", 16),
        ("Capacity", 11),
    ],
)
def test_ambiguous_identity_and_scope_rejected(field, value):
    old, item, kw = sample()
    item["raw"][field] = value
    with pytest.raises(ValueError):
        enrich(old, item, **kw)


def test_crosswalk_conflicts_and_immutable_history():
    old, item, kw = sample()
    with pytest.raises(ValueError, match="Explicit"):
        enrich(old, item, **{**kw, "reviewed_country_code": "COD"})
    new = enrich(old, item, **kw)
    changed = copy.deepcopy(item)
    changed["raw"]["River Name"] = "Other"
    with pytest.raises(ValueError, match="Immutable"):
        enrich(new, changed, **kw)
    old["river"] = "Conflicting river"
    with pytest.raises(ValueError, match="Conflicting"):
        enrich(old, item, **kw)


def workbook(headers, row):
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = SHEET
    sheet.append([])
    sheet.append([])
    sheet.append(headers)
    sheet.append(row)
    stream = io.BytesIO()
    book.save(stream)
    book.close()
    return stream.getvalue()


def test_parser_retains_row_location_and_excludes_model_columns():
    headers = [
        None,
        "Country",
        "Unit Name",
        "Status",
        "Latitude",
        "Longitude",
        "River Name",
        "River Basin",
        "Spill From",
        "River Channel ID",
        "Reservoir ID",
        "Reservoir Size",
        "Mean Annual Discharge",
        "Filling Time",
        "Design Discharge",
        "Availability",
        "First Year",
        "Capacity",
        "MaxMonthlyFlow",
        "EnergyPerUnitVolume",
        "MaxMonthlyFlow (MW-equiv)",
        "DeadVolume",
        "StorageAvailable",
        "Size Type",
        "SharedPlant",
        "SharedPlantSplit",
        "SingleSource",
        "Source_status",
        "Source_location",
        "Source_availability",
        "Source_capacity",
        "Source_reservoir_size",
        "Source_mean_annual_discharge",
        "Source_design_discharge",
        "Source_river",
        "Source_river_basin",
    ]
    row = [None, "ANGOLA", "Synthetic"] + [None] * 33
    row[22] = 5000
    parsed = parse_inventory(workbook(headers, row))
    assert parsed[0]["row"] == 4
    assert parsed[0]["raw"]["Unit Name"] == "Synthetic"
    assert "StorageAvailable" not in parsed[0]["raw"]
    headers[17] = "Capacity in kW"
    with pytest.raises(ValueError, match="headers"):
        parse_inventory(workbook(headers, row))
