"""2021 PV degradation study: published facts, scenarios and synthetic validation.

No network or external data files are needed. Packaged tables are selected
numerical facts, not the original raw measurements or a fitted author model.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from energy_methods.degradation import DegradationParameters
from energy_methods.degradation_preprocessing import annual_stress_summary
from energy_methods.degradation_uncertainty import (
    StressRateParameters,
    combined_rate_2021,
    stress_rate,
)
from energy_methods.pv_reliability import (
    KINDS,
    ReliabilityCurve,
    fit_reliability,
    normalized_rmse,
    relative_difference,
)
from energy_methods.pv_stress_weather import (
    airmass_uv,
    buck_relative_humidity,
    faiman_temperature,
    fit_temperature_model,
    linear_uv,
    ross_temperature,
    wald_uv,
)

REFERENCE_IDS = ("ascencio_vasquez_2021_thesis", "kaaya_2021_uncertainties")


def published_tables() -> dict:
    """Return a fresh copy of the attributed, packaged numerical facts."""
    return json.loads(files(__package__).joinpath("published_tables.json").read_text("utf-8"))


def reliability_table_check() -> pd.DataFrame:
    """Calculate threshold crossings from rounded Table 3 parameters."""
    rows = []
    for record in published_tables()["reliability_table3"]:
        curve = ReliabilityCurve(
            **{k: v for k, v in record.items() if k != "reported_failure_years"}
        )
        calculated = curve.failure_time()
        rows.append(
            {
                **record,
                "coefficient_units": curve.k_units,
                "calculated_failure_years": calculated,
                "calculated_minus_reported_years": calculated - record["reported_failure_years"],
                "evidence": "rounded published parameters, Table 3; no refit",
            }
        )
    return pd.DataFrame(rows)


def climate_input_comparisons() -> pd.DataFrame:
    """Recalculate Eq. 20 on Tables 8, 10 and 11 without inventing hourly errors."""
    data = published_tables()
    baseline = {r["site"]: r for r in data["climate_table6"]}
    rows = []

    def add(site: str, model: str, variable: str, measured: float, modelled: float, table: int):
        rows.append(
            {
                "site": site,
                "model": model,
                "variable": variable,
                "measured": measured,
                "modelled": modelled,
                "relative_difference_percent": float(relative_difference(measured, modelled)),
                "source_table": table,
            }
        )

    for r in data["temperature_table8"]:
        for name in ("mean_c", "upper_c", "lower_c"):
            add(r["site"], r["model"], name, baseline[r["site"]][name], r[name], 8)
    for r in data["uv_table10"]:
        for model in ("linear_5_percent", "linear_fitted", "wald", "airmass"):
            add(r["site"], model, "uv_kwh_m2", r["measured"], r[model], 10)
    for r in data["humidity_table11"]:
        add(r["site"], "buck", "rh_percent", r["measured"], r["modelled"], 11)
    return pd.DataFrame(rows)


def scenario_parameters(*, normalization: float) -> DegradationParameters:
    """Table 5 coefficients plus a caller-declared normalization assumption."""
    return DegradationParameters(
        **published_tables()["combined_table5"],
        a_n=normalization,
        calibration_id="2021-table5-unvalidated-scenario",
        calibration_source="Table 5, DOI 10.1016/j.solener.2021.01.071; A_N assumed by caller",
    )


def climate_sensitivity(
    *, normalization: float, cycles_per_year: float, rate_scale_to_year_inverse: float
) -> pd.DataFrame:
    """One-at-a-time substitutions using published inputs and explicit assumptions.

    These are scenario outputs, NOT reproductions of Figures 3/5/7/9. All three
    temperatures change together for the temperature-model comparison. The
    reliability shape is fixed to gamma=1.2, mu=0.3 as in Section 3.2, but its
    rate convention is a user assumption and has not been calibrated here.
    """
    data = published_tables()
    parameters = scenario_parameters(normalization=normalization)
    climate = {r["site"]: r for r in data["climate_table6"]}
    rows = []

    def evaluate(stresses):
        return combined_rate_2021(
            module_temperature_mean_c=stresses["mean_c"],
            module_temperature_upper_c=stresses["upper_c"],
            module_temperature_lower_c=stresses["lower_c"],
            relative_humidity_percent=stresses["rh_percent"],
            uv_dose_kwh_m2=stresses["uv_kwh_m2"],
            cycles_per_year=cycles_per_year,
            parameters=parameters,
            rate_scale_to_year_inverse=rate_scale_to_year_inverse,
        )

    def compare(site, driver, model, base, changed, source_table):
        reference, estimate = evaluate(base), evaluate(changed)
        ref_k, k = float(reference.annual_fractional_rate), float(estimate.annual_fractional_rate)
        reference_life = ReliabilityCurve("wear_out", ref_k, gamma=1.2, mu=0.3).failure_time()
        life = ReliabilityCurve("wear_out", k, gamma=1.2, mu=0.3).failure_time()
        rows.append(
            {
                "site": site,
                "driver": driver,
                "model": model,
                "source_table": source_table,
                "reference_rate_fraction_per_year": ref_k,
                "rate_fraction_per_year": k,
                "rate_relative_difference_percent": float(relative_difference(ref_k, k)),
                "reference_failure_years": reference_life,
                "failure_years": life,
                "lifetime_relative_difference_percent": float(
                    relative_difference(reference_life, life)
                ),
                "evidence": "unvalidated scenario; A_N, cycles and unit scale assumed",
            }
        )

    for r in data["temperature_table8"]:
        base = climate[r["site"]]
        changed = {**base, **{k: r[k] for k in ("mean_c", "upper_c", "lower_c")}}
        compare(r["site"], "temperature", r["model"], base, changed, 8)
    for r in data["humidity_table11"]:
        base = {**climate[r["site"]], "rh_percent": r["measured"]}
        compare(r["site"], "humidity", "buck", base, {**base, "rh_percent": r["modelled"]}, 11)
    for r in data["uv_table10"]:
        base = {**climate[r["site"]], "uv_kwh_m2": r["measured"]}
        for model in ("linear_5_percent", "linear_fitted", "wald", "airmass"):
            compare(r["site"], "UV dose", model, base, {**base, "uv_kwh_m2": r[model]}, 10)
    return pd.DataFrame(rows)


def synthetic_weather(year: int) -> pd.DataFrame:
    """Deterministic hourly test signal, not an observation of a named location."""
    index = pd.date_range(
        f"{year}-01-01", f"{year + 1}-01-01", freq="h", inclusive="left", tz="UTC"
    )
    season = np.sin(2 * np.pi * (index.dayofyear.to_numpy() - 90) / 365.25)
    daylight = np.maximum(0, np.sin(np.pi * (index.hour.to_numpy() - 6) / 12))
    poa = (750 + 150 * season) * daylight
    ambient = 17 + 8 * season + 5 * daylight + (year - 2023) * 0.3
    wind = 2.4 + np.sin(np.arange(len(index)) / 17) + 0.4 * season
    dewpoint = ambient - 7 - 2 * season
    module = faiman_temperature(ambient, poa, wind, u0=27, u1=6)
    rh = buck_relative_humidity(ambient, dewpoint)
    uv = wald_uv(poa, np.full(len(index), 0.5))
    return pd.DataFrame(
        {
            "ambient_temperature_c": ambient,
            "poa_w_m2": poa,
            "wind_speed_ms": wind,
            "module_temperature_c": module,
            "dewpoint_c": dewpoint,
            "relative_humidity_percent": rh,
            "uv_irradiance_w_m2": uv,
        },
        index=index,
    )


def synthetic_weather_benchmark() -> pd.DataFrame:
    """Fit temperature in 2023 and evaluate in 2024; exercise every weather model.

    Targets are generated by Faiman, original Wald and Buck; their advantage is
    by construction. This validates the workflow, not model skill in the field.
    Equation 1 is exercised on daily irradiance, never on annual UV dose.
    """
    train, test = synthetic_weather(2023), synthetic_weather(2024)
    calibration = train.loc[train.poa_w_m2 > 1]
    day = test.poa_w_m2 > 1
    rows = []
    for model in ("ross", "faiman"):
        coefficients = fit_temperature_model(
            calibration.ambient_temperature_c.to_numpy(),
            calibration.poa_w_m2.to_numpy(),
            calibration.module_temperature_c.to_numpy(),
            model=model,
            wind_speed_ms=calibration.wind_speed_ms.to_numpy(),
        )
        predicted = (
            ross_temperature(
                test.ambient_temperature_c.to_numpy(), test.poa_w_m2.to_numpy(), **coefficients
            )
            if model == "ross"
            else faiman_temperature(
                test.ambient_temperature_c.to_numpy(),
                test.poa_w_m2.to_numpy(),
                test.wind_speed_ms.to_numpy(),
                **coefficients,
            )
        )
        rows.append(
            {
                "variable": "module_temperature_c",
                "model": model,
                "nrmse_percent": normalized_rmse(
                    test.loc[day, "module_temperature_c"].to_numpy(), predicted[day]
                ),
                "coefficients": json.dumps(coefficients, sort_keys=True),
            }
        )
    g = test.poa_w_m2.to_numpy()
    for model, predicted in {
        "linear_5_percent": linear_uv(g, slope=0.05),
        "wald": wald_uv(g, np.full(len(g), 0.5)),
        "airmass_table9_negev": airmass_uv(
            g,
            np.full(len(g), 2.0),
            coefficients=[0.0511, -0.00829, 0.00101, -0.000045, 0.000000643],
        ),
    }.items():
        rows.append(
            {
                "variable": "uv_irradiance_w_m2",
                "model": model,
                "nrmse_percent": normalized_rmse(
                    test.loc[day, "uv_irradiance_w_m2"].to_numpy(), predicted[day]
                ),
                "coefficients": "declared synthetic scenario; see source",
            }
        )
    predicted_rh = buck_relative_humidity(
        test.ambient_temperature_c.to_numpy(), test.dewpoint_c.to_numpy()
    )
    rows.append(
        {
            "variable": "relative_humidity_percent",
            "model": "buck",
            "nrmse_percent": normalized_rmse(
                test.relative_humidity_percent.to_numpy(), predicted_rh
            ),
            "coefficients": "Eq. 17",
        }
    )
    return pd.DataFrame(rows)


def physical_model_scenario() -> pd.DataFrame:
    """Compare the two rate equations on synthetic weather with disclosed scales.

    Both scales are arbitrarily declared as numerical percent/year for this
    demonstration; there is no common-performance calibration. Their difference
    is not a reproduced paper result or evidence of one model's accuracy.
    """
    weather = synthetic_weather(2024)
    daily = weather.module_temperature_c.resample("D")
    uv_day = weather.uv_irradiance_w_m2.where(weather.poa_w_m2 > 0).resample("D").mean()
    bala = stress_rate(
        daily_maximum_temperature_c=daily.max().to_numpy(),
        daily_temperature_range_c=(daily.max() - daily.min()).to_numpy(),
        daily_daytime_uv_w_m2=uv_day.to_numpy(),
        daily_relative_humidity_percent=weather.relative_humidity_percent.resample("D")
        .mean()
        .to_numpy(),
        parameters=StressRateParameters(
            **published_tables()["stress_rate_table4"],
            rate_scale_to_year_inverse=0.01,
            calibration_source="Table 4; scale assumed for synthetic example",
        ),
    )
    combined = combined_rate_2021(
        **annual_stress_summary(weather, year=2024, cycles_per_year=365),
        parameters=scenario_parameters(normalization=1),
        rate_scale_to_year_inverse=0.01,
    )
    return pd.DataFrame(
        [
            {
                "model": "daily stress product (Eq. 1)",
                "rate_fraction_per_year": float(bala.annual_fractional_rate.mean()),
                "aggregation": "mean of daily rate coefficients",
            },
            {
                "model": "combined mechanisms (Eqs. 3-6)",
                "rate_fraction_per_year": float(combined.annual_fractional_rate),
                "aggregation": "evaluate annual daytime stresses and integrated UV dose",
            },
        ]
    ).assign(evidence="synthetic, unvalidated scales; not a fair calibrated model ranking")


def run_study(output: Path) -> dict:
    """Write deterministic CSVs, provenance and figures; return the manifest."""
    output.mkdir(parents=True, exist_ok=True)
    tables = published_tables()
    assumptions = {
        "normalization": 1.0,
        "cycles_per_year": 365.0,
        "rate_scale_to_year_inverse": 0.01,
    }
    reliability = reliability_table_check()
    sensitivity = climate_sensitivity(**assumptions)
    results = {
        "reliability_table3.csv": reliability,
        "climate_input_differences.csv": climate_input_comparisons(),
        "climate_sensitivity_SCENARIO.csv": sensitivity,
        "weather_models_SYNTHETIC.csv": synthetic_weather_benchmark(),
        "physical_models_SYNTHETIC.csv": physical_model_scenario(),
    }
    # Fit known synthetic degradation to demonstrate calibration and extrapolation.
    t = np.linspace(0, 8.1, 98)
    true_curve = ReliabilityCurve("stretched_exponential", 0.003, beta=1.59)
    y = true_curve.power(t)
    fits = [fit_reliability(t, y, kind=kind, gamma=0.43) for kind in KINDS]
    results["reliability_fits_SYNTHETIC.csv"] = pd.DataFrame(
        [
            {
                **asdict(fit.curve),
                "coefficient_units": fit.curve.k_units,
                "nrmse_percent": fit.nrmse_percent,
                "jacobian_condition": fit.jacobian_condition,
                "failure_years": fit.curve.failure_time(),
                "calibration_end_year": fit.calibration_end_year,
            }
            for fit in fits
        ]
    )
    for name, frame in results.items():
        frame.to_csv(output / name, index=False, float_format="%.12g")
    age = np.linspace(0, 50, 501)
    fig, ax = plt.subplots(figsize=(8.2, 4.8), layout="constrained")
    for row in tables["reliability_table3"]:
        curve = ReliabilityCurve(**{k: v for k, v in row.items() if k != "reported_failure_years"})
        ax.plot(
            age,
            curve.power(age),
            label=f"{curve.kind.replace('_', ' ')}: {curve.failure_time():.1f} y",
        )
    ax.axhline(0.8, color="black", ls="--", lw=1, label="80% threshold")
    ax.axvspan(0, 8.1, alpha=0.08, color="black", label="Paper's observation duration")
    ax.set(
        xlabel="Age (years)",
        ylabel="Normalized power",
        ylim=(0, 1.02),
        title="Published Table 3 parameters — extrapolated curves, no raw-data refit",
    )
    ax.legend(fontsize=9)
    fig.savefig(output / "reliability_table3.png", dpi=160)
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(9, 5), layout="constrained")
    selected = sensitivity[sensitivity.driver == "temperature"]
    pivot = selected.pivot(index="site", columns="model", values="rate_relative_difference_percent")
    pivot.plot.barh(ax=ax, color=["#258c91", "#d68a35"])
    ax.set(
        xlabel="Symmetric relative difference in model rate (%)",
        ylabel="",
        title="Temperature substitutions — UNVALIDATED parameter scenario",
    )
    ax.text(
        0,
        -0.19,
        "A_N=1; cycles/year=365; printed 273+ΔT term. Not a reproduction of Fig. 5.",
        transform=ax.transAxes,
        fontsize=9,
    )
    fig.savefig(output / "temperature_sensitivity_SCENARIO.png", dpi=160)
    plt.close(fig)
    manifest = {
        "source": tables["source"],
        "reference_ids": list(REFERENCE_IDS),
        "table_data_sha256": hashlib.sha256(
            files(__package__).joinpath("published_tables.json").read_bytes()
        ).hexdigest(),
        "assumptions_for_scenarios": assumptions,
        "scenario_reliability": {
            "kind": "wear_out",
            "gamma": 1.2,
            "mu": 0.3,
            "retained_power": 0.8,
        },
        "synthetic_reliability": {
            "generator": asdict(true_curve),
            "ages": "98 equally spaced values, 0..8.1 years",
            "noise": "none",
        },
        "synthetic_weather": (
            "Analytic signals; Faiman/Wald/Buck generated targets, "
            "2023 calibration / 2024 evaluation"
        ),
        "versions": {
            p: version(p) for p in ("energy-methods", "energy-analysis", "numpy", "pandas", "scipy")
        },
        "implementation_sha256": {
            name: hashlib.sha256(files("energy_methods").joinpath(name).read_bytes()).hexdigest()
            for name in (
                "pv_reliability.py",
                "degradation.py",
                "degradation_uncertainty.py",
                "pv_stress_weather.py",
                "degradation_weather.py",
                "degradation_preprocessing.py",
            )
        }
        | {
            "study.py": hashlib.sha256(
                files(__package__).joinpath("study.py").read_bytes()
            ).hexdigest()
        },
        "outputs_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(output.iterdir())
            if p.name in results or p.suffix == ".png"
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/degradation-uncertainty"))
    args = parser.parse_args()
    run_study(args.output)
    print(reliability_table_check().to_string(index=False))
    print(f"Saved study to {args.output}. SCENARIO and SYNTHETIC files are not field validation.")
    return 0
