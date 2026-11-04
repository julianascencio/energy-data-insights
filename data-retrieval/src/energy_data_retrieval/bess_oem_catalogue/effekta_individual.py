"""Stage selected facts from reviewed English EFFEKTA monobloc sheets.

Input is local ``pdftotext -layout`` output, never an automatically downloaded
archive. The reviewer supplies the exact printed heading, independently of the
filename. Staging does not reconcile identities, resolve conflicts or import.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

SOURCE_URLS = frozenset(
    {
        "https://www.effekta.com/download/datenblaetter-bt-serie-zip-datei/?wpdmdl=357",
        "https://www.effekta.com/download/datenblaetter-btl-frontterminal-serie-zip-datei/?wpdmdl=358",
    }
)
NUMBER = r"\d+(?:[.,]\d+)?"


def parse_individual_sheet(
    content: bytes, *, source_url: str, expected_model: str
) -> dict[str, Any]:
    """Read page-one identity, nominal Ah, dimensions and separate current types.

    Approximate mass is an observation, not an unqualified scalar. Monobloc Ah
    never becomes cell capacity or MWh. A C-rate never becomes amperes, and a
    short-circuit current never becomes a peak operating discharge rating.
    """
    if source_url not in SOURCE_URLS:
        raise ValueError("Unreviewed EFFEKTA archive URL")
    page = content.decode("utf-8-sig").split("\f")[0]
    headings = re.findall(r"^(BTL?\d[^\n]*?)\s+\([^\n]+\)", page, re.M)
    if headings != [expected_model]:
        raise ValueError("Printed model heading differs from reviewed identity")
    if "Specifications" not in page or "AGM" not in page:
        raise ValueError("Missing reviewed specification/chemistry markers")

    def one(pattern: str) -> tuple[str, ...]:
        hits = list(re.finditer(pattern, page, re.M | re.I))
        if len(hits) != 1:
            raise ValueError(f"Expected one field matching {pattern}")
        return hits[0].groups()

    def number(value: str) -> float:
        result = float(value.replace(",", "."))
        if result <= 0:
            raise ValueError("Nonpositive specification")
        return result

    voltage = number(one(rf"^\s*Nominal Voltage\s+({NUMBER})\s*V\s*$")[0])
    ah = number(one(rf"^\s*Nominal Capacity(?:\(20HR\))?\s+({NUMBER})\s*Ah\s*$")[0])
    dimensions = {}
    for label, key in [("Leng(?:th|ht)", "length"), ("Width", "width")]:
        value, tolerance = one(
            rf"^\s*(?:(?:Dimensions|Abmessungen)\s+)?{label}\s+"
            rf"({NUMBER})(?:\s*±\s*({NUMBER}))?\s*mm\s*$"
        )
        dimensions[key] = {
            "value_mm": number(value),
            "tolerance_mm": number(tolerance) if tolerance else None,
        }
    # Preserve each printed height label: front terminals can sit below the lid.
    heights = re.findall(
        rf"^\s*((?:H[e]?ight|Hight|Total height)[^\n]*?)\s{{2,}}"
        rf"({NUMBER})(?:\s*±\s*({NUMBER}))?\s*mm\s*$",
        page,
        re.M | re.I,
    )
    if not heights or len({h[0] for h in heights}) != len(heights):
        raise ValueError("Missing or duplicated height observations")
    for label, value, tolerance in heights:
        dimensions[label] = {
            "value_mm": number(value),
            "tolerance_mm": number(tolerance) if tolerance else None,
        }
    mass, mass_tolerance = one(
        rf"^\s*Approx\.? Weight\s+({NUMBER})\s*kg(?:\s*±\s*({NUMBER})%)?\s*$"
    )
    charge, charge_unit = one(rf"^\s*Max\. charging current(?: \(25°C\))?\s+({NUMBER})\s*(A|C)\s*$")
    peak = re.findall(
        rf"^\s*Max\. Discharge Current\s+({NUMBER})\s*A\s*\(\s*({NUMBER})\s*s\)\s*$",
        page,
        re.M | re.I,
    )
    short = re.findall(rf"^\s*Short-circuit current\s+({NUMBER})\s*A\s*$", page, re.M | re.I)
    if len(peak) + len(short) != 1:
        raise ValueError("Expected exactly one reviewed peak or short-circuit field")
    return {
        "model": expected_model,
        "voltage_v": voltage,
        "nominal_monobloc_ah": ah,
        "dimensions": dimensions,
        "approximate_mass_kg": number(mass),
        "mass_tolerance_pct": number(mass_tolerance) if mass_tolerance else None,
        "maximum_charge": {"value": number(charge), "unit": charge_unit.upper()},
        "peak_discharge": (
            {"ampere": number(peak[0][0]), "seconds": number(peak[0][1])} if peak else None
        ),
        "short_circuit_ampere": number(short[0]) if short else None,
        "source_url": source_url,
        "locator": "PDF page 1, exact heading and Specifications table",
        "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
    }
