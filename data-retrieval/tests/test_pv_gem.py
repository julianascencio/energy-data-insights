"""Synthetic phase/identity edge cases; no network data in test fixtures."""

import copy
import hashlib
import io
import json

import pytest
from openpyxl import Workbook

from energy_data_retrieval.pv_catalogue.gem import (
    HEADERS,
    SHEET,
    read_gem_workbook,
    stage_gem_projects,
)

NOW = "2026-11-02T00:00:00Z"


def phase(**changes):
    row = {
        "GEM location ID": "L100000000001",
        "GEM phase ID": "G100000000001",
        "Country/Area": "Chile",
        "Project Name": "Synthetic Copper Solar Farm",
        "Technology Type": "PV",
        "Status": "operating",
        "Capacity (MW)": 10,
        "Capacity Rating": "MWac",
        "Latitude": -30,
        "Longitude": -70,
        "Location accuracy": "approximate",
    }
    return row | changes


def stage(rows, existing=None):
    return stage_gem_projects(
        rows,
        existing=existing or [],
        country_codes={"Chile": "CHL", "United States": "USA"},
        source_id="synthetic",
        now=NOW,
    )


def test_group_phases_once_and_preserve_metadata():
    rows, held = stage([phase(), phase(**{"GEM phase ID": "G100000000002", "Owner": "Owner A"})])
    assert not held and len(rows) == 1
    assert rows[0]["capacity_ac_mw"] == 20
    assert len(json.loads(rows[0]["phases_json"])) == 2
    assert "approximate" in rows[0]["location_accuracy"]
    assert "commissioning_year" not in rows[0]


@pytest.mark.parametrize("other", ["TZ: 12", "WKSL: 99", "TZ ID: 9", "tz: 12"])
def test_any_restricted_phase_holds_entire_location(other):
    rows, held = stage(
        [phase(), phase(**{"GEM phase ID": "G100000000002", "Other IDs (unit/phase)": other})]
    )
    assert not rows and "restricted_source_lineage" in held[0]["reasons"]


@pytest.mark.parametrize("technology", ["Assumed PV", "Solar Thermal", None])
def test_only_explicit_pv(technology):
    rows, held = stage([phase(**{"Technology Type": technology})])
    assert not rows and "not_all_explicit_pv" in held[0]["reasons"]


def test_us_requires_crosswalk():
    rows, held = stage([phase(**{"Country/Area": "United States"})])
    assert not rows and "us_eia_crosswalk_required" in held[0]["reasons"]


@pytest.mark.parametrize("change", [{"Status": "construction"}, {"Capacity Rating": "MWp/dc"}])
def test_no_total_for_mixed_status_or_rating(change):
    rows, _ = stage([phase(), phase(**({"GEM phase ID": "G100000000002"} | change))])
    assert not any(
        k in rows[0] for k in ["capacity_ac_mw", "capacity_dc_mw", "capacity_unspecified_mw"]
    )


def test_duplicate_phase_rejected():
    with pytest.raises(ValueError, match="Duplicate GEM phase"):
        stage([phase(), phase()])


def test_name_and_nearby_matches_held_without_changing_existing():
    existing = [
        {
            "entity_type": "projects",
            "country_code": "CHL",
            "name": "Other Name",
            "latitude": -30.001,
            "longitude": -70.001,
        }
    ]
    original = copy.deepcopy(existing)
    rows, held = stage([phase()], existing)
    assert not rows and "near_existing_project_2km" in held[0]["reasons"]
    assert existing == original
    existing[0].update(name="Synthetic Copper PV Plant", latitude=0, longitude=0)
    rows, held = stage([phase()], existing)
    assert not rows and "existing_identity" in held[0]["reasons"]


def test_ambiguous_names_do_not_create_multiple_plants():
    rows, held = stage(
        [phase(), phase(**{"GEM location ID": "L100000000002", "GEM phase ID": "G100000000002"})]
    )
    assert not rows and len(held) == 2


def test_checksum_and_schema_guard():
    book = Workbook()
    sheet = book.active
    sheet.title = SHEET
    headers = sorted(HEADERS)
    sheet.append(headers)
    row = phase()
    sheet.append([row.get(k) for k in headers])
    out = io.BytesIO()
    book.save(out)
    data = out.getvalue()
    assert len(read_gem_workbook(data, sha256=hashlib.sha256(data).hexdigest())) == 1
    with pytest.raises(ValueError, match="checksum"):
        read_gem_workbook(data, sha256="0" * 64)


def test_missing_rating_or_coordinate_does_not_get_inferred():
    rows, _ = stage([phase(**{"Capacity Rating": None, "Longitude": None})])
    assert "capacity_ac_mw" not in rows[0] and "latitude" not in rows[0]
