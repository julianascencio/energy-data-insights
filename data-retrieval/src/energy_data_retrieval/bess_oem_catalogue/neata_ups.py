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


HIGH_MODELS = [f"SC102-{a}" for a in [20, 27, 50, 80, 100, 150, 200]] + [
    f"SC{v}-{a}" for v in [192, 204, 240] for a in [20, 27]
]


def parse_high_sc(content: bytes) -> list[dict[str, str]]:
    """Stage all remaining SC rows; retain type/voltage conflicts verbatim."""
    parse_sc_partitions(content)  # Validate the shared header, units and prior partition.
    p = _Tables()
    p.feed(content.decode("utf-8-sig"))
    rows = [r for r in p.tables[0][2:] if r and r[0].startswith("SC") and r[0] not in MODELS]
    if [r[0] for r in rows] != HIGH_MODELS:
        raise ValueError("Missing, duplicate or changed high SC model")
    for r in rows:
        if len(r) != 13 or not all(r):
            raise ValueError("Incomplete high SC row")
        if any(not re.fullmatch(r"\d+(?:\.\d+)?", r[i]) for i in [2, 3, 6, 7, 9, 10, 11, 12]):
            raise ValueError("Changed high SC numeric units")
        if not re.fullmatch(r"\d+(?:\.\d+)?(?:KW)?", r[4]):
            raise ValueError("Changed high SC power units")
        if not re.fullmatch(r"\d+(?:\.\d+)?~\d+(?:\.\d+)?\(\d+(?:\.\d+)?\)", r[5]):
            raise ValueError("Changed high SC charge voltage")
        if not re.fullmatch(r"(?:\d+W\(\d+W/60[Ss]\)|\d+(?:\.\d+)?KW)", r[8]):
            raise ValueError("Changed high SC discharge units or timing")
    return [dict(zip(FIELDS, r, strict=True)) for r in rows]


CABINET_MODELS = [
    "TC40",
    "NC16",
    "TC40E",
    "NC28",
    "TC50Y",
    "NC20Y",
    "NC35Y",
    "NC50Y",
    "TC50",
    "TC50E",
    "NC35",
    "NC50",
]


def parse_low_voltage_cabinets(content: bytes) -> list[dict[str, str]]:
    """Stage unique reviewed 204.8/240/256V cabinets; no repeated-code inference."""
    parse_high_sc(content)
    p = _Tables()
    p.feed(content.decode("utf-8-sig"))
    rows = [r for r in p.tables[0][2:] if r and r[0] in CABINET_MODELS]
    if [r[0] for r in rows] != CABINET_MODELS:
        raise ValueError("Missing or repeated cabinet identity")
    for r in rows:
        if len(r) != 13 or not all(r):
            raise ValueError("Incomplete cabinet row")
        if r[2] not in ["204.8", "240", "256"]:
            raise ValueError("Unexpected cabinet voltage partition")
        if any(not re.fullmatch(r"\d+(?:\.\d+)?", r[i]) for i in [2, 3, 6, 7, 9, 10, 11, 12]):
            raise ValueError("Changed cabinet numeric units")
        if not re.fullmatch(r"max\.\s*\d+(?:\.\d+)?KW", r[4]):
            raise ValueError("Changed cabinet maximum power units")
        if not re.fullmatch(r"\d+(?:\.\d+)?KW/\d+min", r[8]) and not (
            r[0] == "NC35" and r[8] == "37.85KW/60mi"
        ):
            raise ValueError("Changed cabinet timed discharge notation")
        if not re.fullmatch(r"\d+(?:\.\d+)?~\d+(?:\.\d+)?\(\d+(?:\.\d+)?\)", r[5]):
            raise ValueError("Changed cabinet charging voltage")
    return [dict(zip(FIELDS, r, strict=True)) for r in rows]
