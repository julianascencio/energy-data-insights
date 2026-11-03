"""Published rounded facts, source inconsistencies and executable offline outputs."""

import hashlib
import json

import numpy as np
import pytest

from energy_analysis.degradation_uncertainty.study import (
    climate_input_comparisons,
    climate_sensitivity,
    published_tables,
    reliability_table_check,
    run_study,
    synthetic_weather_benchmark,
)


def test_published_lifetimes_recovered_with_rounding_not_forced_exactly():
    result = reliability_table_check()
    np.testing.assert_allclose(
        result.calculated_failure_years, [24.09638554, 26.25218251, 15.028961, 19.798], atol=0.1
    )
    assert (result.calculated_minus_reported_years.abs() < 0.3).all()
    assert (
        result.loc[result.kind == "stretched_exponential", "coefficient_units"].item()
        == "year**(-beta)"
    )


def test_uv_discrepancy_is_retained_and_recomputed_not_copied():
    tables = published_tables()
    assert tables["climate_table6"][0]["uv_kwh_m2"] == 96.7
    assert tables["uv_table10"][0]["measured"] == 96.9
    results = climate_input_comparisons()
    row = results[(results.site == "Negev") & (results.model == "wald")].iloc[0]
    assert row.relative_difference_percent == pytest.approx(100 * 0.4 / 96.9)
    assert len(results) == 36


def test_sensitivity_requires_conventions_and_fixed_shape_inverse_rate():
    result = climate_sensitivity(
        normalization=1, cycles_per_year=365, rate_scale_to_year_inverse=0.01
    )
    assert len(result) == 20
    assert result.rate_fraction_per_year.gt(0).all()
    np.testing.assert_allclose(
        result.rate_relative_difference_percent, result.lifetime_relative_difference_percent
    )
    assert result.evidence.str.contains("unvalidated").all()


def test_synthetic_weather_fit_uses_separate_year_and_known_generators():
    result = synthetic_weather_benchmark()
    assert result.loc[result.model == "faiman", "nrmse_percent"].item() < 1e-8
    assert result.loc[result.model == "ross", "nrmse_percent"].item() > 0.1
    assert result.loc[result.model == "wald", "nrmse_percent"].item() == 0
    assert result.loc[result.model == "buck", "nrmse_percent"].item() == 0


def test_study_exports_hashes_and_reproducible_csvs(tmp_path):
    manifest = run_study(tmp_path / "first")
    second = run_study(tmp_path / "second")
    assert manifest["table_data_sha256"] == second["table_data_sha256"]
    for name, digest in manifest["outputs_sha256"].items():
        path = tmp_path / "first" / name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
        if path.suffix == ".csv":
            assert path.read_bytes() == (tmp_path / "second" / name).read_bytes()
    loaded = json.loads((tmp_path / "first" / "manifest.json").read_text())
    assert loaded["assumptions_for_scenarios"]["normalization"] == 1
    assert len(loaded["outputs_sha256"]) == 8
