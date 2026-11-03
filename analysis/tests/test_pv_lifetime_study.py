"""Evidence/forecast separation, published cells and exported study integrity."""

import hashlib
from importlib.resources import files

import matplotlib
import numpy as np
import pytest

matplotlib.use("Agg")

from energy_analysis.pv_lifetime.study import (
    field_anchors,
    field_projections,
    horizon_summary,
    module_evidence,
    provenance,
    run_study,
    shape_scenarios,
    stress_scenarios,
    system_evidence,
)


def test_published_cells_dates_and_exclusions_are_preserved():
    frame = module_evidence()
    assert len(frame) == 32
    assert frame.stored_reference.sum() == 6
    assert frame.nominal_power_w.isna().sum() == 4
    assert (frame.exclusion_from_long_term_projection == "included").sum() == 14
    first = frame[frame.module_id == "23-P08/A/1 DETECT"].iloc[0]
    assert first.measured_cell == "PM!M6"
    assert first.retained_nameplate_fraction == pytest.approx(48.267309 / 53)
    assert first.exposure_years == 31
    assert set(frame.exposure_years.dropna()) == {16, 24, 25, 30, 31, 37}
    assert set(field_anchors().group) == {"Birg", "Moehlin", "Tiergarten SM55-HO"}
    assert list(system_evidence().plr_percent_per_year) == [
        -0.07,
        -0.56,
        -0.16,
        -0.12,
        -0.34,
        -0.18,
    ]
    for name, digest in provenance()["tables_sha256"].items():
        content = files("energy_analysis.pv_lifetime").joinpath(f"data/{name}").read_bytes()
        assert hashlib.sha256(content).hexdigest() == digest


def test_field_projections_begin_at_observation_not_fake_history():
    curves = field_projections()
    for anchor in field_anchors().itertuples():
        for model in ("linear", "exponential"):
            frame = curves[(curves.group == anchor.group) & (curves.model == model)]
            assert frame.age_years.iloc[0] == anchor.age_years
            assert frame.retained_power.iloc[0] == pytest.approx(anchor.retained_power)
            assert frame.age_years.iloc[-1] == 50
            assert np.all(np.diff(frame.retained_power) < 0)
            if model == "linear":
                assert frame.retained_power.iloc[-1] == pytest.approx(
                    1 - (1 - anchor.retained_power) * 50 / anchor.age_years
                )
            else:
                assert frame.retained_power.iloc[-1] == pytest.approx(
                    anchor.retained_power ** (50 / anchor.age_years)
                )


def test_scenarios_share_anchor_and_keep_future_damage():
    for curves in (shape_scenarios(), stress_scenarios()):
        for _, frame in curves.groupby("scenario"):
            assert frame.retained_power.iloc[0] == 1
            assert np.interp(30, frame.age_years, frame.retained_power) == pytest.approx(0.9)
            assert np.all(np.diff(frame.retained_power) <= 1e-13)
    summary = horizon_summary(shape_scenarios()).set_index("scenario")
    assert summary.loc["Linear", "power_at_50_percent"] == pytest.approx(83.333333333)
    assert np.isnan(summary.loc["Linear", "threshold_crossing_year"])
    assert summary.loc["Sigmoid B=8", "threshold_crossing_year"] == pytest.approx(
        34.1813, abs=0.001
    )


def test_offline_export_has_all_plots_tables_and_matching_hashes(tmp_path):
    manifest = run_study(tmp_path)
    assert len(list(tmp_path.glob("*.png"))) == 6
    assert len(list(tmp_path.glob("*.csv"))) == 7
    assert (tmp_path / "pv_lifetime_30_50_years.pdf").read_bytes().startswith(b"%PDF")
    for name, digest in manifest["outputs_sha256"].items():
        assert hashlib.sha256((tmp_path / name).read_bytes()).hexdigest() == digest
