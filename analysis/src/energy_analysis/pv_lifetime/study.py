"""2025 field evidence and 2026 methods for a reproducible 50-year PV study."""

from __future__ import annotations

import argparse
import hashlib
import json
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path
from typing import cast

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

from energy_methods.pv_lifetime import (
    equivalent_time_power,
    independent_mode_power,
    sigmoid_exposure,
    sigmoid_power,
    threshold_crossing,
)

REFERENCE_IDS = ("ozkalay_2025_three_decades", "quest_2024_swiss_data", "ravindrababu_2026_maple")
COLORS = ("#176B87", "#C66B27", "#A63A50", "#55845D", "#7851A9", "#727272")
AGE = np.linspace(0, 50, 601)


def provenance() -> dict:
    """Source identities, licenses, hashes and unresolved version differences."""
    return json.loads(files(__package__).joinpath("data/provenance.json").read_text("utf-8"))


def module_evidence() -> pd.DataFrame:
    """All 32 archived module records, retaining exclusions and missing ratings.

    Normalization is measured STC Pmax / workbook nameplate Pmax, not a measured
    before/after degradation ratio. Exposure uses the workbook's own dates.
    """
    with files(__package__).joinpath("data/module_measurements.csv").open("r") as handle:
        frame = pd.read_csv(handle)
    frame["exposure_years"] = frame.dismantle_year - frame.installation_year
    frame["retained_nameplate_fraction"] = frame.measured_power_w / frame.nominal_power_w
    frame["exclusion_from_long_term_projection"] = np.select(
        [frame.stored_reference, frame.nominal_power_w.isna(), frame.exposure_years < 30],
        [
            "stored reference; no field exposure",
            "nameplate power unavailable",
            "exposure below 30 years",
        ],
        default="included",
    )
    return frame


def system_evidence() -> pd.DataFrame:
    """Archived system PLRs and reported CIs, kept separate from module power."""
    with files(__package__).joinpath("data/system_plr.csv").open("r") as handle:
        return pd.read_csv(handle)


def field_anchors() -> pd.DataFrame:
    """Group medians for the 14 rated field samples with >=30 documented years."""
    frame = module_evidence()
    return (
        frame[frame.exclusion_from_long_term_projection == "included"]
        .groupby("group", sort=True)
        .agg(
            age_years=("exposure_years", "first"),
            retained_power=("retained_nameplate_fraction", "median"),
            sample_count=("module_id", "size"),
        )
        .reset_index()
    )


def field_projections() -> pd.DataFrame:
    """One-point, nameplate-anchored scenarios, starting at each measured age.

    Linear: d=(1-Pa)/a, P(t)=Pa-d*(t-a). Exponential: k=-log(Pa)/a,
    P(t)=Pa*exp(-k*(t-a)). These average-to-date slopes do not estimate a
    measured instantaneous rate, and are not fits to longitudinal module data.
    """
    records = []
    for anchor in field_anchors().itertuples():
        age_years = cast(float, anchor.age_years)
        retained_power = cast(float, anchor.retained_power)
        for model in ("linear", "exponential"):
            t = np.unique(np.r_[np.linspace(age_years, 50, 241), 40, 50])
            rate = (
                (1 - retained_power) / age_years
                if model == "linear"
                else -np.log(retained_power) / age_years
            )
            power = (
                retained_power - rate * (t - age_years)
                if model == "linear"
                else retained_power * np.exp(-rate * (t - age_years))
            )
            for age, retained in zip(t, power, strict=True):
                records.append(
                    {
                        "group": anchor.group,
                        "model": model,
                        "age_years": age,
                        "retained_power": retained,
                        "anchor_age_years": age_years,
                        "assumed_rate_per_year": rate,
                        "evidence": "projection from group median; no longitudinal fit",
                    }
                )
    return pd.DataFrame(records)


def shape_scenarios() -> pd.DataFrame:
    """Five hypothetical curves all passing through 90% at 30 years."""
    rows = []
    for label in ("Linear", "Exponential", "Sigmoid B=2", "Sigmoid B=4", "Sigmoid B=8"):
        if label == "Linear":
            power = 1 - 0.1 / 30 * AGE
        elif label == "Exponential":
            power = np.exp(np.log(0.9) / 30 * AGE)
        else:
            b = float(label.split("=")[1])
            power = sigmoid_power(sigmoid_exposure(0.9, shape=b) / 30 * AGE, shape=b)
        rows.extend(
            {"scenario": label, "age_years": age, "retained_power": p}
            for age, p in zip(AGE, power, strict=True)
        )
    return pd.DataFrame(rows)


