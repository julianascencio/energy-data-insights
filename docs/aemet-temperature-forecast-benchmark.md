# AEMET ambient-temperature forecasting benchmark (initial implementation)

This is a **daily** ambient-temperature experiment using AEMET OpenData `tmed` in °C, not an hourly temperature forecast. The existing AEMET connector can acquire station observations; this runner accepts the resulting native daily climatology CSV (`fecha, indicativo, tmed`) to keep source acquisition and forecasting separate.

## Run

```bash
pip install numpy pandas scikit-learn statsmodels
python examples/analysis/aemet_temperature_benchmark.py --csv path/to/aemet_daily.csv --station YOUR_AEMET_INDICATIVO
# Additional optional methods:
pip install lightgbm xgboost prophet
python examples/analysis/aemet_temperature_benchmark.py --csv path/to/aemet_daily.csv --station YOUR_AEMET_INDICATIVO --models last_value seasonal_7 arima ets prophet lightgbm xgboost
```

The output is a per-origin score CSV and metadata JSON. Requires at least one year of complete daily training observations and full, observed test horizons. It raises rather than fabricate scores if no valid folds exist. Choose a station from the AEMET inventory with sufficient uninterrupted observations. No station-specific results are asserted until the runner is executed on verified source data.

## Benchmark design

- Daily mean temperature, horizons 1, 7 and 30 days, expanding chronological training window and non-overlapping forecast origins.
- Persistence, weekly seasonal persistence, ARIMA(2,0,2), nonseasonal additive-trend ETS, Prophet, LightGBM, XGBoost. All tree-model future features are deterministic calendar features; **no realized future weather**.
- Per-origin MAE, RMSE and bias in °C. No artificial temperature clipping.
- Models are refitted at each origin. Missing dates are not silently interpolated. AEMET daily mean is not the same quantity as instantaneous hourly ambient temperature.

## Next phase — unimplemented, do not report as tested

Integrate actual pinned Mistral Timestral, Amazon Chronos-2 and Google TimesFM inference, respecting each model's context length and supported horizon; preserve model versions and weights licence. Use verified model outputs only, never surrogate predictions labeled as foundation models.

Add native predictive 10th/90th quantiles or rolling-calibration residual intervals (trained only on pre-origin data), then report empirical 80% coverage and mean interval width. The LinkedIn hotel-price claim is not an AEMET result; 94% observed coverage for a nominal 80% interval may indicate conservative intervals, not necessarily superior calibration.

Finally publish the verified station ID, data dates, data-source provenance/hash, model package versions, actual scores and runnable Sphinx gallery page after execution and CI checks. This initial implementation is **not a completed seven-model benchmark**.
