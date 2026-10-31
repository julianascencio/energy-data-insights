"""Reproduce archived rates from real stress fixtures, preserving missing coverage."""

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from energy_analysis.degradation.gallery import load_degradation_example, plot_degradation_maps
from energy_methods.degradation_mapping import STRESS_UNITS

DATA = Path(__file__).resolve().parents[2] / "examples/analysis"


def test_real_stresses_recompute_saved_rates_and_missing_cells():
    annual, result, metadata = load_degradation_example(DATA)
    assert annual.year.values.tolist() == [2016, 2017, 2018]
    assert int(result.total_rate.notnull().sum()) == metadata["valid_cells"] == 63
    assert int(result.land_mask.sum()) == metadata["land_cells"] == 71
    assert int(((result.land_mask == 1) & result.total_rate.isnull()).sum()) == 8
    assert np.isnan(result.total_rate.where(result.land_mask == 0)).all()
    assert float(result.total_rate.min()) == pytest.approx(0.018881074950902858)
    assert float(result.total_rate.max()) == pytest.approx(1.1012662044468118)
    assert all(annual[name].attrs["units"] == units for name, units in STRESS_UNITS.items())
    assert json.loads(result.attrs["calibration"])["a_n"] == 1.0


def test_fixture_tampering_is_rejected(tmp_path):
    for path in DATA.glob("degradation_*"):
        shutil.copyfile(path, tmp_path / path.name)
    with (tmp_path / "degradation_stresses.csv").open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="checksum"):
        load_degradation_example(tmp_path)


@pytest.mark.parametrize("categorical", [False, True])
def test_rate_and_class_maps_use_recorded_period_and_no_data(categorical):
    _, rates, _ = load_degradation_example(DATA)
    fig = plot_degradation_maps(
        rates, DATA / "climate_world_boundaries.geojson", categorical=categorical
    )
    assert len(fig.axes) == (2 if categorical else 8)
    assert any("63/71" in text.get_text() for text in fig.texts)
    assert any("gray = missing" in text.get_text() for text in fig.texts)
    plt.close(fig)
