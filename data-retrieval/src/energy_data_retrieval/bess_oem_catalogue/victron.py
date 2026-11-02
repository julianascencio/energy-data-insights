"""Stage the reviewed four-column MultiPlus-II new-model datasheet offline.

Only the 230 V 12/4k, 48/4k5, 48/6k5 and 48/10k layout is supported. This is
candidate extraction, not an import or a claim about current product availability.
"""

from __future__ import annotations

import re
from typing import Any

REFERENCE_IDS = ["victron_multiplus_ii_new_230v_20261102"]
MODELS = ("12/4k/160-32", "48/4k5/55-32", "48/6k5/100-50", "48/10k/150-100")
NUMBER = r"\d+(?:[.,]\d+)?"


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
