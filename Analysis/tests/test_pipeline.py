"""Integration checks use explicitly synthetic data, never claimed as field validation."""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.chile_fleet.config import load_config
from energy_analysis.chile_fleet.demo import create_demo
from energy_analysis.chile_fleet.io import SiteDataSource, load_sites, row_mapping
from energy_analysis.chile_fleet.pipeline import analyze_site, fit_stage, run_fleet


def test_full_synthetic_workflow_and_config_roundtrip(tmp_path: Path) -> None:
    config = create_demo(tmp_path / "demo")
    loaded = load_config(tmp_path / "demo/config.toml")
    assert loaded == config
    result = run_fleet(config)
    assert result["complete"] is True
    descriptors = result["outputs"]
    assert isinstance(descriptors, list)
    for descriptor in descriptors:
        path = config.output_path / descriptor["path"]
        assert path.is_file()
        with path.open("rb") as stream:
            assert (
                hashlib.file_digest(stream, "sha256").hexdigest()
                == descriptor["files"][0]["sha256"]
            )
    summary = result["summary"]
    assert isinstance(summary, dict)
    assert summary["registry_records"] == 3
    assert summary["comparable_records"] == 2
    assert summary["underperforming_records"] == 1
    assert summary["overperforming_records"] == 1
    assert summary["insufficient_comparison_records"] == 1
    final = pd.read_parquet(config.output_path / "hourly/site-000000.parquet")
    assert not final["iec_operating_cause_confirmed"].any()
    assert final.loc[final.timestamp >= config.event_start, "expected_heldout_mwh"].isna().all()
    assert len(list((config.output_path / "tdp").glob("*-avg.parquet"))) == 2
    with (config.output_path / "models/site-000000.json").open() as stream:
        model = json.load(stream)
    assert model["final"]["status"] == model["heldout"]["status"] == "fitted"
    assert model["final"]["qualified_dc_pr_filter_applied"] is True
    with pytest.raises(FileExistsError):
        run_fleet(config)


def test_post_cutoff_labels_do_not_change_training(tmp_path: Path) -> None:
    config = replace(create_demo(tmp_path / "demo"), fit_geometry=True, lag_hours=(-1, 0, 1))
    metadata = next(row_mapping(load_sites(config.sites_path)))
    frame = SiteDataSource(config.hourly_path).site(str(metadata["site_id"]))
    cutoff = pd.Timestamp(config.holdout_start)
    original = fit_stage(frame, metadata, config, cutoff=cutoff)
    changed = frame.copy()
    changed.loc[changed.timestamp >= cutoff, "actual_mwh"] = 1e9
    modified = fit_stage(changed, metadata, config, cutoff=cutoff)
    assert original.provenance["status"] == modified.provenance["status"] == "fitted"
    assert original.provenance == modified.provenance
    np.testing.assert_array_equal(original.expected, modified.expected)


def test_no_output_with_resource_detected_without_model(tmp_path: Path) -> None:
    config = create_demo(tmp_path / "demo")
    metadata = next(row_mapping(load_sites(config.sites_path)))
    frame = SiteDataSource(config.hourly_path).site(str(metadata["site_id"]))
    frame["actual_mwh"] = 0.0
    hourly, comparison, provenance = analyze_site(frame, metadata, replace(config, tdp=False))
    final = provenance["final"]
    assert isinstance(final, dict)
    assert final["status"] == "withheld"
    assert comparison["comparison_supported"] is False
    assert (hourly["final_status_code"] == 5).any()
    assert (hourly["final_status_code"] == 2).any()
