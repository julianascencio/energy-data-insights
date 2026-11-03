"""Rolling-origin solar/wind forecasts with common pre-issue information.

Measured ONS generation is the target. Resource forecasts are deliberately
simple: previous-day valid irradiance and last-valid wind-speed persistence.
They are not archived NWP. Future measured weather and restriction flags never
enter a model. ONS observations are revised historical data, not an as-issued
SCADA vintage; this is a reproducible retrospective forecasting experiment.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from energy_data_retrieval.sources.ons import parse_generation_csv
from energy_methods._arrays import FloatArray, utc_index
from energy_methods.lightgbm import fit_lightgbm_features
from energy_methods.physics import fit_physics_model
from energy_methods.timestral import TimestralConnector
from energy_methods.wind_physics import fit_wind_physics
from energy_methods.xgboost import fit_xgboost

REFERENCE_IDS = ("ascencio_vasquez_2020_modelling", "ons_pv_curtailment", "ons_wind_curtailment")

FEATURES = ("resource", "clock_sin", "clock_cos", "power_previous_day_mw")
MODELS = ("Physical", "LightGBM", "XGBoost", "Timestral", "Previous day")
INPUT_MANIFEST = "forecast_ons_provenance.json"
TIMESTRAL_MANIFEST = "forecast_timestral_provenance.json"
TIMESTRAL_CSV = "forecast_timestral_predictions.csv"


@dataclass(frozen=True, slots=True)
class ForecastBenchmarkConfig:
    """Fourteen-day rolling fit/context, daily issues and a 24-hour horizon."""

    training_steps: int = 14 * 48
    horizon_steps: int = 48
    step_minutes: int = 30
    period_steps: int = 48

    def __post_init__(self) -> None:
        values = (self.training_steps, self.horizon_steps, self.step_minutes, self.period_steps)
        if any(type(value) is not int or value < 1 for value in values):
            raise ValueError("Benchmark sizes must be positive integers")
        if self.step_minutes != 30 or self.period_steps != 48 or self.horizon_steps != 48:
            raise ValueError("This ONS benchmark uses half-hour steps and daily 48-step forecasts")
        if self.training_steps <= self.period_steps:
            raise ValueError("Training must contain more than one daily period")


DEFAULT_CONFIG = ForecastBenchmarkConfig()


@dataclass(frozen=True, slots=True)
class ForecastFold:
    """A model-ready fold containing only history and constructed future features."""

    technology: str
    plant_id: str
    issue_time: pd.Timestamp
    future_index: pd.DatetimeIndex
    history_power: FloatArray
    train_features: FloatArray
    train_power: FloatArray
    future_features: FloatArray
    known_covariates: FloatArray
    baseline: FloatArray
    training_scale_mw: float

    @property
    def key(self) -> str:
        return f"{self.plant_id}|{self.issue_time.isoformat()}"

    @property
    def input_sha256(self) -> str:
        """Bind cached model output to all numerical inputs and forecast labels."""
        digest = hashlib.sha256(self.key.encode())
        digest.update("|".join(stamp.isoformat() for stamp in self.future_index).encode())
        for value in (self.history_power, self.known_covariates):
            array = np.ascontiguousarray(value, dtype="<f8")
            digest.update(str(array.shape).encode())
            digest.update(array.tobytes())
        return digest.hexdigest()


def load_benchmark_observations(data_directory: str | Path) -> dict[str, pd.DataFrame]:
    """Read checksum-verified native subsets and retain quality/restriction evidence."""
    directory = Path(data_directory)
    manifest = json.loads((directory / INPUT_MANIFEST).read_text())
    observations = {}
    for source in manifest["sources"]:
        technology = source["technology"]
        if technology not in {"solar", "wind"} or technology in observations:
            raise ValueError("Exactly one solar and one wind case are required")
        raw = (directory / f"forecast_ons_{technology}.csv").read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["sample_sha256"]:
            raise ValueError(f"{technology} input checksum does not match provenance")
        frame = parse_generation_csv(raw.decode(), product=f"{technology}_curtailment")
        if set(frame["unit_id"]) != {source["plant_id"]}:
            raise ValueError("The fixture must contain the declared single plant")
        resource = "val_irradianciaverificado" if technology == "solar" else "val_ventoverificado"
        flag = "flg_dadoirradianciainvalido" if technology == "solar" else "flg_dadoventoinvalido"
        index = utc_index(pd.DatetimeIndex(frame["timestamp"]))
        if len(index) < 2 or not (index[1:] - index[:-1] == pd.Timedelta(minutes=30)).all():
            raise ValueError("Observations must cover consecutive half-hour UTC labels")
        values = pd.DataFrame(
            {
                "power_mw": frame["value"].to_numpy(dtype=float),
                "resource": frame[resource].to_numpy(dtype=float),
                "resource_valid": pd.to_numeric(frame[flag], errors="raise").eq(0).to_numpy(),
                "restricted": pd.to_numeric(
                    frame["flg_geracaorestrita"], errors="raise"
                ).to_numpy(),
            },
            index=index,
        )
        if not np.isfinite(values["power_mw"]).all() or (values["power_mw"] < 0).any():
            raise ValueError("This fixed benchmark requires complete nonnegative measured power")
        values.attrs.update(plant_id=source["plant_id"], plant_name=source["plant_name"])
        observations[technology] = values
    if set(observations) != {"solar", "wind"}:
        raise ValueError("Exactly one solar and one wind case are required")
    return observations


def _calendar(index: pd.DatetimeIndex) -> FloatArray:
    phase = 2 * np.pi * (index.hour.to_numpy() + index.minute.to_numpy() / 60) / 24
    return np.column_stack((np.sin(phase), np.cos(phase)))


def prepare_forecast_fold(
    history: pd.DataFrame,
    future_index: pd.DatetimeIndex,
    technology: str,
    *,
    config: ForecastBenchmarkConfig = DEFAULT_CONFIG,
) -> ForecastFold:
    """Construct one forecast using history only; no future observation argument exists.

    Invalid historic resource readings stay missing. Solar forecasts use the most
    recent valid value at the same daily offset, searching older history if the
    previous day is flagged; wind uses its last valid reading. Unknown future
    resources are never filled from the held-out measurements.
    """
    if technology not in {"solar", "wind"}:
        raise ValueError("technology must be solar or wind")
    if len(history) != config.training_steps or len(future_index) != config.horizon_steps:
        raise ValueError("History/horizon sizes do not match the benchmark configuration")
    past_index = utc_index(pd.DatetimeIndex(history.index))
    future_index = utc_index(future_index)
    joined = pd.DatetimeIndex(past_index.append(future_index))
    if not (joined[1:] - joined[:-1] == pd.Timedelta(minutes=config.step_minutes)).all():
        raise ValueError("History and forecast labels must be consecutive with no overlap")
    power = history["power_mw"].to_numpy(dtype=float)
    resource = history["resource"].to_numpy(dtype=float).copy()
    valid = history["resource_valid"].to_numpy(dtype=bool) & np.isfinite(resource) & (resource >= 0)
    if technology == "solar":
        valid &= resource <= 1300
    resource[~valid] = np.nan
    if not np.isfinite(power).all() or (power < 0).any():
        raise ValueError("History power must be complete and nonnegative")
    if not valid.any():
        raise ValueError("No valid historical resource observations")
    if technology == "solar" and not (resource > 1).any():
        raise ValueError("Solar history has no identifiable positive irradiance response")
    predicted_resource = np.empty(config.horizon_steps)
    for lead in range(config.horizon_steps):
        candidates = (
            resource[len(resource) + lead - config.period_steps :: -config.period_steps]
            if technology == "solar"
            else resource[::-1]
        )
        finite = candidates[np.isfinite(candidates)]
        if not len(finite):
            raise ValueError("No pre-issue resource value at the required daily offset")
        predicted_resource[lead] = finite[0]
    past_calendar = _calendar(past_index)
    future_calendar = _calendar(future_index)
    lag = np.full(len(power), np.nan)
    lag[config.period_steps :] = power[: -config.period_steps]
    baseline = power[-config.period_steps :][: config.horizon_steps].copy()
    training = np.column_stack((resource, past_calendar, lag))
    usable = np.isfinite(training).all(axis=1)
    future = np.column_stack((predicted_resource, future_calendar, baseline))
    known = np.vstack((training, future)).T[None, ...]
    scale = float(np.quantile(power, 0.95))
    if usable.sum() < 48 or scale <= 0:
        raise ValueError("Insufficient finite training rows or positive historical power scale")
    return ForecastFold(
        technology,
        str(history.attrs["plant_id"]),
        past_index[-1],
        future_index,
        power[None, None, :],
        training[usable],
        power[usable],
        future,
        known,
        baseline,
        scale,
    )


def forecast_folds(
    observations: dict[str, pd.DataFrame], *, config: ForecastBenchmarkConfig = DEFAULT_CONFIG
) -> list[ForecastFold]:
    """Use each test day once, refitting on the preceding fixed-length window."""
    folds = []
    for technology, frame in observations.items():
        for start in range(
            config.training_steps, len(frame) - config.horizon_steps + 1, config.horizon_steps
        ):
            history = frame.iloc[start - config.training_steps : start].copy()
            index = pd.DatetimeIndex(frame.index[start : start + config.horizon_steps])
            folds.append(prepare_forecast_fold(history, index, technology, config=config))
    if not folds:
        raise ValueError("No complete holdout horizon remains after training")
    return folds


def _timestral_rows(fold: ForecastFold, connector: TimestralConnector) -> pd.DataFrame:
    forecast = connector.forecast(
        fold.history_power, len(fold.future_index), known_covariates=fold.known_covariates
    )
    return pd.DataFrame(
        {
            "plant_id": fold.plant_id,
            "issue_time": fold.issue_time.isoformat(),
            "timestamp": [stamp.isoformat() for stamp in fold.future_index],
            "prediction_mw": forecast.median[0, 0],
            "p10_mw": forecast.quantile(0.1)[0, 0],
            "p90_mw": forecast.quantile(0.9)[0, 0],
        }
    )


def capture_timestral_forecasts(
    folds: list[ForecastFold], connector: TimestralConnector
) -> pd.DataFrame:
    """Run actual model inference for every origin; no fabricated fallback outputs."""
    return pd.concat([_timestral_rows(fold, connector) for fold in folds], ignore_index=True)


def load_timestral_forecasts(
    directory: str | Path,
    folds: list[ForecastFold],
    *,
    config: ForecastBenchmarkConfig = DEFAULT_CONFIG,
) -> pd.DataFrame:
    """Reject stale predictions when data, model inputs or issue times change."""
    directory = Path(directory)
    raw = (directory / TIMESTRAL_CSV).read_bytes()
    manifest = json.loads((directory / TIMESTRAL_MANIFEST).read_text())
    if manifest["forecast_sha256"] != hashlib.sha256(raw).hexdigest():
        raise ValueError("Saved Timestral forecast checksum differs from provenance")
    if manifest["config"] != asdict(config) or manifest["fold_inputs"] != {
        fold.key: fold.input_sha256 for fold in folds
    }:
        raise ValueError("Timestral snapshot is stale for these forecast inputs/configuration")
    frame = pd.read_csv(directory / TIMESTRAL_CSV)
    return _validate_timestral_rows(frame, folds)


def _validate_timestral_rows(frame: pd.DataFrame, folds: list[ForecastFold]) -> pd.DataFrame:
    frame = frame.copy()
    keys = ["plant_id", "issue_time", "timestamp"]
    for column in keys[1:]:
        frame[column] = pd.to_datetime(frame[column], utc=True)
    if frame.duplicated(keys).any():
        raise ValueError("Duplicate Timestral forecast keys")
    expected = {
        (fold.plant_id, fold.issue_time, stamp) for fold in folds for stamp in fold.future_index
    }
    if set(frame[keys].itertuples(index=False, name=None)) != expected:
        raise ValueError("Timestral forecast coverage differs from the common holdout")
    values = frame[["p10_mw", "prediction_mw", "p90_mw"]].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (np.diff(values, axis=1) < 0).any():
        raise ValueError("Timestral forecasts must be finite with ordered quantiles")
    return frame


def run_forecast_benchmark(
    data_directory: str | Path,
    *,
    connector: TimestralConnector | None = None,
    config: ForecastBenchmarkConfig = DEFAULT_CONFIG,
) -> pd.DataFrame:
    """Fit LightGBM/XGBoost/physical models locally and replay or run Timestral.

    Four models plus the previous-day baseline are evaluated on identical future
    labels, with common nonnegative clipping. Restriction flags only annotate
    verification rows; they never filter fitting or forecasting observations.
    """
    observations = load_benchmark_observations(data_directory)
    folds = forecast_folds(observations, config=config)
    timestral = (
        load_timestral_forecasts(data_directory, folds, config=config)
        if connector is None
        else _validate_timestral_rows(capture_timestral_forecasts(folds, connector), folds)
    )
    timestral = timestral.set_index(["plant_id", "issue_time", "timestamp"]).sort_index()
    records = []
    for fold in folds:
        lgb = fit_lightgbm_features(fold.train_features, fold.train_power, feature_names=FEATURES)
        xgb = fit_xgboost(fold.train_features, fold.train_power, feature_names=FEATURES)
        if fold.technology == "solar":
            # Existing PV API uses interval MWh. Convert MW means to half-hour
            # MWh before fitting, then back. ONS has no temperature/plane metadata:
            # constant 25 C and POA-proxy irradiance define an isothermal surrogate.
            physical = fit_physics_model(
                fold.train_features[:, 0],
                np.full(len(fold.train_power), 25.0),
                fold.train_power * 0.5,
            )
            physical_values = (
                physical.predict(fold.future_features[:, 0], np.full(len(fold.future_index), 25.0))
                / 0.5
            )
        else:
            wind = fit_wind_physics(fold.train_features[:, 0], fold.train_power)
            physical_values = wind.predict(fold.future_features[:, 0])
        captured = timestral.xs((fold.plant_id, fold.issue_time), level=[0, 1]).reindex(
            fold.future_index
        )
        predictions = {
            "Physical": physical_values,
            "LightGBM": lgb.predict(fold.future_features),
            "XGBoost": xgb.predict(fold.future_features),
            "Timestral": captured["prediction_mw"].to_numpy(),
            "Previous day": fold.baseline,
        }
        truth = observations[fold.technology].loc[fold.future_index]
        for model, predicted in predictions.items():
            if not np.isfinite(predicted).all():
                raise ValueError(f"{model} failed a common holdout row; no selective scoring")
            for i, stamp in enumerate(fold.future_index):
                records.append(
                    {
                        "technology": fold.technology,
                        "plant_id": fold.plant_id,
                        "model": model,
                        "issue_time": fold.issue_time,
                        "timestamp": stamp,
                        "lead_hours": (i + 1) * config.step_minutes / 60,
                        "actual_mw": float(truth["power_mw"].iloc[i]),
                        "prediction_mw": max(0.0, float(predicted[i])),
                        "training_q95_mw": fold.training_scale_mw,
                        "training_rows": len(fold.train_power),
                        "resource_forecast": float(fold.future_features[i, 0]),
                        "restricted": int(truth["restricted"].iloc[i]),
                        "p10_mw": max(0.0, float(captured["p10_mw"].iloc[i]))
                        if model == "Timestral"
                        else np.nan,
                        "p90_mw": max(0.0, float(captured["p90_mw"].iloc[i]))
                        if model == "Timestral"
                        else np.nan,
                    }
                )
    return pd.DataFrame(records)


def benchmark_scores(predictions: pd.DataFrame, *, by_lead: bool = False) -> pd.DataFrame:
    """Score every model on exactly the same keys; never drop failed predictions."""
    key = ["plant_id", "issue_time", "timestamp"]
    required = {"technology", "model", *key, "actual_mw", "prediction_mw", "training_q95_mw"}
    if required - set(predictions) or predictions.empty:
        raise ValueError("Incomplete forecast result table")
    if set(predictions["model"]) != set(MODELS):
        raise ValueError("The benchmark must contain exactly the four models and daily baseline")
    expected = None
    for model in MODELS:
        rows = predictions[predictions["model"] == model]
        keys = set(rows[key].itertuples(index=False, name=None))
        if rows.duplicated(key).any() or not keys or (expected is not None and keys != expected):
            raise ValueError("All models must cover the same unique forecast keys")
        expected = keys
    numeric = predictions[["actual_mw", "prediction_mw", "training_q95_mw"]].to_numpy()
    if not np.isfinite(numeric).all() or (predictions["training_q95_mw"] <= 0).any():
        raise ValueError("Cannot score missing predictions or invalid historical scales")
    if predictions.groupby(key)["actual_mw"].nunique().ne(1).any():
        raise ValueError("Models must share the same verification observations")
    if predictions.groupby(key)["training_q95_mw"].nunique().ne(1).any():
        raise ValueError("Models must share the same pre-issue normalization scale")
    group = ["technology", "model"] + (["lead_hours"] if by_lead else [])
    output = []
    for keys, frame in predictions.groupby(group, sort=True):
        actual = frame["actual_mw"].to_numpy()
        residual = frame["prediction_mw"].to_numpy() - actual
        denominator = float(np.abs(actual).sum())
        row = dict(zip(group, keys, strict=True))
        row.update(
            samples=len(frame),
            origins=frame["issue_time"].nunique(),
            mae_mw=float(np.abs(residual).mean()),
            rmse_mw=float(np.sqrt(np.mean(residual**2))),
            bias_mw=float(residual.mean()),
            wape_pct=np.nan
            if denominator == 0
            else float(np.abs(residual).sum()) / denominator * 100,
            nmae_training_q95_pct=float(np.mean(np.abs(residual) / frame["training_q95_mw"])) * 100,
            p10_p90_coverage=np.nan,
        )
        if row["model"] == "Timestral":
            row["p10_p90_coverage"] = float(
                (
                    (frame["actual_mw"] >= frame["p10_mw"])
                    & (frame["actual_mw"] <= frame["p90_mw"])
                ).mean()
            )
        output.append(row)
    scores = pd.DataFrame(output)
    baseline_keys = ["technology"] + (["lead_hours"] if by_lead else [])
    baseline = scores[scores["model"] == "Previous day"].set_index(baseline_keys)["mae_mw"]
    scores["mae_skill_vs_previous_day"] = [
        np.nan if baseline.loc[keys] == 0 else 1 - mae / baseline.loc[keys]
        for keys, mae in zip(
            (
                tuple(x) if by_lead else x[0]
                for x in scores[baseline_keys].itertuples(index=False, name=None)
            ),
            scores["mae_mw"],
            strict=True,
        )
    ]
    return scores
