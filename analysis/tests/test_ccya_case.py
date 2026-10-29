"""Applied-study accounting, provenance and input-boundary integration checks."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.ccya_case import reports
from energy_analysis.ccya_case.cli import main
from energy_analysis.ccya_case.config import load_config
from energy_analysis.ccya_case.demo import create_demo
from energy_analysis.ccya_case.pipeline import run_case
from energy_methods.ccya import YIELD_COMPONENTS


@pytest.fixture(scope="module")
def completed(tmp_path_factory):
    root = tmp_path_factory.mktemp("ccya") / "demo"
    assert main(["demo", "--output", str(root)]) == 0
    return root


def test_complete_study_and_accounting(completed):
    root = completed / "results"
    manifest = json.loads((root / "manifest.json").read_text())
    summary = pd.read_csv(root / "summary.csv")
    assert manifest["complete"] is True
    assert manifest["data_kind"] == "synthetic"
    assert manifest["thesis"]["numerical_reproduction"] is False
    assert len(manifest["inputs"]) == 15
    assert summary.shape[0] == 7 * 4 * 2
    assert set(summary["calendar_year"]) == {2044, 2069}
    assert summary["data_kind"].eq("synthetic").all()
    assert len(list((root / "scenarios").glob("*/rate-*/annual.csv"))) == 28

    measured = pd.read_csv(root / "inputs/measured.csv")
    years = measured["month"].str[:4]
    quantiles = np.quantile(measured.groupby(years)["dc_yield_kwh_kwp"].sum(), [0.1, 0.5, 0.9])
    for scenario in manifest["configuration"]["scenarios"]:
        for number, rate in enumerate(manifest["configuration"]["degradation_rates"]):
            directory = root / "scenarios" / scenario["id"] / f"rate-{number:02d}"
            monthly = pd.read_csv(directory / "monthly.csv")
            annual = pd.read_csv(directory / "annual.csv")
            assert len(monthly) == 600 and len(annual) == 50
            np.testing.assert_allclose(
                monthly["combined_kwh_kwp"],
                monthly["irradiance_kwh_kwp"]
                * monthly["temperature_factor"]
                * monthly["power_factor"],
            )
            np.testing.assert_allclose(
                monthly["power_factor"], 1 - rate * np.repeat(np.arange(50), 12)
            )
            for component in YIELD_COMPONENTS:
                values = monthly[f"{component}_kwh_kwp"].to_numpy().reshape(50, 12).sum(axis=1)
                np.testing.assert_allclose(annual[f"{component}_kwh_kwp"], values)
                for horizon in (25, 50):
                    rows = summary.loc[
                        (summary["scenario"] == scenario["id"])
                        & (summary["degradation_pct_year"] == 100 * rate)
                        & (summary["operating_year"] == horizon)
                    ]
                    assert len(rows) == 1
                    for q, percentile in zip(quantiles, ("p10", "p50", "p90"), strict=True):
                        expected = 100 * (values[:horizon].sum() / (q * horizon) - 1)
                        assert rows.iloc[0][f"{component}_gain_{percentile}_pct"] == pytest.approx(
                            expected
                        )


def test_report_is_self_contained_and_hashes_match(completed):
    root = completed / "results"
    manifest = json.loads((root / "manifest.json").read_text())
    report = (root / "reports/index.html").read_text()
    assert report.count('src="data:image/png;base64,') == 7
    assert "SYNTHETIC DEMONSTRATION" in report
    assert "not CMIP6/SSP projections" in report
    assert 'src="https://' not in report
    assert "ascencio" in (root / "references.bib").read_text().lower()
    assert len(list((root / "reports/figures").glob("*.svg"))) == 7
    for entry in manifest["inputs"] + manifest["outputs"]:
        raw = (root / entry["path"]).read_bytes()
        assert len(raw) == entry["bytes"]
        assert hashlib.sha256(raw).hexdigest() == entry["sha256"]


def test_existing_outputs_are_preserved(completed):
    config = load_config(completed / "case.toml")
    before = (config.output_path / "manifest.json").read_bytes()
    with pytest.raises(FileExistsError):
        run_case(config)
    with pytest.raises(FileExistsError):
        create_demo(completed)
    assert (config.output_path / "manifest.json").read_bytes() == before


def test_seed_reproduces_input_bytes(tmp_path):
    create_demo(tmp_path / "one", seed=11)
    create_demo(tmp_path / "two", seed=11)
    for first in (tmp_path / "one/inputs").glob("*.csv"):
        assert first.read_bytes() == (tmp_path / "two/inputs" / first.name).read_bytes()


def test_cannot_relabel_synthetic_as_observations(tmp_path):
    config = load_config(create_demo(tmp_path / "demo"))
    with pytest.raises(ValueError, match="data_kind must be 'observations'"):
        run_case(replace(config, data_kind="observed_and_projected"))
    assert not config.output_path.exists()


@pytest.mark.parametrize("fault", ["gap", "duplicate", "calendar", "nonfinite", "label"])
def test_invalid_inputs_never_publish_partial_results(tmp_path, fault):
    config = load_config(create_demo(tmp_path / "demo"))
    path = config.scenarios[0].projection_path
    future = pd.read_csv(path)
    if fault == "gap":
        future = future.drop(index=10)
    elif fault == "duplicate":
        future.loc[1, "month"] = future.loc[0, "month"]
    elif fault == "calendar":
        future["days"] = 30
    elif fault == "nonfinite":
        future.loc[0, "ghi_wm2"] = np.inf
    else:
        future["data_kind"] = "climate_model"
    future.to_csv(path, index=False)
    with pytest.raises(ValueError):
        run_case(config)
    assert not config.output_path.exists()
    assert not list(config.output_path.parent.glob(".results-*"))


def test_shared_projection_horizon_required(tmp_path):
    config = load_config(create_demo(tmp_path / "demo"))
    path = config.scenarios[1].projection_path
    pd.read_csv(path).iloc[:-12].to_csv(path, index=False)
    with pytest.raises(ValueError, match="same projection horizon"):
        run_case(config)
    assert not config.output_path.exists()


def test_report_failure_is_atomic(tmp_path, monkeypatch):
    config = load_config(create_demo(tmp_path / "demo"))
    config = replace(config, scenarios=config.scenarios[:1], degradation_rates=(0.005,))

    def fail(*args, **kwargs):
        raise OSError("Cannot write report")

    monkeypatch.setattr(reports, "generate_report", fail)
    with pytest.raises(OSError, match="Cannot write report"):
        run_case(config)
    assert not config.output_path.exists()
    assert not list(config.output_path.parent.glob(".results-*"))


def test_horizon_must_cover_requested_comparisons(tmp_path):
    config = load_config(create_demo(tmp_path / "demo"))
    with pytest.raises(ValueError, match="exceeds the projection horizon"):
        run_case(replace(config, report_years=(51,)))


@pytest.mark.parametrize(
    "settings",
    [
        {"degradation_rates": (0.005, 0.005)},
        {"plot_degradation_rate": 0.02},
        {"report_years": (True,)},
        {"report_years": (0,)},
        {"degradation_rates": (float("nan"),)},
    ],
)
def test_configuration_rejects_ambiguous_settings(tmp_path, settings):
    config = load_config(create_demo(tmp_path / "demo"))
    with pytest.raises(ValueError):
        replace(config, **settings)


def test_toml_typo_and_unsafe_scenario_id_rejected(tmp_path):
    path = create_demo(tmp_path / "demo")
    text = path.read_text().replace("report_years =", "report_year =")
    path.write_text(text)
    with pytest.raises(ValueError, match="Unknown"):
        load_config(path)
    path.write_text(
        text.replace("report_year =", "report_years =").replace(
            'id = "synthetic-path-1"', 'id = "../outside"'
        )
    )
    with pytest.raises(ValueError, match="Scenario id"):
        load_config(path)


def test_real_data_template_loads():
    path = Path(__file__).parents[1] / "examples/ccya/real-data.toml"
    config = load_config(path)
    assert config.data_kind == "observed_and_projected"
    assert config.report_years == (25, 50)
