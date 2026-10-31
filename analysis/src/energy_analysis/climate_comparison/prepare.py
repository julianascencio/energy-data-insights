"""Acquire source tables, fit frozen models and prepare small offline map samples.

Run ``python -m energy_analysis.climate_comparison.prepare --help``. Full public
datasets stay in the caller's cache; the gallery stores attributed CSV subsets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import UTC, datetime
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from energy_data_retrieval.sources.jrc_climate import client as jrc_source
from energy_data_retrieval.sources.ml21 import client as ml_source
from energy_data_retrieval.sources.pvcz import client as pvcz_source
from energy_data_retrieval.transport import HTTPClient, HTTPConfig
from energy_methods.climate_zones import ClimateProvenance, class_target_rmse
from energy_methods.jrc_climate import fit_jrc_climate
from energy_methods.ml21 import FEATURES, fit_ml21

SOURCES = {
    "jrc": ("jrc_means_global.csv", jrc_source.URL),
    "ml21": ("ml21_supplement.xlsx", ml_source.URL),
    "pvcz": ("pvcz.csv", pvcz_source.URL),
}


def digest(path: Path) -> str:
    """Hash exact local bytes without reading an entire source into memory."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _sample(frame: pd.DataFrame, region: str, step: float | None) -> pd.DataFrame:
    if region == "chile":
        frame = frame[frame.lon.between(-76, -66) & frame.lat.between(-56, -17)]
    if step is None:
        return frame.copy()
    # Keep one actual native observation nearest each display-bin center.
    # No averaging, invented values, categorical interpolation or ocean filling.
    frame = frame.copy()
    frame["_lat_bin"] = np.floor(frame.lat / step)
    frame["_lon_bin"] = np.floor(frame.lon / step)
    frame["_distance"] = (frame.lat / step - frame._lat_bin - 0.5) ** 2 + (
        frame.lon / step - frame._lon_bin - 0.5
    ) ** 2
    return (
        frame.sort_values("_distance", kind="stable")
        .drop_duplicates(["_lat_bin", "_lon_bin"])
        .drop(columns=["_lat_bin", "_lon_bin", "_distance"])
        .sort_values(["lat", "lon"])
        .reset_index(drop=True)
    )


