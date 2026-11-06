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
    parse_bulk_infrastructure_directory,
    parse_bulk_infrastructure_n01_expansion,
    parse_bulk_infrastructure_operations,
    parse_bulk_infrastructure_site_page,
    parse_carrier_19dv_table,
    parse_cummins_generator_table,
    parse_datacenter_united_directory,
    parse_datacenter_united_site_page,
    parse_digital_realty_nbo2_release,
    parse_ecodatacenter_portfolio,
    parse_ecodatacenter_site_page,
    parse_ecodatacenter_smedjebacken_announcement,
    parse_glesys_finland_integration,
    parse_glesys_owned_portfolio,
    parse_glesys_site_page,
    parse_green_mountain_facility_page,
    parse_green_mountain_portfolio,
    parse_icolo_facility_page,
    parse_icolo_home_portfolio,
    parse_maincubes_directory,
    parse_maincubes_site_page,
    parse_meta_locations,
    parse_penta_infra_directory,
    parse_penta_infra_site_page,
    parse_portfolio,
    parse_rack_centre_campus,
    parse_rack_centre_facility_page,
    parse_rack_centre_lgs2_commissioning,
    parse_raxio_facility_page,
    parse_schneider_galaxy_vs_model_list,
    parse_stulz_cyberair_3pro_dx_modulating_table,
    parse_stulz_cyberair_3pro_dx_r134a_table,
    parse_stulz_cyberair_3pro_dx_table,
    parse_uptime_rack_centre_story,
    parse_vertiv_powerups6000_table,
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
    now = "2026-11-04T01:00:00Z"
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


def test_meta_global_fleet_parser_is_complete_and_identity_only():
    content = (FIXTURES / "meta-locations.html").read_bytes()
    data = parse_meta_locations(
        content,
        source_url="https://datacenters.atmeta.com/all-locations/",
        expected_count=3,
    )
    assert [(row["region"], row["locality"]) for row in data["candidates"]] == [
        ("Asia", "Singapore"),
        ("Europe", "Odense"),
        ("United States", "New Albany"),
    ]
    assert data["candidates"][1]["url"] == "https://datacenters.atmeta.com/asset/odense/"
    assert "DO NOT EXTRACT" not in json.dumps(data)
    with pytest.raises(ValueError, match="global-fleet shape"):
        parse_meta_locations(
            content,
            source_url="https://datacenters.atmeta.com/all-locations/",
            expected_count=33,
        )
    with pytest.raises(ValueError, match="official Meta"):
        parse_meta_locations(content, source_url="https://example.com/")


def test_raxio_parser_keeps_public_design_metrics_without_contact_details():
    content = (FIXTURES / "raxio-facility.html").read_bytes()
    data = parse_raxio_facility_page(
        content,
        source_url="https://www.raxiogroup.com/data-centres/example/",
        expected_code="EX1",
    )
    assert data["candidate"] == {
        "external_id": "EX1",
        "it_design_mw": 3.0,
        "rack_capacity": 400,
        "data_hall_area_m2": 2000.0,
        "connection_voltage_kv": 15.0,
        "cooling_provision_mw": 3.0,
        "pue": 1.3,
        "status_markers": ["Opened in 2024"],
        "locator": "Raxio data centre: EX1 / current facility page",
    }
    assert "contact" not in json.dumps(data).lower()
    with pytest.raises(ValueError, match="facility identity"):
        parse_raxio_facility_page(
            content,
            source_url="https://www.raxiogroup.com/data-centres/example/",
            expected_code="WRONG",
        )
    with pytest.raises(ValueError, match="official Raxio"):
        parse_raxio_facility_page(content, source_url="https://example.com/")


