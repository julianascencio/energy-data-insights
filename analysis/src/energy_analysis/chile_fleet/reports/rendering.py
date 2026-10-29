"""Escaped HTML, compact SVG charts and drafts from saved scientific outputs."""

from __future__ import annotations

import html
import json
import math
from collections.abc import Mapping, Sequence

import pandas as pd

from energy_methods.references import get_references

from ..io import json_safe, row_mapping
from .assets import SCRIPT, STYLE

GROUPS = {
    "underperforming": "Below tolerance",
    "within_tolerance": "Within tolerance",
    "overperforming": "Above tolerance",
    "insufficient_comparison": "Insufficient comparison",
}


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def number(value: object) -> float | None:
    if isinstance(value, (float, int, str)):
        try:
            result = float(value)
            return result if math.isfinite(result) else None
        except ValueError:
            return None
    return None


def fmt(value: object, decimals: int = 1, *, signed: bool = False) -> str:
    numeric = number(value)
    if numeric is None:
        return "—"
    return f"{numeric:+,.{decimals}f}" if signed else f"{numeric:,.{decimals}f}"


def percent(value: object) -> str:
    numeric = number(value)
    return "—" if numeric is None else f"{numeric * 100:.1f}%"


def label(value: object, fallback: str = "") -> str:
    return value if isinstance(value, str) and value.strip() else fallback


def _json(value: object) -> str:
    return json.dumps(json_safe(value), ensure_ascii=False, indent=2, allow_nan=False)


def _card(name: str, value: str, detail: str) -> str:
    return (
        f'<article class="card"><span class="label">{escape(name)}</span>'
        f'<strong class="value">{escape(value)}</strong><small>{escape(detail)}</small></article>'
    )


def _badge(group: object) -> str:
    key = str(group) if group in GROUPS else "insufficient_comparison"
    return f'<span class="badge {key}">{GROUPS[key]}</span>'


def _definition_list(items: Sequence[tuple[str, object]]) -> str:
    return (
        '<dl class="metric-list">'
        + "".join(f"<dt>{escape(name)}</dt><dd>{escape(value)}</dd>" for name, value in items)
        + "</dl>"
    )


def _references() -> str:
    rows = []
    for reference in get_references():
        url = reference.url
        title = escape(reference.title)
        if url.startswith("https://"):
            title = f'<a href="{escape(url)}" rel="noreferrer">{title}</a>'
        rows.append(
            f"<li><strong>{title}</strong><br>{escape('; '.join(reference.authors))}"
            f" ({escape(reference.year if reference.year is not None else 'n.d.')}). "
            f'<span class="tag">{escape(reference.kind)} · {escape(reference.role)}</span>'
            f"<br>{escape(reference.note)}</li>"
        )
    return (
        '<section class="panel" id="references"><h2>References &amp; attribution</h2>'
        '<p class="muted">The doctoral thesis is the primary scholarly reference. The catalogue '
        "also records methods, data, software, standards and background literature; inclusion "
        "does not establish that every optional method or provider was used in this run.</p>"
        '<details><summary>Open the full citation catalogue</summary><ol class="references">'
        + "".join(rows)
        + '</ol></details><p class="caption">Machine-readable citations: '
        '<a href="{prefix}references.json">JSON</a> · '
        '<a href="{prefix}references.bib">BibTeX</a> · '
        '<a href="{prefix}references.md">Markdown</a></p></section>'
    )


def _shell(title: str, content: str, *, synthetic: bool, site: bool = False) -> str:
    prefix = "../" if site else ""
    notice = (
        '<div class="notice" role="note"><strong>SYNTHETIC DATA — demonstration only.</strong> '
        "These artificial observations are not evidence of actual Chilean PV performance, "
        "operating losses or damage.</div>"
        if synthetic
        else ""
    )
    nav = (
        f'<a href="{prefix}index.html">Fleet overview</a><a href="#methods">Methods</a>'
        '<a href="#references">References</a>'
        f'<a href="{prefix}manifest.json">Provenance</a>'
    )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<meta name="color-scheme" content="light"><title>{escape(title)}</title>'
        f'<style>{STYLE}</style></head><body><header><a class="brand" '
        f'href="{prefix}index.html">ENERGY DATA INSIGHTS</a><nav aria-label="Report">'
        f"{nav}</nav></header><main>{notice}{content}"
        + _references().replace("{prefix}", prefix)
        + "<footer>Generated from a saved analysis without refitting. Missing observations and "
        "reported zeros retain their original meaning. Energy gaps do not establish recoverable "
        "loss, a fault, storm damage or confirmed IEC operating causes.</footer></main>"
        f"<script>{SCRIPT}</script></body></html>\n"
    )


