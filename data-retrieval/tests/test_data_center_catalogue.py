"""Scope, evidence, conflict quarantine and lossless reproducible export tests."""

import copy
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

from energy_analysis.pv_database import export_viewer_data
from energy_data_retrieval.data_center_catalogue import (
    build_parquet,
    capacity_summary,
    load_records,
    stable_id,
    upsert_records,
    validate_catalogue,
)
from energy_data_retrieval.data_center_catalogue.catalogue import validate_record
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_africa_data_centres_footprint,
    parse_airtrunk_locations,
    parse_portfolio,
    parse_schneider_galaxy_vs_model_list,
    parse_stulz_cyberair_3pro_dx_modulating_table,
    parse_stulz_cyberair_3pro_dx_table,
)

ROOT = Path(__file__).resolve().parents[2] / "catalogues/data_centers"
FIXTURES = Path(__file__).parent / "fixtures/data_centers"


@pytest.fixture
def catalogue():
    return load_records(ROOT), json.loads((ROOT / "sources.json").read_text())


def test_complete_catalogue_and_no_inferred_ratings(catalogue):
    rows, sources = catalogue
    validate_catalogue(rows, sources)
    by_name = {r["name"]: r for r in rows}
    assert by_name["Gulf Data Hub ICAD1"].get("it_capacity_mw") is None
    assert by_name["NEXTDC M2"].get("it_capacity_mw") is None  # '+' is a bound.
    assert by_name["Teraco JB1"].get("it_capacity_mw") is None  # Campus not allocated.
    assert by_name["Vertiv XDU450 documented standard unit"].get("cooling_capacity_kw") is None
    assert by_name["NVIDIA DGX H100 documented base system"]["input_power_kw"] == 10.2
    assert by_name["NVIDIA H100 SXM"].get("input_power_kw") is None
    assert all(not r.get("equipment_record_ids") for r in rows if r["entity_type"] == "projects")


@pytest.mark.parametrize(
    "key,value,error",
    [
        ("it_capacity_mw", -1, "Out of range"),
        ("it_capacity_mw", float("nan"), "Non-finite"),
        ("it_capacity_mw", True, "Wrong type"),
        ("country_code", "US", "alpha-3"),
        ("status", "AI-ready", "Invalid status"),
        ("latitude", 91, "Out of range"),
        ("created_at", "2026-01-01T00:00:00", "UTC"),
        ("it_capacity_basis", None, "requires"),
    ],
)
def test_invalid_project_fields(catalogue, key, value, error):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r.get("it_capacity_mw")))
    row[key] = value
    with pytest.raises(ValueError, match=error):
        validate_record(row, sources)


def test_evidence_units_identity_and_orphans(catalogue):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r.get("it_capacity_mw")))
    detail = json.loads(row["evidence_json"])
    detail["it_capacity_mw"]["unit"] = "kW"
    row["evidence_json"] = json.dumps(detail)
    with pytest.raises(ValueError, match="unit mismatch"):
        validate_record(row, sources)
    with pytest.raises(ValueError, match="Duplicate record"):
        validate_catalogue([rows[0], rows[0]], sources)
    children = [r for r in rows if r.get("parent_record_id")]
    with pytest.raises(ValueError, match="parent"):
        validate_catalogue(children, sources)
    assert stable_id("equipment", "ABC-1") != stable_id("equipment", "ABC1")
    assert stable_id("projects", " X ") == stable_id("projects", "X")


def test_capacity_boundaries_null_zero_and_filtered_overlap():
    rows = [
        {
            "entity_type": "projects",
            "aggregation_role": "independent",
            "it_capacity_mw": 0,
            "it_capacity_basis": "operational",
        },
        {
            "entity_type": "projects",
            "aggregation_role": "child",
            "it_capacity_mw": 10,
            "it_capacity_basis": "ultimate_planned",
        },
        {"entity_type": "projects", "aggregation_role": "aggregate", "it_capacity_mw": 100},
        {"entity_type": "projects", "aggregation_role": "independent", "grid_capacity_mw": 999},
        {
            "entity_type": "projects",
            "aggregation_role": "child",
            "overlap_group": "unresolved",
            "it_capacity_mw": 50,
        },
    ]
    result = capacity_summary(rows, "it_capacity_mw")
    assert result == {
        "excluded": 2,
        "unknown": 1,
        "by_basis": {
            "operational": {"reported_mw": 0.0, "records": 1},
            "ultimate_planned": {"reported_mw": 10.0, "records": 1},
        },
    }
    assert capacity_summary(rows[-1:], "it_capacity_mw")["excluded"] == 1
    assert capacity_summary(rows[3:4], "it_capacity_mw")["by_basis"] == {}
    with pytest.raises(ValueError):
        capacity_summary(rows, "backup_generation_mw")