def test_icolo_parsers_keep_exact_current_metrics_and_capacity_boundaries():
    facility = parse_icolo_facility_page(
        (FIXTURES / "icolo-facility.html").read_bytes(),
        source_url="https://www.icolo.io/location/mba2/",
        expected_code="MBA2",
    )["candidate"]
    assert facility == {
        "external_id": "MBA2",
        "rack_capacity": 600,
        "customer_space_m2": 1200.0,
        "campus_area_m2": 4000.0,
        "lifecycle_marker": "launched in 2022",
        "locator": "MBA2 current facility page / public facility metrics",
    }
    home = parse_icolo_home_portfolio(
        (FIXTURES / "icolo-home.html").read_bytes(), source_url="https://www.icolo.io/"
    )["candidates"]
    assert [(row["external_id"], row["it_power_mw"]) for row in home] == [
        ("MPM1", 0.2),
        ("MBA1", 0.9),
        ("MBA2", 1.75),
    ]
    nbo2 = parse_digital_realty_nbo2_release(
        (FIXTURES / "digital-realty-nbo2.html").read_bytes(),
        source_url=(
            "https://investor.digitalrealty.com/news-releases/news-release-details/"
            "digital-realty-strengthens-nairobi-east-africa-digital-gateway"
        ),
    )["candidate"]
    assert nbo2["reported_capacity_mw"] == 6.4
    assert nbo2["opening_date"] == "2026-09-07"
    assert "DO NOT EXTRACT" not in json.dumps([facility, home, nbo2])
    with pytest.raises(ValueError, match="facility identity"):
        parse_icolo_facility_page(
            (FIXTURES / "icolo-facility.html").read_bytes(),
            source_url="https://www.icolo.io/location/mba2/",
            expected_code="NBO1",
        )
    with pytest.raises(ValueError, match="official iColo"):
        parse_icolo_home_portfolio(b"", source_url="https://example.com/")


def test_green_mountain_parsers_preserve_site_and_capacity_boundaries():
    portfolio = parse_green_mountain_portfolio(
        (FIXTURES / "green-mountain-portfolio.html").read_bytes(),
        source_url="https://greenmountain.no/data-centers/",
    )
    assert [(row["external_id"], row["status"]) for row in portfolio["candidates"]] == [
        ("SVG-Rennesøy", "operational"),
        ("TEL-Rjukan", "operational"),
        ("OSL-Enebakk", "operational"),
        ("OSL-Hamar", "operational"),
        ("LON-East", "operational"),
        ("FRA-Mainz", "under_construction"),
        ("SVG-Undheim", "under_construction"),
    ]
    facility = parse_green_mountain_facility_page(
        (FIXTURES / "green-mountain-facility.html").read_bytes(),
        source_url="https://greenmountain.no/data-center/osl-enebakk/",
        expected_code="OSL-Enebakk",
    )["candidate"]
    assert facility["campus_area_m2"] == 72200
    assert facility["total_it_capacity_mw"] == 75
    assert facility["average_pue"] == 1.2
    assert facility["grid_supplies"] == 2
    assert facility["building_count"] == 3
    with pytest.raises(ValueError, match="site identity"):
        parse_green_mountain_facility_page(
            (FIXTURES / "green-mountain-facility.html").read_bytes(),
            source_url="https://greenmountain.no/data-center/osl-enebakk/",
            expected_code="OSL-Hamar",
        )
    with pytest.raises(ValueError, match="official Green Mountain"):
        parse_green_mountain_portfolio(b"", source_url="https://example.com/")


def test_glesys_parsers_preserve_owned_sites_and_conflicts():
    portfolio = parse_glesys_owned_portfolio(
        (FIXTURES / "glesys-portfolio.html").read_bytes(),
        source_url="https://glesys.com/locations/our-data-centers/",
    )
    assert [(row["external_id"], row["record_scope"]) for row in portfolio["candidates"]] == [
        ("falkenberg", "facility"),
        ("oulu", "campus"),
        ("pori", "facility"),
        ("stockholm", "facility"),
        ("tampere", "facility"),
    ]
    falkenberg = parse_glesys_site_page(
        (FIXTURES / "glesys-falkenberg.html").read_bytes(),
        source_url="https://glesys.com/locations/our-data-centers/falkenberg/",
        expected_site="Falkenberg",
    )["candidate"]
    assert falkenberg["reported_power_mw"] == 10
    assert falkenberg["conflicting_reported_power_mw"] == 5
    assert falkenberg["pue"] == 1.1
    assert falkenberg["conflicting_pue"] == 1.2
    integration = parse_glesys_finland_integration(
        (FIXTURES / "glesys-integration.html").read_bytes(),
        source_url=(
            "https://glesys.com/blog/glesys-strengthens-its-nordic-footprint-through-full-"
            "integration-of-private-cloud-operations-in-finland/"
        ),
    )
    assert [row["external_id"] for row in integration["candidates"]] == ["pori", "tampere"]
    with pytest.raises(ValueError, match="site identity"):
        parse_glesys_site_page(
            (FIXTURES / "glesys-falkenberg.html").read_bytes(),
            source_url="https://glesys.com/locations/our-data-centers/falkenberg/",
            expected_site="Stockholm",
        )
    with pytest.raises(ValueError, match="official GleSYS"):
        parse_glesys_owned_portfolio(b"", source_url="https://example.com/")


