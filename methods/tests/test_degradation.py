"""Independent calculations and physical-domain checks; all inputs are synthetic."""

from __future__ import annotations

import math
from dataclasses import replace

import numpy as np
import pytest

from energy_methods.degradation import DegradationParameters, degradation_rates


@pytest.fixture
def calibration() -> DegradationParameters:
    # Choose energies whose Arrhenius factors are analytically 1/2, 1/3, 1/4.
    return DegradationParameters(
        a_h=2,
        a_p=3,
        a_tm=4,
        e_h=8.62e-5 * 300 * math.log(2),
        e_p=8.62e-5 * 300 * math.log(3),
        e_tm=8.62e-5 * 313.15 * math.log(4),
        n=2,
        x=0.5,
        theta=1,
        a_n=1.2,
        calibration_id="synthetic-analytic",
        calibration_source="Unit test, not module data",
    )


@pytest.fixture
def stresses() -> dict[str, object]:
    return {
        "module_temperature_mean_c": 26.85,
        "module_temperature_upper_c": 40,
        "module_temperature_lower_c": 20,
        "relative_humidity_percent": 2,
        "uv_dose_kwh_m2": 9,
        "cycles_per_year": 2,
    }


def test_independent_arrhenius_values_and_nonadditive_total(calibration, stresses) -> None:
    result = degradation_rates(**stresses, parameters=calibration)
    assert result.hydrolysis == pytest.approx(4)
    assert result.photodegradation == pytest.approx(15)
    assert result.thermomechanical == pytest.approx(40)
    assert result.total == pytest.approx(3935)  # 1.2 * 5 * 16 * 41 - 1, not 1.2*(...-1)
    assert result.total != 4 + 15 + 40


def test_broadcasting_and_joint_missing_mask(calibration, stresses) -> None:
    stresses["relative_humidity_percent"] = [[2], [np.nan]]
    stresses["uv_dose_kwh_m2"] = [9, 0, np.nan]
    result = degradation_rates(**stresses, parameters=calibration)
    assert result.total.shape == (2, 3)
    assert result.photodegradation[0, 1] == 0
    for name in ("hydrolysis", "photodegradation", "thermomechanical", "total"):
        value = getattr(result, name)
        assert np.isnan(value[1]).all()
        assert np.isnan(value[:, 2]).all()


def test_zero_stresses_and_tiny_rates_are_not_lost(calibration, stresses) -> None:
    stresses.update(relative_humidity_percent=0, uv_dose_kwh_m2=0, cycles_per_year=0)
    assert degradation_rates(**stresses, parameters=replace(calibration, a_n=1)).total == 0
    stresses["relative_humidity_percent"] = 1
    tiny = replace(calibration, a_h=1e-20, a_n=1, e_h=0)
    assert float(degradation_rates(**stresses, parameters=tiny).total) == pytest.approx(
        1e-20, abs=1e-30
    )


@pytest.mark.parametrize(
    ("key", "value", "message"),
    [
        ("module_temperature_mean_c", -273.15, "absolute zero"),
        ("module_temperature_upper_c", -300, "absolute zero"),
        ("module_temperature_lower_c", 30, "Lower <= mean"),
        ("module_temperature_upper_c", 25, "Lower <= mean"),
        ("relative_humidity_percent", 101, "humidity"),
        ("relative_humidity_percent", -1, "humidity"),
        ("uv_dose_kwh_m2", -1, "nonnegative"),
        ("cycles_per_year", -1, "nonnegative"),
        ("uv_dose_kwh_m2", np.inf, "infinity"),
    ],
)
def test_invalid_stresses_fail(calibration, stresses, key, value, message) -> None:
    stresses[key] = value
    with pytest.raises(ValueError, match=message):
        degradation_rates(**stresses, parameters=calibration)


@pytest.mark.parametrize(
    "name", ["a_h", "a_p", "a_tm", "e_h", "e_p", "e_tm", "n", "x", "theta", "a_n"]
)
@pytest.mark.parametrize("value", [-1, np.nan, np.inf, True, "1"])
def test_invalid_calibration_fails(calibration, name, value) -> None:
    with pytest.raises(ValueError):
        replace(calibration, **{name: value})


@pytest.mark.parametrize("name", ["n", "x", "theta", "a_n"])
def test_zero_exponents_and_normalization_fail(calibration, name) -> None:
    with pytest.raises(ValueError, match="positive"):
        replace(calibration, **{name: 0})


def test_calibration_requires_provenance(calibration) -> None:
    with pytest.raises(ValueError, match="calibration_source"):
        replace(calibration, calibration_source=" ")
    with pytest.raises(ValueError, match="calibration_id"):
        replace(calibration, calibration_id="")
    assert DegradationParameters(**calibration.to_dict()) == calibration


def test_overflow_and_negative_total_are_not_clipped(calibration, stresses) -> None:
    with pytest.raises(ValueError, match="overflow"):
        degradation_rates(**stresses, parameters=replace(calibration, n=1e308))
    with pytest.raises(ValueError, match="negative total"):
        degradation_rates(
            **stresses, parameters=replace(calibration, a_h=0, a_p=0, a_tm=0, a_n=0.5)
        )
