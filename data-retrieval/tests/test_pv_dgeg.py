"""Synthetic fixtures exercise source boundaries, not claimed real installations."""

import hashlib
import json

import pytest

from energy_data_retrieval.pv_catalogue.dgeg import FIELDS, group_dgeg_pages, read_dgeg_page


def row(identifier=1, process=12, **changes):
    values = dict.fromkeys(FIELDS)
    values.update(
        objectid=identifier,
        processo=process,
        nome="Synthetic PV",
        inspireid=f"test{identifier}",
        tipo_central="CS",
        subtipo_instalacao="Solar fotovoltaico",
        potencia_instaladakva=1000,
        potencia_ligacaokva=900,
    )
    values.update(changes)
    return values


def page(*rows, more=False, **changes):
    data = {
        "fields": [{"name": n} for n in sorted(FIELDS)],
        "features": [{"attributes": r} for r in rows],
        "exceededTransferLimit": more,
    }
    data.update(changes)
    content = json.dumps(data).encode()
    return content, hashlib.sha256(content).hexdigest()


def read(*rows, **kwargs):
    content, checksum = page(*rows, **kwargs)
    return read_dgeg_page(content, sha256=checksum)


def test_no_kva_conversion_no_status_or_geometry_inference():
    result = read(
        row(proprietario="Private person", geometry={"x": 0}, lic_exploracao="LicExploracao")
    )
    staged = result["pv_features"][0]
    assert staged["potencia_geradorkw"] is None
    assert staged["potencia_instaladakva"] == 1000
    assert set(staged) == FIELDS
    assert "capacity_ac_mw" not in staged and "status" not in staged
    assert "proprietario" not in staged and "geometry" not in staged


def test_repeated_process_values_are_not_summed_or_merged_by_name():
    groups = group_dgeg_pages([read(row(), row(2), row(3, process=13))])
    assert len(groups) == 2
    assert [r["potencia_instaladakva"] for r in groups[0]["features"]] == [1000, 1000]
    assert not any(g["accepted"] for g in groups)
    assert all(g["source_coverage_complete"] is False for g in groups)


def test_coverage_requires_reviewed_id_set_even_for_final_page():
    p = read(row(), more=False)
    with pytest.raises(ValueError, match="coverage incomplete"):
        group_dgeg_pages([p], expected_object_ids={1, 2})
    result = group_dgeg_pages([p], expected_object_ids={1})[0]
    assert result["source_coverage_complete"] and not result["accepted"]


def test_duplicate_polygon_across_pages_rejected():
    with pytest.raises(ValueError, match="repeated across"):
        group_dgeg_pages([read(row()), read(row())])


@pytest.mark.parametrize(
    "changes",
    [
        {"tipo_central": "Armazenamento"},
        {"subtipo_instalacao": "Solar termico"},
        {"subtipo_instalacao": None},
    ],
)
def test_explicit_pv_only(changes):
    p = read(row(**changes))
    assert not p["pv_features"] and len(p["excluded_features"]) == 1


@pytest.mark.parametrize("value", [-1, "1000", True, float("nan"), float("inf")])
def test_power_types_and_ranges(value):
    with pytest.raises(ValueError, match="power value"):
        read(row(potencia_geradorkw=value))


def test_hash_error_schema_and_duplicate_guards():
    b, sha = page(row())
    with pytest.raises(ValueError, match="checksum"):
        read_dgeg_page(b + b" ", sha256=sha)
    with pytest.raises(ValueError, match="schema changed"):
        read(row(), fields=[{"name": "objectid"}])
    with pytest.raises(ValueError, match="duplicated"):
        read(row(), row())
    with pytest.raises(ValueError, match="feature page"):
        read(row(), error={"code": 400})


def test_conflicting_blocks_and_missing_names_remain_held():
    g = group_dgeg_pages([read(row(), row(2, nome=None, potencia_instaladakva=2000))])[0]
    assert "multiple_names_in_process" in g["held_reasons"]
    assert "native_power_scope_or_values_differ" in g["held_reasons"]
    assert "missing_public_name_or_polygon_reference" in g["held_reasons"]