def test_ecodatacenter_parsers_preserve_site_and_capacity_boundaries():
    portfolio = parse_ecodatacenter_portfolio(
        (FIXTURES / "ecodatacenter-portfolio.html").read_bytes(),
        source_url="https://ecodatacenter.tech/data-center",
    )
    assert [(row["external_id"], row["record_scope"]) for row in portfolio["candidates"]] == [
        ("ecodatacenter-1", "facility"),
        ("ecodatacenter-2", "campus"),
    ]
    falun = parse_ecodatacenter_site_page(
        (FIXTURES / "ecodatacenter-falun.html").read_bytes(),
        source_url="https://ecodatacenter.tech/data-center/sweden-falun",
        expected_site="EcoDataCenter 1",
    )["candidate"]
    assert falun["reported_power_mw"] == 80
    assert falun["reported_pue"] == 1.2
    borlange = parse_ecodatacenter_site_page(
        (FIXTURES / "ecodatacenter-borlange.html").read_bytes(),
        source_url="https://ecodatacenter.tech/data-center/ecodatacenter2",
        expected_site="EcoDataCenter 2",
    )["candidate"]
    assert borlange["reported_power_upper_bound_mw"] == 600
    assert borlange["reported_land_area_m2"] == 200000
    smedjebacken = parse_ecodatacenter_smedjebacken_announcement(
        (FIXTURES / "ecodatacenter-smedjebacken.html").read_bytes(),
        source_url=(
            "https://ecodatacenter.tech/press/"
            "ecodatacenter-to-establish-third-datacenter-campus-in-sweden-3462219"
        ),
    )["candidate"]
    assert smedjebacken["reported_unclassified_power_mw"] == 150
    assert smedjebacken["publication_date"] == "2026-08-25"
    with pytest.raises(ValueError, match="site identity"):
        parse_ecodatacenter_site_page(
            (FIXTURES / "ecodatacenter-falun.html").read_bytes(),
            source_url="https://ecodatacenter.tech/data-center/sweden-falun",
            expected_site="EcoDataCenter 2",
        )
    with pytest.raises(ValueError, match="official EcoDataCenter"):
        parse_ecodatacenter_portfolio(b"", source_url="https://example.com/")


def test_penta_infra_parsers_preserve_exact_facility_boundaries():
    directory = parse_penta_infra_directory(
        (FIXTURES / "penta-infra-directory.html").read_bytes(),
        source_url="https://penta-infra.com/data-centers/",
    )
    assert len(directory["candidates"]) == 12
    assert directory["candidates"][0] == {
        "external_id": "amsterdam",
        "name": "Amsterdam",
        "status": "under_construction",
        "status_label": "RFS H1 2026",
        "it_capacity_mw": 8.0,
        "technical_area_m2": 4000.0,
        "url": "https://penta-infra.com/data-centers/amsterdam/",
        "locator": "current directory card / Amsterdam",
    }
    assert directory["candidates"][-1]["name"] == "Copenhagen"
    duesseldorf = parse_penta_infra_site_page(
        (FIXTURES / "penta-infra-duesseldorf.html").read_bytes(),
        source_url="https://penta-infra.com/data-centers/duesseldorf/",
        expected_code="DUS01",
    )["candidate"]
    assert duesseldorf["it_capacity_mw"] == 2.4
    assert duesseldorf["technical_area_m2"] == 1942.0
    assert duesseldorf["future_scope_markers"] == [
        "up to 9,5 planned MW of IT capacity",
        "Düsseldorf data center campus",
    ]
    with pytest.raises(ValueError, match="facility code"):
        parse_penta_infra_site_page(
            (FIXTURES / "penta-infra-duesseldorf.html").read_bytes(),
            source_url="https://penta-infra.com/data-centers/duesseldorf/",
            expected_code="DUS01-DUS02",
        )


