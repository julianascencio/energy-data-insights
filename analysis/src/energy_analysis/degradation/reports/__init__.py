"""Offline, analysis-owned figures and HTML from completed degradation maps."""

from __future__ import annotations

import base64
import html
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from matplotlib.colors import BoundaryNorm

from energy_methods.degradation_mapping import RATE_VARIABLES

TITLES = {
    "hydrolysis_rate": "Hydrolysis",
    "photodegradation_rate": "Photodegradation",
    "thermomechanical_rate": "Thermomechanical",
    "total_rate": "Combined degradation",
}


def _geography(ax: Any, result: xr.Dataset, mask: xr.DataArray) -> None:
    ax.contour(mask.lon, mask.lat, mask, levels=[0.5], colors="#49566a", linewidths=0.4)
    step = float(result.attrs["grid_step_degrees"])
    ax.set_xlim(
        max(-180, float(result.lon.min()) - step / 2), min(180, float(result.lon.max()) + step / 2)
    )
    ax.set_ylim(
        max(-90, float(result.lat.min()) - step / 2), min(90, float(result.lat.max()) + step / 2)
    )
    ax.set_facecolor("#eef2f5")
    ax.set_xlabel("Longitude (°)")
    ax.set_ylabel("Latitude (°)")
    ax.grid(alpha=0.15)
    ax.set_aspect("equal", adjustable="box")


def _embed(path: Path) -> str:
    return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode("ascii")


