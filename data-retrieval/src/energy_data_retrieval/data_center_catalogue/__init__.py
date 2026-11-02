"""Global data center facility and exact equipment catalogue."""

from energy_data_retrieval.pv_catalogue.catalogue import load_records

from .catalogue import (
    SCHEMA,
    build_parquet,
    capacity_summary,
    stable_id,
    upsert_records,
    validate_catalogue,
)

__all__ = [
    "SCHEMA",
    "build_parquet",
    "capacity_summary",
    "load_records",
    "stable_id",
    "upsert_records",
    "validate_catalogue",
]