def stress_scenarios() -> pd.DataFrame:
    """Equivalent-time and independent-mode example; all parameters hypothetical.

    Background exp(-0.001*t) times sigmoid corrosion with B=4. The corrosion
    rate is chosen to make combined power 0.9 at year 30. Multipliers change
    the rate, not temperature itself; they are not a climate forecast.
    """
    dt = np.diff(AGE)
    base_rate = sigmoid_exposure(0.9 / np.exp(-0.001 * 30), shape=4) / 30
    rows = []
    for label in ("Constant stress", "1.5x rate after year 30", "2x rate during years 30-40"):
        multiplier = np.ones_like(dt)
        if label.startswith("1.5"):
            multiplier[AGE[:-1] >= 30] = 1.5
        elif label.startswith("2x"):
            multiplier[(AGE[:-1] >= 30) & (AGE[:-1] < 40)] = 2
        corrosion = equivalent_time_power(dt, base_rate * multiplier, shape=4)
        background = np.exp(-0.001 * AGE)
        combined = independent_mode_power([background, corrosion])
        rows.extend(
            {
                "scenario": label,
                "age_years": age,
                "retained_power": p,
                "corrosion_power": c,
                "background_power": bg,
                "interval_rate_per_year": rate,
            }
            for age, p, c, bg, rate in zip(
                AGE,
                combined,
                corrosion,
                background,
                np.r_[np.nan, base_rate * multiplier],
                strict=True,
            )
        )
    return pd.DataFrame(rows)


def horizon_summary(curves: pd.DataFrame) -> pd.DataFrame:
    """30/40/50-year power and horizon-censored 80% crossing for scenario curves."""
    rows = []
    for scenario, frame in curves.groupby("scenario", sort=False):
        t, power = frame.age_years.to_numpy(), frame.retained_power.to_numpy()
        crossing = threshold_crossing(t, power)
        rows.append(
            {
                "scenario": scenario,
                **{
                    f"power_at_{year}_percent": 100 * float(np.interp(year, t, power))
                    for year in (30, 40, 50)
                },
                "threshold_crossing_year": crossing,
                "threshold_status": "not reached by year 50"
                if crossing is None
                else "reached within 50 years",
                "evidence": "hypothetical scenario, not a field prediction",
            }
        )
    return pd.DataFrame(rows)


def _axes(ax, title: str, *, left: float = 0) -> None:
    ax.set(
        title=title,
        xlabel="Age (years)",
        ylabel="Retained power (%)",
        xlim=(left, 50),
        ylim=(0, 105),
    )
    ax.set_xticks(sorted(set([left, 30, 40, 50] + ([10, 20] if left == 0 else []))))
    ax.axhline(80, color="#444444", linestyle="--", linewidth=1)
    for year in (30, 40, 50):
        ax.axvline(year, color="#DADDE0", linewidth=0.8, zorder=0)
    ax.grid(axis="y", alpha=0.15)
    ax.spines[["top", "right"]].set_visible(False)


def _note(fig: Figure, text: str) -> None:
    fig.text(0.09, 0.015, text, fontsize=8.5, va="bottom", color="#444444")
    fig.subplots_adjust(bottom=0.24, top=0.88, left=0.1, right=0.96)


def plot_measurements() -> Figure:
    """All rated field samples, including poorer outcomes and shorter exposures."""
    fig, ax = plt.subplots(figsize=(10, 6.5))
    frame = module_evidence()
    valid = frame[~frame.stored_reference & frame.nominal_power_w.notna()]
    for (group, sample), color in zip(valid.groupby("group"), COLORS, strict=False):
        ax.scatter(
            sample.exposure_years,
            100 * sample.retained_nameplate_fraction,
            label=f"{group} (n={len(sample)})",
            color=color,
            s=42,
            alpha=0.85,
        )
    _axes(ax, "Measured module power after decades in the field", left=20)
    ax.set_ylabel("Measured STC power / nameplate (%)")
    ax.axvspan(40, 50, color="#F0F2F5", zorder=0)
    ax.text(45, 30, "No field samples\nin this archive", ha="center", color="#555555")
    ax.legend(loc="lower left", fontsize=9, ncol=2)
    _note(
        fig,
        "Source: Quest et al., Zenodo v1.0.0; associated paper: Özkalay et al. "
        "(2025), DOI 10.1039/D4EL00040D.\n"
        "Ages = workbook dismantle year minus installation year. Dataset "
        "dates/counts differ from the final paper.\n"
        "22 rated field samples shown; 6 stored references and 4 samples without "
        "nameplate power excluded. No survival estimate.",
    )
    return fig