def test_bulk_infrastructure_parsers_preserve_capacity_boundaries():
    directory = parse_bulk_infrastructure_directory(
        (FIXTURES / "bulk-infrastructure-directory.html").read_bytes(),
        source_url="https://bulkinfrastructure.com/data-centers/",
    )
    assert [row["external_id"] for row in directory["candidates"]] == [
        "OS-IX",
        "N01",
        "DK01",
    ]
    n01 = parse_bulk_infrastructure_site_page(
        (FIXTURES / "bulk-infrastructure-n01.html").read_bytes(),
        source_url="https://bulkinfrastructure.com/data-centers/n01/",
        expected_code="N01",
    )["candidate"]
    assert n01["campus_land_hectares"] == 300
    assert n01["reported_unclassified_power_mw"] == 1000
    assert n01["substation_apparent_power_mva"] == 125
    expansion = parse_bulk_infrastructure_n01_expansion(
        (FIXTURES / "bulk-infrastructure-n01-expansion.html").read_bytes(),
        source_url=(
            "https://bulkinfrastructure.com/newsroom/"
            "bulk-data-centers-expands-n01-campus-with-42mw-facility/"
        ),
    )["candidate"]
    assert expansion["publication_date"] == "2024-01-23"
    assert expansion["existing_facility_mw"] == 12
    assert expansion["expansion_it_space_mw"] == 42
    operations = parse_bulk_infrastructure_operations(
        (FIXTURES / "bulk-infrastructure-operations.html").read_bytes(),
        source_url="https://bulkinfrastructure.com/data-centers/services/",
    )
    assert operations["operating_codes"] == ["N01", "DK01", "OS-IX"]
    with pytest.raises(ValueError, match="site code"):
        parse_bulk_infrastructure_site_page(
            b"",
            source_url="https://bulkinfrastructure.com/data-centers/n01/",
            expected_code="N01-42MW",
        )


def test_maincubes_parsers_preserve_directory_and_design_ranges():
    directory = parse_maincubes_directory(
        (FIXTURES / "maincubes-directory.html").read_bytes(),
        source_url="https://www.maincubes.com/en/data-centers/",
    )
    assert [row["external_id"] for row in directory["candidates"]] == [
        "FRA05",
        "FRA04",
        "FRA03",
        "FRA02",
        "FRA01",
        "BER02",
        "BER01",
        "AMS01",
    ]
    assert directory["candidates"][0]["reported_capacity_min_mw"] == 75
    assert directory["candidates"][5]["reported_capacity_max_mw"] == 186
    fra03 = parse_maincubes_site_page(
        (FIXTURES / "maincubes-fra03.html").read_bytes(),
        source_url=("https://www.maincubes.com/en/data-centers/carrier-neutral-data-center-fra03/"),
        expected_code="FRA03",
    )["candidate"]
    assert fra03["it_capacity_min_mw"] == fra03["it_capacity_max_mw"] == 16
    assert fra03["technical_area_min_m2"] == 7680
    ber02 = parse_maincubes_site_page(
        (FIXTURES / "maincubes-ber02.html").read_bytes(),
        source_url=(
            "https://www.maincubes.com/en/data-centers/berlin-cloud-ai-provider-campus-ber02/"
        ),
        expected_code="BER02",
    )["candidate"]
    assert (ber02["it_capacity_min_mw"], ber02["it_capacity_max_mw"]) == (144, 186)
    assert (ber02["technical_area_min_m2"], ber02["technical_area_max_m2"]) == (
        12000,
        41184,
    )
    with pytest.raises(ValueError, match="site code"):
        parse_maincubes_site_page(
            b"",
            source_url="https://www.maincubes.com/en/data-centers/unknown/",
            expected_code="FRA99",
        )


def test_datacenter_united_parsers_preserve_exact_facility_boundaries():
    directory = parse_datacenter_united_directory(
        (FIXTURES / "datacenter-united-directory.html").read_bytes(),
        source_url="https://datacenterunited.com/en/our-datacenters/",
    )
    assert [row["external_id"] for row in directory["candidates"]] == [
        "DC Antwerp 1",
        "DC Antwerp 2",
        "DC Antwerp 3",
        "DC Burcht",
        "DC Mechelen",
        "DC Evere 1",
        "DC Evere 2",
        "DC Brussels",
        "DC Machelen",
        "DC Ghent",
        "DC Ghent 2",
        "DC Hasselt 1",
        "DC Oostkamp",
        "DC Mouscron",
    ]
    assert directory["candidates"][10]["status_label"] == "under_construction"
    for group in ("antwerp", "flanders", "evere", "ghent", "mouscron"):
        parsed = parse_datacenter_united_site_page(
            (FIXTURES / f"datacenter-united-{group}.html").read_bytes(),
            source_url=f"https://datacenterunited.com/en/{group}/",
            expected_group=group,
        )
        assert parsed["candidate"]["group"] == group
    with pytest.raises(ValueError, match="identity or lifecycle"):
        parse_datacenter_united_site_page(
            b"<h1>DC Ghent</h1>",
            source_url="https://datacenterunited.com/en/our-datacenters/dc-ghent/",
            expected_group="ghent",
        )