def _period(manifest: Mapping[str, object]) -> str:
    configuration = manifest.get("configuration")
    config = configuration if isinstance(configuration, dict) else {}
    start = config.get("report_start", manifest.get("start_inclusive", "not recorded"))
    end = config.get("report_end", manifest.get("end_exclusive", "not recorded"))
    return f"{start} → {end} (end exclusive; UTC)"


def _methods(manifest: Mapping[str, object]) -> str:
    frozen = manifest.get("model_retrained") is False
    configuration = manifest.get("configuration")
    config = configuration if isinstance(configuration, dict) else {}
    model = "Supplied frozen reference" if frozen else str(config.get("algorithm", "Saved model"))
    threshold = percent(
        config.get("minimum_reference_coverage", manifest.get("minimum_reference_coverage"))
    )
    tolerance = percent(config.get("relative_tolerance", manifest.get("relative_tolerance")))
    reference = manifest.get("reference_column", config.get("reference", "saved reference"))
    return (
        '<section class="panel" id="methods"><h2>How to read this study</h2>'
        '<div class="method-grid"><article><h3>Matched energy</h3><p>Actual and expected '
        "energy use the same valid, nonnegative hourly intervals. Only comparable records "
        "enter fleet totals. Missing observations remain missing; observed zeros remain "
        "part of the comparison.</p></article><article><h3>Coverage &amp; tolerance</h3>"
        f"<p>Required coverage: {threshold}. Site-period tolerance: ±{tolerance}. Coverage "
        "is the share of available reference energy with a valid actual observation, "
        "not completeness of every hour or a confidence interval.</p></article>"
        f"<article><h3>Reference &amp; validation</h3><p>Model: {escape(model)}. Reference: "
        f"{escape(reference)}. Held-out prediction scores are separate from final baseline "
        "fits and do not measure operating-state classification accuracy.</p></article>"
        "<article><h3>Operational screening</h3><p>IEC-informed candidate states describe "
        "observable patterns. No operating cause, availability class or recoverable loss "
        "is confirmed without operational records.</p></article>"
        "<article><h3>Typical Daily Profiles</h3><p>AVG pools eligible original observations; "
        "Y2Y keeps each year separate. P90 is the hourly empirical 90th percentile, "
        "not a 90% annual-energy exceedance estimate. Profiles use a fixed "
        "UTC-04 clock.</p></article>"
        "<article><h3>Source boundaries</h3><p>The report uses saved results and their "
        "provenance. It does not acquire new weather, retrain a model, fill a reference "
        "gap or convert optional methods into findings.</p></article></div></section>"
    )


def _bar_chart(rows: list[dict[str, object]]) -> str:
    supported = [row for row in rows if row.get("comparison_supported") is True]
    selected = sorted(
        supported, key=lambda row: abs(number(row.get("matched_deviation_mwh")) or 0), reverse=True
    )[:12]
    if not selected:
        return '<p class="muted">No comparable site-period energy totals are available.</p>'
    maximum = max(abs(number(row.get("matched_deviation_mwh")) or 0) for row in selected) or 1
    height = 36 * len(selected) + 46
    parts = [
        f'<svg class="chart" viewBox="0 0 720 {height}" role="img" '
        'aria-label="Largest signed site-period energy deviations in MWh">',
        f'<line x1="420" y1="10" x2="420" y2="{height - 25}" stroke="#bbcfc3"/>',
    ]
    for index, row in enumerate(selected):
        name = label(row.get("name"), str(row["site_id"]))
        value = number(row.get("matched_deviation_mwh")) or 0
        width = abs(value) / maximum * 165
        x = 420 - width if value < 0 else 420
        y = index * 36 + 15
        color = "#b74b3f" if value < 0 else "#357cba"
        short_name = name if len(name) <= 31 else name[:28] + "…"
        parts.append(
            f'<text x="0" y="{y + 17}" fill="#314f43" font-size="12">'
            f"<title>{escape(name)}</title>{escape(short_name)}</text>"
            f'<rect x="{x:.2f}" y="{y}" width="{width:.2f}" height="23" '
            f'rx="3" fill="{color}"><title>{escape(name)}: '
            f"{fmt(value, signed=True)} MWh</title></rect>"
            f'<text x="710" y="{y + 17}" text-anchor="end" fill="{color}" '
            f'font-size="12">{fmt(value, signed=True)}</text>'
        )
    parts.append(
        f'<text x="335" y="{height - 5}" text-anchor="middle" fill="#64776c" '
        'font-size="11">Below reference</text>'
        f'<text x="505" y="{height - 5}" text-anchor="middle" fill="#64776c" '
        'font-size="11">Above reference</text></svg>'
    )
    return "".join(parts)


