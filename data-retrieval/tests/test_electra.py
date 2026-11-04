"""Electra scope and identity hazards use small synthetic, nonprivate examples."""

import hashlib

import pytest

from energy_data_retrieval.pv_catalogue.electra import (
    read_electra_csv,
    screen_electra_candidates,
)

PAGE = (
    b'<input id="ctl00_ContentPlaceHolder1_mChkDdlTipoTecnologia_mTxtCheckBoxListCombo" '
    b'value="Fotovoltaica">'
    b'<input id="ctl00_ContentPlaceHolder1_mChkDdlAutonomia_mTxtCheckBoxListCombo" '
    b'value="Canarias">'
    b'<input id="ctl00_ContentPlaceHolder1_mTxtPotenciaNetaMin" value="1000">1/1 (2)'
)
CSV = (
    b"AUTOID;INSTALACIONID;REGIMEN;INSTALACION;AUTONOMIA\r\n"
    b"1;11;ESPECIAL;Solar A;Canarias\r\n2;12;ESPECIAL;Solar A;Canarias\r\n"
)


def read(content=CSV, page=PAGE):
    return read_electra_csv(
        content,
        sha256=hashlib.sha256(content).hexdigest(),
        scope_page=page,
        scope_sha256=hashlib.sha256(page).hexdigest(),
        region="Canarias",
        minimum_net_kw=1000,
    )


def test_same_name_distinct_registry_ids_remain_candidates():
    rows = read()
    assert [row["INSTALACIONID"] for row in rows] == ["11", "12"]
    holds = screen_electra_candidates(
        rows, existing=[{"country_code": "ESP", "name": "SOLAR A", "aliases": []}]
    )
    assert all(len(reasons) == 3 for reasons in holds.values())
    assert all("capacity_ac_mw" not in row and "technology" not in row for row in rows)


def test_existing_registry_id_is_flagged_even_after_rename():
    holds = screen_electra_candidates(
        read(),
        existing=[
            {
                "country_code": "ESP",
                "name": "Renamed facility",
                "external_ids_json": '{"electra_installation_id":"11"}',
            }
        ],
    )
    assert "existing_registry_id_requires_reviewed_phase_crosswalk" in holds["11"]
    assert "existing_registry_id_requires_reviewed_phase_crosswalk" not in holds["12"]


@pytest.mark.parametrize(
    "page",
    [
        PAGE.replace(b"Fotovoltaica", b"Solar termica"),
        PAGE.replace(b'value="1000"', b'value="0"'),
        PAGE.replace(b'value="Canarias"', b'value="Andalucia"'),
        PAGE.replace(b"(2)", b"(6465)"),
        PAGE + b" 1/1 (2)",
        PAGE + b'<input id="ctl00_ContentPlaceHolder1_mTxtPotenciaNetaMin" value="1000">',
    ],
)
def test_rejects_unfiltered_ambiguous_or_truncated_capture(page):
    with pytest.raises(ValueError):
        read(page=page)


@pytest.mark.parametrize(
    "content",
    [
        CSV.replace(b";12;", b";11;"),
        CSV.replace(b"2;12;", b"3;12;"),
        CSV.replace(b"Solar A;Canarias", b"Solar A;Madrid"),
        CSV.replace(b"AUTONOMIA", b"EXTRA"),
        CSV.replace(b"2;12;ESPECIAL;Solar A;Canarias", b"2;12;ESPECIAL;;Canarias"),
        CSV.replace(b"2;12;ESPECIAL;Solar A;Canarias", b"2;12;ESPECIAL;Solar A;Canarias;extra"),
    ],
)
def test_rejects_identity_schema_and_row_drift(content):
    with pytest.raises(ValueError):
        read(content)


def test_checksum_mismatch_precedes_extraction():
    with pytest.raises(ValueError, match="checksum"):
        read_electra_csv(
            CSV,
            sha256="0" * 64,
            scope_page=PAGE,
            scope_sha256=hashlib.sha256(PAGE).hexdigest(),
            region="Canarias",
            minimum_net_kw=1000,
        )
