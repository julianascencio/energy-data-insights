"""Synthetic contract boundary tests, without redistributing OEM documents."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.hubble_warranty import parse_warranty


def sample():
    return """HUBBLE HV-SERIES (100Ah) BATTERY WARRANTY
    Battery Design Life 900 years.
    Battery Warranty date of purchase from Hubble Energy.
    Battery cells at least 10 years or deliver 5,000 cycles, whichever event occurs first.
    Monitoring reduced to 3 years.
    Warranty Conditions registration reverting to a 5-year warranty.
    Battery temperature below 50 degrees Celsius.
    BMS standard 5-year warranty. Warranty Claims Process end."""


def test_preserves_two_fallbacks_and_separate_component_terms():
    result = parse_warranty(sample(), scope="HV-SERIES (100Ah)")
    assert result["cell_warranty_years"] == 10
    assert result["cell_cycle_limit"] == 5000
    assert result["electronics_warranty_years"] == 5
    assert result["monitoring_fallback_years_observed"] == [3, 5]
    assert result["monitoring_conflict"]
    assert "design_life_years" not in result


def test_unlimited_is_not_numeric_cycle_life():
    value = (
        sample()
        .replace("HV-SERIES (100Ah)", "AM10+")
        .replace(
            "10 years or deliver 5,000 cycles, whichever event occurs first",
            "10 years\u2019 service life and deliver unlimited "
            "charge-discharge cycles within the warranty period",
        )
        .replace("registration reverting to a 5-year warranty.", "registration.")
    )
    result = parse_warranty(value, scope="AM10+")
    assert result["cell_cycle_limit"] is None
    assert not result["monitoring_conflict"]


@pytest.mark.parametrize(
    "old,new",
    [
        ("(100Ah)", "(101Ah)"),
        ("10 years or", "12 years or"),
        ("date of purchase", "date of installation"),
        ("whichever event occurs first", "whichever event occurs last"),
        ("5,000 cycles", "unlimited cycles"),
        ("standard 5-year warranty", "standard warranty"),
        ("temperature below 50", "temperature above 50"),
        ("Warranty Claims Process", "Claims"),
    ],
)
def test_rejects_changed_or_incomplete_terms(old, new):
    with pytest.raises(ValueError):
        parse_warranty(sample().replace(old, new), scope="HV-SERIES (100Ah)")


def test_rejects_unreviewed_scope():
    with pytest.raises(ValueError):
        parse_warranty(sample(), scope="CUBE V2")
