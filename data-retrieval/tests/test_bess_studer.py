"""Synthetic model tables exercise identity, units and conditional ratings."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.studer import parse_studer_html


def page() -> bytes:
    blocks, copies = [], []
    for model, voltage, low, high in [
        ("900-12", 12, 9.5, 17),
        ("1200-24", 24, 19, 34),
        ("1400-48", 48, 38, 60),
    ]:
        groups = [
            [
                (
                    "Nominal battery voltage (Input range)",
                    f"{voltage}Vdc ({low} \u2013 {high} Vdc)",
                ),
                ("Power 30 min. 25°C", "900<sup>(1)</sup>/ 700 VA"),
                ("Continuous power 25°C", "650<sup>(1)</sup>/ 500 VA"),
                ("Power 5 sec. 25°C", "2.3 kVA"),
                ("Output voltage and frequency (2)", "230 Vac"),
                ("Consumption OFF/Stand-by/ON", "1.1/1.4/7 W"),
            ],
            [("Maximum charging current (2)", "35 A")],
            [
                ("Input voltage and frequency (2)", "150 to 265 Vac"),
                ("Input current max. (transfer relay) / Output current max.", "16 Aac / 20 Aac"),
                ("Transfer time", "&lt; 15 ms"),
            ],
            [
                ("Weight", "8.2 kg"),
                ("Dimensions h/w/l [mm]", "110/210/310 mm"),
                ("Conformity", "synthetic"),
            ],
        ]
        tables = "".join(
            "<table>" + "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in rows) + "</table>"
            for rows in groups
        )
        blocks.append(
            f'<div class="elementor-toggle-item"><a class="elementor-toggle-title">xts {model}</a>'
            f"{tables}<p>These features are valid only when using "
            "the cooling module ecf 01</p></div>"
        )
        copies.append(tables)
    return ("".join(blocks + copies)).encode()


def test_optional_cooling_not_another_model():
    rows = parse_studer_html(page(), "xts")
    assert len(rows) == 3
    assert rows[0]["continuous_va"] == 500
    assert rows[0]["continuous_with_ecf01_va"] == 650
    assert rows[0]["overload_5sec_kva"] == 2.3
    assert rows[0]["dc_min_v"] == 9.5
    assert rows[0]["consumption_off_standby_on_w"] == [1.1, 1.4, 7]
    assert "power_capacity_mw" not in rows[0]


@pytest.mark.parametrize(
    "old,new",
    [
        (b" VA", b" W"),
        (b"xts 900-12", b"xts 950-12"),
        (b"ecf 01", b"other"),
        (b"&lt; 15 ms", b"15 ms"),
        (b"35 A", b"35 mA"),
    ],
)
def test_reject_changed_semantics(old, new):
    with pytest.raises(ValueError):
        parse_studer_html(page().replace(old, new), "xts")


def test_reject_conflicting_responsive_copy():
    with pytest.raises(ValueError, match="Responsive"):
        parse_studer_html(page().replace(b"500 VA", b"510 VA", 1), "xts")


def test_reject_missing_model_and_unreviewed_series():
    with pytest.raises(ValueError):
        parse_studer_html(page(), "next3")
    with pytest.raises(ValueError):
        parse_studer_html(b"<html>no table</html>", "xts")


@pytest.mark.parametrize("before,after", [(b"8.2 kg", b"0 kg"), (b"9.5", b"13")])
def test_reject_invalid_numeric_ranges(before, after):
    with pytest.raises(ValueError):
        parse_studer_html(page().replace(before, after), "xts")
