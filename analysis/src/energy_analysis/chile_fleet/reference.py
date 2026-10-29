"""Fleet accounting for externally supplied frozen generation references."""

from __future__ import annotations

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from .config import utc_datetime
from .fleet import ComparisonConfig, compare_site, summarize_fleet
from .io import (
    SiteDataSource,
    fingerprint,
    load_sites,
    row_mapping,
    validate_output_location,
    write_fleet_csv,
    write_json,
)


def compare_references(
    hourly_path: Path,
    sites_path: Path,
    output_path: Path,
    *,
    start: datetime,
    end: datetime,
    reference: Literal[
        "expected_mwh", "expected_final_mwh", "expected_heldout_mwh"
    ] = "expected_mwh",
    minimum_reference_coverage: float = 0.8,
    relative_tolerance: float = 0.2,
    data_kind: Literal["unspecified", "synthetic", "observational"] = "unspecified",
) -> dict[str, object]:
    """Use supplied expected values unchanged; never fit or fill a missing reference."""
    start, end = utc_datetime(start), utc_datetime(end)
    if data_kind not in {"unspecified", "synthetic", "observational"}:
        raise ValueError("data_kind must be unspecified, synthetic or observational")
    if start >= end:
        raise ValueError("Start must precede the exclusive end")
    if output_path.exists():
        raise FileExistsError(f"Refusing to overwrite comparison: {output_path}")
    validate_output_location(output_path, hourly_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    registry = load_sites(sites_path)
    if registry.empty:
        raise ValueError("The site registry is empty")
    source = SiteDataSource(hourly_path)
    settings = ComparisonConfig(minimum_reference_coverage, relative_tolerance)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output_path.name}-", dir=output_path.parent))
    try:
        rows: list[dict[str, object]] = []
        for site in row_mapping(registry):
            frame = source.site(str(site["site_id"]))
            if reference not in frame:
                raise ValueError(f"Input is missing requested frozen reference column: {reference}")
            frame = frame.loc[(frame.timestamp >= start) & (frame.timestamp < end)].copy()
            frame["expected_mwh"] = frame[reference]
            row = compare_site(frame, settings)
            row.update({key: site.get(key, "") for key in ("site_id", "name", "region")})
            rows.append(row)
        fleet = pd.DataFrame(rows)
        fleet.to_parquet(temporary / "fleet.parquet", index=False, compression="zstd")
        write_fleet_csv(fleet, temporary / "fleet.csv")
        summary = summarize_fleet(fleet)
        write_json(temporary / "summary.json", summary)
        result: dict[str, object] = {
            "schema": "energy-data-insights-frozen-reference-comparison-v1",
            "complete": True,
            "data_kind": data_kind,
            "model_retrained": False,
            "expected_values_modified": False,
            "start_inclusive": start,
            "end_exclusive": end,
            "reference_column": reference,
            "minimum_reference_coverage": minimum_reference_coverage,
            "relative_tolerance": relative_tolerance,
            "inputs": {"hourly": fingerprint(hourly_path), "sites": fingerprint(sites_path)},
            "summary": summary,
            "scope": (
                "Supplied frozen predictions are used unchanged. This command performs energy "
                "accounting only; it does not recreate training support or operational states."
            ),
        }
        write_json(temporary / "manifest.json", result)
        temporary.rename(output_path)
        return result
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
