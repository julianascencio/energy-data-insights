"""Reuse Orbital PV for satellite imagery; add bounded Maxar Open Data discovery."""

from __future__ import annotations

import importlib
import math
import re
import sys
from collections import deque
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, cast
from urllib.parse import urljoin, urlsplit

import pandas as pd
from rasterio import CRS

from energy_data_retrieval.terrain import Bounds, validate_bounds
from energy_data_retrieval.transport import HTTPClient, RequestRecord, object_value

ORBITALPV_COMMIT = "498c47e182f9f0e1b0f0d40bc3125ef7c2110a05"
MAXAR_ROOT = "https://maxar-opendata.s3.amazonaws.com/events/"
IMAGERY_HOSTS = frozenset(
    {
        "maxar-opendata.s3.amazonaws.com",
        "earth-search.aws.element84.com",
        "e84-earth-search-sentinel-data.s3.us-west-2.amazonaws.com",
    }
)
REFERENCE_IDS = ("orbitalpv_imagery", "earth_search_c1", "sentinel2_imagery", "maxar_open_data")


def _orbital() -> Any:
    if sys.version_info < (3, 13):
        raise ImportError(
            "Orbital PV imagery requires Python 3.13+ and energy-data-retrieval[imagery]"
        )
    try:
        module = importlib.import_module("orbitalpv")
    except ImportError as exc:
        raise ImportError("Install energy-data-retrieval[imagery] with Python 3.13+") from exc
    if not all(
        hasattr(module, name)
        for name in ("Sentinel2GroundConnector", "read_ground_image", "load_ground_image")
    ):
        raise ImportError(
            "Install the pinned imagery extra; the older PyPI release lacks these APIs"
        )
    return module


def _utc(value: str) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if pd.isna(stamp):
        raise ValueError("Acquisition times must be finite ISO dates/timestamps")
    return stamp.tz_localize("UTC") if stamp.tzinfo is None else stamp.tz_convert("UTC")


