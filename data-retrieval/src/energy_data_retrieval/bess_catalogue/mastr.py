"""Offline, review-only staging of MaStR revision 26.2 storage XML partitions.

Units and storage installations have different IDs and rating boundaries. No
site aggregation, fuzzy identity matching, operator-name lookup or COD inference
is performed. Downloaded XML and ZIP members remain outside the repository.
"""

from __future__ import annotations

import hashlib
import math
import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date
from pathlib import Path
from typing import Any


def _rows(path: Path, root_name: str, row_name: str):
    """Yield one flat source row at a time without retaining the XML tree."""
    with path.open("rb") as stream:
        context = ET.iterparse(stream, events=("start", "end"))
        _, root = next(context)
        if root.tag != root_name:
            raise ValueError(f"Unexpected XML root: {root.tag}")
        for event, element in context:
            if event == "end" and element.tag == row_name:
                keys = [child.tag for child in element]
                if len(set(keys)) != len(keys):
                    raise ValueError("Duplicate XML field")
                yield {child.tag: child.text for child in element}
                root.clear()


def _number(value: str | None) -> float | None:
    if value is None or value == "":
        return None
    result = float(value)
    if not math.isfinite(result) or result < 0:
        raise ValueError("Expected finite nonnegative registry rating")
    return result


def _identity(value: str | None, prefix: str) -> str:
    if not value or not re.fullmatch(prefix + r"\d{12}", value):
        raise ValueError(f"Invalid {prefix} identity")
    return value


def stage_mastr_storage(
    unit_paths: list[Path],
    storage_paths: list[Path],
    values_path: Path,
    *,
    snapshot_date: str,
    minimum_kw: float = 1000,
) -> list[dict[str, Any]]:
    """Stage ratings >= threshold, including flagged non-battery exclusions.

    Duplicate IDs fail across partitions. Shared locations are flagged using all
    supplied battery units, including those below the power threshold. This is
    not a guarantee of completeness across omitted export partitions. Energy
    joins require a reciprocal, single-unit storage link; otherwise energy is
    withheld. Raw source dates remain observations, never commercial COD.
    """
    as_of = date.fromisoformat(snapshot_date)
    if not math.isfinite(minimum_kw) or minimum_kw < 0:
        raise ValueError("Invalid minimum power")
    values = {r["Id"]: r["Wert"] for r in _rows(values_path, "Katalogwerte", "Katalogwert")}
    if values.get("524") != "Batterie" or values.get("35") != "In Betrieb":
        raise ValueError("Unreviewed MaStR classification mapping")
    seen: set[str] = set()
    locations: Counter[str] = Counter()
    staged: list[dict[str, Any]] = []
    for path in unit_paths:
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        for number, r in enumerate(
            _rows(path, "EinheitenStromSpeicher", "EinheitStromSpeicher"), 1
        ):
            uid = _identity(r.get("EinheitMastrNummer"), "SEE")
            if uid in seen:
                raise ValueError("Duplicate unit identity across supplied partitions")
            seen.add(uid)
            location = r.get("LokationMaStRNummer")
            if location and r.get("Technologie") == "524":
                locations[location] += 1
            power = _number(r.get("Nettonennleistung"))
            if power is None or power < minimum_kw:
                continue
            flags = []
            if r.get("Technologie") != "524":
                flags.append("not_battery")
            if r.get("Land") != "84":
                flags.append("not_germany")
            if not location:
                flags.append("missing_location_identity")
            if r.get("EinheitBetriebsstatus") not in {"31", "35", "37", "38"}:
                flags.append("unmapped_status")
            if not r.get("NameStromerzeugungseinheit"):
                flags.append("missing_name")
            commissioning = r.get("Inbetriebnahmedatum")
            if commissioning:
                parsed = date.fromisoformat(commissioning)
                if parsed.year < 1990 or parsed > as_of:
                    flags.append("commissioning_date_requires_review")
            staged.append(
                {
                    "unit_id": uid,
                    "storage_id": r.get("SpeMastrNummer"),
                    "location_id": location,
                    "operator_id": r.get("AnlagenbetreiberMastrNummer"),
                    "name": r.get("NameStromerzeugungseinheit"),
                    "locality": r.get("Ort"),
                    "municipality": r.get("Gemeinde"),
                    "region": values.get(r.get("Bundesland", "")),
                    "net_power_mw": power / 1000,
                    "gross_power_kw": _number(r.get("Bruttoleistung")),
                    "inverter_active_power_kw": _number(
                        r.get("ZugeordnenteWirkleistungWechselrichter")
                    ),
                    "chemistry_label": values.get(r.get("Batterietechnologie", "")),
                    "technology_label": values.get(r.get("Technologie", "")),
                    "status_code": r.get("EinheitBetriebsstatus"),
                    "status_label": values.get(r.get("EinheitBetriebsstatus", "")),
                    "commissioning_date_reported": commissioning,
                    "retirement_date_reported": r.get("DatumEndgueltigeStilllegung"),
                    "last_source_update": r.get("DatumLetzteAktualisierung"),
                    "network_verification_label": values.get(
                        r.get("NetzbetreiberpruefungStatus", "")
                    ),
                    "network_verification_date": r.get("NetzbetreiberpruefungDatum"),
                    "coupling_label": values.get(r.get("AcDcKoppelung", "")),
                    "latitude_reported": r.get("Breitengrad"),
                    "longitude_reported": r.get("Laengengrad"),
                    "source_member": path.name,
                    "source_row": number,
                    "source_sha256": digest,
                    "snapshot_date": snapshot_date,
                    "review_flags": flags,
                }
            )
    wanted = {r["storage_id"] for r in staged}
    installations: dict[str, dict[str, Any]] = {}
    storage_seen: set[str] = set()
    for path in storage_paths:
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        for number, r in enumerate(_rows(path, "AnlagenStromSpeicher", "AnlageStromSpeicher"), 1):
            sid = _identity(r.get("MaStRNummer"), "SSE")
            if sid in storage_seen:
                raise ValueError("Duplicate storage identity across supplied partitions")
            storage_seen.add(sid)
            if sid in wanted:
                installations[sid] = {
                    "usable_energy_kwh": _number(r.get("NutzbareSpeicherkapazitaet")),
                    "linked_units": r.get("VerknuepfteEinheitenMaStRNummern"),
                    "source_member": path.name,
                    "source_row": number,
                    "source_sha256": digest,
                }
    for row in staged:
        flags = row["review_flags"]
        if locations[row["location_id"]] > 1:
            flags.append("shared_battery_location_in_supplied_partitions")
        row["storage_observation"] = installations.get(row["storage_id"])
        storage = row["storage_observation"]
        row["usable_energy_mwh"] = None
        if not storage or storage["linked_units"] != row["unit_id"]:
            flags.append("missing_or_nonexclusive_reciprocal_storage_link")
        elif storage["usable_energy_kwh"] is not None:
            row["usable_energy_mwh"] = storage["usable_energy_kwh"] / 1000
    return staged
