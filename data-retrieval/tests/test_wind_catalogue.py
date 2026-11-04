"""Wind boundary decisions: synthetic fixtures plus complete offline source validation."""

import copy
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from energy_analysis.pv_database import export_viewer_data
from energy_analysis.wind_database import compatible_curves, specific_power_w_m2
from energy_data_retrieval.wind_catalogue import (
    build_parquet,
    capacity_summary,
    load_records,
    stable_id,
    upsert_records,
    validate_catalogue,
)
from energy_data_retrieval.wind_catalogue.catalogue import validate_record
from energy_data_retrieval.wind_catalogue.gppd import parse_gppd

ROOT = Path(__file__).resolve().parents[2] / "catalogues/wind"
FIXTURE = Path(__file__).parent / "fixtures/wind/gppd_synthetic.csv"
NOW = "2026-11-03T00:00:00Z"


@pytest.fixture(scope="module")
def catalogue():
    return load_records(ROOT), json.loads((ROOT / "sources.json").read_text())


def test_full_catalogue(catalogue):
    rows, sources = catalogue
    validate_catalogue(rows, sources)
    baseline = [r for r in rows if r.get("historical_capacity_mw") is not None]
    assert len(baseline) >= 5344
    assert all(r.get("capacity_reference_year") for r in baseline)
    by_name = {r["name"]: r for r in rows}
    assert by_name["WindFloat Atlantic"]["installed_capacity_mw"] == 25
    assert by_name["Kincardine"]["installed_capacity_mw"] == 50
    assert by_name["Kallpa"]["installed_capacity_mw"] == 344
    assert len([r for r in rows if r["entity_type"] == "equipment"]) >= 30


def test_adapter_complete_partition_and_null_zero(catalogue):
    rows, ledger = parse_gppd(FIXTURE.read_text(), source_id="wri-gppd-1.3.0", now=NOW)
    validate_catalogue(rows, catalogue[1])
    rows.sort(key=lambda r: r["name"], reverse=True)
    assert len(rows) == len(ledger) == 2
    assert rows[0]["historical_capacity_mw"] == 0
    assert rows[0]["latitude"] == rows[0]["longitude"] == 0
    assert rows[1].get("historical_capacity_mw") is None
    assert rows[1].get("latitude") is None
    assert all(r["status"] == "unknown" and r["aggregation_role"] == "unresolved" for r in rows)
    obs = json.loads(rows[0]["observations_json"])
    assert [(x["kind"], x["value"]) for x in obs] == [("reported", 0), ("modeled", 1)]
    assert all(x["period"] == "2017" and "unspecified" in x["boundary"] for x in obs)
    assert capacity_summary(rows, "historical_capacity_mw")["excluded"] == 2
    assert stable_id("projects", " A ") == stable_id("projects", "A")
    assert stable_id("equipment", "A-1") != stable_id("equipment", "A1")


@pytest.mark.parametrize("replacement", ["-1", "nan", "inf"])
def test_adapter_rejects_bad_capacity(replacement):
    text = FIXTURE.read_text().replace("Wind,0,0,0", f"Wind,{replacement},0,0")
    rows, ledger = parse_gppd(text, source_id="fixture", now=NOW)
    assert len(rows) == 1
    assert ledger[0]["decision"] == "deferred"


def test_adapter_duplicate_registry_id_and_missing_header():
    with pytest.raises(ValueError, match="duplicate"):
        parse_gppd(FIXTURE.read_text().replace("TEST0002", "TEST0001"), source_id="x", now=NOW)
    with pytest.raises(ValueError, match="headers"):
        parse_gppd("name\nX\n", source_id="x", now=NOW)


@pytest.mark.parametrize(
    "key,value,error",
    [
        ("installed_capacity_mw", -1, "range"),
        ("latitude", 91, "range"),
        ("turbine_count", True, "type"),
        ("country_code", "US", "alpha-3"),
        ("status_as_of", "2030-01-01", "Future"),
        ("status", "ready", "Invalid status"),
    ],
)
def test_invalid_project_boundaries(catalogue, key, value, error):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r.get("installed_capacity_mw")))
    row[key] = value
    with pytest.raises(ValueError, match=error):
        validate_record(row, sources)


