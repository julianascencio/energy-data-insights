"""Synthetic register cells: unit and configuration boundaries."""

import pytest

from energy_data_retrieval.wind_catalogue.knrec import specification


def row():
    return [
        "1",
        "WT-synthetic",
        "2020.01.01",
        "Example",
        "Example type",
        "3.45/3.6 MW",
        "Country",
        "유",
        "해상용",
        "10.6, 10.8 m/s",
        "126 m",
        "90, 110 m",
        "S",
        "",
    ]


def test_options_are_not_selected_or_cartesian_variants():
    s = specification(row())
    assert s["rating_options_kw"] == [3450, 3600]
    assert s["rated_power_kw"] is None
    assert s["hub_height_options_m"] == [90, 110]
    assert s["hub_height_m"] is None
    assert s["rated_wind_speed_m_s"] is None
    assert s["rotor_diameter_m"] == 126
    assert s["gearbox_present"] is True
    assert s["application"] == "offshore"
    assert s["current_validity"] is None


@pytest.mark.parametrize("value", ["126", "-", "120~126 m", "NaN m"])
def test_untyped_geometry_stays_unknown(value):
    r = row()
    r[10] = value
    assert specification(r)["rotor_diameter_m"] is None


@pytest.mark.parametrize("value", ["0 MW", "3/3 MW"])
def test_invalid_options_rejected(value):
    r = row()
    r[5] = value
    with pytest.raises(ValueError):
        specification(r)


@pytest.mark.parametrize(
    ("note", "status"),
    [("만료", "expired"), ("인증취소(2025.04.04)", "cancelled"), ("", "unspecified")],
)
def test_status_never_infers_validity(note, status):
    r = row()
    r[13] = note
    r[5] = "2.3MW"
    r[7] = "무"
    s = specification(r)
    assert s["rated_power_kw"] == 2300
    assert s["gearbox_present"] is False
    assert s["registry_status"] == status
    assert s["current_validity"] is None
