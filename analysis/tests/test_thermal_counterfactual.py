"""Check scientific pairing and committed public-data numerical reproduction."""

from pathlib import Path

import pandas as pd
import pytest

from energy_analysis.thermal_counterfactual import score_panels, sensitivity_ratios
from energy_data_retrieval.foobot import ThermalPanel


def panel(test, offset, values):
    return ThermalPanel(
        "2024-01-01",
        test,
        offset,
        20.5,
        (0.0, 15.0, 30.0, 45.0),
        (20.0, 21.0, 21.0, 21.0),
        values,
        values,
        values,
        (21.0,) * 4,
        (1.0,) * 4,
    )


def test_uses_t2_baseline_not_t1():
    rows = score_panels(
        (
            panel("T1", 0, (19.0, 19.0, 21.0, 21.0)),
            panel("T2", 0, (20.0, 21.0, 21.0, 21.0)),
            panel("T2", 15, (19.0, 20.0, 21.0, 21.0)),
        )
    )
    assert rows.iloc[2].shift_error_min == 7.5
    with pytest.raises(ValueError, match="baseline"):
        score_panels((panel("T2", 15, (19.0, 20.0, 21.0, 21.0)),))


def test_published_summary_and_censored_counts():
    root = Path(__file__).resolve().parents[2] / "examples/analysis/data/thermal"
    scores = pd.read_csv(root / "thermal_scores.csv")
    a = scores[scores.test == "T1"]
    b = scores[(scores.test == "T2") & (scores.offset_min != 0)]
    assert len(scores) == 180
    assert a.temperature_mae_c.mean() == pytest.approx(0.552, abs=0.0005)
    assert a.timing_error_min.abs().mean() == pytest.approx(107.8, abs=0.05)
    assert b.shift_error_min.abs().mean() == pytest.approx(24.4, abs=0.05)
    assert b.shift_error_min.isna().sum() == 3
    assert sensitivity_ratios(scores).sensitivity_ratio.median() == pytest.approx(
        0.230953, abs=0.000001
    )
