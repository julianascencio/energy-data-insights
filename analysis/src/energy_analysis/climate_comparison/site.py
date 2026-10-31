"""One-site climate context with bounded nearest-source lookup and full provenance.

Nearest points provide screening context, not an assertion that a site occupies
the same climate cell. No interpolation, refitting or silent nearest-valid search.
"""

from __future__ import annotations

import json
from copy import deepcopy
from numbers import Real
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from energy_data_retrieval.sources.jrc_climate.client import read_catalogue as read_jrc
from energy_data_retrieval.sources.ml21.client import read_catalogue as read_ml21
from energy_data_retrieval.sources.pvcz.client import read_catalogue as read_pvcz
from energy_data_retrieval.spatial import MAX_DISTANCE_KM, haversine_distance_km
from energy_data_retrieval.storage import sha256_file
from energy_methods.climate_zones import ClimateClusterModel
from energy_methods.kgpv import IRRADIATION_NAMES, TP_NAMES, ZONE_CODES
from energy_methods.ml21 import PUBLISHED_CODES, PUBLISHED_LABELS
from energy_methods.pvcz import ZONE_CODES as PVCZ_CODES
from energy_methods.pvcz import ZONE_LABELS as PVCZ_LABELS

USES = {
    "KGPV": "Group sites into broad climate/irradiation peers before comparing performance.",
    "JRC": (
        "Screen POA and module-temperature conditions; "
        "verify mounting and tilt before yield modelling."
    ),
    "ML21": (
        "Stratify performance benchmarks by published PV climate family; "
        "validate peers with local data."
    ),
    "PVCZ": "Screen thermal/humidity stress and plan module qualification or targeted inspection.",
}
LIMITS = {
    "KGPV": "A broad class does not give hourly expected power or a measured loss rate.",
    "JRC": (
        "PVGIS optimal-tilt model inputs and refitted classes are not operating-plant measurements."
    ),
    "ML21": (
        "Published labels and a new ML21 refit have different identities; "
        "native feature conventions matter."
    ),
    "PVCZ": "Stress classes are not degradation %/year, failure diagnoses or warranted lifetimes.",
}


def _fields(columns: list[str], source: str) -> dict[str, dict[str, str]]:
    """Describe known native fields; unknown extra fields remain explicitly native."""
    units = {"lat": "degree north", "lon": "degree east"}
    if source == "jrc":
        units.update(
            G="kWh/m²/year, plane-of-array",
            Tw="degC, irradiance-weighted module",
            E="kWh/kWp/year, modelled specific yield",
            eff="source-native efficiency statistic",
            tilt="degree, source optimal tilt",
            Tamb="degC, ambient mean",
            Tmod="degC, module mean",
        )
    elif source == "ml21":
        units.update({name: "degC" for name in ("Tann", "Tmax", "Tmin", "DTRann")})
        units.update(
            {
                name: "J/m², native workbook statistic"
                for name in ("GHIann", "GHImax", "GHImin", "UVann")
            }
        )
        units["Yf"] = "kWh/kWp/year, source target"
    else:
        for name in columns:
            if name.startswith("T_equiv_") and not name.endswith("zone"):
                units[name] = "degC, source-specific activation energy and mounting"
            elif name.startswith("T_ambient_"):
                units[name] = "degC"
            elif name.startswith("T_velocity_"):
                units[name] = "degC/hour"
            elif name.startswith("specific_humidity_") and not name.endswith("zone"):
                units[name] = "g/kg"
        units.update(GHI_mean="kWh/m²/day", wind_speed="m/s, source 25-year recurrence statistic")
    return {
        name: {
            "units": units.get(name, "source-native; see provider definition"),
            "meaning": "Original source field; values and column names are retained",
        }
        for name in columns
    }


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    # Pandas handles NumPy scalars and writes missing values as strict JSON null.
    return json.loads(frame.to_json(orient="records", double_precision=15))


