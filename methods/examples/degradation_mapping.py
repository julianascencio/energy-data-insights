"""Generate a small SYNTHETIC mapping fixture, not a calibrated PV prediction.

Run: uv run python methods/examples/degradation_mapping.py --output artifacts/degradation-input
Then use energy-degradation as documented in docs/degradation.md.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import xarray as xr

from energy_methods.degradation import DegradationParameters
from energy_methods.degradation_mapping import STRESS_UNITS


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    parameters = DegradationParameters(
        a_h=0.00004,
        a_p=0.0000008,
        a_tm=0.000001,
        e_h=0,
        e_p=0,
        e_tm=0,
        n=2,
        x=1,
        theta=1,
        a_n=1,
        calibration_id="SYNTHETIC-DEMO-NOT-A-PV-CALIBRATION",
        calibration_source="Artificial coefficients for software demonstration only",
    )
    coords = {"year": [2016, 2017, 2018], "lat": [40.0, 41.0], "lon": [-4.0, -3.0, -2.0]}
    stresses = xr.Dataset(
        attrs={
            "stress_convention": "SYNTHETIC annual inputs; no measured or reanalysis observations",
            "source": "methods/examples/degradation_mapping.py",
        }
    )
    for (name, units), value in zip(STRESS_UNITS.items(), [20, 40, 0, 50, 100, 365], strict=True):
        stresses[name] = xr.DataArray(
            np.full((3, 2, 3), value, dtype=float),
            dims=("year", "lat", "lon"),
            coords=coords,
            attrs={"units": units},
        )
    stresses.relative_humidity_percent.values[:] = np.array([[20, 40, 60], [50, 70, 90]])
    for name in STRESS_UNITS:
        stresses[name][:, 1, 2] = np.nan  # Explicit no-data cell, never zero degradation.
    args.output.mkdir(parents=True, exist_ok=True)
    stresses.to_netcdf(args.output / "annual_stresses.nc", engine="scipy")
    (args.output / "parameters.json").write_text(
        json.dumps(parameters.to_dict(), indent=2), encoding="utf-8"
    )
    print(args.output)


if __name__ == "__main__":
    main()
