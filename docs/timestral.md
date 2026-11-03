# Mistral Timestral forecasting connector

`energy_methods.timestral.TimestralConnector` connects energy time series to
Mistral AI's official local Timestral inference package. It supports joint
multivariate forecasts, independent series batches, missing observations,
numeric/categorical past and known-future covariates, and quantile outputs.
It uses the official Python model interface, with no Mistral API key.

The [runnable gallery example](https://julianascencio.github.io/energy-data-insights/auto_examples/connectors/plot_timestral_forecast.html)
predicts one day of California ISO solar and wind generation from six preceding
days. The default example **replays captured real Timestral-5M predictions** and
recalculates plots/metrics. It does not run the neural model during docs builds.
Live inference is an explicit alternative, with no fallback to synthetic values.

## Install and run

From the repository root, Python 3.12 or 3.13:

```bash
uv sync --locked --all-packages --group docs
uv run --no-sync python examples/connectors/plot_timestral_forecast.py
```

For an extracted gallery ZIP, install the repository packages first, then run
`uv run --no-sync python /path/to/extracted/plot_timestral_forecast.py` from the
repository root. Keep the ZIP's `data/` directory beside the script.

To run the neural model, install the optional official implementation. The
separate install avoids adding PyTorch and Git dependencies to the core wheels
or the ordinary documentation environment. On CPU, installing the CPU wheel
first avoids unnecessary GPU libraries:

```bash
uv pip install --python .venv/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python .venv/bin/python 'git+https://github.com/mistralai/timestral.git@a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff'
ENERGY_TIMESTRAL_LIVE=1 uv run --no-sync python examples/connectors/plot_timestral_forecast.py
```

These shell examples use POSIX environment-variable syntax. For GPU use, install
the appropriate PyTorch distribution for your system and set
`ENERGY_TIMESTRAL_DEVICE=cuda`. The first live run downloads the checkpoint
from Hugging Face. Set `ENERGY_TIMESTRAL_LOCAL_ONLY=1` to require an existing
local cache. The offline replay needs neither PyTorch nor Timestral.
Run with `--no-sync` after installing optional packages: a normal workspace
sync can remove packages that are not in its lockfile.

## Use the connector

```python
import numpy as np
from energy_methods.timestral import TimestralConnector

# Illustrative data only; replace with consecutive observations in one unit.
history = np.arange(144, dtype=float)[None, None, :]  # (series, targets, time)
connector = TimestralConnector(
    "mistralai/Timestral-5M",
    revision="bdd20cfc15a3fea0e4cb5ccef37f8d3ca7aa335f",
    device="cpu",
)
forecast = connector.forecast(history, prediction_length=24)
print(forecast.median.shape)  # (1, 1, 24)
print(forecast.quantile(0.1).shape)  # (1, 1, 24)
print(forecast.quantiles.shape)  # (1, 1, 24, 21)
```

| Input | Shape / interpretation |
| --- | --- |
| `context` | `(T,)`, `(B, T)` for independent univariate series, or `(B, V, T)` for joint targets |
| `observation_mask` | Boolean array with exactly the original context shape; false means missing |
| `past_covariates` | `(B, C, T)`; only known over history |
| `known_covariates` | `(B, C, T + H)`; known before prediction for the entire horizon |
| Categorical variants | Same shapes, with numeric category codes; NaN marks missing |
| Output | `(B, V, H, Q)` CPU NumPy values, in the original input unit |

`NaN` is preserved as missing; infinity, empty/all-missing retained targets,
misaligned shapes and invalid forecast outputs are rejected before use.
Inputs must be regularly sampled. This array connector does not infer frequency,
timestamps, timezone or units. Reindex to a regular grid with explicit missing
values before calling it; never drop a missing hour and close the time gap.
The gallery checks consecutive UTC hour-ending timestamps.

Use `(1, 2, T)` for jointly forecast solar and wind; `(2, T)` instead means two
independent series. Numeric inputs are copied. History beyond `max_context`
(default 32,768) is trimmed together with masks and covariates, retaining all
future covariate values. Calendar variables are safe known-future inputs;
weather should come from forecasts available at the historical issue time.

The connector caches its loaded model across calls. Choose other official model
IDs (`Timestral-28M`, `Timestral-123M`, `Timestral-209M`) and their corresponding
checkpoint revisions, or supply a local checkpoint directory. Revisions are
**model-specific**. Model/installation errors propagate rather than silently
changing the forecast method.

## Input, method and analysis

- **Input:** the existing 168-hour EIA-930 CISO capture, with its original source
  URL, retrieval time and SHA-256. Values are hourly net energy in MWh; negative
  nighttime solar net generation is retained. This is system data, not SCADA
  from an identifiable PV or wind farm.
- **Method:** the official pretrained Timestral-5M model, CPU, 144-hour context,
  24-hour horizon, joint SUN/WND targets, UTC-hour sine/cosine covariates, upstream
  symmetric averaging and conditional nonnegative clipping defaults. No fitting
  or calibration on the holdout. Future observations are used only for scoring.
- **Analysis:** all 24 hours for all models; MAE, RMSE and WAPE (absolute errors
  divided by the sum of absolute actual energy), compared with the previous
  day's profile and the last observation repeated. P10-P90 coverage is reported
  only for Timestral. Median forecasts are not expected-energy forecasts.

One historical day does not establish general superiority or operational
accuracy. Possible overlap with pretraining data is unknown. Model intervals
are uncalibrated here. Test multiple issue dates, seasons and sites, with
real forecast-time inputs and operational baselines before drawing conclusions.

## Reproduce the saved inference

After the optional installation above:

```bash
uv run --no-sync python scripts/prepare_timestral_example.py \
  --revision bdd20cfc15a3fea0e4cb5ccef37f8d3ca7aa335f
```

This explicitly writes the example's forecast and provenance JSON files. Add
`--local-files-only` for cache-only operation. The manifest records checkpoint
file hashes, exact model revision, reference source revision, installed package
versions, input/output hashes, device, seed, timestamps and forecast settings.
CPU inference uses one PyTorch thread and deterministic algorithms; numerical
differences across dependency/platform versions can still occur.

## Official sources and licences

- [Mistral Timestral inference code and interface](https://github.com/mistralai/timestral/tree/a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff)
- [Mistral Timestral-5M documentation](https://docs.mistral.ai/models/timestral-1-0-5m)
- [Pinned Timestral-5M checkpoint](https://huggingface.co/mistralai/Timestral-5M/tree/bdd20cfc15a3fea0e4cb5ccef37f8d3ca7aa335f)
- [Checkpoint licence](https://huggingface.co/mistralai/Timestral-5M/blob/bdd20cfc15a3fea0e4cb5ccef37f8d3ca7aa335f/LICENSE)

Upstream inference code uses Apache-2.0; model weights use a separate Modified
MIT licence. No model weights are redistributed in this repository. The EIA
capture retains its existing provenance and attribution.
