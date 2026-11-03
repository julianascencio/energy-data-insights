"""Real captured inference is reproducible offline and evaluated without leakage."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import numpy as np
import pytest

from energy_analysis.timestral_case import (
    PROVENANCE_NAME,
    SNAPSHOT_NAME,
    evaluate_timestral_case,
    forecast_timestral_case,
    load_timestral_case,
    load_timestral_snapshot,
)
from energy_methods.timestral import TimestralConnector

DATA = Path(__file__).resolve().parents[2] / "examples/connectors/data"


def test_real_snapshot_and_same_signed_holdout_for_every_model() -> None:
    case = load_timestral_case(DATA)
    forecast = load_timestral_snapshot(DATA, case)
    metrics = evaluate_timestral_case(case, forecast)
    assert case.context.shape == (1, 2, 144)
    assert case.actual.shape == (2, 24)
    assert case.known_covariates.shape == (1, 2, 168)
    assert forecast.quantiles.shape == (1, 2, 24, 21)
    assert len(metrics) == 6
    assert set(metrics.hours) == {24}
    assert (case.actual[0] < 0).any()  # signed nighttime observations must survive
    solar = metrics[(metrics.model == "Timestral median") & (metrics.fuel == "SUN")].iloc[0]
    residual = forecast.median[0, 0] - case.actual[0]
    assert solar.mae_mwh == pytest.approx(np.abs(residual).mean())
    assert solar.wape_pct == pytest.approx(
        100 * np.abs(residual).sum() / np.abs(case.actual[0]).sum()
    )


def test_future_target_values_are_not_sent_to_the_model() -> None:
    case = load_timestral_case(DATA)
    backend = Mock()
    backend.forecast.return_value = SimpleNamespace(
        quantiles=np.ones((1, 2, 24, 3)), quantile_levels=(0.1, 0.5, 0.9)
    )
    case.actual[:] = 1e9
    forecast_timestral_case(case, TimestralConnector(forecaster=backend))
    call = backend.forecast.call_args
    np.testing.assert_array_equal(call.args[0], case.context)
    assert call.args[0].shape[-1] == 144
    assert call.kwargs["known_covariates"].shape[-1] == 168
    assert np.abs(call.kwargs["known_covariates"]).max() <= 1


@pytest.mark.parametrize(
    "field", ["source_sha256", "context_sha256", "known_covariates_sha256", "forecast_sha256"]
)
def test_stale_snapshot_is_rejected(tmp_path: Path, field: str) -> None:
    case = load_timestral_case(DATA)
    manifest = json.loads((DATA / PROVENANCE_NAME).read_text())
    manifest[field] = "changed"
    (tmp_path / PROVENANCE_NAME).write_text(json.dumps(manifest))
    shutil.copyfile(DATA / SNAPSHOT_NAME, tmp_path / SNAPSHOT_NAME)
    with pytest.raises(ValueError, match="checksums differ"):
        load_timestral_snapshot(tmp_path, case)


def test_corrupt_observations_fail_before_parsing(tmp_path: Path) -> None:
    for name in ("generation_eia_ciso_2024.csv", "generation_eia_ciso_2024.provenance.json"):
        shutil.copyfile(DATA / name, tmp_path / name)
    (tmp_path / "generation_eia_ciso_2024.csv").write_text("invalid")
    with pytest.raises(ValueError, match="EIA source checksum"):
        load_timestral_case(tmp_path)
