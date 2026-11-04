"""Synthetic identity and changed-source tests; no live provider access."""

from pathlib import Path

import pytest

from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_cdu_spec_matrix,
    parse_energy_star_ups_inventory,
    parse_generator_dcp_matrix,
    parse_generator_rating_matrix,
    parse_lenovo_gpu_comparison,
    parse_named_inventory,
    parse_power_equipment_matrix,
    parse_precision_cooling_matrix,
    parse_project_permit_matrix,
    parse_server_accelerator_matrix,
    parse_server_accelerator_shipping_matrix,
    parse_supermicro_nvidia_systems,
    parse_ups_rating_matrix,
)

CONTENT = (Path(__file__).parent / "fixtures/data_centers/named-inventory.html").read_bytes()
CDU_MATRIX = (Path(__file__).parent / "fixtures/data_centers/cdu-matrix.csv").read_bytes()
POWER_MATRIX = (
    Path(__file__).parent / "fixtures/data_centers/power-equipment-matrix.csv"
).read_bytes()
PRECISION_COOLING_MATRIX = (
    Path(__file__).parent / "fixtures/data_centers/precision-cooling-matrix.csv"
).read_bytes()
SERVER_MATRIX = (
    Path(__file__).parent / "fixtures/data_centers/server-accelerator-matrix.csv"
).read_bytes()
SERVER_SHIPPING_MATRIX = (
    Path(__file__).parent / "fixtures/data_centers/server-accelerator-shipping-matrix.csv"
).read_bytes()
GENERATOR_MATRIX = (
    Path(__file__).parent / "fixtures/data_centers/generator-rating-matrix.csv"
).read_bytes()
GENERATOR_DCP_MATRIX = (
    Path(__file__).parent / "fixtures/data_centers/generator-dcp-matrix.csv"
).read_bytes()
LENOVO_COMPARISON = (
    Path(__file__).parent / "fixtures/data_centers/lenovo-gpu-comparison.html"
).read_bytes()
SUPERMICRO_SYSTEMS = (
    Path(__file__).parent / "fixtures/data_centers/supermicro-nvidia-systems.html"
).read_bytes()
UPS_MATRIX = (Path(__file__).parent / "fixtures/data_centers/ups-rating-matrix.csv").read_bytes()
PROJECT_PERMIT_MATRIX = (
    Path(__file__).parent / "fixtures/data_centers/project-permit-matrix.csv"
).read_bytes()
ENERGY_STAR_UPS = (Path(__file__).parent / "fixtures/data_centers/energy-star-ups.csv").read_bytes()


