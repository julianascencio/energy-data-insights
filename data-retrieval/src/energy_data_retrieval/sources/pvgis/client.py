"""Complete, versioned PVGIS 5 and 6 API access with unmodified provider outputs.

PVGIS outputs are modelled resource and PV estimates, not measured plant data.
Coordinates are decimal degrees. PVGIS 5 aspect uses south=0, west=90; PVGIS 6
surface orientation uses north=0, east=90. Read returned metadata for output
units, source grids, time zones and model assumptions before combining products.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from datetime import datetime
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any, Literal, cast
from urllib.parse import quote

import pandas as pd

from energy_data_retrieval.transport import (
    BytesResponse,
    HTTPClient,
    JSONValue,
    RequestRecord,
    RetrievalError,
    atomic_bytes,
)

from ._legacy import _PARAMETERS, contract, prepare
from ._validation import encode, validate

PVGIS_HOSTS = frozenset(
    {"re.jrc.ec.europa.eu", "photovoltaic-geographic-information-system.ec.europa.eu"}
)
PVGIS6_BASE_URL = "https://photovoltaic-geographic-information-system.ec.europa.eu/api/v6"
REFERENCE_IDS = ("pvgis_5_api", "pvgis_6_api")


@lru_cache(maxsize=1)
def _v6_contract() -> dict[str, Any]:
    snapshot = json.loads(files(__package__).joinpath("v6_contract.json").read_text())
    for operation in snapshot["operations"].values():
        operation["parameters"] = {
            name: snapshot["schemas"][key] for name, key in operation["parameters"].items()
        }
    return snapshot


def endpoints(version: str = "6") -> tuple[str, ...]:
    """List every supported operation, including GET/POST variants and metadata."""
    if version == "6":
        return tuple(_v6_contract()["operations"])
    if version in {"5.2", "5.3"}:
        return tuple(f"GET {name}" for name in _PARAMETERS)
    raise ValueError("PVGIS version must be 5.2, 5.3 or 6")


def describe_endpoint(endpoint: str, *, version: str = "6", method: str = "GET") -> dict[str, Any]:
    """Return a fresh copy of accepted native parameters and validation constraints.

    The v6 contract is pinned to the source URL/hash and review date packaged with
    the connector, not fetched on import. Upstream may change independently.
    """
    if version == "6":
        key = f"{method} {endpoint}"
        if key not in _v6_contract()["operations"]:
            raise ValueError(f"Unsupported PVGIS 6 operation: {key}")
        return json.loads(json.dumps(_v6_contract()["operations"][key]))
    if version in {"5.2", "5.3"} and method == "GET":
        return contract(endpoint)
    raise ValueError("PVGIS 5 accepts GET only; supported versions are 5.2, 5.3 and 6")


@dataclass(frozen=True, slots=True)
class PVGISResponse:
    """Exact response bytes and provenance; JSON metadata and missing values survive.

    CSV, EPW, GeoJSON, PNG, ZIP, HTML and BibTeX can be saved without conversion.
    These public calculation responses are not cached by this connector.
    """

    body: bytes
    request: RequestRecord
    content_type: str
    request_id: str | None
    version: str

    @classmethod
    def from_http(cls, response: BytesResponse, version: str) -> PVGISResponse:
        return cls(
            response.value, response.record, response.content_type, response.request_id, version
        )

    def text(self) -> str:
        """Decode a UTF-8 native text output, without removing headers or metadata."""
        try:
            return self.body.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise RetrievalError("PVGIS output is binary, not UTF-8 text") from None

    def json(self) -> JSONValue:
        """Read the complete JSON payload; reject malformed or nonfinite values."""

        def reject(value: str) -> None:
            raise ValueError(f"Nonfinite JSON value: {value}")

        try:
            return cast(JSONValue, json.loads(self.text(), parse_constant=reject))
        except ValueError:
            raise RetrievalError("PVGIS output is not valid finite JSON") from None

    def table(self, *path: str, columns: tuple[str, ...] | None = None) -> pd.DataFrame:
        """Select a native record/column table without inferring timestamps or units.

        Example: ``response.table('outputs', 'hourly')`` for PVGIS 5 seriescalc.
        TMY timestamps belong to different source years; do not sort them into a
        supposed continuous observed year. Original payload remains available.
        """
        value = self.json()
        for key in path:
            if not isinstance(value, dict) or key not in value:
                raise RetrievalError(f"PVGIS output has no table path component {key!r}")
            value = value[key]
        if columns is not None:
            if not isinstance(value, dict) or not columns or not set(columns) <= value.keys():
                raise RetrievalError("Requested PVGIS table columns are missing")
            value = {key: value[key] for key in columns}
        if isinstance(value, list) and all(isinstance(row, dict) for row in value):
            return pd.DataFrame(value)
        if (
            isinstance(value, dict)
            and value
            and all(isinstance(v, list) for v in value.values())
            and len({len(v) for v in value.values() if isinstance(v, list)}) == 1
        ):
            return pd.DataFrame(value)
        raise RetrievalError("Selected PVGIS output is not a rectangular table")

    def save(self, path: Path) -> None:
        """Save native bytes and a neighboring ``.provenance.json`` manifest."""
        atomic_bytes(path, self.body)
        manifest = {
            "version": self.version,
            "content_type": self.content_type,
            "request_id": self.request_id,
            "request": asdict(self.request),
            "reference_ids": list(REFERENCE_IDS),
        }
        atomic_bytes(
            path.with_suffix(path.suffix + ".provenance.json"),
            json.dumps(manifest, indent=2, allow_nan=False).encode(),
        )


def load_response(path: Path) -> PVGISResponse:
    """Read an unmodified saved response after checking its byte count and SHA-256.

    The neighboring manifest is written by ``PVGISResponse.save``. Integrity
    checks detect accidental changes; they do not authenticate the data provider.
    """
    raw = path.read_bytes()
    manifest = json.loads(path.with_suffix(path.suffix + ".provenance.json").read_text())
    record = RequestRecord(**manifest["request"])
    if len(raw) != record.size_bytes or hashlib.sha256(raw).hexdigest() != record.sha256:
        raise ValueError("Saved PVGIS response differs from its size or checksum")
    if manifest["version"] not in {"5.2", "5.3", "6"}:
        raise ValueError("Unsupported saved PVGIS response version")
    return PVGISResponse(
        raw, record, manifest["content_type"], manifest["request_id"], manifest["version"]
    )


@dataclass(slots=True)
class PVGISClient:
    """All seven PVGIS 5 endpoints; explicit version defaults to 5.3.

    Use native parameter names through ``request`` or the named methods. Optional
    ``None`` values are omitted. PVGIS chooses its database if none is supplied;
    availability and vintage must be inspected in the returned metadata.
    """

    http: HTTPClient
    version: Literal["5.2", "5.3"] = "5.3"

    def __post_init__(self) -> None:
        if self.version not in {"5.2", "5.3"}:
            raise ValueError("PVGISClient supports versions 5.2 and 5.3; use PVGIS6Client for 6")

    def request(self, endpoint: str, **parameters: Any) -> PVGISResponse:
        """Call a documented endpoint with validated native parameters.

        The default output is JSON; outputformat='csv'/'basic' preserves native
        text and outputformat='epw' is available for TMY. No key is required.
        """
        query = prepare(endpoint, parameters)
        base = f"https://re.jrc.ec.europa.eu/api/v{self.version.replace('.', '_')}"
        return PVGISResponse.from_http(
            self.http.request_bytes(f"{base}/{endpoint}", query), self.version
        )

    def grid_connected(
        self, latitude: float, longitude: float, *, peakpower: float, loss: float, **parameters: Any
    ) -> PVGISResponse:
        """PVcalc: rated peakpower in kW and aggregate system loss in percent."""
        return self.request(
            "PVcalc", lat=latitude, lon=longitude, peakpower=peakpower, loss=loss, **parameters
        )

    def off_grid(
        self,
        latitude: float,
        longitude: float,
        *,
        peakpower: float,
        batterysize: float,
        consumptionday: float,
        cutoff: float,
        **parameters: Any,
    ) -> PVGISResponse:
        """SHScalc: peakpower W, battery Wh, daily demand Wh, cutoff percent.

        Optional hourconsumption is 24 nonnegative fractions summing to one,
        ordered by local standard time, without daylight saving.
        """
        return self.request(
            "SHScalc",
            lat=latitude,
            lon=longitude,
            peakpower=peakpower,
            batterysize=batterysize,
            consumptionday=consumptionday,
            cutoff=cutoff,
            **parameters,
        )

    def monthly_radiation(
        self, latitude: float, longitude: float, **parameters: Any
    ) -> PVGISResponse:
        """MRcalc: select at least one native radiation/temperature output flag."""
        return self.request("MRcalc", lat=latitude, lon=longitude, **parameters)

    def daily_radiation(
        self, latitude: float, longitude: float, *, month: int, **parameters: Any
    ) -> PVGISResponse:
        """DRcalc: representative daily profiles; month=0 requests all months.

        Use ``**{'global': True}`` for the native keyword, or select other outputs
        such as showtemperatures=True. These are not daily observed time series.
        """
        return self.request("DRcalc", lat=latitude, lon=longitude, month=month, **parameters)

    def hourly(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """seriescalc: hourly irradiance/weather and optional PV output.

        pvcalculation=True requires peakpower in kW and loss in percent. Returned
        P is W; radiation fields are W/m². Preserve source timestamp offsets.
        """
        return self.request("seriescalc", lat=latitude, lon=longitude, **parameters)

    def typical_year(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """tmy: composite meteorological year and source-month selection metadata."""
        return self.request("tmy", lat=latitude, lon=longitude, **parameters)

    def horizon(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """printhorizon: native horizon and solar profiles; inspect azimuth convention."""
        return self.request("printhorizon", lat=latitude, lon=longitude, **parameters)


def _horizon_upload(path: Path) -> tuple[str, bytes, str]:
    if path.suffix.lower() not in {".json", ".csv"} or path.stat().st_size > 1024 * 1024:
        raise ValueError("Horizon upload must be JSON/CSV of at most 1 MiB")
    raw = path.read_bytes()
    try:
        value = (
            json.loads(raw)
            if path.suffix.lower() == ".json"
            else {"horizon_height": [float(item) for item in raw.decode().strip().split(",")]}
        )
        if not isinstance(value, dict):
            raise ValueError
        units = value.get("units", "degrees")
        if units not in {"degrees", "radians"}:
            raise ValueError
        maximum = 90 if units == "degrees" else math.pi / 2
        heights = value["horizon_height"]
        validate(
            heights,
            {
                "type": "array",
                "minItems": 4,
                "items": {"type": "number", "minimum": 0, "maximum": maximum},
            },
            "horizon_height",
        )
        if "azimuth" in value:
            validate(
                value["azimuth"],
                {
                    "type": "array",
                    "minItems": len(heights),
                    "maxItems": len(heights),
                    "items": {"type": "number", "minimum": 0, "maximum": maximum * 4},
                },
                "azimuth",
            )
    except (ValueError, KeyError, TypeError, UnicodeError):
        raise ValueError(
            "Invalid PVGIS horizon file: provide at least four valid heights"
        ) from None
    return (
        "horizon" + path.suffix.lower(),
        raw,
        "application/json" if path.suffix.lower() == ".json" else "text/csv",
    )


@dataclass(slots=True)
class PVGIS6Client:
    """PVGIS 6 operations from the packaged, reviewed OpenAPI request contract.

    Coordinates are always explicit for location-dependent operations. A horizon
    file selects the corresponding multipart POST variant. Every calculation
    field then goes into the form body, as required by the current v6 service.
    """

    http: HTTPClient

    def request(
        self,
        endpoint: str,
        *,
        parameters: Mapping[str, Any] | None = None,
        horizon_file: Path | None = None,
        method: Literal["GET", "POST"] | None = None,
        **kwargs: Any,
    ) -> PVGISResponse:
        """Call any listed endpoint, preserving its JSON/text/binary response.

        Use parameters for programmatic native names, or keyword arguments.
        Lists use repeated query/form keys, not comma joining (unless the
        provider explicitly defines a comma-separated string). None is omitted.
        """
        overlap = (parameters or {}).keys() & kwargs.keys()
        if overlap:
            raise ValueError(f"Duplicate PVGIS parameters: {sorted(overlap)}")
        values = {k: v for k, v in (dict(parameters or {}) | kwargs).items() if v is not None}
        chosen = method or ("POST" if horizon_file is not None else "GET")
        if chosen == "GET" and horizon_file is not None:
            raise ValueError("Horizon files require POST")
        definition = describe_endpoint(endpoint, method=chosen)
        schemas = definition["parameters"]
        if {"latitude", "longitude"} <= schemas.keys() and not {
            "latitude",
            "longitude",
        } <= values.keys():
            raise ValueError("Explicit latitude and longitude are required")
        uploaded = {"horizon_profile": _horizon_upload(horizon_file)} if horizon_file else {}
        if uploaded.keys() & values.keys():
            raise ValueError("Supply either horizon_file or horizon_profile, not both")
        supplied = values.keys() | uploaded.keys()
        if supplied - schemas.keys():
            raise ValueError(f"Unsupported PVGIS 6 parameters: {sorted(supplied - schemas.keys())}")
        if missing := set(definition["required"]) - supplied:
            raise ValueError(f"Missing PVGIS 6 parameters: {sorted(missing)}")
        encoded: dict[str, str | list[str]] = {}
        for name, value in values.items():
            if schemas[name].get("contentMediaType") == "application/octet-stream":
                raise ValueError("Use horizon_file for multipart horizon uploads")
            validate(value, schemas[name], name)
            encoded[name] = (
                [encode(item) for item in value]
                if isinstance(value, (list, tuple))
                else encode(value)
            )
        if "multiple-surfaces" in endpoint:
            surface_fields = ("surface_orientation", "surface_tilt", "peak-power")
            arrays = {name: values.get(name, schemas[name]["default"]) for name in surface_fields}
            if len({len(value) for value in arrays.values()}) != 1:
                raise ValueError("Surface orientation, tilt and peak-power need equal lengths")
            for name, maximum in (("surface_orientation", 360), ("surface_tilt", 180)):
                for item in arrays[name]:
                    validate(item, {"type": "number", "minimum": 0, "maximum": maximum}, name)
            if any(value <= 0 for value in arrays["peak-power"]):
                raise ValueError("Each surface peak-power must be positive (kWp)")
        if "start_time" in values and "end_time" in values:
            try:
                if datetime.fromisoformat(values["start_time"]) > datetime.fromisoformat(
                    values["end_time"]
                ):
                    raise ValueError("start_time must not follow end_time")
            except TypeError:
                raise ValueError(
                    "start_time and end_time must use consistent time-zone offsets"
                ) from None
        if "periods" in values and values["periods"] <= 0:
            raise ValueError("periods must be positive")
        path = endpoint
        if endpoint == "/coverage/layers/{name}":
            name = str(values["name"])
            if not name or any(c in name for c in "/\\?#") or name in {".", ".."}:
                raise ValueError("Coverage layer name must be a single path segment")
            path = endpoint.replace("{name}", quote(name, safe=""))
            encoded.pop("name")
        response = self.http.request_bytes(
            PVGIS6_BASE_URL + path,
            encoded if chosen == "GET" else None,
            method=chosen,
            form=encoded if chosen == "POST" else None,
            files=uploaded or None,
        )
        return PVGISResponse.from_http(response, "6")

    def performance(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """PV performance and energy summaries."""
        return self.request(
            "/performance/broadband", latitude=latitude, longitude=longitude, **parameters
        )

    def multiple_surface_performance(
        self, latitude: float, longitude: float, **parameters: Any
    ) -> PVGISResponse:
        """Performance for multiple PV surfaces."""
        return self.request(
            "/performance/broadband-multiple-surfaces",
            latitude=latitude,
            longitude=longitude,
            **parameters,
        )

    def power(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """PV power, irradiance and meteorological time series."""
        return self.request(
            "/power/broadband", latitude=latitude, longitude=longitude, **parameters
        )

    def multiple_surface_power(
        self, latitude: float, longitude: float, **parameters: Any
    ) -> PVGISResponse:
        """PV power time series for multiple surfaces."""
        return self.request(
            "/power/broadband-multiple-surfaces",
            latitude=latitude,
            longitude=longitude,
            **parameters,
        )

    def optimize_surface(
        self, latitude: float, longitude: float, **parameters: Any
    ) -> PVGISResponse:
        """Optimal surface orientation and tilt."""
        return self.request(
            "/power/surface/optimisation", latitude=latitude, longitude=longitude, **parameters
        )

    def solar_position(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """Solar geometry time series and optional horizon shading."""
        return self.request(
            "/solar-position/overview", latitude=latitude, longitude=longitude, **parameters
        )

    def typical_year(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """Composite meteorological year with month-selection metadata."""
        return self.request(
            "/meteorological/typical-meteorological-year",
            latitude=latitude,
            longitude=longitude,
            **parameters,
        )

    def degree_days(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """Heating/cooling degree days with explicit temperature thresholds."""
        return self.request(
            "/meteorological/degree-days", latitude=latitude, longitude=longitude, **parameters
        )

    def horizon(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """Horizon heights; default output angles are radians."""
        return self.request(
            "/topography/horizon-profile", latitude=latitude, longitude=longitude, **parameters
        )

    def elevation(self, latitude: float, longitude: float, **parameters: Any) -> PVGISResponse:
        """Digital terrain elevation in metres."""
        return self.request(
            "/topography/elevation", latitude=latitude, longitude=longitude, **parameters
        )

    def available_sources(
        self, latitude: float, longitude: float, **parameters: Any
    ) -> PVGISResponse:
        """Irradiance datasets covering this location."""
        return self.request(
            "/coverage/available-sources-in-selected-location",
            latitude=latitude,
            longitude=longitude,
            **parameters,
        )

    def location_in_source(
        self, latitude: float, longitude: float, **parameters: Any
    ) -> PVGISResponse:
        """Test location coverage of an explicitly selected source."""
        return self.request(
            "/coverage/location-within-selected-source",
            latitude=latitude,
            longitude=longitude,
            **parameters,
        )

    def coverage_layers(self) -> PVGISResponse:
        """List available coverage layers."""
        return self.request("/coverage/layers")

    def coverage_map(self) -> PVGISResponse:
        """Retrieve the native interactive coverage HTML."""
        return self.request("/coverage/map")

    def citation(self) -> PVGISResponse:
        """Retrieve provider citation metadata."""
        return self.request("/reference/citation")

    def publications(self) -> PVGISResponse:
        """Retrieve provider bibliography."""
        return self.request("/reference/publications")

    def conventions(self) -> PVGISResponse:
        """Retrieve coordinate, time and physical conventions."""
        return self.request("/reference/conventions-in-pvgis")

    def license(self) -> PVGISResponse:
        """Retrieve provider licensing metadata."""
        return self.request("/reference/license")

    def features(self) -> PVGISResponse:
        """Retrieve the current service capability description."""
        return self.request("/features")

    def coverage_layer(self, name: str) -> PVGISResponse:
        """Retrieve a named coverage layer as native GeoJSON."""
        return self.request("/coverage/layers/{name}", name=name)
