"""Stage concrete facts from reviewed LEOCH OPzS sheets, never import identities."""

from __future__ import annotations

import hashlib
import re


def parse_opzs(text: str, model: str) -> dict:
    """Retain 20°C/C10 basis and distinguish dry mass, wet mass and C-rate.

    Residual PDF template tokens are not values. Changed units, headings or
    conditions fail closed. Edition conflicts require separate human review.
    """
    if not re.fullmatch(r"\d+OPzS\d+", model):
        raise ValueError("Unreviewed model scope")
    if not re.search(r"^" + re.escape(model) + r"(?:\s*\([^\n]*\))?\s*$", text, re.M):
        raise ValueError("Missing exact printed model heading")
    revision = re.findall(r"Publication No\.:LB-(\S+)", text)
    if len(revision) != 1 or not revision[0].startswith(model + "-PD-EN-"):
        raise ValueError("Missing or different exact-model revision")
    required = [
        "OPzS SERIES-FLOODED BATTERY",
        "C10,1.80V/cell",
        "-15~55℃",
        "0~45℃",
        "-15~45℃",
        "2.23-2.25V/cell",
        "2.40-2.45V/cell",
        "≤4% per month at 20°C",
        "20 years design life (20℃)",
    ]
    if any(v not in text for v in required):
        raise ValueError("Unreviewed technology, temperature or charging basis")

    def one(pattern: str) -> float:
        values = re.findall(pattern, text)
        if len(values) != 1 or float(values[0]) <= 0:
            raise ValueError("Missing, duplicate or nonpositive concrete value")
        return float(values[0])

    voltage = one(r"Rated Voltage\s+(?:P-RV\s+)?([\d.]+)V\b")
    if voltage != 2:
        raise ValueError("Only reviewed 2 V sheets supported")
    return {
        "model": model,
        "document_revision": revision[0],
        "voltage_v": voltage,
        "capacity_ah": one(r"Nominal Capacity \(20℃\)\s+C10,1.80V/cell\s+(?:P-1080\s+)?([\d.]+)Ah"),
        "capacity_basis": "C10 to 1.80 V/cell at 20°C",
        "short_circuit_a": one(r"Short-circuit current\s+(?:P-SC\s+)?([\d.]+)A\b"),
        "maximum_charging_c_rate": one(r"Max.Charging Current \(20℃\)\s+([\d.]+)C\b"),
        "approximate_mass_kg": one(r"Approx Weight\s+(?:P-GWEIGHT\s+)?([\d.]+)kg\b"),
        "dry_mass_kg": one(r"Dry Weight\s+(?:P-DWEIGHT\s+)?([\d.]+)kg\b"),
        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
    }
