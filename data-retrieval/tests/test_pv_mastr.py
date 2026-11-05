"""Synthetic unit-review cases; no fixture represents a real generating plant."""

from pathlib import Path

import pytest

from energy_data_retrieval.pv_catalogue.mastr import read_mastr_solar_units


def write_xml(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "units.xml"
    path.write_text(body)
    return path


def unit(identifier: str, extra: str = "") -> str:
    return (
        f"<EinheitSolar><EinheitMastrNummer>{identifier}</EinheitMastrNummer>{extra}</EinheitSolar>"
    )


def test_native_scope_and_privacy(tmp_path):
    xml = (
        "<EinheitenSolar>"
        + unit(
            "synthetic-unit",
            "<Bruttoleistung>1.250</Bruttoleistung>"
            "<Nettonennleistung>1</Nettonennleistung>"
            "<ZugeordneteWirkleistungWechselrichter>2</ZugeordneteWirkleistungWechselrichter>"
            "<NetzbetreiberpruefungStatus>2954</NetzbetreiberpruefungStatus>"
            "<NameStromerzeugungseinheit>omit</NameStromerzeugungseinheit>"
            "<AnlagenbetreiberMastrNummer>omit</AnlagenbetreiberMastrNummer>",
        )
        + "</EinheitenSolar>"
    )
    row = read_mastr_solar_units(write_xml(tmp_path, xml))[0]
    assert row["Bruttoleistung"] == "1.250"
    assert row["Nettonennleistung"] == "1"
    assert row["ZugeordneteWirkleistungWechselrichter"] == "2"
    assert row["NetzbetreiberpruefungStatus"] == "2954"
    assert row["LokationMaStRNummer"] is None
    assert "NameStromerzeugungseinheit" not in row
    assert "AnlagenbetreiberMastrNummer" not in row
    assert not any("capacity" in key for key in row)


def test_bounded_physical_cursor(tmp_path):
    xml = "<EinheitenSolar>" + "".join(unit(str(n)) for n in range(4)) + "</EinheitenSolar>"
    rows = read_mastr_solar_units(write_xml(tmp_path, xml), start_row=1, limit=2)
    assert [r["source_row"] for r in rows] == [2, 3]
    assert [r["EinheitMastrNummer"] for r in rows] == ["1", "2"]


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-1", "unknown"])
def test_invalid_power(tmp_path, value):
    xml = (
        "<EinheitenSolar>"
        + unit("a", f"<Bruttoleistung>{value}</Bruttoleistung>")
        + "</EinheitenSolar>"
    )
    with pytest.raises(ValueError, match="power"):
        read_mastr_solar_units(write_xml(tmp_path, xml))


@pytest.mark.parametrize("body", ["<EinheitenWind/>", "<!DOCTYPE x><EinheitenSolar/>"])
def test_wrong_partition_or_dtd(tmp_path, body):
    with pytest.raises(ValueError):
        read_mastr_solar_units(write_xml(tmp_path, body))


def test_no_silent_duplicate_identity_or_field(tmp_path):
    for body in [unit("a") * 2, unit("a", "<Bruttoleistung>1</Bruttoleistung>" * 2), unit("")]:
        with pytest.raises(ValueError):
            read_mastr_solar_units(
                write_xml(tmp_path, "<EinheitenSolar>" + body + "</EinheitenSolar>")
            )


@pytest.mark.parametrize("start,limit", [(-1, 1), (0, 0), (0, 10001)])
def test_invalid_bounds(tmp_path, start, limit):
    with pytest.raises(ValueError):
        read_mastr_solar_units(tmp_path / "not-opened", start_row=start, limit=limit)


def test_dtd_after_large_prolog_is_rejected(tmp_path):
    xml = " " * 16380 + "<!DOCTYPE x><EinheitenSolar/>"
    with pytest.raises(ValueError, match="DTD"):
        read_mastr_solar_units(write_xml(tmp_path, xml))