def site_climate_profile(
    latitude: float,
    longitude: float,
    *,
    catalogues: dict[str, pd.DataFrame],
    source_metadata: dict[str, dict[str, Any]],
    jrc_model: ClimateClusterModel | None = None,
    radius_km: float = 50.0,
) -> dict[str, Any]:
    """Return all four schemes, native row fields, distances, metadata and uses.

    ``catalogues`` uses ``jrc``, ``ml21``, ``pvcz`` keys and normalized reader
    outputs; KGPV reference labels are carried in ML21. Supply full catalogues
    for arbitrary sites. ``source_metadata`` requires source, period and
    resolution for every supplied table; extra provenance fields are retained.

    Distances use a mean-radius sphere and an inclusive caller-selected radius.
    All equally nearest rows are returned, including coincident rounded PVCZ
    coordinates. Conflicting labels yield ``ambiguous`` with no selected code.
    A nearest row with missing features stays missing; a farther complete row
    cannot substitute for it. Empty, out-of-radius and absent sources are explicit.
    """
    haversine_distance_km(latitude, longitude, [], [])  # Validate query even for empty sources.
    if (
        isinstance(radius_km, (bool, np.bool_))
        or not isinstance(radius_km, Real)
        or not np.isfinite(radius_km)
        or not 0 < radius_km <= MAX_DISTANCE_KM
    ):
        raise ValueError(
            "radius_km must be finite, positive and no more than half Earth's circumference"
        )
    radius_km = float(radius_km)
    unknown = set(catalogues) - {"jrc", "ml21", "pvcz"}
    if unknown:
        raise ValueError(f"Unknown climate catalogues: {sorted(unknown)}")
    results: dict[str, Any] = {}
    for source, schemes in (("jrc", ("JRC",)), ("ml21", ("KGPV", "ML21")), ("pvcz", ("PVCZ",))):
        metadata = deepcopy(source_metadata.get(source, {}))
        frame = catalogues.get(source)
        status, distance, nearest = "source_not_supplied", None, pd.DataFrame()
        if frame is not None:
            if any(
                not str(metadata.get(key, "")).strip() for key in ("source", "period", "resolution")
            ):
                raise ValueError(f"{source} requires source, period and resolution metadata")
            if frame.columns.has_duplicates or not {"lat", "lon"} <= set(frame):
                raise ValueError("Catalogue needs unique columns including lat/lon")
            support = metadata.get("sample_support")
            supported = True
            if support is not None:
                separation = float(
                    haversine_distance_km(
                        latitude, longitude, [support["latitude"]], [support["longitude"]]
                    )[0]
                )
                supported = separation + radius_km <= support["radius_km"] + 1e-9
            distances = haversine_distance_km(latitude, longitude, frame.lat, frame.lon)
            if not supported:
                status = "outside_sample_coverage"
            elif not len(distances):
                status = "no_source_rows"
            else:
                distance = float(distances.min())
                status = "outside_radius" if distance > radius_km + 1e-9 else "matched"
                if status == "matched":
                    # 1 micrometre tolerance only resolves numerical distance ties.
                    nearest = frame.iloc[
                        np.flatnonzero(np.isclose(distances, distance, rtol=0, atol=1e-9))
                    ]
        for scheme in schemes:
            item: dict[str, Any] = {
                "status": status,
                "code": None,
                "label": None,
                "distance_km": distance,
                "source": metadata,
                "lookup": "nearest supplied source point; no interpolation or site-cell assertion",
                "candidates": _records(nearest),
                "field_metadata": _fields(list(frame.columns), source) if frame is not None else {},
                "use": USES[scheme],
                "limitation": LIMITS[scheme],
            }
            if status == "matched":
                codes: list[str] = []
                labels: dict[str, str] = {}
                if scheme == "JRC":
                    if jrc_model is None:
                        item["status"] = "model_not_supplied"
                    else:
                        if jrc_model.scheme != "jrc-parametric-refit" or jrc_model.features != (
                            "annual_poa_kwh_m2",
                            "weighted_module_temperature_c",
                        ):
                            raise ValueError("JRC requires the matching two-feature frozen model")
                        predicted = jrc_model.predict(nearest[["G", "Tw"]].to_numpy())
                        codes = predicted.zone.tolist()
                        labels = dict(zip(jrc_model.codes, jrc_model.labels, strict=True))
                        assert predicted.outside_training_range is not None
                        item["outside_training_range"] = predicted.outside_training_range.tolist()
                        item["model"] = jrc_model.to_dict()
                elif scheme == "KGPV":
                    codes = nearest.kgpv_zone.tolist()
                    labels = {
                        code: (
                            f"{TP_NAMES[code[0]]}; merged "
                            f"{IRRADIATION_NAMES[code[1]].lower()} irradiation class"
                        )
                        for code in ZONE_CODES[1:]
                    }
                elif scheme == "ML21":
                    codes = nearest.ml21_zone.tolist()
                    labels = dict(zip(PUBLISHED_CODES, PUBLISHED_LABELS, strict=True))
                else:
                    codes = nearest.pvcz_labeled.tolist()
                    labels = dict(zip(PVCZ_CODES, PVCZ_LABELS, strict=True))
                if codes:
                    if any(code not in labels for code in codes):
                        raise ValueError(f"Unknown {scheme} climate code")
                    item["candidate_codes"] = codes
                    if "" in codes:
                        item["status"] = "missing_inputs"
                    elif len(set(codes)) > 1:
                        item["status"] = "ambiguous"
                    else:
                        item.update(code=codes[0], label=labels[codes[0]])
            results[scheme] = item
    return {
        "format_version": 1,
        "query": {
            "latitude": float(latitude),
            "longitude": float(longitude),
            "radius_km": float(radius_km),
        },
        "classifications": results,
        "interpretation": (
            "Climate screening context; sources have different periods, grids and purposes"
        ),
        "next_steps": [
            "Check distance, native resolution, period and terrain before assigning a site class.",
            (
                "Retrieve local hourly weather and measured PV data; "
                "compare sites with compatible design and data quality."
            ),
            (
                "For degradation %/year, use module calibration and temperature/RH/UV/cycles; "
                "do not convert a class ID to a rate."
            ),
            (
                "Validate modelled risk against observed performance loss and inspection evidence "
                "before operational decisions."
            ),
        ],
    }


def load_site_example(
    directory: Path,
) -> tuple[dict[str, pd.DataFrame], dict[str, Any], ClimateClusterModel]:
    """Load verified, full-field Rengo subsets and the existing global JRC model."""
    manifest = json.loads((directory / "site_climate_provenance.json").read_text())
    if manifest.get("format_version") != 1:
        raise ValueError("Unsupported site fixture format")
    for name, expected in manifest["files"].items():
        if Path(name).name != name or sha256_file(directory / name) != expected:
            raise ValueError(f"Site climate checksum mismatch: {name}")
    frames = {
        name: reader(directory / f"site_climate_{name}.csv")
        for name, reader in (("jrc", read_jrc), ("ml21", read_ml21), ("pvcz", read_pvcz))
    }
    model = ClimateClusterModel.from_dict(
        json.loads((directory / "climate_jrc_model.json").read_text())
    )
    return frames, manifest, model
