"""Synthetic OPzV table safeguards; no redistributed OEM document fixture."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.tab_opzv import MODELS, parse_cells


def sample():
    header = (
        "TAB OPzV BATTERIES\nV15-03-01-2022\n"
        "Uf (V/cell) 1,8 1,8 1,77 1,75 1,67\n"
        "Discharging time (h) 10 10 5 3 1 Ri Isc L W H1/H2 Wet Poles\n"
        "Type Nom. Cap. (Ah) Capacity (Ah) at 20°C mΩ A mm mm mm kg Nr.\n"
        "Weight tolerance is ± 5 %\nElectrical values are approximative.\n"
    )
    return header + "\n".join(
        f"{m} 200 204 172 150 110 1,22 1660 103 206 354/380 19 2" for m in MODELS
    )


def test_nominal_measured_height_and_fault_boundaries():
    r = parse_cells(sample())[0]
    assert r["nominal_capacity_ah"] == 200
    assert r["capacity_observations"][0]["capacity_ah"] == 204
    assert r["capacity_observations"][-1]["end_voltage_v_per_cell"] == 1.67
    assert (r["height_h1_mm"], r["height_h2_mm"]) == (354, 380)
    assert r["short_circuit_current_a"] == 1660
    assert not {"energy_capacity_mwh", "power_capacity_mw", "dc_voltage_nominal_v"} & r.keys()


@pytest.mark.parametrize(
    "old,new",
    [
        ("H1/H2 Wet", "H2/H1 Dry"),
        ("354/380", "380/354"),
        ("354/380", "354"),
        ("20°C", "25°C"),
        ("mΩ A", "Ω A"),
        ("204 172", "170 172"),
        ("V15-03-01-2022", "V16"),
        ("5 OPzV 250", "4 OPzV 200"),
        ("24 OPzV 3000", "26 OPzV 3250"),
    ],
)
def test_changed_units_revision_or_identity_fail(old, new):
    with pytest.raises(ValueError):
        parse_cells(sample().replace(old, new))


def test_partial_duplicate_and_other_family_fail():
    for text in (
        "\n".join(sample().splitlines()[:-1]),
        sample() + "\f" + sample(),
        sample().replace("OPzV", "OPzS"),
    ):
        with pytest.raises(ValueError):
            parse_cells(text)
