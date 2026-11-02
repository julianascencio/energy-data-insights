"""Synthetic applications: scope, privacy allowlist, unit conflicts and identity."""

import json

import pytest

from energy_data_retrieval.bess_catalogue.nemsa import parse_nemsa_minigrid_html

URL = "https://nemsa.gov.ng/admin-request-for-inspection-rea-solar-mini-grid/entry/123/"


def application(community="Example", storage="153,600", state="Site state"):
    rows = [
        ("First Name", "PRIVATE_PERSON"),
        ("State", "Company state"),
        ("Tax Registration Number", "PRIVATE_TAX"),
        ("Name of the Village/Community", community),
        ("State", state),
        ("Total Storage Capacity (kwh)", storage),
        ("Storage Technology/Manufacturer", "Lithium / supplier"),
        ("Date of Installation of Mini-Grid", "October 1, 2024"),
        ("Mini-Grid Owner (Full Name)", "PRIVATE_OWNER"),
        ("Phone", "PRIVATE_PHONE"),
        ("Manufacturer", "PV supplier"),
        ("Model", "PV1"),
        ("Manufacturer", "Battery supplier"),
        ("Model", "B1"),
        ("Technology", "LFP"),
        ("Cell Voltage (V)", "3.2"),
        ("Battery Voltage", "48"),
        ("C10 Capacity", "200"),
        ("Total C10 capacity [kWh]", "153.6"),
        ("Email", "PRIVATE_EMAIL"),
    ]
    return "<table>" + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows) + "</table>"


def parse(html):
    return parse_nemsa_minigrid_html(html.encode(), source_url=URL)


def test_units_scope_and_private_fields_are_not_normalized_or_leaked():
    row = parse(application())
    assert row["site_reported"]["State"] == "Site state"
    assert row["site_reported"]["Total Storage Capacity (kwh)"] == "153,600"
    assert row["battery_capacity_observations"][-1]["reported_value"] == "153.6"
    assert row["battery_reported"][0]["Model"] == "B1"
    assert "PRIVATE" not in json.dumps(row)
    assert "status" not in row and "energy_capacity_mwh" not in row and "record_id" not in row
    assert row["review_required"] is True


def test_malformed_capacity_is_preserved_for_review():
    assert (
        parse(application(storage="Lithium ion"))["site_reported"]["Total Storage Capacity (kwh)"]
        == "Lithium ion"
    )


def test_identical_nested_page_copies_collapse():
    nested = parse(application() + "<table><tr><td>" + application() + "</td></tr></table>")
    flat = parse(application() + application())
    assert nested.pop("source_sha256") != flat.pop("source_sha256")
    assert nested == flat


def test_conflicting_copies_do_not_silently_choose_one():
    with pytest.raises(ValueError, match="Conflicting"):
        parse(application() + application(storage="99"))


def test_community_identity_is_not_fuzzy_merged():
    with pytest.raises(ValueError, match="Conflicting"):
        parse(application() + application(community="Example phase 2"))
    assert parse(application())["external_id"] == {"nemsa_inspection_entry": "123"}


@pytest.mark.parametrize(
    "change",
    ["Name of the Village/Community", "Storage Technology/Manufacturer", "Battery Voltage"],
)
def test_source_layout_drift_fails_closed(change):
    with pytest.raises(ValueError):
        parse(application().replace(change, "Changed header"))


def test_wrong_endpoint_rejected():
    with pytest.raises(ValueError, match="URL"):
        parse_nemsa_minigrid_html(
            application().encode(), source_url="https://example.com/entry/123/"
        )
