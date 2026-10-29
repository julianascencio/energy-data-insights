"""Synthetic PANGAEA exports test BSRN identity, minutes, native values and provenance."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.bsrn import (
    BSRN_HOSTS,
    BSRNClient,
    normalize_dataset,
    save_dataset,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, JSONValue, RetrievalError

DOI = "10.1594/PANGAEA.725795"
ENDPOINT = f"https://doi.pangaea.de/{DOI}"


def metadata() -> dict[str, JSONValue]:
    return {
        "@type": "Dataset",
        "identifier": f"https://doi.org/{DOI}",
        "name": "Basic and other measurements of radiation at station Cabauw (2009-06)",
        "creator": {"@type": "Person", "name": "Synthetic station investigator"},
        "license": "https://bsrn.awi.de/data/conditions-of-data-release/",
        "temporalCoverage": "2009-06-01T00:00:00/2009-06-01T00:02:00",
        "spatialCoverage": {"geo": {"latitude": 51.968, "longitude": 4.928}},
    }


def export() -> str:
    return (
        "/* DATA DESCRIPTION:\n"
        f"Citation:\tSynthetic investigator (2009): synthetic BSRN fixture. https://doi.org/{DOI}\n"
        "Project(s):\tBaseline Surface Radiation Network (BSRN) (URI: https://bsrn.awi.de/)\n"
        "Event(s):\tCAB (Cabauw) * LATITUDE: 51.968000 * LONGITUDE: 4.928000\n"
        "License:\tBaseline Surface Radiation Network License 1.0\n"
        "*/\n"
        "Date/Time\tHeight [m]\tSWD [W/m**2]\tSWD std dev [W/m**2]\tDIR [W/m**2]"
        "\tDIF [W/m**2]\tLWD [W/m**2]\tSWU [W/m**2]\tT2 [°C]\tRH [%]\tPoPoPoPo [hPa]\n"
        "2009-06-01T00:00\t2\t-2\t0.1\t0\t-1\t330\t0\t14.8\t91.6\t1024\n"
        "2009-06-01T00:01\t2\t\t\t?5\t<1\t331\t0\t\t\t1024\n"
        "2009-06-01T00:02\t2\t0\t0.0\t1\t2\t332\t1\t15.0\t90.0\t1023\n"
    )


def normalized(text: str | None = None, meta: dict[str, JSONValue] | None = None) -> pd.DataFrame:
    return normalize_dataset(
        export() if text is None else text,
        metadata() if meta is None else meta,
        doi=DOI,
        station="cab",
        year=2009,
        month=6,
    )


def test_native_minutes_values_missing_qualifiers_and_raw_fields_are_preserved() -> None:
    result = normalized()
    assert result["timestamp"].dt.tz is not None
    assert result["timestamp"].dt.minute.tolist() == [0, 1, 2]
    assert result["station_id"].unique().tolist() == ["cab"]
    assert result["swd_wm2"].iloc[0] == -2
    assert pd.isna(result["swd_wm2"].iloc[1])
    assert result["swd_wm2"].iloc[2] == 0
    assert result["dir_wm2"].iloc[1] == 5
    assert result["dir_wm2_qualifier"].iloc[1] == "?"
    assert result["dif_wm2_qualifier"].iloc[1] == "<"
    assert result["source:DIR [W/m**2]"].iloc[1] == "?5"
    assert result["source:SWD [W/m**2]"].iloc[1] == ""
    assert result.attrs["logical_records"] == ["0100", "0300"]
    assert result.attrs["hourly_weather_contract"] is False
    assert result.attrs["quality_control_applied"] is False
    assert result.attrs["quality_flags_available_in_archive"] is False
    assert result.attrs["missing_minutes_in_calendar_month"] == 30 * 1440 - 3


def test_gaps_are_retained_without_filling_or_changing_source_labels() -> None:
    text = (
        "\n".join(line for line in export().splitlines() if not line.startswith("2009-06-01T00:01"))
        + "\n"
    )
    result = normalized(text)
    assert len(result) == 2
    assert result["timestamp"].dt.minute.tolist() == [0, 2]
    assert result["source:Date/Time"].tolist() == ["2009-06-01T00:00", "2009-06-01T00:02"]


@pytest.mark.parametrize(
    "old,new,error",
    [
        ("Event(s):\tCAB", "Event(s):\tSBO", "station"),
        ("Baseline Surface Radiation Network (BSRN)", "Unrelated observations", "BSRN project"),
        ("SWD [W/m**2]", "SWD [kW/m**2]", "columns or units"),
        ("2009-06-01T00:01\t", "2009-06-01T00:00\t", "unique and ordered"),
        ("2009-06-01T00:01\t", "2009-06-01T00:01:30\t", "minute labels"),
        ("\t?5\t", "\tNaN\t", "unsupported value"),
        ("\t?5\t", "\tø5\t", "unsupported value"),
    ],
)
def test_wrong_identity_units_clock_or_numeric_contract_fails(
    old: str, new: str, error: str
) -> None:
    with pytest.raises(RetrievalError, match=error):
        normalized(export().replace(old, new))


@pytest.mark.parametrize(
    "field,value,error",
    [
        ("identifier", "https://doi.org/10.1594/PANGAEA.123456", "different dataset DOI"),
        ("name", "Other radiation measurements at station Cabauw (2009-06)", "logical record"),
        ("name", "Basic measurements of radiation at station Cabauw (2009-07)", "requested month"),
        ("temporalCoverage", "2009-06-01T00:00:00/2009-06-01T00:03:00", "endpoints"),
        ("license", None, "creator and license"),
    ],
)
def test_dataset_metadata_must_match_export_and_requested_product(
    field: str, value: JSONValue, error: str
) -> None:
    meta = metadata()
    meta[field] = value
    with pytest.raises(RetrievalError, match=error):
        normalized(meta=meta)


def test_malformed_rows_and_bounds_are_rejected() -> None:
    with pytest.raises(RetrievalError, match="row width"):
        normalized(export().replace("\t1024\n", "\n", 1))
    with pytest.raises(RetrievalError, match="maximum_rows"):
        normalize_dataset(
            export(), metadata(), doi=DOI, station="cab", year=2009, month=6, maximum_rows=2
        )


def test_public_dataset_retrieve_keeps_sources_and_reuses_only_verified_snapshot(
    tmp_path: Path,
) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.host == "doi.pangaea.de"
        assert request.url.path == f"/{DOI}"
        if request.url.params["format"] == "metadata_jsonld":
            return httpx.Response(200, json=metadata())
        assert request.url.params["format"] == "textfile"
        return httpx.Response(200, text=export())

    output = tmp_path / "cab_200906.parquet"
    with HTTPClient(
        BSRN_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        client = BSRNClient(http)
        first = client.retrieve(DOI, station="CAB", year=2009, month=6, output=output)
        second = client.retrieve(DOI, station="cab", year=2009, month=6, output=output)
        assert first == second and calls == 2
        assert first.rows == 3
        raw_path = output.with_suffix(".parquet.source.tsv")
        assert raw_path.read_text() == export()
        manifest = json.loads(output.with_suffix(".parquet.json").read_text())
        assert (
            manifest["provenance"]["source_artifacts"][raw_path.name]["sha256"]
            == hashlib.sha256(export().encode()).hexdigest()
        )
        assert manifest["provenance"]["dataset_metadata"]["identifier"] == f"https://doi.org/{DOI}"
        assert pd.read_parquet(output)["source:DIR [W/m**2]"].iloc[1] == "?5"
        raw_path.write_text("modified source")
        with pytest.raises(ValueError, match="sidecar"):
            client.retrieve(DOI, station="cab", year=2009, month=6, output=output)
        assert calls == 2


def test_malformed_metadata_stops_before_data_request() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        meta = metadata()
        meta["name"] = "Radiosonde measurements at station Cabauw (2009-06)"
        return httpx.Response(200, json=meta)

    with (
        HTTPClient(BSRN_HOSTS, transport=httpx.MockTransport(handler)) as http,
        pytest.raises(RetrievalError, match="logical record"),
    ):
        BSRNClient(http).dataset(DOI, station="cab", year=2009, month=6)
    assert len(requests) == 1


def test_search_completes_pagination_but_does_not_promote_candidates_to_verified_data() -> None:
    calls: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        assert request.url.params["q"] == 'project:BSRN event:CAB "2009-06"'
        offset = int(request.url.params["offset"])
        return httpx.Response(
            200,
            json={
                "totalCount": 2,
                "offset": offset,
                "results": [
                    {
                        "URI": f"doi:10.1594/PANGAEA.{725795 + offset}",
                        "html": "Synthetic discovery hit",
                    }
                ],
            },
        )

    with HTTPClient(
        BSRN_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = BSRNClient(http).search("cab", 2009, 6, page_size=1)
    assert len(calls) == 2 and len(result.candidates) == 2
    assert result.candidates[0]["doi"] == DOI
    assert result.as_dict()["candidate_validation_required"] is True
    assert all(request.url.host == "www.pangaea.de" for request in calls)


@pytest.mark.parametrize("case", ["limit", "truncated", "duplicate", "changed_total"])
def test_search_rejects_excessive_incomplete_or_inconsistent_pages(case: str) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        offset = int(request.url.params["offset"])
        count = 3 if case == "limit" or (case == "changed_total" and offset) else 2
        result = {
            "URI": f"doi:10.1594/PANGAEA.{725795 if case == 'duplicate' else 725795 + offset}"
        }
        return httpx.Response(
            200,
            json={
                "totalCount": count,
                "offset": offset,
                "results": [] if case == "truncated" else [result],
            },
        )

    with (
        HTTPClient(
            BSRN_HOSTS,
            transport=httpx.MockTransport(handler),
            config=HTTPConfig(minimum_interval_seconds=0),
        ) as http,
        pytest.raises(RetrievalError),
    ):
        BSRNClient(http).search("cab", 2009, 6, page_size=1, maximum_results=2)


def test_invalid_selection_and_non_pangaea_doi_never_reach_network() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        pytest.fail("invalid selection must fail before network")

    with HTTPClient(BSRN_HOSTS, transport=httpx.MockTransport(handler)) as http:
        client = BSRNClient(http)
        for doi, station, year, month in (
            ("10.1234/other", "cab", 2009, 6),
            (DOI, "../", 2009, 6),
            (DOI, "cab", 2009, 13),
        ):
            with pytest.raises(ValueError):
                client.dataset(doi, station=station, year=year, month=month)


def test_modified_in_memory_result_cannot_be_saved(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return (
            httpx.Response(200, json=metadata())
            if request.url.params["format"] == "metadata_jsonld"
            else httpx.Response(200, text=export())
        )

    with HTTPClient(
        BSRN_HOSTS,
        transport=httpx.MockTransport(handler),
        config=HTTPConfig(minimum_interval_seconds=0),
    ) as http:
        result = BSRNClient(http).dataset(DOI, station="cab", year=2009, month=6)
    original = copy.deepcopy(result.frame)
    result.frame.loc[0, "swd_wm2"] = 999
    with pytest.raises(ValueError, match="differs"):
        save_dataset(result, tmp_path / "modified.parquet")
    assert original["swd_wm2"].iloc[0] == -2
    assert list(tmp_path.iterdir()) == []
