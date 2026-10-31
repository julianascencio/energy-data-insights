"""Reviewable count summaries and candidate CSV/GeoJSON exports."""

from __future__ import annotations

import json
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
from typing import Any

from energy_analysis.module_counting.pipeline import ImageModuleStudy
from energy_methods.pv_module_counting import module_candidates_geojson


def counting_summary(study: ImageModuleStudy) -> dict[str, Any]:
    """Summarize candidate/exclusion counts without inventing an accuracy estimate."""
    result = study.result
    frame = result.to_frame()
    return {
        "interpretation": "Experimental image-grid estimate, not a validated module inventory",
        "estimated_modules": result.estimated_modules,
        "regular_candidates": result.regular_candidates,
        "review_candidates": result.review_candidates,
        "excluded_grid_positions": sum(c.status == "excluded" for c in result.cells),
        "table_counts": [
            {
                **asdict(table),
                "candidates": int(((frame.table == table.id) & (frame.status != "excluded")).sum()),
            }
            for table in result.tables
        ],
        "rejected_tables": list(result.rejected_tables),
        "parameters": asdict(result.config),
        "source_metadata": study.source_metadata,
        "site_scope": study.site_feature,
        "versions": {
            name: version(name) for name in ("energy-methods", "energy-analysis", "numpy", "scipy")
        },
        "limitations": [
            "Candidate counts are not ground-truth module counts or plant capacity.",
            "Colour/layout thresholds need review for each imaging domain.",
            "Excluded grid positions are not proof of missing or failed modules.",
            "No capture date or native GSD is inferred from rendered image dimensions.",
            "Counts cover the supplied polygon, not necessarily the complete installation.",
        ],
    }


def export_counting_study(study: ImageModuleStudy, directory: str | Path) -> Path:
    """Write CSV, GeoJSON and provenance JSON to a fresh external directory."""
    destination = Path(directory)
    destination.mkdir(parents=True, exist_ok=False)
    study.result.to_frame().to_csv(destination / "module_candidates.csv", index=False)
    (destination / "module_candidates.geojson").write_text(
        json.dumps(module_candidates_geojson(study.result, study.bounds_wgs84), indent=2) + "\n"
    )
    (destination / "count_summary.json").write_text(
        json.dumps(counting_summary(study), indent=2, ensure_ascii=False) + "\n"
    )
    return destination
