"""Offline staging of Force-H1-V2 single-string tables, printed 22P1FH1018.

Accepts the two raw pdfplumber tables from PDF pages 11-12. The caller must
check document identity, source rights and the printed revision before use.
Parallel arrangements and component tables are deliberately outside this parser.
"""

import re


def parse_h1_v2(tables: list[list[list[str | None]]], *, revision: str) -> list[dict]:
    """Reject changed identities, units, column counts and invalid voltage bounds."""
    if revision != "22P1FH1018 / 5PMPA08-00135" or len(tables) != 2:
        raise ValueError("Unreviewed revision or page count")
    rows = {}
    for table in tables:
        headers = 0
        for raw in table:
            cells = [re.sub(r"\s+", " ", cell).strip() for cell in raw if cell and cell.strip()]
            if not cells:
                continue
            label, *values = cells
            if label == "Product Type":
                if values != ["Force-H1-V2"]:
                    raise ValueError("Changed model")
                headers += 1
                continue
            if label in rows:
                raise ValueError("Duplicate row: " + label)
            rows[label] = values
        if headers != 1:
            raise ValueError("Missing or duplicate model header")

    def numbers(label: str, count: int = 6) -> list[float]:
        values = rows.get(label, [])
        if len(values) != count or any(not re.fullmatch(r"\d+(?:\.\d+)?", v) for v in values):
            raise ValueError("Changed numeric row/units: " + label)
        return [float(v) for v in values]

    for label, expected in {
        "Battery Module Name": ["FH48074"],
        "Battery Controller Name": ["FC0500-40S-V2"],
        "Cell Technology": ["Li-iron (LFP)"],
        "Battery System Capacity (AH)": ["74Ah"],
    }.items():
        if rows.get(label) != expected:
            raise ValueError("Changed component or chemistry: " + label)
    counts = numbers("Battery Module Quantity(pcs)")
    if counts != list(range(2, 8)):
        raise ValueError("Changed or duplicate configuration order")
    columns = {
        "energy_kwh_reported": numbers("Battery System Capacity(kWh)"),
        "nominal_voltage_v": numbers("Battery System Voltage (Vdc)"),
        "charge_upper_voltage_v": numbers("Battery System Charge Upper Voltage (Vdc)"),
        "discharge_lower_voltage_v": numbers("Battery System Discharge Lower Voltage (Vdc)"),
        "weight_kg": numbers("Weight (kg)"),
    }
    common = {}
    for direction in ["Charge", "Discharge"]:
        for native, key in [
            ("Standard", "standard_a"),
            ("Normal", "normal_a"),
            ("Max.@15s", "peak_a"),
        ]:
            common[direction.lower() + "_" + key] = numbers(
                f"Battery System {direction} Current (Amps, {native})", 1
            )[0]
    dimensions = rows.get("Dimension(W*D*H, mm)", [])
    if len(dimensions) != 6:
        raise ValueError("Changed dimension columns")
    result = []
    for i, count in enumerate(counts):
        row = {k: v[i] for k, v in columns.items()}
        if (
            not 0
            < row["discharge_lower_voltage_v"]
            < row["nominal_voltage_v"]
            < row["charge_upper_voltage_v"]
        ):
            raise ValueError("Invalid voltage bounds")
        dims = re.sub(r"\s+", "", dimensions[i]).split("*")
        if len(dims) != 3 or any(not re.fullmatch(r"\d+", v) or int(v) <= 0 for v in dims):
            raise ValueError("Invalid dimensions")
        if min(row["energy_kwh_reported"], row["weight_kg"], *common.values()) <= 0:
            raise ValueError("Invalid ratings")
        result.append(
            {
                **row,
                **common,
                "module_count": int(count),
                "module_model": "FH48074",
                "controller_model": "FC0500-40S-V2",
                "capacity_ah": 74,
                "dimensions_wdh_mm": [int(v) for v in dims],
                "charge_peak_seconds": 15,
                "discharge_peak_seconds": 15,
            }
        )
    return result