def test_energy_star_ups_inventory_keeps_certification_id_and_power_boundaries():
    result = parse_energy_star_ups_inventory(
        ENERGY_STAR_UPS,
        source_url=(
            "https://data.energystar.gov/api/v3/views/ifxy-2uty/export.csv?accessType=DOWNLOAD"
        ),
        partner="Example UPS Partner",
        expected_count=2,
    )
    first = result["candidates"][0]
    assert first["ENERGY STAR Unique ID"] == "1001"
    assert first["Active Output Power Rating Minimum Configuration (W)"] == "900"
    assert first["Apparent Output Power Rating Minimum Configuration (VA)"] == "1,000"
    assert first["Energy Storage System Runtime at 100% Load (min.)"] == "5"
    assert result["partner"] == "Example UPS Partner"
    assert len(result["sha256"]) == 64

    adi = parse_energy_star_ups_inventory(
        ENERGY_STAR_UPS,
        source_url=(
            "https://data.energystar.gov/api/v3/views/ifxy-2uty/export.csv?accessType=DOWNLOAD"
        ),
        partner="ADI",
        expected_count=1,
    )
    assert [row["ENERGY STAR Unique ID"] for row in adi["candidates"]] == ["2001"]
    assert adi["candidates"][0]["Brand Name"] == "W BOX"

    ablerex = parse_energy_star_ups_inventory(
        ENERGY_STAR_UPS,
        source_url=(
            "https://data.energystar.gov/api/v3/views/ifxy-2uty/export.csv?accessType=DOWNLOAD"
        ),
        partner="Ablerex Electronics Co., Ltd.",
        expected_count=1,
    )
    assert [row["ENERGY STAR Unique ID"] for row in ablerex["candidates"]] == ["3001"]
    assert ablerex["candidates"][0]["Minimum Configuration Tested Model Number"] == "N/A"
    assert ablerex["candidates"][0]["Energy Storage System Runtime at 100% Load (min.)"] == "N/A"

    reviewed_partners = {
        "Panduit Corp.": ("4001", "PANDUIT"),
        "Appleton Grp LLC d/b/a Appleton Group": ("5001", "Emerson / SOLAHD"),
        "Legrand AV Inc.": ("6001", "Middle Atlantic"),
    }
    for partner, (expected_id, expected_brand) in reviewed_partners.items():
        batch = parse_energy_star_ups_inventory(
            ENERGY_STAR_UPS,
            source_url=(
                "https://data.energystar.gov/api/v3/views/ifxy-2uty/export.csv?accessType=DOWNLOAD"
            ),
            partner=partner,
            expected_count=1,
        )
        assert [row["ENERGY STAR Unique ID"] for row in batch["candidates"]] == [expected_id]
        assert batch["candidates"][0]["Brand Name"] == expected_brand


def test_energy_star_ups_inventory_rejects_drift_duplicates_and_unofficial_sources():
    url = "https://data.energystar.gov/api/v3/views/ifxy-2uty/export.csv"
    with pytest.raises(ValueError, match="partner inventory shape"):
        parse_energy_star_ups_inventory(
            ENERGY_STAR_UPS, source_url=url, partner="Example UPS Partner", expected_count=3
        )
    duplicate = ENERGY_STAR_UPS + ENERGY_STAR_UPS.splitlines(keepends=True)[1]
    with pytest.raises(ValueError, match="Duplicate ENERGY STAR UPS unique ID"):
        parse_energy_star_ups_inventory(
            duplicate, source_url=url, partner="Example UPS Partner", expected_count=2
        )
    with pytest.raises(ValueError, match="Unsupported ENERGY STAR UPS"):
        parse_energy_star_ups_inventory(
            ENERGY_STAR_UPS,
            source_url="https://example.com/ups.csv",
            partner="Example UPS Partner",
            expected_count=2,
        )


def test_project_permit_matrix_preserves_authority_scope_and_area():
    result = parse_project_permit_matrix(
        PROJECT_PERMIT_MATRIX,
        source_url="https://ep10.kouvola.fi/cgi/example",
        expected_count=2,
    )
    assert result["candidates"][0]["authority_id"] == "286-2025-165"
    assert result["candidates"][0]["building_area_m2"] == 40285
    assert result["candidates"][1]["building_area_m2"] is None
    assert result["candidates"][1]["address"] == "Sinimäentie 6a"
    assert result["review_required"]
    assert len(result["sha256"]) == 64


def test_project_permit_matrix_rejects_drift_duplicates_and_unofficial_sources():
    url = "https://www.espoo.fi/fi/example"
    with pytest.raises(ValueError, match="Changed project-permit matrix shape"):
        parse_project_permit_matrix(PROJECT_PERMIT_MATRIX, source_url=url, expected_count=3)
    duplicate = PROJECT_PERMIT_MATRIX + PROJECT_PERMIT_MATRIX.splitlines(keepends=True)[1]
    with pytest.raises(ValueError, match="Duplicate project-permit row"):
        parse_project_permit_matrix(duplicate, source_url=url, expected_count=2)
    with pytest.raises(ValueError, match="Unsupported official project-permit"):
        parse_project_permit_matrix(
            PROJECT_PERMIT_MATRIX,
            source_url="https://example.com/permit.csv",
            expected_count=2,
        )


