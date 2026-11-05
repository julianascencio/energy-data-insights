"""Independent checks of the imported PVDeg Arrhenius exposure wrapper."""

import numpy as np
import pandas as pd
import pytest

from energy_methods.pvdeg_mechanisms import relative_arrhenius_exposure


def history(values):
    return pd.Series(
        values, index=pd.date_range("2023-01-01", periods=len(values), freq="h", tz="UTC")
    )


@pytest.mark.parametrize("n,p", [(0, 0), (1, 0), (0, 1), (1, 1)])
def test_reference_and_independent_equation(n, p):
    t, rh, light = history([25.0, 45.0]), history([50.0, 80.0]), history([0.0, 700.0])
    expected = np.mean(
        np.exp(60 / 0.00831446261815324 * (1 / 298.15 - 1 / (t.to_numpy() + 273.15)))
        * (rh.to_numpy() / 50) ** n
        * (light.to_numpy() / 1000) ** p
    )
    actual = relative_arrhenius_exposure(t, rh, light, humidity_exponent=n, irradiance_exponent=p)
    assert actual == pytest.approx(expected, rel=1e-5)
    assert relative_arrhenius_exposure(
        history([25.0] * 2),
        history([50.0] * 2),
        history([1000.0] * 2),
        humidity_exponent=n,
        irradiance_exponent=p,
    ) == pytest.approx(1)


@pytest.mark.parametrize("bad", [np.nan, np.inf, -274])
def test_invalid_temperature(bad):
    with pytest.raises(ValueError):
        relative_arrhenius_exposure(history([bad, 25]), history([50, 50]), history([1, 1]))


def test_misaligned_and_missing_hour():
    t, rh, light = history([25, 25]), history([50, 50]), history([1, 1])
    rh.index = rh.index + pd.Timedelta(hours=1)
    with pytest.raises(ValueError, match="aligned"):
        relative_arrhenius_exposure(t, rh, light)
    for series in (t, rh, light):
        series.index = pd.date_range("2023-01-01", periods=2, freq="2h", tz="UTC")
    with pytest.raises(ValueError, match="hourly"):
        relative_arrhenius_exposure(t, rh, light)
