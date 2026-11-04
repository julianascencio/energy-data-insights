"""Synthetic AJ fixtures protect option, identity, power and unit boundaries."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.studer_aj import MODELS, parse_aj_html


def page():
    blocks, copies = [], []
    for model in MODELS["275-400"]:
        voltage = int(model.rsplit("-", 1)[1])
        rows = [
            (
                "Nominal battery voltage (Input range)",
                f"{voltage} Vdc ({voltage - 2} \u2013 {voltage + 4} Vdc)",
            ),
            ("Continuous power 25°C", "200 VA"),
            ("Power 30 min. 25°C", "275 VA"),
            ("Power 5 min. 25°C", "350 VA"),
            ("Power 5 sec. 25°C", "450 VA"),
            ("Asymmetric load", "100 VA"),
            ("Max. efficiency (%)", "90%"),
            ("Cos φ max.", "0.1 \u2013 1"),
            ("Detection of the load", "2 W only with the solar option -S"),
            ("Short-circuit current AC 2 sec.", "2 Aac (4 Aac*)"),
            ("Output voltage", "230 Vac"),
            ("Frequency", "50 Hz"),
            ("Consumption Stand-by / ON no load", "0.3 W**/ 2.4 W"),
            ("Reverse polarity protection as internal fuse", "60 A"),
            ("Weight", "3 kg"),
            ("Dimensions h/w/l [mm]", "100/200/300 mm"),
            ("Conformity", "synthetic"),
        ]
        tables = "".join(
            "<table>" + "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in group) + "</table>"
            for group in [rows[:14], rows[14:], [("Solar option", "not standard")]]
        )
        foot = (
            "IP30; -20 to 50°C; -1.5% / °C from + 25°C; forced from 45°C ± 5°C; "
            "120Vac/60Hz on request; Standby with solar option -S"
        )
        blocks.append(
            '<div class="elementor-toggle-item"><a class="elementor-toggle-title">'
            f"{model}</a>{tables}<p>{foot}</p></div>"
        )
        copies.append(tables)
    return "".join(blocks + copies).encode()


def test_option_and_unit_boundaries():
    rows = parse_aj_html(page(), "275-400")
    assert len(rows) == 3
    assert rows[0]["standby_requires_solar_option"] is True
    assert rows[0]["apparent_power_25c"]["continuous_va"] == 200
    assert rows[0]["maximum_inverter_efficiency_pct"] == 90
    assert "power_capacity_mw" not in rows[0]
    assert "round_trip_efficiency_pct" not in rows[0]


@pytest.mark.parametrize(
    "old,new",
    [
        (b"200 VA", b"200 W"),
        (b"aj 275-12", b"aj 276-12"),
        (b"Standby with solar option -S", b"standby"),
        (b"3 kg", b"0 kg"),
        (b"10 \xe2\x80\x93 16 Vdc", b"13 \xe2\x80\x93 16 Vdc"),
        (b"90%", b"101%"),
    ],
)
def test_reject_changed_evidence(old, new):
    with pytest.raises(ValueError):
        parse_aj_html(page().replace(old, new), "275-400")


def test_reject_disagreement_and_unknown_series():
    with pytest.raises(ValueError, match="Responsive"):
        parse_aj_html(page().replace(b"200 VA", b"201 VA", 1), "275-400")
    with pytest.raises(ValueError, match="Unreviewed"):
        parse_aj_html(page(), "invented")
