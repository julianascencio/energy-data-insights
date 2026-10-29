"""Run a bounded, reproducible monthly CCYA scenario/degradation case study."""

from __future__ import annotations

import hashlib
import io
import json
import platform
import shutil
import subprocess
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd

from energy_methods.ccya import YIELD_COMPONENTS, CCYAModel, CCYAResult, fit_ccya
from energy_methods.references import references_bibtex, references_markdown

from . import REFERENCE_IDS
from .config import CaseConfig

MAX_INPUT_BYTES = 10_000_000
MAX_MONTHS = 12_000


def _read_input(path: Path, expected_kind: str, *, measured: bool) -> tuple[pd.DataFrame, bytes]:
    with path.open("rb") as stream:
        raw = stream.read(MAX_INPUT_BYTES + 1)
    if len(raw) > MAX_INPUT_BYTES:
        raise ValueError(f"Monthly CSV exceeds {MAX_INPUT_BYTES} bytes: {path.name}")
    frame = pd.read_csv(io.BytesIO(raw), nrows=MAX_MONTHS + 1)
    required = {"month", "ghi_wm2", "temperature_c", "days", "data_kind"}
    if measured:
        required.add("dc_yield_kwh_kwp")
    if set(frame.columns) != required or frame.empty or len(frame) > MAX_MONTHS:
        raise ValueError(
            f"Invalid monthly CSV schema/size for {path.name}: expected {sorted(required)}"
        )
    if not frame["data_kind"].eq(expected_kind).all():
        raise ValueError(f"Input data_kind must be {expected_kind!r}: {path.name}")
    if not frame["month"].astype("string").str.fullmatch(r"\d{4}-\d{2}").all():
        raise ValueError("CSV month labels must be exactly YYYY-MM")
    frame.index = pd.PeriodIndex(frame.pop("month"), freq="M", name="month")
    frame = frame.drop(columns="data_kind")
    return frame, raw


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8"
    )


