"""Offline staging of the four reviewed BOS-G-Pro EU brochure columns.

Candidates are observations, not accepted catalogue records. In particular the
printed G60 power differs from the product page and requires human reconciliation.
"""

from __future__ import annotations

import re

MODELS = ("BOS-G25-Pro", "BOS-G40-Pro", "BOS-G60-Pro", "BOS-G80-Pro")


def parse_bos_g_pro(text: str) -> list[dict[str, object]]:
    """Stage the reviewed four-column layout; reject drift and ambiguous rows.

    Input is UTF-8 ``pdftotext -layout`` output from the EU 20260414 V1.0
    brochure. The caller must verify the original document version and rights.
    No power/energy ratios or additional configurations are calculated.
    """
    pages = text.split("\f")
    if len(pages) < 3:
        raise ValueError("Expected paginated brochure text")
    table = pages[1]
    header = re.findall(r"^\s*Battery Module Number\s+(.+)$", table, re.MULTILINE)
    if len(header) != 1 or header[0].split() != list(MODELS):
        raise ValueError("Missing, duplicate or reordered model columns")

    def values(label: str) -> list[float]:
        found = re.findall(r"^\s*" + re.escape(label) + r"\s+(.+)$", table, re.MULTILINE)
        if len(found) != 1:
            raise ValueError(f"Missing or duplicate row: {label}")
        tokens = found[0].split()
        if len(tokens) != 4 or any(not re.fullmatch(r"\d+(?:\.\d+)?", t) for t in tokens):
            raise ValueError(f"Expected four numeric columns: {label}")
        result = [float(t) for t in tokens]
        if any(v <= 0 for v in result):
            raise ValueError(f"Nonpositive value: {label}")
        return result

    energy = values("System Energy ( kWh )")
    # Poppler places the superscript footnote on its own line in this version.
    normalized = re.sub(r"(System Usable Energy \(kWh \))\s+1\s*\n", r"\1 ", table)
    table = normalized
    usable = values("System Usable Energy (kWh )")
    power = values("Rated DC Power ( kW )")
    voltage = values("System Nominal Voltage ( V )")
    if any(u > e for u, e in zip(usable, energy, strict=True)):
        raise ValueError("Usable energy exceeds system energy")
    for condition in ("90% DOD", "0.3C charge & discharge at 25°C"):
        if condition not in table:
            raise ValueError("Missing usable-energy test conditions")
    return [
        {
            "model": model,
            "system_energy_kwh": energy[i],
            "usable_dc_energy_kwh": usable[i],
            "reported_rated_dc_power_kw": power[i],
            "nominal_dc_voltage_v": voltage[i],
            "locator": f"PDF page 2, {model} column and footnote 1",
            "review_required": True,
        }
        for i, model in enumerate(MODELS)
    ]