def test_rack_centre_parsers_keep_facilities_and_campus_separate():
    campus = parse_rack_centre_campus(
        (FIXTURES / "rack-centre-campus.html").read_bytes(),
        source_url="https://rack-centre.com/lagos-data-centre-campus-expansion/",
    )["candidate"]
    assert campus["facility_codes"] == ["LGS1", "LGS2"]
    assert campus["it_capacity_mw"] == 13.5
    assert campus["lgs2_white_space_m2"] == 3240
    lgs1 = parse_rack_centre_facility_page(
        (FIXTURES / "rack-centre-lgs1.html").read_bytes(),
        source_url=(
            "https://rack-centre.com/lagos-data-centre-campus-expansion/data-centre-campus-lgs-1/"
        ),
        expected_code="LGS1",
    )["candidate"]
    assert lgs1["it_capacity_mw"] == 1.5
    assert lgs1["technical_area_m2"] == 1094
    lgs2 = parse_rack_centre_facility_page(
        (FIXTURES / "rack-centre-lgs2.html").read_bytes(),
        source_url=(
            "https://rack-centre.com/lagos-data-centre-campus-expansion/"
            "data-centre-campus-lgs-2-expansion/"
        ),
        expected_code="LGS2",
    )["candidate"]
    assert lgs2["it_capacity_mw"] == 12
    assert lgs2["reported_white_space_m2"] == 7200
    event = parse_rack_centre_lgs2_commissioning(
        (FIXTURES / "rack-centre-lgs2-commissioning.html").read_bytes(),
        source_url="https://rack-centre.com/rack-centres-lgs2-12mw-data-centre-commissioned/",
    )["candidate"]
    assert event["commissioning_date"] == "2025-04-10"
    issuer = parse_uptime_rack_centre_story(
        (FIXTURES / "rack-centre-uptime-story.html").read_bytes(),
        source_url=(
            "https://uptimeinstitute.com/clients/"
            "rack-centre-tier-iii-certification-of-constructed-facility"
        ),
    )["candidate"]
    assert issuer["awards"][1]["date"] == "2017-04"
    with pytest.raises(ValueError, match="facility code"):
        parse_rack_centre_facility_page(
            b"", source_url="https://rack-centre.com/", expected_code="LGS3"
        )


def test_vertiv_powerups_parser_keeps_only_explicit_topology_ratings():
    content = (FIXTURES / "vertiv-powerups6000.txt").read_bytes()
    data = parse_vertiv_powerups6000_table(
        content,
        source_url="https://www.vertiv.com/globalassets/vertiv-power-ups-industrial.pdf",
        expected_count=19,
    )
    assert len(data["candidates"]) == 19
    assert data["candidates"][0]["variant"] == ("6 kVA; single-phase input; single-phase output")
    assert data["candidates"][-1]["variant"] == ("200 kVA; three-phase input; three-phase output")
    assert data["candidates"][1]["input_voltage_text"] == "380/400/415 V"
    assert all(row["apparent_power_kva"] != 999 for row in data["candidates"])
    assert data["shared_conditions"]["output_power_factor"] == 1.0
    with pytest.raises(ValueError, match="table shape"):
        parse_vertiv_powerups6000_table(
            content,
            source_url="https://www.vertiv.com/globalassets/vertiv-power-ups-industrial.pdf",
            expected_count=20,
        )


