"""Connector contract tests run without torch, model downloads or network access."""

from __future__ import annotations

import subprocess
import sys
from types import SimpleNamespace
from typing import TypedDict
from unittest.mock import Mock

import numpy as np
import pytest
from numpy.typing import ArrayLike

import energy_methods.timestral as module
from energy_methods.timestral import TimestralConnector, TimestralForecast


class RecordingBackend:
    def __init__(self) -> None:
        self.calls: list[tuple[np.ndarray, int, dict[str, object]]] = []

    def forecast(self, context: np.ndarray, prediction_length: int, **kwargs: object) -> object:
        self.calls.append((context.copy(), prediction_length, kwargs))
        values = np.broadcast_to(
            np.array([1.0, 2.0, 3.0]), (*context.shape[:2], prediction_length, 3)
        ).copy()
        return SimpleNamespace(quantiles=values, quantile_levels=(0.1, 0.5, 0.9))


def test_import_and_construction_do_not_import_optional_model() -> None:
    subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; from energy_methods.timestral import TimestralConnector; "
            "TimestralConnector(); assert 'torch' not in sys.modules; "
            "assert 'timestral' not in sys.modules",
        ],
        check=True,
    )


@pytest.mark.parametrize(
    "shape,expected", [((5,), (1, 1, 3)), ((2, 5), (2, 1, 3)), ((2, 3, 5), (2, 3, 3))]
)
def test_shapes_and_units_are_preserved(shape: tuple, expected: tuple) -> None:
    backend = RecordingBackend()
    context = np.ones(shape) * 1500
    result = TimestralConnector(forecaster=backend).forecast(context, 3)
    assert result.median.shape == expected
    np.testing.assert_array_equal(result.median, 2)
    assert np.all(backend.calls[0][0] == 1500)
    assert context.shape == shape
    with pytest.raises(ValueError, match="read-only"):
        result.quantiles.flat[0] = 0
    with pytest.raises(ValueError, match="Unsupported quantile"):
        result.quantile(0.25)


def test_mask_and_all_covariates_trim_together_without_mutating_inputs() -> None:
    backend = RecordingBackend()
    connector = TimestralConnector(max_context=3, forecaster=backend)
    context = np.arange(6.0)
    context[-2] = np.nan
    mask = np.array([True, True, True, True, True, False])
    past = np.arange(6.0).reshape(1, 1, 6)
    known = np.arange(8.0).reshape(1, 1, 8)
    connector.forecast(
        context,
        2,
        observation_mask=mask,
        past_covariates=past,
        known_covariates=known,
        categorical_past_covariates=past,
        categorical_known_covariates=known,
        clip_nonnegative=False,
        symmetric_averaging=False,
    )
    x, horizon, kwargs = backend.calls[0]
    assert horizon == 2
    np.testing.assert_array_equal(x[0, 0], [3, np.nan, 5])
    np.testing.assert_array_equal(kwargs["observation_mask"], [[[True, False, False]]])
    for name in ("past_covariates", "categorical_past_covariates"):
        np.testing.assert_array_equal(kwargs[name], [[[3, 4, 5]]])
    for name in ("known_covariates", "categorical_known_covariates"):
        np.testing.assert_array_equal(kwargs[name], [[[3, 4, 5, 6, 7]]])
    assert kwargs["clip_nonnegative"] is False
    assert kwargs["symmetric_averaging"] is False
    np.testing.assert_array_equal(known, np.arange(8.0).reshape(1, 1, 8))
    assert mask[-1] == np.bool_(False)


@pytest.mark.parametrize(
    "context", [[], np.empty((0, 4)), np.zeros((1, 1, 1, 1)), [np.nan], [1, np.inf], 2.0]
)
def test_invalid_context_is_rejected_before_loading(context: ArrayLike) -> None:
    connector = TimestralConnector()
    with pytest.raises(ValueError):
        connector.forecast(context, 2)
    assert connector._forecaster is None


@pytest.mark.parametrize("horizon", [0, -1, True, 1.5])
def test_invalid_horizon_is_rejected(horizon: int) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        TimestralConnector().forecast([1, 2], horizon)


@pytest.mark.parametrize("maximum", [0, 32769, True, 1.5])
def test_context_cap_is_validated(maximum: int) -> None:
    with pytest.raises(ValueError):
        TimestralConnector(max_context=maximum)


def test_retained_context_must_have_observed_value_for_every_target() -> None:
    with pytest.raises(ValueError, match="observed value"):
        TimestralConnector(max_context=2).forecast([1, np.nan, np.nan], 2)
    with pytest.raises(ValueError, match="observed value"):
        TimestralConnector().forecast(
            [[1, 2], [3, 4]], 2, observation_mask=[[True, True], [False, False]]
        )


