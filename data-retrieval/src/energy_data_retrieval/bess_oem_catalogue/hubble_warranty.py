"""Stage numeric warranty observations from reviewed local Hubble warranty text.

This does not establish sale-date eligibility, resolve contradictory monitoring
clauses, assign warranties to models, or reinterpret design life as warranty.
"""

import re

SCOPES = (
    "HV-SERIES (100Ah)",
    "HV-SERIES (280Ah/314Ah)",
    "AM-4",
    "AM5+",
    "AM10+",
    "AM16+",
    "BLADE 10KW",
)


def parse_warranty(text: str, *, scope: str) -> dict:
    """Return separately scoped cell, electronics and monitoring observations."""
    if scope not in SCOPES:
        raise ValueError("Unreviewed warranty scope")
    flat = " ".join(text.replace("\x02", "-").split())
    if not flat.startswith("HUBBLE " + scope + " BATTERY WARRANTY"):
        raise ValueError("Wrong exact warranty heading")
    if "Battery Warranty" not in flat or "BMS" not in flat or "Warranty Claims Process" not in flat:
        raise ValueError("Incomplete warranty")
    cell = flat.split("Battery Warranty", 1)[1].split("Warranty Conditions", 1)[0]
    years = re.findall(r"(?:at least )?(\d+) years(?:\u2019 service life| or deliver)", cell)
    if years != ["10"] or "date of purchase from Hubble Energy" not in cell:
        raise ValueError("Changed cell term or start basis")
    cycles = re.findall(r"deliver (?:at least )?([\d,]+) (?:charge-\s*discharge )?cycles", cell)
    unlimited = bool(
        re.search(r"unlimited charge-\s*discharge cycles within the warranty period", cell)
    )
    if (len(cycles) != 1 and not unlimited) or (cycles and unlimited):
        raise ValueError("Missing or ambiguous cycle limit")
    if cycles and not re.search(r"which\s*ever event occurs first", cell):
        raise ValueError("Missing earlier-of condition")
    electronics = re.findall(r"standard (\d+)-year warranty", flat)
    temperatures = re.findall(r"Battery temperature below (\d+) degrees Celsius", flat)
    fallbacks = re.findall(r"(?:reduced to (\d+) years|reverting to a (\d+)-year warranty)", flat)
    fallback_values = sorted({int(a or b) for a, b in fallbacks})
    if len(electronics) != 1 or len(temperatures) != 1:
        raise ValueError("Missing or repeated electronics/temperature terms")
    if scope == "AM-4" and fallback_values:
        raise ValueError("Unexpected AM-4 monitoring term")
    if scope != "AM-4" and not fallback_values:
        raise ValueError("Missing monitoring fallback")
    return {
        "scope": scope,
        "cell_warranty_years": int(years[0]),
        "cell_cycle_limit": int(cycles[0].replace(",", "")) if cycles else None,
        "termination": "earlier_of_years_or_cycles"
        if cycles
        else "years_with_unlimited_cycles_within_term",
        "start_basis": "Hubble purchase tax invoice date",
        "electronics_warranty_years": int(electronics[0]),
        "warranty_battery_temperature_strictly_below_c": int(temperatures[0]),
        "monitoring_fallback_years_observed": fallback_values,
        "monitoring_conflict": len(fallback_values) > 1,
    }