def _numeric_cell(value: object, *, suffix: str = "", signed: bool = False) -> str:
    numeric = number(value)
    sort = "" if numeric is None else str(numeric)
    css = "negative" if numeric is not None and numeric < 0 else ""
    return (
        f'<td class="num {css}" data-sort="{sort}">'
        f"{fmt(value, signed=signed)}{suffix if numeric is not None else ''}</td>"
    )


def fleet_page(
    title: str,
    rows: list[dict[str, object]],
    summary: Mapping[str, object],
    manifest: Mapping[str, object],
    pages: Mapping[str, str],
    *,
    synthetic: bool,
) -> str:
    cards = "".join(
        (
            _card(
                "Actual energy",
                fmt(summary.get("matched_actual_mwh")),
                "MWh · comparable matched intervals",
            ),
            _card(
                "Expected energy",
                fmt(summary.get("matched_expected_mwh")),
                "MWh · same intervals and records",
            ),
            _card(
                "Net deviation",
                fmt(summary.get("net_deviation_pct"), signed=True) + "%",
                "Actual / expected - 1",
            ),
            _card(
                "Comparable records",
                f"{fmt(summary.get('comparable_records'), 0)} / "
                f"{fmt(summary.get('registry_records'), 0)}",
                "All registry records remain visible",
            ),
        )
    )
    headers = [
        ("Site", "text"),
        ("Region", "text"),
        ("Status", "text"),
        ("Actual · MWh", "number"),
        ("Expected · MWh", "number"),
        ("Deviation · %", "number"),
        ("Coverage", "number"),
        ("Held-out score · %", "number"),
    ]
    table_rows = []
    for row in rows:
        site_id = str(row["site_id"])
        name = label(row.get("name"), site_id)
        coverage = number(row.get("reference_energy_coverage"))
        coverage_width = max(0.0, min(1.0, coverage or 0)) * 100
        group = str(row.get("performance_group", "insufficient_comparison"))
        cells = (
            f'<td><a class="site-name" href="{escape(pages[site_id])}">{escape(name)}</a>'
            f'<br><span class="caption">{escape(site_id)}</span></td>'
            f"<td>{escape(label(row.get('region'), '—'))}</td><td>{_badge(group)}</td>"
            + _numeric_cell(row.get("matched_actual_mwh"))
            + _numeric_cell(row.get("matched_expected_mwh"))
            + _numeric_cell(row.get("deviation_pct"), signed=True)
            + f'<td class="num" data-sort="{coverage if coverage is not None else ""}">'
            f'{percent(coverage)}<div class="coverage"><span style="width:{coverage_width:.2f}%">'
            "</span></div></td>" + _numeric_cell(row.get("test_score_pct"))
        )
        table_rows.append(f'<tr data-group="{escape(group)}">{cells}</tr>')
    table = (
        '<div class="scroll"><table data-fleet-table><thead><tr>'
        + "".join(
            f'<th scope="col" data-kind="{kind}" class="{"num" if kind == "number" else ""}">'
            f'<button type="button" aria-label="Sort by {escape(name)}">'
            f"{escape(name)} ↕</button></th>"
            for name, kind in headers
        )
        + "</tr></thead><tbody>"
        + "".join(table_rows)
        + "</tbody></table></div>"
    )
    overview = _definition_list(
        [
            ("Below tolerance", fmt(summary.get("underperforming_records"), 0)),
            ("Within tolerance", fmt(summary.get("within_tolerance_records"), 0)),
            ("Above tolerance", fmt(summary.get("overperforming_records"), 0)),
            ("Insufficient comparison", fmt(summary.get("insufficient_comparison_records"), 0)),
            ("Site-period shortfall", fmt(summary.get("site_shortfall_mwh")) + " MWh"),
            ("Site-period excess", fmt(summary.get("site_excess_mwh")) + " MWh"),
            ("Signed fleet balance", fmt(summary.get("net_deviation_mwh"), signed=True) + " MWh"),
        ]
    )
    content = (
        f'<section class="hero"><span class="eyebrow">Chile · Solar performance study</span>'
        f'<h1>{escape(title)}</h1><p class="muted">{escape(_period(manifest))}</p>'
        "<p>Compare the fleet on a common energy basis, then open a site to inspect coverage, "
        "prediction validation, weather, operating screens and daily profiles.</p></section>"
        f'<section class="cards" aria-label="Fleet indicators">{cards}</section>'
        '<div class="two"><section class="panel"><h2>Where the energy differs</h2>'
        '<p class="caption">Largest absolute signed site-period deviations; comparable records '
        f'only. Values in MWh.</p>{_bar_chart(rows)}</section><section class="panel">'
        f'<h2>Fleet accounting</h2>{overview}<p class="caption">Shortfall and excess are '
        "calculated separately at site-period level. Hourly fluctuations can cancel within "
        "a site period; these gaps are not estimates of recoverable losses.</p></section></div>"
        '<section class="panel" id="sites"><h2>Explore every site</h2>'
        '<p class="muted">Open a site for its evidence. Click a heading to sort the table.</p>'
        '<div class="toolbar"><label>Search sites<input id="site-search" type="search" '
        'placeholder="Name, ID or region"></label><label>Comparison group<select '
        'id="group-filter"><option value="">All groups</option>'
        + "".join(f'<option value="{key}">{value}</option>' for key, value in GROUPS.items())
        + '</select></label></div><p class="caption" id="visible-count" aria-live="polite">'
        f'{len(rows)} sites shown</p>{table}<p class="caption">Actual and expected columns '
        "show the matched sums for each record, including records excluded from fleet totals for "
        "insufficient comparison. A dash means unavailable; it does not mean zero.</p></section>"
        + _methods(manifest)
        + '<section class="panel"><h2>Reproducible outputs</h2><p>'
        '<a href="data.json">Report data</a> · <a href="manifest.json">Input/output hashes</a> · '
        '<a href="website_article.md">Website article draft</a> · '
        '<a href="linkedin_post.md">LinkedIn post draft</a></p>'
        '<p class="caption">Drafts are generated locally. Nothing is posted.</p></section>'
    )
    return _shell(title, content, synthetic=synthetic)