def prepare(
    raw_directory: Path,
    output_directory: Path,
    *,
    download: bool = False,
    world_boundaries: Path | None = None,
) -> dict:
    """Build the study from complete native sources; optional explicit live retrieval."""
    raw_directory.mkdir(parents=True, exist_ok=True)
    output_directory.mkdir(parents=True, exist_ok=True)
    if download:
        with HTTPClient(
            frozenset({"jeodpp.jrc.ec.europa.eu", "raw.githubusercontent.com", "ars.els-cdn.com"}),
            config=HTTPConfig(maximum_response_bytes=300_000_000, timeout_seconds=120),
        ) as http:
            for filename, url in SOURCES.values():
                http.download_file(url, raw_directory / filename)
    jrc = jrc_source.read_catalogue(raw_directory / SOURCES["jrc"][0])
    ml = ml_source.read_catalogue(raw_directory / SOURCES["ml21"][0])
    pvc = pvcz_source.read_catalogue(raw_directory / SOURCES["pvcz"][0])
    # Published global JRC training sample: complete native rows at 0.5-degree nodes.
    complete = jrc.dropna()
    training = complete[
        np.isclose(complete.lat / 0.5, np.round(complete.lat / 0.5))
        & np.isclose(complete.lon / 0.5, np.round(complete.lon / 0.5))
    ]
    jrc_provenance = ClimateProvenance(
        "JRC PVGIS ERA5 global means",
        "2005-2023",
        "0.1 degree native; 0.5 degree training",
        "documented refit",
    )
    jrc_model = fit_jrc_climate(
        training[["G", "Tw"]].to_numpy(),
        latitude=training.lat.to_numpy(),
        provenance=jrc_provenance,
    )
    # Spatial blocks, not random neighboring rows, define ML holdout sites.
    blocks = np.floor(ml.lat / 5).astype(int) * 73 + np.floor(ml.lon / 5).astype(int)
    holdout = blocks % 5 == 0
    train_ml = ml.loc[~holdout]
    ml_model = fit_ml21(
        train_ml[list(FEATURES)].to_numpy(),
        train_ml.Yf.to_numpy(),
        provenance=ClimateProvenance(
            "ML21 author supplementary workbook",
            "Mixed source climatologies; see publication",
            "0.5 degree",
            "documented spatial-training refit",
        ),
        feature_convention=ml_source.FEATURE_CONVENTION,
    )
    predicted = ml_model.predict(ml.loc[holdout, list(FEATURES)].to_numpy())
    metrics = {
        "ml21_training_sites": len(train_ml),
        "ml21_holdout_sites": int(holdout.sum()),
        "split": "5-degree blocks: (floor(lat/5)*73 + floor(lon/5)) modulo 5 == 0",
        "holdout_adjusted_rand_vs_published_labels": adjusted_rand_score(
            ml.loc[holdout, "ml21_zone"], predicted.class_id
        ),
        "holdout_within_class_yield_rmse_kwh_kwp": class_target_rmse(
            predicted, ml.loc[holdout, "Yf"].to_numpy()
        ),
        "interpretation": "Reference-label agreement and within-class target dispersion; "
        "not measured-yield prediction accuracy or an independent field validation.",
    }
    manifest: dict = {
        "format_version": 1,
        "prepared_at_utc": datetime.now(UTC).isoformat(),
        "comparison": "Native maps with different periods and source support; qualitative only.",
        "sampling": {
            "world": "One actual native row nearest each 2-degree display-bin center; "
            "no averaging.",
            "chile": "BBox [-76,-56,-66,-17]; JRC uses 0.2-degree bins; "
            "plot selects centers inside mainland contour.",
            "canary": "BBox [-18.5,27.5,-13.4,29.6], excluding the African mainland corner; "
            "all native source rows.",
        },
        "sources": {},
        "files": {},
        "metrics": metrics,
        "software": {name: version(name) for name in ("numpy", "pandas", "scipy", "scikit-learn")},
    }
    for name, (filename, url) in SOURCES.items():
        path = raw_directory / filename
        manifest["sources"][name] = {
            "url": url,
            "sha256": digest(path),
            "size_bytes": path.stat().st_size,
        }
    manifest["sources"]["jrc"].update(
        period="2005-2023",
        resolution="0.1 degree",
        licence="European Commission reuse notice; attribution required",
    )
    manifest["sources"]["ml21"].update(
        period="Mixed source climatologies; see publication",
        resolution="0.5 degree",
        licence="Article CC BY; attributed supplementary-data extracts",
    )
    manifest["sources"]["pvcz"].update(
        period="2010-2018",
        resolution="0.25 degree; rounded coordinates",
        licence="MIT",
        commit=pvcz_source.COMMIT,
    )
    for name, model in (("jrc", jrc_model), ("ml21", ml_model)):
        path = output_directory / f"climate_{name}_model.json"
        path.write_text(json.dumps(model.to_dict(), indent=2) + "\n")
        manifest["files"][path.name] = digest(path)
    jrc_columns = ["lat", "lon", "G", "Tw", "E", "eff"]
    ml_columns = ["lat", "lon", *FEATURES, "Yf", "ml21_zone", "kgpv_zone"]
    pvc_columns = [
        "lat",
        "lon",
        "T_equiv_rack_1p1eV",
        "specific_humidity_mean",
        "pvcz",
        "pvcz_labeled",
    ]
    for name, frame, columns in (
        ("jrc", jrc, jrc_columns),
        ("ml21", ml, ml_columns),
        ("pvcz", pvc, pvc_columns),
    ):
        for region in ("world", "chile", "canary"):
            if region == "canary":
                selected = frame[frame.lon.between(-18.5, -13.4) & frame.lat.between(27.5, 29.6)]
            else:
                selected = _sample(
                    frame, region, 2.0 if region == "world" else 0.2 if name == "jrc" else None
                )
            selected = selected[columns].copy()
            if name == "jrc":
                selected["jrc_class"] = jrc_model.predict(selected[["G", "Tw"]].to_numpy()).class_id
            path = output_directory / f"climate_{name}_{region}.csv"
            selected.to_csv(path, index=False, float_format="%.12g")
            manifest["files"][path.name] = digest(path)
            manifest.setdefault("counts", {})[f"{name}_{region}"] = len(selected)
    if world_boundaries is not None:
        destination = output_directory / "climate_world_boundaries.geojson"
        if world_boundaries.resolve() != destination.resolve():
            shutil.copyfile(world_boundaries, destination)
    context = [
        output_directory / "climate_world_boundaries.geojson",
        output_directory / "kgpv_chile_mainland.geojson",
        *sorted(output_directory.glob("kgpv_canary_*.tif")),
    ]
    manifest["context_files"] = {p.name: digest(p) for p in context if p.exists()}
    manifest["context_attribution"] = (
        "Natural Earth public-domain outlines; Canary climate "
        "footprints from the existing KGPV study, see kgpv_canary_provenance.json "
        "and docs/kgpv-canary.md."
    )
    path = output_directory / "climate_provenance.json"
    path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def main() -> int:
    """CLI for regenerating the complete comparison study."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-directory", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--world-boundaries", type=Path)
    args = parser.parse_args()
    result = prepare(
        args.raw_directory,
        args.output_directory,
        download=args.download,
        world_boundaries=args.world_boundaries,
    )
    print(json.dumps({"counts": result["counts"], "metrics": result["metrics"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
