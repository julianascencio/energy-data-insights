"""Independent boundary and energy accounting checks for storm screening."""

import numpy as np
import pandas as pd
import pytest

from energy_methods.storm_energy import storm_energy, wind_capacity_factor


def test_curve_boundaries() -> None:
    np.testing.assert_allclose(
        wind_capacity_factor(np.array([0, 3, 12, 24, 25, 30])), [0, 0, 1, 1, 0, 0]
    )


def test_hourly_accounting() -> None:
    frame = pd.DataFrame(
        dict(
            timestamp=pd.date_range("2026-11-07", periods=2, freq="h", tz="UTC"),
            ghi_wm2=[500, 0],
            clear_ghi_wm2=[1000, 0],
            wind_ms=[12, 25],
        )
    )
    result = storm_energy(frame, baseline_wind_ms=12)
    assert result.pv_mwh_per_mw.sum() == pytest.approx(0.4)
    assert result.pv_delta_mwh_per_mw.sum() == pytest.approx(-0.4)
    assert result.wind_delta_mwh_per_mw.sum() == pytest.approx(-1)
    frame.loc[0, "ghi_wm2"] = np.nan
    with pytest.raises(ValueError, match="Incomplete"):
        storm_energy(frame)


def test_duplicate_and_missing_hour() -> None:
    for timestamps in (["2026-11-07", "2026-11-07"], ["2026-11-07T00:00", "2026-11-07T02:00"]):
        frame = pd.DataFrame(
            dict(timestamp=timestamps, ghi_wm2=[0, 0], clear_ghi_wm2=[0, 0], wind_ms=[8, 8])
        )
        with pytest.raises(ValueError, match="hourly"):
            storm_energy(frame)


def test_invalid_wind() -> None:
    for value in (-1, np.nan, np.inf):
        with pytest.raises(ValueError):
            wind_capacity_factor(np.array([value]))
