"""Synthetic NEM rows exercise lifecycle and unit boundaries, not live downloads."""

import json
from copy import deepcopy

import pytest

from energy_data_retrieval.wind_catalogue.aemo import stage_wind_sites


def unit(ident=101, **changes):
    return {
        "AEMO Survey ID": 1,
        "Site Name": "Synthetic wind and battery site",
        "Site Owner": "Synthetic owner",
        "Region": "NSW1",
        "Gen Info Unit ID": ident,
        "Technology Type": "Wind",
        "Technology Detail": "Onshore",
        "Commitment Status": "In Service",
        "Agg Nameplate Capacity (MW AC)": 12,
        "Unit Count": 4,
        "Unit Capacity (MW AC)": 3,
        "Max Site Capacity (AC)": 900,
        "Full Commercial Use Date": "2020-01-01",
        "source_row": 5,
        **changes,
    }


def stage(rows, **kwargs):
    return stage_wind_sites(
        rows,
        source_id="synthetic",
        now="2026-11-04T20:55:00Z",
        published_date="2026-10-30",
        **kwargs,
    )


def test_no_unit_count_multiplication_or_hybrid_export_substitution():
    r = stage([unit(), unit(102, **{"Technology Type": "Battery Storage"})])[0]
    assert r["installed_capacity_mw"] == 12
    assert "export_capacity_mw" not in r
    assert r["turbine_count"] == 4
    assert r["aggregation_role"] == "unresolved"
    assert "commissioning_date" not in r


def test_mixed_status_capacity_stays_separate_and_dates_do_not_imply_operation():
    r = stage(
        [
            unit(),
            unit(
                102,
                **{"Commitment Status": "Publicly Announced", "Agg Nameplate Capacity (MW AC)": 80},
            ),
        ]
    )[0]
    assert r["status"] == "partially_operational"
    assert "installed_capacity_mw" not in r and "planned_capacity_mw" not in r
    states = json.loads(r["extensions_json"])["capacity_by_aemo_status"]
    assert states["In Service"]["nameplate_mw_ac"] == 12
    assert states["Publicly Announced"]["nameplate_mw_ac"] == 80
    assert "turbine_count" not in r


def test_missing_capacity_is_not_zero_or_inferred_from_count():
    r = stage([unit(), unit(102, **{"Agg Nameplate Capacity (MW AC)": None})])[0]
    assert "installed_capacity_mw" not in r
    assert stage([unit(**{"Agg Nameplate Capacity (MW AC)": 0})])[0]["installed_capacity_mw"] == 0


@pytest.mark.parametrize("state", ["Committed", "Committed*", "Anticipated", "Publicly Announced"])
def test_commitment_is_not_construction_or_permission(state):
    r = stage([unit(**{"Commitment Status": state})])[0]
    assert r["status"] == "announced" and r["planned_capacity_mw"] == 12
    assert "installed_capacity_mw" not in r


def test_commissioning_is_not_installed_total():
    r = stage([unit(**{"Commitment Status": "In Commissioning"})])[0]
    assert r["status"] == "commissioning" and "installed_capacity_mw" not in r


@pytest.mark.parametrize(
    "changes",
    [
        {"Gen Info Unit ID": 1.5},
        {"Unit Count": 2.5},
        {"Unit Count": -1},
        {"Agg Nameplate Capacity (MW AC)": float("nan")},
        {"Commitment Status": "Unknown future status"},
    ],
)
def test_invalid_source_fields_fail(changes):
    with pytest.raises(ValueError):
        stage([unit(**changes)])


def test_duplicate_ids_and_inconsistent_site_metadata_fail():
    with pytest.raises(ValueError, match="Duplicate"):
        stage([unit(), deepcopy(unit())])
    with pytest.raises(ValueError, match="Inconsistent"):
        stage([unit(), unit(102, **{"Region": "VIC1"})])


def test_partition_is_half_open_and_ids_do_not_depend_on_rating():
    assert stage([unit()], minimum_id=1, maximum_id=2)
    assert not stage([unit()], minimum_id=2, maximum_id=3)
    assert (
        stage([unit()])[0]["record_id"]
        == stage([unit(**{"Agg Nameplate Capacity (MW AC)": 15})])[0]["record_id"]
    )


def test_fractional_counts_cannot_cancel_in_aggregate():
    with pytest.raises(ValueError, match="Fractional"):
        stage([unit(**{"Unit Count": 2.5}), unit(102, **{"Unit Count": 1.5})])


def test_workbook_adapter_checks_headers_and_keeps_excel_locators(tmp_path):
    from openpyxl import Workbook

    from energy_data_retrieval.wind_catalogue.aemo import read_wind_units

    path = tmp_path / "synthetic.xlsx"
    book = Workbook()
    sheet = book.active
    sheet.title = "Generator Information"
    for _ in range(3):
        sheet.append(["Synthetic fixture; no real inventory"])
    row = unit()
    row.pop("source_row")
    sheet.append(list(row))
    sheet.append(list(row.values()))
    book.save(path)
    result = read_wind_units(path)
    assert result[0]["source_row"] == 5
    assert result[0]["Agg Nameplate Capacity (MW AC)"] == 12
    sheet.cell(4, 1, "Changed header")
    book.save(path)
    with pytest.raises(ValueError, match="headers"):
        read_wind_units(path)
