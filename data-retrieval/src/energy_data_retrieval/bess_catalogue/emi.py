"""Stage Electricity Authority dispatched-fleet battery observations offline."""

import csv
import io
import math


def parse_emi_batteries(content: bytes) -> list[dict[str, str]]:
    """Keep dated BAT observations, without treating effective dates as COD.

    Repeated units with different effective periods remain separate candidates;
    conflicting or duplicate observation identities require manual review.
    """
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    required = {
        "PlantName",
        "TechnologyCode",
        "PointOfConnectionCode",
        "UnitCode",
        "NameplateMegawatts",
        "EffectiveStartDate",
        "EffectiveEndDate",
    }
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("EMI header changed")
    output = []
    seen = set()
    for row in reader:
        if row["TechnologyCode"] != "BAT":
            continue
        key = tuple(row[k] for k in ("PointOfConnectionCode", "UnitCode", "EffectiveStartDate"))
        if key in seen:
            raise ValueError("Duplicate EMI observation; review revisions")
        seen.add(key)
        value = float(row["NameplateMegawatts"])
        if not math.isfinite(value) or value < 0:
            raise ValueError("Invalid EMI battery power")
        output.append(row)
    return output
