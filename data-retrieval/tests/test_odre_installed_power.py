"""Synthetic regression cases for reviewed existing-project installed-power gaps."""

import json

import pytest

from energy_data_retrieval.pv_catalogue.odre import reviewed_installed_power_updates

EIC = "17W000000043200D"


def inputs():
    row = dict(
        codeeicresourceobject=EIC,
        nominstallation="Example PV",
        codetechnologie="PHOTV",
        nbinstallations=1,
        regime="En service",
        puismaxinstallee=1440,
        puismaxrac=900,
        private_contact="Not exported",
    )
    record = dict(
        record_id="existing",
        entity_type="projects",
        country_code="FRA",
        name="Example",
        capacity_ac_mw=1.4,
        capacity_basis="MWac",
        phases_json=json.dumps([{"Other IDs (unit/phase)": "ODRE: " + EIC}]),
    )
    return row, record


def stage(rows, records):
    return reviewed_installed_power_updates(
        rows, records, reviewed_crosswalks={"existing": EIC}, source_id="pinned"
    )


def test_installed_not_injection_and_original_untouched():
    row, record = inputs()
    before = json.dumps(record, sort_keys=True)
    result = stage([row], [record])[0]
    assert result["capacity_unspecified_mw"] == 1.44
    assert (
        not {"capacity_ac_mw", "capacity_dc_mw", "capacity_basis", "status", "phases_json"}
        & result.keys()
    )
    assert "Not exported" not in json.dumps(result)
    assert json.dumps(record, sort_keys=True) == before


@pytest.mark.parametrize(
    "changes",
    [
        {"nbinstallations": 2},
        {"nbinstallations": True},
        {"codetechnologie": "SOLAI"},
        {"regime": "Projet"},
        {"puismaxinstallee": float("nan")},
        {"puismaxinstallee": 5000},
        {"puismaxinstallee": 999},
        {"nominstallation": "CONFIDENTIEL"},
    ],
)
def test_source_scope_fails_closed(changes):
    row, record = inputs()
    row.update(changes)
    with pytest.raises(ValueError):
        stage([row], [record])


def test_duplicate_source_and_canonical_eics_fail():
    row, record = inputs()
    with pytest.raises(ValueError, match="Duplicate source"):
        stage([row, row], [record])
    other = dict(record, record_id="other")
    with pytest.raises(ValueError, match="nonunique"):
        stage([row], [record, other])


@pytest.mark.parametrize(
    "changes",
    [
        {"capacity_unspecified_mw": 2},
        {"name": "Example Confidentiel"},
        {"phases_json": "[]"},
        {"phases_json": json.dumps([{"Other IDs (unit/phase)": "ODRE: 17W000000043384E"}])},
    ],
)
def test_existing_values_and_identity_fail_closed(changes):
    row, record = inputs()
    record.update(changes)
    with pytest.raises(ValueError):
        stage([row], [record])


def test_external_registry_identity_also_participates_in_uniqueness():
    row, record = inputs()
    other = dict(record_id="other", external_ids_json=json.dumps({"odre_eic": EIC}))
    with pytest.raises(ValueError, match="nonunique"):
        stage([row], [record, other])