def _line_chart(
    labels: Sequence[str],
    series: Sequence[tuple[str, Sequence[float | None], str]],
    *,
    description: str,
    unit: str,
) -> str:
    if not labels:
        return '<p class="muted">No observations are available for this chart.</p>'
    finite = [v for _, values, _ in series for v in values if v is not None]
    if not finite:
        return '<p class="muted">No qualified values are available for this chart.</p>'
    maximum = max(finite) or 1.0
    minimum = min(0.0, min(finite))
    scale = maximum - minimum or 1.0
    left, top, width, height = 63.0, 25.0, 620.0, 185.0
    parts = [
        '<svg class="chart" viewBox="0 0 720 258" role="img" '
        f'aria-label="{escape(description)}"><title>{escape(description)}</title>'
    ]
    for tick in range(5):
        y = top + height * tick / 4
        value = maximum - scale * tick / 4
        parts.append(
            f'<line x1="{left}" y1="{y}" x2="{left + width}" y2="{y}" stroke="#e1eae4"/>'
            f'<text x="{left - 8}" y="{y + 4}" text-anchor="end" fill="#61766a" '
            f'font-size="11">{fmt(value)}</text>'
        )
    count = len(labels)
    x_positions = [left + (i * width / max(count - 1, 1)) for i in range(count)]
    for name, values, color in series:
        segments: list[str] = []
        active = False
        for index, value in enumerate(values):
            if value is None:
                active = False
                continue
            x, y = x_positions[index], top + (maximum - value) / scale * height
            segments.append(f"{'L' if active else 'M'}{x:.2f},{y:.2f}")
            active = True
        parts.append(
            f'<path d="{" ".join(segments)}" fill="none" stroke="{color}" stroke-width="2.3">'
            f"<title>{escape(name)}</title></path>"
        )
        if count <= 100:
            for index, value in enumerate(values):
                if value is None:
                    continue
                y = top + (maximum - value) / scale * height
                parts.append(
                    f'<circle cx="{x_positions[index]:.2f}" cy="{y:.2f}" r="2" fill="{color}">'
                    f"<title>{escape(labels[index])} · {escape(name)}: {fmt(value, 3)} "
                    f"{escape(unit)}</title></circle>"
                )
    for index in sorted({0, count // 2, count - 1}):
        parts.append(
            f'<text x="{x_positions[index]:.2f}" y="234" text-anchor="middle" '
            f'font-size="10" fill="#61766a">{escape(labels[index][:16])}</text>'
        )
    parts.append(f'<text x="10" y="13" font-size="10" fill="#61766a">{escape(unit)}</text></svg>')
    parts.append(
        '<div class="legend">'
        + "".join(
            f'<span><i class="dot" style="background:{color}"></i>{escape(name)}</span>'
            for name, _, color in series
        )
        + "</div>"
    )
    return "".join(parts)


def energy_series(hourly: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Bound display points with matched energy sums and explicit empty bins."""
    frame = hourly[["timestamp", "actual_mwh", "expected_mwh"]].copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    actual = pd.to_numeric(frame["actual_mwh"], errors="raise")
    expected = pd.to_numeric(frame["expected_mwh"], errors="raise")
    matched = actual.ge(0) & expected.ge(0) & actual.lt(float("inf")) & expected.lt(float("inf"))
    frame.loc[~matched, ["actual_mwh", "expected_mwh"]] = float("nan")
    frame = frame.set_index("timestamp").sort_index()
    granularity = "hourly"
    if len(frame) > 744:
        frame = frame.resample("D").sum(min_count=1)
        granularity = "daily"
    if len(frame) > 744:
        frame = frame.resample("MS").sum(min_count=1)
        granularity = "monthly"
    if len(frame) > 744:
        frame = frame.resample("YS").sum(min_count=1)
        granularity = "yearly"
    if len(frame) > 744:
        raise ValueError("Report chart exceeds the supported 744-year span")
    return frame, granularity


def _time_chart(hourly: pd.DataFrame) -> str:
    if hourly.empty or not {"timestamp", "actual_mwh", "expected_mwh"} <= set(hourly):
        return '<p class="muted">Saved hourly evidence is unavailable for this comparison.</p>'
    frame, granularity = energy_series(hourly)
    labels = [str(v)[:16] for v in frame.index]
    chart = _line_chart(
        labels,
        [
            ("Actual", [number(v) for v in frame["actual_mwh"]], "#157656"),
            ("Expected", [number(v) for v in frame["expected_mwh"]], "#357cba"),
        ],
        description=f"Matched actual and expected energy, {granularity} UTC intervals",
        unit="MWh",
    )
    return chart + (
        f'<p class="caption">{escape(granularity.capitalize())} matched sums, UTC interval start. '
        "Aggregation preserves energy and gaps with no valid pair remain blank. This figure "
        "uses the report period only; it does not treat missing observations as zero.</p>"
    )


def _status_panel(hourly: pd.DataFrame, manifest: Mapping[str, object]) -> str:
    configuration = manifest.get("configuration")
    config = configuration if isinstance(configuration, dict) else {}
    prefix = "heldout" if config.get("reference") == "heldout" else "final"
    column = f"{prefix}_status"
    if column not in hourly:
        return (
            '<p class="muted">No saved hourly operating screens exist for this output. '
            "Frozen-reference accounting does not reconstruct them.</p>"
        )
    counts = hourly[column].value_counts(dropna=False)
    rows = "".join(
        f'<tr><td>{escape(str(state).replace("_", " "))}</td><td class="num">'
        f"{int(count):,}</td></tr>"
        for state, count in counts.items()
    )
    return (
        f'<p class="caption">Saved {prefix} reference · report period · '
        'candidate patterns, operating cause unconfirmed.</p><div class="scroll"><table>'
        '<thead><tr><th>Screening state</th><th class="num">Hours</th></tr></thead>'
        f"<tbody>{rows}</tbody></table></div>"
    )


def _model_panel(model: Mapping[str, object]) -> str:
    if not model:
        return '<p class="muted">Model fit metadata was not part of this saved comparison.</p>'
    raw_metrics = model.get("heldout_metrics")
    metrics = raw_metrics if isinstance(raw_metrics, dict) else {}
    result = _definition_list(
        [
            ("Held-out matched hours", fmt(metrics.get("matched_hours"), 0)),
            ("Prediction score", fmt(metrics.get("score_pct")) + "%"),
            ("MAE · MWh", fmt(metrics.get("mae_mwh"), 3)),
            ("RMSE · MWh", fmt(metrics.get("rmse_mwh"), 3)),
            ("Prediction bias · %", fmt(metrics.get("bias_pct"), 3, signed=True)),
        ]
    )
    for stage in ("heldout", "final"):
        raw = model.get(stage)
        details = raw if isinstance(raw, dict) else {}
        result += (
            f"<details><summary>{stage.capitalize()} fit: "
            f"{escape(details.get('status', 'unavailable'))}</summary>"
            f"<pre>{escape(_json(details))}</pre></details>"
        )
    return result + (
        '<p class="caption">Held-out metrics concern later observations excluded from model '
        "fitting. Final-model baseline predictions are in-sample. Scores are not fault "
        "classification accuracy and no minimum score is guaranteed.</p>"
    )


def _tdp_panel(tdp: Mapping[str, pd.DataFrame]) -> str:
    avg = tdp.get("avg", pd.DataFrame())
    if avg.empty:
        return '<p class="muted">No saved Typical Daily Profiles are available for this site.</p>'
    parts = [
        '<p class="muted">Stored profiles from all supplied history, separate from the '
        "fleet report period. Fixed UTC-04 clock; values are hourly energy in MWh.</p>",
        '<div class="small-grid">',
    ]
    for month, group in avg.groupby("month", sort=True, observed=True):
        group = group.sort_values("hour")
        parts.append(
            f"<article><h3>Month {escape(month)} · AVG</h3>"
            + _line_chart(
                [f"{int(h):02d}:00" for h in group["hour"]],
                [
                    ("P50", [number(v) for v in group["p50"]], "#157656"),
                    ("P90", [number(v) for v in group["p90"]], "#357cba"),
                ],
                description=f"Typical daily energy profile, calendar month {month}",
                unit="MWh per hourly interval",
            )
            + "</article>"
        )
    parts.append("</div>")
    y2y = tdp.get("y2y", pd.DataFrame())
    if not y2y.empty:
        # A compact per-year/month table keeps decades of profiles out of the dashboard.
        rows = []
        for (year, month), group in y2y.groupby(["year", "month"], sort=True, observed=True):
            qualified = pd.to_numeric(group["p50"], errors="raise").notna()
            rows.append(
                f"<tr><td>{escape(year)}</td><td>{escape(month)}</td>"
                f'<td class="num">{fmt(group["useful_days"].max(), 0)}</td>'
                f'<td class="num">{int(qualified.sum())} / 24</td>'
                f'<td class="num">{fmt(group["n"].min(), 0)}</td></tr>'
            )
        parts.append(
            '<details><summary>Y2Y qualification by year and month</summary><div class="scroll">'
            '<table><thead><tr><th>Year</th><th>Month</th><th class="num">Useful days</th>'
            '<th class="num">Qualified bins</th><th class="num">Minimum bin observations</th>'
            f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div></details>"
        )
    coverage = tdp.get("coverage", pd.DataFrame())
    if not coverage.empty:
        parts.append(
            "<details><summary>Profile coverage and filtering audit</summary>"
            f"<pre>{escape(_json(list(row_mapping(coverage))))}</pre></details>"
        )
    parts.append(
        '<p class="caption">Only stored qualified P50/P90 values are plotted. Unqualified '
        "bins remain blank. P90 is an hourly empirical quantile and must not be interpreted "
        "as annual P90 energy. No additional profile fitting occurs here.</p>"
    )
    return "".join(parts)


def site_page(
    row: Mapping[str, object],
    manifest: Mapping[str, object],
    hourly: pd.DataFrame,
    model: Mapping[str, object],
    tdp: Mapping[str, pd.DataFrame],
    *,
    synthetic: bool,
) -> str:
    name = label(row.get("name"), str(row["site_id"]))
    cards = "".join(
        [
            _card(
                "Matched actual", fmt(row.get("matched_actual_mwh")), "MWh · valid paired intervals"
            ),
            _card(
                "Matched expected", fmt(row.get("matched_expected_mwh")), "MWh · the same intervals"
            ),
            _card(
                "Site deviation",
                fmt(row.get("deviation_pct"), signed=True) + "%",
                "Unavailable if comparison is unsupported",
            ),
            _card(
                "Reference coverage",
                percent(row.get("reference_energy_coverage")),
                "Energy-weighted; not all-hour completeness",
            ),
        ]
    )
    quality = _definition_list(
        [
            ("Hours in report window", fmt(row.get("hours_in_window"), 0)),
            ("Valid reported hours", fmt(row.get("reported_valid_hours"), 0)),
            ("Matched hours", fmt(row.get("matched_hours"), 0)),
            ("Reported zero hours", fmt(row.get("reported_zero_hours"), 0)),
            ("Invalid generation hours", fmt(row.get("negative_or_infinite_actual_hours"), 0)),
            ("Available reference energy", fmt(row.get("available_reference_mwh")) + " MWh"),
            ("Site-period shortfall", fmt(row.get("site_shortfall_mwh")) + " MWh"),
            ("Site-period excess", fmt(row.get("site_excess_mwh")) + " MWh"),
        ]
    )
    weather = []
    for field, field_label, unit in (
        ("ghi_wm2", "GHI", "W/m²"),
        ("temperature_c", "Air temperature", "°C"),
        ("wind_speed_ms", "Wind speed", "m/s"),
        ("gust_ms", "Gust", "m/s"),
    ):
        weather.append(
            f'<tr><td>{escape(field_label)}</td><td class="num">'
            f"{fmt(row.get(f'{field}_valid_hours'), 0)}</td>"
            f'<td class="num">{fmt(row.get(f"{field}_minimum"))}</td>'
            f'<td class="num">{fmt(row.get(f"{field}_average"))}</td>'
            f'<td class="num">{fmt(row.get(f"{field}_maximum"))}</td><td>{escape(unit)}</td></tr>'
        )
    unsupported = (
        '<p class="notice">This registry record does not meet comparison requirements '
        "and is excluded from comparable fleet energy totals.</p>"
        if row.get("comparison_supported") is not True
        else ""
    )
    content = (
        '<section class="hero"><span class="eyebrow">Site evidence</span>'
        f'<h1>{escape(name)}</h1><p class="muted">{escape(row["site_id"])} · '
        f"{escape(label(row.get('region'), 'Region not recorded'))}</p>"
        f'<p class="caption">{escape(_period(manifest))}</p>{_badge(row.get("performance_group"))}'
        f'</section>{unsupported}<section class="cards">{cards}</section>'
        '<section class="panel"><h2>Actual &amp; expected energy</h2>'
        f'{_time_chart(hourly)}</section><div class="two"><section class="panel">'
        f'<h2>Coverage &amp; accounting</h2>{quality}</section><section class="panel">'
        f"<h2>Model validation</h2>{_model_panel(model)}</section></div>"
        '<section class="panel"><h2>Weather context</h2><div class="scroll"><table>'
        '<thead><tr><th>Variable</th><th class="num">Valid hours</th><th class="num">Minimum</th>'
        '<th class="num">Mean</th><th class="num">Maximum</th><th>Unit</th></tr></thead>'
        f'<tbody>{"".join(weather)}</tbody></table></div><p class="caption">Saved report-period '
        "statistics. Weather context is not proof of an operating cause; provider and interval "
        "semantics remain those of the source analysis.</p></section>"
        '<section class="panel"><h2>Hourly operating screens</h2>'
        f'{_status_panel(hourly, manifest)}</section><section class="panel">'
        "<h2>Typical Daily Profiles</h2>"
        f"{_tdp_panel(tdp)}</section>" + _methods(manifest)
    )
    return _shell(name + " · PV performance", content, synthetic=synthetic, site=True)


def publication_drafts(
    title: str, summary: Mapping[str, object], manifest: Mapping[str, object], *, synthetic: bool
) -> tuple[str, str]:
    evidence = (
        "SYNTHETIC DATA: artificial demonstration only; not measured Chilean fleet performance."
        if synthetic
        else "This draft summarizes user-supplied saved analysis outputs; source quality and "
        "operational causes require the accompanying provenance."
    )
    main = get_references()[0]
    thesis = f"{'; '.join(main.authors)} ({main.year}). *{main.title}*. {main.url}"
    article = (
        f"# DRAFT — {title}\n\n{evidence}\n\n"
        f"Study period: {_period(manifest)}.\n\n"
        "## What the saved results show\n\n"
        f"The registry contains {fmt(summary.get('registry_records'), 0)} records, of which "
        f"{fmt(summary.get('comparable_records'), 0)} meet the comparison requirements. "
        f"{fmt(summary.get('insufficient_comparison_records'), 0)} records remain visible "
        "as insufficient comparisons and do not enter the comparable fleet totals.\n\n"
        f"On matched valid intervals, actual energy is {fmt(summary.get('matched_actual_mwh'))} "
        f"MWh and expected energy is {fmt(summary.get('matched_expected_mwh'))} MWh. "
        f"The signed balance is {fmt(summary.get('net_deviation_mwh'), signed=True)} MWh "
        f"({fmt(summary.get('net_deviation_pct'), signed=True)}%).\n\n"
        f"Site-period shortfall totals {fmt(summary.get('site_shortfall_mwh'))} MWh, while "
        f"site-period excess totals {fmt(summary.get('site_excess_mwh'))} MWh. Keeping these "
        "separate avoids hiding one site's gap behind another site's excess. They are "
        "model-relative differences, not established recoverable losses.\n\n"
        "## How the evidence should be interpreted\n\n"
        "Actual and expected energy use identical valid intervals. Coverage measures the "
        "available reference energy supported by actual observations, not all-hour completeness. "
        "Missing values stay missing and reported zeros remain in energy accounting. "
        "Held-out prediction scores are separate from in-sample final reference fitting. "
        "IEC-informed operating screens remain unconfirmed until checked against operational "
        "records; the outputs do not establish outages, storm damage or recoverable loss.\n\n"
        "The report generator does not fit models, change expected generation, retrieve new "
        "measurements or publish this draft. See index.html, the site pages and manifest.json "
        "for the evidence and file hashes.\n\n"
        f"## Primary scholarly reference\n\n{thesis}\n\n"
        "The complete method, dataset, software and standards catalogue is in references.md "
        "and references.bib. Background and optional items are explicitly identified.\n"
    )
    post = (
        f"DRAFT — {title}\n\n{evidence}\n\n"
        f"{fmt(summary.get('comparable_records'), 0)} of "
        f"{fmt(summary.get('registry_records'), 0)} registry records support an energy comparison "
        "in this saved study.\n\n"
        f"Matched actual: {fmt(summary.get('matched_actual_mwh'))} MWh\n"
        f"Matched expected: {fmt(summary.get('matched_expected_mwh'))} MWh\n"
        f"Signed difference: {fmt(summary.get('net_deviation_mwh'), signed=True)} MWh\n\n"
        "The useful part is the evidence behind those totals: coverage, held-out model "
        "validation, site-level differences and traceable references. Missing observations "
        "are not zero production, and an energy gap is not a confirmed fault "
        "or recoverable loss.\n\n"
        f"Primary reference: {thesis}\n\n"
        "Review the report and source provenance before publication. "
        "This text has not been posted.\n"
    )
    return article, post
