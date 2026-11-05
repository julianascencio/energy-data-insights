"""Offline industry-input connector validation: no live API calls."""

import json
from pathlib import Path

import pytest

from energy_data_retrieval.sources.jwpa_cost import load_offshore_cost_snapshot


def test_published_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "benchmark.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "evidence_class": "published_industry_assumption",
                "source": {
                    "primary_url": "https://www.meti.go.jp/shingikai/santeii/111.html",
                    "published_date": "2026-01-08",
                },
                "inputs": {
                    "capex_jpy_per_kw": 900_000,
                    "opex_jpy_per_kw_year": 12_300,
                    "net_capacity_factor": 0.366,
                },
            }
        ),
        encoding="utf-8",
    )
    result = load_offshore_cost_snapshot(path)
    assert result.capex_jpy_per_kw == 900_000
    assert result.net_capacity_factor == pytest.approx(0.366)


@pytest.mark.parametrize("value", ["measured", "synthetic", "missing"])
def test_reject_mislabelled_inputs(tmp_path: Path, value: str) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": 1, "evidence_class": value}))
    with pytest.raises(ValueError):
        load_offshore_cost_snapshot(path)