def test_ups_matrix_preserves_kva_kw_and_market_boundaries():
    toshiba_rows = b"\n".join(UPS_MATRIX.splitlines()[:3]) + b"\n"
    result = parse_ups_rating_matrix(
        toshiba_rows,
        source_url="https://toshiba.com/tic/product/example-ups/",
        expected_count=2,
    )
    assert [row["variant"] for row in result["candidates"]] == [
        "40 kVA/kW; 480 V; 60 Hz",
        "100 kVA; 480 V; 60 Hz",
    ]
    assert result["candidates"][0]["output_power_kw"] == 40
    assert result["candidates"][1]["output_power_kw"] is None
    assert result["review_required"]
    assert len(result["sha256"]) == 64


def test_ups_matrix_drift_duplicates_and_invalid_sources_fail():
    url = "https://www.toshiba.com/tic/product/example-ups/"
    toshiba_rows = b"\n".join(UPS_MATRIX.splitlines()[:3]) + b"\n"
    with pytest.raises(ValueError, match="Changed UPS matrix shape"):
        parse_ups_rating_matrix(toshiba_rows, source_url=url, expected_count=3)
    duplicate = toshiba_rows + UPS_MATRIX.splitlines(keepends=True)[1]
    with pytest.raises(ValueError, match="Duplicate UPS rating row"):
        parse_ups_rating_matrix(duplicate, source_url=url, expected_count=2)
    with pytest.raises(ValueError, match="Unsupported official UPS"):
        parse_ups_rating_matrix(UPS_MATRIX, source_url="https://example.com/", expected_count=2)
    with pytest.raises(ValueError, match="manufacturer/source mismatch"):
        parse_ups_rating_matrix(UPS_MATRIX, source_url=url, expected_count=3)


def test_ups_matrix_accepts_mitsubishi_official_rows():
    header, *rows = UPS_MATRIX.splitlines()
    mitsubishi_row = next(row for row in rows if row.startswith(b"Mitsubishi Electric,"))
    mitsubishi = header + b"\n" + mitsubishi_row + b"\n"
    result = parse_ups_rating_matrix(
        mitsubishi,
        source_url="https://mitsubishicritical.com/uninterruptible-power-supplies/",
        expected_count=1,
    )
    assert result["candidates"][0]["manufacturer"] == "Mitsubishi Electric"
    assert result["candidates"][0]["apparent_power_kva"] == 300
    assert result["candidates"][0]["output_power_kw"] == 300


