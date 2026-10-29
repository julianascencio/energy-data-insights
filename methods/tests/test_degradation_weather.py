"""Independent hand calculations for published weather transformations; synthetic inputs."""

import numpy as np
import pytest

from energy_methods.degradation_weather import faiman_from_ghi, wald_uv_irradiance


def test_faiman_height_scaling_and_night() -> None:
    # At 10 m the wind scaling is exactly one; 800/(20+5*4) = 20 degrees.
    actual = faiman_from_ghi([25, 10], [800, 0], 4, u0=20, u1=5, module_height_m=10)
    np.testing.assert_allclose(actual, [45, 10])
    assert faiman_from_ghi(25, 800, 4) > faiman_from_ghi(25, 800, 4, module_height_m=10)
    assert np.isnan(faiman_from_ghi(25, np.nan, 4))


def test_wald_regressions_clipping_and_unavailable_sun() -> None:
    # kt=.5: UVB fraction .001467 + UVA fraction .060275 = .061742.
    assert wald_uv_irradiance(500, 1000) == pytest.approx(30.871)
    # Clamp kt below .1 and above .7, rather than extrapolate the regressions.
    np.testing.assert_allclose(wald_uv_irradiance([1, 500], [1000, 100]), [0.071546, 28.42])
    np.testing.assert_allclose(
        wald_uv_irradiance([0, 0, 1, np.nan], [0, np.nan, 0, 1]),
        [0, np.nan, np.nan, np.nan],
        equal_nan=True,
    )


@pytest.mark.parametrize("values", [(-274, 1, 1), (20, -1, 1), (20, 1, -1), (20, np.inf, 1)])
def test_faiman_invalid_weather(values: tuple[float, float, float]) -> None:
    with pytest.raises(ValueError):
        faiman_from_ghi(*values)


@pytest.mark.parametrize("values", [(1, -1), (-1, 1), (1, np.inf)])
def test_wald_invalid_weather(values: tuple[float, float]) -> None:
    with pytest.raises(ValueError):
        wald_uv_irradiance(*values)
