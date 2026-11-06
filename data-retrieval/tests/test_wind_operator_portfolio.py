"""Offline synthetic operator tables test date, capacity and identity boundaries."""

import hashlib
import json
from copy import deepcopy

import pytest

from energy_data_retrieval.wind_catalogue.operator_portfolio import stage_operator_portfolio

ORIGINAL = b"Synthetic operator table fixture, not real project evidence"


@pytest.fixture
def document():
    return dict(
        sha256=hashlib.sha256(ORIGINAL).hexdigest(),
        source_id="fixture",
        operator="Example",
        url="https://example.org",
        as_of="2024-03-31",
        published_at="2024-07-15",
        expected_names=["Farm"],
        entries=[
            dict(
                source_name="Farm",
                country_code="ESP",
                technology="onshore",
                identity_basis="Reviewed source project, no catalogue collision",
                locator="p1 table1",
                facts=dict(
                    turbine_count=3,
                    turbine_rating_mw=2.1,
                    rating_basis="reported_fleet_average",
                    capacity_mw=6,
                    capacity_basis="contracted",
                    cod="2017-07",
                    cod_precision="month",
                ),
            )
        ],
    )


def stage(document, existing=None, original=ORIGINAL, now="2026-11-06T12:00:00Z"):
    return stage_operator_portfolio(document, original, existing or [], now=now)


def test_average_rating_and_month_date_never_supply_installed_mw_or_exact_model(document):
    row = stage(document)[0][0]
    assert row.get("installed_capacity_mw") is None
    assert row.get("commissioning_date") is None
    assert row.get("turbine_model") is None
    assert row["aggregation_role"] == "unresolved"
    facts = json.loads(row["extensions_json"])["operator_portfolio_observations"][0]["facts"]
    assert facts["count_times_rating_check"]["value"] == 6.3
    assert facts["capacity_mw"] == 6
    assert facts["cod"] == "2017-07"


def test_enrichment_preserves_scalars_creation_and_is_idempotent(document):
    row = stage(document)[0][0]
    original_creation = row["created_at"]
    entry = document["entries"][0]
    entry.update(record_id=row["record_id"], expected_name="Farm")
    replay = stage(document, [row], now="2026-11-07T00:00:00Z")[0][0]
    assert replay == row
    changed = deepcopy(document)
    changed["source_id"] = "later"
    changed["entries"][0]["facts"]["turbine_count"] = 4
    enriched = stage(changed, [row])[0][0]
    assert enriched["turbine_count"] == 3
    assert enriched["created_at"] == original_creation
    assert len(json.loads(enriched["extensions_json"])["operator_portfolio_observations"]) == 2
    with pytest.raises(ValueError, match="Immutable"):
        stage(
            changed,
            [enriched | {"extensions_json": row["extensions_json"].replace("fixture", "later")}],
        )


@pytest.mark.parametrize(
    "mutation", ["checksum", "missing", "duplicate", "date", "crosswalk", "basis", "rating"]
)
def test_invalid_review_fails_closed(document, mutation):
    if mutation == "checksum":
        document["sha256"] = "0" * 64
    if mutation == "missing":
        document["entries"] = []
    if mutation == "duplicate":
        document["entries"] *= 2
    if mutation == "date":
        document["as_of"] = "2025-01-01"
    if mutation == "crosswalk":
        document["entries"][0]["identity_basis"] = ""
    if mutation == "basis":
        document["entries"][0]["facts"]["capacity_basis"] = "installed"
    if mutation == "rating":
        document["entries"][0]["facts"]["turbine_rating_mw"] = float("nan")
    with pytest.raises(ValueError):
        stage(document)


def test_identity_hold_is_logged_without_project(document):
    document["entries"][0]["hold_reason"] = "Original registry crosswalk missing"
    records, ledger = stage(document)
    assert records == []
    assert ledger[0]["decision"] == "deferred_identity"