def _revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(Path(__file__).parent), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def run_case(config: CaseConfig) -> dict[str, object]:
    """Fit each historical model once; publish all outputs atomically after success.

    The run consumes monthly CSV snapshots and preserves their exact bytes and
    hashes. It never downloads observations or treats synthetic inputs as real.
    All projection cases require a shared horizon and a shared month-length
    pattern. 360_day and fixed-leap calendars require explicit preprocessing
    before this physical annual-yield comparison; no silent calendar conversion
    or interpolation takes place here.
    """
    from .reports import generate_report

    destination = config.output_path.resolve()
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite {destination}")
    measured_kind = "synthetic" if config.data_kind == "synthetic" else "observations"
    model_kind = "synthetic" if config.data_kind == "synthetic" else "climate_model"
    measured, measured_raw = _read_input(config.measured_path, measured_kind, measured=True)
    assert isinstance(measured.index, pd.PeriodIndex)
    if not np.array_equal(measured["days"].to_numpy(), measured.index.days_in_month):
        raise ValueError("Measured annual yield requires Gregorian month lengths")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}-", dir=destination.parent))
    try:
        inputs = temporary / "inputs"
        inputs.mkdir()
        provenance: list[dict[str, object]] = []

        def snapshot(name: str, raw: bytes, source: str) -> None:
            (inputs / name).write_bytes(raw)
            provenance.append(
                {
                    "path": f"inputs/{name}",
                    "source": source,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "bytes": len(raw),
                }
            )

        snapshot("measured.csv", measured_raw, config.measured_source)
        models: dict[str, CCYAModel] = {}
        historical: dict[str, pd.DataFrame] = {}
        results: dict[tuple[str, float], CCYAResult] = {}
        summary_rows = []
        horizon: pd.PeriodIndex | None = None
        month_lengths: pd.Series | None = None
        for scenario in config.scenarios:
            history, raw = _read_input(scenario.historical_path, model_kind, measured=False)
            snapshot(f"{scenario.id}-historical.csv", raw, scenario.source)
            future, raw = _read_input(scenario.projection_path, model_kind, measured=False)
            snapshot(f"{scenario.id}-projection.csv", raw, scenario.source)
            assert isinstance(future.index, pd.PeriodIndex)
            # Native 365-day and Gregorian projections are both explicit. A 360-day
            # year would manufacture a calendar-length loss against measured years.
            noleap = future.index.days_in_month.to_numpy().copy()
            noleap[future.index.month == 2] = 28
            if not (
                np.array_equal(future["days"].to_numpy(), future.index.days_in_month)
                or np.array_equal(future["days"].to_numpy(), noleap)
            ):
                raise ValueError("Projection calendar must be Gregorian or noleap for this study")
            if horizon is not None and (
                not future.index.equals(horizon)
                or month_lengths is None
                or not np.array_equal(future["days"].to_numpy(), month_lengths.to_numpy())
            ):
                raise ValueError("All scenarios must have the same projection horizon and calendar")
            horizon, month_lengths = future.index, future["days"]
            if max(config.report_years) > len(future) // 12:
                raise ValueError("A requested report year exceeds the projection horizon")
            model = fit_ccya(measured, history)
            models[scenario.id], historical[scenario.id] = model, history
            directory = temporary / "scenarios" / scenario.id
            directory.mkdir(parents=True)
            _write_json(directory / "model.json", model.to_dict())
            for rate_index, rate in enumerate(config.degradation_rates):
                result = model.project(future, scenario=scenario.id, degradation_per_year=rate)
                results[scenario.id, rate] = result
                output = directory / f"rate-{rate_index:02d}"
                output.mkdir()
                result.monthly.to_csv(output / "monthly.csv", index_label="month")
                result.annual.to_csv(output / "annual.csv", index_label="year")
                _write_json(output / "metadata.json", result.metadata)
                for year in config.report_years:
                    row = result.annual.iloc[year - 1]
                    summary_rows.append(
                        {
                            "scenario": scenario.id,
                            "scenario_label": scenario.label,
                            "degradation_pct_year": 100 * rate,
                            "operating_year": year,
                            "calendar_year": int(result.annual.index[year - 1]),
                            "data_kind": config.data_kind,
                            **{
                                f"{c}_gain_{p}_pct": float(row[f"{c}_cumulative_gain_{p}_pct"])
                                for c in YIELD_COMPONENTS
                                for p in ("p10", "p50", "p90")
                            },
                            "combined_cumulative_kwh_kwp": float(
                                row["combined_cumulative_kwh_kwp"]
                            ),
                        }
                    )
        summary = pd.DataFrame(summary_rows)
        summary.to_csv(temporary / "summary.csv", index=False)
        configuration = asdict(config)
        configuration["measured_path"] = "inputs/measured.csv"
        configuration["output_path"] = "."
        configuration["scenarios"] = [
            {
                **asdict(s),
                "historical_path": f"inputs/{s.id}-historical.csv",
                "projection_path": f"inputs/{s.id}-projection.csv",
            }
            for s in config.scenarios
        ]
        manifest: dict[str, object] = {
            "schema": "energy-data-insights-ccya-case-v1",
            "complete": True,
            "created_at": datetime.now(UTC).isoformat(),
            "data_kind": config.data_kind,
            "configuration": configuration,
            "inputs": provenance,
            "reference_ids": list(REFERENCE_IDS),
            "git_revision": _revision(),
            "python": platform.python_version(),
            "versions": {
                p: version(p)
                for p in ("energy-analysis", "energy-methods", "numpy", "pandas", "matplotlib")
            },
            "thesis": {
                "sections": "7.5.2-7.5.3",
                "figures": "7.10-7.21",
                "numerical_reproduction": False,
            },
            "uncertainty": "Historical nonexceedance quantiles; no scenario probabilities",
        }
        (temporary / "references.bib").write_text(
            references_bibtex(REFERENCE_IDS), encoding="utf-8"
        )
        (temporary / "references.md").write_text(
            references_markdown(REFERENCE_IDS), encoding="utf-8"
        )
        generate_report(temporary, config, measured, historical, models, results, summary, manifest)
        manifest["outputs"] = [
            {
                "path": p.relative_to(temporary).as_posix(),
                "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
            }
            for p in sorted(temporary.rglob("*"))
            if p.is_file()
        ]
        _write_json(temporary / "manifest.json", manifest)
        if destination.exists():
            raise FileExistsError(f"Output appeared during the run: {destination}")
        temporary.rename(destination)
        return manifest
    except BaseException:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
