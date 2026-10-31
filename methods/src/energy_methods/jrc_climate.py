"""JRC parametric PV climates: annual POA irradiation and weighted module temperature.

Independent implementation of the published clustering workflow. A fit creates
a new numerical model; the model's source, scaling and seed identify its map.
"""

from __future__ import annotations

from importlib.metadata import version

import numpy as np
from numpy.typing import ArrayLike, NDArray
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits

from energy_methods.climate_zones import ClimateClusterModel, ClimateProvenance, validate_training

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "medina_2026_pv_climates")
FEATURES = ("annual_poa_kwh_m2", "weighted_module_temperature_c")


def performance_features(
    poa_wm2: ArrayLike, module_temperature_c: ArrayLike, *, duration_hours: ArrayLike = 1.0
) -> NDArray[np.float64]:
    """Integrate POA and compute sum(G*T*dt)/sum(G*dt), over the final time axis.

    Supply one complete year or divide a complete multi-year irradiation total
    by its year count before fitting. The function does not invent chronology.
    Missing intervals propagate. No irradiation means undefined temperature.
    """
    g, t = np.broadcast_arrays(
        np.asarray(poa_wm2, dtype=float), np.asarray(module_temperature_c, dtype=float)
    )
    if g.ndim < 1 or not g.shape[-1]:
        raise ValueError("A nonempty time axis is required")
    dt = np.broadcast_to(np.asarray(duration_hours, dtype=float), g.shape)
    if (
        np.isinf(g).any()
        or np.isinf(t).any()
        or np.any(g < 0)
        or np.any(t <= -273.15)
        or not np.isfinite(dt).all()
        or np.any(dt <= 0)
    ):
        raise ValueError("Physical irradiance/temperature and positive durations required")
    energy = np.sum(g * dt, axis=-1)
    weighted = np.full(energy.shape, np.nan)
    np.divide(np.sum(g * t * dt, axis=-1), energy, out=weighted, where=energy > 0)
    return np.stack((energy / 1000, weighted), axis=-1)


def fit_jrc_climate(
    values: ArrayLike,
    *,
    provenance: ClimateProvenance,
    latitude: ArrayLike | None = None,
    n_clusters: int = 10,
    random_seed: int = 10,
    n_init: int = 100,
    max_iter: int = 20,
) -> ClimateClusterModel:
    """Fit JRC's two-feature workflow to an explicitly selected training grid.

    Publication settings: global 0.5° subsample, population standard deviations,
    cosine-latitude centroid weights, 100 random starts, 20 Lloyd iterations,
    best unweighted squared distance, and centers ordered by [1, 1.5]. The
    sklearn solver's early-convergence/empty-cluster handling is an adaptation.
    """
    x = validate_training(values, 2, n_clusters)
    if np.any(x[:, 0] < 0) or np.any(x[:, 1] <= -273.15):
        raise ValueError("Expected nonnegative POA irradiation and physical module temperature")
    if not 1 <= n_init <= 1000 or not 1 <= max_iter <= 10000:
        raise ValueError("Bounded positive n_init and max_iter required")
    area = np.ones(len(x))
    if latitude is not None:
        lat = np.asarray(latitude, dtype=float)
        if lat.shape != (len(x),) or not np.isfinite(lat).all() or np.any(np.abs(lat) >= 90):
            raise ValueError("Latitude must match rows and lie strictly between -90 and 90")
        area = np.cos(np.deg2rad(lat))
    scale = np.std(x, axis=0)
    z = x / scale
    rng = np.random.RandomState(random_seed)
    best_score = np.inf
    best_centers = None
    with threadpool_limits(limits=1):
        for _ in range(n_init):
            indices = rng.choice(len(z), n_clusters, replace=False)
            km = KMeans(
                n_clusters=n_clusters,
                init=z[indices],
                n_init=1,
                max_iter=max_iter,
                tol=0,
                algorithm="lloyd",
            ).fit(z, sample_weight=area)
            score = float(np.sum(np.min(km.transform(z) ** 2, axis=1)))
            if score < best_score:
                best_score, best_centers = score, km.cluster_centers_.copy()
    assert best_centers is not None
    centers = best_centers[np.argsort(best_centers @ np.array([1.0, 1.5]))]
    labels = tuple(f"POA {g:.0f} kWh/m²/year; module {t:.1f} °C" for g, t in centers * scale)
    return ClimateClusterModel(
        "jrc-parametric-refit",
        FEATURES,
        np.zeros(2),
        scale,
        np.ones(2),
        centers,
        x.min(axis=0),
        x.max(axis=0),
        ("", *(f"JRC{i:02}" for i in range(1, n_clusters + 1))),
        ("Unclassified", *labels),
        provenance,
        REFERENCE_IDS,
        {
            "software": {name: version(name) for name in ("numpy", "scikit-learn")},
            "random_seed": random_seed,
            "n_init": n_init,
            "max_iter": max_iter,
            "centroid_weighting": "cos(latitude)" if latitude is not None else "uniform",
            "selection_objective": "unweighted squared distance",
            "objective": best_score,
            "training_rows": len(x),
            "units": ["kWh/m2/year POA", "degC"],
        },
    )
