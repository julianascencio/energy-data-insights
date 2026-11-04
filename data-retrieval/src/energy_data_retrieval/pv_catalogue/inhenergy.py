"""Offline staging of reviewed INHENERGY SI technical-table columns.

Input is Poppler ``pdftotext -layout`` output from a separately checksum-verified
PDF. Only the reviewed model sequence is accepted. Shared scalar cells may repeat
across models; partially merged cells and wrapped rows require manual review.
No network, model-name rating inference, current summation or canonical upsert.
"""

from __future__ import annotations

import math
import re
import unicodedata


def read_inhenergy_layout(text: str, *, models: list[str]) -> list[dict[str, object]]:
    """Extract exact power/current columns, refusing layout or identity drift."""
    text = unicodedata.normalize("NFKC", text)
    if "INHENERGY CO., LTD." not in text or "GRID-CONNECTED INVERTER" not in text:
        raise ValueError("Not the reviewed INHENERGY technical-table format")
    if not models or len(set(models)) != len(models):
        raise ValueError("Reviewed model identities must be nonempty and unique")
    headers = [line for line in text.splitlines() if "Technical Data" in line]
    if len(headers) != 1:
        raise ValueError("Expected exactly one technical table")
    observed = re.findall(r"SI-\s*\d+(?:\.\d+)?K(?:-[ST]2)?", headers[0])
    observed = [re.sub(r"\s+", "", model) for model in observed]
    if observed != models:
        raise ValueError("Model sequence differs from reviewed exact identities")

    def row(label: str) -> str:
        found = [line.split(label, 1)[1].strip() for line in text.splitlines() if label in line]
        if len(found) != 1 or not found[0]:
            raise ValueError(f"Missing, duplicate or wrapped row: {label}")
        return found[0]

    def quantities(label: str, unit: str) -> list[float]:
        value = row(label)
        pattern = re.compile(rf"(\d+(?:\.\d+)?)\s*({unit})", re.IGNORECASE)
        matches = list(pattern.finditer(value))
        if pattern.sub("", value).strip() or len(matches) not in {1, len(models)}:
            raise ValueError(f"Unresolved units or partially merged cells: {label}")
        values = [float(m[1]) * (1000 if m[2].lower() == "kw" else 1) for m in matches]
        if not all(math.isfinite(v) and v > 0 for v in values):
            raise ValueError(f"Nonpositive/nonfinite physical quantity: {label}")
        return values * len(models) if len(values) == 1 else values

    columns = {
        "pac_rated_w": quantities("Rated output power", "kW|W"),
        "output_current_max_a": quantities("Max. output current", "A"),
        "vdc_max_v": quantities("Max. PV input voltage", "V"),
        "max_output_power_w": quantities("Max. output power", "kW|W"),
        "max_pv_access_power_w": quantities("Max. PV access power", "kW|W"),
        "max_pv_input_power_w": quantities("Max. PV input power", "kW|W"),
        "rated_output_current_a": quantities("Rated output current", "A"),
    }
    shared = {
        "operating_voltage_as_reported": row("Operation voltage range"),
        "ac_voltage_as_reported": row("Rated output voltage"),
        "frequency_as_reported": row("Rated output frequency"),
        "table_mppt_current_cells_as_reported": row("MPPT max."),
        "dimensions_as_reported": row("Dimensions (L/W/H) in mm"),
        "table_weight_cells_as_reported": row("Weight"),
        "table_cooling_cells_as_reported": row("Heat dissipation mode"),
        "night_power_as_reported": row("Self-Consumption night"),
        "communications_as_reported": row("Communication interface"),
        "warranty_as_reported": row("Warranty"),
    }
    return [
        {"model": model, **{key: values[i] for key, values in columns.items()}, **shared}
        for i, model in enumerate(models)
    ]
