"""Synthetic table tests: units, physical boundaries and identity safeguards."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.tab_opzs import parse_cells


def sample():
    header = (
        "TAB OPzS CELLS\nUf (V/cell) 1,80 1,77 1,75 1,67\n"
        "Discharging time (h) 10 5 3 1 Ri Isc L W H Dry Wet Poles\n"
        "Type Ah Ah Ah Ah mΩ A mm mm mm kg kg Nr.\n"
        "REFERENCE TEMPERATURE · 20 °C\nWeight tolerance is ± 5 %\n"
        "Electrical values are approximative.\n"
    )
    models = ["2 OPzS 100"] + [f"{i} OPzS {i * 100}" for i in range(3, 23)] + ["24 OPzS 3000"]
    return header + "\n".join(f"{m} 111 97 85 62 1,48 1350 103 206 420 8,0 13,0 2" for m in models)


def test_preserves_rate_mass_and_fault_current_boundaries():
    rows = parse_cells(sample())
    assert len(rows) == 22
    r = rows[0]
    assert r["capacity_observations"][0] == {
        "hours": 10,
        "end_voltage_v_per_cell": 1.8,
        "capacity_ah": 111,
        "reference_temperature_c": 20,
    }
    assert r["dry_mass_kg"] == 8 and r["wet_mass_kg"] == 13
    assert r["short_circuit_current_a"] == 1350
    assert not {"power_capacity_mw", "energy_capacity_mwh", "continuous_current_a"} & r.keys()


@pytest.mark.parametrize(
    "old,new",
    [
        ("Dry Wet", "Wet Dry"),
        ("mΩ A mm", "Ω A mm"),
        ("1,80", "1,85"),
        ("111 97", "90 97"),
        ("8,0 13,0", "13,0 8,0"),
        ("3 OPzS 300", "2 OPzS 100"),
        ("24 OPzS 3000", "26 OPzS 3250"),
        ("REFERENCE TEMPERATURE · 20 °C", "REFERENCE TEMPERATURE · 25 °C"),
    ],
)
def test_changed_basis_and_duplicate_identity_fail(old, new):
    with pytest.raises(ValueError):
        parse_cells(sample().replace(old, new))


def test_partial_and_duplicate_pages_fail():
    with pytest.raises(ValueError):
        parse_cells("\n".join(sample().splitlines()[:-1]))
    with pytest.raises(ValueError):
        parse_cells(sample() + "\f" + sample())


def block_sample():
    header = (
        "TAB OPzS BLOCKS\nUf (V/cell) 1,80 1,77 1,75 1,67\n"
        "Discharging time (h) 10 5 3 1 Ri Isc L W H Dry Wet\n"
        "Type Ah Ah Ah Ah mΩ A mm mm mm kg kg\n"
        "Weight tolerance is ± 5 %\nElectrical values are approximative.\n"
    )
    models = [
        "12V 1 OPzS 50",
        "12V 2 OPzS 100",
        "12V 3 OPzS 150",
        "6V 4 OPzS 200",
        "6V 5 OPzS 250",
        "6V 6 OPzS 300",
    ]
    return header + "\n".join(f"{m} 51 40,9 38,0 28,4 20,0 613 272 205 392 26 39" for m in models)


def test_block_voltage_and_ah_boundary():
    from energy_data_retrieval.bess_oem_catalogue.tab_opzs import parse_blocks

    rows = parse_blocks(block_sample())
    assert [r["nominal_block_voltage_v"] for r in rows] == [12, 12, 12, 6, 6, 6]
    assert rows[0]["capacity_observations"][0]["block_capacity_ah"] == 51
    assert "cell_capacity_ah" not in rows[0]
    with pytest.raises(ValueError):
        parse_blocks(block_sample().replace("6V 6 OPzS 300", "6V 5 OPzS 250"))
    with pytest.raises(ValueError):
        parse_blocks(block_sample().replace("Dry Wet", "Wet Dry"))
    with pytest.raises(ValueError):
        parse_cells(block_sample())
