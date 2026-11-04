"""Synthetic controller table tests; not an OEM document reproduction."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.elum import parse_es_text


def fixture():
    return (
        b"Synthetic cover\fTECHNICAL SPECIFICATIONS\n"
        b"GENERAL INFORMATION  ES Compact  ES  ES +\n"
        b"Weight (without accessories)  0.1 kg  0.2 kg  0.4 kg\n"
        b"Maximum capacity (indicative solar kWp)  100 kWp  200 kWp  1 MWp\n"
        b"Maximum BESS capacity (KWh)  100 kWh  200 kWh  1 MWh\n"
        b"Max. number of devices  10  20  30\n"
        b"PV inverters  1  2  3\nBESS  2  3  4\nGenset  N/A  1  N/A\n"
        b"Meters  2  4  6\nGrid Connections (point of injection)  1  2  3\n"
    )


def test_exact_columns_and_scope():
    rows = parse_es_text(fixture())
    assert [r["limits"]["bess"] for r in rows] == [2, 3, 4]
    assert rows[0]["limits"]["gensets"] is None
    assert rows[2]["reported_fields"]["Maximum BESS capacity (KWh)"] == "1 MWh"
    assert all("energy_capacity_mwh" not in r for r in rows)


@pytest.mark.parametrize(
    "old,new",
    [
        (b"ES Compact  ES  ES +", b"ES  ES Compact  ES +"),
        (b"BESS  2  3  4", b"BESS  2  4"),
        (b"1 MWh", b"1 MW"),
        (b"Genset  N/A  1  N/A", b"Genset  N/A  x  N/A"),
        (b"Meters  2  4  6", b"Meters 2 4 6\nMeters  2  4  6"),
    ],
)
def test_changed_layout_fails(old, new):
    with pytest.raises(ValueError):
        parse_es_text(fixture().replace(old, new))
