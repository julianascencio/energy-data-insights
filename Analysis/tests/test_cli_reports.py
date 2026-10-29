"""The CLI must report frozen results without re-entering the model pipeline."""

import json
from pathlib import Path
from typing import NoReturn

import pandas as pd
import pytest

from energy_analysis.chile_fleet import cli
from energy_analysis.chile_fleet.io import fingerprint


def test_compare_and_report_cli_preserve_frozen_inputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    hourly, sites = tmp_path / "hourly.parquet", tmp_path / "sites.csv"
    pd.DataFrame(
        {
            "site_id": ["station-a", "station-a"],
            "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z"],
            "actual_mwh": [0.0, 4.0],
            "expected_final_mwh": [2.0, 4.0],
        }
    ).to_parquet(hourly, index=False)
    pd.DataFrame({"site_id": ["station-a", "empty"], "name": ["Demo A", "No data"]}).to_csv(
        sites, index=False
    )
    original = fingerprint(hourly)

    def forbidden_fit(*args: object, **kwargs: object) -> NoReturn:
        raise AssertionError("Frozen comparison/report attempted to refit a model")

    monkeypatch.setattr(cli, "run_fleet", forbidden_fit)
    output = tmp_path / "comparison"
    assert (
        cli.main(
            [
                "compare",
                "--hourly",
                str(hourly),
                "--sites",
                str(sites),
                "--start",
                "2026-01-01T00:00:00Z",
                "--end",
                "2026-01-02T00:00:00Z",
                "--reference",
                "expected_final_mwh",
                "--output",
                str(output),
                "--synthetic",
                "--reports",
            ]
        )
        == 0
    )
    capsys.readouterr()
    assert fingerprint(hourly) == original
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["data_kind"] == "synthetic"
    assert manifest["model_retrained"] is False
    assert manifest["summary"]["matched_expected_mwh"] == 6.0
    assert (output / "reports/index.html").is_file()
    before_manifest = (output / "manifest.json").read_bytes()
    reviewed = tmp_path / "reviewed-report"
    assert cli.main(["report", "--run", str(output), "--output", str(reviewed)]) == 0
    assert (reviewed / "index.html").is_file()
    assert (output / "manifest.json").read_bytes() == before_manifest
    assert fingerprint(hourly) == original

    # An accidental rerun must not delete or replace the published report.
    before_html = (reviewed / "index.html").read_bytes()
    assert cli.main(["report", "--run", str(output), "--output", str(reviewed)]) == 2
    assert (reviewed / "index.html").read_bytes() == before_html
