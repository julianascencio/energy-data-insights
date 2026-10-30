"""TEPCO CP932, declared power units and signed-flow contracts."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

import httpx
import pandas as pd
import pytest

from energy_data_retrieval.sources.tepco import (
    TEPCO_HOSTS,
    TEPCOClient,
    generation_urls,
    parse_generation_csv,
)
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RetrievalError

DATA = Path(__file__).resolve().parents[2] / "examples/connectors/data"


def sample() -> str:
    return "\n".join((DATA / "generation_tepco.csv").read_text().splitlines()[:3]) + "\n"


def test_native_encoding_units_and_signed_flows() -> None:
    frame = parse_generation_csv(sample().encode("cp932"), include_flows=True)
    assert frame.timestamp.eq(pd.Timestamp("2026-08-31T15:00Z")).all()
    assert frame.unit.eq("MW").all()
    assert frame.loc[frame.technology.eq("pumped_storage"), "value"].item() == -639
    assert frame.loc[frame.technology.eq("pumped_storage"), "flow"].item() == "storage_net"
    assert frame.loc[frame.technology.eq("interconnector"), "value"].item() == 4490
    assert (
        frame.loc[frame.technology.eq("solar") & frame.flow.eq("generation"), "value"].item() == 0
    )
    assert frame.may_include_estimates.all()
    generation = parse_generation_csv(sample())
    assert generation.flow.eq("generation").all()
    assert "interconnector" not in set(generation.technology)


def test_declared_legacy_unit_conversion() -> None:
    data = sample().replace("単位[MW平均]", "単位[万kW平均]")
    frame = parse_generation_csv(data)
    nuclear = frame.loc[frame.technology.eq("nuclear")].iloc[0]
    assert nuclear.value == 12900 and nuclear.source_value == 1290
    with pytest.raises(RetrievalError, match="unit declaration"):
        parse_generation_csv(sample().replace("MW平均", "MWh"))


def test_missing_invalid_duplicate_and_row_limit() -> None:
    missing = sample().replace(",1290,", ",,", 1)
    assert pd.isna(
        parse_generation_csv(missing).loc[lambda x: x.technology.eq("nuclear"), "value"]
    ).all()
    for raw in (sample().replace(",1290,", ",nan,", 1), sample().replace("0:00", "0:15")):
        with pytest.raises(RetrievalError):
            parse_generation_csv(raw)
    with pytest.raises(RetrievalError, match="duplicate"):
        parse_generation_csv(sample() + sample().splitlines()[2] + "\n")
    with pytest.raises(RetrievalError, match="maximum_rows"):
        parse_generation_csv(sample(), maximum_rows=1)


def test_download_native_bytes_and_interval_filter() -> None:
    data = (DATA / "generation_tepco.csv").read_text().encode("cp932")
    with HTTPClient(
        TEPCO_HOSTS,
        config=HTTPConfig(minimum_interval_seconds=0),
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=data)),
    ) as http:
        result = TEPCOClient(http).generation(date(2026, 9, 2), date(2026, 9, 2))
    assert result.frame.timestamp.nunique() == 48
    assert result.requests[0].sha256 == hashlib.sha256(data).hexdigest()
    assert result.frame.timestamp.min() == pd.Timestamp("2026-09-01T15:00Z")
    with pytest.raises(ValueError, match="February 2024"):
        generation_urls(date(2023, 1, 1), date(2023, 1, 1))


def test_real_fixture_checksum_and_coverage() -> None:
    raw = (DATA / "generation_tepco.csv").read_bytes()
    manifest = json.loads((DATA / "generation_tepco_provenance.json").read_text())
    assert hashlib.sha256(raw).hexdigest() == manifest["fixture_sha256"]
    assert parse_generation_csv(raw).timestamp.nunique() == 144