def plot_system_rates() -> Figure:
    """System PLR evidence is not used as a module degradation coefficient."""
    frame = system_evidence().sort_values("plr_percent_per_year")
    fig, ax = plt.subplots(figsize=(10, 5.5))
    value = frame.plr_percent_per_year.to_numpy()
    ax.errorbar(
        value,
        np.arange(len(frame)),
        xerr=[value - frame.ci_low_percent_per_year, frame.ci_high_percent_per_year - value],
        fmt="o",
        capsize=4,
        color=COLORS[0],
    )
    ax.set_yticks(np.arange(len(frame)), frame.site_id)
    ax.set(
        xlabel="System performance loss rate (%/year)",
        title="Archived system loss rates and reported confidence intervals",
    )
    ax.grid(axis="x", alpha=0.2)
    _note(
        fig,
        "Source: Quest et al., DOI 10.5281/zenodo.14524159, Outdoor_PLR_results.xlsx.\n"
        "The paper identifies 95% bootstrap CIs. Archive values are retained "
        "despite small differences from final text.\n"
        "These are system performance-ratio trends, not measured module-power "
        "slopes or 50-year prediction intervals.",
    )
    fig.subplots_adjust(left=0.25)
    return fig


def plot_field_projections() -> Figure:
    """Constant-rate projections anchored at measured group medians."""
    fig, ax = plt.subplots(figsize=(10, 6.5))
    curves = field_projections()
    for anchor, color in zip(field_anchors().itertuples(), COLORS, strict=False):
        age_years = cast(float, anchor.age_years)
        retained_power = cast(float, anchor.retained_power)
        for model, style in (("linear", "--"), ("exponential", ":")):
            frame = curves[(curves.group == anchor.group) & (curves.model == model)]
            ax.plot(
                frame.age_years,
                100 * frame.retained_power,
                color=color,
                linestyle=style,
                linewidth=2,
            )
        ax.scatter(
            age_years,
            100 * retained_power,
            color=color,
            s=65,
            zorder=4,
            label=(
                f"{anchor.group}: {retained_power:.1%} at {age_years:g} y (n={anchor.sample_count})"
            ),
        )
    _axes(ax, "From measured group medians to year 50", left=25)
    ax.set_ylabel("Power / original nameplate (%)")
    handles, labels = ax.get_legend_handles_labels()
    handles += [Line2D([0], [0], color="black", ls="--"), Line2D([0], [0], color="black", ls=":")]
    ax.legend(
        handles,
        [*labels, "Linear projection", "Exponential projection"],
        loc="lower left",
        fontsize=9,
    )
    _note(
        fig,
        "Dots: measured group medians from Zenodo v1.0.0. All lines: "
        "extrapolations, not observations.\n"
        "Rates inferred from one median and the original nameplate, assuming "
        "unchanged average ageing.\n"
        "No measured initial power, late-life acceleration, failure hazard, "
        "replacements or uncertainty interval is supplied.",
    )
    return fig


def plot_shape_scenarios() -> Figure:
    """One 30-year point cannot identify a 50-year degradation trajectory."""
    fig, ax = plt.subplots(figsize=(10, 6.5))
    for (label, frame), color in zip(
        shape_scenarios().groupby("scenario", sort=False), COLORS, strict=False
    ):
        ax.plot(frame.age_years, 100 * frame.retained_power, label=label, color=color, linewidth=2)
    _axes(ax, "Same 90% power at year 30, different outcomes at year 50")
    ax.scatter([30], [90], color="black", zorder=5)
    ax.legend(loc="lower left", fontsize=9)
    _note(
        fig,
        "All curves are hypothetical, including the common 30-year anchor. Shape "
        "values B=2, 4, 8 are assumed.\n"
        "Sigmoid: MAPLE Eq. 10 (Ravindrababu et al., 2026), DOI 10.1016/j.egyr.2026.109323.\n"
        "The dashed horizontal line is an 80% power criterion; it is not a safety "
        "limit or probability of survival.",
    )
    return fig


def plot_stress_scenarios() -> Figure:
    """Variable stress preserves damage through equivalent-time updates."""
    fig, ax = plt.subplots(figsize=(10, 6.5))
    for (label, frame), color in zip(
        stress_scenarios().groupby("scenario", sort=False), COLORS, strict=False
    ):
        ax.plot(frame.age_years, 100 * frame.retained_power, label=label, color=color, linewidth=2)
    _axes(ax, "Late-life stress changes the 30-50-year outlook")
    ax.legend(loc="lower left", fontsize=9)
    _note(
        fig,
        "Hypothetical scenarios: sigmoid corrosion B=4 multiplied by independent "
        "background exp(-0.001 \u00d7 age).\n"
        "All start at 90% combined power at year 30. Stress multipliers alter the "
        "corrosion rate, not calendar age.\n"
        "MAPLE Eqs. 8, 10, 13; no full framework replication or calibrated "
        "climate forecast. Damage persists after stress falls.",
    )
    return fig


