"""Real captured ONS inputs; no network or optional Timestral runtime required."""

import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.forecast_benchmark import (
    MODELS,
    TIMESTRAL_CSV,
    TIMESTRAL_MANIFEST,
    benchmark_scores,
    forecast_folds,
    load_benchmark_observations,
    load_timestral_forecasts,
    prepare_forecast_fold,
    run_forecast_benchmark,
)

DATA = Path(__file__).resolve().parents[2] / "examples/analysis/data/forecast"


def test_real_inputs_and_preissue_folds() -> None:
    observations = load_benchmark_observations(DATA)
    folds = forecast_folds(observations)
    assert len(folds) == 32
    for fold in folds:
        assert len(fold.future_index) == 48
        assert fold.future_index[0] - fold.issue_time == pd.Timedelta(minutes=30)
        assert fold.future_index[-1] - fold.issue_time == pd.Timedelta(hours=24)
        assert fold.history_power.shape == (1, 1, 672)
        assert fold.known_covariates.shape == (1, 4, 720)
        assert np.isfinite(fold.future_features).all()
        assert fold.train_features.shape[1] == 4
    saved = load_timestral_forecasts(DATA, folds)
    assert len(saved) == 1536
    assert {f.plant_id for f in folds} == {"PBFCM4", "MAEDT1"}


@pytest.mark.parametrize("technology", ["solar", "wind"])
def test_future_outcomes_cannot_change_current_forecast_inputs(technology: str) -> None:
    observations = load_benchmark_observations(DATA)
    frame = observations[technology]
    before = forecast_folds({technology: frame})[0]
    altered = frame.copy()
    altered.loc[altered.index[672:], ["resource", "power_mw"]] *= 100
    altered.loc[altered.index[672:], "restricted"] = 1
    after = forecast_folds({technology: altered.iloc[:720].copy()})[0]
    assert after.input_sha256 == before.input_sha256
    np.testing.assert_array_equal(after.train_features, before.train_features)
    np.testing.assert_array_equal(after.future_features, before.future_features)
    # Restriction labels are evaluation annotations, including in history.
    history = frame.iloc[:672].copy()
    history["restricted"] = 1
    assert (
        prepare_forecast_fold(history, before.future_index, technology).input_sha256
        == before.input_sha256
    )


def test_invalid_resource_fallback_only_searches_past_same_clock() -> None:
    frame = load_benchmark_observations(DATA)["solar"]
    history = frame.iloc[:672].copy()
    history.loc[history.index[-48], "resource_valid"] = False
    fold = prepare_forecast_fold(history, pd.DatetimeIndex(frame.index[672:720]), "solar")
    assert fold.future_features[0, 0] == history["resource"].iloc[-96]
    assert np.isnan(fold.known_covariates[0, 0, -96])
    assert len(fold.train_power) == history["resource_valid"].iloc[48:].sum()
    history["resource_valid"] = False
    with pytest.raises(ValueError, match="No valid"):
        prepare_forecast_fold(history, fold.future_index, "solar")


def test_snapshot_rejects_corruption_and_changed_inputs(tmp_path: Path) -> None:
    for path in DATA.glob("*"):
        shutil.copy(path, tmp_path / path.name)
    folds = forecast_folds(load_benchmark_observations(DATA))
    path = tmp_path / TIMESTRAL_MANIFEST
    manifest = json.loads(path.read_text())
    manifest["fold_inputs"][folds[0].key] = "changed"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="stale"):
        load_timestral_forecasts(tmp_path, folds)
    (tmp_path / TIMESTRAL_CSV).write_text("corrupted")
    with pytest.raises(ValueError, match="checksum"):
        load_timestral_forecasts(tmp_path, folds)
    (tmp_path / "forecast_ons_wind.csv").write_text("corrupted")
    with pytest.raises(ValueError, match="checksum"):
        load_benchmark_observations(tmp_path)


@pytest.fixture(scope="module")
def results() -> pd.DataFrame:
    return run_forecast_benchmark(DATA)


def test_complete_benchmark_and_independent_metric_calculation(results: pd.DataFrame) -> None:
    scores = benchmark_scores(results)
    assert len(results) == 7680 and len(scores) == 10
    assert set(scores["model"]) == set(MODELS)
    assert scores["samples"].eq(768).all() and scores["origins"].eq(16).all()
    for row in scores.itertuples():
        group = results[(results["technology"] == row.technology) & (results["model"] == row.model)]
        error = group["prediction_mw"].to_numpy() - group["actual_mw"].to_numpy()
        assert row.mae_mw == pytest.approx(np.mean(np.abs(error)))
        assert row.rmse_mw == pytest.approx(np.sqrt(np.mean(error**2)))
    assert len(benchmark_scores(results, by_lead=True)) == 480
    # The fixture is never selected/filtered by test errors or curtailment.
    assert results["restricted"].gt(0).any()
    assert results["prediction_mw"].ge(0).all()


@pytest.mark.parametrize("damage", ["drop", "duplicate", "missing", "truth", "scale", "model"])
def test_scoring_refuses_selective_coverage(results: pd.DataFrame, damage: str) -> None:
    bad = results.copy()
    if damage == "drop":
        bad = bad.iloc[1:]
    elif damage == "duplicate":
        bad = pd.concat([bad, bad.iloc[:1]])
    elif damage == "missing":
        bad.loc[0, "prediction_mw"] = np.nan
    elif damage == "truth":
        bad.loc[0, "actual_mw"] = float(bad["actual_mw"].iloc[0]) + 1
    elif damage == "scale":
        bad.loc[0, "training_q95_mw"] = float(bad["training_q95_mw"].iloc[0]) + 1
    else:
        bad = bad[bad["model"] != "Timestral"]
    with pytest.raises(ValueError):
        benchmark_scores(bad)
