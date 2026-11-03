"""Review-only staging for the Swiss SFOE production plant register."""

from __future__ import annotations

import csv
import hashlib
import io
import zipfile
from collections import Counter, defaultdict
from collections.abc import Iterator
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


def _kw(value: str) -> Decimal:
    try:
        power = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid native kW value") from exc
    if not power.is_finite() or power < 0:
        raise ValueError("Invalid native kW value")
    return power


def stage_swiss_pv(
    payload: bytes, *, sha256: str, minimum_kw: Decimal = Decimal(1000)
) -> list[dict[str, Any]]:
    """Stage explicitly coded PV parents and exact child relationships, without site details."""
    if hashlib.sha256(payload).hexdigest() != sha256:
        raise ValueError("Swiss archive checksum mismatch")
    threshold = _kw(str(minimum_kw))
    candidates = {}
    all_ids: set[str] = set()
    buildings: Counter[str] = Counter()
    children: dict[str, list[Decimal | None]] = defaultdict(list)
    detail_ids: set[str] = set()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        for name in (
            "SubCategoryCatalogue.csv",
            "ElectricityProductionPlant.csv",
            "PlantDetail.csv",
        ):
            if archive.namelist().count(name) != 1:
                raise ValueError(f"Expected one ZIP member: {name}")

        def rows(name: str, required: set[str]) -> Iterator[dict[str, str]]:
            with archive.open(name) as stream:
                reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig"))
                if not required <= set(reader.fieldnames or ()):
                    raise ValueError(f"Missing Swiss CSV columns: {name}")
                yield from reader

        codes = [
            row["en"].strip().casefold()
            for row in rows("SubCategoryCatalogue.csv", {"Catalogue_id", "en"})
            if row["Catalogue_id"] == "subcat_2"
        ]
        if codes != ["photovoltaic"]:
            raise ValueError("Unexpected Swiss PV code definition")
        for row in rows(
            "ElectricityProductionPlant.csv",
            {"xtf_id", "SubCategory", "InitialPower", "TotalPower", "BeginningOfOperation", "EGID"},
        ):
            identifier = row["xtf_id"]
            if not identifier or identifier in all_ids:
                raise ValueError("Missing or duplicate Swiss parent ID")
            all_ids.add(identifier)
            if row["SubCategory"] != "subcat_2":
                continue
            if row["EGID"]:
                buildings[row["EGID"]] += 1
            total = _kw(row["TotalPower"])
            if total >= threshold:
                candidates[identifier] = (row, total)

        for row in rows(
            "PlantDetail.csv", {"xtf_id", "ElectricityProductionPlantR", "Power", "Date"}
        ):
            identifier = row["xtf_id"]
            parent = row["ElectricityProductionPlantR"]
            if not identifier or identifier in detail_ids:
                raise ValueError("Missing or duplicate Swiss detail ID")
            detail_ids.add(identifier)
            if parent not in all_ids:
                raise ValueError("Orphan Swiss detail row")
            if parent in candidates:
                if row["Date"]:
                    date.fromisoformat(row["Date"])
                children[parent].append(_kw(row["Power"]) if row["Power"] else None)

    staged = []
    for identifier, (row, total) in sorted(candidates.items()):
        initial = _kw(row["InitialPower"])
        linked = children[identifier]
        known = [kw for kw in linked if kw is not None]
        child_total = sum(known, Decimal(0)) if linked and len(known) == len(linked) else None
        staged.append(
            {
                "source_parent_id": identifier,
                "technology": "photovoltaic",
                "beginning_of_operation": date.fromisoformat(
                    row["BeginningOfOperation"]
                ).isoformat(),
                "initial_power_kw": str(initial),
                "total_power_kw": str(total),
                "power_basis": "unspecified_ac_dc",
                "linked_detail_count": len(linked),
                "linked_detail_power_kw": str(child_total) if child_total is not None else None,
                "linked_detail_equals_parent_total": child_total == total
                if child_total is not None
                else None,
                "shared_building_review": bool(row["EGID"] and buildings[row["EGID"]] > 1),
                "disposition": "review_only",
            }
        )
    return staged
