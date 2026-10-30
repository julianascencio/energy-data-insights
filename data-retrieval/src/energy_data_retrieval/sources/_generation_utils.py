"""Strict tabular parsing shared by file-based generation connectors."""

from __future__ import annotations

import csv
import hashlib
import io
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from pytz.exceptions import AmbiguousTimeError, NonExistentTimeError

from energy_data_retrieval.transport import RetrievalError


def bounded_csv(
    content: str | bytes, *, maximum_rows: int = 1_000_000, skiprows: list[int] | None = None
) -> pd.DataFrame:
    """Read bounded, rectangular CSV records without pandas' inferred index.

    ``skiprows`` refers to logical CSV records, including any provider metadata
    records before the header. Quoted multiline fields therefore cannot change
    which records are skipped or cause the validation and parsing to disagree.
    """
    if type(maximum_rows) is not int or not 1 <= maximum_rows <= 10_000_000:
        raise ValueError("maximum_rows must be an integer in 1..10,000,000")
    try:
        text = (
            content.decode("utf-8-sig") if isinstance(content, bytes) else content.lstrip("\ufeff")
        )
    except UnicodeDecodeError:
        raise RetrievalError("Expected a UTF-8 generation CSV") from None
    if not text.strip() or text.lstrip().startswith(("<", "<?")):
        raise RetrievalError("Expected CSV observations, not an empty or markup response")
    if len(text.encode("utf-8")) > 128 * 1024**2:
        raise RetrievalError("CSV exceeds the parser's 128 MiB limit")
    skipped = set(skiprows or [])
    if any(type(index) is not int or index < 0 for index in skipped):
        raise ValueError("skiprows must contain nonnegative CSV record indices")
    normalized = io.StringIO()
    writer = csv.writer(normalized)
    header = None
    row_count = 0
    try:
        for index, row in enumerate(csv.reader(io.StringIO(text), strict=True)):
            if index in skipped or not row:
                continue
            if header is None:
                if len(set(row)) != len(row):
                    raise RetrievalError("CSV contains duplicate column names")
                header = row
            else:
                row_count += 1
                if row_count > maximum_rows:
                    raise RetrievalError("Generation CSV exceeds maximum_rows")
                if len(row) != len(header):
                    raise RetrievalError("Generation CSV row does not match its header width")
            writer.writerow(row)
    except csv.Error:
        raise RetrievalError("Invalid generation CSV") from None
    if header is None:
        raise RetrievalError("Generation CSV has no valid header")
    normalized.seek(0)
    try:
        frame = pd.read_csv(normalized, nrows=maximum_rows + 1)
    except (ValueError, pd.errors.ParserError):
        raise RetrievalError("Invalid generation CSV") from None
    if len(frame) > maximum_rows:
        raise RetrievalError("Generation CSV exceeds maximum_rows")
    return frame


def numeric(values: pd.Series, name: str) -> pd.Series:
    """Preserve missing and signed observations; reject invalid/infinite values."""
    if values.map(lambda value: isinstance(value, (bool, np.bool_))).any():
        raise RetrievalError(f"{name} contains boolean measurements")
    try:
        result = pd.to_numeric(values, errors="raise").astype("float64")
    except (ValueError, TypeError):
        raise RetrievalError(f"{name} contains nonnumeric measurements") from None
    if np.isinf(result).any():
        raise RetrievalError(f"{name} contains infinite measurements")
    return result


def utc_labels(
    values: pd.Series,
    *,
    source_timezone: str | None,
    timestamp_format: str | None = None,
) -> pd.Series:
    """Convert explicit source time semantics; fail on ambiguous local labels."""
    try:
        try:
            # pandas 2 warns and produces object dtype for mixed UTC offsets;
            # newer versions reject them. Both cases need the same aware-only
            # fallback, without treating naive values as UTC by accident.
            with warnings.catch_warnings():
                warnings.simplefilter("error", FutureWarning)
                parsed = pd.to_datetime(values, errors="raise", format=timestamp_format)
        except (ValueError, FutureWarning) as error:
            scalar_values = values.map(
                lambda value: pd.to_datetime(value, errors="raise", format=timestamp_format)
            )
            if scalar_values.isna().any():
                raise ValueError("Missing timestamp") from None
            aware = scalar_values.map(lambda value: value.utcoffset() is not None)
            if not aware.all():
                if aware.any():
                    raise ValueError("Cannot mix offset-aware and naive timestamp labels") from None
                raise ValueError(str(error)) from None
            parsed = pd.to_datetime(scalar_values, errors="raise", utc=True)
        else:
            if parsed.dt.tz is not None and not isinstance(values.dtype, pd.DatetimeTZDtype):
                # With format="ISO8601", some pandas versions silently attach
                # the first row's offset to later naive strings. Verify the
                # original labels before accepting an aware vector result.
                aware = values.map(
                    lambda value: (
                        pd.to_datetime(value, errors="raise", format=timestamp_format).utcoffset()
                        is not None
                    )
                )
                if not aware.all():
                    raise ValueError("Cannot mix offset-aware and naive timestamp labels")
        if parsed.isna().any():
            raise ValueError("Missing timestamp")
        if parsed.dt.tz is None:
            if source_timezone is None:
                raise ValueError("Naive source labels need an explicit timezone")
            zone: str | timezone = source_timezone
            if source_timezone.startswith(("+", "-")):
                offset = datetime.fromisoformat("2000-01-01T00:00:00" + source_timezone).utcoffset()
                if offset is None:
                    raise ValueError("Invalid fixed offset")
                zone = timezone(offset)
            parsed = parsed.dt.tz_localize(zone, ambiguous="raise", nonexistent="raise")
        return parsed.dt.tz_convert("UTC")
    except (
        ValueError,
        TypeError,
        AttributeError,
        KeyError,
        AmbiguousTimeError,
        NonExistentTimeError,
    ) as error:
        raise RetrievalError(f"Invalid or ambiguous source timestamps: {error}") from None


def unique_observations(frame: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Collapse exact repeats, never average conflicting observations."""
    attrs = dict(frame.attrs)
    frame = frame.drop_duplicates()
    if frame.duplicated(keys).any():
        raise RetrievalError("Source returned conflicting observations for the same key")
    frame = frame.sort_values(keys).reset_index(drop=True)
    frame.attrs.update(attrs)
    return frame


def local_export(path: Path, *, maximum_bytes: int = 128 * 1024**2) -> tuple[bytes, dict[str, str]]:
    """Read a bounded local export and retain its byte identity, without its path."""
    with Path(path).open("rb") as stream:
        content = stream.read(maximum_bytes + 1)
    if len(content) > maximum_bytes:
        raise RetrievalError("Local export exceeds maximum_bytes")
    return content, {
        "input_filename": Path(path).name,
        "input_sha256": hashlib.sha256(content).hexdigest(),
        "access_method": "user_downloaded_provider_export",
    }
