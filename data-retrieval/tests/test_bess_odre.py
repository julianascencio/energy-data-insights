"""Synthetic ODRÉ classification, unit, identity and lifecycle boundaries."""

import json

import pytest

from energy_data_retrieval.bess_catalogue.odre import stage_odre_batteries


def row(**changes):
    result = dict(
        codeeicresourceobject="17W000000000001A",
        nominstallation="Synthetic battery",
        filiere="Stockage non hydraulique",
        technologie="Batterie",
        typestockage="BATTE",
        nbinstallations=1,
        regime="En service",
        puismaxinstallee=2000,
        energiestockable=4000,
        puismaxcharge=1800,
        puismaxrac=1500,
        puismaxraccharge=1700,
        datemiseenservice="02/03/2026",
        energieannuelleglissanteinjectee=99999999,
    )
    return result | changes


def stage(*rows):
    return stage_odre_batteries(json.dumps({"results": rows}).encode(), snapshot_date="2026-08-31")


def test_separate_ratings_and_industrial_date():
    r = stage(row())[0]
    assert (
        r["power_mw"],
        r["energy_mwh"],
        r["charging_power_mw"],
        r["connection_power_mw"],
        r["connection_charging_power_mw"],
    ) == (2, 4, 1.8, 1.5, 1.7)
    assert r["dates"]["datemiseenservice"] == "2026-03-02"
    assert "commercial_operation_date" not in r
    assert not r["review_flags"]


@pytest.mark.parametrize(
    "changes,flag",
    [
        ({"typestockage": "V.INE"}, "not_explicit_battery_only"),
        ({"filiere": "Solaire"}, "not_explicit_battery_only"),
        ({"nbinstallations": 10}, "aggregate_or_unknown_installation_count"),
        ({"nominstallation": "Confidentiel"}, "withheld_or_missing_name"),
        ({"datemiseenservice": "01/09/2026"}, "datemiseenservice_after_snapshot"),
    ],
)
def test_stages_exclusions_without_silently_classifying(changes, flag):
    assert flag in stage(row(**changes))[0]["review_flags"]


def test_energy_anomaly_preserved_not_scaled_or_replaced():
    r = stage(row(energiestockable=1))[0]
    assert r["energy_mwh"] is None
    assert r["energy_kwh_reported"] == 1
    assert r["energy_requires_review"]


def test_missing_energy_not_estimated():
    assert stage(row(energiestockable=None))[0]["energy_mwh"] is None


def test_duplicate_identity_fails():
    with pytest.raises(ValueError, match="Duplicate EIC"):
        stage(row(), row(nominstallation="Alias"))


@pytest.mark.parametrize("value", [-1, True, "2000", float("nan")])
def test_invalid_numeric_fails(value):
    with pytest.raises(ValueError):
        stage(row(puismaxinstallee=value))
