"""Synthetic five-column fixtures: no OEM document text or binary copied."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.atess import parse_table


def fixture(family="PCS"):
    models = (
        "PCS100 PCS250 PCS500 PCS630 PCS1000"
        if family == "PCS"
        else "HPS30 HPS50 HPS100 HPS120 HPS150"
    )

    def row(label, values):
        return label + "  " + "  ".join(values) + "\n"

    text = models + "\nAC(on-grid)\n"
    text += row("Rated power", ["10kW"] * 5)
    text += row("Apparent power", ["12kVA"] * 5)
    text += row("Rated voltage", ["400V"] * 5)
    text += row("Rated current", ["14A"] * 5)
    text += row(
        "Max. rectified power" if family == "PCS" else "AC input",
        ["7kW" if family == "PCS" else "20kVA"] * 5,
    )
    text += "AC(off-grid)\n" + row("Rated power", ["9kW"] * 5)
    text += "DC (Battery)\n" if family == "PCS" else "DC (Battery and PV)\n"
    text += row("Voltage range" if family == "PCS" else "Battery voltage range", ["500V-800V"] * 5)
    if family == "PCS":
        text += row("Rated power", ["11kW"] * 5)
        text += row("Max. charge/discharge current", ["20A"] * 4 + ["15A/25A"])
    else:
        for label, value in [
            ("Max. charge power", "15kW"),
            ("Max. discharge power", "11kW"),
            ("Max. charge current", "30A"),
            ("Max. discharge current", "22A"),
            ("Max. PV power", "17kWp"),
        ]:
            text += row(label, [value] * 5)
    text += "General Information\n"
    text += row("Max. efficiency", ["97.5%"] * 5)
    text += row(
        "Dimension(W/H/D)mm" if family == "PCS" else "Dimension (W/H/D)",
        ["100/200/300" + ("mm" if family == "HPS" else "")] * 5,
    )
    text += row("Weight", ["80kg"] * 5)
    text += row("Build-in transformer", ["Yes"] * 2 + ["No"] * 3)
    return text + "Communication\nCertificate\n"


def test_power_boundaries_and_asymmetric_current():
    rows = parse_table(fixture(), family="PCS")
    assert len(rows) == 5
    r = rows[-1]
    assert r["rated_ac_kw"] == 10 and r["apparent_ac_kva"] == 12
    assert r["rated_dc_kw"] == 11 and r["max_rectified_kw"] == 7
    assert r["off_grid_rated_kw"] == 9
    assert (r["max_charge_a"], r["max_discharge_a"]) == (15, 25)
    assert (r["width_mm"], r["height_mm"], r["depth_mm"]) == (100, 200, 300)
    assert "energy_capacity_mwh" not in r and "round_trip_efficiency_pct" not in r
    assert not r["builtin_transformer"]


def test_hybrid_dc_and_pv_not_ac_ratings():
    r = parse_table(fixture("HPS"), family="HPS")[0]
    assert (r["rated_ac_kw"], r["max_dc_charge_kw"], r["max_pv_kwp"], r["ac_input_kva"]) == (
        10,
        15,
        17,
        20,
    )
    assert r["max_charge_a"] == 30 and r["max_discharge_a"] == 22
    assert "maximum_conversion_efficiency_pct" not in r


@pytest.mark.parametrize(
    "old,new",
    [
        ("PCS100 PCS250", "PCS250 PCS100"),
        ("PCS1000", "PCS1001"),
        ("10kW", "10kVA"),
        ("500V-800V", "800V-500V"),
        ("15A/25A", "15A/25A/35A"),
        ("15A/25A", "15/25A"),
        ("80kg  80kg  80kg  80kg  80kg", "80kg  80kg  80kg  80kg"),
        ("Yes", "Optional"),
        ("AC(off-grid)", "AC(on-grid)"),
    ],
)
def test_reject_ambiguous_or_changed_tables(old, new):
    with pytest.raises(ValueError):
        parse_table(fixture().replace(old, new), family="PCS")


def test_reject_repeated_numeric_row():
    s = fixture().replace(
        "Rated power  10kW  10kW  10kW  10kW  10kW",
        "Rated power  10kW  10kW  10kW  10kW  10kW\nRated power  10kW  10kW  10kW  10kW  10kW",
    )
    with pytest.raises(ValueError, match="repeated row"):
        parse_table(s, family="PCS")


def test_reject_unknown_family():
    with pytest.raises(ValueError, match="Unreviewed"):
        parse_table(fixture(), family="PCS-HV")


def test_normalizes_pdf_ligature_without_changing_units():
    assert (
        parse_table(fixture().replace("rectified", "rectiﬁed"), family="PCS")[0]["max_rectified_kw"]
        == 7
    )


def cluster_fixture():
    return """ATESS ESS-BM-51.2-314RPB-S
Battery cluster specification
Energy code  BS96  BS112  BS128  BS144  BS160  BS176  BS192  BS208R  BS225
Module Number  6  7  8  9  10  11  12  13  14
Weight(kg)  700  800  900  1000  1100  1200  1300  1400  1500
Norminal Energy/KWh  16.076n (n=Module Number)
Norminal Voltage/V  51.2n (n=Module Number)
Voltage Range/V  44.8n~57.6n (n=Module Number)
Certificate
"""


def test_cluster_formula_not_rounded_model_name():
    from energy_data_retrieval.bess_oem_catalogue.atess import parse_enerstack314_clusters

    rows = parse_enerstack314_clusters(cluster_fixture())
    assert rows[-1]["energy_code"] == "BS225"
    assert rows[-1]["nominal_energy_kwh"] == 225.064
    assert rows[-2]["module_count"] == 13
    assert rows[0]["voltage_min_v"] == 268.8
    assert rows[0]["nominal_voltage_v"] == 307.2
    assert "power_capacity_mw" not in rows[0]


@pytest.mark.parametrize(
    "old,new",
    [
        ("BS208R", "BS208"),
        ("16.076n (n=Module Number)", "16.076"),
        ("  14\n", "  15\n"),
        ("  1500\n", "\n"),
        ("314RPB", "100CPB"),
    ],
)
def test_cluster_rejects_implicit_formula_or_shifted_identity(old, new):
    from energy_data_retrieval.bess_oem_catalogue.atess import parse_enerstack314_clusters

    with pytest.raises(ValueError):
        parse_enerstack314_clusters(cluster_fixture().replace(old, new))