def test_carrier_19dv_parser_keeps_exact_rows_and_rating_conditions():
    content = (FIXTURES / "carrier-19dv.txt").read_bytes()
    data = parse_carrier_19dv_table(
        content,
        source_url="https://brandportal.carrier.com/original/NA2316A_19DV.pdf",
        expected_count=3,
    )
    assert [row["model"] for row in data["candidates"]] == [
        "19DV-F20F223345B9",
        "19DV-F21F223345B9",
        "19DV-F20F223345B3",
    ]
    assert data["candidates"][0]["cooling_capacity_kw"] == 1055
    assert data["candidates"][0]["input_power_kw"] == 151.5
    assert data["candidates"][0]["input_voltage_v"] == 400
    assert data["candidates"][-1]["frequency_hz"] == 60
    assert data["shared_conditions"]["leaving_evaporator_water_c"] == 6.7
    assert "DO NOT EXTRACT" not in json.dumps(data)
    with pytest.raises(ValueError, match="table shape"):
        parse_carrier_19dv_table(
            content,
            source_url="https://brandportal.carrier.com/original/NA2316A_19DV.pdf",
            expected_count=28,
        )
    with pytest.raises(ValueError, match="official Carrier"):
        parse_carrier_19dv_table(content, source_url="https://example.com/19dv.pdf")


def test_cummins_parser_deduplicates_dcc_and_quarantines_rating_conflicts():
    content = (FIXTURES / "cummins-generators.html").read_bytes()
    data = parse_cummins_generator_table(
        content,
        source_url="https://www.cummins.com/en-na/generators/products/test",
        expected_count=1,
    )
    row = data["candidates"][0]
    assert (row["model"], row["frequency_hz"]) == ("DQTEST", 60.0)
    assert (row["data_center_continuous_kw"], row["data_center_continuous_kva"]) == (
        1000.0,
        1250.0,
    )
    assert row["ratings"]["standby"] == [{"kw": 1100.0, "kva": 1375.0}]
    assert set(row["conflicts"]) == {"prime_rating", "continuous_rating"}
    assert "NO-DCC" not in json.dumps(data)
    with pytest.raises(ValueError, match="table shape"):
        parse_cummins_generator_table(
            content,
            source_url="https://www.cummins.com/en-na/generators/products/test",
            expected_count=2,
        )
    with pytest.raises(ValueError, match="official Cummins"):
        parse_cummins_generator_table(content, source_url="https://example.com/test")


def test_cummins_qsk50_fixture_preserves_complete_dcc_inventory():
    content = (FIXTURES / "cummins-qsk50.html").read_bytes()
    data = parse_cummins_generator_table(
        content,
        source_url="https://www.cummins.com/en-na/generators/products/qsk50",
        expected_count=8,
    )
    rows = data["candidates"]
    assert [(row["model"], row["frequency_hz"]) for row in rows] == [
        ("DQGAN", 50.0),
        ("DQGAH", 50.0),
        ("DQGAK", 50.0),
        ("DQGAE", 60.0),
        ("DQGAG", 50.0),
        ("DQGAJ", 50.0),
        ("DQGAM", 50.0),
        ("DQGAF", 60.0),
    ]
    assert all(not row["conflicts"] for row in rows)
    assert rows[0]["ratings"]["data_center_continuous"] == [{"kw": 1020.0, "kva": 1275.0}]
    assert rows[-1]["data_center_continuous_kva"] == 1706.0


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


def test_stulz_cyberair_parser_uses_r134a_availability_mask():
    content = (FIXTURES / "stulz-cyberair-3pro-dx.txt").read_bytes()
    data = parse_stulz_cyberair_3pro_dx_r134a_table(
        content,
        source_url="https://www.stulz.es/fileadmin/CyberAir_3PRO_DX_ASR-ALR.pdf",
        expected_count=4,
    )
    assert [row["model"] for row in data["candidates"]] == [
        "ASR 201 A",
        "ASR 561 A",
        "ALR 201 GE",
        "ALR 422 GE",
    ]
    assert all(row["model"] not in {"ASR 451 A", "ALR 551 GE"} for row in data["candidates"])
    assert data["candidates"][1]["cooling_net_kw"] == 61.8
    assert data["candidates"][2]["free_cooling_water_temperature_c"] == 16.2
    assert data["candidates"][3]["medium_volume_flow_m3_h"] == 8.2
    with pytest.raises(ValueError, match="R134a table shape"):
        parse_stulz_cyberair_3pro_dx_r134a_table(
            content,
            source_url="https://www.stulz.es/fileadmin/CyberAir_3PRO_DX_ASR-ALR.pdf",
            expected_count=23,
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
