"""Synthetic paired tables test rating, time and identity boundaries."""

import copy
import json
from typing import Any

import pytest

from energy_data_retrieval.hydro_catalogue.kengen import NAMES, enrich_reviewed, parse_statistics


def table_text():
    years = "2025 2024 2023 2022 2021\n"
    capacities = "\n".join(n + "  10 9 10 9 10 9 10 9 10 9" for n in NAMES[:9])
    generation = "\n".join(n + "  5 4 5 4 5 4 5 4 - -" for n in NAMES)
    return (
        "Installed vs Effective Capacity (MW)\n"
        + years
        + "Power Plant  Installed  Effective\nHYDRO\n"
        + capacities
        + "\nSmall Hydros  12 11\nHydro Total  100 90\fUnits Sent out (GWh)\n"
        + years
        + "Power Plant  Generated  Sales\nHYDRO\n"
        + generation
        + "\nTotal Hydro  900 800\f"
    )


def test_separate_columns_missing_years_and_excluded_aggregates():
    rows = parse_statistics(table_text())
    assert len(rows) == 13
    obs = rows[0]["observations"]
    assert [(o["field"], o["value"]) for o in obs[:2]] == [
        ("installed_capacity_mw", 10),
        ("effective_capacity_mw", 9),
    ]
    assert obs[10]["field"] == "annual_generation_gwh"
    assert obs[11]["field"] == "sold_energy_gwh"
    assert obs[10]["period"] == "FY ended 2025-06-30"
    assert obs[-1]["value"] is None
    assert obs[-1]["original_value"] == "-"
    assert "p. 249" in obs[-1]["locator"]
    assert len(rows[-1]["observations"]) == 10


@pytest.mark.parametrize(
    "bad",
    [
        lambda s: s.replace("2025 2024", "2024 2025"),
        lambda s: s.replace("Installed  Effective", "Effective  Installed"),
        lambda s: s.replace("Generated  Sales", "Sales  Generated"),
        lambda s: s.replace("Tana  10 9", "Tana  10"),
        lambda s: s.replace("Tana  10 9", "Tana  -10 9"),
        lambda s: s.replace("Tana  10 9", "Tana  nan 9"),
        lambda s: s.replace("Tana  10 9 10 9 10 9 10 9 10 9", ""),
        lambda s: s.replace("HYDRO\n", "HYDRO\nTana  10 9 10 9 10 9 10 9 10 9\n", 1),
    ],
)
def test_rejects_table_drift_before_acceptance(bad):
    with pytest.raises(ValueError):
        parse_statistics(bad(table_text()))


def test_explicit_identity_idempotence_and_no_current_rating_promotion():
    old = dict(
        record_id="synthetic",
        country_code="KEN",
        name="Tana",
        owner_names=["Kenya Electric Generating Company"],
        extensions_json="{}",
        observations_json="[]",
        field_sources_json="{}",
        evidence_json="{}",
        sources=[],
        created_at="2020-01-01",
        status="unknown",
        installed_capacity_mw=None,
        aggregation_role="unresolved",
    )
    entry: dict[str, Any] = dict(
        record_id="synthetic",
        canonical_name="Tana",
        decision="accepted_owner_identity",
        identity_basis="Synthetic reviewed match",
        inventory=parse_statistics(table_text())[0],
    )
    original = copy.deepcopy(old)
    new = enrich_reviewed(old, entry, now="2026-11-06T00:00:00Z")
    assert old == original
    assert new["created_at"] == old["created_at"]
    assert new["installed_capacity_mw"] is None
    assert new["status"] == "unknown"
    assert new["aggregation_role"] == "unresolved"
    assert len(json.loads(new["observations_json"])) == 20
    assert enrich_reviewed(new, entry, now="2026-11-07T00:00:00Z") == new
    with pytest.raises(ValueError, match="identity"):
        enrich_reviewed({**old, "country_code": "UGA"}, entry, now="2026-11-06")
    with pytest.raises(ValueError, match="identity"):
        enrich_reviewed(old, {**entry, "canonical_name": "Turkwel"}, now="2026-11-06")
    altered = copy.deepcopy(entry)
    altered["inventory"]["observations"][0]["value"] = 11
    with pytest.raises(ValueError, match="conflict"):
        enrich_reviewed(new, altered, now="2026-11-06")


def test_zero_is_not_missing_and_wrong_station_is_rejected():
    rows = parse_statistics(table_text().replace("Tana  10 9", "Tana  0 0"))
    assert rows[0]["observations"][0]["value"] == 0
    assert rows[0]["observations"][1]["value"] == 0
    with pytest.raises(ValueError, match="complete station"):
        enrich_reviewed(
            dict(
                record_id="id",
                name="Tana",
                country_code="KEN",
                owner_names=["Kenya Electric Generating Company"],
            ),
            dict(
                record_id="id",
                canonical_name="Tana",
                decision="accepted_owner_identity",
                inventory=rows[1],
            ),
            now="2026-11-06",
        )
