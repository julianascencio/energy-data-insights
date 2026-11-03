"""Synthetic identity and changed-source tests; no live provider access."""

from pathlib import Path

import pytest

from energy_data_retrieval.data_center_catalogue.inventories import parse_named_inventory

CONTENT = (Path(__file__).parent / "fixtures/data_centers/named-inventory.html").read_bytes()


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
