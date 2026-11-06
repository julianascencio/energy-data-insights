"""Leakage-safe AEMET daily ambient-temperature forecasting benchmark.

Input: AEMET OpenData daily climatology CSV with fecha, indicativo, tmed.
Optional dependencies: pip install pandas numpy scikit-learn statsmodels prophet
lightgbm xgboost chronos-forecasting timesfm timestral
Foundation-model adapters are deliberately not faked: add verified inference
separately rather than presenting persistence as a foundation-model result.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def load_aemet(path: Path, station: str) -> pd.Series:
    frame = pd.read_csv(path, dtype=str)
    required = {"fecha", "indicativo", "tmed"}
    if not required.issubset(frame):
        raise ValueError(f"AEMET CSV must contain {sorted(required)}")
    frame = frame.loc[frame["indicativo"] == station].copy()
    frame["fecha"] = pd.to_datetime(frame["fecha"], errors="coerce")
    frame["tmed"] = pd.to_numeric(frame["tmed"].str.replace(",", ".", regex=False), errors="coerce")
    series = frame.dropna(subset=["fecha"]).set_index("fecha")["tmed"].sort_index()
    if series.index.has_duplicates:
        raise ValueError("Duplicate dates for station")
    return series.asfreq("D")


def features(dates: pd.DatetimeIndex, history: pd.Series) -> pd.DataFrame:
    day = dates.dayofyear.to_numpy()
    return pd.DataFrame({
        "sin_year": np.sin(2 * np.pi * day / 365.25),
        "cos_year": np.cos(2 * np.pi * day / 365.25),
        "trend": (dates - history.index[0]).days.to_numpy(),
    }, index=dates)


def forecast(name: str, train: pd.Series, future: pd.DatetimeIndex) -> np.ndarray:
    if name == "last_value":
        return np.repeat(train.iloc[-1], len(future))
    if name == "seasonal_7":
        return np.array([train.iloc[-7 + (i % 7)] for i in range(len(future))])
    if name in {"lightgbm", "xgboost"}:
        if name == "lightgbm":
            from lightgbm import LGBMRegressor
            model = LGBMRegressor(n_estimators=150, learning_rate=0.05, verbosity=-1, random_state=42)
        else:
            from xgboost import XGBRegressor
            model = XGBRegressor(n_estimators=150, max_depth=3, learning_rate=0.05, random_state=42)
        model.fit(features(train.index, train), train.to_numpy())
        return np.asarray(model.predict(features(future, train)))
    if name == "arima":
        from statsmodels.tsa.arima.model import ARIMA
        return np.asarray(ARIMA(train, order=(2, 0, 2)).fit().forecast(len(future)))
    if name == "ets":
        from statsmodels.tsa.holtwinters import ExponentialSmoothing
        return np.asarray(ExponentialSmoothing(train, trend="add", seasonal=None).fit().forecast(len(future)))
    if name == "prophet":
        from prophet import Prophet
        model = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        model.fit(pd.DataFrame({"ds": train.index, "y": train.to_numpy()}))
        return model.predict(pd.DataFrame({"ds": future}))["yhat"].to_numpy()
    raise ValueError(f"Unsupported or unverified model: {name}")


def benchmark(series: pd.Series, models: list[str], horizons: list[int], origins: int) -> pd.DataFrame:
    """Expanding-window, non-overlapping origins; no test-label imputation."""
    rows = []
    for horizon in horizons:
        available = [i for i in range(365, len(series) - horizon + 1, horizon)
                     if series.iloc[:i].notna().all() and series.iloc[i:i+horizon].notna().all()]
        for i in available[-origins:]:
            train = series.iloc[:i]
            actual = series.iloc[i:i+horizon].to_numpy()
            for name in models:
                prediction = forecast(name, train, series.index[i:i+horizon])
                if len(prediction) != horizon or not np.isfinite(prediction).all():
                    raise ValueError(f"Incomplete forecast: {name}, origin={series.index[i]}")
                errors = prediction - actual
                rows.append({"model": name, "horizon_days": horizon,
                             "origin": str(series.index[i-1].date()),
                             "mae_c": float(np.abs(errors).mean()),
                             "rmse_c": float(np.sqrt(np.square(errors).mean())),
                             "bias_c": float(errors.mean()), "n": horizon})
    if not rows:
        raise ValueError("No complete eligible origins; inspect AEMET missing data and coverage")
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True, help="AEMET daily climatology CSV")
    parser.add_argument("--station", required=True, help="Exact AEMET indicativo")
    parser.add_argument("--output", type=Path, default=Path("aemet_temperature_scores.csv"))
    parser.add_argument("--models", nargs="+", default=["last_value", "seasonal_7", "arima", "ets"])
    parser.add_argument("--origins", type=int, default=6)
    args = parser.parse_args()
    if args.origins < 1:
        parser.error("--origins must be positive")
    data = load_aemet(args.csv, args.station)
    scores = benchmark(data, args.models, [1, 7, 30], args.origins)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    scores.to_csv(args.output, index=False)
    summary = scores.groupby(["model", "horizon_days"])[["mae_c", "rmse_c", "bias_c"]].mean()
    print(summary.to_string())
    args.output.with_suffix(".metadata.json").write_text(json.dumps({
        "station": args.station, "source_file": str(args.csv),
        "target": "AEMET daily tmed (C)", "source_type": "observed",
        "validation": "expanding origin, complete-case, no future covariates",
        "intervals": "not available; do not infer 80% coverage from point forecasts",
    }, indent=2))


if __name__ == "__main__":
    main()
