"""Weather equations, calibration recovery and domain checks."""

import numpy as np
import pytest

from energy_methods.pv_stress_weather import (
    airmass_uv,
    buck_relative_humidity,
    buck_vapour_pressure,
    faiman_temperature,
    fit_temperature_model,
    linear_uv,
    ross_temperature,
    wald_uv,
)


def test_temperature_equations_use_poa_and_no_hidden_wind_height_scaling():
    assert ross_temperature(20, 800, coefficient=0.025) == 40
    assert faiman_temperature(20, 800, 2, u0=25, u1=7.5) == 40


def test_uv_equations_and_modified_wald_sign():
    assert linear_uv(1000, slope=0.05) == 50
    assert wald_uv(1000, 0.5) == pytest.approx((7.210 - 2.365 * 0.5) * 10 + 1.897 - 0.860 * 0.5)
    assert wald_uv(1000, 0.5, a=2.711, b=-2.286) == pytest.approx(40.007)
    assert wald_uv(1000, 10) == wald_uv(1000, 0.7)
    assert airmass_uv(1000, 2, coefficients=[0.05, 0.01, 0, 0, 0]) == 70
    assert linear_uv(0, slope=0.05) == 0


def test_buck_units_ice_water_and_rh():
    assert buck_vapour_pressure(0) == pytest.approx(0.61121)
    assert buck_vapour_pressure(-10) == pytest.approx(0.2599469165)
    np.testing.assert_array_equal(
        buck_relative_humidity([-10, 0, 20], [-10, 0, 20]), [100, 100, 100]
    )
    assert 50 < buck_relative_humidity(20, 10) < 55
    with pytest.raises(ValueError):
        buck_relative_humidity(10, 20)
    with pytest.raises(ValueError):
        buck_vapour_pressure(-100)


def test_temperature_fits_recover_generating_coefficients():
    t = np.linspace(10, 30, 100)
    g = np.linspace(100, 1000, 100)
    wind = 2 + np.sin(np.arange(100))
    ross = fit_temperature_model(t, g, ross_temperature(t, g, coefficient=0.024), model="ross")
    assert ross["coefficient"] == pytest.approx(0.024)
    faiman = fit_temperature_model(
        t, g, faiman_temperature(t, g, wind, u0=28, u1=6), model="faiman", wind_speed_ms=wind
    )
    assert faiman == pytest.approx({"u0": 28, "u1": 6})
    with pytest.raises(ValueError, match="varying wind"):
        fit_temperature_model(t, g, t + 20, model="faiman", wind_speed_ms=np.ones(100))


@pytest.mark.parametrize(
    "call",
    [
        lambda: linear_uv(100, slope=-0.1),
        lambda: linear_uv(0, slope=0.1, intercept=1),
        lambda: airmass_uv(100, 2, coefficients=[1, 2]),
        lambda: airmass_uv(100, 2, coefficients=[2, 0, 0, 0, 0]),
        lambda: faiman_temperature(20, 800, -1, u0=25, u1=6),
        lambda: ross_temperature(np.nan, 800, coefficient=0.02),
        lambda: wald_uv(1000, -0.1),
    ],
)
def test_invalid_weather_domains_fail(call):
    with pytest.raises(ValueError):
        call()
