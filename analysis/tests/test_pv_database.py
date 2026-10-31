"""Analytical and browser parity guarantees using tiny typed Parquet snapshots."""

import hashlib
import json
from datetime import UTC, datetime

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from energy_analysis.pv_database import (
    export_viewer_data,
    field_profile,
    grouped_statistics,
    snapshot_overview,
)


@pytest.fixture
def snapshot(tmp_path):
    schema = pa.schema(
        [
            pa.field("country", pa.string()),
            pa.field("power", pa.float64(), metadata={"unit": "MWac"}),
            pa.field("dc", pa.float64()),
            pa.field("bifacial", pa.bool_()),
            pa.field("sources", pa.list_(pa.string())),
            pa.field("updated_at", pa.timestamp("us", tz="UTC")),
            pa.field("unknown", pa.string()),
        ]
    )
    rows = [
        {
            "country": "CHL",
            "power": 0.0,
            "dc": 1.0,
            "bifacial": False,
            "sources": ["ñ"],
            "updated_at": datetime(2026, 1, 1, tzinfo=UTC),
        },
        {"country": "CHL", "power": 10.0, "dc": None},
        {"country": "ESP", "power": None},
        {"country": None, "power": 5.0},
    ]
    manifest = {"input_sha256": "input", "schema_version": "1", "tables": {}}
    for entity, records in [("projects", rows), ("modules", [])]:
        path = tmp_path / f"{entity}.parquet"
        pq.write_table(pa.Table.from_pylist(records, schema=schema), path)
        manifest["tables"][entity] = {
            "rows": len(records),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    (tmp_path / "schema.json").write_text(
        json.dumps(
            {"fields": {name: {} for name in schema.names}, "entity_types": ["projects", "modules"]}
        )
    )
    return tmp_path


def test_field_profile_counts_zero_false_and_empty_tables(snapshot):
    profile = field_profile(snapshot / "projects.parquet")
    assert profile.loc["power", "known"] == 3
    assert profile.loc["power", "unit"] == "MWac"
    assert profile.loc["bifacial", "known"] == 1
    assert profile.loc["unknown", "coverage_pct"] == 0
    assert field_profile(snapshot / "modules.parquet")["coverage_pct"].isna().all()
    overview = snapshot_overview(snapshot)
    assert overview.loc["projects", "rows"] == 4
    assert overview.loc["modules", "columns"] == 7


def test_groups_retain_unknowns_and_do_not_mix_ac_dc(snapshot):
    ac = grouped_statistics(snapshot / "projects.parquet", "country", "power")
    dc = grouped_statistics(snapshot / "projects.parquet", "country", "dc")
    assert ac["records"].sum() == 4
    assert ac.loc["CHL", "reported_sum"] == 10
    assert ac.loc["CHL", "complete_sum"] == 10
    assert dc.loc["CHL", "reported_sum"] == 1
    assert dc.loc["CHL", "missing"] == 1
    assert dc.loc[["CHL", "ESP"], "complete_sum"].isna().all()
    assert ac.loc[["ESP"], "reported_sum"].isna().all()
    with pytest.raises(ValueError, match="numeric"):
        grouped_statistics(snapshot / "projects.parquet", "country", "bifacial")
    with pytest.raises(ValueError, match="differ"):
        grouped_statistics(snapshot / "projects.parquet", "power", "power")


def test_browser_export_retains_every_row_value_and_schema_with_checksums(snapshot):
    index = export_viewer_data(snapshot)
    assert index["tables"]["projects"]["rows"] == 4
    assert "unknown" in index["fields"]
    for entity in ("projects", "modules"):
        info = index["tables"][entity]
        raw = (snapshot / info["viewer"]).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == info["viewer_sha256"]
        payload = json.loads(raw)
        assert payload["parquet_sha256"] == info["parquet_sha256"]
        actual = [dict(zip(payload["columns"], values, strict=True)) for values in payload["rows"]]
        expected = pq.read_table(snapshot / info["parquet"]).to_pylist()
        assert len(actual) == len(expected)
        for original, browser in zip(expected, actual, strict=True):
            for key, value in original.items():
                assert browser.get(key) == (
                    value.isoformat() if isinstance(value, datetime) else value
                )
    assert export_viewer_data(snapshot) == index


def test_browser_export_rejects_corrupt_snapshot(snapshot):
    path = snapshot / "projects.parquet"
    path.write_bytes(path.read_bytes() + b"corruption")
    with pytest.raises(ValueError, match="checksum mismatch"):
        export_viewer_data(snapshot)
