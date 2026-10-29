"""GPCC Monthly v2025 archive plans, bounded retrieval and CF processing."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

import xarray as xr

from energy_data_retrieval.climate_grid import normalize_monthly, open_netcdf
from energy_data_retrieval.transport import HTTPClient, RequestRecord

GPCC_HOSTS = frozenset({"opendata.dwd.de"})
ROOT = "https://opendata.dwd.de/climate_environment/GPCC/GPCC_Precipitation_Analysis_Monthly/Version_2025"
REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "gpcc_monthly_v2025")
_RESOLUTIONS = {0.25: "025", 0.5: "050", 1.0: "100", 2.5: "250"}


@dataclass(frozen=True, slots=True)
class GPCCRequest:
    """Inclusive years; v2025 uses five-year blocks through 2020, then monthly files.

    2021-2024 is one four-year block. A recent requested month may not yet be
    published (about two months latency); HTTP failures are never treated as zero.
    """

    start_year: int
    end_year: int
    resolution: float = 0.5
    end_month: int = 12

    def __post_init__(self) -> None:
        if (
            type(self.start_year) is not int
            or type(self.end_year) is not int
            or not 1891 <= self.start_year <= self.end_year <= 9998
        ):
            raise ValueError("GPCC years must be ordered integers from 1891")
        if self.resolution not in _RESOLUTIONS or isinstance(self.resolution, bool):
            raise ValueError("GPCC resolution must be 0.25, 0.5, 1.0 or 2.5 degrees")
        if type(self.end_month) is not int or not 1 <= self.end_month <= 12:
            raise ValueError("end_month must be 1..12")

    def urls(self) -> tuple[str, ...]:
        code = _RESOLUTIONS[self.resolution]
        periods = [
            f"{year}_{year + 4}"
            for year in range(1891, 2021, 5)
            if year <= self.end_year and year + 4 >= self.start_year
        ]
        if self.start_year <= 2024 and self.end_year >= 2021:
            periods.append("2021_2024")
        periods.extend(
            f"{year}_{month:02d}"
            for year in range(max(2025, self.start_year), self.end_year + 1)
            for month in range(1, (self.end_month if year == self.end_year else 12) + 1)
        )
        return tuple(
            f"{ROOT}/{code}_degree/gpcc_precipitation_analysis_monthly_{period}_v2025_{code}.nc.gz"
            for period in periods
        )

    @property
    def doi(self) -> str:
        return f"10.5676/DWD_GPCC/MONTHLY_V2025_{_RESOLUTIONS[self.resolution]}"


class GPCCClient:
    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def download(self, request: GPCCRequest, directory: Path) -> tuple[RequestRecord, ...]:
        """Stream archives sequentially using the shared retry/hash/checkpoint transport."""
        return tuple(
            self.http.download_file(url, directory / url.rsplit("/", 1)[1])
            for url in request.urls()
        )


def iter_monthly(
    paths: Sequence[Path],
    *,
    start_year: int,
    end_year: int,
    bbox: tuple[float, float, float, float] | None = None,
    use_infilled: bool = False,
    maximum_values: int = 20_000_000,
) -> Iterator[xr.DataArray]:
    """Yield monthly totals in mm, retaining NaNs; infilling is explicit opt-in.

    Original archives retain all gauge/error diagnostics. These arrays expose only
    the selected precipitation variable and do not apply undercatch corrections.
    """
    native = "precip_infill" if use_infilled else "precip"
    for path in paths:
        with open_netcdf(path) as ds:
            if ds[native].attrs.get("units", "").lower() not in {"mm", "mm/month", "mm month-1"}:
                raise ValueError("GPCC precipitation must declare monthly millimetres")
            result = normalize_monthly(
                ds,
                {native: ("precipitation_mm", "mm")},
                start_year=start_year,
                end_year=end_year,
                bbox=bbox,
                maximum_values=maximum_values,
            )["precipitation_mm"]
            result = result.where(result >= 0)
            result.attrs.update(
                source="GPCC",
                product_version="2025",
                source_file=path.name,
                infilled=str(use_infilled),
                cell_methods="time: sum",
            )
            yield result
