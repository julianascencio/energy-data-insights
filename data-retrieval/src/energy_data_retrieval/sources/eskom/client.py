"""Discover current Eskom hourly renewable exports without frozen upload URLs."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

import pandas as pd

from energy_data_retrieval.generation import GenerationResult
from energy_data_retrieval.sources._generation_utils import (
    bounded_csv,
    numeric,
    unique_observations,
    utc_labels,
)
from energy_data_retrieval.transport import HTTPClient, RetrievalError, array_value, object_value

ESKOM_HOSTS = frozenset({"www.eskom.co.za"})
MEDIA_ENDPOINT = "https://www.eskom.co.za/dataportal/wp-json/wp/v2/media"
DATASET_URL = (
    "https://www.eskom.co.za/dataportal/renewables-performance/hourly-renewable-generation/"
)
REFERENCE_IDS = ("eskom_hourly_renewables", "eskom_generation_statistics")
_TECHNOLOGIES = {
    "Wind": "wind",
    "PV": "solar_pv",
    "CSP": "solar_thermal",
    "Other RE": "other_renewable",
}


def parse_generation_csv(content: str | bytes, *, maximum_rows: int = 100_000) -> pd.DataFrame:
    """Read hourly reported MW, labelled at hour beginning in South African time.

    The product covers Eskom-owned/contracted renewables and excludes embedded
    generation. No energy integration or more precise sampling claim is made.
    """
    wide = bounded_csv(content, maximum_rows=maximum_rows)
    label = "Date Time Hour Beginning"
    if not {label, *_TECHNOLOGIES}.issubset(wide.columns):
        raise RetrievalError("Unexpected Eskom hourly renewable export schema")
    stamp = utc_labels(wide[label], source_timezone="Africa/Johannesburg")
    if (stamp.dt.minute.ne(0) | stamp.dt.second.ne(0)).any():
        raise RetrievalError("Eskom hourly labels must fall on the hour")
    frames = []
    for column, technology in _TECHNOLOGIES.items():
        frames.append(
            pd.DataFrame(
                {
                    "timestamp": stamp,
                    "source_datetime": wide[label],
                    "source": "eskom",
                    "area": "South Africa: Eskom-owned/contracted renewables",
                    "technology": technology,
                    "value": numeric(wide[column], column),
                    "unit": "MW",
                    "interval_minutes": 60,
                    "measurement_kind": "reported_hourly_power",
                }
            )
        )
    result = unique_observations(pd.concat(frames, ignore_index=True), ["timestamp", "technology"])
    result.attrs.update(
        source_url=DATASET_URL,
        timestamp_semantics="Hour beginning, Africa/Johannesburg (UTC+02:00)",
        scope="Eskom-owned or contracted renewables; embedded generation excluded",
        units_basis="MW contribution convention in Eskom renewable system-operator statistics",
        reference_ids=list(REFERENCE_IDS),
    )
    return result


@dataclass(frozen=True, slots=True)
class EskomClient:
    """Public media discovery and a bounded latest-export read.

    The provider's chart page can retain a stale monthly upload URL. The public
    WordPress media catalogue supplies current exact filenames. Discovery selects
    only Hourly_Generation exports, never the separate Total_Hourly product.
    """

    http: HTTPClient
    maximum_rows: int = 100_000

    def generation(
        self, start: date | None = None, end: date | None = None, *, url: str | None = None
    ) -> GenerationResult:
        """Fetch latest published file, optionally filter inclusive local dates.

        This endpoint does not promise an arbitrary historical archive. Missing
        requested days remain absent; frame metadata reports the returned range.
        An explicit URL permits an independently discovered official archive.
        """
        if (start is None) != (end is None) or (
            start is not None and end is not None and start > end
        ):
            raise ValueError("Supply both inclusive dates with start <= end, or neither")
        records = []
        if url is None:
            catalogue = self.http.get_json(
                MEDIA_ENDPOINT,
                {
                    "search": "Hourly_Generation",
                    "per_page": "100",
                    "orderby": "date",
                    "order": "desc",
                },
            )
            records.append(catalogue.record)
            candidates: list[tuple[str, str]] = []
            for item in array_value(catalogue.value):
                row = object_value(item)
                candidate = row.get("source_url")
                if isinstance(candidate, str) and re.search(
                    r"/Hourly_Generation(?:-\d+)?\.csv$", candidate
                ):
                    candidates.append((str(row.get("date", "")), candidate))
            if not candidates:
                raise RetrievalError(
                    "Eskom catalogue has no hourly renewable CSV; supply a verified official URL"
                )
            url = max(candidates)[1]
        parsed = urlsplit(url)
        if (
            parsed.scheme != "https"
            or parsed.hostname not in ESKOM_HOSTS
            or not parsed.path.startswith("/dataportal/wp-content/uploads/")
            or not re.search(r"/Hourly_Generation(?:-\d+)?\.csv$", parsed.path)
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Use an official Eskom Hourly_Generation CSV URL")
        response = self.http.get_text(url)
        records.append(response.record)
        frame = parse_generation_csv(response.value, maximum_rows=self.maximum_rows)
        if start is not None and end is not None:
            local_dates = frame.timestamp.dt.tz_convert("Africa/Johannesburg").dt.date
            frame = frame.loc[local_dates.between(start, end)].reset_index(drop=True)
        frame.attrs.update(export_url=url, requested_start=str(start), requested_end=str(end))
        return GenerationResult(frame, tuple(records))
