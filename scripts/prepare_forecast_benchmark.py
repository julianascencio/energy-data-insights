"""Capture real ONS subsets, optional actual Timestral inference, and benchmark scores.

The default recomputes tree/physical fits and metrics from the bundled inputs.
Use --download to refresh the two public monthly files and --capture-timestral
to replace the real model predictions. Neither action is implicit in docs builds.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
from dataclasses import asdict
from datetime import UTC, datetime
from importlib import import_module
from importlib.metadata import version
from pathlib import Path

import httpx
import pandas as pd
import pyarrow.parquet as pq

from energy_analysis.forecast_benchmark import (
    DEFAULT_CONFIG,
    INPUT_MANIFEST,
    TIMESTRAL_CSV,
    TIMESTRAL_MANIFEST,
    benchmark_scores,
    capture_timestral_forecasts,
    forecast_folds,
    load_benchmark_observations,
    run_forecast_benchmark,
)
from energy_data_retrieval.sources.ons import ONS_HOSTS
from energy_data_retrieval.transport import HTTPClient
from energy_methods.lightgbm import DEFAULT_CONFIG as LIGHTGBM_CONFIG
from energy_methods.physics import DEFAULT_CONFIG as SOLAR_CONFIG
from energy_methods.timestral import TIMESTRAL_SOURCE_REVISION, TimestralConnector
from energy_methods.wind_physics import DEFAULT_CONFIG as WIND_CONFIG
from energy_methods.xgboost import DEFAULT_CONFIG as XGBOOST_CONFIG

SOURCES = (
    ("solar", "fotovoltaica", "PBFCM4", "Coremas IV"),
    ("wind", "eolica", "MAEDT1", "Delta 3 I"),
)


def download_observations(
    directory: Path, cache_directory: Path, *, use_env_proxy: bool = False
) -> None:
    """Retain all native fields for two fixed plants; no test-period quality selection."""
    cache_directory.mkdir(parents=True, exist_ok=True)
    sources = []
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    transport = httpx.HTTPTransport(proxy=proxy) if use_env_proxy and proxy else None
    with HTTPClient(ONS_HOSTS, transport=transport) as http:
        for technology, native, plant_id, plant_name in SOURCES:
            url = (
                "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/"
                f"restricao_coff_{native}_detail_tm/RESTRICAO_COFF_{native.upper()}_DETAIL_2024_06.parquet"
            )
            path = cache_directory / f"{technology}_202406.parquet"
            record = http.download_file(url, path)
            if pq.read_metadata(path).num_rows > 2_000_000:
                raise ValueError("Monthly source exceeds the reviewed two-million-row limit")
            # Predicate filtering avoids materializing unrelated farms in memory.
            frame = pd.read_parquet(path, filters=[("id_ons", "==", plant_id)])
            frame = frame.sort_values("din_instante")
            if len(frame) != 1440 or frame["din_instante"].duplicated().any():
                raise ValueError("Expected 1,440 distinct half-hour records for the selected plant")
            if technology == "solar":
                initial = frame.iloc[:672]
                valid = initial["flg_dadoirradianciainvalido"].eq(0)
                daylight = initial["val_irradianciaverificado"].gt(100)
                if valid.sum() < 650 or (valid & daylight).sum() < 150:
                    raise ValueError("Initial solar training data fail resource qualification")
            output = directory / f"forecast_ons_{technology}.csv"
            frame.to_csv(output, sep=";", index=False, date_format="%Y-%m-%d %H:%M:%S")
            sources.append(
                {
                    "technology": technology,
                    "plant_id": plant_id,
                    "plant_name": plant_name,
                    "source_url": url,
                    "request": asdict(record),
                    "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "sample_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                    "sample_rows": len(frame),
                    "source_columns": list(frame.columns),
                    "transformation": "Select declared plant; sort source timestamps; serialize "
                    "all original Parquet columns as semicolon CSV. "
                    "No interpolation or observations generated.",
                    "dictionary_url": (
                        "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/"
                        "restricao_coff_eolica_detail_tm/"
                        "DicionarioDados_RestricaoContrainedoff_UsiEolicas_DetalhamentoPorUsina.pdf"
                        if technology == "wind"
                        else "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/"
                        "restricao_coff_fotovoltaica_detail_tm/"
                        "DicionarioDados_RestricaoContrainedoff_UsiFotovoltaica_Detail.json"
                    ),
                }
            )
    manifest = {
        "retrieved_at_utc": datetime.now(UTC).isoformat(),
        "sources": sources,
        "attribution": "Operador Nacional do Sistema Eletrico (ONS), CC-BY; selections identified.",
        "period": "2024-06-01 through 2024-06-30 inclusive, native Brazilian labels",
        "plant_selection": "Solar PBFCM4 is the first plant in native export order with 672 "
        "initial training records, >=650 valid resource flags and >=150 valid readings above "
        "100 W/m2. This excludes degenerate all-zero sensors despite valid flags. Wind MAEDT1 "
        "is the first wind plant in the native export. Selection used only the initial 14-day "
        "training inputs, never model errors or test-period quality.",
        "clock": "America/Sao_Paulo source reference labels converted to UTC without shifting. "
        "Interval start/end is not asserted. Issue is last available historical source label.",
        "target_unit": "MWmed (mean MW over the native half hour), not MWh",
        "resource_policy": "Invalid resource flags mask training covariates. Solar forecasts "
        "reuse the latest valid same-clock observation; wind uses the last valid observation.",
        "wind_unit_assumption": "The ONS PDF calls val_ventoverificado wind speed but prints "
        "m3/s. This dimensional inconsistency is retained here; the cubic-curve benchmark "
        "explicitly interprets the native numerical speeds as m/s. No volumetric-flow conversion.",
        "solar_assumptions": "Measured irradiance is a POA proxy of undocumented sensor-plane "
        "orientation. No temperature observation is provided; the physical surrogate fixes 25 C.",
        "availability_assumption": "Historical SCADA generation and resource are assumed "
        "available at their labels for this experiment. Exports include post-operation revisions; "
        "this is not a verified as-issued operational backtest.",
    }
    (directory / INPUT_MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")


def capture_model(directory: Path, model_id: str, revision: str, local_only: bool) -> None:
    """Record checkpoint hashes and actual deterministic CPU model predictions."""
    torch = import_module("torch")
    hub = import_module("huggingface_hub")
    timestral = import_module("timestral")
    module_file = timestral.__file__
    if module_file is None:
        raise RuntimeError("Timestral source files are required to record provenance")
    package = Path(module_file).parent
    torch.set_num_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    checkpoint_hashes = {}
    for filename in ("config.json", "model.safetensors", "LICENSE"):
        path = Path(
            hub.hf_hub_download(model_id, filename, revision=revision, local_files_only=local_only)
        )
        checkpoint_hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
    folds = forecast_folds(load_benchmark_observations(directory))
    connector = TimestralConnector(model_id, revision=revision, local_files_only=local_only)
    print(f"Running real {model_id} inference for {len(folds)} rolling origins", flush=True)
    predictions = capture_timestral_forecasts(folds, connector)
    path = directory / TIMESTRAL_CSV
    predictions.to_csv(path, index=False, float_format="%.10g")
    source_hashes = {
        p.relative_to(package).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(package.rglob("*.py"))
    }
    manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "kind": "Actual Timestral inference, never synthetic baseline replacement",
        "model_id": model_id,
        "model_revision": revision,
        "checkpoint_sha256": checkpoint_hashes,
        "reference_code_revision": TIMESTRAL_SOURCE_REVISION,
        "installed_source_sha256": source_hashes,
        "config": asdict(DEFAULT_CONFIG),
        "fold_inputs": {fold.key: fold.input_sha256 for fold in folds},
        "forecast_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "device": "cpu",
        "seed": 0,
        "torch_threads": 1,
        "python": platform.python_version(),
        "versions": {
            name: version(name)
            for name in ("timestral", "torch", "numpy", "pandas", "huggingface_hub", "safetensors")
        },
        "quantiles_retained": [0.1, 0.5, 0.9],
        "limits": "Unknown pretraining overlap; intervals uncalibrated. See input provenance "
        "for weather-persistence, revised-data and physical-surrogate assumptions.",
    }
    (directory / TIMESTRAL_MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--data-directory", type=Path, default=root / "examples/analysis/data/forecast"
    )
    parser.add_argument("--download", action="store_true")
    parser.add_argument(
        "--use-env-proxy", action="store_true", help="Opt into HTTPS_PROXY downloads"
    )
    parser.add_argument("--capture-timestral", action="store_true")
    parser.add_argument("--model", default="mistralai/Timestral-5M")
    parser.add_argument("--revision", default="bdd20cfc15a3fea0e4cb5ccef37f8d3ca7aa335f")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--output", type=Path, default=root / "artifacts/forecast-benchmark")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.revision):
        parser.error("Model revision must be a full 40-character commit SHA")
    args.data_directory.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.download:
        download_observations(
            args.data_directory, args.output / "raw", use_env_proxy=args.use_env_proxy
        )
    if args.capture_timestral:
        capture_model(args.data_directory, args.model, args.revision, args.local_files_only)
    predictions = run_forecast_benchmark(args.data_directory)
    scores = benchmark_scores(predictions)
    predictions.to_csv(args.output / "predictions.csv", index=False, float_format="%.10g")
    scores.to_csv(
        args.data_directory / "forecast_benchmark_scores.csv", index=False, float_format="%.10g"
    )
    benchmark_scores(predictions, by_lead=True).to_csv(
        args.data_directory / "forecast_benchmark_lead_scores.csv",
        index=False,
        float_format="%.10g",
    )
    result_manifest = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "python": platform.python_version(),
        "versions": {
            name: version(name)
            for name in (
                "numpy",
                "pandas",
                "scipy",
                "lightgbm",
                "xgboost",
                "energy-methods",
                "energy-analysis",
                "energy-data-retrieval",
            )
        },
        "benchmark_config": asdict(DEFAULT_CONFIG),
        "model_configs": {
            name: asdict(config)
            for name, config in (
                ("LightGBM", LIGHTGBM_CONFIG),
                ("XGBoost", XGBOOST_CONFIG),
                ("Solar physical", SOLAR_CONFIG),
                ("Wind physical", WIND_CONFIG),
            )
        },
        "timestral_mode": "Replay verified actual model inference; see Timestral provenance",
        "file_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(args.data_directory.glob("forecast_*.csv"))
        },
        "code_sha256": {
            p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [
                root / "analysis/src/energy_analysis/forecast_benchmark.py",
                *[
                    root / f"methods/src/energy_methods/{name}.py"
                    for name in ("lightgbm", "xgboost", "physics", "wind_physics")
                ],
            ]
        },
    }
    (args.data_directory / "forecast_benchmark_provenance.json").write_text(
        json.dumps(result_manifest, indent=2) + "\n"
    )
    print(scores.to_string(index=False))


if __name__ == "__main__":
    main()
