"""Synthetic inventory fixtures test filtering and aggregation, not real projects."""

import io
import json
from zipfile import ZipFile

import pandas as pd
import pytest

from energy_data_retrieval.bess_catalogue.inventories import (
    parse_aemo_frame,
    parse_cne_frame,
    parse_eia860_archive,
    parse_eia860_frames,
    parse_inventory_workbook,
    parse_repd_csv,
    parse_repd_frame,
)

ARGS = {"source_id": "synthetic", "retrieved_at": "2026-11-01T00:00:00Z"}
PUBLISHED = {**ARGS, "published_date": "2026-10-30"}


def aemo_frame():
    base = {
        "AEMO Survey ID": 1,
        "Site Name": "Synthetic mixed site",
        "Site Owner": "Test",
        "Region": "NSW1",
        "Technology Type": "Battery Storage",
        "Technology Detail": "Lithium-ion",
        "Commitment Status": "In Service",
        "Max Site Capacity (AC)": 999,
        "Unit Count": 100,
        "Full Commercial Use Date": pd.Timestamp("2025-01-01"),
    }
    return pd.DataFrame(
        [
            {
                **base,
                "Gen Info Unit ID": 101,
                "Agg Nameplate Capacity (MW AC)": 10,
                "Agg Nameplate Storage Capacity (MWh)": 20,
            },
            {
                **base,
                "Gen Info Unit ID": 102,
                "Agg Nameplate Capacity (MW AC)": 0,
                "Agg Nameplate Storage Capacity (MWh)": 30,
            },
            {
                **base,
                "Gen Info Unit ID": 103,
                "Agg Nameplate Capacity (MW AC)": 900,
                "Agg Nameplate Storage Capacity (MWh)": 900,
                "Commitment Status": "Committed",
            },
            {
                **base,
                "Gen Info Unit ID": 104,
                "Agg Nameplate Capacity (MW AC)": 999,
                "Technology Type": "Solar",
            },
        ]
    )


def test_aemo_uses_unit_aggregate_not_shared_site_or_unit_multiplier():
    (row,) = parse_aemo_frame(aemo_frame(), **PUBLISHED)
    assert (row["power_capacity_mw"], row["energy_capacity_mwh"]) == (10, 50)
    assert row["power_basis"] == "ac" and row["energy_basis"] == "nominal"
    assert row["status"] == "partially_operational"
    assert "commercial_operation_date" not in row
    assert "grid_connection_capacity_mw" not in row
    phases = json.loads(row["phases_json"])
    assert [p["included_in_capacity"] for p in phases] == [True, True, False]
    assert phases[0]["aemo_unit"]["Full Commercial Use Date"].startswith("2025-01-01")


def test_aemo_missing_total_and_past_forecast_do_not_change_status():
    f = aemo_frame()
    f.loc[0, "Agg Nameplate Storage Capacity (MWh)"] = float("nan")
    f.loc[:1, "Commitment Status"] = "In Commissioning"
    (row,) = parse_aemo_frame(f, **PUBLISHED)
    assert "energy_capacity_mwh" not in row
    assert row["status"] == "commissioning"
    with pytest.raises(ValueError, match="Duplicate AEMO"):
        parse_aemo_frame(pd.concat([f, f.iloc[:1]]), **PUBLISHED)
    f.loc[1, "Site Owner"] = "Different owner"
    with pytest.raises(ValueError, match="Inconsistent AEMO"):
        parse_aemo_frame(f, **PUBLISHED)


def cne_frame():
    return pd.DataFrame(
        [
            {
                "Proyecto": "Synthetic solar",
                "Propietario": "Test",
                "Ubicación": "Test region",
                "Resolución Original DeC - CNE": "1/2026",
                "Tipo de Tecnología": "PMGD Fotovoltaico + BESS",
                "Potencia Neta [MW]": 999,
                "Capacidad de Almacenamiento [MWh]": 0,
                "Potencia Neta Central [MW]": 900,
                "Inyección Adicional BESS [MW]": 800,
                "Fecha Estimada de Interconexión": pd.Timestamp("2025-01-01"),
                "Nota": "Synthetic incumplimiento notice",
            }
        ]
    )


def test_cne_hybrid_scope_and_administrative_status_keep_forecasts_native():
    (row,) = parse_cne_frame(cne_frame(), **PUBLISHED)
    assert row["energy_capacity_mwh"] == 0
    assert "power_capacity_mw" not in row
    assert "grid_connection_capacity_mw" not in row
    assert "expected_operation_date" not in row
    assert row["status"] == "under_construction"
    assert row["quality_status"] == "needs_review"
    native = json.loads(row["extensions_json"])["cne"]
    assert native["milestone_noncompliance_reported"]
    assert native["Potencia Neta [MW]"] == 999
    assert "Nota" not in native
    f = cne_frame()
    f.loc[0, "Tipo de Tecnología"] = "BESS"
    assert parse_cne_frame(f, **PUBLISHED)[0]["power_capacity_mw"] == 999
    with pytest.raises(ValueError, match="Duplicate CNE"):
        parse_cne_frame(pd.concat([f, f]), **PUBLISHED)


@pytest.mark.parametrize(
    "provider,sheet,header,fixture",
    [
        ("aemo", "Generator Information", 3, aemo_frame),
        ("cne", "BESS", 2, cne_frame),
    ],
)
def test_workbook_sheet_header_and_schema_drift(provider, sheet, header, fixture):
    content = io.BytesIO()
    fixture().to_excel(content, sheet_name=sheet, startrow=header, index=False)
    assert len(parse_inventory_workbook(content.getvalue(), provider=provider, **PUBLISHED)) == 1
    adapter = parse_aemo_frame if provider == "aemo" else parse_cne_frame
    with pytest.raises(ValueError, match="columns changed"):
        adapter(pd.DataFrame(), **PUBLISHED)


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


def test_australia_chile_ledger_preserves_scope_and_withheld_records():
    """Registry-to-project crosswalks must prevent republishing overlapping phases."""
    from pathlib import Path

    from energy_data_retrieval.bess_catalogue import load_records

    root = Path(__file__).resolve().parents[2] / "catalogues/bess"
    rows = {r["record_id"]: r for r in load_records(root)}
    audit = json.loads((root / "research/2026-11-01_australia_chile_review.json").read_text())
    for mapping in audit["aemo_crosswalk"]:
        row = rows[mapping["record_id"]]
        if mapping["action"] == "consolidated_into_mreh":
            assert mapping["survey_id"] in json.loads(row["extensions_json"])["aemo_survey_ids"]
            assert row["power_capacity_mw"] == 600
            assert len(json.loads(row["phases_json"])) == 3
        else:
            assert json.loads(row["external_ids_json"])["aemo_survey_id"] == mapping["survey_id"]
    for held in audit["withheld"]:
        assert held["candidate_record_id"] not in rows
    for accepted in audit["cne_accepted"]:
        assert accepted["record_id"] in rows
    hornsdale = next(r for r in rows.values() if r["name"] == "Hornsdale Power Reserve")
    assert (hornsdale["power_capacity_mw"], hornsdale["energy_capacity_mwh"]) == (150, 193.5)
    assert hornsdale["quality_status"] == "needs_review"
    das = next(r for r in rows.values() if r["name"] == "BESS Diego de Almagro Sur II")
    assert das["status"] == "commissioning"
    assert "commercial_operation_date" not in das
    assert "battery_manufacturers" not in das  # Supplier role is not manufacturer evidence.
