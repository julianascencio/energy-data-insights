"""Parse dated New Zealand dispatch observations without inferring plant totals."""

import csv
import io
import math
from datetime import datetime
from typing import Any

FIELDS = (
    "PlantName",
    "PointOfConnectionCode",
    "UnitCode",
    "TechnologyCode",
    "Technology",
    "FuelCode",
    "Fuel",
    "PeakingPlantFlag",
    "PlantOperatorCode",
    "PlantOperator",
    "DateCommissioned",
    "DateDecommissioned",
    "NameplateMegawatts",
    "EffectiveStartDate",
    "EffectiveEndDate",
)


def parse_inventory(data: bytes) -> list[dict[str, Any]]:
    """Retain original row locators and intervals, including sentinel dates.

    Multiple connections and effective periods are observations, not independent
    plants or generating units. Never sum their ratings or infer present status.
    """
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if tuple(reader.fieldnames or ()) != FIELDS:
        raise ValueError("Unexpected NZ fleet columns")
    result = []
    seen = set()
    for index, row in enumerate(reader, 2):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("Malformed NZ row")
        if row["TechnologyCode"] != "HYD":
            continue
        if row["FuelCode"] != "HYD":
            raise ValueError("Inconsistent hydro fuel")
        if any(not row[k].strip() for k in FIELDS[:3]):
            raise ValueError("Missing dispatch identity")
        key = tuple(row[k] for k in (*FIELDS[:3], "EffectiveStartDate", "EffectiveEndDate"))
        if key in seen:
            raise ValueError("Duplicate dispatch interval")
        seen.add(key)
        start = datetime.fromisoformat(row["EffectiveStartDate"])
        end = datetime.fromisoformat(row["EffectiveEndDate"])
        if start.tzinfo is None or end.tzinfo is None or start >= end:
            raise ValueError("Invalid dispatch interval")
        mw = float(row["NameplateMegawatts"])
        if not math.isfinite(mw) or mw < 0:
            raise ValueError("Invalid generating MW")
        result.append({"row": index, "raw": row})
    return result
