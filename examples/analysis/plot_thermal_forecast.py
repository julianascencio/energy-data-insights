"""
HVAC: temperature accuracy versus comfort timing
================================================

Reanalyse all 30 published T1 mornings from Antoine Galataud's Foobot experiment
(2026): `source article <https://techblog.foobot.io/ai/hvac/control/tsfm-counterfactual-thermal-dynamics.html>`_.
These are imported EnergyPlus simulations and Timestral-209M predictions, not
measured buildings or new inference. Inputs and acquisition hashes accompany
this example in ``data/thermal/thermal_provenance.json``.

A low temperature MAE can coexist with a large comfort-time error. Comfort means
21 degrees C minus 0.25 degrees C tolerance for two consecutive samples. Crossing
is interpolated and gated at the HVAC start, matching the published event data.
Missed events remain missing; they are not replaced with the forecast horizon.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

root = (
    Path(globals().get("__file__", "plot_thermal_forecast.py")).resolve().parent
    / "data"
    / "thermal"
)
scores = pd.read_csv(root / "thermal_scores.csv")
t1 = scores[scores.test == "T1"]
fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
axes[0].scatter(t1.temperature_mae_c, t1.timing_error_min.abs(), color="#167d9a")
axes[0].axhline(15, color="gray", linestyle="--", label="15-minute tolerance")
axes[0].set(xlabel="Temperature MAE (°C)", ylabel="Absolute comfort-time error (min)")
axes[0].legend()
axes[1].bar(range(len(t1)), t1.timing_error_min, color="#167d9a")
axes[1].set(xlabel="Published morning index", ylabel="Signed timing error (min)")
fig.suptitle("Published simulations: accurate temperatures do not guarantee timely comfort")
print(f"Mornings: {len(t1)}; observed timing pairs: {t1.timing_error_min.notna().sum()}")
print(f"Mean temperature MAE: {t1.temperature_mae_c.mean():.3f} °C")
print(f"Median absolute timing error: {t1.timing_error_min.abs().median():.1f} min")
print(f"Mean absolute timing error: {t1.timing_error_min.abs().mean():.1f} min")
print(f"Within ±15 minutes: {(t1.timing_error_min.abs() <= 15).sum()} / {len(t1)}")
plt.show()
