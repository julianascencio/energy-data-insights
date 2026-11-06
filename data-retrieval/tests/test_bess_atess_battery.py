"""Synthetic tables test exact configuration identity, unit boundaries and source conflicts."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.atess_battery import SOURCE_URLS, parse_battery_table


def fixture(model="BC55NPB"):
    n = 6 if model == "BC55NPB" else 7
    dims = "Dimension (W/H/D) mm" if n == 6 else "Dimension (W/H/D)mm"
    lines = [
        model,
        "Battery module specification",
        "Rated energy 5.12kWh",
        "Battery rack specification",
    ]
    lines += [
        "Configuration " + " ".join(f"{i} modules" for i in range(6, 6 + n)),
        " ".join(["+1 BPU"] * n),
    ]
    for label, cell in [
        ("Rated energy", "30kWh"),
        ("Rated voltage", "300V"),
        ("Voltage range", "250V-350V"),
        ("Weight", "400kg"),
        (dims, "900/1000/600mm"),
        ("Rated charge/discharge", "0.5C"),
        ("Max. charge/discharge", "1C"),
        ("Max. altitude", "3000m"),
        ("Protection degree", "IP54"),
        ("BMS", "Included"),
        ("Communication", "CAN"),
        ("Monitoring", "RS485"),
    ]:
        lines.append(label + " " + " ".join([cell] * n))
    lines += ["BMS parameters on LCD", "Cell voltage Yes", "Certificate", "CE"]
    return "\n".join(lines).encode()


def parse(data, model="BC55NPB"):
    return parse_battery_table(data, model=model, source_url=SOURCE_URLS[model])


def test_explicit_configurations_not_module_or_cartesian_products():
    rows = parse(fixture())
    assert [r["module_count"] for r in rows] == list(range(6, 12))
    assert all(r["reported_energy_kwh"] == 30 for r in rows)
    assert all(r["active_power_kw"] is None for r in rows)
    assert rows[0]["height_mm"] == 1000
    assert rows[0]["depth_mm"] == 600


def test_voltstack_nine_module_claim_is_held_not_repaired():
    rows = parse(fixture("VoltStack Battery"), "VoltStack Battery")
    assert len(rows) == 7
    assert [r["module_count"] for r in rows if r["rating_review_required"]] == [9]
    assert rows[3]["reported_energy_kwh"] == 30


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"6 modules 7 modules", b"7 modules 6 modules"),
        (b"+1 BPU", b"+2 BPU"),
        (b"30kWh", b"30kW"),
        (b"30kWh", b"0kWh"),
        (b"250V-350V", b"350V-250V"),
        (b"0.5C", b"2C"),
        (b"900/1000/600mm", b"900x1000x600mm"),
        (b"Included", b"Optional"),
        (b"RS485", b"RS232"),
        (b"IP54", b"IP54/IP20"),
    ],
)
def test_changed_units_order_and_scope_fail_closed(old, new):
    with pytest.raises(ValueError):
        parse(fixture().replace(old, new, 1))


def test_duplicate_table_and_missing_column_fail_closed():
    with pytest.raises(ValueError):
        parse(fixture() * 2)
    with pytest.raises(ValueError):
        parse(fixture().replace(b"30kWh 30kWh", b"30kWh", 1))
    with pytest.raises(ValueError):
        parse(fixture().replace(b"Weight ", b"Weight 400kg\nWeight "))


def test_wrong_source_is_rejected():
    with pytest.raises(ValueError):
        parse_battery_table(fixture(), model="BC55NPB", source_url="https://example.com/copy.pdf")
