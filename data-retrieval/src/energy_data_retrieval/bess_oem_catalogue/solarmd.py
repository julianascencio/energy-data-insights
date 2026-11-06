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


LEGACY_MODELS = tuple(
    "SS" + c
    for c in ("7011", "7013", "7014", "7016", "7017", "7019", "7020", "7021", "7023", "7024")
)


def parse_legacy_ss7000(table: list[list[str]], *, revision: str) -> list[dict]:
    """Stage the unsuffixed H17/SS6143 table, without inferring power or warranty."""
    headings = [
        "Battery Name",
        "Module Quantity",
        "Voltage Range (V)",
        "Nominal Voltage (V)",
        "Nominal Capacity (kWh)",
        "Current Rating (A)",
    ]
    if revision != "1.0 / 2024-04-26" or len(table) != 11:
        raise ValueError("Unreviewed revision or row count")
    if any(len(row) != 6 or any(not isinstance(c, str) for c in row) for row in table):
        raise ValueError("Missing or shifted cells")
    table = [[" ".join(c.split()) for c in row] for row in table]
    if table[0] != headings or tuple(r[0] for r in table[1:]) != LEGACY_MODELS:
        raise ValueError("Changed headings or exact identities")
    result = []
    for i, row in enumerate(table[1:], 8):
        model, quantity, envelope, nominal, capacity, current = row
        match = re.fullmatch(NUMBER + r"V - " + NUMBER, envelope)
        if not match or not quantity.isdigit():
            raise ValueError("Changed voltage units or module count")
        if any(not re.fullmatch(NUMBER, v) for v in [nominal, capacity, current]):
            raise ValueError("Invalid number or unit")
        low, high = map(float, match.groups())
        voltage, energy, amps = map(float, [nominal, capacity, current])
        if int(quantity) != i or not 0 < low < voltage < high or min(energy, amps) <= 0:
            raise ValueError("Invalid bounds or configuration")
        result.append(
            dict(
                model=model,
                module_count=i,
                module_model="SS6143",
                voltage_min_v=low,
                voltage_max_v=high,
                nominal_voltage_v=voltage,
                energy_kwh=energy,
                current_rating_a=amps,
            )
        )
    return result
