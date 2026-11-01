"""Reports must preserve accounting, provenance, gaps and safe document boundaries."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from energy_analysis.chile_fleet.io import fingerprint, write_json
from energy_analysis.chile_fleet.reference import compare_references
from energy_analysis.chile_fleet.reports import generate_reports
from energy_analysis.chile_fleet.reports.generator import RUN_SCHEMA
from energy_analysis.chile_fleet.reports.rendering import energy_series


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _comparison(tmp_path: Path) -> Path:
    site_id = '../../<script>alert("x")</script>'
    pd.DataFrame(
        {
            "site_id": [site_id, site_id, "missing"],
            "timestamp": [
                "2026-01-01T00:00:00Z",
                "2026-01-01T01:00:00Z",
                "2026-01-01T00:00:00Z",
            ],
            "actual_mwh": [0.0, 4.0, np.nan],
            "expected_mwh": [2.0, 4.0, 5.0],
        }
    ).to_parquet(tmp_path / "hourly.parquet", index=False)
    pd.DataFrame(
        {
            "site_id": [site_id, "missing", "empty"],
            "name": ['Solar <img src=x onerror="alert(1)">', "Missing", "Empty registry row"],
            "region": ["Example", "Example", "Example"],
        }
    ).to_csv(tmp_path / "sites.csv", index=False)
    output = tmp_path / "result"
    compare_references(
        tmp_path / "hourly.parquet",
        tmp_path / "sites.csv",
        output,
        start=datetime(2026, 1, 1, tzinfo=UTC),
        end=datetime(2026, 1, 2, tzinfo=UTC),
    )
    return output


def _run(tmp_path: Path) -> Path:
    output = _comparison(tmp_path)
    manifest = json.loads((output / "manifest.json").read_text())
    manifest["schema"] = RUN_SCHEMA
    manifest["data_kind"] = "synthetic"
    manifest["configuration"] = {
        "report_start": "2026-01-01T00:00:00Z",
        "report_end": "2026-01-02T00:00:00Z",
        "minimum_reference_coverage": 0.8,
        "relative_tolerance": 0.2,
        "algorithm": "physics",
        "reference": "final",
    }
    manifest["site_outputs"] = []
    (output / "hourly").mkdir()
    (output / "models").mkdir()
    fleet = pd.read_parquet(output / "fleet.parquet")
    for index, site_id in enumerate(fleet["site_id"]):
        key = f"site-{index:06d}"
        manifest["site_outputs"].append({"site_id": site_id, "key": key})
        pd.DataFrame(
            {
                "site_id": [site_id] * 3,
                "timestamp": pd.to_datetime(
                    ["2025-12-31T23:00Z", "2026-01-01T00:00Z", "2026-01-01T01:00Z"],
                    utc=True,
                ),
                "actual_mwh": [800.0, 0.0, 4.0],
                "expected_mwh": [900.0, 2.0, 4.0],
                "final_status": [
                    "outside_report",
                    "no_generation_with_resource",
                    "generation_model_consistent",
                ],
            }
        ).to_parquet(output / "hourly" / f"{key}.parquet", index=False)
        write_json(
            output / "models" / f"{key}.json",
            {
                "site_id": site_id,
                "final": {"status": "fitted"},
                "heldout": {"status": "fitted"},
                "heldout_metrics": {
                    "matched_hours": 10,
                    "score_pct": 81.5,
                    "mae_mwh": 0.123,
                    "rmse_mwh": 0.234,
                    "bias_pct": -1.25,
                },
            },
        )
    manifest["outputs"] = [
        {"path": path.relative_to(output).as_posix(), **fingerprint(path)}
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name != "manifest.json"
    ]
    write_json(output / "manifest.json", manifest)
    return output


def test_frozen_report_preserves_summary_sources_and_safely_escapes_labels(tmp_path: Path) -> None:
    source = _comparison(tmp_path)
    before = {path: _sha(path) for path in source.iterdir() if path.is_file()}
    result = generate_reports(source, title='<script>alert("title")</script>')
    output = source / "reports"
    assert result["complete"] is True
    assert result["model_retrained"] is False
    assert result["expected_values_modified"] is False
    assert result["primary_reference"] == "ascencio_vasquez_2021_thesis"
    assert result["summary"] == json.loads((source / "summary.json").read_text())
    data = json.loads((output / "data.json").read_text())
    assert data["summary"]["matched_actual_mwh"] == 4
    assert data["summary"]["matched_expected_mwh"] == 6
    assert data["summary"]["registry_records"] == 3
    assert data["summary"]["comparable_records"] == 1
    assert len(data["sites"]) == 3
    assert {path: _sha(path) for path in before} == before
    document = (output / "index.html").read_text()
    assert '<script>alert("title")</script>' not in document
    assert '<img src=x onerror="alert(1)">' not in document
    assert "&lt;img" in document
    assert "site-search" in document and "group-filter" in document
    assert "<script src=" not in document
    # Bound the report UI independently of the deliberately complete, growing bibliography.
    before_references, marker, remainder = document.partition('<ol class="references">')
    references_html, closing, after_references = remainder.partition("</ol>")
    assert marker and closing and references_html
    assert len(before_references + after_references) < 150_000
    assert all(path.name.startswith("site-") for path in (output / "sites").iterdir())
    first_site = (output / "sites/site-000000.html").read_text()
    assert "No saved hourly operating screens" in first_site
    assert "Model fit metadata was not part" in first_site
    assert "DRAFT" in (output / "website_article.md").read_text()
    assert "not been posted" in (output / "linkedin_post.md").read_text()
    references = json.loads((output / "references.json").read_text())
    assert references[0]["id"] == "ascencio_vasquez_2021_thesis"
    outputs = result["outputs"]
    assert isinstance(outputs, list)
    for entry in outputs:
        assert isinstance(entry, dict)
        assert _sha(output / entry["path"]) == entry["sha256"]
    with pytest.raises(FileExistsError):
        generate_reports(source)


def test_run_report_keeps_synthetic_warning_and_uses_report_period(tmp_path: Path) -> None:
    source = _run(tmp_path)
    result = generate_reports(source, synthetic=False)
    assert result["synthetic"] is True
    assert result["source_hashes_verified"]
    page = (source / "reports/sites/site-000000.html").read_text()
    assert "SYNTHETIC DATA" in page
    assert "outside report" not in page
    assert "no generation with resource" in page
    assert "0.123" in page and "0.234" in page
    assert "operating cause unconfirmed" in page
    for name in ("website_article.md", "linkedin_post.md"):
        assert "SYNTHETIC DATA" in (source / "reports" / name).read_text()


def test_source_hash_changes_are_refused_before_publication(tmp_path: Path) -> None:
    source = _run(tmp_path)
    path = source / "models/site-000000.json"
    path.write_text(path.read_text() + " ")
    with pytest.raises(ValueError, match="hash does not match"):
        generate_reports(source)
    assert not (source / "reports").exists()
    assert not list(source.glob(".reports-*"))


def test_stale_summary_and_unsafe_manifest_mapping_are_refused(tmp_path: Path) -> None:
    source = _comparison(tmp_path)
    summary = json.loads((source / "summary.json").read_text())
    summary["matched_actual_mwh"] = 4000
    write_json(source / "summary.json", summary)
    with pytest.raises(ValueError, match="summary disagrees"):
        generate_reports(source)
    assert not (source / "reports").exists()
    other = tmp_path / "other"
    other.mkdir()
    run = _run(other)
    manifest = json.loads((run / "manifest.json").read_text())
    manifest["site_outputs"][0]["key"] = "../../outside"
    write_json(run / "manifest.json", manifest)
    with pytest.raises(ValueError, match="Unsafe"):
        generate_reports(run)


@pytest.mark.parametrize(
    "destination", ["hourly/new-report", "models/new-report", "tdp/new-report"]
)
def test_reports_cannot_contaminate_source_data_folders(tmp_path: Path, destination: str) -> None:
    source = _comparison(tmp_path)
    with pytest.raises(ValueError, match="contaminate"):
        generate_reports(source, source / destination)


def test_compact_charts_preserve_matched_energy_and_all_missing_days() -> None:
    hours = pd.date_range("2025-01-01", periods=24 * 800, freq="h", tz="UTC")
    frame = pd.DataFrame({"timestamp": hours, "actual_mwh": 2.0, "expected_mwh": 3.0})
    frame.loc[: 24 * 31 - 1, "actual_mwh"] = np.nan
    frame.loc[24 * 31, "actual_mwh"] = 0.0
    frame.loc[24 * 32, "actual_mwh"] = -1.0
    original = frame.copy()
    series, granularity = energy_series(frame)
    paired = frame.actual_mwh.ge(0) & frame.expected_mwh.ge(0)
    assert granularity == "monthly"
    assert len(series) < 30
    assert series.actual_mwh.sum() == frame.loc[paired, "actual_mwh"].sum()
    assert series.expected_mwh.sum() == frame.loc[paired, "expected_mwh"].sum()
    assert series.iloc[0].isna().all()
    pd.testing.assert_frame_equal(frame, original)
