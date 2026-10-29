"""Atomic checkpoint and bounded-submission behavior."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest

from energy_data_retrieval.cli import build_parser
from energy_data_retrieval.storage import bounded_map, existing_artifact, fingerprint, write_parquet
from energy_data_retrieval.transport import JSONValue


def test_parquet_resume_and_checksum(tmp_path: Path) -> None:
    frame = pd.DataFrame(
        {
            "site_id": ["fixture"],
            "timestamp": pd.to_datetime(["2026-10-27T00:00Z"]),
            "actual_mwh": [0.0],
        }
    )
    path = tmp_path / "day.parquet"
    request: dict[str, JSONValue] = {"date": "2026-10-27"}
    first = write_parquet(frame, path, request=request, provenance={"synthetic_fixture": True})
    second = write_parquet(frame, path, request=request, provenance={"synthetic_fixture": True})
    assert first == second == existing_artifact(path, fingerprint(request))
    assert pd.read_parquet(path)["actual_mwh"].iloc[0] == 0
    with pytest.raises(ValueError, match="does not match"):
        write_parquet(frame, path, request={"date": "2026-10-28"}, provenance={})
    path.write_bytes(path.read_bytes() + b"corrupted")
    with pytest.raises(ValueError, match="checksum"):
        existing_artifact(path, fingerprint(request))


def test_incomplete_checkpoint_is_not_silently_reused(tmp_path: Path) -> None:
    path = tmp_path / "partial.parquet"
    path.write_bytes(b"unfinished")
    with pytest.raises(ValueError, match="Incomplete"):
        existing_artifact(path, "fixture")


def test_tasks_are_submitted_lazily() -> None:
    produced = 0

    def source() -> Iterator[int]:
        nonlocal produced
        for i in range(100):
            produced += 1
            yield i

    def square(value: int) -> int:
        return value * value

    results = bounded_map(square, source(), workers=3)
    next(results)
    assert produced == 3
    remainder = list(results)
    assert len(remainder) == 99 and produced == 100


def test_cli_contract() -> None:
    args = build_parser().parse_args(
        [
            "open-meteo",
            "--sites",
            "sites.csv",
            "--start",
            "2026-10-01",
            "--end",
            "2026-10-27",
            "--product",
            "ifs",
            "--output",
            "data/weather",
        ]
    )
    assert args.product == "ifs" and args.workers == 2
