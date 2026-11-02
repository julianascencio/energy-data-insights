"""Publication partitions must never relax the complete-source review gate."""

import copy
import hashlib
import runpy
from pathlib import Path
from typing import Any

import pytest

from energy_data_retrieval.pv_catalogue.gem_batches import select_reviewed_gem_batch


@pytest.fixture
def fixture():
    rows: list[dict[str, Any]] = [
        {
            "record_id": f"{prefix}-synthetic",
            "entity_type": "projects",
            "country_code": country,
            "sources": ["gem"],
        }
        for prefix, country in [("00", "CHL"), ("7f", "CHL"), ("80", "DEU"), ("ff", "FRA")]
    ]
    review = {
        "source_id": "gem",
        "accepted": 4,
        "accepted_ids_sha256": hashlib.sha256(
            "\n".join(sorted(r["record_id"] for r in rows)).encode()
        ).hexdigest(),
    }
    summary = {
        "new_projects": 4,
        "batches": [
            {
                "batch": 1,
                "prefix_start": "00",
                "prefix_end": "7f",
                "new_projects": 2,
                "countries": 1,
                "new_country_counts": {"CHL": 2},
            },
            {
                "batch": 2,
                "prefix_start": "80",
                "prefix_end": "ff",
                "new_projects": 2,
                "countries": 2,
                "new_country_counts": {"DEU": 1, "FRA": 1},
            },
        ],
    }
    return rows, review, summary


def test_disjoint_exhaustive_unchanged_selection(fixture):
    rows, review, summary = fixture
    original = copy.deepcopy(rows)
    a = select_reviewed_gem_batch(rows, review=review, summary=summary, batch=1)
    b = select_reviewed_gem_batch(rows, review=review, summary=summary, batch=2)
    assert a + b == rows == original
    assert {r["record_id"] for r in a}.isdisjoint(r["record_id"] for r in b)


@pytest.mark.parametrize("mutation", ["partial", "duplicate", "changed_id", "source", "entity"])
def test_reject_bad_input(fixture, mutation):
    rows, review, summary = fixture
    if mutation == "partial":
        rows.pop()
    elif mutation == "duplicate":
        rows.append(rows[0])
    elif mutation == "changed_id":
        rows[0]["record_id"] = "01-other"
    elif mutation == "source":
        rows[0]["sources"] = ["other"]
    else:
        rows[0]["entity_type"] = "inverters"
    with pytest.raises(ValueError):
        select_reviewed_gem_batch(rows, review=review, summary=summary, batch=1)


@pytest.mark.parametrize(
    "mutation", ["overlap", "gap", "count", "country", "number", "range", "total"]
)
def test_reject_bad_ledger(fixture, mutation):
    rows, review, summary = fixture
    a, b = summary["batches"]
    if mutation == "overlap":
        b["prefix_start"] = "7f"
    elif mutation == "gap":
        a["prefix_start"] = "01"
    elif mutation == "count":
        b["new_projects"] = 3
    elif mutation == "country":
        b["new_country_counts"] = {"DEU": 2}
    elif mutation == "number":
        b["batch"] = 1
    elif mutation == "range":
        b["prefix_end"] = "GG"
    else:
        summary["new_projects"] = 5
    with pytest.raises(ValueError):
        select_reviewed_gem_batch(rows, review=review, summary=summary, batch=1)


def test_unknown_batch(fixture):
    rows, review, summary = fixture
    with pytest.raises(ValueError, match="Unknown batch"):
        select_reviewed_gem_batch(rows, review=review, summary=summary, batch=3)


@pytest.mark.parametrize("option", [["--batch", "4"], ["--summary", "missing.json"]])
def test_cli_requires_paired_options_before_read_or_write(monkeypatch, tmp_path, option):
    output = tmp_path / "not-created.jsonl"
    monkeypatch.setattr(
        "sys.argv",
        [
            "stage_pv_gem.py",
            "--input",
            "missing.xlsx",
            "--review",
            "missing.json",
            "--output",
            str(output),
            *option,
        ],
    )
    with pytest.raises(SystemExit) as error:
        runpy.run_path(
            str(Path(__file__).parents[2] / "scripts/stage_pv_gem.py"), run_name="__main__"
        )
    assert error.value.code == 2
    assert not output.exists()
