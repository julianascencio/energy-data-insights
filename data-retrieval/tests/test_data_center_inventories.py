"""Synthetic identity and changed-source tests; no live provider access."""

from pathlib import Path

import pytest

from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_cdu_spec_matrix,
    parse_named_inventory,
)

CONTENT = (Path(__file__).parent / "fixtures/data_centers/named-inventory.html").read_bytes()
CDU_MATRIX = (Path(__file__).parent / "fixtures/data_centers/cdu-matrix.csv").read_bytes()


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
