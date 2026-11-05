"""Stage selected Fullriver DC cards without inferring ratings or model variants."""

import re
from html.parser import HTMLParser
from typing import TypedDict


class Card(TypedDict):
    """One exact model with separate native unit panels."""

    model: str
    panels: dict[str, dict[str, str]]


class _Cards(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str], list[str]]] = []
        self.rows: list[dict[str, str]] = []
        self.row: dict[str, str] = {}
        self.label = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = set((dict(attrs).get("class") or "").split())
        if "card-batt" in classes:
            if self.stack:
                raise ValueError("Nested battery cards")
            self.row = {}
        if (self.stack or "card-batt" in classes) and tag not in {
            "img",
            "br",
            "hr",
            "input",
            "source",
            "link",
            "meta",
            "wbr",
        }:
            self.stack.append((tag, classes, []))

    def handle_data(self, data: str) -> None:
        for _, _, parts in self.stack:
            parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        actual, classes, parts = self.stack.pop()
        if actual != tag:
            raise ValueError("Unbalanced card markup")
        value = " ".join("".join(parts).split())
        if "card-batt__model" in classes:
            if "model" in self.row:
                raise ValueError("Duplicate model heading")
            self.row["model"] = value
        if "card-batt__specs--label" in classes:
            self.label = value
        if "card-batt__specs--value" in classes:
            if not self.label or self.label in self.row or not value:
                raise ValueError("Missing or duplicate card field")
            self.row[self.label] = value
            self.label = ""
        if "card-batt" in classes:
            self.rows.append(self.row)


def parse_cards(content: bytes, *, expected_models: list[str]) -> list[Card]:
    """Return metric/imperial observations for explicitly reviewed exact models.

    Requires two complete unit panels per selected model. Other models are ignored,
    never fuzzy-matched. Capacity has no inferred discharge rate. Reserve minutes,
    current and dimensions remain strings with original units for manual review.
    """
    if not expected_models or len(set(expected_models)) != len(expected_models):
        raise ValueError("Expected unique reviewed models")
    parser = _Cards()
    parser.feed(content.decode("utf-8-sig"))
    if parser.stack:
        raise ValueError("Incomplete card markup")
    result: list[Card] = []
    for model in expected_models:
        rows = [r for r in parser.rows if r.get("model") == model]
        if len(rows) != 2:
            raise ValueError(f"Expected two unit panels: {model}")
        panels: dict[str, dict[str, str]] = {}
        for row in rows:
            if not {"model", "Group", "Capacity", "Dimms", "Weight"} <= row.keys():
                raise ValueError("Incomplete card fields")
            unit = "metric" if row["Dimms"].endswith(" mm") else "imperial"
            patterns = {
                "Capacity": r"\d+(?:\.\d+)? Ah",
                "Dimms": r"\d+(?:\.\d+)? x \d+(?:\.\d+)? x \d+(?:\.\d+)? "
                + ("mm" if unit == "metric" else "in"),
                "Weight": r"\d+(?:\.\d+)? " + ("kg" if unit == "metric" else "lbs"),
            }
            for key, value in row.items():
                if key in {"model", "Group"}:
                    continue
                pattern = patterns.get(key)
                if pattern is None and re.fullmatch(r"Reserve Capacity @ \d+A", key):
                    pattern = r"\d+(?:\.\d+)? min"
                if pattern is None or not re.fullmatch(pattern, value):
                    raise ValueError(f"Unreviewed label/unit: {key}")
            if unit in panels:
                raise ValueError("Duplicate unit panel")
            panels[unit] = row
        result.append({"model": model, "panels": panels})
    return result


def parse_datasheet(text: str, *, model: str) -> dict[str, object]:
    """Stage rate-specific battery-unit capacity from reviewed PDF layout text.

    Requires an exact first heading and the explicit test-condition footnote.
    Does not interpret charts, infer cell counts, or select a preferred revision.
    """
    if text.strip().splitlines()[0].strip() != model:
        raise ValueError("Exact model heading mismatch")
    if not all(token in text for token in ("100% SoC", "25°C", "1.75VPC")):
        raise ValueError("Unreviewed capacity test conditions")
    values = {}
    for rate in (100, 20, 10, 5):
        matches = re.findall(rf"^\s*C{rate}\s+(\d+(?:\.\d+)?)\s*AH\b", text, re.M)
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous C{rate} capacity")
        values[str(rate)] = float(matches[0])
    resistance = re.findall(r"Internal Resistance\s+(\d+(?:\.\d+)?)\s*m\s*[ΩΩ]", text)
    if len(resistance) != 1:
        raise ValueError("Missing or ambiguous milliohm resistance")
    return {
        "capacity_ah_by_discharge_hours": values,
        "capacity_boundary": "Complete battery unit, not cell capacity or stored energy",
        "reference_soc_pct": 100,
        "reference_temperature_c": 25,
        "end_voltage_v_per_cell": 1.75,
        "internal_resistance_milliohm": float(resistance[0]),
        "qualification": "OEM estimation ratings; application-dependent, design subject to change",
    }


