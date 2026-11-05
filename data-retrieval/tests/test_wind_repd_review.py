"""Synthetic offline planning applications; no real project claims."""

import csv
import hashlib
import io

import pytest

from energy_data_retrieval.wind_catalogue.repd_review import (
    FIELDS,
    REASON,
    review_unlinked_applications,
)


def fixture():
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["Ref ID", *FIELDS])
    writer.writeheader()
    for ref in ["1", "2", "3"]:
        writer.writerow(
            {"Ref ID": ref, "Site Name": f"Synthetic {ref}", "Technology Type": "Wind Onshore"}
        )
    original = output.getvalue().encode("cp1252")
    decisions = [
        dict(repd_id=i, name=f"Synthetic {i}", reason=REASON, source_id="test")
        for i in ["3", "1", "2"]
    ]
    return original, decisions, hashlib.sha256(original).hexdigest()


def test_exact_filtered_ledger_order_and_unknowns():
    data, ledger, sha = fixture()
    ledger.insert(0, dict(reason="already completed"))
    out = review_unlinked_applications(data, ledger, sha256=sha, offset=1, limit=2)
    assert [r["repd_id"] for r in out] == ["1", "2"]
    assert all(r["decision"] == "deferred_identity" for r in out)
    assert out[0]["facts"]["Planning Application Reference"] is None
    assert "installed_capacity_mw" not in out[0]
    assert review_unlinked_applications(data, ledger, sha256=sha, offset=3, limit=2) == []


@pytest.mark.parametrize("fault", ["hash", "bounds", "duplicate", "missing", "name"])
def test_mismatched_release_or_partition_rejected(fault):
    data, ledger, sha = fixture()
    offset = 0
    if fault == "hash":
        sha = "0" * 64
    elif fault == "bounds":
        offset = -1
    elif fault == "duplicate":
        ledger.append(ledger[0])
    elif fault == "missing":
        ledger[0]["repd_id"] = "999"
    else:
        ledger[0]["name"] = "Different"
    with pytest.raises(ValueError):
        review_unlinked_applications(data, ledger, sha256=sha, offset=offset, limit=2)