@pytest.mark.parametrize("mask", [[1, 0], [True], [[True, False]]])
def test_mask_requires_exact_shape_and_boolean_values(mask: list) -> None:
    with pytest.raises(ValueError, match="observation_mask"):
        TimestralConnector().forecast([1, 2], 1, observation_mask=mask)


class Covariates(TypedDict, total=False):
    past_covariates: ArrayLike
    known_covariates: ArrayLike
    categorical_past_covariates: ArrayLike
    categorical_known_covariates: ArrayLike


@pytest.mark.parametrize(
    "name,malformed,invalid",
    [
        ("past_covariates", {"past_covariates": [[1, 2]]}, {"past_covariates": [[[np.inf, 2]]]}),
        ("known_covariates", {"known_covariates": [[1, 2]]}, {"known_covariates": [[[np.inf, 2]]]}),
        (
            "categorical_past_covariates",
            {"categorical_past_covariates": [[1, 2]]},
            {"categorical_past_covariates": [[[np.inf, 2]]]},
        ),
        (
            "categorical_known_covariates",
            {"categorical_known_covariates": [[1, 2]]},
            {"categorical_known_covariates": [[[np.inf, 2]]]},
        ),
    ],
)
def test_covariate_shapes_and_infinity_are_rejected(
    name: str,
    malformed: Covariates,
    invalid: Covariates,
) -> None:
    connector = TimestralConnector()
    with pytest.raises(ValueError, match=name):
        connector.forecast([1, 2], 1, **malformed)
    with pytest.raises(ValueError, match="infinity"):
        connector.forecast([1, 2], 1, **invalid)


def test_missing_optional_dependency_has_actionable_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(module, "import_module", Mock(side_effect=ImportError("missing")))
    with pytest.raises(
        ImportError, match=r"pip install git\+https://github.com/mistralai/timestral"
    ):
        TimestralConnector().forecast([1, 2], 1)


def test_loading_options_forwarded_once_and_failures_never_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend = RecordingBackend()
    loader = Mock(return_value=backend)
    monkeypatch.setattr(
        module,
        "import_module",
        lambda _: SimpleNamespace(TimestralForecaster=SimpleNamespace(from_pretrained=loader)),
    )
    connector = TimestralConnector(
        "model/path",
        revision="pinned",
        cache_dir="cache",
        device="cpu",
        local_files_only=True,
        max_context=128,
    )
    connector.forecast([1, 2], 2)
    connector.forecast([1, 2], 2)
    loader.assert_called_once_with(
        "model/path",
        device="cpu",
        revision="pinned",
        cache_dir="cache",
        local_files_only=True,
        max_context=128,
    )
    broken = Mock()
    broken.forecast.side_effect = RuntimeError("checkpoint failure")
    with pytest.raises(RuntimeError, match="checkpoint failure"):
        TimestralConnector(forecaster=broken).forecast([1, 2], 2)


def test_gpu_like_tensor_is_detached_and_moved_to_cpu() -> None:
    tensor = Mock()
    tensor.detach.return_value.cpu.return_value.numpy.return_value = np.ones((1, 1, 2, 3))
    backend = Mock()
    backend.forecast.return_value = SimpleNamespace(
        quantiles=tensor, quantile_levels=(0.1, 0.5, 0.9)
    )
    result = TimestralConnector(forecaster=backend).forecast([1, 2], 2)
    assert result.median.shape == (1, 1, 2)
    tensor.detach.assert_called_once()
    tensor.detach.return_value.cpu.assert_called_once()


@pytest.mark.parametrize(
    "levels", [(0.5, 0.1), (0.1, 0.9), (0.5, 0.5), (0, 0.5), (0.5, np.nan), (0.5, 1)]
)
def test_bad_quantile_levels_rejected(levels: tuple) -> None:
    with pytest.raises(ValueError, match="Quantile levels"):
        TimestralForecast(np.ones((1, 1, 2, len(levels))), levels)


@pytest.mark.parametrize(
    "values", [[[[[3, 2, 1]]]], [[[[1, np.inf, 3]]]], np.ones((1, 1, 2)), np.ones((1, 1, 0, 3))]
)
def test_bad_forecast_output_rejected(values: object) -> None:
    with pytest.raises(ValueError):
        TimestralForecast(np.asarray(values), (0.1, 0.5, 0.9))


def test_wrong_model_output_dimensions_rejected() -> None:
    backend = Mock()
    backend.forecast.return_value = SimpleNamespace(
        quantiles=np.ones((2, 1, 2, 3)), quantile_levels=(0.1, 0.5, 0.9)
    )
    with pytest.raises(ValueError, match="requested batch"):
        TimestralConnector(forecaster=backend).forecast([1, 2], 2)
