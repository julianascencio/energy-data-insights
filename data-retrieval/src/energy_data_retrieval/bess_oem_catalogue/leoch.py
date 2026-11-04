"""Offline staging of reviewed LEOCH two-page 2 V OPzV sheets; no import or networking."""

from __future__ import annotations

import hashlib
import re


def parse_opzv(text: str, model: str) -> dict:
    """Preserve C10 capacity, short-circuit rating and conditional OEM claims.

    Template placeholders may remain in the PDF. Only concrete printed values
    adjacent to reviewed labels are accepted. C-rate is never converted to A.
    """
    if not re.fullmatch(r"\d+OPzV\d+", model):
        raise ValueError("Unreviewed model scope")
    if not re.search(r"^" + re.escape(model) + r"(?:\s*\([^\n]*\))?\s*$", text, re.M):
        raise ValueError("Missing exact printed model heading")
    revision = re.findall(r"Publication No\.:LB-(\S+)", text)
    if len(revision) != 1 or not revision[0].startswith(model + "-PD-EN-"):
        raise ValueError("Missing or different exact-model publication")
    if "OPzV SERIES-TUBULAR GEL" not in text or "C10,1.80V/cell" not in text:
        raise ValueError("Unreviewed technology or capacity basis")

    def one(pattern: str) -> float:
        values = re.findall(pattern, text)
        if len(values) != 1 or float(values[0]) <= 0:
            raise ValueError("Missing, duplicate or nonpositive labelled value")
        return float(values[0])

    voltage = one(r"Rated Voltage\s+(?:P-RV\s+)?([\d.]+)V\b")
    if voltage != 2:
        raise ValueError("Only reviewed 2 V sheets supported")
    ah = one(r"Nominal Capacity \(25℃\)\s+C10,1.80V/cell\s+(?:P-1080\s+)?([\d.]+)Ah")
    short = one(r"Short-circuit current\s+(?:P-SC\s+)?([\d.]+)A\b")
    charge = one(r"Max.Charging Current \(25℃\)\s+([\d.]+)C\b")
    mass = one(r"([\d.]+)kg\s*\(")
    conditions = [
        "-20~55℃",
        "0~40℃",
        "-20~50℃",
        "2.23-2.27V/cell",
        "2.40-2.45V/cell",
        "20 year design life (20℃)",
        "≤3% per month at 25°C",
    ]
    if any(value not in text for value in conditions):
        raise ValueError("Changed temperature, charging or life conditions; review required")
    return {
        "model": model,
        "document_revision": revision[0],
        "voltage_v": voltage,
        "capacity_ah": ah,
        "capacity_basis": "C10 to 1.80 V/cell at 25°C",
        "short_circuit_a": short,
        "maximum_charging_c_rate": charge,
        "approximate_mass_kg": mass,
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
