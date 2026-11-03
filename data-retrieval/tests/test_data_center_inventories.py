"""Synthetic identity and changed-source tests; no live provider access."""

from pathlib import Path

import pytest

from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_cdu_spec_matrix,
    parse_generator_rating_matrix,
    parse_lenovo_gpu_comparison,
    parse_named_inventory,
    parse_power_equipment_matrix,
    parse_server_accelerator_matrix,
    parse_server_accelerator_shipping_matrix,
    parse_supermicro_nvidia_systems,
)

CONTENT = (Path(__file__).parent / "fixtures/data_centers/named-inventory.html").read_bytes()
CDU_MATRIX = (Path(__file__).parent / "fixtures/data_centers/cdu-matrix.csv").read_bytes()
POWER_MATRIX = (
    Path(__file__).parent / "fixtures/data_centers/power-equipment-matrix.csv"
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
LENOVO_COMPARISON = (
    Path(__file__).parent / "fixtures/data_centers/lenovo-gpu-comparison.html"
).read_bytes()
SUPERMICRO_SYSTEMS = (
    Path(__file__).parent / "fixtures/data_centers/supermicro-nvidia-systems.html"
).read_bytes()


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
