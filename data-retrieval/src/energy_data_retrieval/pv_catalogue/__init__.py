"""Versioned PV equipment and project catalogues with explicit field evidence."""

from .catalogue import (
    SCHEMA,
    build_parquet,
    load_records,
    stable_id,
    upsert_records,
    validate_catalogue,
    validate_record,
    write_records,
)

__all__ = [
    "SCHEMA",
    "build_parquet",
    "load_records",
    "stable_id",
    "upsert_records",
    "validate_catalogue",
    "validate_record",
    "write_records",
]
