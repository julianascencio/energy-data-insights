"""Publish an atomic, read-only report snapshot from a completed analysis."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import cast

import pandas as pd

from energy_methods.references import (
    PRIMARY_REFERENCE_ID,
    get_references,
    references_bibtex,
    references_markdown,
)

from ..fleet import summarize_fleet
from ..io import json_safe, row_mapping, write_json
from .rendering import fleet_page, publication_drafts, site_page

RUN_SCHEMA = "energy-data-insights-chile-fleet-run-v1"
COMPARISON_SCHEMA = "energy-data-insights-frozen-reference-comparison-v1"


def _hash(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class _Snapshot:
    """Hash only consumed files; never trust arbitrary source paths in a manifest."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.files: dict[str, dict[str, object]] = {}
        self.expected: dict[str, str] = {}

    def record(self, relative: str) -> Path:
        path = self.root / relative
        if not path.is_file() or not path.resolve().is_relative_to(self.root):
            raise ValueError(f"Missing or unsafe report source file: {relative}")
        digest = _hash(path)
        if relative in self.expected and digest != self.expected[relative]:
            raise ValueError(f"Source output hash does not match its run manifest: {relative}")
        previous = self.files.get(relative)
        if previous is not None and previous["sha256"] != digest:
            raise ValueError(f"Source changed while generating report: {relative}")
        self.files[relative] = {"path": relative, "bytes": path.stat().st_size, "sha256": digest}
        return path

    def read_json(self, relative: str) -> dict[str, object]:
        raw = json.loads(self.record(relative).read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError(f"Expected a JSON object: {relative}")
        return cast("dict[str, object]", raw)

    def read_table(self, relative: str) -> pd.DataFrame:
        return pd.read_parquet(self.record(relative))

    def load_expected(self, manifest: dict[str, object]) -> None:
        outputs = manifest.get("outputs", [])
        if not isinstance(outputs, list):
            raise ValueError("Malformed run output catalogue")
        for raw in outputs:
            if not isinstance(raw, dict) or not isinstance(raw.get("path"), str):
                raise ValueError("Malformed run output entry")
            files = raw.get("files")
            if isinstance(files, list) and len(files) == 1 and isinstance(files[0], dict):
                digest = files[0].get("sha256")
                if isinstance(digest, str):
                    self.expected[raw["path"]] = digest

    def verify_unchanged(self) -> None:
        for relative, entry in self.files.items():
            if _hash(self.root / relative) != entry["sha256"]:
                raise ValueError(f"Source changed while generating report: {relative}")


def _validate_summary(fleet: pd.DataFrame, summary: dict[str, object]) -> None:
    """A stale summary must not silently appear beside current site-level results."""
    needed = {
        "site_id",
        "comparison_supported",
        "performance_group",
        "matched_actual_mwh",
        "matched_expected_mwh",
        "site_shortfall_mwh",
        "site_excess_mwh",
        "hourly_shortfall_mwh",
        "hourly_excess_mwh",
    }
    if not needed <= set(fleet):
        raise ValueError(f"Fleet table is missing report columns: {sorted(needed - set(fleet))}")
    if fleet.empty or fleet["site_id"].isna().any() or fleet["site_id"].duplicated().any():
        raise ValueError("Fleet table requires unique, nonempty site identifiers")
    if not fleet["comparison_supported"].map(lambda value: isinstance(value, bool)).all():
        raise ValueError("Fleet comparison_supported values must be booleans")
    calculated = summarize_fleet(fleet)
    for key, value in calculated.items():
        if key == "scope":
            continue
        saved = summary.get(key)
        if isinstance(value, (float, int)):
            if not isinstance(saved, (float, int)) or not math.isclose(
                value, saved, rel_tol=1e-10, abs_tol=1e-9
            ):
                raise ValueError(f"Saved summary disagrees with the fleet table: {key}")
        elif value != saved:
            raise ValueError(f"Saved summary disagrees with the fleet table: {key}")


def _site_keys(manifest: dict[str, object], fleet: pd.DataFrame) -> dict[str, str]:
    if manifest["schema"] == COMPARISON_SCHEMA:
        return {}
    raw = manifest.get("site_outputs")
    if not isinstance(raw, list):
        raise ValueError("Completed run is missing site_outputs")
    result: dict[str, str] = {}
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("Malformed site output mapping")
        site_id, key = item.get("site_id"), item.get("key")
        if not isinstance(site_id, str) or not isinstance(key, str):
            raise ValueError("Site output identifiers and keys must be strings")
        if not re.fullmatch(r"site-\d{6,}", key):
            raise ValueError("Unsafe or unrecognized site output key")
        if site_id in result or key in result.values():
            raise ValueError("Duplicate site output mapping")
        result[site_id] = key
    if set(result) != set(fleet["site_id"].astype(str)):
        raise ValueError("Site output mappings differ from the fleet registry")
    return result


def _synthetic_evidence(
    snapshot: _Snapshot, manifest: dict[str, object], fleet: pd.DataFrame, requested: bool | None
) -> bool:
    config = manifest.get("configuration")
    config_kind = config.get("data_kind") if isinstance(config, dict) else None
    known = manifest.get("data_kind") == "synthetic" or config_kind == "synthetic"
    # Compatibility with the original demo, which predates explicit data_kind metadata.
    known |= fleet["site_id"].astype(str).str.startswith("synthetic-").any()
    marker = snapshot.root.parent / "SYNTHETIC_DATA.json"
    if marker.is_file():
        try:
            contents = json.loads(marker.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            contents = {}
        known |= isinstance(contents, dict) and contents.get("synthetic") is True
    return bool(known or requested is True)


def _report_window(hourly: pd.DataFrame, manifest: dict[str, object]) -> pd.DataFrame:
    config = manifest.get("configuration")
    if not isinstance(config, dict):
        raise ValueError("Saved model run has no configuration")
    start, end = config.get("report_start"), config.get("report_end")
    if not isinstance(start, str) or not isinstance(end, str):
        raise ValueError("Saved run is missing report time boundaries")
    timestamps = pd.to_datetime(hourly["timestamp"], utc=True)
    lower, upper = pd.Timestamp(start), pd.Timestamp(end)
    if lower.tzinfo is None or upper.tzinfo is None or lower >= upper:
        raise ValueError("Saved report boundaries must be ordered and timezone-aware")
    return hourly.loc[(timestamps >= lower) & (timestamps < upper)].copy()


def generate_reports(
    run_path: Path,
    output_path: Path | None = None,
    *,
    title: str = "Chile PV fleet performance",
    synthetic: bool | None = None,
) -> dict[str, object]:
    """Render a saved run or frozen comparison without altering its scientific outputs.

    By default all generated reports belong to ``run_path / 'reports'``. Existing
    destinations are refused. One site's hourly evidence is resident at a time;
    the entry dashboard contains site summaries, never the fleet's hourly history.
    Source files and every generated artifact are content-hashed. Known synthetic
    evidence cannot be suppressed by passing ``synthetic=False``.
    """
    source = run_path.resolve(strict=True)
    if not source.is_dir():
        raise ValueError("Report input must be a completed analysis directory")
    output = (output_path if output_path is not None else source / "reports").absolute()
    if output.exists():
        raise FileExistsError(f"Refusing to overwrite reports: {output}")
    destination = output.resolve()
    if source.is_relative_to(destination) or any(
        destination.is_relative_to(source / protected) for protected in ("hourly", "models", "tdp")
    ):
        raise ValueError("Report destination must not replace or contaminate source data folders")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Report title must not be empty")
    snapshot = _Snapshot(source)
    manifest = snapshot.read_json("manifest.json")
    if manifest.get("complete") is not True or manifest.get("schema") not in {
        RUN_SCHEMA,
        COMPARISON_SCHEMA,
    }:
        raise ValueError("Report input must be a supported, completed analysis or comparison")
    snapshot.load_expected(manifest)
    fleet = snapshot.read_table("fleet.parquet")
    summary = snapshot.read_json("summary.json")
    _validate_summary(fleet, summary)
    if json_safe(manifest.get("summary")) != json_safe(summary):
        raise ValueError("Run manifest and summary.json disagree")
    keys = _site_keys(manifest, fleet)
    is_synthetic = _synthetic_evidence(snapshot, manifest, fleet, synthetic)
    rows = list(row_mapping(fleet))
    pages = {str(row["site_id"]): f"sites/site-{i:06d}.html" for i, row in enumerate(rows)}
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    try:
        (temporary / "sites").mkdir()
        for row in rows:
            site_id = str(row["site_id"])
            hourly = pd.DataFrame()
            model: dict[str, object] = {}
            tdp: dict[str, pd.DataFrame] = {}
            if site_id in keys:
                key = keys[site_id]
                hourly = snapshot.read_table(f"hourly/{key}.parquet")
                if "site_id" not in hourly or not hourly["site_id"].astype(str).eq(site_id).all():
                    raise ValueError(f"Hourly file has another site's observations: {key}")
                hourly = _report_window(hourly, manifest)
                model = snapshot.read_json(f"models/{key}.json")
                if model.get("site_id") != site_id:
                    raise ValueError(f"Model file belongs to another site: {key}")
                for profile in ("avg", "y2y", "coverage"):
                    relative = f"tdp/{key}-{profile}.parquet"
                    if (source / relative).exists():
                        tdp[profile] = snapshot.read_table(relative)
                        if (
                            "site_id" in tdp[profile]
                            and not tdp[profile]["site_id"].astype(str).eq(site_id).all()
                        ):
                            raise ValueError(f"TDP file belongs to another site: {key}")
            (temporary / pages[site_id]).write_text(
                site_page(row, manifest, hourly, model, tdp, synthetic=is_synthetic),
                encoding="utf-8",
            )
        (temporary / "index.html").write_text(
            fleet_page(title, rows, summary, manifest, pages, synthetic=is_synthetic),
            encoding="utf-8",
        )
        article, post = publication_drafts(title, summary, manifest, synthetic=is_synthetic)
        (temporary / "website_article.md").write_text(article, encoding="utf-8")
        (temporary / "linkedin_post.md").write_text(post, encoding="utf-8")
        references = get_references()
        (temporary / "references.md").write_text(references_markdown(), encoding="utf-8")
        (temporary / "references.bib").write_text(references_bibtex(), encoding="utf-8")
        write_json(temporary / "references.json", [asdict(item) for item in references])
        write_json(
            temporary / "data.json",
            {
                "schema": "energy-data-insights-chile-report-data-v1",
                "synthetic": is_synthetic,
                "summary": summary,
                "sites": rows,
                "source_manifest": manifest,
            },
        )
        snapshot.verify_unchanged()
        result: dict[str, object] = {
            "schema": "energy-data-insights-chile-reports-v1",
            "complete": True,
            "output_path": str(output),
            "entrypoint": "index.html",
            "source_schema": manifest["schema"],
            "source_directory": source.name,
            "synthetic": is_synthetic,
            "model_retrained": False,
            "expected_values_modified": False,
            "primary_reference": PRIMARY_REFERENCE_ID,
            "summary": summary,
            "sites": [{"site_id": key, "page": value} for key, value in pages.items()],
            "inputs": [snapshot.files[key] for key in sorted(snapshot.files)],
            "source_hashes_verified": sorted(snapshot.expected.keys() & snapshot.files.keys()),
            "outputs": [
                {
                    "path": file.relative_to(temporary).as_posix(),
                    "bytes": file.stat().st_size,
                    "sha256": _hash(file),
                }
                for file in sorted(temporary.rglob("*"))
                if file.is_file()
            ],
            "interpretation": [
                "Fleet totals and site metrics are copied from the completed source analysis.",
                "Source summary consistency and available run-output hashes are verified.",
                "Only comparable records enter fleet energy totals; all registry records appear.",
                "Chart aggregation preserves matched energy; no interpolation or refitting occurs.",
                "Operating causes remain unconfirmed; draft text has not been published.",
                "The catalogue includes explicitly labeled optional and background references.",
            ],
        }
        write_json(temporary / "manifest.json", result)
        temporary.rename(output)
        return result
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
