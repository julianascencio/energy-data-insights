"""Frozen-reference comparison must leave supplied predictions unchanged."""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from energy_analysis.chile_fleet.io import fingerprint, write_fleet_csv
from energy_analysis.chile_fleet.reference import compare_references


def test_frozen_comparison_retains_reference_and_empty_site(tmp_path: Path) -> None:
    hourly, sites, output = (tmp_path / n for n in ("hourly.parquet", "sites.csv", "result"))
    pd.DataFrame(
        {
            "site_id": ["a", "a"],
            "timestamp": ["2026-01-01T00:00:00Z", "2026-01-01T01:00:00Z"],
            "actual_mwh": [0, 4],
            "expected_final_mwh": [2, 4],
        }
    ).to_parquet(hourly)
    pd.DataFrame({"site_id": ["a", "empty"]}).to_csv(sites, index=False)
    before = fingerprint(hourly)
    result = compare_references(
        hourly,
        sites,
        output,
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
        reference="expected_final_mwh",
    )
    assert result["model_retrained"] is False
    assert result["expected_values_modified"] is False
    assert fingerprint(hourly) == before
    summary = result["summary"]
    assert isinstance(summary, dict)
    assert summary["registry_records"] == 2
    assert summary["comparable_records"] == 1
    assert summary["matched_expected_mwh"] == 6


def test_output_cannot_contaminate_input_dataset(tmp_path: Path) -> None:
    source = tmp_path / "dataset"
    source.mkdir()
    with pytest.raises(ValueError, match="outside"):
        compare_references(
            source,
            tmp_path / "sites.csv",
            source / "result",
            start=datetime(2026, 1, 1, tzinfo=UTC),
            end=datetime(2026, 1, 2, tzinfo=UTC),
        )


def test_csv_formula_labels_escaped_but_numeric_sign_preserved(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "site_id": ["+bad", "safe"],
            "name": ["=1+1", "\tlabel"],
            "matched_deviation_mwh": [-2, -3],
        }
    )
    target = tmp_path / "fleet.csv"
    write_fleet_csv(frame, target)
    output = pd.read_csv(target)
    assert output.site_id.iloc[0] == "'+bad"
    assert output.name.iloc[0] == "'=1+1"
    assert output.name.iloc[1] == "'\tlabel"
    assert output.matched_deviation_mwh.iloc[0] == -2
    assert frame.site_id.iloc[0] == "+bad"
