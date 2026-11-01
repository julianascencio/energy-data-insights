"""REPD safety checks use tiny synthetic CSVs, never live registry access."""

from __future__ import annotations

import csv
import hashlib
import io
import json

import pytest

from energy_data_retrieval.pv_catalogue.repd import (
    REQUIRED,
    read_repd_csv,
    reviewed_repd_records,
    screen_repd_identities,
)


def native(ref="123", **changes):
    row = dict.fromkeys(REQUIRED, "")
    row.update(
        {
            "Ref ID": ref,
            "Site Name": "Example solar park",
            "Technology Type": "Solar Photovoltaics",
            "Country": "England",
            "Region": "East Midlands",
            "County": "Lincolnshire",
            "Development Status (short)": "Operational",
            "Mounting Type for Solar": "Ground",
            "Installed Capacity (MWelec)": "5.1",
            "Solar Site Area (sqm)": "25000",
            "X-coordinate": "500000",
            "Y-coordinate": "300000",
            "Operational": "01/02/2020",
            "Record Last Updated (dd/mm/yyyy)": "02/07/2026",
            "Operator (or Applicant)": "Private person",
            "Address": "Private address",
        }
    )
    row.update(changes)
    return row


def read(*rows):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    content = stream.getvalue().encode("cp1252")
    return read_repd_csv(content, sha256=hashlib.sha256(content).hexdigest())


def mapped(rows, ids=None):
    return reviewed_repd_records(
        rows,
        reviewed_ids=ids or {"123"},
        source_id="test",
        retrieved_at="2026-11-01T09:00:00Z",
        snapshot_date="2026-06-30",
    )


def test_mapping_preserves_basis_milestone_and_privacy():
    result = mapped(read(native()))[0]
    assert result["capacity_unspecified_mw"] == 5.1
    assert result["land_area_ha"] == 2.5
    assert (
        not {
            "capacity_ac_mw",
            "capacity_dc_mw",
            "owners",
            "operators",
            "latitude",
            "commissioning_date",
        }
        & result.keys()
    )
    ext = json.loads(result["extensions_json"])["repd"]
    assert ext["operational_milestone_date"] == "2020-02-01"
    assert ext["row_updated_date"] == "2026-07-02"  # publication can follow reference quarter
    assert ext["csv_row"] == 2
    assert "Private" not in json.dumps(result)


def test_missing_area_and_date_are_not_zero():
    result = mapped(
        read(
            native(
                **{
                    "Solar Site Area (sqm)": "NA",
                    "Operational": "",
                    "Installed Capacity (MWelec)": "",
                }
            )
        )
    )[0]
    assert "land_area_ha" not in result and "capacity_unspecified_mw" not in result
    assert json.loads(result["extensions_json"])["repd"]["operational_milestone_date"] is None


def test_checksum_and_duplicate_ids_fail_closed():
    with pytest.raises(ValueError, match="checksum"):
        read_repd_csv(b"bad", sha256="0" * 64)
    with pytest.raises(ValueError, match="Duplicate"):
        read(native(), native())


@pytest.mark.parametrize("technology", ["Solar", "Solar Thermal", "Battery"])
def test_only_explicit_pv_can_be_reviewed(technology):
    with pytest.raises(ValueError, match="photovoltaic"):
        mapped(read(native(**{"Technology Type": technology})))


def test_nearby_phases_are_flagged_not_merged():
    rows = read(
        native(), native("124", **{"Site Name": "Example extension", "X-coordinate": "500050"})
    )
    risks = screen_repd_identities(rows, {"123", "124"})
    assert set(risks) == {"123", "124"}
    with pytest.raises(ValueError, match="identity review"):
        mapped(rows)


def test_distant_punctuation_alias_and_same_application_are_flagged():
    rows = read(
        native(), native("124", **{"Site Name": "EXAMPLE SOLAR-PARK", "X-coordinate": "600000"})
    )
    assert screen_repd_identities(rows, {"123"})["123"][0]["reason"] == "same_normalized_name"
    rows = read(
        native(**{"Planning Application Reference": "APP1"}),
        native(
            "125",
            **{
                "Site Name": "Renamed",
                "X-coordinate": "600000",
                "Planning Application Reference": "APP1",
            },
        ),
    )
    assert "same_planning_application" in screen_repd_identities(rows, {"123"})["123"][0]["reason"]


@pytest.mark.parametrize(
    "change",
    [
        {"Operational": "01/07/2026"},
        {"Operational": "31/02/2020"},
        {"Installed Capacity (MWelec)": "NaN"},
        {"Solar Site Area (sqm)": "-1"},
        {"Development Status (short)": "Awaiting Construction"},
    ],
)
def test_bad_dates_numbers_and_unreviewed_scope_fail(change):
    with pytest.raises(ValueError):
        mapped(read(native(**change)))


def test_reviewed_ids_do_not_accept_the_rest_of_the_registry():
    rows = read(native(), native("124", **{"Site Name": "Other park", "X-coordinate": "600000"}))
    assert len(mapped(rows)) == 1
    assert mapped(rows)[0]["record_id"] == mapped(read(native()))[0]["record_id"]
