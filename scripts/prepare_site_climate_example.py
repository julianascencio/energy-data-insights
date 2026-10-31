"""Capture all native columns around Rengo from the pinned global catalogues."""

import argparse
import json
import shutil
from pathlib import Path

from energy_data_retrieval.sources.jrc_climate import client as jrc
from energy_data_retrieval.sources.ml21 import client as ml21
from energy_data_retrieval.sources.pvcz import client as pvcz
from energy_data_retrieval.spatial import haversine_distance_km
from energy_data_retrieval.storage import sha256_file


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=root / "examples/analysis")
    args = parser.parse_args()
    baseline = root / "examples/analysis"
    original = json.loads((baseline / "climate_provenance.json").read_text())
    support = {"latitude": -34.406, "longitude": -70.858, "radius_km": 75.0}
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    sources, files = {}, {}
    for source, client, filename in (
        ("jrc", jrc, "jrc_means_global.csv"),
        ("ml21", ml21, "ml21_supplement.xlsx"),
        ("pvcz", pvcz, "pvcz.csv"),
    ):
        raw = args.raw_directory / filename
        if sha256_file(raw) != original["sources"][source]["sha256"]:
            raise ValueError(f"Source differs from reviewed global catalogue: {source}")
        frame = client.read_catalogue(raw)
        distances = haversine_distance_km(
            support["latitude"], support["longitude"], frame.lat, frame.lon
        )
        selected = frame.loc[distances <= support["radius_km"]]
        name = f"site_climate_{source}.csv"
        selected.to_csv(output / name, index=False)
        files[name] = sha256_file(output / name)
        sources[source] = {
            **original["sources"][source],
            "source": {
                "jrc": "JRC PVGIS/ERA5 climate catalogue",
                "ml21": "ML21 publisher supplementary workbook",
                "pvcz": "PVCZ author stressor catalogue",
            }[source],
            "sample_support": support,
            "selection": (
                "Every native row within 75 km of the declared Rengo coordinate; "
                "all columns retained"
            ),
            "original_rows": len(frame),
            "retained_rows": len(selected),
            "columns": list(selected.columns),
            "sample_sha256": files[name],
            "reference_ids": list(client.REFERENCE_IDS),
        }
    model = "climate_jrc_model.json"
    if (output / model).resolve() != (baseline / model).resolve():
        shutil.copyfile(baseline / model, output / model)
    files[model] = sha256_file(output / model)
    license_file = "climate_PVCZ_LICENSE.txt"
    if (output / license_file).resolve() != (baseline / license_file).resolve():
        shutil.copyfile(baseline / license_file, output / license_file)
    files[license_file] = sha256_file(output / license_file)
    manifest = {
        "format_version": 1,
        "site": {
            "name": "Rengo, Chile (illustrative site coordinate)",
            "latitude": support["latitude"],
            "longitude": support["longitude"],
        },
        "sources": sources,
        "files": files,
        "purpose": "Offline site context, not a surveyed plant location or field validation",
    }
    path = output / "site_climate_provenance.json"
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    print(path)


if __name__ == "__main__":
    main()
