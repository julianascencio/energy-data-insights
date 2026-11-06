"""Synthetic ONS identity and unit-scope boundaries."""

import json

import pytest

from energy_data_retrieval.hydro_catalogue.gppd import parse_gppd
from energy_data_retrieval.hydro_catalogue.ons import eligibility, enrich, parse_inventory, wri_id


def csv_text(mw="4", second=""):
    return (
        "ceg;nom_tipousina;nom_usina;cod_equipamento;val_potenciaefetiva;"
        "nom_agenteproprietario;nom_agenteoperador;dat_entradaoperacao;dat_desativacao\n"
        f"PCH.PH.MT.002547-0.01;HIDROELÉTRICA;SYNTHETIC;UG01;{mw};Owner;Operator;2000-01-01;\n"
        + second
    )


def test_identity_and_no_operational_or_plant_capacity_inference():
    item = parse_inventory(csv_text())[0]
    old = parse_gppd(
        "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude\n"
        "BRA,Synthetic,BRA0002547,Hydro,4,-10,-50\n",
        source_id="wri",
        now="2026-01-01T00:00:00Z",
    )[0][0]
    kw = dict(source_id="ons", identity_source_id="mapping", now="2026-11-05T00:00:00Z")
    new = enrich(old, item, **kw)
    assert new["created_at"] == old["created_at"]
    assert new["status"] == old["status"] == "unknown"
    assert new.get("installed_capacity_mw") is None
    assert new.get("operational_capacity_mw") is None
    assert new["aggregation_role"] == "unresolved"
    assert json.loads(new["external_ids_json"])["aneel_ceg"] == item["ceg"]
    assert enrich(new, item, **kw) == new
    assert wri_id(item["ceg"]) == "BRA0002547"
    old["name"] = "Synthetic II"
    assert eligibility(old, item) == "name_review"


@pytest.mark.parametrize("mw", ["nan", "inf", "-1", "missing"])
def test_invalid_capacity_rejected(mw):
    with pytest.raises(ValueError):
        parse_inventory(csv_text(mw))


def test_duplicates_and_missing_columns_rejected():
    row = csv_text().splitlines()[1] + "\n"
    with pytest.raises(ValueError, match="Duplicate"):
        parse_inventory(csv_text(second=row))
    with pytest.raises(ValueError, match="columns"):
        parse_inventory("ceg\nX\n")


def test_ceg_variant_not_collapsed_and_unknown_optional_id_not_invented():
    a = csv_text().splitlines()[1]
    b = a.replace(".01", ".02").replace("UG01", "UG02")
    items = parse_inventory(csv_text(second=b + "\n"))
    assert len(items) == 2
    assert items[0]["units"][0]["_row"] == 2
    assert "id_ons" not in items[0]["units"][0]
    assert wri_id(items[0]["ceg"]) == wri_id(items[1]["ceg"])


def test_dispatch_metadata_keeps_multiple_values_and_preserves_unit_evidence():
    from energy_data_retrieval.hydro_catalogue.ons import enrich_dispatch_metadata

    old = parse_gppd(
        "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude\n"
        "BRA,Synthetic,BRA0002547,Hydro,4,-10,-50\n",
        source_id="wri",
        now="2026-01-01T00:00:00Z",
    )[0][0]
    item = parse_inventory(csv_text())[0]
    item["units"][0].update(id_estado="MT", nom_estado="MATO GROSSO", id_subsistema="SE")
    item["units"].append({**item["units"][0], "id_estado": "GO", "_row": 3})
    old = enrich(
        old, item, source_id="ons", identity_source_id="mapping", now="2026-11-05T00:00:00Z"
    )
    new = enrich_dispatch_metadata(old, now="2026-11-06T03:44:00Z")
    ext = json.loads(new["extensions_json"])
    assert ext["ons_dispatch_metadata"]["id_estado"]["values"] == ["GO", "MT"]
    assert ext["ons_dispatch_metadata"]["nom_modalidadeoperacao"]["values"] == []
    assert (
        ext["ons_hydro_unit_inventory"]
        == json.loads(old["extensions_json"])["ons_hydro_unit_inventory"]
    )
    assert new["created_at"] == old["created_at"]
    assert new["status"] == old["status"]
    assert new.get("grid_connection") is None
    assert new.get("installed_capacity_mw") is None
    assert enrich_dispatch_metadata(new, now="2026-11-07T00:00:00Z") == new
    ext["ons_dispatch_metadata"]["id_estado"]["values"] = ["XX"]
    new["extensions_json"] = json.dumps(ext)
    with pytest.raises(ValueError, match="conflict"):
        enrich_dispatch_metadata(new, now="2026-11-07T00:00:00Z")
