"""Synthetic OGi safeguards; no copyrighted document fixtures."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.tab_ogi import MODELS, parse_models


def sample():
    return (
        "TAB OGi BATTERIES\n"
        "Uf (V/cell) 1,80 1,75 1,75 1,70 1,65 1,65 1,60\n"
        "Discharging time (h) 10 5 3 1 1/2 1/6 1/12 Ri Isc L W H Dry Wet\n"
        "Type Ah Ah Ah Ah Ah Ah Ah mΩ (kA) mm mm mm kg kg\n"
        + "\n".join(f"{m} 100 90 80 70 60 50 40 1,2 2,3 200 100 400 15 20" for m in MODELS)
        + "\fV15-03-01-2022"
    )


def test_product_level_rate_basis_fault_units_and_masses():
    rows = parse_models(sample())
    assert len(rows) == 25
    assert rows[0]["product_level"] == "monobloc"
    assert rows[0]["rated_voltage_v"] == 12
    assert rows[-1]["product_level"] == "cell"
    assert rows[-1]["rated_voltage_v"] == 2
    assert rows[0]["short_circuit_current_ka"] == 2.3
    assert rows[0]["capacity_observations"][-1]["hours"] == 1 / 12
    assert rows[0]["capacity_observations"][-1]["end_voltage_v_per_cell"] == 1.6
    assert (rows[0]["dry_mass_kg"], rows[0]["wet_mass_kg"]) == (15, 20)
    assert not {"power_capacity_mw", "energy_capacity_mwh", "cell_capacity_ah"} & rows[0].keys()


@pytest.mark.parametrize(
    "old,new",
    [
        ("(kA)", "(A)"),
        ("Dry Wet", "Wet Dry"),
        ("1/12 Ri", "1/10 Ri"),
        ("1,80 1,75", "1,85 1,75"),
        ("V15-03-01-2022", "V16"),
        ("100 90 80", "80 90 80"),
        ("400 15 20", "400 20 15"),
        ("1,2 2,3", "1,2 --"),
        ("12V 2 OGi 50", "12V 1 OGi 25"),
        ("2V 24 OGi 600", "2V 24 OGi 601"),
    ],
)
def test_unreviewed_units_values_revision_identity_rejected(old, new):
    with pytest.raises(ValueError):
        parse_models(sample().replace(old, new))


def test_partial_duplicate_and_other_family_rejected():
    for text in [
        sample().replace(MODELS[-1] + " 100", "unknown 100"),
        sample() + "\f" + sample(),
        sample().replace("OGi", "OPzS"),
    ]:
        with pytest.raises(ValueError):
            parse_models(text)
