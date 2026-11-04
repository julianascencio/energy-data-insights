"""Synthetic model panels check identity alignment and incompatible unit boundaries."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.kehua import parse_kehua_html


def fixture():
    fields = {
        "MAX. DC voltage": "1000Vdc",
        "DC voltage range": "500~900Vdc",
        "Max. DC current": "25A",
        "Max. AC output power": "11kVA",
        "Max. efficiency": "96.4%",
    }
    return (
        '<div class="xx_xh"><a>Test-A</a></div><div class="info_list">'
        + "".join(
            '<div class="attr_item"><p>' + k + "</p><p>" + v + "</p></div>"
            for k, v in fields.items()
        )
        + '<div class="g-btn-red">'
    )


def test_apparent_power_and_conversion_efficiency_not_active_or_round_trip():
    (row,) = parse_kehua_html(fixture().encode(), expected_models=["Test-A"])
    assert row["numeric"]["maximum_apparent_power_kva"] == 11
    assert "rated_ac_power_kw" not in row["numeric"]
    assert row["numeric"]["absolute_maximum_dc_voltage_v"] == 1000
    assert row["numeric"]["dc_voltage_range_v"] == [500, 900]
    assert row["numeric"]["maximum_conversion_efficiency_pct"] == 96.4
    assert "round_trip_efficiency_pct" not in row["numeric"]


@pytest.mark.parametrize(
    "before,after",
    [
        ("11kVA", "11kW"),
        ("25A", "25kA"),
        ("500~900Vdc", "900~500Vdc"),
        ("Max. efficiency", "Efficiency"),
        ("<a>Test-A</a>", "<a>Test-A</a><a>Test-A</a>"),
        ("<p>25A</p>", "<p>25A</p><p>extra</p>"),
    ],
)
def test_changed_layout_units_and_duplicate_models_fail_closed(before, after):
    with pytest.raises(ValueError):
        parse_kehua_html(fixture().replace(before, after).encode(), expected_models=["Test-A"])


def test_model_order_must_match_explicit_review():
    with pytest.raises(ValueError, match="model"):
        parse_kehua_html(fixture().encode(), expected_models=["Test-B"])


def test_modular_full_load_range_and_temperature_stay_attached_to_exact_panel():
    def panel(power, voltage):
        fields = {
            "DC full load voltage range": voltage,
            "Rated output voltage": "400Vac3P3W",
            "Rated AC Frequency": "50/60Hz(settable)",
            "Rated AC output power": power,
            "IP rating": "IP66",
        }
        return (
            '<div class="info_list">'
            + "".join(
                '<div class="attr_item" ><p>' + k + "</p><p>" + v + "</p></div>"
                for k, v in fields.items()
            )
            + '<div class="g-btn-red">'
        )

    html = (
        '<div class="xx_xh"><a>Model-A</a><a>Model-B</a></div>'
        + panel("100kW@45°C", "600~1000Vdc")
        + panel("200kW@40°C", "1060~1450Vdc")
    )
    a, b = parse_kehua_html(html.encode(), expected_models=["Model-A", "Model-B"])
    assert a["numeric"]["rated_ac_power_kw"] == 100
    assert b["numeric"]["rated_ac_power_kw"] == 200
    assert a["numeric"]["rated_power_temperature_c"] == 45
    assert b["numeric"]["rated_power_temperature_c"] == 40
    assert a["numeric"]["voltage_range_basis"] == "full_load"
    assert b["numeric"]["dc_voltage_range_v"] == [1060, 1450]
    with pytest.raises(ValueError, match="count"):
        parse_kehua_html(
            (html + panel("1kW", "600~1000Vdc")).encode(), expected_models=["Model-A", "Model-B"]
        )
