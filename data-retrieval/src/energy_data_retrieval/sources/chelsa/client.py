"""Crop pinned CHELSA v2.1 climatology COGs without downloading global rasters."""

from __future__ import annotations

import hashlib
import io
import json
import math
import re
import time
from collections import OrderedDict
from datetime import UTC, datetime
from pathlib import Path

import httpx
import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds

from energy_data_retrieval.transport import RetrievalError

CHELSA_BASE_URL = "https://os.unil.cloud.switch.ch/chelsa02/chelsa/global/climatologies"
REFERENCE_IDS = ("chelsa_2021_climatologies", "karger_2017_chelsa")


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class RangeReader(io.RawIOBase):
    """Seekable HTTP ranges with exact response validation and bounded memory/I/O.

    The source-specific caller fixes the URL, size and strong ETag. Every read
    carries If-Match; an ETag is a version validator, not a SHA-256 checksum.
    No redirects or full-body fallbacks are accepted. The caller owns HTTP.
    """

    def __init__(
        self,
        http: httpx.Client,
        url: str,
        size: int,
        etag: str,
        *,
        block_size: int = 1_048_576,
        maximum_bytes: int = 64_000_000,
    ) -> None:
        self.http, self.url, self.length, self.etag = http, url, size, etag
        self.block_size, self.maximum_bytes = block_size, maximum_bytes
        self.position = 0
        self.transferred_bytes = 0
        self.cache: OrderedDict[int, bytes] = OrderedDict()

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence not in (0, 1, 2):
            raise ValueError("Invalid seek origin")
        position = offset + (0 if whence == 0 else self.position if whence == 1 else self.length)
        if position < 0:
            raise ValueError("Cannot seek before the source")
        self.position = position
        return position

    def _block(self, number: int) -> bytes:
        if number in self.cache:
            self.cache.move_to_end(number)
            return self.cache[number]
        start = number * self.block_size
        stop = min(start + self.block_size, self.length) - 1
        length = stop - start + 1
        for attempt in range(3):
            if self.transferred_bytes + length > self.maximum_bytes:
                raise RetrievalError("COG request exceeded its regional transfer budget")
            try:
                with self.http.stream(
                    "GET",
                    self.url,
                    follow_redirects=False,
                    headers={
                        "Range": f"bytes={start}-{stop}",
                        "If-Match": self.etag,
                        "Accept-Encoding": "identity",
                    },
                ) as response:
                    if response.status_code in (429, 500, 502, 503, 504):
                        raise httpx.ReadError("Retryable COG response")
                    if (
                        response.status_code != 206
                        or response.headers.get("content-range")
                        != f"bytes {start}-{stop}/{self.length}"
                        or response.headers.get("etag") != self.etag
                    ):
                        raise RetrievalError("COG range, version or response status changed")
                    data = bytearray()
                    for chunk in response.iter_bytes(64 * 1024):
                        self.transferred_bytes += len(chunk)
                        data.extend(chunk)
                        if len(data) > length or self.transferred_bytes > self.maximum_bytes:
                            raise RetrievalError("COG range exceeded its declared byte limit")
                    if len(data) != length:
                        raise RetrievalError("Incomplete COG range response")
                self.cache[number] = bytes(data)
                if len(self.cache) > 8:
                    self.cache.popitem(last=False)
                return self.cache[number]
            except httpx.TransportError:
                if attempt == 2:
                    raise RetrievalError("COG regional retrieval failed") from None
                time.sleep(1)
        raise AssertionError("Unreachable retry state")

    def read(self, size: int = -1) -> bytes:
        if self.closed:
            raise ValueError("Read from a closed COG")
        if size < 0:
            size = self.length - self.position
        if size > 32_000_000:
            raise RetrievalError("Refusing an unbounded raster read")
        end = min(self.position + size, self.length)
        parts = []
        while self.position < end:
            number = self.position // self.block_size
            block = self._block(number)
            offset = self.position % self.block_size
            piece = block[offset : offset + end - self.position]
            parts.append(piece)
            self.position += len(piece)
        return b"".join(parts)


