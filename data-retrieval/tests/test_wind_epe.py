"""Independent coverage, identity and category-boundary checks for EPE SIGA."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from energy_data_retrieval.wind_catalogue.epe import ceg_key, parse_partition, reconcile

FIXTURE = Path(__file__).parent / "fixtures/wind_epe/bahia_one.json"
NOW = "2026-11-05T18:12:00Z"


def parse(
    doc=None,
    *,
    sha256: list[str] | None = None,
    expected_ids: list[int] | None = None,
    confirmed_ids: list[int] | None = None,
    state: str = "BA",
    retrieved_at: str = NOW,
):
    data = FIXTURE.read_bytes() if doc is None else json.dumps(doc).encode()
    return parse_partition(
        [data],
        sha256=[hashlib.sha256(data).hexdigest()] if sha256 is None else sha256,
        expected_ids=[68] if expected_ids is None else expected_ids,
        confirmed_ids=[68] if confirmed_ids is None else confirmed_ids,
        state=state,
        retrieved_at=retrieved_at,
    )


def existing():
    return [
        dict(
            record_id="stable",
            entity_type="projects",
            country_code="BRA",
            name="Macaúbas",
            external_ids_json=json.dumps(
                dict(wri_gppd="BRA0030283", aneel_ceg="EOL.CV.BA.030283-0.01")
            ),
            extensions_json="{}",
            field_sources_json="{}",
            evidence_json="{}",
            sources=["prior"],
            created_at="2020-01-01T00:00:00Z",
            aggregation_role="unresolved",
            status="unknown",
            installed_capacity_mw=None,
        )
    ]


def attach(candidates, rows):
    return reconcile(candidates, rows, source_id="epe", identity_source_id="wri", now=NOW)


def test_real_row_preserves_quantities_dates_and_native_ceg():
    row = parse()[0]
    assert row["normalized_power"] == dict(
        authorized_mw=35.07, inspected_mw=35.07, physical_guarantee_mw=13.4
    )
    assert row["observation_date"] == "2026-01-13"
    assert row["original"]["datentradaoperacao"] == "2012-07-06"
    assert row["ceg"].endswith(".1")
    assert row["positional_accuracy_m"] is None
    assert row["wri_gppd"] == "BRA0030283"


def test_zero_and_unknown_are_distinct():
    doc = json.loads(FIXTURE.read_text())
    doc["features"][0]["attributes"].update(mdapotenciaoutorgadakw=0, mdapotenciafiscalizadakw=None)
    row = parse(doc)[0]
    assert row["normalized_power"]["authorized_mw"] == 0
    assert row["normalized_power"]["inspected_mw"] is None


@pytest.mark.parametrize(
    "options",
    [
        dict(expected_ids=[68, 69], confirmed_ids=[68, 69]),
        dict(confirmed_ids=[69]),
        dict(expected_ids=[68, 68]),
        dict(sha256=["bad"]),
    ],
)
def test_partition_failures(options):
    with pytest.raises(ValueError):
        parse(**options)


@pytest.mark.parametrize(
    "field,value",
    [
        ("mdapotenciaoutorgadakw", -1),
        ("mdapotenciafiscalizadakw", True),
        ("mdagarantiafisicakw", float("nan")),
        ("datentradaoperacao", "2012"),
        ("datgeracaoconjuntodados", None),
        ("sigufprincipal", "RN"),
        ("sigtipogeracao", "UFV"),
        ("codceg", "EOL.CV.RN.030283-0.1"),
    ],
)
def test_reject_invalid_fields(field, value):
    doc = json.loads(FIXTURE.read_text())
    doc["features"][0]["attributes"][field] = value
    with pytest.raises(ValueError):
        parse(doc)


@pytest.mark.parametrize("change", ["truncated", "duplicate", "crs", "coordinate", "server_error"])
def test_reject_incomplete_or_inconsistent_response(change):
    doc = json.loads(FIXTURE.read_text())
    if change == "truncated":
        doc["exceededTransferLimit"] = True
    elif change == "duplicate":
        doc["features"] *= 2
    elif change == "crs":
        doc["spatialReference"]["wkid"] = 4674
    elif change == "coordinate":
        doc["features"][0]["geometry"]["x"] = 181
    else:
        doc["error"] = {"code": 500}
    with pytest.raises(ValueError):
        parse(doc)


def test_enrichment_preserves_every_scalar_and_creation_time_and_replays():
    old = existing()
    saved = copy.deepcopy(old)
    rows, ledger = attach(parse(), old)
    assert old == saved
    assert ledger[0]["decision"] == "enriched"
    changed = {k for k in rows[0] if rows[0].get(k) != old[0].get(k)}
    assert changed == {
        "extensions_json",
        "field_sources_json",
        "evidence_json",
        "sources",
        "updated_at",
        "last_verified_at",
    }
    again, _ = attach(parse(), rows)
    assert rows == again
    altered = parse()
    altered[0]["normalized_power"]["authorized_mw"] = 100
    with pytest.raises(ValueError, match="Immutable"):
        attach(altered, rows)


@pytest.mark.parametrize("change", ["missing", "name", "duplicate", "revision"])
def test_identity_holds(change):
    old = existing()
    if change == "missing":
        old = []
    elif change == "name":
        old[0]["name"] = "Macaúbas II"
    elif change == "duplicate":
        old.append({**old[0], "record_id": "other"})
    else:
        old[0]["external_ids_json"] = json.dumps(
            dict(wri_gppd="BRA0030283", aneel_ceg="EOL.CV.BA.030283-0.02")
        )
    rows, ledger = attach(parse(), old)
    assert rows == []
    assert ledger[0]["decision"] == "deferred"


def test_ceg_padding_only_not_different_revisions():
    assert ceg_key("EOL.CV.BA.030283-0.1") == ceg_key("EOL.CV.BA.030283-0.01")
    assert ceg_key("EOL.CV.BA.030283-0.1") != ceg_key("EOL.CV.BA.030283-0.02")
    items = parse()
    other = copy.deepcopy(items[0])
    other["ceg"] = "EOL.CV.BA.030283-0.2"
    rows, ledger = attach([*items, other], existing())
    assert not rows and len(ledger) == 2
