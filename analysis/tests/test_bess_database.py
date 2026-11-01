"""BESS integrates with existing generic Parquet statistics and browser delivery."""

import json
from pathlib import Path

from energy_analysis.pv_database import export_viewer_data, grouped_statistics
from energy_data_retrieval.bess_catalogue import build_parquet

ROOT = Path(__file__).resolve().parents[2] / "catalogues/bess"


def test_bess_viewer_preserves_missing_power_and_conflicts(tmp_path):
    manifest = build_parquet(ROOT, tmp_path / "bess")
    index = export_viewer_data(tmp_path / "bess")
    assert index["tables"]["projects"]["rows"] == manifest["tables"]["projects"]["rows"]
    payload = json.loads((tmp_path / "bess/projects.viewer.json").read_text())
    rows = [dict(zip(payload["columns"], values, strict=True)) for values in payload["rows"]]
    edwards = next(r for r in rows if r["name"] == "Edwards & Sanborn BESS")
    assert edwards["power_capacity_mw"] is None
    assert edwards["energy_capacity_mwh"] == 3287
    assert edwards["source_urls"]
    assert any(r["quality_status"] == "needs_review" and r["conflicts_json"] for r in rows)
    power = grouped_statistics(
        tmp_path / "bess/projects.parquet", "country_code", "power_capacity_mw"
    )
    assert power.loc[["USA"], "missing"].ge(1).all()
    assert power["records"].sum() == len(rows)