def _interval(time_min: str, time_max: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    start, stop = _utc(time_min), _utc(time_max)
    if stop <= start:
        raise ValueError("time_max must be later than time_min")
    return start, stop


def _positive(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) and value > 0 else None


def _https(url: str, *, maxar_only: bool = False) -> str:
    parsed = urlsplit(url)
    hosts = {"maxar-opendata.s3.amazonaws.com"} if maxar_only else IMAGERY_HOSTS
    if (
        parsed.scheme != "https"
        or parsed.hostname not in hosts
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("Imagery URL must be unsigned HTTPS on an approved provider host")
    if maxar_only and not parsed.path.startswith("/events/"):
        raise ValueError("Maxar assets must belong to the public events catalogue")
    return url


def _intersects(a: Bounds, b: Bounds) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


@dataclass(frozen=True, slots=True)
class ImagerySearch:
    """Search scope and completeness, not a promise of global finest imagery."""

    provider: str
    items: tuple[dict[str, Any], ...]
    bounds_wgs84: Bounds
    time_min: str
    time_max: str
    complete: bool
    requests: tuple[RequestRecord, ...]
    metadata: dict[str, Any]


@dataclass(frozen=True, slots=True)
class AssetResolution:
    """Keep sensor sampling separate from the delivered raster/display grid.

    ``detail_limit_m`` is a conservative sampling bound, not measured resolving
    power or positional accuracy. Unknown native GSD remains None. A finer
    display grid cannot improve this bound; panchromatic GSD must not be used
    as the native spectral resolution of multispectral bands.
    """

    scene_id: str
    asset_key: str
    product_kind: str
    native_gsd_m: float | None
    grid_spacing_m: tuple[float, float] | None
    detail_limit_m: float | None
    acquisition_utc: str
    platform: str


def describe_asset(item: dict[str, Any], asset: str = "visual") -> AssetResolution:
    """Inspect a STAC asset without opening its pixels or inventing native GSD."""
    metadata = item.get("assets", {}).get(asset)
    properties = item.get("properties", {})
    if not isinstance(metadata, dict) or "image/tiff" not in str(metadata.get("type", "")):
        raise ValueError("Select a numeric GeoTIFF asset, not a preview or vector mask")
    affine = metadata.get("proj:transform", properties.get("proj:transform"))
    epsg = metadata.get("proj:epsg", properties.get("proj:epsg"))
    code = metadata.get("proj:code", properties.get("proj:code"))
    crs = CRS.from_user_input(code or epsg) if (code or epsg) is not None else None
    spacing = None
    if isinstance(affine, list) and len(affine) in (6, 9):
        if (
            not all(
                isinstance(v, (float, int)) and not isinstance(v, bool) and math.isfinite(v)
                for v in affine
            )
            or affine[1] != 0
            or affine[3] != 0
            or affine[0] <= 0
            or affine[4] >= 0
        ):
            raise ValueError("Expected a finite north-up image transform")
        if crs is not None and crs.is_projected and crs.linear_units in {"metre", "meter"}:
            spacing = float(affine[0]), abs(float(affine[4]))
    native = _positive(metadata.get("gsd"))
    kind = "spectral" if "reflectance" in metadata.get("roles", []) else "image"
    if item.get("collection") == "sentinel-2-c1-l2a":
        if native is None:
            bands = metadata.get("raster:bands", [])
            resolutions = [
                _positive(b.get("spatial_resolution")) for b in bands if isinstance(b, dict)
            ]
            if resolutions and all(r is not None for r in resolutions):
                native = max(r for r in resolutions if r is not None)
        kind = (
            "rendered_rgb" if asset == "visual" else "categorical" if asset == "scl" else "spectral"
        )
    elif asset in {"pan_analytic", "visual", "ms_analytic"} and str(
        properties.get("platform", "")
    ).startswith(("WV", "GE")):
        kind = {
            "pan_analytic": "panchromatic",
            "visual": "rendered_pansharpened_rgb",
            "ms_analytic": "multispectral",
        }[asset]
        if asset in {"pan_analytic", "visual"}:
            scene_native = _positive(properties.get("gsd"))
            native = (
                max(native, scene_native) if native and scene_native else native or scene_native
            )
        # The scene's GSD describes pan sampling, not native multispectral bands.
    detail = max(native, *(spacing or (native,))) if native is not None else None
    if (
        asset == "visual"
        and kind == "rendered_pansharpened_rgb"
        and "pan_analytic" in item.get("assets", {})
    ):
        pan_detail = describe_asset(item, "pan_analytic").detail_limit_m
        if pan_detail is not None and detail is not None:
            detail = max(detail, pan_detail)
    return AssetResolution(
        str(item.get("id", "")),
        asset,
        kind,
        native,
        spacing,
        detail,
        str(properties.get("datetime", "unknown")),
        str(properties.get("platform", "unknown")),
    )


def select_finest(
    search: ImagerySearch,
    *,
    asset: str = "pan_analytic",
    maximum_detail_m: float | None = None,
    allow_incomplete: bool = False,
) -> dict[str, Any]:
    """Choose finest declared native detail for the same asset across matching scenes.

    This ranks the specified event/date/AOI search, not all imagery worldwide.
    Search caps and missing GSD cannot silently establish a finest-image claim.
    Ties use acquisition time then item ID; cloud/validity still need inspection.
    """
    if not search.complete and not allow_incomplete:
        raise ValueError("Search is incomplete; expand its cap before claiming finest available")
    if maximum_detail_m is not None and _positive(maximum_detail_m) is None:
        raise ValueError("maximum_detail_m must be finite and positive")
    ranked = []
    for item in search.items:
        if asset not in item.get("assets", {}):
            continue
        metadata = describe_asset(item, asset)
        if metadata.detail_limit_m is None:
            continue
        if maximum_detail_m is None or metadata.detail_limit_m <= maximum_detail_m:
            ranked.append(
                (metadata.detail_limit_m, metadata.acquisition_utc, metadata.scene_id, item)
            )
    if not ranked:
        raise ValueError(
            "No matching asset has verified native GSD within the requested detail limit"
        )
    return deepcopy(min(ranked, key=lambda x: x[:3])[3])


class OrbitalPVImageryClient:
    """Sentinel-2 and event-limited Maxar satellite imagery using Orbital PV.

    Public native pixels are read and persisted by Orbital PV, not copied
    implementations. No accounts, purchases, tasking or commercial entitlements
    are created. Maxar Open Data carries CC-BY-NC-4.0 at the event level;
    preserve original lower-level licence declarations as well.
    """

    def __init__(self, http: HTTPClient) -> None:
        self.http = http

    def search_sentinel(
        self,
        bounds_wgs84: Bounds,
        *,
        time_min: str,
        time_max: str,
        max_cloud_cover: float = 20.0,
        max_items: int = 100,
        cache_path: str | None = None,
    ) -> ImagerySearch:
        """Delegate bounded search and its query-bound cache to Orbital PV."""
        validate_bounds(bounds_wgs84)
        _interval(time_min, time_max)
        opv = _orbital()
        with opv.Sentinel2GroundConnector() as connector:
            document = connector.search(
                bbox=bounds_wgs84,
                time_min=time_min,
                time_max=time_max,
                max_cloud_cover=max_cloud_cover,
                max_items=max_items,
                cache_path=cache_path,
            )
        complete = not document.get("context", {}).get("limit_reached", True)
        return ImagerySearch(
            "sentinel-2-c1-l2a",
            tuple(document["features"]),
            bounds_wgs84,
            time_min,
            time_max,
            complete,
            (),
            document,
        )

    def events(self) -> dict[str, Any]:
        """List the provider's explicit public event catalogue and licence."""
        return object_value(self.http.get_json(f"{MAXAR_ROOT}catalog.json", {}).value)

    def search_maxar(
        self,
        event: str,
        bounds_wgs84: Bounds,
        *,
        time_min: str,
        time_max: str,
        acquisition_ids: tuple[str, ...] | None = None,
        maximum_documents: int = 512,
        maximum_items: int = 500,
    ) -> ImagerySearch:
        """Traverse one bounded event, pruning by collection extent and dates.

        Filters are inclusive UTC instants. An optional acquisition selection
        narrows the claim to those acquisitions. Any traversal/item budget breach
        raises, so a partial traversal cannot masquerade as a finest selection.
        Full scene/asset metadata and every visited document's receipt survive.
        """
        validate_bounds(bounds_wgs84)
        start, stop = _interval(time_min, time_max)
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,119}", event):
            raise ValueError("Choose an event ID from events()")
        if any(type(v) is not int or v < 1 for v in (maximum_documents, maximum_items)):
            raise ValueError("Catalogue budgets must be positive integers")
        if acquisition_ids is not None and (
            not acquisition_ids
            or any(not re.fullmatch(r"[0-9A-F]{16}", x) for x in acquisition_ids)
        ):
            raise ValueError("acquisition_ids must contain provider 16-character uppercase IDs")
        url = f"{MAXAR_ROOT}{event}/collection.json"
        queue: deque[tuple[str, str | None]] = deque([(url, None)])
        seen: set[str] = set()
        items: list[dict[str, Any]] = []
        records: list[RequestRecord] = []
        event_metadata: dict[str, Any] = {}
        while queue:
            current, parent_license = queue.popleft()
            if current in seen:
                raise ValueError("Repeated catalogue link; refusing an ambiguous traversal")
            if len(seen) >= maximum_documents:
                raise ValueError("Catalogue exceeds maximum_documents; narrow dates/acquisitions")
            seen.add(current)
            response = self.http.get_json(_https(current, maxar_only=True), {})
            document = cast(dict[str, Any], object_value(response.value))
            records.append(response.record)
            if current == url:
                if document.get("id") != event or document.get("type") != "Collection":
                    raise ValueError("Unexpected Maxar event collection")
                event_metadata = deepcopy(document)
                if acquisition_ids is not None:
                    available = {
                        match[1]
                        for link in document.get("links", [])
                        if (
                            match := re.search(
                                r"/([0-9A-F]{16})_collection.json$", link.get("href", "")
                            )
                        )
                    }
                    if not set(acquisition_ids) <= available:
                        raise ValueError(
                            "An explicitly requested acquisition is absent from this event"
                        )
            if document.get("type") == "Feature":
                item = deepcopy(document)
                bbox = item.get("bbox")
                properties = item.get("properties", {})
                if not isinstance(bbox, list) or len(bbox) != 4:
                    raise ValueError("Maxar item has no geographic bbox")
                bbox = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
                validate_bounds(bbox)
                if (
                    not _intersects(bounds_wgs84, bbox)
                    or not start <= _utc(properties["datetime"]) <= stop
                ):
                    continue
                if len(items) >= maximum_items:
                    raise ValueError("Catalogue exceeds maximum_items; narrow the search")
                for value in item.get("assets", {}).values():
                    value["href"] = _https(urljoin(current, value["href"]), maxar_only=True)
                item["properties"]["edi:open_data"] = {
                    "event": event,
                    "event_url": url,
                    "event_license": event_metadata.get("license"),
                    "acquisition_license": parent_license,
                    "item_url": current,
                }
                items.append(item)
                continue
            if document.get("type") not in {"Collection", "Catalog"}:
                raise ValueError("Unexpected static STAC document")
            extent = document.get("extent", {})
            boxes = extent.get("spatial", {}).get("bbox", [])
            if boxes and not any(_intersects(bounds_wgs84, tuple(box)) for box in boxes):
                continue
            intervals = extent.get("temporal", {}).get("interval", [])
            if intervals and not any(
                (end is None or _utc(end) >= start) and (begin is None or _utc(begin) <= stop)
                for begin, end in intervals
            ):
                continue
            for link in document.get("links", []):
                if link.get("rel") not in {"child", "item"}:
                    continue
                target = _https(urljoin(current, link["href"]), maxar_only=True)
                if not target.startswith(f"{MAXAR_ROOT}{event}/"):
                    raise ValueError("Catalogue link leaves the selected public event")
                if current == url and acquisition_ids is not None:
                    match = re.search(r"/([0-9A-F]{16})_collection.json$", target)
                    if match is None or match[1] not in acquisition_ids:
                        continue
                queue.append((target, document.get("license")))
        identities = [i.get("id") for i in items]
        if len(identities) != len(set(identities)):
            raise ValueError("Duplicate item IDs in the event catalogue")
        return ImagerySearch(
            "maxar-open-data",
            tuple(items),
            bounds_wgs84,
            time_min,
            time_max,
            True,
            tuple(records),
            {"event": event_metadata, "acquisition_ids": acquisition_ids},
        )

    def read_image(
        self,
        item: dict[str, Any],
        bounds_wgs84: Bounds,
        *,
        asset: str = "visual",
        maximum_samples: int = 4_000_000,
    ) -> Any:
        """Use Orbital PV's native COG reader; return its full GroundImage object.

        ``maximum_samples`` bounds bands times rows times columns before reading.
        GDAL may transfer whole compressed blocks; this is not a network-byte
        limit. No resize, overview selection, sharpening or implicit cloud mask
        is requested. Declared grid spacing is checked against the actual TIFF.
        """
        validate_bounds(bounds_wgs84)
        metadata = describe_asset(item, asset)
        _https(item["assets"][asset]["href"])
        image = _orbital().read_ground_image(
            item, bbox=bounds_wgs84, asset=asset, max_pixels=maximum_samples
        )
        declared = item["assets"][asset]
        properties = item.get("properties", {})
        crs = declared.get("proj:code", properties.get("proj:code")) or declared.get(
            "proj:epsg", properties.get("proj:epsg")
        )
        if crs is not None and CRS.from_user_input(crs) != CRS.from_user_input(image.crs):
            raise ValueError("Actual TIFF CRS differs from its STAC metadata")
        if metadata.grid_spacing_m is not None:
            actual = image.transform[0], abs(image.transform[4])
            if any(
                not math.isclose(x, y, rel_tol=1e-9, abs_tol=1e-9)
                for x, y in zip(actual, metadata.grid_spacing_m, strict=True)
            ):
                raise ValueError("Actual TIFF spacing differs from its STAC metadata")
        return image


def load_satellite_image(path: str, *, maximum_samples: int = 4_000_000) -> Any:
    """Delegate checksum, metadata, grid and mask validation to Orbital PV."""
    return _orbital().load_ground_image(path, max_pixels=maximum_samples)
