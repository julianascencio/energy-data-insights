"""Analytical arithmetic and published-precision sensitivity tests."""

import pytest

from energy_methods.mix_rounding import infer_incremental_month_share


def test_exact_monthly_share() -> None:
    result = infer_incremental_month_share(
        preceding_demand_twh=9,
        new_month_demand_twh=1,
        preceding_share_pct=20,
        cumulative_share_pct=25,
        share_rounding_pp=0,
    )
    assert result.central_pct == pytest.approx(70)
    assert result.minimum_pct == pytest.approx(70)
    assert result.maximum_pct == pytest.approx(70)


def test_portugal_ren_rounding_does_not_contradict_october() -> None:
    # REN's Jan-Sep and Jan-Oct shares; 4.5 TWh October demand is an
    # explicitly SYNTHETIC assumption, not a measured observation.
    for before, cumulative, october in ((64, 62, 47), (22, 24, 40)):
        result = infer_incremental_month_share(
            preceding_demand_twh=40.5,
            new_month_demand_twh=4.5,
            preceding_share_pct=before,
            cumulative_share_pct=cumulative,
            preceding_demand_rounding_twh=0.05,
        )
        assert result.minimum_pct <= result.central_pct <= result.maximum_pct
        assert result.contains_reported(october)


def test_no_rounding_no_artificial_range() -> None:
    result = infer_incremental_month_share(
        preceding_demand_twh=2,
        new_month_demand_twh=1,
        preceding_share_pct=45,
        cumulative_share_pct=45,
        share_rounding_pp=0,
        preceding_demand_rounding_twh=0,
    )
    assert result.minimum_pct == result.maximum_pct == 45


@pytest.mark.parametrize(
    "kwargs",
    [
        {"preceding_demand_twh": 0},
        {"new_month_demand_twh": 0},
        {"share_rounding_pp": -0.5},
        {"preceding_demand_rounding_twh": 41},
        {"cumulative_share_pct": 100},
        {"preceding_share_pct": float("nan")},
    ],
)
def test_invalid_inputs(kwargs: dict[str, float]) -> None:
    params = dict(
        preceding_demand_twh=40.5,
        new_month_demand_twh=4.5,
        preceding_share_pct=22.0,
        cumulative_share_pct=24.0,
    )
    params.update(kwargs)
    with pytest.raises(ValueError):
        infer_incremental_month_share(**params)