def test_mixed_fleet_and_unit_evidence(catalogue):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r.get("fleet_completeness") == "complete"))
    row["turbine_count"] += 1
    with pytest.raises(ValueError, match="fleet count"):
        validate_record(row, sources)
    row = copy.deepcopy(next(r for r in rows if r.get("rated_power_kw")))
    ev = json.loads(row["evidence_json"])
    ev["rated_power_kw"]["unit"] = "MW"
    row["evidence_json"] = json.dumps(ev)
    with pytest.raises(ValueError, match="unit mismatch"):
        validate_record(row, sources)


def test_capacity_scopes_survive_filtering():
    base = {"entity_type": "projects", "status": "operational", "aggregation_role": "child"}
    rows = [
        {**base, "installed_capacity_mw": 0},
        {**base, "installed_capacity_mw": 10},
        {**base, "installed_capacity_mw": 100, "aggregation_role": "aggregate"},
        {**base, "export_capacity_mw": 50},
        {**base, "installed_capacity_mw": 99, "overlap_group": "repower-unresolved"},
        {**base, "installed_capacity_mw": 5, "status": "decommissioned"},
    ]
    result = capacity_summary(rows, "installed_capacity_mw")
    assert result["by_status"] == {
        "operational": {"reported_mw": 10, "records": 2},
        "decommissioned": {"reported_mw": 5, "records": 1},
    }
    assert result["excluded"] == 2 and result["unknown"] == 1
    assert capacity_summary(rows[4:5], "installed_capacity_mw")["excluded"] == 1
    with pytest.raises(ValueError):
        capacity_summary(rows, "rated_power_kw")


def test_identity_links_and_conflict_quarantine(catalogue):
    rows, sources = catalogue
    old = copy.deepcopy(next(r for r in rows if r.get("installed_capacity_mw")))
    new = copy.deepcopy(old)
    new["installed_capacity_mw"] += 1
    merged, conflicts = upsert_records([old], [new], now=old["last_verified_at"])
    assert conflicts
    assert merged[0]["installed_capacity_mw"] is None
    assert merged[0]["created_at"] == old["created_at"]
    assert merged[0]["name"] == old["name"]
    validate_record(merged[0], sources)
    with pytest.raises(ValueError, match="Duplicate record"):
        validate_catalogue([old, old], sources)
    phase = next(r for r in rows if r.get("parent_record_id"))
    with pytest.raises(ValueError, match="relationship"):
        validate_catalogue([phase], sources)


def test_curves_compare_only_compatible_original_conditions(catalogue):
    rows, sources = catalogue
    curves = [copy.deepcopy(r) for r in rows if r["entity_type"] == "curves"]
    assert compatible_curves(curves)
    assert not compatible_curves([])
    curves[0]["curve_origin"] = "digitized"
    assert not compatible_curves(curves)
    curves[0]["curve_origin"] = "original_numeric"
    conditions = json.loads(curves[0]["curve_conditions"])
    conditions["air_density_kg_m3"] = 1.1
    curves[0]["curve_conditions"] = json.dumps(conditions)
    assert not compatible_curves(curves)
    points = json.loads(curves[0]["curve_points_json"])
    curves[0]["curve_points_json"] = json.dumps(points[::-1])
    with pytest.raises(ValueError, match="increasing"):
        validate_record(curves[0], sources)
    assert specific_power_w_m2(None, 100) is None
    assert specific_power_w_m2(1000, 100) == pytest.approx(127.323954)
    with pytest.raises(ValueError):
        specific_power_w_m2(1000, 0)


