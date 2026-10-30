"""Capture real station catalogues for the offline connector coverage gallery.

Run explicitly from a repository checkout. The gallery never calls this script,
downloads observations, or needs credentials. All valid catalogue coordinates
are retained, including historical sites; no current availability is inferred.
Raw public responses and their request records are saved under ignored
``artifacts/`` so ``--from-cache`` can reproduce a capture without network access.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path

import httpx
import numpy as np
import pandas as pd

from energy_data_retrieval.sources import dwd, noaa, surfrad
from energy_data_retrieval.sources.bsrn import stations as bsrn
from energy_data_retrieval.transport import HTTPClient, HTTPConfig, RequestRecord, TextResponse

FIXTURE_NAME = "generation_coverage_stations.csv"
MANIFEST_NAME = "generation_coverage_stations_provenance.json"
PROVIDERS = ("bsrn", "dwd", "noaa", "surfrad")
FIELDS = ("provider", "station_id", "latitude", "longitude")
MAXIMUM_SOURCE_BYTES = 32_000_000
MAXIMUM_FIXTURE_BYTES = 2_000_000


class CatalogueHTTPClient(HTTPClient):
    """Retain the public text response while exercising the existing client API."""

    source_text: str = ""

    def get_text(
        self,
        endpoint: str,
        parameters: Mapping[str, str] | None = None,
        *,
        secrets: Mapping[str, str] | None = None,
        secret_headers: Mapping[str, str] | None = None,
        use_cache: bool = True,
    ) -> TextResponse:
        if secrets or secret_headers:
            raise ValueError("This preparation script captures public station catalogues only")
        response = super().get_text(endpoint, parameters, use_cache=use_cache)
        self.source_text = response.value
        return response


@dataclass(frozen=True)
class Catalogue:
    provider: str
    frame: pd.DataFrame
    request: RequestRecord
    raw: bytes


def _source(provider: str) -> tuple[frozenset[str], str, dict[str, str]]:
    return {
        "noaa": (noaa.NOAA_HOSTS, noaa.STATIONS_ENDPOINT, {}),
        "bsrn": (bsrn.STATION_HOSTS, bsrn.STATIONS_ENDPOINT, {"format": "textfile"}),
        "dwd": (dwd.DWD_HOSTS, dwd.STATIONS_ENDPOINT, {}),
        "surfrad": (surfrad.SURFRAD_HOSTS, surfrad.STATIONS_ENDPOINT, {}),
    }[provider]


def _acquire(provider: str, *, proxy: str | None) -> Catalogue:
    hosts, _, _ = _source(provider)
    http = CatalogueHTTPClient(
        hosts,
        config=HTTPConfig(
            timeout_seconds=30,
            attempts=2,
            maximum_retry_seconds=2,
            maximum_response_bytes=MAXIMUM_SOURCE_BYTES,
        ),
        transport=httpx.HTTPTransport(proxy=proxy),
    )
    with http:
        if provider == "noaa":
            result = noaa.NOAAClient(http).stations()
        elif provider == "bsrn":
            result = bsrn.fetch_stations(http)
        elif provider == "surfrad":
            result = surfrad.SURFRADClient(http).stations()
        elif provider == "dwd":
            result = dwd.DWDClient(http).stations()
            return Catalogue(provider, result.frame, result.request, result.raw_bytes)
        else:
            raise ValueError(f"Unsupported catalogue: {provider}")
        return Catalogue(provider, result.frame, result.request, http.source_text.encode("utf-8"))


def _cached(provider: str, cache: Path) -> Catalogue:
    raw = (cache / f"{provider}.source").read_bytes()
    request = RequestRecord(**json.loads((cache / f"{provider}.request.json").read_text()))
    _, endpoint, parameters = _source(provider)
    if (
        len(raw) > MAXIMUM_SOURCE_BYTES
        or len(raw) != request.size_bytes
        or hashlib.sha256(raw).hexdigest() != request.sha256
        or request.endpoint != endpoint
        or request.parameters != parameters
    ):
        raise ValueError(f"{provider} cached source differs from its expected request or checksum")
    if provider == "dwd":
        frame = dwd.normalize_stations(raw)
    else:
        text = raw.decode("utf-8")
        normalizer = {
            "noaa": noaa.normalize_stations,
            "bsrn": bsrn.normalize_stations,
            "surfrad": surfrad.normalize_stations,
        }[provider]
        frame = normalizer(text)
    return Catalogue(provider, frame, request, raw)


def _native_count(catalogue: Catalogue) -> tuple[int, str]:
    if catalogue.provider in {"noaa", "bsrn"}:
        delimiter = "," if catalogue.provider == "noaa" else "\t"
        rows = csv.reader(io.StringIO(catalogue.raw.decode("utf-8")), delimiter=delimiter)
        next(rows)
        return sum(bool(row) for row in rows), "Nonempty native CSV/TSV data records"
    if catalogue.provider == "dwd":
        rows = catalogue.raw.decode("iso-8859-1").splitlines()[2:]
        return sum(bool(row.strip()) for row in rows), "Native fixed-width station data records"
    return len(catalogue.frame), (
        "Supported SURFRAD network rows; the linked ARM SGP station and table footnote "
        "are outside this connector and excluded by its catalogue parser"
    )


def _metadata(catalogue: Catalogue, valid: pd.Series) -> dict[str, object]:
    frame = catalogue.frame
    native_count, count_scope = _native_count(catalogue)
    unsupported = (
        frame.loc[~frame["retrieval_supported"], "station_id"].tolist()
        if "retrieval_supported" in frame
        else []
    )
    details = {
        "noaa": {
            "api": "NOAAClient.stations()",
            "native_fields": ["GHCN_ID", "LATITUDE", "LONGITUDE"],
            "scope": (
                "Full historical GHCNh station catalogue, with no country, date or bounding-box "
                "filter; a location does not establish period or variable availability"
            ),
        },
        "bsrn": {
            "api": "energy_data_retrieval.sources.bsrn.stations.fetch_stations()",
            "native_fields": ["Event label", "Latitude", "Longitude"],
            "scope": (
                "Full PANGAEA BSRN station-event catalogue, including entries whose identifier "
                "the current observation retrieval API does not support; event dates do not "
                "establish continuous observation coverage"
            ),
        },
        "dwd": {
            "api": "DWDClient.stations()",
            "native_fields": ["Stations_id", "geoBreite", "geoLaenge"],
            "scope": (
                "All stations in the DWD CDC hourly solar catalogue, not every DWD network; "
                "catalogue positions are recent metadata and do not describe all relocations"
            ),
        },
        "surfrad": {
            "api": "SURFRADClient.stations()",
            "native_fields": ["Code", "Latitude", "Longitude"],
            "scope": (
                "All seven SURFRAD archive stations supported by this connector; the ARM SGP "
                "station linked from the source table belongs to a different provider"
            ),
        },
    }[catalogue.provider]
    return {
        "provider": catalogue.provider,
        **details,
        "request": asdict(catalogue.request),
        "native_station_count": native_count,
        "native_count_scope": count_scope,
        "normalized_station_count": len(frame),
        "identical_native_rows_coalesced": native_count - len(frame),
        "valid_coordinate_count": int(valid.sum()),
        "invalid_coordinate_count": int((~valid).sum()),
        "dropped_station_ids": frame.loc[~valid, "station_id"].tolist(),
        "drop_reason": (
            "Only missing, nonfinite or out-of-range source coordinates are excluded; "
            "latitude/longitude are never swapped or repaired"
        ),
        "catalogue_only_station_ids": unsupported,
        "catalogue_only_reason": (
            "Retained as source catalogue locations, but the current BSRN observation API "
            "accepts only three-letter station identifiers"
            if unsupported
            else None
        ),
        "selected_normalized_fields": ["station_id", "latitude", "longitude"],
        "catalogue_attributes": dict(frame.attrs),
        "reference_ids": list(frame.attrs["reference_ids"]),
    }


def prepare_stations(
    output: Path,
    cache: Path,
    *,
    use_environment_proxy: bool = False,
    from_cache: bool = False,
) -> Path:
    """Write every valid catalogue location, failing if any source cannot be read."""
    proxy = os.environ.get("HTTPS_PROXY") if use_environment_proxy else None
    catalogues = []
    for provider in PROVIDERS:
        catalogue = _cached(provider, cache) if from_cache else _acquire(provider, proxy=proxy)
        if (
            hashlib.sha256(catalogue.raw).hexdigest() != catalogue.request.sha256
            or len(catalogue.raw) != catalogue.request.size_bytes
        ):
            raise ValueError(f"{provider} capture differs from the transport's source checksum")
        if not from_cache:
            cache.mkdir(parents=True, exist_ok=True)
            (cache / f"{provider}.source").write_bytes(catalogue.raw)
            (cache / f"{provider}.request.json").write_text(
                json.dumps(asdict(catalogue.request), indent=2) + "\n", encoding="utf-8"
            )
        catalogues.append(catalogue)

    stream = io.StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    writer.writerow(FIELDS)
    metadata = []
    row_count = 0
    for catalogue in catalogues:
        frame = catalogue.frame
        valid = (
            np.isfinite(frame.latitude)
            & np.isfinite(frame.longitude)
            & frame.latitude.between(-90, 90)
            & frame.longitude.between(-180, 180)
        )
        if frame.station_id.duplicated().any():
            raise ValueError(f"{catalogue.provider} repeats a station ID")
        metadata.append(_metadata(catalogue, valid))
        for row in frame.loc[valid].sort_values("station_id").itertuples():
            coordinates = [
                f"{value:.6f}".rstrip("0").rstrip(".") for value in (row.latitude, row.longitude)
            ]
            writer.writerow((catalogue.provider, row.station_id, *coordinates))
            row_count += 1
    content = stream.getvalue().encode("utf-8")
    if len(content) > MAXIMUM_FIXTURE_BYTES:
        raise ValueError("Full station fixture exceeds 2 MB; no station sampling was applied")
    manifest = {
        "schema_version": 1,
        "fixture": FIXTURE_NAME,
        "fixture_sha256": hashlib.sha256(content).hexdigest(),
        "fixture_bytes": len(content),
        "fixture_rows": row_count,
        "columns": list(FIELDS),
        "coordinates": "Source latitude/longitude in decimal degrees",
        "coordinate_serialization": (
            "Round to at most six decimal places and remove trailing zeros; added decimals "
            "do not imply greater accuracy than the source catalogue"
        ),
        "station_id_reading": "Read station_id as text to preserve DWD leading zeros",
        "sort_order": ["provider", "station_id"],
        "sampling_applied": False,
        "date_country_or_bbox_filter_applied": False,
        "cross_provider_deduplication_applied": False,
        "interpretation": (
            "Each row is a provider catalogue location, not a power-generation site, current "
            "observation guarantee or unique physical station. NOAA includes historical sites. "
            "BSRN and SURFRAD overlap; their identifiers are provider-specific and are retained "
            "separately. Catalogue coordinates do not reconstruct historical station moves."
        ),
        "excluded_connector": {
            "provider": "aemet",
            "reason": "Its station catalogue requires an API key; no credentials were requested",
        },
        "transformations": [
            "Acquire the official public catalogue through each existing station connector",
            "Use the connector's native station ID and coordinate normalization",
            "Retain every finite coordinate within latitude [-90, 90] and longitude [-180, 180]",
            "Preserve catalogue-only station IDs and document their retrieval limitation",
            "Select provider, station_id, latitude and longitude; sort and serialize UTF-8 CSV",
        ],
        "catalogues": metadata,
        "reference_ids": sorted(
            {
                reference
                for catalogue in catalogues
                for reference in catalogue.frame.attrs["reference_ids"]
            }
        ),
    }
    output.mkdir(parents=True, exist_ok=True)
    fixture = output / FIXTURE_NAME
    fixture.write_bytes(content)
    (output / MANIFEST_NAME).write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    return fixture


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=root / "examples/connectors/data")
    parser.add_argument(
        "--cache", type=Path, default=root / "artifacts/connector-coverage/stations"
    )
    parser.add_argument("--use-environment-proxy", action="store_true")
    parser.add_argument(
        "--from-cache", action="store_true", help="Verify and replay saved responses"
    )
    args = parser.parse_args()
    fixture = prepare_stations(
        args.output,
        args.cache,
        use_environment_proxy=args.use_environment_proxy,
        from_cache=args.from_cache,
    )
    print(f"Saved {fixture}; every valid catalogue location was retained")


if __name__ == "__main__":
    main()
