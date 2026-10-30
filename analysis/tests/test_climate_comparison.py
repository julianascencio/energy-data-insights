"""Real attributed reference subsets and the reproducible native-point comparison."""

import json
import shutil
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from energy_analysis.climate_comparison.plotting import load_study, plot_comparison
from energy_analysis.climate_comparison.prepare import _sample, digest
from energy_data_retrieval.sources.ml21.client import read_catalogue
from energy_methods.climate_zones import ClimateClusterModel, ClimateProvenance
from energy_methods.ml21 import FEATURES, PUBLISHED_CODES
from energy_methods.pvcz import classify_pvcz

DATA = Path(__file__).resolve().parents[2] / "examples/analysis"


def test_manifest_covers_exact_files_and_original_sources():
    manifest = json.loads((DATA / "climate_provenance.json").read_text())
    for name, expected in manifest["files"].items():
        assert digest(DATA / name) == expected
    assert set(manifest["sources"]) == {"jrc", "ml21", "pvcz"}
    assert all(len(source["sha256"]) == 64 for source in manifest["sources"].values())
    assert (
        manifest["metrics"]["ml21_training_sites"] + manifest["metrics"]["ml21_holdout_sites"]
        == 55418
    )
    for name in ("jrc", "ml21"):
        model = ClimateClusterModel.from_dict(
            json.loads((DATA / f"climate_{name}_model.json").read_text())
        )
        assert model.provenance.source


def test_published_pvcz_and_fixed_thresholds_agree_away_from_rounding_boundaries():
    frames, _ = load_study(DATA, "world")
    frame = frames["pvcz"]
    temperature = frame.T_equiv_rack_1p1eV.to_numpy()
    humidity = frame.specific_humidity_mean.to_numpy()
    # CSV stress rounding: avoid one last decimal around the published edges.
    safe = np.min(abs(temperature[:, None] - np.arange(14, 55, 5)), axis=1) > 0.11
    safe &= np.min(abs(humidity[:, None] - [3, 4.1, 5.9, 10.5]), axis=1) > 0.051
    result = classify_pvcz(
        temperature[safe],
        humidity[safe],
        provenance=ClimateProvenance("PVCZ CSV", "2010-2018", "0.25 degree"),
    )
    np.testing.assert_array_equal(result.class_id - 1, frame.pvcz.to_numpy()[safe])
    assert safe.sum() > 3000


def test_original_ml21_labels_and_frozen_refit_are_separate():
    frame = read_catalogue(DATA / "climate_ml21_world.csv")
    model = ClimateClusterModel.from_dict(
        json.loads((DATA / "climate_ml21_model.json").read_text())
    )
    result = model.predict(frame[list(FEATURES)].to_numpy())
    assert result.class_id.min() > 0
    assert set(result.zone).isdisjoint(set(frame.ml21_zone))
    assert set(frame.ml21_zone) == {code for code in PUBLISHED_CODES if code}
    sampled = _sample(frame, "world", 5)
    assert len(sampled) < len(frame)
    assert set(zip(sampled.lat, sampled.lon, strict=True)) <= set(
        zip(frame.lat, frame.lon, strict=True)
    )


def test_tampered_example_is_rejected(tmp_path):
    for path in DATA.glob("climate_*"):
        shutil.copyfile(path, tmp_path / path.name)
    with (tmp_path / "climate_jrc_world.csv").open("a") as stream:
        stream.write("\n")
    with pytest.raises(ValueError, match="checksum"):
        load_study(tmp_path, "world")


@pytest.mark.parametrize("region", ["world", "chile", "canary"])
def test_gallery_has_four_schemes_and_exposes_real_canary_coverage(region):
    frames, _ = load_study(DATA, region)
    if region == "canary":
        assert len(frames["ml21"]) == 2
        assert frames["pvcz"].empty
    fig = plot_comparison(DATA, region)
    assert len(fig.axes) == 8
    if region == "canary":
        assert any(
            "No source observations" in text.get_text() for ax in fig.axes for text in ax.texts
        )
    plt.close(fig)
