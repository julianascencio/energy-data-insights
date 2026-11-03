"""Protect the 2019 API and verify 2021 equations independently."""

from dataclasses import replace

import numpy as np
import pytest

from energy_methods.degradation import BOLTZMANN_EV_K, DegradationParameters, degradation_rates
from energy_methods.degradation_uncertainty import (
    StressRateParameters,
    combined_rate_2021,
    stress_rate,
)


def calibration(**changes):
    baseline = DegradationParameters(
        a_h=0,
        a_p=0,
        a_tm=1,
        e_h=0,
        e_p=0,
        e_tm=0,
        n=1,
        x=1,
        theta=1,
        a_n=1,
        calibration_id="analytic",
        calibration_source="unit test",
    )
    return replace(baseline, **changes)


def stresses(**changes):
    return {
        "module_temperature_mean_c": 25,
        "module_temperature_upper_c": 30,
        "module_temperature_lower_c": 20,
        "relative_humidity_percent": 50,
        "uv_dose_kwh_m2": 100,
        "cycles_per_year": 1,
        **changes,
    }


def test_printed_273_offset_is_separate_from_existing_model():
    old = degradation_rates(**stresses(), parameters=calibration())
    new = combined_rate_2021(
        **stresses(), parameters=calibration(), rate_scale_to_year_inverse=0.01
    )
    assert old.total == pytest.approx(10)
    assert new.raw_rate == pytest.approx(283)
    assert new.annual_fractional_rate == pytest.approx(2.83)
    assert new.mechanisms[2] == 283
    zero_range = combined_rate_2021(
        **stresses(module_temperature_mean_c=20, module_temperature_upper_c=20),
        parameters=calibration(),
        rate_scale_to_year_inverse=1,
    )
    assert zero_range.raw_rate == pytest.approx(273)


def test_normalization_subtraction_is_outside_product():
    result = combined_rate_2021(
        **stresses(),
        parameters=calibration(a_n=2),
        rate_scale_to_year_inverse=1,
    )
    assert result.raw_rate == pytest.approx(2 * (1 + 283) - 1)


def test_equation_one_hand_calculation_and_percent_scale():
    params = StressRateParameters(
        beta0=2,
        beta1=BOLTZMANN_EV_K * 300 * np.log(2),
        beta2=1,
        beta3=1,
        beta4=1,
        rate_scale_to_year_inverse=0.01,
        calibration_source="analytic",
    )
    result = stress_rate(
        daily_maximum_temperature_c=26.85,
        daily_temperature_range_c=10,
        daily_daytime_uv_w_m2=20,
        daily_relative_humidity_percent=50,
        parameters=params,
    )
    assert result.raw_rate == pytest.approx(10000)
    assert result.annual_fractional_rate == pytest.approx(100)


@pytest.mark.parametrize(
    "field,value",
    [
        ("relative_humidity_percent", 101),
        ("cycles_per_year", -1),
        ("uv_dose_kwh_m2", -1),
        ("module_temperature_mean_c", -274),
    ],
)
def test_bad_combined_inputs_fail(field, value):
    with pytest.raises(ValueError):
        combined_rate_2021(
            **stresses(**{field: value}), parameters=calibration(), rate_scale_to_year_inverse=1
        )


def test_missing_masks_all_mechanisms_and_invalid_scale_fails():
    result = combined_rate_2021(
        **stresses(uv_dose_kwh_m2=np.nan), parameters=calibration(), rate_scale_to_year_inverse=1
    )
    assert np.isnan(result.raw_rate)
    assert all(np.isnan(v) for v in result.mechanisms)
    for scale in [0, -1, np.inf, np.nan]:
        with pytest.raises(ValueError):
            combined_rate_2021(
                **stresses(), parameters=calibration(), rate_scale_to_year_inverse=scale
            )
