"""Synthetic layout/identity and unit-boundary regressions; no OEM document fixture."""

import pytest

from energy_data_retrieval.pv_catalogue.inhenergy import read_inhenergy_layout

TEXT = """INHENERGY CO., LTD. GRID-CONNECTED INVERTER
Technical Data SI-7K-S2 SI-8K-S2
Rated output power 7kW 8000W
Max. output power 7.7kW 8.8kW
Max. PV access power 14000W 16000W
Max. PV input power 9100W 10400W
Max. PV input voltage 550V
Rated output current 30.5A 35A
Max. output current 34A 38.5A
Operation voltage range 80V-540V
Rated output voltage 230V/180V-280V
Rated output frequency 50Hz/60Hz
MPPT max. current 20A/20A/20A
Dimensions (L/W/H) in mm 358/180/400
Weight 16kg
Heat dissipation mode Natural Smart cooling
Self-Consumption night <1w
Communication interface WIFI/4G/GPRS/RS485(optional)
Warranty 5 years (standard)/20 years(optional)
"""
MODELS = ["SI-7K-S2", "SI-8K-S2"]


def test_units_and_boundaries():
    rows = read_inhenergy_layout(TEXT, models=MODELS)
    assert [r["pac_rated_w"] for r in rows] == [7000, 8000]
    assert rows[0]["max_pv_access_power_w"] == 14000
    assert rows[0]["max_pv_input_power_w"] == 9100
    assert rows[0]["vdc_max_v"] == rows[1]["vdc_max_v"] == 550
    assert rows[0]["table_mppt_current_cells_as_reported"] == "current 20A/20A/20A"
    assert rows[0]["night_power_as_reported"] == "<1w"
    assert rows[0]["warranty_as_reported"] == "5 years (standard)/20 years(optional)"
    assert "cooling_method" not in rows[0]
    assert "idc_max_a" not in rows[0]
    assert "pdc_rated_w" not in rows[0]


@pytest.mark.parametrize("models", [MODELS[::-1], [*MODELS, "SI-9K-S2"], [MODELS[0]] * 2])
def test_identity_drift(models):
    with pytest.raises(ValueError):
        read_inhenergy_layout(TEXT, models=models)


@pytest.mark.parametrize(
    "old,new",
    [
        ("7kW 8000W", "7kVA 8000W"),
        ("7kW 8000W", "0kW 8000W"),
        ("7kW 8000W", "7kW 8kW 9kW"),
        ("7kW 8000W", ""),
        ("GRID-CONNECTED INVERTER", "UNREVIEWED FAMILY"),
        ("Weight 16kg", "Weight 16kg\nWeight 17kg"),
    ],
)
def test_unreviewed_layout_rejected(old, new):
    with pytest.raises(ValueError):
        read_inhenergy_layout(TEXT.replace(old, new), models=MODELS)
