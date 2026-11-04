"""Build reviewed Baudouin April 2025 Data Centre Power configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_generator_dcp_matrix,
)

RETRIEVED_AT = "2026-11-04T05:18:00Z"
AS_OF = "2026-11-04"
SOURCE_ID = "baudouin-dcp-rating-card-202504"
SOURCE_URL = (
    "https://baudouin.com/wp-content/uploads/2025/04/"
    "Baudouin_RatingCard_Genset-DCP-50-60-Hz-0425.pdf"
)
REVISION = "PK.R.228.EN.04.25; April 2025"

# Complete printed table: model, Hz, engine gross kWm, genset kWe, genset kVA,
# rpm, aspiration and governor. No standby/prime values are synthesized.
ROWS: tuple[tuple[str, int, int, int, int, int, str, str], ...] = (
    ("6M33G715/5", 50, 575, 500, 625, 1500, "T/A-A", "ECU"),
    ("6M33G825/5", 50, 675, 600, 750, 1500, "T/A-A", "ECU"),
    ("8M33G875/5", 50, 730, 640, 800, 1500, "T/A-A", "ECU"),
    ("8M33G1100/5", 50, 890, 800, 1000, 1500, "T/A-A", "ECU"),
    ("12M33G1265/5", 50, 1018, 920, 1150, 1500, "T/A-A", "ECU"),
    ("12M33G1410/5", 50, 1130, 1024, 1280, 1500, "T/A-A", "ECU"),
    ("12M33G1650/5", 50, 1350, 1200, 1500, 1500, "T/A-A", "ECU"),
    ("16M33G1900/5", 50, 1530, 1400, 1750, 1500, "T/A-W", "ECU"),
    ("16M33G2000/5", 50, 1680, 1500, 1875, 1500, "T/A-W", "ECU"),
    ("16M33G8D0/5", 50, 1800, 1600, 2000, 1500, "T/A-W", "ECU"),
    ("20M33G2250/5", 50, 1850, 1600, 2000, 1500, "T/A-W", "ECU"),
    ("20M33G2500/5", 50, 2010, 1800, 2250, 1500, "T/A-W", "ECU"),
    ("20M33G10D0/5", 50, 2210, 2000, 2500, 1500, "T/A-W", "ECU"),
    ("12M55G2550/5", 50, 1985, 1800, 2250, 1500, "T/A-W", "ECU"),
    ("12M55G2750/5", 50, 2200, 2000, 2500, 1500, "T/A-W", "ECU"),
    ("12M55G8D0/5", 50, 2420, 2200, 2750, 1500, "T/A-W", "ECU"),
    ("16M55G3300/5", 50, 2646, 2400, 3000, 1500, "T/A-W", "ECU"),
    ("16M55G3750/5", 50, 2900, 2600, 3250, 1500, "T/A-W", "ECU"),
    ("16M55G4000/5", 50, 3300, 3000, 3750, 1500, "T/A-W", "ECU"),
    ("6M33G580/6", 60, 575, 500, 625, 1800, "T/A-A", "ECU"),
    ("6M33G660/6", 60, 670, 600, 750, 1800, "T/A-A", "ECU"),
    ("8M33G700/6", 60, 730, 640, 800, 1800, "T/A-A", "ECU"),
    ("8M33G900/6", 60, 910, 800, 1000, 1800, "T/A-A", "ECU"),
    ("12M33G1105/6", 60, 1100, 1005, 1256, 1800, "T/A-A", "ECU"),
    ("12M33G1240/6", 60, 1235, 1100, 1375, 1800, "T/A-A", "ECU"),
    ("12M33G1320/6", 60, 1350, 1200, 1500, 1800, "T/A-A", "ECU"),
    ("16M33G1500/6", 60, 1530, 1400, 1750, 1800, "T/A-W", "ECU"),
    ("16M33G8D0/6", 60, 1750, 1600, 2000, 1800, "T/A-W", "ECU"),
    ("20M33G2000/6", 60, 2027, 1800, 2250, 1800, "T/A-W", "ECU"),
    ("20M33G2200/6", 60, 2200, 2000, 2500, 1800, "T/A-W", "ECU"),
    ("12M55G8D0/6", 60, 2450, 2250, 2813, 1800, "T/A-W", "ECU"),
    ("16M55G2640/6", 60, 2710, 2400, 3000, 1800, "T/A-W", "ECU"),
    ("16M55G3000/6", 60, 2930, 2640, 3300, 1800, "T/A-W", "ECU"),
    ("16M55G3300/6", 60, 3300, 3000, 3750, 1800, "T/A-W", "ECU"),
)

FIELDS = [
    "model",
    "frequency_hz",
    "engine_power_kwm",
    "output_power_kw",
    "apparent_power_kva",
    "speed_rpm",
    "aspiration",
    "governor",
    "locator",
]


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def extracted_csv() -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for model, hz, kwm, kw, kva, rpm, aspiration, governor in ROWS:
        writer.writerow(
            {
                "model": model,
                "frequency_hz": hz,
                "engine_power_kwm": kwm,
                "output_power_kw": kw,
                "apparent_power_kva": kva,
                "speed_rpm": rpm,
                "aspiration": aspiration,
                "governor": governor,
                "locator": f"April 2025 DCP rating card / {hz} Hz row {model}",
            }
        )
    return stream.getvalue().encode()


def observation(
    candidate: dict[str, Any], field: str, value: object, unit: str | None, boundary: str
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": candidate["locator"],
        "source_id": SOURCE_ID,
        "unit": unit,
        "value": value,
    }


def build_record(candidate: dict[str, Any]) -> dict[str, object]:
    model = candidate["model"]
    frequency = candidate["frequency_hz"]
    boundary = f"{model} {frequency:g} Hz exact Data Centre Power row"
    observations = [
        observation(
            candidate,
            "engine_gross_mechanical_power",
            candidate["engine_power_kwm"],
            "kWm",
            boundary,
        ),
        observation(candidate, "engine_speed", candidate["speed_rpm"], "rpm", boundary),
        observation(candidate, "aspiration", candidate["aspiration"], None, boundary),
        observation(candidate, "governor", candidate["governor"], None, boundary),
        observation(candidate, "document_revision", REVISION, None, "complete rating card"),
        observation(
            candidate,
            "data_centre_power_definition",
            (
                "maximum generating-set power for a variable or continuous electrical load "
                "during unlimited run hours; site and utility reliability may require "
                "hardware, software or maintenance-plan adaptation"
            ),
            None,
            "rating-card DCP definition; shared condition, not a site deployment",
        ),
    ]
    fields = [
        "apparent_power_kva",
        "capacity_scope",
        "equipment_category",
        "form_factor",
        "frequency_hz",
        "manufacturer",
        "model",
        "name",
        "notes",
        "observations_json",
        "official_url",
        "output_power_kw",
        "power_conditions",
        "power_rating_kind",
        "record_scope",
        "variant",
    ]
    evidence = {
        field: {
            "confidence": "high",
            "locator": candidate["locator"],
            "source_publication_dates": {SOURCE_ID: "2025-04-01"},
        }
        for field in fields
    }
    for field, unit in (
        ("apparent_power_kva", "kVA"),
        ("frequency_hz", "Hz"),
        ("output_power_kw", "kW"),
    ):
        evidence[field]["unit"] = unit
    return {
        "apparent_power_kva": candidate["apparent_power_kva"],
        "capacity_scope": (
            f"Exact Baudouin {model} {frequency:g} Hz DCP generator row; normalized kW "
            "is generator electrical output and kVA is generator apparent output, not "
            "engine mechanical power or facility backup capacity"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "backup_generator",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [SOURCE_ID] for field in fields}),
        "form_factor": "stationary diesel generator set",
        "frequency_hz": frequency,
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "Baudouin",
        "model": model,
        "name": f"Baudouin {model} {frequency:g} Hz Data Centre Power generator",
        "notes": (
            "Engine gross mechanical kWm, generator electrical kWe and generator kVA are "
            "kept distinct. Aspiration, governor and speed are exact row observations. "
            "No alternator, voltage, emissions package, installation or deployment is inferred."
        ),
        "observations_json": compact(observations),
        "official_url": SOURCE_URL,
        "output_power_kw": candidate["output_power_kw"],
        "power_conditions": (
            "OEM Data Centre Power (DCP): maximum generating-set power for variable or "
            "continuous electrical load during unlimited run hours; exact printed row"
        ),
        "power_rating_kind": "Data Centre Power generator output active/apparent power",
        "quality_status": "source_backed",
        "record_id": stable_id(
            "equipment", "Baudouin", model, f"{frequency:g} Hz", "DCP April 2025"
        ),
        "record_scope": "configuration",
        "source_urls": [SOURCE_URL],
        "sources": [SOURCE_ID],
        "updated_at": RETRIEVED_AT,
        "variant": f"{frequency:g} Hz; {candidate['speed_rpm']:g} rpm; DCP",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    staged = parse_generator_dcp_matrix(
        extracted_csv(), source_url=SOURCE_URL, expected_count=len(ROWS)
    )
    records = [build_record(candidate) for candidate in staged["candidates"]]
    if len(records) != 34 or len({record["record_id"] for record in records}) != 34:
        raise ValueError("Expected 34 unique Baudouin DCP configurations")
    records.sort(key=lambda record: (record["frequency_hz"], record["model"]))
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print(f"Wrote {len(records)} reviewed Baudouin DCP configurations")


if __name__ == "__main__":
    main()