def test_reproducible_snapshot_and_lossless_viewer(tmp_path, catalogue):
    first, second = tmp_path / "a", tmp_path / "b"
    manifest = build_parquet(ROOT, first)
    assert manifest == build_parquet(ROOT, second)
    for entity in manifest["tables"]:
        assert (first / f"{entity}.parquet").read_bytes() == (
            second / f"{entity}.parquet"
        ).read_bytes()
    assert pq.read_table(first / "projects.parquet").num_rows >= 5355
    turbines = pq.read_table(first / "turbines.parquet").to_pylist()
    expected = [r for r in catalogue[0] if r["entity_type"] == "turbines"]
    assert len(turbines) == len(expected)
    project_ids = {r["record_id"] for r in catalogue[0] if r["entity_type"] == "projects"}
    assert all(r["project_record_id"] in project_ids for r in turbines)
    index = export_viewer_data(first)
    assert index["input_sha256"] == manifest["input_sha256"]
    with pytest.raises(FileExistsError):
        build_parquet(ROOT, first)


def test_application_dependent_choke_ratings_and_frame_ambiguity(catalogue):
    rows, _ = catalogue
    by_model = {r.get("model"): r for r in rows if r.get("equipment_category") == "line_choke"}
    choke = by_model["LCVT280AL-525"]
    specs = json.loads(choke["extensions_json"])
    assert specs["nominal_current_a"] is None
    assert specs["power_dissipation_w"] is None
    assert specs["inductance_mh"] == 0.105
    assert [
        (o["nominal_current_a"], o["power_dissipation_w"])
        for o in specs["application_observations"]
    ] == [(280, 460), (270, 430)]
    links = json.loads(choke["compatibility_json"])
    assert [link["model"] for link in links] == ["ACU 510-53"]
    # ACU410-51 has two documented frames; the choke table does not choose one.
    assert len([r for r in rows if r.get("model") == "ACU 410-51"]) == 2


def test_emc_filter_explicit_frame_and_voltage_boundary(catalogue):
    rows, _ = catalogue
    by_id = {r["record_id"]: r for r in rows}
    filters = {r["model"]: r for r in rows if r.get("equipment_category") == "emc_filter"}
    assert len(filters) == 15
    links = json.loads(filters["FTV401A"]["compatibility_json"])
    assert len(links) == 6
    assert all("Frame size 8" in by_id[link["equipment_record_id"]]["variant"] for link in links)
    high_voltage = filters["FTV400A-690"]
    assert high_voltage.get("voltage_v") is None
    spec = json.loads(high_voltage["extensions_json"])
    assert spec["leakage_current_ma"] == 17
    assert "not applied as scalar" in spec["voltage_observation"]["scope"]
    eight = json.loads(filters["HLD 110-500/8"]["compatibility_json"])
    assert "ACU 210-12" not in [link["model"] for link in eight]
    assert (
        "ACU 210-12"
        in json.loads(filters["HLD 110-500/8"]["extensions_json"])["printed_application_models"]
    )


def test_braking_combination_does_not_duplicate_component(catalogue):
    rows, _ = catalogue
    resistors = [r for r in rows if r.get("equipment_category") == "braking_resistor"]
    assert len(resistors) == 11
    spec = json.loads(next(r for r in resistors if r["model"] == "BR 8000/7")["extensions_json"])
    assert spec["resistance_ohm"] == 7.5
    assert spec["continuous_rated_power_w"] == 8000
    double = [o for o in spec["application_observations"] if o["quantity"] == 2]
    assert len(double) == 2
    assert all(
        o["combination_resistance_ohm"] == 3.75 and o["combination_continuous_power_w"] == 16000
        for o in double
    )
    assert spec["thermal_switch"] is None
    missing = next(r for r in rows if r.get("model") == "HLD 110-500/42")
    assert "assembly_specifications" not in json.loads(missing["extensions_json"])


def test_legacy_resistor_observations_do_not_promote_current_claims(catalogue):
    rows, _ = catalogue
    r = next(r for r in rows if r.get("model") == "BR 8000/7")
    spec = json.loads(r["extensions_json"])
    legacy = spec["legacy_vec501_r0_observations"]
    assert legacy["intermittent_power_kw"] == 80
    assert legacy["duty_cycle_pct"] == 10
    assert spec["continuous_rated_power_w"] == 8000
    assert legacy["thermal_protection"] is True
    assert spec["thermal_switch"] is None
    assert legacy["mass_kg"] == 31.5
    assert r.get("mass_kg") is None
    assert legacy["dimension_unit"] is None
