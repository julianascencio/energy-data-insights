import csv
import hashlib
from dataclasses import asdict

import pytest

from energy_data_retrieval.pv_catalogue.cne import HEADERS, read_cne_csv


def _fixture(tmp_path, *overrides):
    path = tmp_path / "cne.csv"
    row = dict.fromkeys(HEADERS, "")
    row |= {
        "sistema": "SEN",
        "central": "Fixture Central",
        "region_nombre": "Maule",
        "comuna_nombre": "Talca",
        "rut": "OMIT-TAX-ID",
        "propietario": "OMIT-OWNER",
        "coord_este_utm": "OMIT-COORDINATE",
        "tipo_final": "Solar Fotovoltaica",
        "tipo_de_energia": "Solar",
        "potencia_bruta_mw": "10,25",
        "potencia_neta_mw": "9,8",
        "estado": "En Pruebas",
        "fecha_act": "2026-03-16",
        "fecha_puesta_servicio_central": "01/01/2020",
    }
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(row | values for values in overrides)
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_only_explicit_pv_and_no_private_or_inferred_fields(tmp_path):
    path, digest = _fixture(tmp_path, {}, {"tipo_final": "Solar"}, {"tipo_final": "CSP"})
    (row,) = read_cne_csv(path, sha256=digest)
    assert row.row_number == 2
    assert (row.gross_mw, row.net_mw) == (10.25, 9.8)
    assert row.native_status == "En Pruebas"
    assert row.reported_plant_service_date == "2020-01-01"
    assert "OMIT-" not in repr(asdict(row))
    assert not {"capacity_ac_mw", "owners", "commissioning_date"} & asdict(row).keys()


def test_repeated_site_and_conflicting_native_values_are_flagged(tmp_path):
    path, digest = _fixture(
        tmp_path,
        {"cod_unidad": "U1", "potencia_neta_mw": "11,0", "tipo_de_energia": "Solar-CSP"},
        {"cod_unidad": "U2", "tipo_final": "CSP"},
    )
    (row,) = read_cne_csv(path, sha256=digest)
    assert row.site_rows == 2
    assert row.review_flags == (
        "multiple_native_rows_for_site",
        "conflicting_technology",
        "net_exceeds_gross",
    )
    assert row.net_mw == 11.0


@pytest.mark.parametrize("bad", ["NaN", "1.234,5", "-1", "inf"])
def test_malformed_decimal_is_rejected(tmp_path, bad):
    path, digest = _fixture(tmp_path, {"potencia_neta_mw": bad})
    with pytest.raises(ValueError, match="malformed MW"):
        read_cne_csv(path, sha256=digest)


def test_checksum_and_header_drift_fail_closed(tmp_path):
    path, digest = _fixture(tmp_path, {})
    path.write_bytes(path.read_bytes().replace(b"potencia_neta_mw", b"potencia_kw"))
    with pytest.raises(ValueError, match="checksum mismatch"):
        read_cne_csv(path, sha256=digest)
    with pytest.raises(ValueError, match="header drift"):
        read_cne_csv(path, sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def test_pv_classification_does_not_override_conflicting_source_labels(tmp_path):
    path, digest = _fixture(tmp_path, {"central": "PMGD TER Test", "combustible_1": "Diesel"})
    (row,) = read_cne_csv(path, sha256=digest)
    assert row.review_flags == ("conflicting_fuel_label", "potential_non_pv_plant_label")
