"""Municipal PV identities, units, privacy and phase risks use synthetic fixtures."""

from __future__ import annotations

import csv
import hashlib
import io
import json

import pytest

from energy_data_retrieval.pv_catalogue.madrid import (
    COLUMNS,
    read_madrid_csv,
    reviewed_madrid_records,
    screen_madrid_identities,
)


def native(**changes):
    r = dict.fromkeys(COLUMNS, "")
    r.update(
        {
            "Número": "1",
            "Código Ayto": "100",
            "Centro": "PUBLIC LIBRARY",
            "Latitud": "40.4",
            "Longitud": "-3.7",
            "Potencia KWp": "8,2",
            "Puesta en servicio": "24/07/2019",
            "Dirección": "Private contact address",
            "Empresa instaladora": "Private installer person",
            "Superficie (m2)": "3000",
            "Adscripción": "Municipal district",
            "Uso del edificio": "cultural",
        }
    )
    r.update(changes)
    return r


def mapped(rows=None, existing=None, sequences=None):
    return reviewed_madrid_records(
        [native()] if rows is None else rows,
        existing=[] if existing is None else existing,
        reviewed_sequences={"1"} if sequences is None else sequences,
        source_id="test",
        snapshot_date="2026-06-30",
    )


def test_pinned_csv_decimal_comma_and_bom():
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=sorted(COLUMNS), delimiter=";")
    writer.writeheader()
    writer.writerow(native())
    content = stream.getvalue().encode("utf-8-sig")
    assert (
        read_madrid_csv(content, sha256=hashlib.sha256(content).hexdigest())[0]["Potencia KWp"]
        == "8,2"
    )
    with pytest.raises(ValueError, match="checksum"):
        read_madrid_csv(content, sha256="0" * 64)
    bad = b"number;plant\n1;bad\n"
    with pytest.raises(ValueError, match="schema"):
        read_madrid_csv(bad, sha256=hashlib.sha256(bad).hexdigest())


def test_mapping_preserves_peak_capacity_scope_and_omits_private_or_inferred_roles():
    r = mapped()[0]
    assert r["capacity_dc_mw"] == pytest.approx(0.0082) and r["commissioning_date"] == "2019-07-24"
    assert json.loads(r["external_ids_json"]) == {"madrid_building_code": "100"}
    assert r["latitude"] == 40.4 and "datum/CRS" in r["location_accuracy"]
    assert (
        not {
            "capacity_ac_mw",
            "owners",
            "operators",
            "epc_contractors",
            "land_area_ha",
            "area_m2",
            "module_count",
        }
        & r.keys()
    )
    assert "Private contact" not in json.dumps(r) and "Private installer" not in json.dumps(r)
    assert json.loads(r["extensions_json"])["madrid_inventory"]["area_as_reported_m2"] == "3000"


def test_building_code_identity_survives_sequence_and_display_name_changes():
    a = mapped()[0]
    b = mapped([native(**{"Número": "99", "Centro": "NEW LIBRARY NAME"})], sequences={"99"})[0]
    assert a["record_id"] == b["record_id"]
    assert "99" not in json.loads(b["external_ids_json"]).values()


@pytest.mark.parametrize(
    "changes",
    [
        {"Código Ayto": ""},
        {"Código Ayto": "a"},
        {"Centro": ""},
        {"Potencia KWp": "0"},
        {"Potencia KWp": "NaN"},
        {"Potencia KWp": "-1"},
        {"Latitud": "3.7"},
        {"Longitud": "3.7"},
        {"Latitud": ""},
    ],
)
def test_invalid_identity_capacity_location_cannot_be_allowlisted(changes):
    with pytest.raises(ValueError, match="identity"):
        mapped([native(**changes)])


def test_repeated_building_and_nearby_pins_are_held_without_merging():
    second = native(**{"Número": "2", "Centro": "LIBRARY EXTENSION", "Latitud": "40.405"})
    risks = screen_madrid_identities([native(), second], existing=[])
    assert all("missing_or_repeated_building_code" in reasons for reasons in risks.values())
    second.update({"Código Ayto": "200", "Latitud": "40.4001"})
    risks = screen_madrid_identities([native(), second], existing=[])
    assert all(
        "incoming_buildings_within_100m_scope_review" in reasons for reasons in risks.values()
    )
    with pytest.raises(ValueError):
        mapped([native(), second])


def test_canonical_alias_external_code_and_proximity_hold():
    for existing in [
        {"country_code": "ESP", "name": "Old", "aliases": ["PUBLIC LIBRARY"]},
        {
            "country_code": "ESP",
            "name": "Different",
            "external_ids_json": '{"madrid_building_code":"100"}',
        },
        {"country_code": "ESP", "name": "Different", "latitude": 40.4001, "longitude": -3.7001},
    ]:
        with pytest.raises(ValueError, match="identity"):
            mapped(existing=[existing])


def test_dates_missing_future_invalid_and_allowlist():
    assert "commissioning_date" not in mapped([native(**{"Puesta en servicio": ""})])[0]
    for value in ["01/07/2026", "31/02/2020"]:
        with pytest.raises(ValueError):
            mapped([native(**{"Puesta en servicio": value})])
    with pytest.raises(ValueError, match="identity"):
        mapped(sequences={"99"})
    assert mapped(sequences=set()) == []
    with pytest.raises(ValueError, match="Duplicate"):
        mapped([native(), native()])
