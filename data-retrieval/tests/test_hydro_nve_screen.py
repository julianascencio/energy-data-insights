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
