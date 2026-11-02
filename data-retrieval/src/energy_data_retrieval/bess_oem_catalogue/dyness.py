"""Stage the reviewed 2025 Dyness STACK100 manual's explicit configurations.

This offline parser accepts Poppler ``pdftotext -layout`` output for the printed
V2 (2025-03-07) table only. It produces factual candidates, not canonical records.
No option combinations, power, usable energy or current availability are inferred.
A changed edition/layout must receive a separate review before parsing is widened.
"""

from __future__ import annotations

import re
from typing import Any

REFERENCE_IDS = ["dyness_stack100_manual_20250307"]


def _row(page: str, label: str) -> str:
    match = re.search(rf"^[ \t]*{re.escape(label)}[ \t]+(.+)$", page, re.MULTILINE)
    if match is None:
        raise ValueError(f"Missing or changed STACK100 row: {label}")
    return match.group(1).strip()


def parse_stack100_manual(text: str) -> list[dict[str, Any]]:
    """Extract thirteen named strings from the reviewed manual's three table pages.

    Input is offline layout-preserving text, with form-feed page separators.
    Output energy is the printed, rounded kWh value with unspecified basis; voltage
    limits are V DC. Printed page/model locators accompany every candidate.
    Duplicate, missing, reordered or unexpected columns fail closed. The caller
    must retain the original PDF checksum and inspect all additional specifications.
    """
    if not re.search(r"\bV2\s+2025\.03\.07\b", text):
        raise ValueError("Expected printed STACK100 manual revision V2, 2025-03-07")
    if "Table 2-1 Parameters of the STACK100 system" not in text:
        raise ValueError("Missing reviewed STACK100 Table 2-1 heading")
    candidates: list[dict[str, Any]] = []
    pages = [p for p in text.split("\f") if "System Modules Serial Number" in p]
    if len(pages) != 3:
        raise ValueError("Expected exactly three STACK100 configuration table pages")
    expected_groups = [list(range(3, 8)), list(range(8, 13)), list(range(13, 16))]
    for index, (page, expected) in enumerate(zip(pages, expected_groups, strict=True)):
        if "STACK100 User Manual" not in page:
            raise ValueError("Unexpected document/table context")
        header = page.split("Module Voltage/Capacity", 1)[0]
        models = [int(n) for n in re.findall(r"\b100-(\d+)s\b", header)]
        if models != expected:
            raise ValueError("Missing, duplicated, reordered or unexpected model columns")
        counts_row = _row(page, "System Modules Serial Number")
        if not re.fullmatch(r"\d+(?:\s+\d+)*", counts_row):
            raise ValueError("Invalid module-count row")
        counts = [int(n) for n in counts_row.split()]
        if counts != models:
            raise ValueError("Module counts do not match exact model identities")
        energy_row = _row(page, "System Energy Range")
        energy_tokens = re.findall(r"(\d+(?:\.\d+)?)\s*kWh", energy_row)
        voltage_row = _row(page, "Operating Voltage")
        voltage_tokens = re.findall(r"(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)V", voltage_row)
        if len(energy_tokens) != len(models) or len(voltage_tokens) != len(models):
            raise ValueError("Incomplete energy or voltage columns")
        if re.sub(r"\d+(?:\.\d+)?\s*kWh", "", energy_row).strip():
            raise ValueError("Unexpected energy qualifier or unit")
        if re.sub(r"\d+(?:\.\d+)?-\d+(?:\.\d+)?V", "", voltage_row).strip():
            raise ValueError("Unexpected voltage qualifier or unit")
        for n, energy, (lower, upper) in zip(models, energy_tokens, voltage_tokens, strict=True):
            energy_kwh, lower_v, upper_v = float(energy), float(lower), float(upper)
            if energy_kwh <= 0 or not 0 < lower_v < upper_v:
                raise ValueError("Invalid energy or ordered operating-voltage limits")
            candidates.append(
                {
                    "manufacturer": "Dyness",
                    "model": f"STACK100-{n}s",
                    "module_count": n,
                    "energy_kwh": energy_kwh,
                    "energy_basis": "unspecified",
                    "dc_voltage_min_v": lower_v,
                    "dc_voltage_max_v": upper_v,
                    "document_revision": "Printed V2, 2025-03-07; filename V29",
                    "locator": f"Printed page {index + 7}, Table 2-1, STACK100-{n}s column",
                    "review_required": True,
                }
            )
    return candidates
