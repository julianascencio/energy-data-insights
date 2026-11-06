"""Stage the reviewed Solar MD SS70xx-05 table from a local PDF extraction.

Input is the ten-row table on PDF page 4 of the July 2025 URL edition.
The caller reviews source rights, the page image and exact component identity.
No network access, canonical writes, warranty inference or Cartesian expansion.
"""

import re

MODELS = tuple(
    "SS" + code + "-05"
    for code in (
        "7008",
        "7010",
        "7011",
        "7013",
        "7014",
        "7016",
        "7018",
        "7019",
        "7021",
        "7022",
        "7024",
        "7026",
        "7027",
    )
)
LABELS = (
    "",
    "Rated capacity",
    "Nominal Power (@0.5C)",
    "Nominal Voltage",
    "Operational Voltage (Min/Max)",
    "Communication",
    "Number of battery modules",
    "Battery Rack",
    "Total weight1",
    "Dimensions W x D x H",
)
NUMBER = r"(\d+(?:\.\d+)?)"


def parse_ss70xx(table: list[list[str | None]], *, edition: str) -> list[dict]:
    """Validate exact headings, units, model order and DC voltage envelopes."""
    if edition != "2025-07 URL edition" or len(table) != len(LABELS):
        raise ValueError("Unreviewed edition or row count")
    if any(len(row) != 14 or any(cell is None for cell in row) for row in table):
        raise ValueError("Missing or shifted cells")
    rows = [[re.sub(r"\s+", " ", str(cell)).strip() for cell in row] for row in table]
    if tuple(row[0] for row in rows) != LABELS or tuple(rows[0][1:]) != MODELS:
        raise ValueError("Changed headings, units or model identities")

    def match(pattern: str, value: str) -> tuple[str, ...]:
        result = re.fullmatch(pattern, value)
        if not result:
            raise ValueError("Invalid number or unit: " + value)
        return result.groups()

    result = []
    for i, model in enumerate(MODELS, 1):
        energy = float(match(NUMBER + r" kWh", rows[1][i])[0])
        power = float(match(NUMBER + r" kW", rows[2][i])[0])
        voltage = float(match(NUMBER + r"V", rows[3][i])[0])
        low, high = map(float, match(NUMBER + r"V - " + NUMBER + r"V", rows[4][i]))
        count = int(match(r"(\d+)", rows[6][i])[0])
        rack = rows[7][i]
        weight = float(match(NUMBER + r" kg", rows[8][i])[0])
        dims = list(
            map(float, match(NUMBER + r"mm x " + NUMBER + r"mm x " + NUMBER + r"mm", rows[9][i]))
        )
        if count != i + 4 or not 0 < low < voltage < high or min(energy, power, weight, *dims) <= 0:
            raise ValueError("Invalid configuration or voltage bounds")
        if rows[5][i] != "CANBUS / RS485 / Ethernet" or not re.fullmatch(
            r"CB5[12]x_HV-H[689]-R[12]", rack
        ):
            raise ValueError("Changed communication or rack configuration")
        result.append(
            dict(
                model=model,
                energy_kwh=energy,
                nominal_power_kw=power,
                nominal_voltage_v=voltage,
                voltage_min_v=low,
                voltage_max_v=high,
                module_count=count,
                module_model="SS6160",
                rack_model=rack,
                total_site_weight_kg=weight,
                dimensions_wdh_mm=dims,
                communication_interfaces=["CANBUS", "RS485", "Ethernet"],
            )
        )
    return result
