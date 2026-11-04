"""Offline staging of the reviewed SC48/SC51/SC76 UPS battery partitions."""

import re

from energy_data_retrieval.bess_catalogue.pib import _Tables

MODELS = [f"SC{v}-{a}" for v in [48, 51, 76] for a in [20, 27, 50, 80, 100, 150, 200]]
HEADER = [
    "MODEL",
    "Battery type",
    "Nominal voltage",
    "Capacity (Ah)",
    "Power",
    "Charging Votage",
    "charging (A)",
    "Max discharging power",
    "Dimision(MM)",
    "Weight about",
]
FIELDS = [
    "model",
    "battery_type_label",
    "voltage_v",
    "pack_ah",
    "power_w",
    "charging_voltage_native",
    "usual_charge_a",
    "max_charge_a",
    "discharge_power_native",
    "length_mm",
    "width_mm",
    "height_mm",
    "approx_mass_kg",
]


def parse_sc_partitions(content: bytes) -> list[dict[str, str]]:
    """Retain native observations; conflicting type labels are not reconciled here."""
    p = _Tables()
    p.feed(content.decode("utf-8-sig"))
    p.close()
    if p.stack or len(p.tables) != 1 or p.tables[0][0] != HEADER:
        raise ValueError("Unexpected UPS table/header")
    table = p.tables[0]
    if table[1] != ["(V)", "W", "(V)", "usually", "Max", "L", "W", "H", "(kg)"]:
        raise ValueError("Changed units")
    rows = [r for r in table[2:] if r and re.match(r"SC(?:48|51|76)-", r[0])]
    if [r[0] for r in rows] != MODELS:
        raise ValueError("Missing, duplicate or changed selected model")
    for r in rows:
        if len(r) != 13 or not all(r):
            raise ValueError("Incomplete row")
        if any(not re.fullmatch(r"\d+(?:\.\d+)?", r[i]) for i in [2, 3, 4, 6, 7, 9, 10, 11, 12]):
            raise ValueError("Changed numeric units")
        if not re.fullmatch(r"\d+(?:\.\d+)?~\d+(?:\.\d+)?\(\d+(?:\.\d+)?\)", r[5]):
            raise ValueError("Changed charge-voltage notation")
        if not re.fullmatch(r"\d+W\(\d+W/60[Ss]\)", r[8]):
            raise ValueError("Changed discharge duration or units")
    return [dict(zip(FIELDS, r, strict=True)) for r in rows]
