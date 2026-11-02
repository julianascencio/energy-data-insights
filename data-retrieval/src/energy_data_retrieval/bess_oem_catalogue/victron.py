"""Stage reviewed MultiPlus-II and Quattro 230 V datasheet layouts offline.

The four new MultiPlus-II columns and nine explicit Quattro codes are supported. This is
candidate extraction, not an import or a claim about current product availability.
"""

from __future__ import annotations

import re
from itertools import pairwise
from typing import Any

REFERENCE_IDS = ["victron_multiplus_ii_new_230v_20261102", "victron_quattro_230v_20261102"]
MODELS = ("12/4k/160-32", "48/4k5/55-32", "48/6k5/100-50", "48/10k/150-100")
NUMBER = r"\d+(?:[.,]\d+)?"

QUATTRO_GROUPS = (
    ("12/3000/120-50/50", "24/3000/70-50/50"),
    ("12/5000/220-100/100", "24/5000/120-100/100", "48/5000/70-100/100"),
    ("24/8000/200-100/100", "48/8000/110-100/100"),
    ("48/10000/140-100/100",),
    ("48/15000/200-100/100",),
)


def parse_quattro_230v(text: str) -> list[dict[str, Any]]:
    """Stage nine explicit codes from the reviewed five-column Quattro table.

    Merged power cells apply only to codes printed in the same column. The
    slash-delimited charge currents must match that column's model count. No
    model combinations, battery capacities or peak durations are invented.
    Other specifications and source revisions still require human review.
    """
    pages = [p for p in text.split("\f") if "Charge current house battery (A) (4)" in p]
    if len(pages) != 1:
        raise ValueError("Expected one Quattro specification page")
    page = pages[0]
    if not re.search(r"Output voltage:\s*230 VAC", page):
        raise ValueError("Expected a 230 V output table")
    header = page.split("Nominal Battery Voltage")[0]
    columns: dict[str, int] = {}
    for line in header.splitlines():
        for match in re.finditer(r"\d+/\d+/\d+-\d+/\d+", line):
            model = match.group()
            if model in columns:
                raise ValueError("Duplicated Quattro model")
            # Poppler centre-aligns strings of unequal lengths within columns.
            columns[model] = match.start() + len(model) // 2
    expected = {m for group in QUATTRO_GROUPS for m in group}
    if set(columns) != expected:
        raise ValueError("Missing or unexpected Quattro models")
    centres = []
    for group in QUATTRO_GROUPS:
        points = [columns[m] for m in group]
        if max(points) - min(points) > 3:
            raise ValueError("Changed Quattro model grouping")
        centres.append(sum(points) / len(points))
    if any(b - a < 15 for a, b in pairwise(centres)):
        raise ValueError("Reordered or overlapping Quattro columns")

    def values(label: str) -> list[float]:
        raw = _row(page, label).split()
        if len(raw) != 5 or any(not re.fullmatch(NUMBER, v) for v in raw):
            raise ValueError("Expected five unqualified Quattro numeric cells")
        result = [float(v.replace(",", ".")) for v in raw]
        if any(v <= 0 for v in result):
            raise ValueError("Ratings must be positive")
        return result

    power = {t: values(f"Cont. output power at {t} °C (W)") for t in (25, 40, 65)}
    apparent = values("Cont. output power at 25 °C (VA) (3)")
    peak = values("Peak power (W)")
    raw_charge = _row(page, "Charge current house battery (A) (4)")
    charge_cells = re.split(r"\s{2,}", raw_charge)
    if len(charge_cells) != 5:
        raise ValueError("Expected five charge-current groups")
    result = []
    for i, group in enumerate(QUATTRO_GROUPS):
        tokens = [v.strip() for v in charge_cells[i].split("/")]
        if len(tokens) != len(group) or any(not re.fullmatch(NUMBER, v) for v in tokens):
            raise ValueError("Charge-current/model cardinality mismatch")
        if not peak[i] >= power[25][i] >= power[40][i] >= power[65][i]:
            raise ValueError("Invalid power-rating order")
        for model, current in zip(group, tokens, strict=True):
            amps = float(current.replace(",", "."))
            if amps <= 0:
                raise ValueError("Charge current must be positive")
            result.append(
                {
                    "manufacturer": "Victron Energy",
                    "model": f"Quattro {model}",
                    "variant": "230 V AC",
                    "power_capacity_mw": power[25][i] / 1e6,
                    "apparent_power_mva": apparent[i] / 1e6,
                    "power_basis": "ac",
                    "output_w_at_40c": power[40][i],
                    "output_w_at_65c": power[65][i],
                    "peak_output_w": peak[i],
                    "peak_duration_seconds": None,
                    "maximum_charge_current_a_at_25c": amps,
                    "locator": f"PDF page 2, column {i + 1}, model {model}",
                    "review_required": True,
                }
            )
    return result