def parse_charging_conditions(text: str, *, model: str) -> dict[str, object]:
    """Stage exact-sheet temperature categories and bank-voltage charging rows.

    Preserve recommended versus maximum ranges and both native temperature units.
    Bank voltage columns are not separate models or battery operating limits.
    No temperature conversion, current inference or curve digitization is performed.
    """
    if text.strip().splitlines()[0].strip() != model:
        raise ValueError("Exact model heading mismatch")
    if text.count("TEMPERATURE RANGE SPECIFICATIONS") != 1:
        raise ValueError("Expected one temperature table")
    part = text.split("TEMPERATURE RANGE SPECIFICATIONS")[1].split("TERMINAL TORQUE")[0]
    compact = " ".join(part.split())
    if "Condition Recommended Maximum Recommended Maximum" not in compact:
        raise ValueError("Unreviewed temperature columns")
    if "TC= Temperature Compensation" not in compact:
        raise ValueError("Missing temperature compensation definition")
    temperatures = {}
    for label in ("Storage", "Operation", "Charge with TC", "Charge w/o TC"):
        found = re.findall(rf"^\s*{re.escape(label)}\s+(.+)$", part, re.M)
        if len(found) != 1:
            raise ValueError(f"Missing or ambiguous condition: {label}")
        ranges = re.findall(r"(-?\d+)°([FC]) to (-?\d+)°([FC])", found[0])
        if len(ranges) != 4 or [a[1] + a[3] for a in ranges] != ["FF", "FF", "CC", "CC"]:
            raise ValueError("Unreviewed temperature units/order")
        temperatures[label] = {
            key: {"min": int(a), "max": int(b), "unit": unit}
            for key, (a, unit, b, _) in zip(
                ("recommended_f", "maximum_f", "recommended_c", "maximum_c"),
                ranges,
                strict=True,
            )
        }
        if any(int(a) > int(b) for a, _, b, _ in ranges):
            raise ValueError("Reversed temperature range")
    headers = re.findall(r"Charge Stage\s+([\dV\s]+)$", part, re.M)
    if len(headers) != 1:
        raise ValueError("Missing bank voltage columns")
    banks = re.findall(r"(\d+)V", headers[0])
    if len(banks) != 4 or len(set(banks)) != 4:
        raise ValueError("Expected four distinct bank voltages")
    charges = {}
    for stage in ("Bulk", "Absorption", "Float"):
        values = re.findall(rf"\b{stage}\s+((?:\d+(?:\.\d+)?V\s*){{4}})$", part, re.M)
        if len(values) != 1:
            raise ValueError(f"Missing or ambiguous charge stage: {stage}")
        charges[stage.lower()] = dict(
            zip(banks, map(float, re.findall(r"(\d+(?:\.\d+)?)V", values[0])), strict=True)
        )
    compensation = re.findall(r"TC Factor:\s*\((-?\d+)mV/°F/cell\) or \((-?\d+)mV/°C/cell\)", part)
    if len(compensation) != 1:
        raise ValueError("Unreviewed compensation units")
    return {
        "temperature_ranges": temperatures,
        "tc_definition": "Temperature Compensation",
        "charge_voltages_v_by_bank_voltage_v": charges,
        "temperature_compensation_mv_per_cell_per_degree": {
            "F": int(compensation[0][0]),
            "C": int(compensation[0][1]),
        },
        "boundary": "Printed battery-bank charging table; not model operating voltage limits",
        "qualification": (
            "Native rounded units retained; no inferred reference temperature or charge current"
        ),
    }


def parse_small_battery_sheet(text: str, *, model: str) -> dict[str, object]:
    """Stage reviewed small DC AGM units with rate capacities and dimensions.

    Exact mechanical labels and native units are required. Case and terminal
    heights stay separate; a terminal is not an alternative model configuration.
    """
    row = parse_datasheet(text, model=model)
    original = row["capacity_ah_by_discharge_hours"]
    assert isinstance(original, dict)
    capacities = dict(original)
    for rate in (3, 2, 1):
        matches = re.findall(rf"^\s*C{rate}\s+(\d+(?:\.\d+)?)\s*AH\b", text, re.M)
        if len(matches) > 1:
            raise ValueError(f"Ambiguous C{rate} capacity")
        if matches:
            capacities[str(rate)] = float(matches[0])
    row["capacity_ah_by_discharge_hours"] = capacities
    if "DEEP CYCLE AGM" not in text:
        raise ValueError("Missing explicit AGM classification")
    mechanical = {}
    for label, key, unit in (
        ("Nominal Voltage", "nominal_voltage_v", "Volt"),
        ("Height (w/ terminal)", "terminal_height_mm", "mm"),
        ("Height (case only)", "case_height_mm", "mm"),
        ("Width", "width_mm", "mm"),
        ("Length", "length_mm", "mm"),
        ("Weight", "weight_kg", "kg"),
    ):
        matches = re.findall(
            re.escape(label) + r"\s+[^\n]*?\b(\d+(?:\.\d+)?)\s*" + unit + r"\b", text
        )
        if len(matches) != 1:
            raise ValueError(f"Missing or ambiguous mechanical field: {label}")
        mechanical[key] = float(matches[0])
    if mechanical["case_height_mm"] > mechanical["terminal_height_mm"]:
        raise ValueError("Case exceeds terminal height")
    row["mechanical"] = mechanical
    return row