def generate_report(
    result: xr.Dataset, native_land_mask: xr.DataArray, manifest: dict[str, Any], output: Path
) -> Path:
    """Write PNG/SVG maps and a self-contained HTML report; never retrieve or fit."""
    output.mkdir(parents=True, exist_ok=False)
    study = manifest["study"]
    period = f"{study['start_year']}-{study['end_year']}"
    subtitle = (
        f"{period} · {study['step_degrees']:g}° sampling · "
        f"{manifest['valid_cells']}/{manifest['land_cells']} land centres with complete data"
    )
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 10}):
        fig, axes = plt.subplots(2, 2, figsize=(16, 8.5), layout="constrained")
        for ax, name in zip(axes.flat, RATE_VARIABLES, strict=True):
            layer = result[name]
            high = float(layer.max()) if bool(layer.notnull().any()) else 1.0
            mesh = ax.pcolormesh(
                result.lon,
                result.lat,
                layer,
                shading="nearest",
                cmap="magma",
                vmin=0,
                vmax=max(high, 1e-6),
                rasterized=True,
            )
            _geography(ax, result, native_land_mask)
            ax.set_title(TITLES[name], loc="left", fontweight="bold")
            fig.colorbar(mesh, ax=ax, shrink=0.75, label="Rate (% per year)")
        fig.suptitle(f"PV degradation: climate-stress scenario\n{subtitle}", fontsize=17)
        fig.savefig(output / "mechanisms.png", dpi=160)
        fig.savefig(output / "mechanisms.svg")
        plt.close(fig)

        labels = json.loads(result.rate_class.attrs["class_labels"])
        # Class 0 is nodata, never the lowest degradation band.
        class_ids = sorted(int(key) for key in labels if int(key) > 0)
        cmap = matplotlib.colormaps["viridis"].resampled(len(class_ids))
        norm = BoundaryNorm(np.arange(0.5, len(class_ids) + 1.5), cmap.N)
        fig, ax = plt.subplots(figsize=(13, 6), layout="constrained")
        mesh = ax.pcolormesh(
            result.lon,
            result.lat,
            result.rate_class.where(result.rate_class > 0),
            cmap=cmap,
            norm=norm,
            shading="nearest",
            rasterized=True,
        )
        _geography(ax, result, native_land_mask)
        ax.set_title(f"Combined degradation classes\n{subtitle}", loc="left", fontsize=15)
        bar = fig.colorbar(mesh, ax=ax, ticks=class_ids, shrink=0.8)
        bar.ax.set_yticklabels([labels[str(key)] for key in class_ids])
        bar.set_label("Rate (% per year)")
        fig.savefig(output / "classes.png", dpi=160)
        fig.savefig(output / "classes.svg")
        plt.close(fig)

    def number(value: float | None) -> str:
        return "Unavailable" if value is None else f"{value:.4f}"

    rows = "".join(
        f"<tr><th>{TITLES[name]}</th><td>{number(values['minimum'])}</td>"
        f"<td>{number(values['footprint_area_weighted_mean'])}</td>"
        f"<td>{number(values['maximum'])}</td></tr>"
        for name, values in manifest["statistics"].items()
    )
    references = "".join(
        f"<li>{html.escape('; '.join(reference['authors']))} "
        f"({reference['year'] or 'n.d.'}). "
        f"<a href='{html.escape(reference['url'], quote=True)}'>"
        f"{html.escape(reference['title'])}</a>.</li>"
        for reference in manifest["references"]
    )
    parameters = html.escape(json.dumps(manifest["parameters"], indent=2, ensure_ascii=False))
    page = f"""<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>PV degradation analysis · {period}</title>
<style>
:root{{color-scheme:light;font-family:system-ui,sans-serif;color:#182d3c;background:#eef2f5}}
body{{max-width:1150px;margin:auto;padding:35px 22px}}header{{margin:15px 0 30px}}
h1{{font-size:clamp(28px,4vw,44px);line-height:1.1;margin:12px 0}}
h2{{font-size:23px}}p,li{{line-height:1.65}}.eyebrow{{color:#276675;font-weight:700}}
section{{background:white;padding:24px;border-radius:12px;margin:22px 0}}
img{{width:100%;height:auto}}.metrics{{display:flex;gap:18px;flex-wrap:wrap}}
.metric{{flex:1;min-width:160px;background:#fff;padding:20px;border-radius:10px}}
.metric strong{{display:block;font-size:28px;color:#245f6e}}
a{{color:#17617b}}table{{border-collapse:collapse;width:100%;font-size:14px}}
th,td{{padding:12px;text-align:right;border-bottom:1px solid #dae3e7}}
th:first-child{{text-align:left}}
pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px;line-height:1.5}}
.note{{color:#526978;font-size:14px}}.scroll{{overflow:auto}}
</style>
<header><div class="eyebrow">ENERGY DATA INSIGHTS / APPLIED ANALYSIS</div>
<h1>PV degradation across climates</h1><p>{html.escape(subtitle)}</p>
<p>Real ERA5 weather retrieved through Open-Meteo. Published Kaaya coefficients applied
with explicitly chosen stress aggregation and cycling assumptions.</p></header>
<div class="metrics">
<div class="metric"><strong>{manifest["hours_retrieved"]:,}</strong>hourly location records</div>
<div class="metric"><strong>{manifest["valid_cells"]}</strong>mapped land sample centres</div>
<div class="metric"><strong>{manifest["masked_incomplete_cells"]}</strong>
incomplete centres masked</div>
</div>
<section><h2>Mechanisms and combined rate</h2>
<img src="{_embed(output / "mechanisms.png")}" alt="Four geographic maps of degradation rates">
<p class="note">Each panel has its own colour scale. Rectangles represent sample-centred
{study["step_degrees"]:g}° footprints, not spatially averaged ERA5 values or land polygons.
Grey indicates ocean, unsupported or incomplete cells. Outlines are the CRU validity mask.</p>
</section>
<section><h2>Rate classes</h2><img src="{_embed(output / "classes.png")}"
alt="Combined degradation rate classes on the sample grid"></section>
<section><h2>Sample-grid statistics</h2><div class="scroll"><table>
<thead><tr><th>Mechanism</th><th>Minimum</th><th>Footprint-weighted mean</th>
<th>Maximum</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="note">All rates are % per year. Weighting uses whole sampled cell footprints;
coastal ocean fractions are not removed. These are not global land-area estimates.</p></section>
<section><h2>Model and processing choices</h2>
<ul><li>Interval-start UTC hours. Temperature, 10 m wind and ambient relative humidity use
means of instantaneous endpoints; GHI and TOA use preceding-hour means.</li>
<li>GHI-based Faiman module temperature: u₀ = {study["u0"]:g}, u₁ = {study["u1"]:g}; wind scaled
from 10 m to {study["module_height_m"]:g} m with exponent 0.2.
Wald UVA + UVB covers 280-400 nm.</li>
<li>Arithmetic annual mean module temperature and ambient RH in percent; mean daily
maximum/minimum module temperatures; annual integrated UV dose; {study["cycles_per_day"]:g}
thermal cycle(s) per day, including leap days.
Aggregation: {html.escape(study["aggregation"])}.</li>
<li>A complete cell-year is required. No weather gap filling. Positive GHI with zero TOA
remains unavailable; observed hours with that condition:
 {manifest["positive_ghi_zero_toa_hours"]}. Negative TOA hours are also unavailable:
{manifest["negative_toa_hours"]}; raw provider values remain in the input files.</li>
<li>A_N = {manifest["parameters"]["a_n"]:g} is an explicit study assumption. The other nine
coefficients are the published mono-Si calibration. These maps are a screening scenario,
not a site-specific prediction or exact reproduction of the thesis figures.</li></ul>
<details><summary>Calibration record</summary><pre>{parameters}</pre></details></section>
<section><h2>Downloads and reproducibility</h2><p>
<a href="../degradation.nc">Maps · NetCDF</a> ·
<a href="../annual_stresses.nc">Annual stresses · NetCDF</a> ·
<a href="../map_cells.csv">Cell table · CSV</a> ·
<a href="../source_cells.csv">Selected ERA5 cells · CSV</a> ·
<a href="../manifest.json">Run manifest</a> ·
<a href="mechanisms.svg">Mechanism maps · SVG</a> ·
<a href="classes.svg">Classes · SVG</a></p>
<p>The bundle also contains one GeoJSON file per rate and one for classes. The manifest
records input SHA-256 checksums, parameters, coverage, versions and references.</p></section>
<section><h2>Attribution</h2><p>Primary scientific reference: Julián Ascencio Vásquez's
2021 thesis. Weather: Copernicus ERA5 via Open-Meteo (CC BY 4.0). Land support: CRU TS v4.10,
Climatic Research Unit, University of East Anglia (ODbL / Database Contents License).
Open-Meteo's public endpoint is for non-commercial use.</p><ol>{references}</ol></section>
</html>"""
    destination = output / "index.html"
    destination.write_text(page, encoding="utf-8")
    return destination
