"""Stage two reviewed ATESS battery configuration tables; never import or repair ratings."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

SOURCE_URLS = {
    "BC55NPB": "https://static.atesspower.com/upload/files/20251217/7c0c17764eba3bd9b8e84ece4feb9539.pdf",
    "VoltStack Battery": "https://static.atesspower.com/upload/files/20251217/e6d723421e67acbbe9034d7b9513d950.pdf",
}
NUM = r"\d+(?:\.\d+)?"


def parse_battery_table(content: bytes, *, model: str, source_url: str) -> list[dict[str, Any]]:
    """Read explicit rack columns from local pdftotext -layout output.

    Module specifications, accessories and cover claims are deliberately excluded.
    Changed scope/units and duplicate rows fail closed. The known nine-module
    VoltStack inconsistency is flagged without replacing the source observations.
    No active power, current in amperes, duration or usable energy is inferred.
    """
    if model not in SOURCE_URLS or source_url != SOURCE_URLS[model]:
        raise ValueError("Expected reviewed model and official source URL")
    text = unicodedata.normalize("NFKC", content.decode("utf-8-sig"))
    if model not in text or text.count("Battery rack specification") != 1:
        raise ValueError("Expected one model-specific battery rack table")
    text = text.split("Battery rack specification", 1)[1]
    text = re.split(r"\n\s*(?:BMS parameters on LCD|Certificate)\b", text, maxsplit=1)[0]
    lines = [" ".join(line.split()) for line in text.splitlines()]
    count = 6 if model == "BC55NPB" else 7

    def row(label: str) -> str:
        found = [line[len(label) :].strip() for line in lines if line.startswith(label)]
        if len(found) != 1:
            raise ValueError(f"Missing or duplicate row: {label}")
        return found[0]

    header = row("Configuration")
    counts = [int(x) for x in re.findall(r"(\d+) (?:battery )?modules", header)]
    if counts != list(range(6, 6 + count)):
        raise ValueError("Unexpected configuration identity/order")
    # The +1 BPU row wraps differently in the two editions. Do not infer extra combinations.
    bpu_lines = [line for line in lines if "+1 BPU" in line]
    if sum(line.count("+1 BPU") for line in bpu_lines) != count:
        raise ValueError("Unexpected BPU configuration scope")

    def values(label: str, pattern: str) -> list[tuple[float, ...]]:
        value = row(label)
        tokens = value.split()
        if len(tokens) != count or any(not re.fullmatch(pattern, t) for t in tokens):
            raise ValueError(f"Unexpected units or column scope: {label}")
        result = [tuple(float(v) for v in re.findall(NUM, token)) for token in tokens]
        if any(v <= 0 for item in result for v in item):
            raise ValueError(f"Nonpositive rating: {label}")
        return result

    energy = values("Rated energy", rf"{NUM}kWh")
    voltage = values("Rated voltage", rf"{NUM}V")
    limits = values("Voltage range", rf"{NUM}V-{NUM}V")
    weight = values("Weight", rf"{NUM}kg")
    # Both reviewed rows carry mm in the label; BC55NPB also repeats mm per cell.
    dimension_label = "Dimension (W/H/D) mm" if model == "BC55NPB" else "Dimension (W/H/D)mm"
    dimensions = values(dimension_label, rf"{NUM}/{NUM}/{NUM}(?:mm)?")
    rated_c = values("Rated charge/discharge", rf"{NUM}C")
    max_c = values("Max. charge/discharge", rf"{NUM}C")
    altitude = values("Max. altitude", rf"{NUM}m")
    ip = row("Protection degree").split()
    if len(ip) != count or any(not re.fullmatch(r"IP\d{2}", x) for x in ip):
        raise ValueError("Unexpected enclosure scope")
    if row("BMS").split() != ["Included"] * count:
        raise ValueError("Unexpected BMS scope")
    if (
        row("Communication").split() != ["CAN"] * count
        or row("Monitoring").split() != ["RS485"] * count
    ):
        raise ValueError("Unexpected interface scope")
    rows = []
    for i, modules in enumerate(counts):
        low, high = limits[i]
        if not low < voltage[i][0] < high or rated_c[i][0] > max_c[i][0]:
            raise ValueError("Invalid voltage or C-rate envelope")
        rows.append(
            {
                "model": model,
                "module_count": modules,
                "bpu_count": 1,
                "reported_energy_kwh": energy[i][0],
                "reported_voltage_v": voltage[i][0],
                "voltage_min_v": low,
                "voltage_max_v": high,
                "weight_kg": weight[i][0],
                "width_mm": dimensions[i][0],
                "height_mm": dimensions[i][1],
                "depth_mm": dimensions[i][2],
                "rated_charge_discharge_c": rated_c[i][0],
                "maximum_charge_discharge_c": max_c[i][0],
                "altitude_max_m": altitude[i][0],
                "ingress_protection": ip[i],
                "active_power_kw": None,
                "rating_review_required": model == "VoltStack Battery" and modules == 9,
                "source_url": source_url,
                "locator": (
                    f"PDF page 2, Battery rack specification, {modules} modules +1 BPU column"
                ),
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return rows
