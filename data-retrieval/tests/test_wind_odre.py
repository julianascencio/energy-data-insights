"""Synthetic French network identities, unit boundaries and conservative scope."""

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from energy_data_retrieval.wind_catalogue import capacity_summary
from energy_data_retrieval.wind_catalogue.odre import read_inventory, stage_inventory

NOW = "2026-11-04T07:35:00Z"


def inputs():
    return json.loads((Path(__file__).parent / "fixtures/wind/odre_synthetic.json").read_text())


def stage(rows, existing=None):
    return stage_inventory(rows, existing or [], source_id="fixture", now=NOW)


def test_capacity_grid_and_inventory_are_distinct():
    raw = inputs()
    before = deepcopy(raw)
    rows, ledger = stage(raw)
    assert raw == before
    assert len(rows) == 1 and ledger[0]["decision"] == "added"
    row = rows[0]
    assert row["installed_capacity_mw"] == 12
    assert row["export_capacity_mw"] == 10
    assert row["status_as_of"] == "2026-08-31"
    assert row["commissioning_date"] == "2024-01-02"
    assert not {"turbine_count", "latitude", "connection_voltage_kv", "turbine_model"} & row.keys()
    assert capacity_summary(rows, "installed_capacity_mw")["excluded"] == 1
    evidence = json.loads(row["evidence_json"])["installed_capacity_mw"]
    assert evidence["original_value"] == 12000 and evidence["original_unit"] == "kW"
    assert (
        json.loads(row["extensions_json"])["odre"]["source_fields"][
            "energieannuelleglissanteinjectee"
        ]
        == 0
    )
    assert stage(inputs())[0] == rows
    assert stage(inputs(), rows)[0] == []


def test_null_export_is_not_zero():
    raw = inputs()
    raw[0]["puismaxrac"] = None
    assert "export_capacity_mw" not in stage(raw)[0][0]
    raw[0]["puismaxrac"] = 0
    assert stage(raw)[0][0]["export_capacity_mw"] == 0


def test_bounded_cohort_keeps_other_years_in_identity_screen():
    raw = inputs()
    raw[0]["datemiseenservice"] = "01/01/2020"
    options = dict(
        source_id="fixture", now=NOW, service_start="2020-01-01", service_end="2021-12-31"
    )
    assert len(stage_inventory(raw, [], **options)[0]) == 1
    raw[0]["datemiseenservice"] = "31/12/2021"
    assert len(stage_inventory(raw, [], **options)[0]) == 1
    other = deepcopy(raw[0])
    other["codeeicresourceobject"] = "17W000000000002B"
    other["datemiseenservice"] = "01/01/2024"
    assert not stage_inventory([*raw, other], [], **options)[0]
    raw[0]["datemiseenservice"] = "01/01/2022"
    assert not stage_inventory(raw, [], **options)[0]


@pytest.mark.parametrize("start,end", [("2021-01-01", "2020-12-31"), ("2020-01-01", "2027-01-01")])
def test_invalid_service_bounds_fail(start, end):
    with pytest.raises(ValueError, match="cohort"):
        stage_inventory(
            inputs(), [], source_id="fixture", now=NOW, service_start=start, service_end=end
        )


def test_generic_name_is_not_a_defensible_farm_identity():
    raw = inputs()
    raw[0]["nominstallation"] = "Hangar"
    assert stage(raw)[1][0]["reasons"] == ["generic_name_requires_identity_review"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("nominstallation", "Confidentiel"),
        ("nominstallation", "Farm PHASE II"),
        ("nbinstallations", 2),
        ("regime", "Hors service"),
        ("codetechnologie", "M.FLO"),
        ("datemiseenservice", "01/01/2019"),
        ("datederaccordement", "01/01/2025"),
    ],
)
def test_unresolved_and_outside_cohort_rows_are_held(field, value):
    raw = inputs()
    raw[0][field] = value
    assert not stage(raw)[0]
    assert stage(raw)[1][0]["reasons"]


@pytest.mark.parametrize("shared_name", [True, False])
def test_full_national_identity_screen(shared_name):
    raw = inputs()
    other = deepcopy(raw[0])
    other["codeeicresourceobject"] = "17W000000000002B"
    other["datemiseenservice"] = "01/01/2010"  # outside cohort still screens identities
    other["nominstallation"] = raw[0]["nominstallation"] if shared_name else "Elsewhere"
    raw.append(other)
    assert not stage(raw)[0]


def test_old_municipality_name_is_not_silently_merged():
    old = {
        "record_id": "old",
        "name": "Synthetic Commune",
        "entity_type": "projects",
        "country_code": "FRA",
    }
    assert stage(inputs(), [old])[1][0]["candidate_record_ids"] == ["old"]


def test_bad_dates_and_incomplete_or_duplicate_source_fail():
    raw = inputs()
    raw[0]["datemiseenservice"] = "01/01/2027"
    with pytest.raises(ValueError, match="exceeds"):
        stage(raw)
    raw = inputs()
    content = json.dumps(raw).encode()
    checksum = hashlib.sha256(content).hexdigest()
    assert read_inventory(content, sha256=checksum, expected_count=1) == raw
    with pytest.raises(ValueError, match="complete"):
        read_inventory(content, sha256=checksum, expected_count=2)
    duplicate = json.dumps(raw + raw).encode()
    with pytest.raises(ValueError, match="duplicate"):
        read_inventory(duplicate, sha256=hashlib.sha256(duplicate).hexdigest(), expected_count=2)
