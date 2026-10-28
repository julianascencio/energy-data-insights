"""Partition-sized Parquet outputs with verifiable, restart-safe provenance."""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import tempfile
from collections.abc import Callable, Iterable, Iterator, Mapping
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

from energy_data_retrieval.transport import JSONValue, atomic_bytes


@dataclass(frozen=True, slots=True)
class Artifact:
    filename: str
    sha256: str
    bytes: int
    rows: int
    request_fingerprint: str


def sha256_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fingerprint(metadata: Mapping[str, JSONValue]) -> str:
    """Fingerprint only non-secret request semantics and source/time conventions."""
    return hashlib.sha256(
        json.dumps(metadata, sort_keys=True, allow_nan=False).encode()
    ).hexdigest()


def existing_artifact(path: Path, request_fingerprint: str) -> Artifact | None:
    manifest_path = path.with_suffix(path.suffix + ".json")
    if not path.exists() and not manifest_path.exists():
        return None
    if not path.exists() or not manifest_path.exists():
        raise ValueError(
            "Incomplete prior output; inspect and remove or choose a new output directory"
        )
    saved = json.loads(manifest_path.read_text())
    record = Artifact(**saved["artifact"])
    if (
        record.filename != path.name
        or record.request_fingerprint != request_fingerprint
        or record.bytes != path.stat().st_size
        or record.sha256 != sha256_file(path)
    ):
        raise ValueError("Existing output does not match the requested snapshot or its checksum")
    return record


def write_parquet(
    frame: pd.DataFrame,
    path: Path,
    *,
    request: Mapping[str, JSONValue],
    provenance: Mapping[str, JSONValue],
) -> Artifact:
    """Publish a Parquet partition, then its manifest; refuse mismatched overwrites.

    A crash between the two atomic publications is detected on restart. The user
    must inspect that incomplete pair; an unaudited file is never silently reused.
    """
    identity = fingerprint(request)
    previous = existing_artifact(path, identity)
    if previous is not None:
        return previous
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    os.close(descriptor)
    temporary = Path(name)
    try:
        frame.to_parquet(temporary, engine="pyarrow", compression="zstd", index=False)
        with temporary.open("rb") as stream:
            os.fsync(stream.fileno())
        record = Artifact(
            path.name, sha256_file(temporary), temporary.stat().st_size, len(frame), identity
        )
        temporary.replace(path)
        atomic_bytes(
            path.with_suffix(path.suffix + ".json"),
            json.dumps(
                {
                    "artifact": asdict(record),
                    "request": dict(request),
                    "provenance": dict(provenance),
                },
                ensure_ascii=False,
                indent=2,
                allow_nan=False,
            ).encode(),
        )
        return record
    finally:
        temporary.unlink(missing_ok=True)


def bounded_map[Input, Output](
    function: Callable[[Input], Output],
    items: Iterable[Input],
    *,
    workers: int = 2,
) -> Iterator[Output]:
    """Yield completion-order results with at most ``workers`` tasks in flight."""
    if not 1 <= workers <= 8:
        raise ValueError("workers must be between 1 and 8")
    source = iter(items)
    pending: set[Future[Output]] = set()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        for _ in range(workers):
            try:
                pending.add(executor.submit(function, next(source)))
            except StopIteration:
                break
        while pending:
            completed, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in completed:
                yield future.result()
                with contextlib.suppress(StopIteration):
                    pending.add(executor.submit(function, next(source)))
