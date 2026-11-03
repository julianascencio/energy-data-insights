"""Independent synthetic tests of registry identity and capacity boundaries."""

import json
from pathlib import Path

import pytest

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json
from energy_data_retrieval.wind_catalogue import capacity_summary, stable_id, validate_catalogue
from energy_data_retrieval.wind_catalogue.gppd import evidence_record
from energy_data_retrieval.wind_catalogue.repd import reconcile_repd

FIXTURES = Path(__file__).parent / "fixtures/wind"
NOW = "2026-11-03T06:44:32Z"
OLD = "2026-11-03T00:00:00Z"


def baseline():
    return [
        evidence_record(
            {
                "record_id": stable_id("projects", external),
                "entity_type": "projects",
                "name": name,
                "record_scope": "farm",
                "capacity_scope": "Historical scope unresolved",
                "country_code": "GBR",
                "external_ids_json": canonical_json({"wri_gppd": external}),
                "aggregation_role": "unresolved",
                "status": "unknown",
                "technology": "unknown",
                "status_as_of": "2026-11-03",
                "status_date_basis": "historical review",
                "historical_capacity_mw": 10,
                "capacity_reference_year": 2021,
                "quality_status": "needs_review",
            },
            source_id="historical",
            now=OLD,
            locator="Synthetic baseline",
        )
        for external, name in [("GBR_TEST_1", "Synthetic Hill"), ("GBR_TEST_2", "Synthetic Sea")]
    ]


def run(text=None, crosswalk=None, rows=None):
    return reconcile_repd(
        text if text is not None else (FIXTURES / "repd_synthetic.csv").read_text(),
        crosswalk
        if crosswalk is not None
        else (FIXTURES / "repd_crosswalk_synthetic.csv").read_text(),
        rows if rows is not None else baseline(),
        source_id="repd",
        crosswalk_source_id="crosswalk",
        now=NOW,
        as_of="2026-08-03",
    )


def test_repd_reported_zero_pipeline_and_exclusions():
    rows, ledger = run()
    sources = {
        key: {
            "url": "https://example.org/synthetic",
            "publisher": "Synthetic fixture",
            "title": "Synthetic fixture",
            "license": "Synthetic",
            "retrieved_at": OLD,
            "original_availability": "Synthetic fixture, not a source capture",
        }
        for key in ("historical", "repd", "crosswalk")
    }
    validate_catalogue(rows, sources)
    assert len(rows) == len(ledger) == 2
    assert rows[0]["installed_capacity_mw"] == 0
    assert rows[0]["turbine_count"] == 0
    assert rows[1]["planned_capacity_mw"] == 12  # Not 3 turbines times 5 MW.
    assert rows[1].get("installed_capacity_mw") is None
    assert rows[1].get("turbine_model") is None
    assert rows[1].get("hub_height_m") is rows[1].get("tip_height_m") is None
    assert rows[1]["technology"] == "offshore_unspecified"
    assert all(r["created_at"] == OLD and r["updated_at"] == NOW for r in rows)
    assert all(r["status_as_of"] == "2026-08-03" for r in rows)
    assert capacity_summary(rows, "installed_capacity_mw")["excluded"] == 2
    assert [r["record_id"] for r in rows] == [r["record_id"] for r in baseline()]


@pytest.mark.parametrize(
    "old,new",
    [
        ("Operational,0", "Revised,0"),
        ("Synthetic Hill,Wind", "Different Hill,Wind"),
        (",100,,,", ",100,104,,"),
        ("Operational,0", "Operational,nan"),
        ("Scotland,0,2", "Scotland,1.5,2"),
    ],
)
def test_ambiguous_or_invalid_rows_are_held(old, new):
    rows, ledger = run(text=(FIXTURES / "repd_synthetic.csv").read_text().replace(old, new))
    assert len(rows) == 1
    assert ledger[0]["decision"].startswith("deferred")


def test_duplicate_id_and_missing_headers_fail():
    with pytest.raises(ValueError, match="duplicate"):
        run(text=(FIXTURES / "repd_synthetic.csv").read_text().replace("102,", "101,"))
    with pytest.raises(ValueError, match="headers"):
        run(text="name\nX\n")


def test_multiple_crosswalk_links_and_existing_primary_evidence_are_held():
    crosswalk = (FIXTURES / "repd_crosswalk_synthetic.csv").read_text()
    rows, ledger = run(crosswalk=crosswalk.replace("101,,", "101,104,"))
    assert len(rows) == 1 and "second" in ledger[0]["reason"]
    old = baseline()
    old[0]["status"] = "operational"
    rows, ledger = run(rows=old)
    assert len(rows) == 1 and "primary lifecycle" in ledger[0]["reason"]


def test_missing_capacity_stays_null():
    rows, _ = run(
        text=(FIXTURES / "repd_synthetic.csv").read_text().replace("Operational,0", "Operational,")
    )
    assert rows[0].get("installed_capacity_mw") is None
    assert rows[0]["historical_capacity_mw"] == 10
    assert json.loads(rows[0]["extensions_json"])["repd"]["height_of_turbines_m_original"] == "100"
