"""Synthetic card tests, independent of copyrighted source HTML."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.fullriver import parse_cards


def card(metric=True):
    fields = {
        "Group": "TEST [BCI]",
        "Capacity": "180 Ah",
        "Reserve Capacity @ 56A": "125 min",
        "Dimms": "260 x 182 x 272 mm" if metric else "10.24 x 7.17 x 10.71 in",
        "Weight": "34.2 kg" if metric else "75.4 lbs",
    }
    return (
        '<div class="card-batt"><h3 class="card-batt__model">DC-TEST</h3>'
        + "".join(
            f'<div class="card-batt__specs--label">{k}</div>'
            f'<div class="card-batt__specs--value"><span>{v}</span></div>'
            for k, v in fields.items()
        )
        + "</div>"
    )


def test_native_boundaries_and_exact_identity():
    row = parse_cards((card() + card(False)).encode(), expected_models=["DC-TEST"])[0]
    assert row["panels"]["metric"]["Reserve Capacity @ 56A"] == "125 min"
    assert row["panels"]["metric"]["Capacity"] == "180 Ah"
    assert "energy_capacity_mwh" not in row


@pytest.mark.parametrize(
    "old,new",
    [(" Ah", " kWh"), ("56A", "56kA"), (" kg", " lbs"), ("Dimms", "Size"), ("DC-TEST", "DC-TESTB")],
)
def test_reject_unreviewed_units_labels_and_variants(old, new):
    with pytest.raises(ValueError):
        parse_cards((card() + card(False)).replace(old, new).encode(), expected_models=["DC-TEST"])


@pytest.mark.parametrize("html", [card(), card() + card(), card() + card(False) + card()])
def test_require_exactly_two_distinct_unit_panels(html):
    with pytest.raises(ValueError):
        parse_cards(html.encode(), expected_models=["DC-TEST"])


def test_reject_duplicate_identity_request():
    with pytest.raises(ValueError):
        parse_cards((card() + card(False)).encode(), expected_models=["DC-TEST", "DC-TEST"])