def test_upsert_quarantines_only_conflicting_field_and_retains_creation(catalogue):
    rows, sources = catalogue
    old = copy.deepcopy(next(r for r in rows if r.get("it_capacity_mw") and not r.get("aliases")))
    new = copy.deepcopy(old)
    new["it_capacity_mw"] += 1
    new["aliases"] = ["Synthetic renamed alias"]
    fs = json.loads(new["field_sources_json"])
    fs["aliases"] = new["sources"]
    new["field_sources_json"] = json.dumps(fs)
    ev = json.loads(new["evidence_json"])
    ev["aliases"] = {"locator": "synthetic test observation", "confidence": "high"}
    new["evidence_json"] = json.dumps(ev)
    now = "2026-11-04T00:00:00Z"
    merged, conflicts = upsert_records([old], [new], now=now)
    row = merged[0]
    assert row["created_at"] == old["created_at"]
    assert row["it_capacity_mw"] is None
    assert row["aliases"] == new["aliases"]
    assert row["country_code"] == old["country_code"]
    assert len(conflicts) == 1
    validate_record(row, sources)
    repeated, _ = upsert_records(merged, [new], now="2026-11-05T00:00:00Z")
    assert repeated[0]["updated_at"] == now


def test_export_is_deterministic_typed_and_lossless(tmp_path, catalogue):
    rows, _ = catalogue
    a, b = tmp_path / "a", tmp_path / "b"
    assert build_parquet(ROOT, a) == build_parquet(ROOT, b)
    for entity in ("projects", "equipment"):
        assert (a / f"{entity}.parquet").read_bytes() == (b / f"{entity}.parquet").read_bytes()
        table = pq.read_table(a / f"{entity}.parquet")
        assert table.num_rows == sum(r["entity_type"] == entity for r in rows)
        assert table.schema.field("it_capacity_mw").metadata[b"unit"] == b"MW"
    export_viewer_data(a)
    index = json.loads((a / "viewer-index.json").read_text())
    for entity in ("projects", "equipment"):
        data = json.loads((a / index["tables"][entity]["viewer"]).read_text())
        assert len(data["rows"]) == index["tables"][entity]["rows"]
        assert data["parquet_sha256"] == index["tables"][entity]["parquet_sha256"]
    with pytest.raises(FileExistsError):
        build_parquet(ROOT, a)


def test_offline_inventory_parsers_preserve_uncertainty_and_allowlist_fields():
    data = parse_portfolio(
        (FIXTURES / "nextdc.html").read_bytes(), source_url="https://www.nextdc.com/data-centres"
    )
    assert data["candidates"][0]["power"] == "20+"
    assert data["candidates"][0]["status"] == "Under evaluation"
    assert data["review_required"]
    data = parse_portfolio(
        (FIXTURES / "odata.html").read_bytes(), source_url="https://odatadc.com/localidades/"
    )
    assert data["candidates"][0]["latitude"] == 0
    assert "DO NOT EXTRACT" not in json.dumps(data)
    with pytest.raises(ValueError, match="exactly one"):
        parse_portfolio(b"<html></html>", source_url="https://odatadc.com/localidades/")
    with pytest.raises(ValueError, match="Unsupported"):
        parse_portfolio(b"", source_url="https://example.com")


def test_airtrunk_inventory_parser_is_complete_deduplicated_and_identity_only():
    data = parse_airtrunk_locations(
        (FIXTURES / "airtrunk.html").read_bytes(), source_url="https://airtrunk.com/locations/"
    )
    assert len(data["candidates"]) == 22
    assert {row["external_id"] for row in data["candidates"]} >= {"BOM1", "JHB4", "SYD1"}
    assert next(row for row in data["candidates"] if row["external_id"] == "TOK1")["url"].endswith(
        "tok1-east-tokyo/"
    )
    assert "DO NOT EXTRACT" not in json.dumps(data)
    with pytest.raises(ValueError, match="inventory shape"):
        parse_airtrunk_locations(
            b"<a href='/location/syd1/'>SYD1</a>", source_url="https://airtrunk.com/locations/"
        )


def test_africa_data_centres_footprint_parser_is_complete_and_identity_only():
    data = parse_africa_data_centres_footprint(
        (FIXTURES / "africa-data-centres.html").read_bytes(),
        source_url="https://www.africadatacentres.com/nairobi/",
    )
    assert [row["external_id"] for row in data["candidates"]] == [
        "CPT1",
        "JHB1",
        "JHB2",
        "LOS1",
        "NBO1",
    ]
    assert next(row for row in data["candidates"] if row["external_id"] == "NBO1")["url"].endswith(
        "/nairobi/"
    )
    assert "DO NOT EXTRACT" not in json.dumps(data)
    with pytest.raises(ValueError, match="footprint shape"):
        parse_africa_data_centres_footprint(
            b"<a href='/nairobi/'>NBO1 Nairobi</a>",
            source_url="https://www.africadatacentres.com/",
        )
    with pytest.raises(ValueError, match="official Africa"):
        parse_africa_data_centres_footprint(b"", source_url="https://example.com/")


