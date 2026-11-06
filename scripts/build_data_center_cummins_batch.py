"""Build reviewed Cummins generator records from official product-page captures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_cummins_generator_table,
)

RETRIEVED_AT = "2026-11-03T08:17:47Z"
AS_OF = "2026-11-03"
SOURCES = (
    (
        "cummins-kta50-current-20261103",
        "https://www.cummins.com/en-na/generators/products/kta50",
        "cummins-kta50.html",
        5,
    ),
    (
        "cummins-qsk60-current-20261103",
        "https://www.cummins.com/en-na/generators/products/qsk60",
        "cummins-qsk60.html",
        17,
    ),
)


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observations(
    candidate: dict[str, Any],
    source_id: str,
    *,
    as_of: str = AS_OF,
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for kind, values in candidate["ratings"].items():
        for rating in values:
            for field, unit in (("kw", "kW"), ("kva", "kVA")):
                rows.append(
                    {
                        "as_of": as_of,
                        "boundary": (
                            f"{candidate['model']} at {candidate['frequency_hz']:g} Hz; "
                            f"Cummins {kind.replace('_', ' ')} rating"
                        ),
                        "field": f"{kind}_{field}",
                        "kind": "reported",
                        "locator": candidate["locator"],
                        "source_id": source_id,
                        "unit": unit,
                        "value": rating[field],
                    }
                )
    rows.append(
        {
            "as_of": as_of,
            "boundary": f"{candidate['model']} exact table configuration",
            "field": "fuel_type",
            "kind": "reported",
            "locator": candidate["locator"],
            "source_id": source_id,
            "unit": None,
            "value": candidate["fuel_type"],
        }
    )
    if candidate.get("engine_model"):
        rows.append(
            {
                "as_of": AS_OF,
                "boundary": f"{candidate['model']} exact table configuration",
                "field": "engine_model",
                "kind": "reported",
                "locator": candidate["locator"],
                "source_id": source_id,
                "unit": None,
                "value": candidate["engine_model"],
            }
        )
    return rows


def conflict_payload(
    candidate: dict[str, Any],
    source_id: str,
    *,
    retrieved_at: str = RETRIEVED_AT,
) -> str | None:
    conflicts = candidate["conflicts"]
    if not conflicts:
        return None
    unresolved: list[dict[str, object]] = []
    for rating_kind, ratings in conflicts.items():
        for field, unit in (("kw", "kW"), ("kva", "kVA")):
            values = sorted({rating[field] for rating in ratings})
            if len(values) < 2:
                continue
            unresolved.extend(
                {
                    "boundary": (
                        f"{candidate['model']} at {candidate['frequency_hz']:g} Hz; "
                        f"duplicate Cummins {rating_kind} rows"
                    ),
                    "field": f"{rating_kind}_{field}",
                    "observed_at": retrieved_at,
                    "sources": [source_id],
                    "unit": unit,
                    "value": value,
                }
                for value in values
            )
    # The current typed schema has no normalized prime/standby/general-continuous
    # columns. Keep the exact field labels on each observation and quarantine the
    # free-text notes field rather than misusing the DCC kW/kVA columns.
    return compact({"notes": unresolved}) if unresolved else None


def build_record(
    candidate: dict[str, Any],
    source_id: str,
    url: str,
    *,
    retrieved_at: str = RETRIEVED_AT,
    as_of: str = AS_OF,
) -> dict[str, object]:
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "equipment_category",
        "form_factor",
        "frequency_hz",
        "manufacturer",
        "model",
        "name",
        "observations_json",
        "official_url",
        "output_power_kw",
        "power_conditions",
        "power_rating_kind",
        "record_scope",
        "variant",
    ]
    conflicts = conflict_payload(candidate, source_id, retrieved_at=retrieved_at)
    if conflicts:
        fields.append("conflicts_json")
    locator = candidate["locator"]
    evidence = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {source_id: None},
        }
        for field in fields
    }
    for field, unit in (
        ("apparent_power_kva", "kVA"),
        ("frequency_hz", "Hz"),
        ("output_power_kw", "kW"),
    ):
        evidence[field]["unit"] = unit
    frequency = candidate["frequency_hz"]
    model = candidate["model"]
    row: dict[str, object] = {
        "apparent_power_kva": candidate["data_center_continuous_kva"],
        "capacity_scope": (
            f"Exact Cummins {model} {frequency:g} Hz configuration; normalized kW and kVA "
            "are Data Center Continuous ratings, not facility backup capacity"
        ),
        "created_at": retrieved_at,
        "entity_type": "equipment",
        "equipment_category": "backup_generator",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": "stationary diesel generator set",
        "frequency_hz": frequency,
        "last_verified_at": retrieved_at,
        "manufacturer": "Cummins",
        "model": model,
        "name": f"Cummins {model} {frequency:g} Hz Data Center Continuous generator",
        "observations_json": compact(observations(candidate, source_id, as_of=as_of)),
        "official_url": url,
        "output_power_kw": candidate["data_center_continuous_kw"],
        "power_conditions": (
            "OEM Data Center Continuous duty: continuous supply to a constant or varying "
            "electrical load for unlimited hours in a data-center application; exact "
            f"{frequency:g} Hz table row"
        ),
        "power_rating_kind": "Data Center Continuous generator output active/apparent power",
        "quality_status": "needs_review" if conflicts else "source_backed",
        "record_id": stable_id("equipment", "Cummins", model, f"{frequency:g} Hz", "DCC"),
        "record_scope": "configuration",
        "source_urls": [url],
        "sources": [source_id],
        "updated_at": retrieved_at,
        "variant": f"{frequency:g} Hz; Data Center Continuous; diesel",
    }
    if conflicts:
        row["conflicts_json"] = conflicts
    else:
        row["notes"] = (
            "Prime, standby and general continuous values are retained as observations. "
            "Only the explicit Data Center Continuous row is normalized; no power-factor "
            "conversion or facility-capacity inference is made."
        )
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows: list[dict[str, object]] = []
    identities: set[tuple[str, float]] = set()
    for source_id, url, filename, expected_count in SOURCES:
        staged = parse_cummins_generator_table(
            (args.capture_dir / filename).read_bytes(),
            source_url=url,
            expected_count=expected_count,
        )
        for candidate in staged["candidates"]:
            identity = (candidate["model"], candidate["frequency_hz"])
            if identity in identities:
                raise ValueError(f"Duplicate Cummins configuration across pages: {identity}")
            identities.add(identity)
            rows.append(build_record(candidate, source_id, url))
    rows.sort(key=lambda row: (row["model"], row["frequency_hz"]))
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Cummins generator configurations to {args.output}")


if __name__ == "__main__":
    main()