class CHELSAClient:
    """Explicit acquisition of native tas/pr windows for baseline 1981-2010."""

    def __init__(self, http: httpx.Client) -> None:
        self.http = http

    def download_window(
        self,
        directory: Path,
        variable: str,
        month: int,
        bounds: tuple[float, float, float, float],
        *,
        expected_etag: str | None = None,
        expected_pixels_sha256: str | None = None,
    ) -> tuple[Path, dict]:
        if variable not in {"tas", "pr"} or type(month) is not int or not 1 <= month <= 12:
            raise ValueError("Select tas/pr and an integer month in 1..12")
        if (
            len(bounds) != 4
            or not np.isfinite(bounds).all()
            or not -180 <= bounds[0] < bounds[2] <= 180
            or not -90 <= bounds[1] < bounds[3] <= 90
        ):
            raise ValueError("Expected finite west,south,east,north bounds")
        if (bounds[2] - bounds[0]) * (bounds[3] - bounds[1]) * 120**2 > 10_000_000:
            raise ValueError("Requested region exceeds ten million native cells")
        name = f"CHELSA_{variable}_{month:02d}_1981-2010_V.2.1.tif"
        url = f"{CHELSA_BASE_URL}/{variable}/1981-2010/{name}"
        path = Path(directory) / name
        manifest = path.with_suffix(".tif.subset.json")
        if path.exists() or manifest.exists():
            if not path.exists() or not manifest.exists():
                raise ValueError("Incomplete CHELSA subset checkpoint")
            record = json.loads(manifest.read_text())
            if (
                record["url"] != url
                or record["requested_bounds"] != list(bounds)
                or record["sha256"] != sha256(path)
                or (expected_etag is not None and record["etag"] != expected_etag)
                or (
                    expected_pixels_sha256 is not None
                    and record["pixels_sha256"] != expected_pixels_sha256
                )
            ):
                raise ValueError("CHELSA subset checkpoint or source pin changed")
            return path, record
        head = self.http.head(url, follow_redirects=False)
        if head.status_code != 200:
            raise RetrievalError("CHELSA metadata request failed")
        etag = head.headers.get("etag", "")
        if not re.fullmatch(r'"[0-9a-f]{1,64}(?:-\d+)?"', etag):
            raise RetrievalError("CHELSA source needs a strong version ETag")
        if expected_etag is not None and etag != expected_etag:
            raise ValueError("CHELSA source version differs from the pinned ETag")
        size = int(head.headers["content-length"])
        if not 0 < size <= 1_000_000_000:
            raise RetrievalError("Unexpected CHELSA source size")
        readers = []

        def opener(filename, mode="rb"):
            if filename != name or mode not in ("r", "rb"):
                raise FileNotFoundError(filename)
            reader = RangeReader(self.http, url, size, etag)
            readers.append(reader)
            return reader

        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tif.partial")
        try:
            with (
                rasterio.Env(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"),
                rasterio.open(name, opener=opener) as source,
            ):
                tags = source.tags()
                unit = "K" if variable == "tas" else "kg m-2 month-1"
                if (
                    source.crs != rasterio.crs.CRS.from_epsg(4326)
                    or source.count != 1
                    or tags.get("version") != "2.1"
                    or tags.get("datetime") != "1981-2010"
                    or tags.get("variable") != variable
                    or tags.get("variable_unit") != unit
                    or source.transform.b != 0
                    or source.transform.d != 0
                    or not np.isclose(source.transform.a, 1 / 120)
                    or not np.isclose(source.transform.e, -1 / 120)
                    or source.nodata != 65535
                    or source.dtypes != ("uint16",)
                    or not np.isfinite([source.scales[0], source.offsets[0]]).all()
                    or source.scales[0] <= 0
                ):
                    raise ValueError("Unexpected CHELSA units, baseline, encoding or grid")
                floating = from_bounds(*bounds, transform=source.transform)
                row, col = math.floor(floating.row_off), math.floor(floating.col_off)
                bottom = math.ceil(floating.row_off + floating.height)
                right = math.ceil(floating.col_off + floating.width)
                if row < 0 or col < 0 or bottom > source.height or right > source.width:
                    raise ValueError("Region extends outside the CHELSA source")
                window = Window.from_slices((row, bottom), (col, right))
                values = source.read(1, window=window)
                pixel_hash = hashlib.sha256(values.astype("<u2").tobytes()).hexdigest()
                if expected_pixels_sha256 is not None and pixel_hash != expected_pixels_sha256:
                    raise ValueError("CHELSA subset pixels differ from the reviewed data")
                transform = source.window_transform(window)
                profile = dict(
                    driver="GTiff",
                    width=values.shape[1],
                    height=values.shape[0],
                    count=1,
                    dtype="uint16",
                    crs=source.crs,
                    transform=transform,
                    nodata=source.nodata,
                    compress="deflate",
                    tiled=True,
                )
                with rasterio.open(temporary, "w", **profile) as target:
                    target.write(values, 1)
                    target.scales, target.offsets = source.scales, source.offsets
                    target.update_tags(**tags)
                record = {
                    "url": url,
                    "etag": etag,
                    "source_size_bytes": size,
                    "source_shape": list(source.shape),
                    "source_transform": list(source.transform),
                    "requested_bounds": list(bounds),
                    "shape": list(values.shape),
                    "transform": list(transform),
                    "scale": source.scales[0],
                    "offset": source.offsets[0],
                    "units": unit,
                    "baseline": [1981, 2010],
                    "pixels_sha256": pixel_hash,
                    "retrieved_at_utc": datetime.now(UTC).isoformat(),
                    "transfer_bytes": sum(r.transferred_bytes for r in readers),
                    "license": "CC0 1.0",
                    "reference_ids": list(REFERENCE_IDS),
                }
            temporary.replace(path)
            record.update(sha256=sha256(path), size_bytes=path.stat().st_size)
            manifest.write_text(json.dumps(record, indent=2) + "\n")
        finally:
            temporary.unlink(missing_ok=True)
            for reader in readers:
                reader.close()
        return path, record
