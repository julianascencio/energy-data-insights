"""Offline staging for the ODRÉ national installation register, Etalab v2.

The dataset includes aggregates, other storage technologies and hybrid-plant
ratings. Only individual explicitly battery-only installations are staged here.
Identity reconciliation against projects and other EICs remains a human step.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date, datetime
from typing import Any


def _number(row: dict[str, Any], key: str) -> float | None:
    value = row.get(key)
    if value is None:
        return None
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ValueError(f"Invalid nonnegative numeric {key}")
    return float(value)


def _mw(row: dict[str, Any], key: str) -> float | None:
    value = _number(row, key)
    return None if value is None else value / 1000


def stage_odre_batteries(content: bytes, *, snapshot_date: str) -> list[dict[str, Any]]:
    """Stage API ``results`` with explicit units, exclusions and review flags.

    ``snapshot_date`` is the register's reporting date, never download time.
    Anomalously small energy-to-power ratios flag a field for review; the value
    is not repaired. Commissioning is retained as an industrial-service date,
    not silently relabelled commercial operation. Annual energy is never used.
    """
    as_of = date.fromisoformat(snapshot_date)
    payload = json.loads(content)
    rows = payload.get("results")
    if not isinstance(rows, list):
        raise ValueError("Expected ODRÉ API results array")
    seen: set[str] = set()
    staged = []
    for number, row in enumerate(rows, 1):
        eic = row.get("codeeicresourceobject")
        if not isinstance(eic, str) or not re.fullmatch(r"[A-Z0-9-]{16}", eic):
            raise ValueError("Missing or invalid EIC installation identity")
        if eic in seen:
            raise ValueError("Duplicate EIC in incoming partition")
        seen.add(eic)
        flags = []
        if not (
            row.get("filiere") == "Stockage non hydraulique"
            and row.get("technologie") == "Batterie"
            and row.get("typestockage") == "BATTE"
        ):
            flags.append("not_explicit_battery_only")
        if row.get("nbinstallations") != 1:
            flags.append("aggregate_or_unknown_installation_count")
        if not row.get("nominstallation") or row["nominstallation"].casefold() == "confidentiel":
            flags.append("withheld_or_missing_name")
        if row.get("regime") not in {"En service", "En retrait provisoire"}:
            flags.append("unmapped_operating_regime")
        dates = {}
        for key in (
            "dateraccordement",
            "datederaccordement",
            "datemiseenservice",
            "datedebutversion",
        ):
            value = row.get(key)
            if value:
                parsed = datetime.strptime(value, "%d/%m/%Y").date()
                dates[key] = parsed.isoformat()
                if parsed > as_of:
                    flags.append(f"{key}_after_snapshot")
        power = _number(row, "puismaxinstallee")
        energy = _number(row, "energiestockable")
        energy_review = bool(power and energy is not None and energy / power < 0.01)
        staged.append(
            {
                "eic": eic,
                "name": row.get("nominstallation"),
                "source_row": number,
                "source_sha256": hashlib.sha256(content).hexdigest(),
                "snapshot_date": snapshot_date,
                "dates": dates,
                "power_mw": None if power is None else power / 1000,
                "energy_mwh": None if energy is None or energy_review else energy / 1000,
                "energy_kwh_reported": energy,
                "energy_requires_review": energy_review,
                "charging_power_mw": _mw(row, "puismaxcharge"),
                "connection_power_mw": _mw(row, "puismaxrac"),
                "connection_charging_power_mw": _mw(row, "puismaxraccharge"),
                "review_flags": flags,
                "review_required": True,
            }
        )
    return staged