def _row(text: str, label: str) -> str:
    matches = re.findall(rf"^[ \t]*{re.escape(label)}[ \t]+(.+)$", text, re.MULTILINE)
    if len(matches) != 1:
        raise ValueError(f"Missing, duplicated or changed Victron row: {label}")
    return matches[0].strip()


def _quantities(value: str, unit: str, count: int = 4) -> list[float]:
    pattern = rf"({NUMBER})\s*{re.escape(unit)}"
    tokens = re.findall(pattern, value)
    if len(tokens) != count or re.sub(pattern, "", value).strip():
        raise ValueError(f"Expected {count} unqualified {unit} values")
    numbers = [float(v.replace(",", ".")) for v in tokens]
    if any(v <= 0 for v in numbers):
        raise ValueError("Ratings must be positive")
    return numbers


def parse_multiplus_new_230v(text: str) -> list[dict[str, Any]]:
    """Read Poppler layout text and preserve active-power and overload boundaries.

    The four model columns must occur in the reviewed order. Only the selected
    power and charge-current rows are staged; shared cells require manual review.
    Never infer MVA from a row
    labelled apparent power but printed in kW, or nominal DC voltage from a name.
    Caller must retain original PDF and extracted-text hashes outside Git.
    """
    if "MultiPlus-II Inverter/Charger, new models" not in text:
        raise ValueError("Expected the new-model datasheet title")
    pages = [page for page in text.split("\f") if "MultiPlus-II 230V" in page]
    if len(pages) != 1:
        raise ValueError("Expected one specification page")
    header_lines = [line for line in pages[0].splitlines() if "MultiPlus-II 230V" in line]
    if len(header_lines) != 1:
        raise ValueError("Expected one model header")
    offset = header_lines[0].index("MultiPlus-II 230V")
    text = "\n".join(line[offset:] for line in pages[0].splitlines())
    header = _row(text, "MultiPlus-II 230V")
    if tuple(header.split()) != MODELS:
        raise ValueError("Missing, duplicated, reordered or unexpected model columns")
    power = {
        temp: _quantities(_row(text, f"Cont. output power at {temp} °C"), "kW")
        for temp in (25, 40, 65)
    }
    apparent_row = _row(text, "Max apparent feed-in power")
    _quantities(apparent_row, "kW")  # Reject a changed edition rather than silently mapping it.
    charge = {
        temp: _quantities(_row(text, f"Max. battery charge current at {temp} °C"), "A")
        for temp in (25, 40)
    }
    peak_row = _row(text, "Peak power")
    peak_pattern = rf"({NUMBER})\s*kW/({NUMBER})\s*(s|min)"
    peaks = re.findall(peak_pattern, peak_row)
    if len(peaks) != 4 or re.sub(peak_pattern, "", peak_row).strip():
        raise ValueError("Incomplete or changed time-qualified peak-power row")
    candidates = []
    for i, model in enumerate(MODELS):
        peak_kw, duration, unit = peaks[i]
        peak_kw, duration = float(peak_kw.replace(",", ".")), float(duration.replace(",", "."))
        if peak_kw <= 0 or duration <= 0 or not power[25][i] >= power[40][i] >= power[65][i]:
            raise ValueError("Invalid peak duration or temperature-rating order")
        candidates.append(
            {
                "manufacturer": "Victron Energy",
                "model": f"MultiPlus-II {model}",
                "variant": "230 V AC",
                "power_capacity_mw": power[25][i] / 1000,
                "power_basis": "ac",
                "power_rating_kind": "rated",
                "power_conditions": "Continuous inverter output at 25 degC",
                "output_kw_at_40c": power[40][i],
                "output_kw_at_65c": power[65][i],
                "peak_output_kw": peak_kw,
                "peak_duration_seconds": duration * (60 if unit == "min" else 1),
                "maximum_charge_current_a_at_25c": charge[25][i],
                "maximum_charge_current_a_at_40c": charge[40][i],
                "apparent_power_mva": None,
                "apparent_power_note": "Printed row is labelled apparent power but uses kW",
                "locator": f"PDF page 2, {model} column, inverter/charger rows",
                "review_required": True,
            }
        )
    return candidates
