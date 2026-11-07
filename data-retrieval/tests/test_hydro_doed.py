"""Synthetic official-licence parsing, identity and coordinate-boundary checks."""

import copy
import json

import pytest

from energy_data_retrieval.hydro_catalogue import era
from energy_data_retrieval.hydro_catalogue.doed import new_record, parse_inventory


def html():
    headers = [
        "S No",
        "Project",
        "Capacity (MW)",
        "River",
        "Lic No",
        "Isuue Date",
        "Validity",
        "Promoter",
        "Address",
        "Latitiude N",
        "Longitude E",
        "VDC/District",
    ]
    cells = [
        "1",
        "Synthetic",
        "4.2",
        "Synthetic river",
        "092",
        "2068-01-28",
        "2103-01-27",
        "Synthetic promoter",
        "Excluded contact",
        "27 00",
        "28 00",
        "85 00",
        "86 00",
        "District",
    ]
    return (
        "<table><tr>"
        + "".join(f"<th>{x}</th>" for x in headers)
        + "</tr><tr>"
        + "".join(f"<td>{x}</td>" for x in cells)
        + "</tr></table>"
    )


def entry():
    return dict(
        inventory=parse_inventory(html())[0],
        review=dict(
            decision="reviewed_new_identity", licence="092", identity_basis="Synthetic review"
        ),
    )


def test_leading_zero_dates_and_bounds_are_not_converted():
    item = parse_inventory(html())[0]
    assert item["licence"] == "092"
    assert item["issue_date_raw"] == "2068-01-28"
    assert item["bounds_raw"] == ["27 00", "28 00", "85 00", "86 00"]
    assert "Excluded contact" not in json.dumps(item)
    row = new_record(entry(), now="2026-11-06T00:00:00Z")
    assert row["status"] == "unknown"
    assert row["aggregation_role"] == "unresolved"
    assert row.get("latitude") is None
    assert row.get("installed_capacity_mw") is None
    assert row.get("commissioning_date") is None
    assert json.loads(row["observations_json"])[0]["field"] == "licensed_capacity_mw"


@pytest.mark.parametrize(
    "old,new",
    [
        ("Capacity (MW)", "Capacity"),
        ("4.2", "-1"),
        ("4.2", "NaN"),
        ("<td>092</td>", "<td></td>"),
        ("<td>1</td>", "<td>2</td>"),
    ],
)
def test_reject_shape_numeric_or_identity_drift(old, new):
    with pytest.raises(ValueError):
        parse_inventory(html().replace(old, new))


def test_stable_official_identity_and_review_gate():
    e = entry()
    original = new_record(e, now="2026-11-06T00:00:00Z")
    changed = copy.deepcopy(e)
    changed["inventory"].update(name="Renamed", capacity_mw=9)
    assert new_record(changed, now="2026-11-06T00:00:00Z")["record_id"] == original["record_id"]
    changed["review"]["licence"] = "wrong"
    with pytest.raises(ValueError):
        new_record(changed, now="2026-11-06T00:00:00Z")


def test_nepal_collision_checked_by_shared_inserter(tmp_path, monkeypatch):
    monkeypatch.setattr(
        era,
        "load_records",
        lambda root: [dict(record_id="old", country_code="NPL", name="Synthetic", aliases=None)],
    )
    with pytest.raises(ValueError, match="Name collision"):
        era.accept_new(
            tmp_path,
            dict(reviewed_at="2026-11-06T00:00:00Z", accepted=[entry()]),
            tmp_path / "new.jsonl",
            record_factory=new_record,
        )
    assert not (tmp_path / "new.jsonl").exists()


def test_page_update_date_and_capture_specific_provenance():
    from energy_data_retrieval.hydro_catalogue.doed import parse_updated_date

    stamp = "Updated on - October 15, 2026"
    assert parse_updated_date(stamp + stamp) == "2026-10-15"
    for text in ("", stamp + " Updated on - October 16, 2026"):
        with pytest.raises(ValueError):
            parse_updated_date(text)
    row = new_record(
        entry(),
        now="2026-11-07T00:00:00Z",
        source_id="synthetic-new-capture",
        source_as_of="2026-10-15",
    )
    observation = json.loads(row["observations_json"])[0]
    assert observation["source_id"] == "synthetic-new-capture"
    assert observation["period"] == "2026-10-15"
    assert row["sources"] == ["synthetic-new-capture"]
    assert row["record_id"] == new_record(entry(), now="2026-11-06T00:00:00Z")["record_id"]
    with pytest.raises(ValueError, match="after retrieval"):
        new_record(entry(), now="2026-11-07T00:00:00Z", source_as_of="2026-11-08")


def reviewed_batch():
    one = entry()
    two = copy.deepcopy(one["inventory"])
    two.update(row=2, name="Different synthetic project", licence="093")
    return dict(
        parsed_inventory=[one["inventory"], two],
        partition=dict(first_row=1, last_row=2, total_source_rows=2, next_row=None),
        accepted=[one],
        held=[dict(inventory=two, reason="Synthetic unresolved scope")],
        new=1,
    )


def test_partition_is_exhaustive_disjoint_and_source_exact():
    from energy_data_retrieval.hydro_catalogue.doed import validate_reviewed_batch

    batch = reviewed_batch()
    validate_reviewed_batch(batch)
    for defect in ("missing", "duplicate", "changed", "cursor", "partition", "count"):
        changed = copy.deepcopy(batch)
        if defect == "missing":
            changed["held"] = []
        elif defect == "duplicate":
            changed["held"].append(changed["accepted"][0])
        elif defect == "changed":
            changed["accepted"][0]["inventory"] = dict(
                batch["accepted"][0]["inventory"], capacity_mw=9
            )
        elif defect == "cursor":
            changed["partition"]["next_row"] = 3
        elif defect == "partition":
            changed["partition"]["first_row"] = 0
        else:
            changed["new"] = 2
        with pytest.raises(ValueError):
            validate_reviewed_batch(changed)


def test_duplicate_name_outside_partition_is_not_accepted():
    from energy_data_retrieval.hydro_catalogue.doed import validate_reviewed_batch

    batch = reviewed_batch()
    batch["parsed_inventory"][1]["name"] = batch["parsed_inventory"][0]["name"]
    batch["partition"].update(last_row=1, next_row=2)
    batch["held"] = []
    with pytest.raises(ValueError, match="Duplicate source name"):
        validate_reviewed_batch(batch)
