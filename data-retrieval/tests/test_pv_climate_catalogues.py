"""Offline catalogue imports retain published labels and reject corrupt source fields."""

from urllib.parse import urlsplit

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.jrc_climate import client as jrc
from energy_data_retrieval.sources.ml21 import client as ml
from energy_data_retrieval.sources.pvcz import client as pvc
from energy_data_retrieval.transport import HTTPClient


@pytest.mark.parametrize("client", [jrc, ml, pvc])
def test_download_uses_exact_public_object_and_records_bytes(client, tmp_path):
    seen = []

    def respond(request):
        seen.append(str(request.url))
        return httpx.Response(200, content=b"source fixture")

    with HTTPClient(
        allowed_hosts=frozenset({urlsplit(client.URL).hostname}),
        transport=httpx.MockTransport(respond),
    ) as http:
        client.download(http, tmp_path / "source")
    assert seen == [client.URL]
    assert (tmp_path / "source").read_bytes() == b"source fixture"
    assert (tmp_path / "source.download.json").exists()


def test_jrc_comments_nan_measurements_and_duplicate_locations(tmp_path):
    path = tmp_path / "jrc.csv"
    path.write_text("# native source\nlat,lon,G,Tw,E,eff\n1,2,1500,30,1400,.93\n2,2,,20,,\n")
    result = jrc.read_catalogue(path)
    assert result.G.iloc[0] == 1500
    assert pd.isna(result.G.iloc[1])
    path.write_text(path.read_text() + "1,2,1500,30,1400,.93\n")
    with pytest.raises(ValueError, match="duplicate"):
        jrc.read_catalogue(path)


def test_pvcz_preserves_rounded_duplicate_coordinates_and_original_threshold_labels(tmp_path):
    path = tmp_path / "pvcz.csv"
    path.write_text(
        "lat,lon,T_equiv_rack_1p1eV,specific_humidity_mean,pvcz,pvcz_labeled\n"
        "10,169,14,3,0,T1:H1\n10,169,14,3,11,T2:H2\n"
    )
    result = pvc.read_catalogue(path)
    assert result.pvcz.tolist() == [0, 11]
    path.write_text(path.read_text().replace("11,T2:H2", "11,T1:H1"))
    with pytest.raises(ValueError, match="disagree"):
        pvc.read_catalogue(path)


def test_ml_workbook_original_and_normalized_csv_labels(tmp_path):
    columns = [
        "LAT",
        "LON",
        "Tann",
        "Tmax",
        "Tmin",
        "DTRann",
        "Pann",
        "Pmin",
        "RHann",
        "GHIann",
        "GHImax",
        "GHImin",
        "UVann",
        "WSann",
        "Yf",
        "ML Climate zone",
        "KGPV",
        "KGPV (names)",
    ]
    frame = pd.DataFrame(
        [[1, 2, 20, 30, 10, 10, 600, 5, 80, 2e8, 3e8, 1e8, 1e7, 2, 1500, "Tro1", 1, "AH"]],
        columns=columns,
    )
    path = tmp_path / "source.xlsx"
    frame.to_excel(path, index=False)
    parsed = ml.read_catalogue(path)
    assert parsed.ml21_zone.tolist() == ["Tro1"]
    assert parsed.GHIann.iloc[0] == 2e8  # No invented annual-total conversion.
    csv = tmp_path / "normalized.csv"
    parsed.to_csv(csv, index=False)
    pd.testing.assert_frame_equal(ml.read_catalogue(csv), parsed)
    parsed.loc[0, "ml21_zone"] = "unknown"
    parsed.to_csv(csv, index=False)
    with pytest.raises(ValueError, match="Unknown"):
        ml.read_catalogue(csv)
