"""Synthetic arrays validate native tile batching and resumability without S3."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime

import numpy as np
import pandas as pd
import pytest
from numpy.typing import NDArray

from energy_data_retrieval.sources.earthmover_era5 import NativeERA5Client
from energy_data_retrieval.sources.open_meteo import Site
from energy_data_retrieval.transport import RetrievalError


@dataclass
class FixtureArray:
    values: NDArray
    attrs: dict[str, object] = field(default_factory=dict)
    encoding: dict[str, object] = field(default_factory=lambda: {"chunks": (8736, 12, 12)})
    reads: list[str] = field(default_factory=list)

    def isel(self, **indexers: slice) -> FixtureArray:
        self.reads.append("tile")
        array = self.values[indexers["valid_time"], indexers["latitude"], indexers["longitude"]]
        return FixtureArray(array, self.attrs, self.encoding, self.reads)


@dataclass
class FixtureDataset:
    latitude: FixtureArray
    longitude: FixtureArray
    valid_time: FixtureArray
    arrays: dict[str, FixtureArray]
    closed: bool = False

    def __getitem__(self, name: str) -> FixtureArray:
        return self.arrays[name]

    def close(self) -> None:
        self.closed = True


def dataset() -> FixtureDataset:
    start = int(datetime(2026, 10, 27, tzinfo=UTC).timestamp())
    seconds = np.arange(start, start + 25 * 3600, 3600)
    values = {
        "t2m": (274.15, "K"),
        "u10": (3.0, "m s**-1"),
        "v10": (4.0, "m s**-1"),
        "ssrd": (360000.0, "J m**-2"),
        "fg10": (8.0, "m s**-1"),
    }
    return FixtureDataset(
        FixtureArray(np.arange(-40, -28)),
        FixtureArray(np.arange(280, 292)),
        FixtureArray(seconds.astype("datetime64[s]")),
        {
            name: FixtureArray(np.full((25, 12, 12), value), {"units": unit})
            for name, (value, unit) in values.items()
        },
    )


def test_shared_native_tile_is_read_once(monkeypatch: pytest.MonkeyPatch) -> None:
    source = dataset()
    monkeypatch.setattr(NativeERA5Client, "_open", lambda _: source)
    sites = [Site("fixture-a", -34, -70), Site("fixture-b", -33, -69)]
    chunks = list(
        NativeERA5Client(chunk_hours=24).iter_weather(sites, date(2026, 10, 27), date(2026, 10, 27))
    )
    assert len(chunks) == 2 and source.closed
    assert sum(len(array.reads) for array in source.arrays.values()) == 5
    for chunk in chunks:
        assert len(chunk.frame) == 24
        np.testing.assert_allclose(chunk.frame["temperature_c"], 1)
        np.testing.assert_allclose(chunk.frame["wind_speed_ms"], 5)
        np.testing.assert_allclose(chunk.frame["ghi_wm2"], 100)
        assert chunk.frame["timestamp"].iloc[-1] == pd.Timestamp("2026-10-27T23:00Z")


def test_verified_partitions_skip_remote_tile_reads(monkeypatch: pytest.MonkeyPatch) -> None:
    source = dataset()
    monkeypatch.setattr(NativeERA5Client, "_open", lambda _: source)
    seen: list[str] = []

    def skip(site: Site, first: int, last: int, lat: float, lon: float) -> bool:
        assert last - first == 23 * 3600 and lat == -34 and lon == -70
        seen.append(site.site_id)
        return True

    chunks = list(
        NativeERA5Client().iter_weather(
            [Site("fixture", -34, -70)], date(2026, 10, 27), date(2026, 10, 27), skip_partition=skip
        )
    )
    assert chunks == [] and seen == ["fixture"]
    assert not any(array.reads for array in source.arrays.values())
    assert source.closed


def test_snapshot_coverage_and_unit_drift_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    source = dataset()
    monkeypatch.setattr(NativeERA5Client, "_open", lambda _: source)
    with pytest.raises(RetrievalError, match="outside"):
        list(
            NativeERA5Client().iter_weather(
                [Site("fixture", -34, -70)], date(2026, 10, 27), date(2026, 10, 28)
            )
        )
    assert source.closed
    source.arrays["t2m"].attrs["units"] = "Celsius"
    with pytest.raises(RetrievalError, match="native units"):
        list(
            NativeERA5Client().iter_weather(
                [Site("fixture", -34, -70)], date(2026, 10, 27), date(2026, 10, 27)
            )
        )
