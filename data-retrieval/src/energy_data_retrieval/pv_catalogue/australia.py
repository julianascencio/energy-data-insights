"""Stage reviewed Australian PV stations from Geoscience Australia and AEMO.

The station inventory and survey have different capacity definitions. Review
decisions are tied to the two file checksums and never transfer GA's unspecified
capacity to an AC/DC field. Coordinates provide an independent identity check
for an existing record; automated proximity matching is deliberately disabled.
"""

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any

from .catalogue import canonical_json, load_records, stable_id

_STATES = {
    "ACT": "Australian Capital Territory",
    "NSW": "New South Wales",
    "QLD": "Queensland",
    "SA": "South Australia",
    "TAS": "Tasmania",
    "VIC": "Victoria",
    "WA": "Western Australia",
    "NT": "Northern Territory",
}
_STATUS = {"In Service": "operating", "In Commissioning": "commissioning"}
_HEADERS = {
    0: "AEMO Survey ID",
    1: "Site Name",
    5: "Region",
    9: "Technology Type",
    12: "DUID",
    17: "Agg Nameplate Capacity (MW DC)",
    18: "Agg Nameplate Capacity (MW AC)",
    20: "Commitment Status",
    21: "Full Commercial Use Date",
}


def _site(value: str) -> str:
    name = re.sub(r"\s+solar(?:\s+(?:farm|plant|park|project))?$", "", value.lower())
    return re.sub(r"[^a-z0-9]", "", name)


def _positive(value: Any) -> bool:
    return type(value) in {int, float} and math.isfinite(value) and value > 0


