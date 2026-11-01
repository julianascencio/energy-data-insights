"""Synthetic inventory fixtures test filtering and aggregation, not real projects."""

import io
from zipfile import ZipFile

import pandas as pd
import pytest

from energy_data_retrieval.bess_catalogue.inventories import (
    parse_eia860_archive,
    parse_eia860_frames,
    parse_repd_csv,
    parse_repd_frame,
)

ARGS = {"source_id": "synthetic", "retrieved_at": "2026-11-01T00:00:00Z"}


def frames():
    plants = pd.DataFrame(
        [
            {
                "Plant Code": 1,
                "Plant Name": "Synthetic mixed plant",
                "State": "CA",
                "County": "Test",
                "Latitude": 30.0,
                "Longitude": -110.0,
            }
        ]
    )
    base = {
        "Plant Code": 1,
        "Status": "OP",
        "Prime Mover": "BA",
        "Technology": "Batteries",
        "Storage Technology 1": "LIB",
    }
    storage = pd.DataFrame(
        [
            {
                **base,
                "Generator ID": "A",
                "Nameplate Capacity (MW)": 10,
                "Nameplate Energy Capacity (MWh)": 20,
            },
            {
                **base,
                "Generator ID": "B",
                "Nameplate Capacity (MW)": 5,
                "Nameplate Energy Capacity (MWh)": 30,
            },
            {
                **base,
                "Generator ID": "C",
                "Status": "OA",
                "Nameplate Capacity (MW)": 999,
                "Nameplate Energy Capacity (MWh)": 999,
            },
            {
                **base,
                "Generator ID": "D",
                "Prime Mover": "FW",
                "Technology": "Flywheels",
                "Nameplate Capacity (MW)": 999,
            },
            {
                **base,
                "Generator ID": "E",
                "Storage Technology 1": "ECC",
                "Nameplate Capacity (MW)": 999,
            },
        ]
    )
    return plants, storage


def test_eia_aggregates_only_operating_batteries_and_keeps_other_units_nested():
    import json

    p, s = frames()
    (row,) = parse_eia860_frames(p, s, year=2025, **ARGS)
    assert row["power_capacity_mw"] == 15
    assert row["energy_capacity_mwh"] == 50
    assert row["power_basis"] == "ac"
    assert row["energy_basis"] == "nominal"
    assert row["status"] == "partially_operational"
    assert row["status_as_of"] == "2025-12-31"
    assert row["status_date_basis"] == "reporting_period_end"
    assert "commercial_operation_date" not in row
    assert "duration_hours" not in row
    units = json.loads(row["phases_json"])
    assert [u["generator_id"] for u in units] == ["A", "B", "C"]
    assert [u["included_in_capacity"] for u in units] == [True, True, False]
    assert row["chemistry"] == "lithium-ion"


def test_eia_incomplete_total_is_unknown_and_zero_is_not_missing():
    p, s = frames()
    s.loc[0, "Nameplate Energy Capacity (MWh)"] = float("nan")
    s.loc[0, "Nameplate Capacity (MW)"] = 0
    (row,) = parse_eia860_frames(p, s, year=2025, **ARGS)
    assert "energy_capacity_mwh" not in row
    assert row["power_capacity_mw"] == 5
    s.loc[0, "Storage Technology 1"] = "OTH"
    (row,) = parse_eia860_frames(p, s, year=2025, **ARGS)
    assert "chemistry" not in row


def test_eia_duplicate_or_missing_keys_fail():
    p, s = frames()
    with pytest.raises(ValueError, match="Duplicate EIA battery"):
        parse_eia860_frames(p, pd.concat([s, s.iloc[:1]]), year=2025, **ARGS)
    with pytest.raises(ValueError, match="lacks plant"):
        parse_eia860_frames(p.iloc[:0], s, year=2025, **ARGS)
    with pytest.raises(ValueError, match="columns changed"):
        parse_eia860_frames(p, s.drop(columns="Nameplate Energy Capacity (MWh)"), year=2025, **ARGS)


