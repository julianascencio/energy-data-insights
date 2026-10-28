"""Read native ERA5 in bounded time/spatial tiles from a pinned public snapshot.

Optional dependencies are imported only when native acquisition is requested.
The public 2026 study snapshot is explicit, never silently advanced to ``main``.
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Protocol, cast

import numpy as np
import pandas as pd
from numpy.typing import NDArray

from energy_data_retrieval.sources.open_meteo import Site
from energy_data_retrieval.transport import RetrievalError

PINNED_SNAPSHOT = "TZ2KX6A24CJ5DG17T7MG"
VARIABLES = ("t2m", "u10", "v10", "ssrd", "fg10")


class _Array(Protocol):
    @property
    def values(self) -> NDArray: ...
    @property
    def attrs(self) -> Mapping[str, object]: ...
    @property
    def encoding(self) -> Mapping[str, object]: ...
    def isel(self, **indexers: slice) -> _Array: ...


class _Dataset(Protocol):
    @property
    def latitude(self) -> _Array: ...
    @property
    def longitude(self) -> _Array: ...
    @property
    def valid_time(self) -> _Array: ...
    def __getitem__(self, variable: str) -> _Array: ...
    def close(self) -> None: ...


@dataclass(frozen=True, slots=True)
class NativeWeatherChunk:
    site: Site
    frame: pd.DataFrame
    snapshot_id: str
    cell_latitude: float
    cell_longitude: float


@dataclass(frozen=True, slots=True)
class NativeERA5Client:
    snapshot_id: str = PINNED_SNAPSHOT
    chunk_hours: int = 8736

    def __post_init__(self) -> None:
        if not self.snapshot_id or not 1 <= self.chunk_hours <= 8736:
            raise ValueError("A pinned snapshot and 1-8736-hour chunks are required")

    def _open(self) -> _Dataset:
        try:
            icechunk = importlib.import_module("icechunk")
            xarray = importlib.import_module("xarray")
        except ModuleNotFoundError:
            raise ImportError(
                "Install energy-data-retrieval[era5-native] for native ERA5 retrieval"
            ) from None
        storage = icechunk.s3_storage(
            bucket="earthmover-icechunk-era5",
            prefix="icechunkV2",
            region="us-east-1",
            anonymous=True,
        )
        repository = icechunk.Repository.open(storage)
        session = repository.readonly_session(snapshot_id=self.snapshot_id)
        return cast(
            _Dataset,
            xarray.open_zarr(
                session.store,
                group="single/temporal",
                consolidated=False,
                chunks=None,
            ),
        )

    def iter_weather(
        self,
        sites: Sequence[Site],
        start: date,
        end: date,
        *,
        skip_partition: Callable[[Site, int, int, float, float], bool] | None = None,
    ) -> Iterator[NativeWeatherChunk]:
        """Read each intersecting native tile once per time block, yielding site frames.

        At most five 12 by 12 spatial tiles of ``chunk_hours + 1`` are resident.
        Sites sharing a native cell reuse values. Source hours beyond snapshot
        coverage fail explicitly, instead of substituting a different weather product.
        """
        if start > end or len({site.site_id for site in sites}) != len(sites):
            raise ValueError("Dates must be ordered and site IDs unique")
        dataset = self._open()
        try:
            _validate_metadata(dataset)
            latitude = np.asarray(dataset.latitude.values, dtype=np.float64)
            longitude = np.asarray(dataset.longitude.values, dtype=np.float64)
            times = np.asarray(dataset.valid_time.values).astype("datetime64[s]").astype(np.int64)
            begin = int(datetime.combine(start, datetime.min.time(), UTC).timestamp())
            stop = int(
                datetime.combine(end + timedelta(days=1), datetime.min.time(), UTC).timestamp()
            )
            first, last = int(np.searchsorted(times, begin)), int(np.searchsorted(times, stop))
            if (
                first >= len(times)
                or last >= len(times)
                or times[first] != begin
                or times[last] != stop
            ):
                raise RetrievalError("Requested interval endpoints are outside this ERA5 snapshot")
            tiles: dict[tuple[int, int], list[tuple[Site, int, int]]] = {}
            for site in sites:
                yi = int(np.abs(latitude - site.latitude).argmin())
                xi = int(np.abs((longitude - site.longitude + 180) % 360 - 180).argmin())
                tiles.setdefault((yi // 12, xi // 12), []).append((site, yi, xi))
            for (tile_y, tile_x), members in sorted(tiles.items()):
                for lo in range(first, last, self.chunk_hours):
                    hi = min(lo + self.chunk_hours, last) + 1
                    active = [
                        (site, yi, xi)
                        for site, yi, xi in members
                        if skip_partition is None
                        or not skip_partition(
                            site,
                            int(times[lo]),
                            int(times[hi - 2]),
                            float(latitude[yi]),
                            float((longitude[xi] + 180) % 360 - 180),
                        )
                    ]
                    if not active:
                        continue
                    arrays = {
                        name: np.asarray(
                            dataset[name]
                            .isel(
                                valid_time=slice(lo, hi),
                                latitude=slice(tile_y * 12, (tile_y + 1) * 12),
                                longitude=slice(tile_x * 12, (tile_x + 1) * 12),
                            )
                            .values,
                            dtype=np.float64,
                        )
                        for name in VARIABLES
                    }
                    for site, yi, xi in active:
                        cell_arrays = {
                            name: array[:, yi % 12, xi % 12] for name, array in arrays.items()
                        }
                        frame = normalize_native_arrays(site.site_id, times[lo:hi], **cell_arrays)
                        yield NativeWeatherChunk(
                            site,
                            frame,
                            self.snapshot_id,
                            float(latitude[yi]),
                            float((longitude[xi] + 180) % 360 - 180),
                        )
        finally:
            dataset.close()


def _validate_metadata(dataset: _Dataset) -> None:
    expected_units = {
        "t2m": {"K"},
        "u10": {"m s**-1", "m s-1", "m/s"},
        "v10": {"m s**-1", "m s-1", "m/s"},
        "ssrd": {"J m**-2", "J m-2", "J/m2"},
        "fg10": {"m s**-1", "m s-1", "m/s"},
    }
    for name in VARIABLES:
        units = dataset[name].attrs.get("units")
        if not isinstance(units, str) or units not in expected_units[name]:
            raise RetrievalError(f"Unexpected ERA5 native units for {name}")
        if tuple(cast(Sequence[int], dataset[name].encoding.get("chunks", ()))) != (8736, 12, 12):
            raise RetrievalError("ERA5 source chunk layout changed; inspect before acquiring")


def normalize_native_arrays(
    site_id: str,
    time_seconds: NDArray,
    *,
    t2m: NDArray,
    u10: NDArray,
    v10: NDArray,
    ssrd: NDArray,
    fg10: NDArray,
) -> pd.DataFrame:
    """Convert original ERA5 units and interval labels without interpolation."""
    times = np.asarray(time_seconds, dtype=np.int64)
    arrays = [np.asarray(value, dtype=np.float64) for value in (t2m, u10, v10, ssrd, fg10)]
    if times.ndim != 1 or len(times) < 2 or not np.all(np.diff(times) == 3600):
        raise ValueError("Native source must contain consecutive hourly endpoint labels")
    if any(array.shape != times.shape or np.isinf(array).any() for array in arrays):
        raise ValueError("Native weather arrays must match the time axis and contain no infinity")
    temperature, u, v, radiation, gust = arrays
    speed = np.hypot(u, v)
    frame = pd.DataFrame(
        {
            "site_id": site_id,
            "timestamp": pd.to_datetime(times[:-1], unit="s", utc=True),
            "duration_hours": 1.0,
            "ghi_wm2": radiation[1:] / 3600.0,
            "temperature_c": (temperature[:-1] + temperature[1:]) / 2 - 273.15,
            "wind_speed_ms": (speed[:-1] + speed[1:]) / 2,
            "gust_ms": gust[1:],
        }
    )
    frame.attrs.update(
        source="ECMWF ERA5 via Earthmover Icechunk",
        timestamp_convention="UTC interval start",
        ghi_alignment="source preceding-hour accumulated J/m2 divided by 3600",
        temperature_wind_alignment="mean of instantaneous start/end samples",
        gust_alignment="source fg10 maximum since previous postprocessing at end label",
        spatial_selection="nearest native 0.25 degree cell",
        station_observations=False,
    )
    return frame