def stage_australian_stations(
    stations: dict[str, Any],
    survey_rows: list[tuple[Any, ...]],
    decisions: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    *,
    ga_source: str,
    survey_source: str,
    survey_date: str,
) -> list[dict[str, Any]]:
    """Stage explicit decisions against a complete ArcGIS response and survey."""
    if stations.get("exceededTransferLimit") or "features" not in stations:
        raise ValueError("A complete GA response is required")
    features = [item["attributes"] for item in stations["features"]]
    by_guid = {x["globalid"]: x for x in features}
    if len(by_guid) != len(features):
        raise ValueError("Duplicate GA identifier")
    if any(survey_rows[3][i] != label for i, label in _HEADERS.items()):
        raise ValueError("Unexpected AEMO survey layout")
    survey = [(i, row) for i, row in enumerate(survey_rows[4:], 5) if row[0]]
    by_duid: dict[str, list[tuple[int, tuple[Any, ...]]]] = {}
    for i, row in survey:
        if row[12]:
            by_duid.setdefault(row[12], []).append((i, row))
    survey_counts = Counter(row[0] for _, row in survey)
    ga_names = Counter(
        (_site(x["feature_name"]), x["state"])
        for x in features
        if x["technology_type"] == "Solar Photovoltaic"
    )
    australia = [r for r in existing if r.get("country_code") == "AUS"]
    as_of = date.fromisoformat(survey_date)
    result = []
    used_records: set[str] = set()
    used_guids: set[str] = set()
    used_duids: set[str] = set()
    for decision in decisions:
        g = by_guid[decision["ga_globalid"]]
        duid = decision["aemo_duid"]
        entries = by_duid.get(duid, [])
        if len(entries) != 1:
            raise ValueError(f"Nonunique AEMO DUID: {duid}")
        number, row = entries[0]
        state = g["state"]
        name = g["feature_name"]
        identity = _site(name)
        if (
            not identity
            or ga_names[identity, state] != 1
            or g["technology_type"] != "Solar Photovoltaic"
            or row[9] != "Solar PV"
            or _site(row[1]) != identity
            or row[5] != ("NSW1" if state == "ACT" else state + "1")
            or survey_counts[row[0]] != 1
            or g["objectid"] != decision["ga_objectid"]
            or number != decision["survey_row"]
            or g["globalid"] in used_guids
            or duid in used_duids
        ):
            raise ValueError(f"Unresolved station boundary: {name} / {duid}")
        used_guids.add(g["globalid"])
        used_duids.add(duid)
        matches = [
            r
            for r in australia
            if any(_site(a) == identity for a in [r["name"], *(r.get("aliases") or [])])
        ]
        current_id = decision.get("record_id")
        linked = [
            r
            for r in australia
            if g["globalid"] in json.loads(r.get("external_ids_json") or "{}").values()
            or duid in json.loads(r.get("external_ids_json") or "{}").values()
            or any(
                phase.get("Phase Name") == duid
                for phase in json.loads(r.get("phases_json") or "[]")
            )
        ]
        if any(r["record_id"] != current_id for r in linked):
            raise ValueError(f"Identifier is already assigned: {duid}")
        locality = decision["locality"]
        if locality.casefold() != g["locality"].casefold():
            raise ValueError(f"Unreviewed locality: {name}")
        if current_id:
            if (
                len(matches) != 1
                or matches[0]["record_id"] != current_id
                or matches[0].get("region") != _STATES[state]
            ):
                raise ValueError(f"Canonical identity has changed: {name}")
            old = matches[0]
            if old.get("locality") not in (None, locality):
                raise ValueError(f"Existing locality differs: {name}")
            d_lat = old["latitude"] - g["latitude"]
            d_lon = (old["longitude"] - g["longitude"]) * math.cos(math.radians(g["latitude"]))
            if math.hypot(d_lat, d_lon) * 111 > 3:
                raise ValueError(f"Canonical and GA positions differ: {name}")
            item = {"record_id": current_id, "locality": locality}
            mapping = {"locality": ga_source}
            # Do not emit repeat observations after the same locality has been applied.
            if old.get("locality") == locality:
                continue
        else:
            if matches or row[20] not in _STATUS or g["spatial_confidence"] != 5:
                raise ValueError(f"New identity or status requires review: {name}")
            if not (-44 <= g["latitude"] <= -9 and 112 <= g["longitude"] <= 155):
                raise ValueError(f"Unexpected Australian coordinates: {name}")
            item = {
                "record_id": stable_id("projects", "AUS", "geoscience_australia", g["globalid"]),
                "name": name,
                "country_code": "AUS",
                "region": _STATES[state],
                "locality": locality,
                "latitude": g["latitude"],
                "longitude": g["longitude"],
                "location_accuracy": "GA power station point (GDA2020; native confidence class 5)",
                "technology": "photovoltaic",
                "quality_status": "primary_source_extract",
                "external_ids_json": canonical_json(
                    {"aemo_duid": duid, "aemo_survey_id": row[0], "ga_globalid": g["globalid"]}
                ),
                "status": _STATUS[row[20]],
                "source_date": survey_date,
            }
            mapping = {
                "*": ga_source,
                "status": survey_source,
                "source_date": survey_source,
                "external_ids_json": [ga_source, survey_source],
            }
            # Require deliberate rating approval; a generic GA MW value has no comparable basis.
            for field, column in (("capacity_ac_mw", 18), ("capacity_dc_mw", 17)):
                if field in decision.get("approve_nameplate", ()) and _positive(row[column]):
                    item[field] = row[column]
                    mapping[field] = survey_source
            use = row[21]
            if (
                row[20] == "In Service"
                and isinstance(use, datetime)
                and use.date() <= as_of
                and use.year >= 2000
            ):
                item["commissioning_date"] = use.date().isoformat()
                mapping["commissioning_date"] = survey_source
        if item["record_id"] in used_records:
            raise ValueError(f"Duplicate canonical candidate: {name}")
        used_records.add(item["record_id"])
        result.append(
            dict(
                item,
                entity_type="projects",
                sources=sorted({ga_source, survey_source}),
                field_sources_json=canonical_json(mapping),
            )
        )
    return result


def main() -> None:
    """Write staged JSONL for the catalogue's ordinary upsert command."""
    from openpyxl import load_workbook

    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("stations", "survey", "review", "catalogue", "output"):
        parser.add_argument(name, type=Path)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    ga = args.stations.read_bytes()
    if hashlib.sha256(ga).hexdigest() != review["ga_sha256"] or (
        hashlib.sha256(args.survey.read_bytes()).hexdigest() != review["survey_sha256"]
    ):
        raise ValueError("Review decisions are pinned to different source bytes")
    workbook = load_workbook(args.survey, read_only=True, data_only=True)
    try:
        rows = list(workbook["Generator Information"].values)
    finally:
        workbook.close()
    records = stage_australian_stations(
        json.loads(ga),
        rows,
        review["accepted"],
        load_records(args.catalogue),
        ga_source=review["ga_source"],
        survey_source=review["survey_source"],
        survey_date=review["survey_date"],
    )
    with args.output.open("x", encoding="utf-8") as handle:
        for item in records:
            handle.write(canonical_json(item) + "\n")


if __name__ == "__main__":
    main()
