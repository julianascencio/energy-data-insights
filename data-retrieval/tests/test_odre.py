"""ODRE identity, privacy and unit guards use synthetic offline fixtures."""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from energy_data_retrieval.pv_catalogue.odre import (
    REQUIRED,
    read_odre_json,
    reviewed_odre_records,
    screen_odre_identities,
)


def native(eic="17W000000043200D", **changes):
    row = dict.fromkeys(REQUIRED)
    row.update(
        codeeicresourceobject=eic,
        nominstallation="Example solar park",
        codeinseecommuneimplantation="03100",
        codeinseecommune="03100",
        puismaxinstallee=12000,
        codetechnologie="PHOTV",
        nbinstallations=1,
        regime="En service",
        datemiseenservice="18/12/2013",
        gestionnaire="Enedis",
        commune="Diou",
        region="Auvergne",
        tensionraccordement="HTA",
        postesource="DIOU",
        puismaxrac=10000,
        nbgroupes=7,
        energieannuelleglissanteinjectee=12345,
        private_contact="Private person",
    )
    row.update(changes)
    return row


def read(rows):
    content = json.dumps(rows).encode()
    return read_odre_json(content, sha256=hashlib.sha256(content).hexdigest())


def mapped(rows, identities=None, existing=None):
    return reviewed_odre_records(
        rows,
        identities or rows,
        reviewed_ids={rows[0]["codeeicresourceobject"]},
        existing=existing or [],
        source_id="test",
        retrieved_at="2026-11-01T09:28:04Z",
        snapshot_date="2026-08-31",
    )


def test_mapping_retains_basis_dates_and_privacy():
    r = mapped(read([native()]))[0]
    assert r["capacity_unspecified_mw"] == 12
    assert r["commissioning_date"] == "2013-12-18"
    assert r["grid_operator"] == "Enedis"
    assert (
        not {
            "capacity_ac_mw",
            "capacity_dc_mw",
            "latitude",
            "longitude",
            "grid_voltage_kv",
            "locality",
            "owners",
            "operators",
            "inverter_count",
            "expected_generation_mwh_year",
        }
        & r.keys()
    )
    assert "Private person" not in json.dumps(r)
    ext = json.loads(r["extensions_json"])["odre"]
    assert ext["puismaxrac"] == 10000 and ext["energieannuelleglissanteinjectee"] == 12345


def test_explicit_voltage_and_missing_date():
    r = mapped([native(tensionraccordement="63 kV", datemiseenservice=None)])[0]
    assert r["grid_voltage_kv"] == 63 and "commissioning_date" not in r


def test_checksum_schema_duplicate_eic():
    with pytest.raises(ValueError, match="checksum"):
        read_odre_json(b"[]", sha256="0" * 64)
    with pytest.raises(ValueError, match="schema"):
        read([{}])
    with pytest.raises(ValueError, match="duplicate"):
        read([native(), native()])


@pytest.mark.parametrize(
    "change",
    [
        {"codetechnologie": "SOLAI"},
        {"nbinstallations": 2},
        {"nominstallation": "Confidentiel"},
        {"nominstallation": "Station PDL II"},
        {"nominstallation": "Ferme eolienne"},
        {"codeinseecommuneimplantation": "97101"},
        {"regime": "Projet"},
        {"puismaxinstallee": 9999},
        {"datemiseenservice": "01/09/2026"},
        {"datemiseenservice": "31/02/2020"},
        {"puismaxinstallee": -1},
    ],
)
def test_scope_and_invalid_values_fail_closed(change):
    with pytest.raises(ValueError):
        mapped(read([native(**change)]))


def test_sub_mw_names_and_shared_large_commune_flag_without_merging():
    first = native()
    other = native(
        "17W000000043384E",
        nominstallation="EXAMPLE Solar-Park",
        puismaxinstallee=50,
        codeinseecommuneimplantation="59000",
    )
    with pytest.raises(ValueError, match="identity"):
        mapped([first], [first, other])
    other = native("17W000000043384E", nominstallation="Other", puismaxinstallee=1000)
    risks = screen_odre_identities([first], [first, other], existing=[])
    assert "shared_commune_requires_project_scope_review" in risks[first["codeeicresourceobject"]]


def test_existing_alias_and_changed_export_are_held():
    first = native()
    with pytest.raises(ValueError, match="identity"):
        mapped(
            [first],
            existing=[
                {"name": "Old name", "aliases": ["Example solar park"], "country_code": "FRA"}
            ],
        )
    with pytest.raises(ValueError, match="identity"):
        mapped([first], [native(puismaxinstallee=13000)])


def test_allowlist_does_not_accept_other_rows():
    rows = [
        native(),
        native(
            "17W000000043384E", nominstallation="Other park", codeinseecommuneimplantation="59000"
        ),
    ]
    assert len(mapped(rows)) == 1


def test_null_aggregate_eics_keep_distinct_review_locators():
    rows = read(
        [
            native(codeeicresourceobject=None, nbinstallations=8),
            native(codeeicresourceobject=None, nbinstallations=9),
        ]
    )
    risks = screen_odre_identities(rows, [], existing=[])
    assert len(risks) == 2 and all(k.startswith("aggregate:") for k in risks)
    with pytest.raises(ValueError, match="Invalid"):
        read([native(codeeicresourceobject=None)])


@pytest.mark.parametrize("count", [True, 1.5, -1])
def test_installation_count_requires_positive_integer(count):
    with pytest.raises(ValueError, match="installation count"):
        read([native(nbinstallations=count)])


@pytest.mark.parametrize(
    "capacity,allowed", [(4999, False), (5000, True), (9999, True), (10000, False)]
)
def test_reviewed_capacity_partition_boundaries(capacity, allowed):
    row = native(puismaxinstallee=capacity)
    args: dict[str, Any] = dict(
        reviewed_ids={row["codeeicresourceobject"]},
        existing=[],
        source_id="test",
        retrieved_at="2026-11-02T00:00:00Z",
        snapshot_date="2026-08-31",
        minimum_kw=5000,
        maximum_kw=10000,
    )
    if allowed:
        assert (
            reviewed_odre_records([row], [row], **args)[0]["capacity_unspecified_mw"]
            == capacity / 1000
        )
    else:
        with pytest.raises(ValueError, match="identity"):
            reviewed_odre_records([row], [row], **args)


@pytest.mark.parametrize(
    "low,high", [(True, None), (999, None), (5000, 5000), (5000, 4999), (5000, float("nan"))]
)
def test_capacity_partition_invalid_bounds(low, high):
    with pytest.raises(ValueError):
        screen_odre_identities([], [], existing=[], minimum_kw=low, maximum_kw=high)


def test_lower_partition_keeps_national_identity_and_privacy_guards():
    row = native(puismaxinstallee=6000)
    other = native("17W000000043384E", nominstallation="Another park", puismaxinstallee=1000)
    risks = screen_odre_identities(
        [row], [row, other], existing=[], minimum_kw=5000, maximum_kw=10000
    )
    assert "shared_commune_requires_project_scope_review" in risks[row["codeeicresourceobject"]]
    row["nbinstallations"] = 2
    risks = screen_odre_identities([row], [], existing=[], minimum_kw=5000, maximum_kw=10000)
    assert "aggregate_not_single_project" in risks[row["codeeicresourceobject"]]
