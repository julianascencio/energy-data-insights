"""Seven-feature, yield-weighted PV clustering following de las Heras et al.

Published ML21 map labels are available through the separate source connector.
This module fits new clusters; their numeric IDs are not the paper's zone IDs.
"""

from __future__ import annotations

from importlib.metadata import version

import numpy as np
from numpy.typing import ArrayLike
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits

from energy_methods.climate_zones import ClimateClusterModel, ClimateProvenance, validate_training

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "triana_2026_ml_climates")
FEATURES = ("Tann", "Tmax", "Tmin", "GHIann", "GHImax", "GHImin", "UVann")
PUBLISHED_CODES = (
    "",
    "Tro1",
    "Tro2",
    "Tro3",
    "Tro4",
    "Des1",
    "Des2",
    "Des3",
    "Mou1",
    "Mou2",
    "Mou3",
    "Tem1",
    "Tem2",
    "Tem3",
    "Tem4",
    "Tem5",
    "Col1",
    "Col2",
    "Col3",
    "Col4",
    "Pol1",
    "Pol2",
)
_NAMES = {
    "Tro": "Tropical",
    "Des": "Desert",
    "Mou": "Mountainous",
    "Tem": "Temperate",
    "Col": "Cold",
    "Pol": "Polar",
}
PUBLISHED_LABELS = (
    "Unclassified",
    *(f"{_NAMES[code[:3]]}; published subtype {code[3:]}" for code in PUBLISHED_CODES[1:]),
)


def fit_ml21(
    values: ArrayLike,
    specific_yield: ArrayLike,
    *,
    provenance: ClimateProvenance,
    feature_convention: str,
    n_clusters: int = 21,
    random_seed: int = 42,
    n_init: int = 20,
) -> ClimateClusterModel:
    """Fit standardization, yield regression weights and k-means on training rows.

    ``values`` follows FEATURES. ``specific_yield`` is a corresponding training
    target (kWh/kWp/year). The feature convention must declare units and source
    aggregation; the paper's radiation statistics are retained natively by its
    workbook connector. It is unsafe to substitute physical annual totals into
    a model trained on a different radiation-statistic convention.

    Fit only training sites; reuse this frozen model on holdouts or new regions.
    This refits regression coefficients rather than copying rounded Table 4.
    """
    x = validate_training(values, 7, n_clusters)
    y = np.asarray(specific_yield, dtype=float)
    if (
        y.shape != (len(x),)
        or not np.isfinite(y).all()
        or np.any(y < 0)
        or np.std(y) == 0
        or not feature_convention.strip()
    ):
        raise ValueError("Finite nonconstant nonnegative training yield and convention required")
    if np.any(x[:, 3:] < 0) or np.any(x[:, :3] <= -273.15):
        raise ValueError("Physical climate features required")
    if not 1 <= n_init <= 1000:
        raise ValueError("n_init must be between 1 and 1000")
    offset, scale = np.mean(x, axis=0), np.std(x, axis=0)
    z = (x - offset) / scale
    coefficients, _, rank, _ = np.linalg.lstsq(np.column_stack((np.ones(len(z)), z)), y, rcond=None)
    if rank != 8:
        raise ValueError("Yield-weight regression requires full-rank training features")
    weights = np.abs(coefficients[1:])
    if weights.max() <= 0:
        raise ValueError("Yield regression has no nonzero climate weights")
    weights /= weights.max()  # Global factor leaves Euclidean cluster assignments unchanged.
    with threadpool_limits(limits=1):
        km = KMeans(
            n_clusters=n_clusters, n_init=n_init, random_state=random_seed, algorithm="lloyd"
        ).fit(z * weights)
    # Stable order by the actual mean irradiation and temperature of each fitted cluster.
    raw = np.stack([x[km.labels_ == i].mean(axis=0) for i in range(n_clusters)])
    order = np.lexsort((raw[:, 0], raw[:, 3]))
    labels = tuple(
        f"Mean air {row[0]:.1f} °C; irradiation statistic {row[3]:.3g}" for row in raw[order]
    )
    return ClimateClusterModel(
        "ml21-refit",
        FEATURES,
        offset,
        scale,
        weights,
        km.cluster_centers_[order],
        x.min(axis=0),
        x.max(axis=0),
        ("", *(f"ML{i:02}" for i in range(1, n_clusters + 1))),
        ("Unclassified", *labels),
        provenance,
        REFERENCE_IDS,
        {
            "software": {name: version(name) for name in ("numpy", "scikit-learn")},
            "random_seed": random_seed,
            "n_init": n_init,
            "training_rows": len(x),
            "feature_convention": feature_convention,
            "regression_coefficients": coefficients.tolist(),
            "target_units": "kWh/kWp/year",
            "published_map_reproduction": False,
        },
    )
