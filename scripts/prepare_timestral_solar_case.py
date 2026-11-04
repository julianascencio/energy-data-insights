"""Reproduce the Mendubim VI case and its disclosed development search.

Default: offline replay, refit comparators, export scores. --download refreshes
native ONS inputs; --capture-timestral runs the pinned real model. --research
reruns the earlier plant/input search on June/July only, writing an audit under
artifacts rather than changing the frozen case or selecting on August errors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict
from importlib import import_module
from pathlib import Path

import httpx
import numpy as np
import pandas as pd
from prepare_forecast_benchmark import capture_model

from energy_analysis.forecast_benchmark import (
    INPUT_MANIFEST,
    capture_timestral_forecasts,
    forecast_folds,
    predict_comparators,
)
from energy_analysis.timestral_solar_case import (
    MODEL_ID,
    MODEL_REVISION,
    PLANT_ID,
    daily_errors,
    run_solar_case,
    solar_case_scores,
)
from energy_data_retrieval.sources.ons import ONS_HOSTS, parse_generation_csv
from energy_data_retrieval.transport import HTTPClient
from energy_methods.timestral import TimestralConnector

SMALL_REVISION = "bdd20cfc15a3fea0e4cb5ccef37f8d3ca7aa335f"
SOURCE_PREFIX = (
    "https://ons-aws-prod-opendata.s3.amazonaws.com/dataset/restricao_coff_fotovoltaica_detail_tm/"
)


def download_inputs(directory: Path, cache: Path, *, use_env_proxy: bool) -> None:
    """Preserve every native field, all three months and source-file hashes."""
    cache.mkdir(parents=True, exist_ok=True)
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    transport = httpx.HTTPTransport(proxy=proxy) if use_env_proxy and proxy else None
    downloads, frames = [], []
    with HTTPClient(ONS_HOSTS, transport=transport) as http:
        for month in ("06", "07", "08"):
            url = f"{SOURCE_PREFIX}RESTRICAO_COFF_FOTOVOLTAICA_DETAIL_2024_{month}.parquet"
            path = cache / f"solar_2024{month}.parquet"
            record = http.download_file(url, path)
            downloads.append({"source_url": url, "request": asdict(record)})
            frames.append(pd.read_parquet(path, filters=[("id_ons", "==", PLANT_ID)]))
    frame = pd.concat(frames).sort_values("din_instante")
    if len(frame) != 4416 or frame["din_instante"].duplicated().any():
        raise ValueError("Expected every half-hour label from June 1 through August 31")
    output = directory / "forecast_ons_solar.csv"
    frame.to_csv(output, sep=";", index=False, date_format="%Y-%m-%d %H:%M:%S")
    manifest = {
        "sources": [
            {
                "technology": "solar",
                "plant_id": PLANT_ID,
                "plant_name": "Mendubim VI",
                "downloads": downloads,
                "sample_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                "sample_rows": len(frame),
                "source_columns": list(frame.columns),
                "transformation": "Select RNMB06, concatenate June/July/August, sort native "
                "timestamps, serialize all original columns as semicolon CSV; no interpolation.",
                "dictionary_url": SOURCE_PREFIX
                + "DicionarioDados_RestricaoContrainedoff_UsiFotovoltaica_Detail.json",
            }
        ],
        "attribution": "Operador Nacional do Sistema Eletrico (ONS), CC-BY; subset identified.",
        "target_unit": "MWmed: mean MW over the half-hour; measured, not reference generation",
        "clock": "America/Sao_Paulo reference labels converted to UTC without shifting. "
        "Interval start/end is not asserted. Issue is the last historical reference label.",
        "availability": "Revised historical observations, assumed available at their labels; "
        "not a verified as-issued SCADA backtest.",
        "physical_assumptions": "Measured irradiance is a POA proxy of undocumented plane; "
        "constant 25 C because temperature and module thermal parameters are unavailable.",
        "selection": "See selection_audit.json, plant_search.csv and variant_search.csv. "
        "The plant was chosen on June errors; the final configuration used June/July only.",
    }
    (directory / INPUT_MANIFEST).write_text(json.dumps(manifest, indent=2) + "\n")


def native_observations(raw: pd.DataFrame) -> pd.DataFrame:
    """Use the production ONS parser, including its native timestamp semantics."""
    raw = raw.sort_values("din_instante")
    frame = parse_generation_csv(raw.to_csv(sep=";", index=False), product="solar_curtailment")
    observations = pd.DataFrame(
        {
            "power_mw": frame["value"].to_numpy(dtype=float),
            "resource": frame["val_irradianciaverificado"].to_numpy(dtype=float),
            "resource_valid": pd.to_numeric(frame["flg_dadoirradianciainvalido"], errors="raise")
            .eq(0)
            .to_numpy(),
            "restricted": pd.to_numeric(frame["flg_geracaorestrita"], errors="raise").to_numpy(),
        },
        index=pd.DatetimeIndex(frame["timestamp"]),
    )
    observations.attrs.update(
        plant_id=str(raw["id_ons"].iloc[0]), plant_name=str(raw["nom_usina"].iloc[0])
    )
    return observations


def research_predictions(
    raw: pd.DataFrame, connector: TimestralConnector, *, covariates: str = "all"
) -> pd.DataFrame:
    """Run the same seven comparators on development observations only."""
    observations = native_observations(raw)
    if observations.index.max() >= pd.Timestamp("2024-08-01 03:00", tz="UTC"):
        raise ValueError("August outcomes cannot enter the development search")
    folds = forecast_folds({"solar": observations}, timestral_covariates=covariates)
    neural = capture_timestral_forecasts(folds, connector)
    records = []
    for number, fold in enumerate(folds):
        predictions = predict_comparators(fold)
        days = fold.history_power.reshape(14, 48)
        predictions.update(
            {
                "Daily mean": days.mean(axis=0),
                "Daily median": np.median(days, axis=0),
                "Timestral": neural["prediction_mw"]
                .iloc[number * 48 : (number + 1) * 48]
                .to_numpy(),
            }
        )
        actual = observations.loc[fold.future_index, "power_mw"].to_numpy()
        for model, values in predictions.items():
            error = np.maximum(values, 0) - actual
            for stamp, residual in zip(fold.future_index, error, strict=True):
                records.append(
                    {
                        "plant_id": fold.plant_id,
                        "model": model,
                        "timestamp": stamp,
                        "error_mw": float(residual),
                    }
                )
    return pd.DataFrame(records)


def summarize_research(frame: pd.DataFrame) -> pd.DataFrame:
    """Record MAE/RMSE without discarding failed or missing observations."""
    if not np.isfinite(frame["error_mw"]).all():
        raise ValueError("Every development forecast must be finite")
    rows = []
    for (plant, model), group in frame.groupby(["plant_id", "model"]):
        error = group["error_mw"].to_numpy()
        rows.append(
            {
                "plant_id": plant,
                "model": model,
                "samples": len(error),
                "mae_mw": float(np.abs(error).mean()),
                "rmse_mw": float(np.sqrt(np.mean(error**2))),
            }
        )
    return pd.DataFrame(rows)


def research(cache: Path, output: Path, *, local_only: bool) -> None:
    """Audit the fixed 20-plant search and six variants; never choose on August."""
    torch = import_module("torch")
    torch.set_num_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    june = pd.read_parquet(cache / "solar_202406.parquet")
    small = TimestralConnector(revision=SMALL_REVISION, local_files_only=local_only)
    candidates = []
    for _, raw in june.groupby("id_ons", sort=False):
        initial = raw.sort_values("din_instante").iloc[:672]
        valid = initial["flg_dadoirradianciainvalido"].eq(0)
        if (
            len(initial) == 672
            and valid.sum() >= 650
            and (valid & initial["val_irradianciaverificado"].gt(100)).sum() >= 150
            and np.isfinite(initial["val_geracaoverificada"]).all()
            and initial["val_geracaoverificada"].ge(0).all()
        ):
            candidates.append(raw)
        if len(candidates) == 20:
            break
    if len(candidates) != 20:
        raise ValueError("Expected the declared 20 initial-data-qualified candidates")
    scores = []
    for raw in candidates:
        print("Development plant:", raw["id_ons"].iloc[0], flush=True)
        scores.append(summarize_research(research_predictions(raw, small)))
    table = pd.concat(scores, ignore_index=True)
    table.to_csv(output / "plant_search.csv", index=False)
    pivot = table.pivot(index="plant_id", columns="model", values="mae_mw")
    gain = 1 - pivot["Timestral"] / pivot.drop(columns="Timestral").min(axis=1)
    winner = gain.sort_values(ascending=False).index[0]
    if winner != PLANT_ID:
        raise ValueError("The regenerated search differs from the frozen plant selection")
    july = pd.read_parquet(cache / "solar_202407.parquet", filters=[("id_ons", "==", PLANT_ID)])
    selected = pd.concat([june[june["id_ons"] == PLANT_ID], july])
    variants = []
    for size, revision in (("5M", SMALL_REVISION), ("28M", MODEL_REVISION)):
        model = TimestralConnector(
            "mistralai/Timestral-" + size, revision=revision, local_files_only=local_only
        )
        for mode in ("target_only", "calendar", "all"):
            print("Development variant:", size, mode, flush=True)
            predictions = research_predictions(selected, model, covariates=mode)
            summary = summarize_research(predictions)
            score = summary[summary["model"] == "Timestral"].iloc[0]
            variants.append(
                {
                    "size": size,
                    "revision": revision,
                    "inputs": mode,
                    "mae_mw": float(score["mae_mw"]),
                }
            )
            if size == "5M" and mode == "all":
                failed = predictions[
                    predictions["timestamp"] >= pd.Timestamp("2024-07-01 03:00", tz="UTC")
                ]
                summarize_research(failed).to_csv(
                    output / "first_validation_scores.csv", index=False
                )
    pd.DataFrame(variants).to_csv(output / "variant_search.csv", index=False)


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-directory", type=Path, default=root / "examples/analysis/data/timestral_solar"
    )
    parser.add_argument("--output", type=Path, default=root / "artifacts/timestral-solar")
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--capture-timestral", action="store_true")
    parser.add_argument("--research", action="store_true")
    parser.add_argument("--local-files-only", action="store_true")
    parser.add_argument("--use-env-proxy", action="store_true")
    args = parser.parse_args()
    args.data_directory.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    if args.download:
        download_inputs(args.data_directory, args.output / "raw", use_env_proxy=args.use_env_proxy)
    if args.research:
        research(args.output / "raw", args.output, local_only=args.local_files_only)
    if args.capture_timestral:
        capture_model(
            args.data_directory,
            MODEL_ID,
            MODEL_REVISION,
            args.local_files_only,
            technologies=("solar",),
            timestral_covariates="target_only",
            extend_resource_history=True,
        )
    predictions = run_solar_case(args.data_directory)
    scores = solar_case_scores(predictions)
    scores.to_csv(args.data_directory / "solar_case_scores.csv", index=False, float_format="%.10g")
    daily_errors(predictions).to_csv(args.output / "daily_errors.csv", index=False)
    predictions.to_csv(args.output / "predictions.csv", index=False)
    print(scores[["period", "model", "samples", "mae_mw", "rmse_mw"]].to_string(index=False))


if __name__ == "__main__":
    main()
