"""Synthetic NVE records test hydraulic and identity boundaries."""

import json

import pytest

from energy_data_retrieval.hydro_catalogue.nve import parse_nve

NOW = "2026-11-05T08:50:00Z"


def raw(**changes):
    return {
        "VannKraftverkID": 1,
        "Navn": "Synthetic",
        "VannKVTypeID": "K",
        "MaksYtelse": 5,
        "ErIDrift": True,
        "UnderBygging": False,
        "Kraftverkstatus": "Idrift",
        "MidProd_91_20": 12,
        **changes,
    }


def parse(*rows):
    return parse_nve(json.dumps(rows), source_id="synthetic", now=NOW)


def test_pumps_cannot_be_generating_plants():
    rows, ledger = parse(raw(VannKVTypeID="P"))
    assert not rows
    assert ledger[0]["decision"] == "excluded_pump_only"


def test_pumped_capability_not_energy_or_pumping_power():
    rows, _ = parse(raw(VannKVTypeID="PK"))
    row = rows[0]
    assert row["technology"] == "pumped_storage"
    assert "pumping_capacity_mw" not in row
    assert "storage_capacity_mwh" not in row
    assert row["aggregation_role"] == "unresolved"
    assert "latitude" not in row
    assert json.loads(row["observations_json"])[0]["kind"] == "modeled"


def test_duplicate_registry_id_rejected_but_names_not_merged():
    with pytest.raises(ValueError, match="duplicate"):
        parse(raw(), raw())
    rows, _ = parse(raw(), raw(VannKraftverkID=2))
    assert len(rows) == 2
    assert rows[0]["record_id"] != rows[1]["record_id"]


@pytest.mark.parametrize(
    "changes",
    [
        {"MaksYtelse": -1},
        {"MaksYtelse": True},
        {"MaksYtelse": float("nan")},
        {"Kraftverkstatus": "Ute av drift"},
        {"UnderBygging": True},
        {"VannKVTypeID": "new_type"},
    ],
)
def test_bad_values_quarantined(changes):
    rows, ledger = parse(raw(**changes))
    assert not rows
    assert ledger[0]["decision"] == "quarantined"


def test_retired_rating_not_current_installed_capacity():
    rows, _ = parse(raw(ErIDrift=False, Kraftverkstatus="Ute av drift"))
    assert rows[0]["status"] == "decommissioned"
    assert "installed_capacity_mw" not in rows[0]


def test_replay_and_registry_identity_stable():
    first, _ = parse(raw())
    second, _ = parse(raw(Navn="Renamed", MaksYtelse=6))
    assert first[0]["record_id"] == second[0]["record_id"]
    assert parse(raw()) == parse(raw())