def plot_rate_thresholds() -> Figure:
    """Transparent linear-rate sensitivity in the requested 30-50-year window."""
    age = np.linspace(30, 50, 201)
    rate = np.linspace(0.1, 1.2, 221)
    retained = 100 - rate[:, None] * age[None, :]
    fig, ax = plt.subplots(figsize=(10, 6.5))
    color = ax.pcolormesh(age, rate, retained, shading="auto", cmap="viridis", vmin=40, vmax=100)
    fig.colorbar(color, ax=ax, label="Retained original power (%)")
    ax.plot(age, 20 / age, color="white", linewidth=2)
    for year in (30, 40, 50):
        r = 20 / year
        ax.scatter(year, r, color="white", edgecolors="black", zorder=5, clip_on=False)
        ax.annotate(
            f"{r:.3f}%/y",
            (year, r),
            xytext=(4 if year < 50 else -4, 13),
            textcoords="offset points",
            ha="left" if year < 50 else "right",
            color="white",
            fontsize=10,
        )
    ax.set(
        xlim=(30, 50),
        ylim=(0.1, 1.2),
        xlabel="Age (years)",
        ylabel="Constant loss (% of original power per year)",
        title="How low must linear degradation be to retain 80%?",
    )
    _note(
        fig,
        "Assumption: P(t)/P(0) = 1 \u2212 d \u00d7 t, without a first-year step "
        "or later acceleration. White line: 80% threshold.\n"
        "To retain at least 80% at year 50, linear loss must be at most 0.400% of "
        "original power per year.\n"
        "This is a mathematical sensitivity map, not a measured distribution of module lifetimes.",
    )
    return fig


PLOTS = {
    "01_module_measurements": plot_measurements,
    "02_system_loss_rates": plot_system_rates,
    "03_field_anchored_projections": plot_field_projections,
    "04_model_shape_sensitivity": plot_shape_scenarios,
    "05_late_life_stress": plot_stress_scenarios,
    "06_rate_thresholds_30_50": plot_rate_thresholds,
}


def run_study(output: Path) -> dict:
    """Write six PNGs, a six-page PDF, seven CSVs and a provenance manifest."""
    output.mkdir(parents=True, exist_ok=True)
    tables = {
        "module_evidence.csv": module_evidence(),
        "system_evidence.csv": system_evidence(),
        "field_anchored_PROJECTIONS.csv": field_projections(),
        "shape_SCENARIOS.csv": shape_scenarios(),
        "stress_SCENARIOS.csv": stress_scenarios(),
        "shape_30_40_50_summary.csv": horizon_summary(shape_scenarios()),
        "stress_30_40_50_summary.csv": horizon_summary(stress_scenarios()),
    }
    outputs = []
    for name, frame in tables.items():
        frame.to_csv(output / name, index=False, float_format="%.12g")
        outputs.append(name)
    with PdfPages(
        output / "pv_lifetime_30_50_years.pdf",
        metadata={"Title": "PV lifetime: field evidence and 30-50-year projections"},
    ) as pdf:
        for name, plot in PLOTS.items():
            fig = plot()
            fig.savefig(output / f"{name}.png", dpi=180)
            pdf.savefig(fig)
            plt.close(fig)
            outputs.append(f"{name}.png")
    outputs.append("pv_lifetime_30_50_years.pdf")
    manifest = {
        "sources": provenance(),
        "reference_ids": list(REFERENCE_IDS),
        "horizon_years": 50,
        "threshold_power_fraction": 0.8,
        "scenario_anchor": {"age_years": 30, "retained_power": 0.9, "evidence": "hypothetical"},
        "sigmoid_shapes": [2, 4, 8],
        "stress_background_rate_per_year": 0.001,
        "stress_sigmoid_shape": 4,
        "stress_multipliers": [1, 1.5, 2],
        "time_step_years": 1 / 12,
        "versions": {
            name: version(name)
            for name in ("energy-methods", "energy-analysis", "numpy", "pandas", "matplotlib")
        },
        "code_sha256": {
            "study.py": hashlib.sha256(
                files(__package__).joinpath("study.py").read_bytes()
            ).hexdigest(),
            "pv_lifetime.py": hashlib.sha256(
                files("energy_methods").joinpath("pv_lifetime.py").read_bytes()
            ).hexdigest(),
        },
        "outputs_sha256": {
            name: hashlib.sha256((output / name).read_bytes()).hexdigest() for name in outputs
        },
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("artifacts/pv-lifetime"))
    args = parser.parse_args()
    run_study(args.output)
    print(horizon_summary(shape_scenarios()).to_string(index=False))
    print(
        f"Saved six plots and data to {args.output}. All 40-50-year trajectories are projections."
    )
    return 0