def test_eia_archive_names_and_header_rows():
    p, s = frames()
    content = io.BytesIO()
    with ZipFile(content, "w") as archive:
        for name, frame, sheet in [
            ("2___Plant_Y2025.xlsx", p, "Plant"),
            ("3_4_Energy_Storage_Y2025.xlsx", s, "Operable"),
        ]:
            workbook = io.BytesIO()
            with pd.ExcelWriter(workbook, engine="openpyxl") as writer:
                frame.to_excel(writer, sheet_name=sheet, startrow=1, index=False)
            archive.writestr(name, workbook.getvalue())
    (row,) = parse_eia860_archive(content.getvalue(), year=2025, **ARGS)
    assert row["power_capacity_mw"] == 15


def repd_frame():
    base = {
        "Site Name": "Synthetic BESS",
        "Technology Type": "Battery",
        "Development Status": "Operational ",
        "Installed Capacity (MWelec)": 10,
        "County": "Test",
        "Country": "England",
        "Region": "Test",
        "Operator (or Applicant)": "Unconfirmed role",
        "X-coordinate": "100",
        "Y-coordinate": "200",
        "Operational": "01/02/2025",
    }
    return pd.DataFrame(
        [
            {**base, "Ref ID": 1},
            {**base, "Ref ID": 2, "Development Status": "Under Construction"},
            {**base, "Ref ID": 3, "Technology Type": "Pumped Storage Hydroelectricity"},
        ]
    )


def test_repd_trims_labels_preserves_native_dates_and_avoids_role_inference():
    r = repd_frame()
    (row,) = parse_repd_csv(
        r.to_csv(index=False).encode("cp1252"), published_date="2026-08-03", **ARGS
    )
    assert row["status"] == "operational"
    assert row["power_capacity_mw"] == 10
    for absent in [
        "energy_capacity_mwh",
        "latitude",
        "longitude",
        "operators",
        "owners",
        "commercial_operation_date",
    ]:
        assert absent not in row
    with pytest.raises(ValueError, match="Duplicate REPD"):
        parse_repd_frame(pd.concat([r, r.iloc[:1]]), published_date="2026-08-03", **ARGS)
    r.loc[0, "Country"] = "Unknown"
    with pytest.raises(ValueError, match="country"):
        parse_repd_frame(r, published_date="2026-08-03", **ARGS)


def test_reviewed_batch_does_not_publish_overlapping_inventory_rows():
    """The acceptance ledger must agree with actual external IDs, not just counts."""
    import json
    from pathlib import Path

    from energy_data_retrieval.bess_catalogue import load_records

    root = Path(__file__).resolve().parents[2] / "catalogues/bess"
    rows = load_records(root)
    audit = json.loads((root / "research/2026-11-01_inventory_review.json").read_text())
    external = {}
    for row in rows:
        for namespace, value in json.loads(row.get("external_ids_json") or "{}").items():
            external[(namespace, value)] = row
    for provider, namespace in [("eia", "eia_plant_code"), ("repd", "repd_ref_id")]:
        assert all(
            (namespace, code) in external for code in audit["accepted_external_ids"][provider]
        )
    for excluded in audit["withheld"]:
        namespace = "eia_plant_code" if excluded["provider"] == "eia860" else "repd_ref_id"
        if excluded["reason"].startswith("Matched existing"):
            assert (namespace, excluded["external_id"]) in external
        else:
            assert (namespace, excluded["external_id"]) not in external
    salisbury = external[("repd_ref_id", "7510")]
    assert salisbury["power_capacity_mw"] == 50
    assert salisbury["quality_status"] == "needs_review"
    assert (
        json.loads(salisbury["conflicts_json"])["power_capacity_mw"]["alternative"]["value"] == 49.5
    )
    edwards = next(r for r in rows if r["name"] == "Edwards & Sanborn BESS")
    assert edwards.get("power_capacity_mw") is None
    assert edwards["energy_capacity_mwh"] == 3287
    assert len(json.loads(edwards["extensions_json"])["eia_2025_scope_review"]["plant_codes"]) == 13
