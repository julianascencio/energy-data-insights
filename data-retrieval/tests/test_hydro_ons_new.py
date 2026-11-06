"""Synthetic new-identity acceptance and conservative aggregation boundaries."""

import copy
import json

import pytest

from energy_data_retrieval.hydro_catalogue import capacity_summary
from energy_data_retrieval.hydro_catalogue.ons import parse_inventory
from energy_data_retrieval.hydro_catalogue.ons_new import accept_new, new_record

NOW = "2026-11-06T06:50:00Z"


def entry():
    item = parse_inventory(
        "ceg;nom_tipousina;nom_usina;cod_equipamento;val_potenciaefetiva;"
        "nom_agenteproprietario;nom_agenteoperador;dat_entradaoperacao;dat_desativacao;id_estado\n"
        "PCH.PH.MT.999991-0.01;HIDROELÉTRICA;SYNTHETIC;UG1;5;Owner;Operator;2020-01-01;;MT\n"
    )[0]
    return {
        "inventory": item,
        "source_id": "synthetic",
        "source_retrieved_at": "2026-11-05T00:00:00Z",
        "review": {
            "decision": "reviewed_new_identity",
            "ceg": item["ceg"],
            "source_name": "SYNTHETIC",
            "identity_basis": "Synthetic review",
        },
    }


@pytest.fixture
def root(tmp_path):
    (tmp_path / "records/projects").mkdir(parents=True)
    (tmp_path / "sources.json").write_text(
        json.dumps(
            {
                "synthetic": {
                    "url": "https://example.org/synthetic",
                    "publisher": "Synthetic",
                    "title": "Synthetic",
                    "license": "Synthetic fixture",
                    "retrieved_at": NOW,
                    "original_availability": "Synthetic in-memory CSV",
                }
            }
        )
    )
    return tmp_path


def test_insert_replay_and_nonadditive_power(root):
    batch = {"accepted": [entry()], "reviewed_at": NOW}
    out = root / "records/projects/new.jsonl"
    assert accept_new(root, batch, out) == 1
    before = out.read_bytes()
    assert accept_new(root, batch, out) == 0
    assert out.read_bytes() == before
    row = json.loads(before)
    assert row["created_at"] == row["updated_at"] == NOW
    assert row["status"] == "unknown"
    assert row.get("installed_capacity_mw") is None
    assert json.loads(row["external_ids_json"]) == {"aneel_ceg": "PCH.PH.MT.999991-0.01"}
    assert capacity_summary([row], "installed_capacity_mw")["excluded"] == 1
    assert json.loads(row["extensions_json"])["ons_hydro_unit_inventory"][0]["retrieved_at"] != NOW


@pytest.mark.parametrize("collision", ["name", "alias", "registry", "wri", "changed", "duplicate"])
def test_all_collisions_fail_before_writing(root, collision):
    first = entry()
    old = new_record(first, now=NOW)
    if collision != "changed":
        old["record_id"] = "different-id"
    if collision == "name":
        old["name"] = "Sýnthetic"
        old["external_ids_json"] = "{}"
    if collision == "alias":
        old.update(name="Other", aliases=["synthetic"], external_ids_json="{}")
    if collision == "wri":
        old.update(name="Renamed", external_ids_json=json.dumps({"wri_gppd": "BRA0999991"}))
    if collision == "changed":
        old["operator_names"] = ["Different operator"]
    prior = root / "records/projects/old.jsonl"
    prior.write_text(json.dumps(old) + "\n")
    before = prior.read_bytes()
    batch = {"accepted": [first], "reviewed_at": NOW}
    if collision == "duplicate":
        batch["accepted"].append(copy.deepcopy(first))
    out = root / "records/projects/new.jsonl"
    with pytest.raises(ValueError):
        accept_new(root, batch, out)
    assert not out.exists()
    assert prior.read_bytes() == before


@pytest.mark.parametrize("bad", ["review", "unit", "scope", "attribution"])
def test_malformed_review_or_unsafe_fact_rejected(bad):
    e = entry()
    if bad == "review":
        e["review"]["decision"] = "automatic_name_match"
    if bad == "unit":
        e["inventory"]["units"].append(copy.deepcopy(e["inventory"]["units"][0]))
    if bad == "scope":
        e["facts"] = {"aggregation_role": {"value": "independent"}}
    if bad == "attribution":
        e["facts"] = {"installed_capacity_mw": {"value": 5}}
    with pytest.raises(ValueError):
        new_record(e, now=NOW)
