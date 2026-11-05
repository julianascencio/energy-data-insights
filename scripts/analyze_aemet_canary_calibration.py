"""Recompute the captured AEMET/ERA5 study and export degradation raster layers."""

from pathlib import Path

from energy_analysis.aemet_era5_canary import run_study

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    summary = run_study(
        root / "examples/analysis/aemet_era5_canary",
        root / "examples/analysis/degradation_parameters.json",
    )
    print(summary["ranges_percent_per_year"])
    print(summary["validation"])
