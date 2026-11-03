"""REPD safety checks use tiny synthetic CSVs, never live registry access."""

from __future__ import annotations

import csv
import hashlib
import io
import json

import pytest

from energy_data_retrieval.pv_catalogue.catalogue import upsert_records
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


def construction_rows(**changes):
    return read(
        native(
            **{
                "Development Status (short)": "Under Construction",
                "Operational": "",
                "Under Construction": "01/03/2025",
                **changes,
            }
        )
    )


def construction_mapped(rows):
    return reviewed_repd_records(
        rows,
        reviewed_ids={"123"},
        source_id="test",
        retrieved_at="2026-11-02T23:00:00Z",
        snapshot_date="2026-06-30",
        reviewed_status="Under Construction",
    )


def test_construction_requires_explicit_scope_and_keeps_lifecycle_milestone():
    rows = construction_rows()
    with pytest.raises(ValueError, match="outside reviewed scope"):
        mapped(rows)
    record = construction_mapped(rows)[0]
    assert record["status"] == "under_construction_registry_snapshot"
    ext = json.loads(record["extensions_json"])["repd"]
    assert ext["construction_start_milestone_date"] == "2025-03-01"
    assert ext["operational_milestone_date"] is None
    assert not {"commissioning_date", "capacity_ac_mw", "owners", "operators"} & record.keys()
    assert "Private" not in json.dumps(record)
    assert record["record_id"] == mapped(read(native()))[0]["record_id"]


def test_construction_missing_milestone_remains_unknown():
    record = construction_mapped(construction_rows(**{"Under Construction": ""}))[0]
    assert (
        json.loads(record["extensions_json"])["repd"]["construction_start_milestone_date"] is None
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"Operational": "01/01/2025"},
        {"Under Construction": "01/07/2026"},
        {"Under Construction": "31/02/2025"},
        {"Development Status (short)": "Awaiting Construction"},
    ],
)
def test_construction_conflicting_future_or_unreviewed_scope_is_held(changes):
    with pytest.raises(ValueError):
        construction_mapped(construction_rows(**changes))


def test_unlisted_lifecycle_scope_and_missing_construction_column_fail_closed():
    with pytest.raises(ValueError, match="Unsupported"):
        reviewed_repd_records(
            read(native()),
            reviewed_ids={"123"},
            source_id="test",
            retrieved_at="2026-11-02T23:00:00Z",
            snapshot_date="2026-06-30",
            reviewed_status="Application Submitted",
        )
    rows = construction_rows()
    del rows[0]["Under Construction"]
    with pytest.raises(ValueError, match="missing"):
        construction_mapped(rows)


def test_construction_observation_cannot_downgrade_existing_operation():
    existing = mapped(read(native()))
    incoming = construction_mapped(construction_rows())
    merged, conflicts = upsert_records(existing, incoming, now="2026-11-02T23:00:00Z")
    assert len(conflicts) == 1
    assert merged == existing
    assert merged[0]["status"] == "operational_registry_snapshot"


def awaiting_mapped(rows):
    return reviewed_repd_records(
        rows,
        reviewed_ids={"123"},
        source_id="test",
        retrieved_at="2026-11-02T23:00:00Z",
        snapshot_date="2026-06-30",
        reviewed_status="Awaiting Construction",
    )


def test_awaiting_scope_does_not_invent_construction_or_operation():
    rows = construction_rows(
        **{"Development Status (short)": "Awaiting Construction", "Under Construction": ""}
    )
    with pytest.raises(ValueError, match="outside reviewed scope"):
        mapped(rows)
    record = awaiting_mapped(rows)[0]
    assert record["status"] == "awaiting_construction_registry_snapshot"
    assert record["record_id"] == mapped(read(native()))[0]["record_id"]
    assert "commissioning_date" not in record
    ext = json.loads(record["extensions_json"])["repd"]
    assert "construction_start_milestone_date" not in ext
    assert ext["operational_milestone_date"] is None


@pytest.mark.parametrize(
    "milestones",
    [{"Under Construction": "01/01/2025"}, {"Operational": "01/01/2025"}],
)
def test_awaiting_scope_rejects_actual_lifecycle_milestones(milestones):
    rows = construction_rows(
        **{
            "Development Status (short)": "Awaiting Construction",
            "Under Construction": "",
            **milestones,
        }
    )
    with pytest.raises(ValueError):
        awaiting_mapped(rows)


def test_explicit_area_hold_keeps_native_assertion_without_selecting_a_value():
    record = reviewed_repd_records(
        read(native()),
        reviewed_ids={"123"},
        source_id="test",
        retrieved_at="2026-11-02T23:00:00Z",
        snapshot_date="2026-06-30",
        held_fields_by_ref_id={"123": {"land_area_ha"}},
    )[0]
    assert "land_area_ha" not in record
    ext = json.loads(record["extensions_json"])["repd"]
    assert ext["Solar Site Area (sqm)"] == "25000"
    assert ext["held_canonical_fields"] == ["land_area_ha"]


@pytest.mark.parametrize("holds", [{"123": {"name"}}, {"124": {"land_area_ha"}}])
def test_field_holds_cannot_drop_identity_or_target_unreviewed_rows(holds):
    with pytest.raises(ValueError, match="field hold"):
        reviewed_repd_records(
            read(native()),
            reviewed_ids={"123"},
            source_id="test",
            retrieved_at="2026-11-02T23:00:00Z",
            snapshot_date="2026-06-30",
            held_fields_by_ref_id=holds,
        )
