"""Offline real-input smoke check and provenance rejection."""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.pvdeg_mechanisms import METRICS, analyze_manifest, analyze_weather

ROOT = Path(__file__).resolve().parents[2]


def test_real_canary_mechanisms():
    result = analyze_manifest(ROOT / "examples/analysis/pvdeg_canary_weather")
    assert len(result) == 11
    assert result.name.is_unique
    assert np.isfinite(result[list(METRICS)].to_numpy()).all()
    assert (result[list(METRICS)] >= 0).all().all()
    assert result.thermal.max() > result.thermal.min()


def test_missing_fixture_is_not_invented(tmp_path):
    (tmp_path / "wrong.csv.gz").write_bytes(b"bad")
    (tmp_path / "manifest.json").write_text(
        '{"sites": [{"file": "wrong.csv.gz", "sha256": "wrong"}]}'
    )
    with pytest.raises(ValueError, match="provenance"):
        analyze_manifest(tmp_path)


def test_incomplete_year_rejected():
    # Explicitly synthetic boundary fixture; no scientific output is asserted.
    weather = pd.DataFrame(
        {
            "temp_air": [25, 25],
            "relative_humidity": [50, 50],
            "wind_speed": [1, 1],
            "ghi": [0, 0],
            "dni": [0, 0],
            "dhi": [0, 0],
        },
        index=pd.date_range("2023-01-01", periods=2, freq="h", tz="UTC"),
    )
    with pytest.raises(ValueError, match="complete"):
        analyze_weather(weather, {})
