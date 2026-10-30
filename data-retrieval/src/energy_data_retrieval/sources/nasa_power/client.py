"""Bounded NASA POWER AOD550 retrieval; no inferred aerosol wavelengths."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd

from energy_data_retrieval.sources.open_meteo import Site
from energy_data_retrieval.transport import HTTPClient, RequestRecord, RetrievalError, object_value

NASA_POWER_HOSTS = frozenset({"power.larc.nasa.gov"})
REFERENCE_IDS = ("nasa_power_aerosols",)


@dataclass(frozen=True, slots=True)
class AODChunk:
    """Daily dimensionless AOD550; source grid resolution is not point precision."""

    site: Site
    frame: pd.DataFrame
    request: RequestRecord
    source: str


@dataclass(slots=True)
class NASAPowerClient:
    http: HTTPClient

    def daily_aod(self, site: Site, start: date, end: date) -> AODChunk:
        """Fetch 1-366 UTC days of total AOD at 550 nm (unadjusted AOD_55).

        NASA POWER serves CERES SYN1deg aerosol fields. Provider fill values
        become NaN; missing dates, unknown units and negative observations fail.
        This is a separate source from the thesis's ECMWF/CAMS aerosol product.
        """
        if start < date(2001, 1, 1) or not 1 <= (end - start).days + 1 <= 366:
            raise ValueError("Request 1-366 days from 2001 onward")
        response = self.http.get_json(
            "https://power.larc.nasa.gov/api/temporal/daily/point",
            {
                "parameters": "AOD_55",
                "community": "RE",
                "format": "JSON",
                "latitude": str(site.latitude),
                "longitude": str(site.longitude),
                "start": start.strftime("%Y%m%d"),
                "end": end.strftime("%Y%m%d"),
                "time-standard": "UTC",
            },
        )
        payload = object_value(response.value)
        header = object_value(payload.get("header"))
        units = object_value(object_value(payload.get("parameters")).get("AOD_55"))
        if units.get("units") != "dimensionless" or header.get("time_standard") != "UTC":
            raise RetrievalError("Unexpected NASA AOD units or time standard")
        fill = header.get("fill_value")
        if isinstance(fill, bool) or not isinstance(fill, (int, float)) or not np.isfinite(fill):
            raise RetrievalError("NASA fill value is missing or invalid")
        parameters = object_value(object_value(payload.get("properties")).get("parameter"))
        raw = object_value(parameters.get("AOD_55"))
        time = pd.date_range(start, end, freq="D", tz="UTC")
        keys = time.strftime("%Y%m%d").tolist()
        if set(raw) != set(keys):
            raise RetrievalError("NASA AOD dates differ from the requested interval")
        values = [raw[key] for key in keys]
        if not all(v is None or (type(v) in (int, float)) for v in values):
            raise RetrievalError("NASA AOD contains nonnumeric observations")
        array = np.asarray(values, dtype=float)
        array[array == fill] = np.nan
        if np.isinf(array).any() or np.any(array < 0):
            raise RetrievalError("NASA AOD contains invalid negative or infinite observations")
        return AODChunk(
            site,
            pd.DataFrame({"timestamp": time, "aod550": array}),
            response.record,
            f"NASA POWER AOD_55; source products: {header.get('sources', [])}",
        )
