"""Synthetic exact names remain candidates, even when source matches are unique."""

import json
import runpy
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/screen_hydro_nve.py"


@pytest.mark.parametrize("truncated", [False, True])
def test_screen_never_accepts_name_matches(tmp_path, monkeypatch, truncated):
    folder = tmp_path / "catalogues/hydro/records/projects"
    folder.mkdir(parents=True)
    record = dict(
        record_id="synthetic",
        country_code="NOR",
        name="Synthetic",
        external_ids_json='{"wri_gppd":"WRI1"}',
        historical_capacity_mw=10,
    )
    (folder / "a.jsonl").write_text(json.dumps(record) + "\n")
    api, gis, output = (tmp_path / n for n in ("api.json", "gis.json", "out.json"))
    api.write_text(json.dumps([{"Navn": "Synthetic", "VannKraftverkID": 1}]))
    gis.write_text(
        json.dumps(
            dict(
                exceededTransferLimit=truncated,
                features=[{"attributes": {"vannkraftverknavn": "Synthetic"}}],
            )
        )
    )
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT),
            "--api",
            str(api),
            "--gis",
            str(gis),
            "--output",
            str(output),
            "--reviewed-at",
            "2026-11-06T00:44:00Z",
        ],
    )
    if truncated:
        with pytest.raises(ValueError, match="Incomplete"):
            runpy.run_path(str(SCRIPT), run_name="__main__")
        assert not output.exists()
    else:
        runpy.run_path(str(SCRIPT), run_name="__main__")
        result = json.loads(output.read_text())
        assert result["accepted"] == 0 and result["held"] == 1
        assert result["decisions"][0]["record_id"] == "synthetic"
        original = output.read_bytes()
        runpy.run_path(str(SCRIPT), run_name="__main__")
        assert output.read_bytes() == original


def test_stable_cursor_survives_earlier_identity_acceptance(tmp_path, monkeypatch):
    folder = tmp_path / "catalogues/hydro/records/projects"
    folder.mkdir(parents=True)
    records = [
        dict(
            record_id=f"r{i}",
            country_code="NOR",
            name=f"Plant{i}",
            historical_capacity_mw=1,
            external_ids_json=json.dumps({"wri_gppd": f"WRI{i}"}),
        )
        for i in range(1, 4)
    ]
    path = folder / "a.jsonl"
    path.write_text("\n".join(map(json.dumps, records)) + "\n")
    api, gis, output = (tmp_path / n for n in ("api.json", "gis.json", "out.json"))
    api.write_text("[]")
    gis.write_text('{"features": []}')
    monkeypatch.chdir(tmp_path)
    argv = [
        str(SCRIPT),
        "--api",
        str(api),
        "--gis",
        str(gis),
        "--output",
        str(output),
        "--reviewed-at",
        "2026-11-06T01:43:00Z",
        "--after-wri-id",
        "WRI2",
    ]
    monkeypatch.setattr(sys, "argv", argv)
    runpy.run_path(str(SCRIPT), run_name="__main__")
    original = output.read_bytes()
    assert json.loads(original)["decisions"][0]["wri_id"] == "WRI3"
    assert json.loads(original)["partition"]["next_offset"] is None
    assert json.loads(original)["partition"]["next_after_wri_id"] == "WRI3"
    records[0]["external_ids_json"] = '{"wri_gppd":"WRI1", "nve":"1"}'
    path.write_text("\n".join(map(json.dumps, records)) + "\n")
    runpy.run_path(str(SCRIPT), run_name="__main__")
    assert output.read_bytes() == original
    monkeypatch.setattr(sys, "argv", [*argv, "--offset", "1"])
    with pytest.raises(SystemExit):
        runpy.run_path(str(SCRIPT), run_name="__main__")
    assert output.read_bytes() == original
