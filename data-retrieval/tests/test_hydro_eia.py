"""Synthetic EIA identities and generating/pumping boundaries; no live requests."""

import io
import json

import openpyxl
import pytest

from energy_data_retrieval.hydro_catalogue.eia import (
    PLANT_FIELDS,
    UNIT_FIELDS,
    eligibility,
    enrich,
    parse_partition,
)
from energy_data_retrieval.hydro_catalogue.gppd import parse_gppd


def sample():
    rows, _ = parse_gppd(
        "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude\n"
        "USA,Synthetic,USA0000001,Hydro,9,40,-90\n",
        source_id="wri",
        now="2026-01-01T00:00:00Z",
    )
    item = {
        "year": 2025,
        "plant_code": 1,
        "plant": {
            "Plant Code": 1,
            "Plant Name": "Synthetic",
            "Latitude": 40,
            "Longitude": -90,
            "_row": 3,
        },
        "units": [
            {
                "Generator ID": "01",
                "Prime Mover": "HY",
                "Status": "OP",
                "Nameplate Capacity (MW)": 4,
                "Utility Name": "Synthetic Operator",
            },
            {
                "Generator ID": "02",
                "Prime Mover": "HY",
                "Status": "OP",
                "Nameplate Capacity (MW)": 6,
                "Utility Name": "Synthetic Operator",
            },
        ],
    }
    return rows[0], item


def test_sum_distinct_generators_preserve_identity_and_dates():
    old, item = sample()
    result = enrich(
        old, item, source_id="eia", identity_source_id="mapping", now="2026-11-05T00:00:00Z"
    )
    assert result["record_id"] == old["record_id"]
    assert result["created_at"] == old["created_at"]
    assert result["installed_capacity_mw"] == 10
    assert result["historical_capacity_mw"] == 9
    assert result["status_as_of"] == "2025-12-31"
    assert result["aggregation_role"] == "unresolved"
    assert "pumping_capacity_mw" not in result
    assert "storage_capacity_mwh" not in result
    assert "turbine_count" not in result
    assert (
        enrich(
            result, item, source_id="eia", identity_source_id="mapping", now="2026-11-06T00:00:00Z"
        )
        == result
    )


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"Prime Mover": "PS"}, "mixed_technology_or_state"),
        ({"Status": "SB"}, "mixed_technology_or_state"),
        ({"Status": "OS"}, "mixed_technology_or_state"),
        ({"Nameplate Capacity (MW)": None}, "capacity_review"),
        ({"Nameplate Capacity (MW)": -1}, "capacity_review"),
        ({"Nameplate Capacity (MW)": True}, "capacity_review"),
        ({"Generator ID": "01"}, "duplicate_unit_review"),
    ],
)
def test_ineligible_units_do_not_become_operating_hydro(change, reason):
    old, item = sample()
    item["units"][1].update(change)
    assert eligibility(old, item) == reason
    with pytest.raises(ValueError, match=reason):
        enrich(old, item, source_id="eia", identity_source_id="mapping", now="2026-11-05T00:00:00Z")


def test_same_name_is_not_registry_identity():
    old, item = sample()
    item["plant_code"] = 2
    assert eligibility(old, item) == "registry_id_review"


def workbook(sheet, headers, rows):
    book = openpyxl.Workbook()
    page = book.active
    page.title = sheet
    page.append(["2025 Form EIA-860 Data - Synthetic"])
    page.append(headers)
    for row in rows:
        page.append([row.get(k) for k in headers])
    output = io.BytesIO()
    book.save(output)
    return output.getvalue()


def test_parser_retains_mixed_units_and_spreadsheet_locators():
    plants = workbook("Plant", PLANT_FIELDS, [{"Plant Code": 1, "Plant Name": "Synthetic"}])
    units = workbook(
        "Operable",
        ("Plant Code", *UNIT_FIELDS),
        [
            {"Plant Code": 1, "Generator ID": "01", "Prime Mover": "HY"},
            {"Plant Code": 1, "Generator ID": "02", "Prime Mover": "PS"},
            {"Plant Code": 501, "Generator ID": "03", "Prime Mover": "HY"},
        ],
    )
    rows = parse_partition(plants, units, year=2025, first=1, last=500)
    assert len(rows) == 1
    assert [u["Generator ID"] for u in rows[0]["units"]] == ["01", "02"]
    assert [u["_row"] for u in rows[0]["units"]] == [3, 4]


def test_existing_capacity_conflict_requires_review():
    old, item = sample()
    old["installed_capacity_mw"] = 20
    with pytest.raises(ValueError, match="conflict review"):
        enrich(old, item, source_id="eia", identity_source_id="mapping", now="2026-11-05T00:00:00Z")


def test_unknown_subtype_remains_unknown():
    old, item = sample()
    result = enrich(
        old, item, source_id="eia", identity_source_id="mapping", now="2026-11-05T00:00:00Z"
    )
    assert result["technology"] == "unknown"
    assert json.loads(result["external_ids_json"])["eia_plant_code"] == "1"


def test_recognized_footer_is_skipped_but_malformed_rows_fail():
    plants = workbook("Plant", PLANT_FIELDS, [{"Plant Code": 1}])
    footer = {"Utility ID": "NOTE: synthetic source footer"}
    headers = ("Plant Code", *UNIT_FIELDS)
    assert (
        parse_partition(
            plants, workbook("Operable", headers, [footer]), year=2025, first=1, last=500
        )
        == []
    )
    with pytest.raises(ValueError, match="Malformed EIA footer"):
        parse_partition(
            plants,
            workbook("Operable", headers, [{**footer, "Generator ID": "1"}]),
            year=2025,
            first=1,
            last=500,
        )
    with pytest.raises(ValueError, match="plant code"):
        parse_partition(
            plants,
            workbook("Operable", headers, [{"Generator ID": "1"}]),
            year=2025,
            first=1,
            last=500,
        )


def test_annual_inventory_cannot_overwrite_newer_lifecycle_evidence():
    old, item = sample()
    old.update(status="decommissioned", status_as_of="2026-06-30")
    assert eligibility(old, item) == "newer_status_review"
