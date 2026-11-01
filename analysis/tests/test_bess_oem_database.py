"""Browser projections preserve every product and source-qualified rating."""

import json
from pathlib import Path

from energy_analysis.pv_database import export_viewer_data, grouped_statistics
from energy_data_retrieval.bess_oem_catalogue import build_parquet

ROOT = Path(__file__).resolve().parents[2] / "catalogues/bess_oem"


def test_oem_browser_projection_keeps_families_and_apparent_power_separate(tmp_path):
    snapshot = tmp_path / "bess_oem"
    manifest = build_parquet(ROOT, snapshot)
    index = export_viewer_data(snapshot)
    assert index["tables"]["systems"]["rows"] == manifest["tables"]["systems"]["rows"]
    payload = json.loads((snapshot / "systems.viewer.json").read_text())
    rows = [dict(zip(payload["columns"], values, strict=True)) for values in payload["rows"]]
    assert all(r["source_urls"] for r in rows)
    assert all(r["energy_capacity_mwh"] is None for r in rows if r["record_scope"] == "family")
    nidec = next(r for r in rows if r["manufacturer"] == "Nidec Conversion")
    assert nidec["power_capacity_mw"] is None
    assert nidec["apparent_power_mva"] > 0
    profile = grouped_statistics(
        snapshot / "systems.parquet", "manufacturer", "energy_capacity_mwh"
    )
    assert profile["records"].sum() == len(rows)