def test_ups_matrix_accepts_fuji_electric_official_rows():
    header, *rows = UPS_MATRIX.splitlines()
    fuji_row = next(row for row in rows if row.startswith(b"Fuji Electric,"))
    fuji = header + b"\n" + fuji_row + b"\n"
    result = parse_ups_rating_matrix(
        fuji,
        source_url=(
            "https://americas.fujielectric.com/wp-content/uploads/2024/10/"
            "FEA-UPS-DS-100d-UPS7400.pdf"
        ),
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["manufacturer"] == "Fuji Electric"
    assert candidate["apparent_power_kva"] == 1000
    assert candidate["output_power_kw"] == 1000


def test_ups_matrix_accepts_kehua_kw_only_row_without_inventing_kva():
    header, *rows = UPS_MATRIX.splitlines()
    kehua_row = next(row for row in rows if row.startswith(b"Kehua Tech,"))
    kehua = header + b"\n" + kehua_row + b"\n"
    result = parse_ups_rating_matrix(
        kehua,
        source_url="https://www.kehua.com/critical-power.html",
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["manufacturer"] == "Kehua Tech"
    assert candidate["apparent_power_kva"] is None
    assert candidate["output_power_kw"] == 60


def test_ups_matrix_accepts_kstar_quarantined_kva_without_inventing_value():
    header, *rows = UPS_MATRIX.splitlines()
    kstar_row = next(row for row in rows if row.startswith(b"KSTAR,"))
    kstar = header + b"\n" + kstar_row + b"\n"
    result = parse_ups_rating_matrix(
        kstar,
        source_url="https://www.kstar.com/bocupload/2025/04/03/transfomerbasedups.pdf",
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["manufacturer"] == "KSTAR"
    assert candidate["apparent_power_kva"] is None
    assert candidate["output_power_kw"] == 24


def test_ups_matrix_keeps_kstar_epower_apparent_and_active_power_separate():
    header, *rows = UPS_MATRIX.splitlines()
    kstar_row = next(row for row in rows if b"EP600-H" in row)
    kstar = header + b"\n" + kstar_row + b"\n"
    result = parse_ups_rating_matrix(
        kstar,
        source_url="https://www.kstar.com/bocupload/2025/04/03/transfomerbasedups.pdf",
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["manufacturer"] == "KSTAR"
    assert candidate["apparent_power_kva"] == 600
    assert candidate["output_power_kw"] == 540


def test_ups_matrix_accepts_makelsan_exact_rating_row():
    header, *rows = UPS_MATRIX.splitlines()
    makelsan_row = next(row for row in rows if row.startswith(b"Makelsan,"))
    makelsan = header + b"\n" + makelsan_row + b"\n"
    result = parse_ups_rating_matrix(
        makelsan,
        source_url=("https://www.makelsan.com.tr/katalog/levelups-t3-series-10---200-kva.pdf"),
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["manufacturer"] == "Makelsan"
    assert candidate["family"] == "LEVELUPS T3"
    assert candidate["apparent_power_kva"] == 200
    assert candidate["output_power_kw"] == 200


def test_ups_matrix_accepts_borri_row_without_deriving_power_factor():
    header, *rows = UPS_MATRIX.splitlines()
    borri_row = next(row for row in rows if row.startswith(b"Borri,"))
    borri = header + b"\n" + borri_row + b"\n"
    result = parse_ups_rating_matrix(
        borri,
        source_url="https://www.borri.it/product/b9000fxs/",
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["manufacturer"] == "Borri"
    assert candidate["apparent_power_kva"] == 300
    assert candidate["output_power_kw"] == 270


def test_ups_matrix_accepts_tescom_exact_rating_row():
    header, *rows = UPS_MATRIX.splitlines()
    tescom_row = next(row for row in rows if row.startswith(b"Tescom,"))
    tescom = header + b"\n" + tescom_row + b"\n"
    result = parse_ups_rating_matrix(
        tescom,
        source_url="https://www.tescom-ups.com/es/producto/ds-power-300ht-8",
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["manufacturer"] == "Tescom"
    assert candidate["family"] == "DS POWER 300HT"
    assert candidate["apparent_power_kva"] == 300
    assert candidate["output_power_kw"] == 270


def test_ups_matrix_rejects_fuji_source_manufacturer_mismatch():
    header, *rows = UPS_MATRIX.splitlines()
    mitsubishi_row = next(row for row in rows if row.startswith(b"Mitsubishi Electric,"))
    mitsubishi = header + b"\n" + mitsubishi_row + b"\n"
    with pytest.raises(ValueError, match="manufacturer/source mismatch"):
        parse_ups_rating_matrix(
            mitsubishi,
            source_url="https://www.fujielectric.com/example/ups.html",
            expected_count=1,
        )


@pytest.mark.parametrize(
    "url,identities",
    [
        ("https://www.atnorth.com/nordic-data-centers/", ["FIN91", "NOR91"]),
        ("https://www.coolitsystems.com/products/", ["ahx920", "chx910"]),
    ],
)
def test_only_exact_same_host_identities_are_staged(url, identities):
    result = parse_named_inventory(CONTENT, source_url=url, expected_count=2)
    assert [r["external_id"] for r in result["candidates"]] == identities
    assert len(result["sha256"]) == 64
    assert result["review_required"]
    assert "DO NOT EXTRACT" not in str(result)
    assert all(set(r) == {"external_id", "url", "locator"} for r in result["candidates"])


def test_conflicting_identity_urls_and_inventory_drift_fail():
    url = "https://www.atnorth.com/nordic-data-centers/"
    conflict = CONTENT + b'<a href="/nordic-data-centers/different/">FIN91</a>'
    with pytest.raises(ValueError, match="Conflicting inventory URL"):
        parse_named_inventory(conflict, source_url=url, expected_count=2)
    with pytest.raises(ValueError, match="Changed inventory shape"):
        parse_named_inventory(CONTENT, source_url=url, expected_count=3)
    with pytest.raises(ValueError, match="Unsupported official"):
        parse_named_inventory(CONTENT, source_url="https://example.com/", expected_count=2)


def test_cdu_matrix_preserves_models_ratings_and_loop_boundaries():
    result = parse_cdu_spec_matrix(
        CDU_MATRIX,
        source_url="https://www.motivaircorp.com/example.pdf",
        expected_count=2,
    )
    assert [row["model"] for row in result["candidates"]] == ["MCDU-X1", "MCDU-X2"]
    assert result["candidates"][0]["cooling_capacity_kw"] == 125.5
    assert result["candidates"][0]["primary_flow"] == "30 GPM"
    assert result["candidates"][0]["secondary_flow"] == "20 GPM"
    assert result["review_required"]
    assert len(result["sha256"]) == 64


def test_cdu_matrix_drift_duplicates_and_invalid_sources_fail():
    url = "https://www.nvent.com/example.pdf"
    with pytest.raises(ValueError, match="Changed CDU matrix shape"):
        parse_cdu_spec_matrix(CDU_MATRIX, source_url=url, expected_count=3)
    duplicate = CDU_MATRIX + CDU_MATRIX.splitlines(keepends=True)[1]
    with pytest.raises(ValueError, match="Duplicate CDU row"):
        parse_cdu_spec_matrix(duplicate, source_url=url, expected_count=2)
    with pytest.raises(ValueError, match="Unsupported official CDU"):
        parse_cdu_spec_matrix(
            CDU_MATRIX,
            source_url="https://example.com/example.pdf",
            expected_count=2,
        )


def test_precision_cooling_matrix_keeps_exact_rating_boundaries():
    result = parse_precision_cooling_matrix(
        PRECISION_COOLING_MATRIX,
        source_url="https://info.support.huawei.com/example",
        expected_count=2,
    )
    by_model = {row["model"]: row for row in result["candidates"]}
    assert by_model["Air-42"]["cooling_capacity_kw"] == 42.5
    assert by_model["Air-42"]["airflow_m3_h"] == 12000
    assert by_model["CDU-90"]["liquid_flow_l_min"] == 120
    assert by_model["CDU-90"]["input_power_kw"] is None
    assert result["review_required"]
    assert len(result["sha256"]) == 64


def test_precision_cooling_matrix_rejects_drift_duplicates_and_unofficial_sources():
    url = "https://www.deltapowersolutions.com/example"
    with pytest.raises(ValueError, match="Changed precision-cooling matrix shape"):
        parse_precision_cooling_matrix(PRECISION_COOLING_MATRIX, source_url=url, expected_count=3)
    duplicate = PRECISION_COOLING_MATRIX + PRECISION_COOLING_MATRIX.splitlines(keepends=True)[1]
    with pytest.raises(ValueError, match="Duplicate precision-cooling row"):
        parse_precision_cooling_matrix(duplicate, source_url=url, expected_count=2)
    with pytest.raises(ValueError, match="Unsupported official precision-cooling"):
        parse_precision_cooling_matrix(
            PRECISION_COOLING_MATRIX,
            source_url="https://example.com/table.csv",
            expected_count=2,
        )


def test_precision_cooling_matrix_accepts_exact_immersion_rows_without_scalar_capacity():
    immersion = PRECISION_COOLING_MATRIX.decode().splitlines()
    immersion[1] = immersion[1].replace(",crac,42.5,", ",immersion,,")
    result = parse_precision_cooling_matrix(
        ("\n".join([immersion[0], immersion[1]]) + "\n").encode(),
        source_url="https://en.envicool.com/example.pdf",
        expected_count=1,
    )
    assert result["candidates"][0]["category"] == "immersion"
    assert result["candidates"][0]["cooling_capacity_kw"] is None


def test_precision_cooling_matrix_accepts_exact_daikin_chiller_rows():
    header = PRECISION_COOLING_MATRIX.splitlines()[0]
    daikin_row = (
        b"Daikin,EWAT-CZN,016; cooling-only,chiller,15.9,12/7 C entering/leaving "
        b"water; 35 C ambient,,5.5,,48,,,,,EWAT-CZN table / 016"
    )
    result = parse_precision_cooling_matrix(
        header + b"\n" + daikin_row + b"\n",
        source_url=(
            "https://www.daikin.eu/content/dam/internet-denv/catalogues_brochures/"
            "industrial/Chillers_Catalogue_2026-ECPEN26-411.pdf"
        ),
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["category"] == "chiller"
    assert candidate["cooling_capacity_kw"] == 15.9
    assert candidate["input_power_kw"] == 5.5
    assert candidate["liquid_flow_l_min"] == 48


def test_power_equipment_matrix_stages_exact_boundaries():
    result = parse_power_equipment_matrix(
        POWER_MATRIX,
        source_url="https://www.eaton.com/example/transformers.html",
        expected_count=2,
    )
    by_category = {row["category"]: row for row in result["candidates"]}
    transformer = by_category["transformer"]
    switchgear = by_category["switchgear"]
    assert transformer["apparent_power_kva"] == 400
    assert transformer["max_voltage_kv"] == 12
    assert transformer["max_current_a"] is None
    assert switchgear["max_voltage_kv"] == 24
    assert switchgear["max_short_circuit_ka"] == 25
    assert switchgear["max_current_a"] == 2000
    assert result["review_required"]
    assert len(result["sha256"]) == 64


@pytest.mark.parametrize(
    ("source_url", "expected_count"),
    [
        ("https://example.com/table.csv", 2),
        ("https://www.siemens.com/example/table.csv", 3),
    ],
)
def test_power_equipment_matrix_rejects_unbounded_input(source_url, expected_count):
    with pytest.raises(ValueError):
        parse_power_equipment_matrix(
            POWER_MATRIX,
            source_url=source_url,
            expected_count=expected_count,
        )


def test_server_accelerator_matrix_preserves_power_boundary_and_range():
    result = parse_server_accelerator_matrix(
        SERVER_MATRIX,
        source_url=(
            "https://www.delltechnologies.com/asset/en-us/products/servers/"
            "briefs-summaries/poweredge-server-gpu-matrix.pdf"
        ),
        expected_count=2,
    )
    by_accelerator = {row["accelerator_model"]: row for row in result["candidates"]}
    assert by_accelerator["X1"]["max_power_w"] == 600
    assert by_accelerator["X1"]["server_generation"] == "17th"
    assert by_accelerator["X2"]["max_power_w"] is None
    assert by_accelerator["X2"]["server_generation"] == "16th"
    assert by_accelerator["X2"]["max_power_text"] == "350-400 W"
    assert result["review_required"]
    assert len(result["sha256"]) == 64


def test_server_accelerator_matrix_keeps_generation_specific_identity():
    header = SERVER_MATRIX.splitlines()[0]
    first = SERVER_MATRIX.splitlines()[1].replace(b",17th,", b",16th,")
    second = SERVER_MATRIX.splitlines()[1].replace(b",17th,", b",15th,")
    result = parse_server_accelerator_matrix(
        b"\n".join((header, first, second, b"")),
        source_url="https://www.dell.com/server-gpu-matrix.csv",
        expected_count=2,
    )
    assert [row["server_generation"] for row in result["candidates"]] == [
        "15th",
        "16th",
    ]


def test_server_shipping_matrix_preserves_unknown_and_maximum_quantities():
    result = parse_server_accelerator_shipping_matrix(
        SERVER_SHIPPING_MATRIX,
        source_url="https://www.delltechnologies.com/poweredge-gpu-matrix.pdf",
        expected_count=2,
    )
    by_accelerator = {row["accelerator_model"]: row for row in result["candidates"]}
    assert by_accelerator["X1"]["max_shipping_quantity"] == 4
    assert by_accelerator["X2"]["max_shipping_quantity"] is None
    assert result["review_required"]


@pytest.mark.parametrize(
    ("source_url", "expected_count"),
    [("https://example.com/matrix.csv", 2), ("https://www.dell.com/matrix.csv", 3)],
)
def test_server_shipping_matrix_rejects_unbounded_input(source_url, expected_count):
    with pytest.raises(ValueError):
        parse_server_accelerator_shipping_matrix(
            SERVER_SHIPPING_MATRIX,
            source_url=source_url,
            expected_count=expected_count,
        )


def test_generator_matrix_preserves_dcc_apparent_power_boundary():
    result = parse_generator_rating_matrix(
        GENERATOR_MATRIX,
        source_url="https://www.mtu-solutions.com/example.pdf",
        expected_count=2,
    )
    by_frequency = {row["frequency_hz"]: row for row in result["candidates"]}
    assert by_frequency[50.0]["data_center_continuous_kva"] == 1600
    assert by_frequency[50.0]["prime_emergency_kva"] == 1600
    assert by_frequency[60.0]["data_center_continuous_kva"] == 1125
    assert by_frequency[60.0]["prime_kva"] == 1125
    assert "output_power_kw" not in by_frequency[50.0]
    assert result["review_required"]
    assert len(result["sha256"]) == 64


@pytest.mark.parametrize(
    ("source_url", "expected_count"),
    [("https://example.com/table.pdf", 2), ("https://www.mtu-solutions.com/x.pdf", 3)],
)
def test_generator_matrix_rejects_unofficial_sources_and_drift(source_url, expected_count):
    with pytest.raises(ValueError):
        parse_generator_rating_matrix(
            GENERATOR_MATRIX,
            source_url=source_url,
            expected_count=expected_count,
        )


def test_dcp_generator_matrix_preserves_power_boundaries_and_frequency_identity():
    result = parse_generator_dcp_matrix(
        GENERATOR_DCP_MATRIX,
        source_url="https://baudouin.com/example.pdf",
        expected_count=2,
    )
    by_frequency = {row["frequency_hz"]: row for row in result["candidates"]}
    assert by_frequency[50.0]["engine_power_kwm"] == 575
    assert by_frequency[50.0]["output_power_kw"] == 500
    assert by_frequency[50.0]["apparent_power_kva"] == 625
    assert by_frequency[60.0]["speed_rpm"] == 1800
    assert result["review_required"]
    assert len(result["sha256"]) == 64


@pytest.mark.parametrize(
    ("source_url", "expected_count"),
    [("https://example.com/table.pdf", 2), ("https://baudouin.com/table.pdf", 3)],
)
def test_dcp_generator_matrix_rejects_unofficial_sources_and_drift(source_url, expected_count):
    with pytest.raises(ValueError):
        parse_generator_dcp_matrix(
            GENERATOR_DCP_MATRIX,
            source_url=source_url,
            expected_count=expected_count,
        )


@pytest.mark.parametrize(
    ("source_url", "expected_count"),
    [("https://example.com/matrix.csv", 2), ("https://www.dell.com/matrix.csv", 3)],
)
def test_server_accelerator_matrix_rejects_unbounded_input(source_url, expected_count):
    with pytest.raises(ValueError):
        parse_server_accelerator_matrix(
            SERVER_MATRIX,
            source_url=source_url,
            expected_count=expected_count,
        )


def test_supermicro_systems_stage_exact_rows_and_reconcile_statuses():
    result = parse_supermicro_nvidia_systems(
        SUPERMICRO_SYSTEMS,
        source_url="https://www.supermicro.com/en/accelerators/nvidia-certified-systems",
        expected_count=2,
    )
    by_model = {row["model"]: row for row in result["candidates"]}
    assert set(by_model) == {"AS-X200-B3RT-LCC", "SYS-X100-BRT"}
    assert by_model["SYS-X100-BRT"]["accelerator_power_w_per_gpu"] == 1000
    assert by_model["SYS-X100-BRT"]["memory_gb_per_gpu"] == 180
    assert by_model["AS-X200-B3RT-LCC"]["certification_states"] == [
        "NVIDIA-Certified",
        "NVIDIA-Qualified",
    ]
    assert result["review_required"]
    assert len(result["sha256"]) == 64


@pytest.mark.parametrize(
    ("source_url", "expected_count"),
    [
        ("https://example.com/table", 2),
        ("https://www.supermicro.com/en/accelerators/nvidia-certified-systems", 3),
    ],
)
def test_supermicro_systems_reject_unofficial_sources_and_drift(source_url, expected_count):
    with pytest.raises(ValueError):
        parse_supermicro_nvidia_systems(
            SUPERMICRO_SYSTEMS,
            source_url=source_url,
            expected_count=expected_count,
        )


def test_lenovo_comparison_stages_only_current_exact_options():
    result = parse_lenovo_gpu_comparison(
        LENOVO_COMPARISON,
        source_url="https://lenovopress.lenovo.com/lp2265-thinksystem-gpu-comparison",
        expected_count=1,
    )
    assert len(result["candidates"]) == 1
    candidate = result["candidates"][0]
    assert candidate["feature_code"] == "ABCD"
    assert candidate["gpu_count"] == 8
    assert candidate["tdp_w_per_gpu"] == 1000
    assert candidate["memory_gb_per_gpu"] == 192
    assert candidate["cooling_method"] == "Liquid / Water"
    assert result["review_required"]
    assert len(result["sha256"]) == 64


def test_lenovo_comparison_rejects_drift_and_unofficial_sources():
    with pytest.raises(ValueError, match="Changed Lenovo"):
        parse_lenovo_gpu_comparison(
            LENOVO_COMPARISON,
            source_url="https://lenovopress.lenovo.com/lp2265-thinksystem-gpu-comparison",
            expected_count=2,
        )
    with pytest.raises(ValueError, match="Unsupported official Lenovo"):
        parse_lenovo_gpu_comparison(
            LENOVO_COMPARISON,
            source_url="https://example.com/table",
            expected_count=1,
        )


def test_ups_matrix_accepts_siel_modular_kva_without_active_kw():
    content = (
        b"manufacturer,family,variant,apparent_power_kva,output_power_kw,"
        b"voltage_text,frequency_text,locator\n"
        b"SIEL,Safepower Modular SPM,1200 kVA cabinet,1200,,"
        b"380/400/415 Vac 3Ph+N,50/60 Hz,SPM frame table / 1200 kVA\n"
    )
    result = parse_ups_rating_matrix(
        content,
        source_url="https://www.sielups.com/example.pdf",
        expected_count=1,
    )
    candidate = result["candidates"][0]
    assert candidate["apparent_power_kva"] == 1200
    assert candidate["output_power_kw"] is None
    assert candidate["manufacturer"] == "SIEL"
