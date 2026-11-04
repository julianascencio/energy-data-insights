"""Verify chronological separation, real capture bindings and honest model scoring."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.forecast_benchmark import (
    forecast_folds,
    load_benchmark_observations,
    load_timestral_forecasts,
    prepare_forecast_fold,
)
from energy_analysis.timestral_solar_case import (
    CASE_MODELS,
    HOLDOUT_START,
    daily_errors,
    run_solar_case,
    solar_case_scores,
)

DATA = Path(__file__).resolve().parents[2] / "examples/analysis/data/timestral_solar"


def test_capture_uses_real_target_only_inputs_and_complete_native_observations() -> None:
    observations = load_benchmark_observations(DATA, technologies=("solar",))
    assert len(observations["solar"]) == 4416
    folds = forecast_folds(
        observations, timestral_covariates="target_only", extend_resource_history=True
    )
    assert len(folds) == 78
    assert all(f.known_covariates.shape == (1, 0, 720) for f in folds)
    captured = load_timestral_forecasts(DATA, folds)
    assert len(captured) == 3744
    wrong_inputs = forecast_folds(observations, extend_resource_history=True)
    with pytest.raises(ValueError, match="stale"):
        load_timestral_forecasts(DATA, wrong_inputs)
    manifest = json.loads((DATA / "forecast_timestral_provenance.json").read_text())
    assert manifest["model_id"] == "mistralai/Timestral-28M"
    assert manifest["timestral_covariates"] == "target_only"
    assert manifest["checkpoint_sha256"]["model.safetensors"]


def test_missing_resource_fallback_uses_only_earlier_same_clock_measurements() -> None:
    frame = load_benchmark_observations(DATA, technologies=("solar",))["solar"]
    history, future = frame.iloc[-720:-48], pd.DatetimeIndex(frame.index[-48:])
    with pytest.raises(ValueError, match="No pre-issue resource"):
        prepare_forecast_fold(history, future, "solar")
    older = frame.iloc[:-720]
    fold = prepare_forecast_fold(history, future, "solar", earlier_resource=older)
    assert np.isfinite(fold.future_features).all()
    # This final-day 04:00 native offset has no valid resource in the 14-day fit.
    lead = 8
    stamp = future[lead]
    older_index = pd.DatetimeIndex(older.index)
    eligible = older[
        older["resource_valid"]
        & older["resource"].between(0, 1300)
        & (older_index.hour == stamp.hour)
        & (older_index.minute == stamp.minute)
    ]
    assert fold.future_features[lead, 0] == eligible["resource"].iloc[-1]
    with pytest.raises(ValueError, match="precede"):
        prepare_forecast_fold(history, future, "solar", earlier_resource=frame.iloc[-48:])


@pytest.fixture(scope="module")
def results() -> pd.DataFrame:
    return run_solar_case(DATA)


def test_common_holdout_and_independent_errors(results: pd.DataFrame) -> None:
    scores = solar_case_scores(results)
    assert set(scores["model"]) == set(CASE_MODELS)
    holdout = results[results["period"] == "August holdout"]
    development = results[results["period"] == "Development"]
    assert development["timestamp"].max() < HOLDOUT_START
    assert holdout["timestamp"].min() == HOLDOUT_START
    assert len(holdout) == 31 * 48 * 7 and len(development) == 47 * 48 * 7
    saved = pd.read_csv(DATA / "solar_case_scores.csv").set_index(["period", "model"])
    for row in scores.itertuples():
        subset = results[(results["period"] == row.period) & (results["model"] == row.model)]
        error = subset["prediction_mw"].to_numpy() - subset["actual_mw"].to_numpy()
        assert row.mae_mw == pytest.approx(np.abs(error).mean())
        assert row.rmse_mw == pytest.approx(np.sqrt(np.mean(error**2)))
        assert row.mae_mw == pytest.approx(saved.loc[(row.period, row.model), "mae_mw"], rel=1e-6)
    ranking = scores[scores["period"] == "August holdout"].set_index("model")
    mae, rmse = ranking["mae_mw"].to_dict(), ranking["rmse_mw"].to_dict()
    assert mae["Timestral"] < mae["Physical"]
    # The strong seasonal baselines must remain visible; no manufactured superiority.
    assert abs(mae["Timestral"] - mae["Daily median"]) < 0.001
    assert rmse["Daily mean"] < rmse["Timestral"]
    assert len(daily_errors(results)) == 78 * 7


def test_fit_fallback_is_auditable_without_dropping_outcomes(results: pd.DataFrame) -> None:
    final_issue = results["issue_time"].max()
    final = results[results["issue_time"] == final_issue]
    assert len(final) == 48 * 7
    for model in ("Physical", "LightGBM", "XGBoost"):
        assert final[final["model"] == model]["calibration_issue_time"].lt(final_issue).all()
    for model in ("Timestral", "Previous day", "Daily mean", "Daily median"):
        assert final[final["model"] == model]["calibration_issue_time"].eq(final_issue).all()
    with pytest.raises(ValueError, match="same unique"):
        solar_case_scores(results.iloc[1:])
    with pytest.raises(ValueError, match="Both development"):
        solar_case_scores(results[results["period"] == "Development"])


def test_search_audit_preserves_unfavorable_results() -> None:
    search = pd.read_csv(DATA / "plant_search.csv")
    assert search["plant_id"].nunique() == 20 and len(search) == 140
    pivot = search.pivot(index="plant_id", columns="model", values="mae_mw")
    gain = 1 - pivot["Timestral"] / pivot.drop(columns="Timestral").min(axis=1)
    assert gain.idxmax() == "RNMB06" and (gain > 0).sum() == 1
    variants = pd.read_csv(DATA / "variant_search.csv")
    best = variants.sort_values("mae_mw").iloc[0]
    assert len(variants) == 6 and (best["size"], best["inputs"]) == ("28M", "target_only")
    failed = pd.read_csv(DATA / "first_validation_scores.csv").set_index("model")
    assert failed["mae_mw"].loc["Timestral"] > failed["mae_mw"].loc["Daily mean"]
