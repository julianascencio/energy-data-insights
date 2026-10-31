"""Real-image reproducibility and offline export checks; not count-accuracy validation."""

import json
import runpy
import socket
from pathlib import Path

import pandas as pd
import pytest

from energy_analysis.module_counting import count_rendered_site
from energy_analysis.module_counting.reports import export_counting_study

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "examples/connectors/data"


def test_real_photo_count_and_complete_exports(tmp_path):
    site = json.loads((DATA / "candelaria_site.json").read_text())
    study = count_rendered_site(DATA / "candelaria_pnoa.png", site["footprint"])
    assert len(study.result.tables) == 7
    # These are algorithm regression results, NOT independently labelled truth.
    assert study.result.estimated_modules == 3030
    assert study.result.regular_candidates == 2946 and study.result.review_candidates == 84
    assert len(study.result.cells) == 3036
    assert study.source_metadata["native_resolution_m"] is None
    exported = export_counting_study(study, tmp_path / "count")
    frame = pd.read_csv(exported / "module_candidates.csv")
    features = json.loads((exported / "module_candidates.geojson").read_text())["features"]
    summary = json.loads((exported / "count_summary.json").read_text())
    assert len(frame) == len(features) == 3036
    assert frame.id.nunique() == 3036
    assert (frame.status != "excluded").sum() == summary["estimated_modules"] == 3030
    assert sum(f["properties"]["status"] == "excluded" for f in features) == 6
    assert summary["source_metadata"]["sha256"] == study.source_metadata["sha256"]
    with pytest.raises(FileExistsError):
        export_counting_study(study, exported)


def test_receipt_tamper_axis_order_and_scope_validation(tmp_path):
    image = tmp_path / "sample.png"
    image.write_bytes((DATA / "candelaria_pnoa.png").read_bytes())
    receipt = image.with_suffix(".png.meta.json")
    metadata = json.loads((DATA / "candelaria_pnoa.png.meta.json").read_text())
    site = json.loads((DATA / "candelaria_site.json").read_text())["footprint"]
    for field, value, match in (
        ("SRS", "EPSG:3857", "WMS"),
        ("VERSION", "1.3.0", "WMS"),
        ("WIDTH", 12, "dimensions"),
        ("BBOX", "0,0,1,1", "bounds"),
    ):
        altered = json.loads(json.dumps(metadata))
        altered["request"][field] = value
        receipt.write_text(json.dumps(altered))
        with pytest.raises(ValueError, match=match):
            count_rendered_site(image, site)
    receipt.write_text(json.dumps(metadata))
    with pytest.raises(ValueError, match="polygon"):
        count_rendered_site(image, {"geometry": {"type": "Point", "coordinates": [0, 0]}})
    image.write_bytes(image.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="checksum"):
        count_rendered_site(image, site)


def test_complete_gallery_executes_without_network(monkeypatch):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    def forbidden(*args, **kwargs):
        raise AssertionError("The counting gallery must run offline")

    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(plt, "show", lambda: None)
    try:
        result = runpy.run_path(str(ROOT / "examples/analysis/plot_candelaria_module_counting.py"))
        sensitivity = result["sensitivity"]
        assert len(sensitivity) == 9
        assert set(sensitivity.tables) == {7}
        assert (sensitivity.candidates.min(), sensitivity.candidates.max()) == (3030, 3032)
        assert len(result["fig"].axes) == 3
        assert 0.26 < result["mx"] < 0.27 and 0.25 < result["my"] < 0.27
    finally:
        plt.close("all")
