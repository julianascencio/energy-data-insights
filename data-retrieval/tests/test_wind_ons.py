"""Synthetic offline ONS fixtures exercise identity and unit-boundary decisions."""

import copy
import csv
import hashlib
import io
import json

import pytest

from energy_data_retrieval.wind_catalogue.ons import COLUMNS, parse_partition, reconcile, wri_id


def native(**updates):
    row = dict.fromkeys(COLUMNS, "")
    row.update(
        nom_tipousina="EOLIELÉTRICA",
        ceg="EOL.CV.BA.030283-0.01",
        nom_usina="TEST WIND",
        cod_equipamento="UNIT-1",
        val_potenciaefetiva="0",
        dat_entradaoperacao="2020-02-29",
    )
    row.update(updates)
    return row


def parse(rows, **options):
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=COLUMNS, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    data = stream.getvalue().encode()
    return parse_partition(
        data,
        sha256=hashlib.sha256(data).hexdigest(),
        offset=options.get("offset", 0),
        limit=options.get("limit", 100),
        retrieved_at="2026-11-05T15:13:00Z",
    )


def existing():
    return dict(
        record_id="test-project",
        entity_type="projects",
        name="Test Wind",
        country_code="BRA",
        created_at="2020-01-01T00:00:00Z",
        status="unknown",
        aggregation_role="unresolved",
        installed_capacity_mw=None,
        external_ids_json='{"wri_gppd":"BRA0030283"}',
        extensions_json="{}",
        field_sources_json="{}",
        evidence_json="{}",
        sources=["historical"],
    )


def enrich(partition, rows=None, **options):
    return reconcile(
        partition["candidates"],
        rows or [existing()],
        source_id=options.get("source_id", "ons"),
        identity_source_id="wri-identity",
        now="2026-11-05T15:21:00Z",
    )


def test_complete_ceg_partition_retains_units_zero_unknown_and_original():
    p = parse(
        [
            native(),
            native(cod_equipamento="UNIT-2", val_potenciaefetiva=""),
            native(ceg="EOL.CV.CE.030284-1.01"),
        ],
        limit=1,
    )
    assert p["total_cegs"] == 2 and p["total_wind_rows"] == 3
    assert p["next_cegs"] == ["EOL.CV.CE.030284-1.01"]
    units = p["candidates"][0]["units"]
    assert [u["reported_nominal_mw"] for u in units] == [0, None]
    assert units[0]["original"]["dat_entradaoperacao"] == "2020-02-29"
    assert all(u["turbine_count"] is None for u in units)
    assert p["candidates"][0]["observation_date"] is None


def test_enrichment_preserves_scalars_and_is_idempotent():
    p = parse([native()])
    before = existing()
    result, ledger = enrich(p)
    assert ledger[0]["decision"] == "enriched"
    for field in ("created_at", "status", "aggregation_role", "installed_capacity_mw"):
        assert result[0][field] == before[field]
    assert enrich(p, result)[0] == result
    assert before == existing()
    assert json.loads(result[0]["external_ids_json"])["aneel_ceg"] == "EOL.CV.BA.030283-0.01"


def test_competing_ceg_outside_partition_prevents_acceptance():
    p = parse([native(), native(ceg="EOL.CV.CE.030283-0.02")], limit=1)
    result, ledger = enrich(p)
    assert result == [] and "Multiple CEG" in ledger[0]["reason"]


@pytest.mark.parametrize("name", ["Test Wind II", "Tést Wind"])
def test_names_must_match_without_phase_or_accent_fuzziness(name):
    result, ledger = enrich(parse([native(nom_usina=name)]))
    assert not result and "disagreement" in ledger[0]["reason"]


def test_no_missing_or_ambiguous_identity_is_created():
    p = parse([native()])
    row = existing()
    row["external_ids_json"] = "{}"
    assert not enrich(p, [row])[0]
    row = existing()
    other = {**row, "record_id": "other"}
    assert not enrich(p, [row, other])[0]


def test_immutable_and_overlapping_snapshots_rejected():
    p = parse([native()])
    result, _ = enrich(p)
    changed = copy.deepcopy(p)
    changed["candidates"][0]["units"][0]["reported_nominal_mw"] = 1
    with pytest.raises(ValueError, match="Immutable"):
        enrich(changed, result)
    with pytest.raises(ValueError, match="Overlapping"):
        enrich(p, result, source_id="alias")


@pytest.mark.parametrize("value", ["nan", "inf", "-1"])
def test_invalid_nominal_quantity(value):
    with pytest.raises(ValueError, match="nominal MW"):
        parse([native(val_potenciaefetiva=value)])


def test_duplicate_unit_is_not_summed():
    with pytest.raises(ValueError, match="Duplicate or missing"):
        parse([native(), native()])


def test_invalid_dates_and_ceg_and_checksum():
    with pytest.raises(ValueError):
        parse([native(dat_entradaoperacao="2021-02-29")])
    with pytest.raises(ValueError, match="CEG"):
        wri_id("EOL.CV.BA.000000-0.01")
    with pytest.raises(ValueError, match="checksum"):
        parse_partition(b"bad", sha256="bad", offset=0, limit=1, retrieved_at="date")
