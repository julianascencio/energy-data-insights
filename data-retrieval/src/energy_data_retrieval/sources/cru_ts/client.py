"""CRU TS v4.10 decadal NetCDF retrieval and native monthly processing."""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

import xarray as xr

from energy_data_retrieval.climate_grid import normalize_monthly, open_netcdf
from energy_data_retrieval.transport import HTTPClient, RequestRecord

CRU_TS_HOSTS = frozenset({"crudata.uea.ac.uk"})
ROOT = "https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/cruts.2604091129.v4.10"
REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "harris_2020_cru_ts", "cru_ts_410")
# Canonical units match native CRU semantics: PET is a rate, PRE a monthly total.
VARIABLES = {
    "tmp": ("temperature_c", "degC"),
    "tmn": ("minimum_temperature_c", "degC"),
    "tmx": ("maximum_temperature_c", "degC"),
    "dtr": ("diurnal_temperature_range_c", "degC"),
    "pre": ("precipitation_mm", "mm"),
    "cld": ("cloud_cover_pct", "%"),
    "vap": ("vapour_pressure_hpa", "hPa"),
    "wet": ("wet_days", "days"),
    "frs": ("frost_days", "days"),
    "pet": ("potential_evapotranspiration_mm_day", "mm/day"),
}
_UNITS = {
    "degC": {"degrees celsius", "degc", "degree_celsius", "degrees_celsius"},
    "mm": {"mm", "mm/month", "mm month-1"},
    "%": {"%", "percent", "percentage"},
    "hPa": {"hpa"},
    "days": {"days", "days/month", "days month-1"},
    "mm/day": {"mm/day", "mm day-1"},
}


@dataclass(frozen=True, slots=True)
class CRUTSRequest:
    """Pin the release, variable and years; select decadal files instead of the full archive."""

    variable: str
    start_year: int
    end_year: int

    def __post_init__(self) -> None:
        if self.variable not in VARIABLES:
            raise ValueError(f"CRU TS variable must be one of {tuple(VARIABLES)}")
        if (
            type(self.start_year) is not int
            or type(self.end_year) is not int
            or not 1901 <= self.start_year <= self.end_year <= 2025
        ):
            raise ValueError("CRU TS v4.10 years must be ordered integers in 1901..2025")

    def urls(self) -> tuple[str, ...]:
        return tuple(
            f"{ROOT}/{self.variable}/cru_ts4.10.{year}.{min(year + 9, 2025)}."
            f"{self.variable}.dat.nc.gz"
            for year in range(1901, 2026, 10)
            if year <= self.end_year and min(year + 9, 2025) >= self.start_year
        )


class CRUTSClient:
    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def download(self, request: CRUTSRequest, directory: Path) -> tuple[RequestRecord, ...]:
        """Use UEA's copy when CEDA is unavailable, per the provider's instructions."""
        return tuple(
            self.http.download_file(url, directory / url.rsplit("/", 1)[1])
            for url in request.urls()
        )


def iter_monthly(
    paths: Sequence[Path],
    *,
    variable: str,
    start_year: int,
    end_year: int,
    bbox: tuple[float, float, float, float] | None = None,
    maximum_values: int = 40_000_000,
) -> Iterator[xr.DataArray]:
    """Yield CF-decoded months, preserving missing cells and native time semantics."""
    CRUTSRequest(variable, start_year, end_year)
    name, unit = VARIABLES[variable]
    for path in paths:
        with open_netcdf(path) as ds:
            if ds[variable].attrs.get("units", "").lower() not in _UNITS[unit]:
                raise ValueError(f"Unexpected CRU TS units for {variable}; expected {unit}")
            result = normalize_monthly(
                ds,
                {variable: (name, unit)},
                start_year=start_year,
                end_year=end_year,
                bbox=bbox,
                maximum_values=maximum_values,
            )[name]
            if variable not in {"tmp", "tmn", "tmx"}:
                result = result.where(result >= 0)
            result.attrs.update(
                source="CRU TS",
                product_version="4.10",
                source_file=path.name,
                attribution="Climatic Research Unit, University of East Anglia",
                license="ODbL-1.0; Database Contents License",
            )
            yield result
