"""Selection edge cases and real-image abstention, not module-accuracy validation."""

import json
import runpy
import shutil
import socket
from pathlib import Path

import pandas as pd
import pytest

from energy_analysis.module_counting.chile import (
    audit_site_image,
    export_chile_audit,
    load_chile_study,
    rank_operating_solar_sites,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples/analysis/data/chile_modules"


def test_ranking_scope_missing_power_coordinates_and_ties():
    rows = [
        {
            "id": i,
            "nombre": str(i),
            "tipo_central_nombre": "Solares",
            "estado": "EN_OPERACION",
            "potencia_maxima": power,
            "latitud": None,
        }
        for i, power in enumerate([0, None, -1, float("inf"), 0.1, 0.1, 100, 0.01, 0.001])
    ]
    rows[-2]["estado"] = "EN_CONSTRUCCION"
    rows[-1]["tipo_central_nombre"] = "Hidroeléctricas"
    assert rank_operating_solar_sites(pd.DataFrame(rows)).id.tolist() == [4, 5, 6]
    with pytest.raises(ValueError, match="unique"):
        rank_operating_solar_sites(pd.DataFrame([*rows, rows[0]]))


def test_real_snapshot_extrema_and_reference_inventory():
    manifest, ranking = load_chile_study(DATA)
    assert len(ranking) == 757
    assert ranking.iloc[0].id == 2082 and ranking.iloc[-1].id == 2010
    assert (ranking.potencia_maxima == ranking.iloc[0].potencia_maxima).sum() == 1
    assert (ranking.potencia_maxima == ranking.iloc[-1].potencia_maxima).sum() == 1
    reference = manifest["sites"]["ceme1"]["reported_inventory"]
    assert sum(g["modules"] for g in reference["module_groups"]) == 882720
    assert reference["strings"] * reference["modules_per_string"] == 882720
    assert manifest["sites"]["concon"]["reported_inventory"]["modules"] is None


def test_real_images_abstain_and_export_null_not_zero(tmp_path):
    large = audit_site_image(DATA, "ceme1")
    small = audit_site_image(DATA, "concon")
    assert large["status"] == "insufficient_source_sampling"
    assert large["result"] is None  # Never mistake wide strips for modules.
    assert small["status"] == "unresolved_grid"
    assert small["result"] is not None  # Actual Icor detector attempted.
    assert large["image_candidate_count"] is small["image_candidate_count"] is None
    exported = export_chile_audit(DATA, tmp_path / "exports")
    summary = json.loads((exported / "count_audit.json").read_text())
    assert all(a["whole_plant_image_count"] is None for a in summary["attempts"])
    assert not list(exported.glob("*image_candidates.csv"))
    with pytest.raises(FileExistsError):
        export_chile_audit(DATA, exported)


def test_source_tampering_and_ambiguous_export_extent_fail(tmp_path):
    shutil.copytree(DATA, tmp_path / "data")
    data = tmp_path / "data"
    image = data / "chile_concon.png"
    original = image.read_bytes()
    image.write_bytes(original + b"tampered")
    with pytest.raises(ValueError, match="checksum"):
        audit_site_image(data, "concon")
    image.write_bytes(original)
    path = data / "chile_module_study.json"
    manifest = json.loads(path.read_text())
    manifest["sites"]["concon"]["detail_capture"]["bbox_wgs84"][0] -= 0.01
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="extent"):
        audit_site_image(data, "concon")


@pytest.mark.parametrize(
    "filename",
    [
        "plot_chile_largest_module_counting.py",
        "plot_chile_smallest_module_counting.py",
    ],
)
def test_gallery_runs_offline(filename, monkeypatch):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def forbidden(*args, **kwargs):
        raise AssertionError("Gallery must run offline")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(plt, "show", lambda: None)
    try:
        variables = runpy.run_path(str(ROOT / "examples/analysis" / filename))
        assert variables["audit"]["whole_plant_image_count"] is None
        assert len(variables["fig"].axes) == 3
    finally:
        plt.close("all")
