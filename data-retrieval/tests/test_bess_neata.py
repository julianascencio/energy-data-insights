"""Synthetic table tests; no publisher table copied into fixtures."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.neata import LFP_HEADER, LFP_MODELS, parse_neata_html


def fixture():
    rows = [["48V Series"] + [""] * 10, LFP_HEADER]
    rows += [
        [m, "48", "17", "4", "8A/16A", "9", "400*300*50", "Support 16P", "3000", "2Y", "CAN"]
        for m in LFP_MODELS
    ]
    return (
        "<table>"
        + "".join("<tr>" + "".join("<td>" + v + "</td>" for v in row) + "</tr>" for row in rows)
        + "</table>"
    ).encode()


def test_native_quantities_not_model_suffix():
    rows = parse_neata_html(fixture(), series="lfp48")
    assert len(rows) == 8
    assert rows[0]["Typical capacity (Ah)"] == "17"
    assert rows[0]["Constant discharge current/ Peak current (3S)"] == "8A/16A"
    assert "energy_capacity_mwh" not in rows[0]


@pytest.mark.parametrize(
    "before,after",
    [
        (b"LFP4810", b"LFP4820"),
        (b"(Ah)", b"(Wh)"),
        (b"8A/16A", b"8kW/16kW"),
        (b"400*300*50", b"400x300x50"),
        (b"</table>", b""),
    ],
)
def test_fail_closed(before, after):
    with pytest.raises(ValueError):
        parse_neata_html(fixture().replace(before, after, 1), series="lfp48")


def test_duplicate_tables():
    with pytest.raises(ValueError):
        parse_neata_html(fixture() * 2, series="lfp48")


def ess_fixture():
    from energy_data_retrieval.bess_oem_catalogue.neata import ESS_FIELDS

    sections = [
        "Battery system parameters",
        "AC system parameters",
        "Communication parameters",
        "System parameters",
    ]
    values = {
        "Battery rated energy": "25kWh",
        "Rated power at AC side": "10kW",
        "Maximum power at AC side": "12kW",
        "Rated voltage at AC side": "400Vac",
        "Dimensions (W × D × H)": "100×200×300mm",  # noqa: RUF001 -- exact publisher table syntax
        "Equipment weight (including battery)": "200kg",
    }
    rows = (
        [["Product model", "ES100-2", "ES185-2"]]
        + [[s, ""] for s in sections]
        + [[s, values.get(s, "synthetic"), values.get(s, "synthetic")] for s in ESS_FIELDS]
    )
    return (
        "<table>"
        + "".join("<tr>" + "".join("<td>" + v + "</td>" for v in row) + "</tr>" for row in rows)
        + "</table>"
    ).encode()


def test_ess_boundaries_preserved():
    rows = parse_neata_html(ess_fixture(), series="ess")
    assert rows[0]["Battery rated energy"] == "25kWh"
    assert rows[1]["Rated power at AC side"] == "10kW"
    assert "round_trip_efficiency_pct" not in rows[0]


@pytest.mark.parametrize(
    "a,b",
    [(b"ES185-2", b"ES100-2"), (b"25kWh", b"25kW"), (b"10kW", b"10kVA"), (b"200kg", b"200lb")],
)
def test_ess_changed_units_and_models(a, b):
    with pytest.raises(ValueError):
        parse_neata_html(ess_fixture().replace(a, b, 1), series="ess")