def test_schneider_model_list_parser_keeps_only_explicit_commercial_references():
    content = (FIXTURES / "schneider-galaxy-vs.txt").read_bytes()
    data = parse_schneider_galaxy_vs_model_list(
        content,
        source_url="https://www.se.com/uk/en/download/document/990-91317_EN/",
        expected_count=3,
    )
    assert [row["commercial_reference"] for row in data["candidates"]] == [
        "GVSUPS10KB2HS",
        "GVSUPS20K0B4HS",
        "GVSUPS60KB5HS",
    ]
    assert data["candidates"][1]["rated_active_power_kw"] == 20
    assert "DO NOT EXTRACT" not in json.dumps(data)
    with pytest.raises(ValueError, match="model-list shape"):
        parse_schneider_galaxy_vs_model_list(
            content,
            source_url="https://www.se.com/uk/en/download/document/990-91317_EN/",
            expected_count=23,
        )
    with pytest.raises(ValueError, match="official Schneider"):
        parse_schneider_galaxy_vs_model_list(content, source_url="https://example.com/")


def test_stulz_cyberair_parser_keeps_exact_fixed_speed_r410a_rows():
    content = (FIXTURES / "stulz-cyberair-3pro-dx.txt").read_bytes()
    data = parse_stulz_cyberair_3pro_dx_table(
        content,
        source_url="https://www.stulz.es/fileadmin/CyberAir_3PRO_DX_ASR-ALR.pdf",
        expected_count=4,
    )
    assert [row["model"] for row in data["candidates"]] == [
        "ASR 201 A",
        "ASR 291 A",
        "ALR 201 GE",
        "ALR 291 GE",
    ]
    assert data["candidates"][0]["cooling_net_kw"] == 30.2
    assert data["candidates"][3]["circuits_compressors"] == "1/1"
    assert data["rating_conditions"]["return_air_temperature_c"] == 33
    assert "DO NOT EXTRACT" not in json.dumps(data)
    with pytest.raises(ValueError, match="table shape"):
        parse_stulz_cyberair_3pro_dx_table(
            content,
            source_url="https://www.stulz.es/fileadmin/CyberAir_3PRO_DX_ASR-ALR.pdf",
            expected_count=30,
        )
    with pytest.raises(ValueError, match="official STULZ"):
        parse_stulz_cyberair_3pro_dx_table(content, source_url="https://example.com/")


def test_stulz_cyberair_parser_keeps_exact_modulating_r410a_rows():
    content = (FIXTURES / "stulz-cyberair-3pro-dx.txt").read_bytes()
    data = parse_stulz_cyberair_3pro_dx_modulating_table(
        content,
        source_url="https://www.stulz.es/fileadmin/CyberAir_3PRO_DX_ASR-ALR.pdf",
        expected_count=4,
    )
    assert [row["model"] for row in data["candidates"]] == [
        "ASR 271 AS",
        "ASR 401 AS",
        "ALR 271 GES",
        "ALR 401 GES",
    ]
    assert data["candidates"][1]["cooling_net_kw"] == 54.0
    assert data["candidates"][2]["free_cooling_water_temperature_c"] == 12.7
    assert data["candidates"][3]["medium_volume_flow_m3_h"] == 8.7
    with pytest.raises(ValueError, match="modulating-ec table shape"):
        parse_stulz_cyberair_3pro_dx_modulating_table(
            content,
            source_url="https://www.stulz.es/fileadmin/CyberAir_3PRO_DX_ASR-ALR.pdf",
            expected_count=20,
        )


def test_pue_table_selection_preserves_period_precision_and_empty_ttm():
    from energy_data_retrieval.data_center_catalogue.portfolios import parse_google_pue

    content = (FIXTURES / "google-pue.html").read_bytes()
    data = parse_google_pue(content, year=2026, quarter=2)
    assert len(data["candidates"]) == 2
    assert data["candidates"][0]["quarterly_pue_text"] == "1.10"
    assert data["candidates"][0]["ttm_pue_text"] is None
    with pytest.raises(ValueError, match="exactly one"):
        parse_google_pue(content, year=2026, quarter=1)
    with pytest.raises(ValueError, match="Invalid measured"):
        parse_google_pue(content.replace(b"1.10", b"0.9"), year=2026, quarter=2)


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("estimates_json", {"it_capacity_mw": {"value": 1}}, "method and uncertainty"),
        ("certifications_json", {"tier": {"certificate": "Tier IV"}}, "issuer, scope, date"),
        ("renewable_supply_json", {"renewable": "100%"}, "Separate physical"),
    ],
)
def test_unbounded_estimates_certificates_and_supply_claims_fail(catalogue, field, value, error):
    rows, sources = catalogue
    row = copy.deepcopy(next(r for r in rows if r["entity_type"] == "projects"))
    row[field] = json.dumps(value)
    fs = json.loads(row["field_sources_json"])
    fs[field] = row["sources"]
    row["field_sources_json"] = json.dumps(fs)
    evidence = json.loads(row["evidence_json"])
    evidence[field] = {"locator": "synthetic invalid claim", "confidence": "low"}
    row["evidence_json"] = json.dumps(evidence)
    with pytest.raises(ValueError, match=error):
        validate_record(row, sources)
