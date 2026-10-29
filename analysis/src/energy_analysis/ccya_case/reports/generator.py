"""Static scientific figures and a self-contained report for the CCYA case study."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path

import matplotlib as mpl
import numpy as np
import pandas as pd
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from energy_methods.ccya import YIELD_COMPONENTS, CCYAModel, CCYAResult
from energy_methods.references import get_references

from .. import REFERENCE_IDS
from ..config import CaseConfig

COMPONENT_LABELS = {
    "irradiance": "Irradiance",
    "irradiance_temperature": "Irradiance + temperature",
    "irradiance_power": "Irradiance + degradation",
    "combined": "All three effects",
}


def generate_report(
    root: Path,
    config: CaseConfig,
    measured: pd.DataFrame,
    historical: dict[str, pd.DataFrame],
    models: dict[str, CCYAModel],
    results: dict[tuple[str, float], CCYAResult],
    summary: pd.DataFrame,
    manifest: dict[str, object],
) -> None:
    """Write PNG/SVG figures plus HTML with embedded figures and CSV download.

    The report is generated from the same result tables written by the analysis,
    not separately refitted models. All labels from inputs are HTML-escaped.
    """
    output = root / "reports"
    figures = output / "figures"
    figures.mkdir(parents=True)
    synthetic = config.data_kind == "synthetic"
    banner = "SYNTHETIC DEMONSTRATION" if synthetic else "OBSERVATIONS + CLIMATE PROJECTIONS"
    colors = mpl.colormaps["tab10"](np.linspace(0, 0.9, len(config.scenarios)))
    entries: list[tuple[str, str, str]] = []
    selected_rate = config.plot_degradation_rate
    first = config.scenarios[0]
    first_model = models[first.id]
    first_result = results[first.id, selected_rate]
    first_history = historical[first.id]
    assert isinstance(measured.index, pd.PeriodIndex)
    measured_annual = measured["dc_yield_kwh_kwp"].groupby(measured.index.year).sum()
    quantiles = np.quantile(measured_annual, [0.1, 0.5, 0.9])

    def save(fig: Figure, key: str, title: str, caption: str) -> None:
        FigureCanvasAgg(fig)
        fig.suptitle(f"{title}\n{banner}", fontsize=14, fontweight="bold")
        for axis in fig.axes:
            axis.tick_params(labelsize=9)
            axis.spines[["top", "right"]].set_visible(False)
        for suffix in ("png", "svg"):
            fig.savefig(figures / f"{key}.{suffix}", dpi=150, bbox_inches="tight")
        entries.append((key, title, caption))
        fig.clear()

    fig = Figure(figsize=(12, 5), layout="constrained")
    axes = fig.subplots(1, 2)
    for axis, column, label in zip(
        axes, ["ghi_wm2", "temperature_c"], ["GHI (W/m²)", "Ambient temperature (°C)"], strict=True
    ):
        for i, scenario in enumerate(config.scenarios):
            raw = historical[scenario.id][column].to_numpy()
            obs = measured[column].to_numpy()
            fit = (
                models[scenario.id].ghi_adaptation
                if column == "ghi_wm2"
                else models[scenario.id].temperature_adaptation
            )
            axis.scatter(raw, obs, color=colors[i], s=9, alpha=0.2)
            line = np.linspace(raw.min(), raw.max(), 100)
            axis.plot(line, fit.predict(line), color=colors[i], label=scenario.label)
        axis.set(xlabel=f"Historical model {label}", ylabel=f"Observed {label}")
        axis.grid(alpha=0.15)
    axes[-1].legend(fontsize=8, ncols=2)
    save(
        fig,
        "01-calibration",
        "Weather site adaptation",
        "Thesis Figures 7.11-7.12: monthly calibration pairs and fitted model-to-site regressions. "
        "These are in-sample relationships, not forecast validation.",
    )

    fig = Figure(figsize=(10, 6), layout="constrained")
    axis = fig.subplots()
    x = first_history["ghi_wm2"].to_numpy()
    y = (measured["dc_yield_kwh_kwp"] / measured["days"]).to_numpy()
    month = measured.index.month.to_numpy()
    scatter = axis.scatter(x, y, c=month, cmap="twilight", vmin=1, vmax=12, alpha=0.65, s=22)
    for m in range(1, 13):
        mask = month == m
        axis.scatter(
            x[mask].mean(),
            y[mask].mean(),
            marker="*",
            s=180,
            color="#193e52",
            edgecolors="white",
            linewidths=0.8,
        )
    axis.set(
        xlabel="Historical model monthly mean GHI (W/m²)",
        ylabel="Mean daily specific DC yield (kWh/kWp/day)",
    )
    axis.grid(alpha=0.15)
    fig.colorbar(scatter, ax=axis, ticks=range(1, 13), label="Calendar month")
    save(
        fig,
        "02-seasonal-response",
        "Seasonal invariant-yield calibration",
        f"Thesis Figure 7.13: monthly clouds and centroid stars for {first.label}. "
        "The method uses one proportional yield response per calendar month.",
    )

    fig = Figure(figsize=(12, 6), layout="constrained")
    axis = fig.subplots()
    axis.plot(
        measured_annual.index, measured_annual, "o-", color="#18272e", label="Historical yield"
    )
    for i, scenario in enumerate(config.scenarios):
        annual = results[scenario.id, selected_rate].annual
        axis.plot(annual.index, annual["irradiance_kwh_kwp"], color=colors[i], alpha=0.25, lw=1)
        axis.plot(
            annual.index,
            annual["irradiance_rolling_mean_kwh_kwp"],
            color=colors[i],
            label=f"{scenario.label}: 10-year mean",
            lw=2,
        )
    for label, value, style in zip(
        ["P10 = Q10", "P50 = Q50", "P90 = Q90"], quantiles, [":", "--", "-."], strict=True
    ):
        axis.axhline(value, color="#63717b", ls=style, lw=1, label=label)
    axis.set(xlabel="Calendar year", ylabel="Annual specific DC yield (kWh/kWp)")
    axis.grid(alpha=0.15)
    axis.legend(fontsize=8, ncols=3)
    save(
        fig,
        "03-yield",
        "Annual irradiance-driven yield and rolling trends",
        "Thesis Figures 7.14-7.15: faint curves are annual values; "
        "solid curves require ten complete "
        "trailing years. Historical P-values are nonexceedance quantiles, "
        "not financial guarantees.",
    )

    fig = Figure(figsize=(12, 5), layout="constrained")
    axis = fig.subplots()
    for i, scenario in enumerate(config.scenarios):
        annual = results[scenario.id, selected_rate].annual
        factor = 100 * annual["irradiance_temperature_kwh_kwp"] / annual["irradiance_kwh_kwp"]
        axis.plot(annual["operating_year"], factor, color=colors[i], alpha=0.25, lw=1)
        axis.plot(
            annual["operating_year"],
            factor.rolling(10, min_periods=10).mean(),
            color=colors[i],
            label=scenario.label,
            lw=2,
        )
    axis.axhline(100, color="#63717b", ls="--", lw=1)
    axis.set(xlabel="Operating year", ylabel="Annual energy-weighted temperature multiplier (%)")
    axis.grid(alpha=0.15)
    axis.legend(fontsize=9, ncols=4)
    save(
        fig,
        "04-temperature",
        "Incremental temperature effect",
        "Thesis Figure 7.17: the annual factor is the ratio of temperature-adjusted to "
        "irradiance-only energy. Reference climate equals 100%; historical thermal losses "
        "are not applied twice. Solid lines are ten-year means.",
    )

    fig = Figure(figsize=(10, 5), layout="constrained")
    axis = fig.subplots()
    for rate in config.degradation_rates:
        result = results[first.id, rate]
        assert isinstance(result.monthly.index, pd.PeriodIndex)
        power = result.monthly["power_factor"].groupby(result.monthly.index.year).first()
        axis.plot(result.annual["operating_year"], 100 * power, label=f"{100 * rate:g}%/year", lw=2)
    axis.set(xlabel="Operating year", ylabel="Power retention (%)")
    axis.grid(alpha=0.15)
    axis.legend()
    save(
        fig,
        "05-power",
        "Assumed degradation paths",
        "Thesis Figure 7.19: linear rates are assumptions, not fitted degradation estimates. "
        "The first operating year has zero age; the monthly factor is constant within each year.",
    )

    def heatmaps(keys: list[tuple[str, str]], name: str, title: str, caption: str) -> None:
        fig = Figure(figsize=(12, 3.3 * len(keys)), layout="constrained")
        axes = np.atleast_1d(fig.subplots(len(keys), 1))
        arrays = [
            np.stack(
                [results[s.id, selected_rate].annual[key].to_numpy() for s in config.scenarios]
            )
            for key, _ in keys
        ]
        vmax = max(1.0, max(float(np.max(np.abs(a))) for a in arrays))
        for axis, (_, label), data in zip(axes, keys, arrays, strict=True):
            chart = axis.imshow(
                data, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto", interpolation="nearest"
            )
            n = data.shape[1]
            ticks = np.unique(np.linspace(0, n - 1, min(n, 11)).astype(int))
            axis.set(
                title=label,
                xlabel="Operating year",
                xticks=ticks,
                xticklabels=ticks + 1,
                yticks=range(len(config.scenarios)),
                yticklabels=[s.label for s in config.scenarios],
            )
            fig.colorbar(chart, ax=axis, label="Cumulative gain / loss (%)", shrink=0.85)
        save(fig, name, title, caption)

    heatmaps(
        [
            (f"irradiance_cumulative_gain_{p}_pct", f"Compared with measured {p.upper()}")
            for p in ("p10", "p50", "p90")
        ],
        "06-historical-baselines",
        "Irradiance effect against historical yield baselines",
        "Thesis Figure 7.16: cumulative yield divided by the historical annual quantile times "
        "operating years, minus one. A lower historical baseline produces a larger apparent gain.",
    )
    heatmaps(
        [(f"{c}_cumulative_gain_p50_pct", COMPONENT_LABELS[c]) for c in YIELD_COMPONENTS],
        "07-components",
        f"Separated and combined effects at {100 * selected_rate:g}%/year degradation",
        "Thesis Figures 7.18, 7.20-7.21: all panels use the same historical P50 baseline. "
        "Multiplicative effects interact; their signed percentages must not simply be added.",
    )

    columns = [
        "scenario_label",
        "degradation_pct_year",
        "operating_year",
        "calendar_year",
        *[f"{c}_gain_p50_pct" for c in YIELD_COMPONENTS],
    ]
    table = (
        summary[columns]
        .rename(
            columns={
                "scenario_label": "Scenario",
                "degradation_pct_year": "Degradation %/year",
                "operating_year": "Operating year",
                "calendar_year": "Calendar year",
                **{f"{c}_gain_p50_pct": f"{COMPONENT_LABELS[c]} (%)" for c in YIELD_COMPONENTS},
            }
        )
        .to_html(index=False, escape=True, float_format=lambda value: f"{value:.2f}", border=0)
    )
    quantile_table = "".join(f"<td>{value:,.1f}</td>" for value in quantiles)
    figure_sections = []
    for key, title, caption in entries:
        encoded = base64.b64encode((figures / f"{key}.png").read_bytes()).decode("ascii")
        figure_sections.append(
            f'<section id="{key}"><h2>{html.escape(title)}</h2>'
            f'<p>{html.escape(caption)}</p><img alt="{html.escape(title, quote=True)}" '
            f'src="data:image/png;base64,{encoded}"></section>'
        )
    download = base64.b64encode(summary.to_csv(index=False).encode()).decode("ascii")
    provenance = base64.b64encode(json.dumps(manifest, ensure_ascii=False).encode()).decode("ascii")
    citations = "".join(
        f"<li>{html.escape('; '.join(r.authors))} ({r.year or 'n.d.'}). "
        f'<a href="{html.escape(r.url, quote=True)}">{html.escape(r.title)}</a>.</li>'
        for r in get_references(REFERENCE_IDS)
    )
    status = (
        "All measurements and climate paths in this report are artificially generated. "
        "Paths A-G are not CMIP6/SSP projections. This demonstrates the thesis's Bolzano workflow; "
        "it does not estimate the actual plant's future yield or reproduce its published results."
        if synthetic
        else "This report uses user-supplied plant observations and climate-model projections. "
        "Source identifiers and hashes are retained. Neither dataset authenticity nor "
        "numerical reproduction of the thesis is independently established by running the software."
    )
    unsupported = sum(
        int(results[s.id, selected_rate].monthly["outside_calibration_support"].sum())
        for s in config.scenarios
    )
    notes = (
        "Full-year monthly inputs only; no gap filling. Calendar conversion and spatial extraction "
        "must occur explicitly upstream. Annual totals retain their Gregorian/noleap duration. "
        "Percentiles summarize historical interannual variation; they do not include climate-model "
        "spread, regression uncertainty or scenario probabilities. Seasonal calibration absorbs "
        "historical operating losses; future degradation is relative to that reference. "
        "The monthly centroid fit, incremental temperature normalization "
        "and signed gain convention "
        "are documented implementation choices where the thesis is not fully explicit."
    )
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport"
content="width=device-width,initial-scale=1">
<title>{html.escape(config.title)}</title><style>
body{{margin:0;background:#f0f4f5;color:#19313e;font:16px/1.6 system-ui,sans-serif}}
main{{max-width:1180px;margin:auto;padding:32px 22px}}header,section{{background:white;padding:24px;
border-radius:12px;margin:0 0 24px}}h1{{line-height:1.15;font-size:34px}}h2{{font-size:24px}}
.tag{{letter-spacing:.10em;color:#9a4e11;font-weight:700;font-size:13px}}.notice{{background:#fff4dd;
padding:16px;border-left:4px solid #d09a36}}img{{max-width:100%;height:auto}}a{{color:#096785}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}
td,th{{padding:9px;border-bottom:1px solid #dde5e9;text-align:right;white-space:nowrap}}
th:first-child,td:first-child{{text-align:left}}.downloads a{{margin-right:24px}}
@media(max-width:600px){{main{{padding:12px}}header,section{{padding:16px}}h1{{font-size:27px}}}}
</style></head><body><main><header><div
class="tag">{banner}</div><h1>{html.escape(config.title)}</h1>
<p>Applied Climate Change Yield Assessment · thesis §§7.5.2-7.5.3, Figures 7.10-7.21</p>
<p class="notice">{html.escape(status)}</p>
<p>Calibration: {first_model.calibration_start} to {first_model.calibration_end} ·
Projection: {first_result.annual.index[0]}-{first_result.annual.index[-1]} ·
{len(config.scenarios)} scenario/member cases x {len(config.degradation_rates)} degradation
assumptions.</p>
<p class="downloads"><a download="ccya-summary.csv"
href="data:text/csv;base64,{download}">Download full comparison CSV</a>
<a download="ccya-provenance.json" href="data:application/json;base64,{provenance}">Download input
provenance</a></p>
<p><a href="#comparison">Jump to horizon comparison</a> · <a href="#limits">Assumptions and
sources</a></p></header>
<section><h2>Historical annual reference</h2><p>Specific DC yield, kWh/kWp/year.
P10/P50/P90 here are nonexceedance quantiles: Q10 ≤ Q50 ≤ Q90.</p>
<table><thead><tr><th>P10 = Q10</th><th>P50 = Q50</th><th>P90 = Q90</th></tr></thead>
<tbody><tr>{quantile_table}</tr></tbody></table></section>
{"".join(figure_sections)}
<section id="comparison"><h2>Horizon comparison: cumulative gain/loss</h2>
<p>Analogous to thesis Figure 7.21. Percentages compare cumulative energy with measured annual P50
times operating years. Positive means more cumulative energy than that reference.</p>
<div class="scroll">{table}</div></section>
<section id="limits"><h2>Assumptions, provenance and source access</h2><p>{html.escape(notes)}</p>
<p>{unsupported} scenario-months fall outside the fitted support checks (counted once per scenario,
not once per degradation rate). Future extrapolation is allowed and flagged, not independently
validated.</p>
<p>Eurac's ABD production/meteo database is access-restricted. No original Bolzano plant
measurements
were downloaded for this demonstration. The code accepts qualified replacement CSVs; the report
does not imply that restricted data are included.</p><ul>{citations}</ul></section>
</main></body></html>"""
    (output / "index.html").write_text(document, encoding="utf-8")
