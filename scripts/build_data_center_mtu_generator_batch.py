"""Build reviewed mtu Series 4000 Data Center Continuous configurations."""

from __future__ import annotations

import argparse
import csv
import io
import json
from pathlib import Path
from typing import Any, TypedDict

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.inventories import (
    parse_generator_rating_matrix,
)

RETRIEVED_AT = "2026-11-03T17:26:00Z"
AS_OF = "2026-11-03"
FIFTY_HZ_URL = (
    "https://www.mtu-solutions.com/content/dam/mtu/download/applications/"
    "power-generation/16120753_PowerGeneration_S4000_Diesel_brochure.pdf/"
    "_jcr_content/renditions/original./"
    "16120753_PowerGeneration_S4000_Diesel_brochure.pdf"
)
SIXTY_HZ_URL = (
    "https://www.mtu-solutions.com/content/dam/mtu/download/applications/"
    "power-generation/16120923_mtu_S4000_Diesel_brochure_60Hz.pdf/"
    "_jcr_content/renditions/original./"
    "16120923_mtu_S4000_Diesel_brochure_60Hz.pdf"
)


class SourceSpec(TypedDict):
    source_id: str
    url: str
    revision: str
    voltages: list[int]
    page: str


SOURCES: dict[float, SourceSpec] = {
    50.0: {
        "source_id": "mtu-series-4000-50hz-edition-202101",
        "url": FIFTY_HZ_URL,
        "revision": "1620735 | Edition 01/21 | BMC 2021-07",
        "voltages": [380, 400, 415, 6300, 6600, 10000, 10500, 11000],
        "page": "printed page 14",
    },
    60.0: {
        "source_id": "mtu-series-4000-60hz-edition-202301",
        "url": SIXTY_HZ_URL,
        "revision": "16120923 | Edition 01/23 | BMC 2023-04",
        "voltages": [380, 416, 440, 480, 600, 4160, 12470, 13200, 13800],
        "page": "Power Ratings table",
    },
}

# Each tuple is one complete printed row: model, standby, stationary-emergency,
# Data Center Continuous and prime kVA. None preserves a printed dash.
FIFTY_HZ_ROWS: tuple[tuple[str, float, float | None, float, float | None], ...] = (
    ("12V4000 DS1650", 1780, 1600, 1600, 1600),
    ("12V4000 DS1750", 1880, 1700, 1700, 1700),
    ("12V4000 DS2000", 2080, 1880, 1880, 1880),
    ("12V4000 DS2250", 2300, 2100, 2100, None),
    ("16V4000 DS2250", 2330, 2160, 2160, 2160),
    ("16V4000 DS2500", 2610, 2360, 2360, 2360),
    ("16V4000 DS2750", 2850, 2600, 2600, None),
    ("20V4000 DS2750", 2800, 2640, 2640, 2640),
    ("20V4000 DS3100", 3200, 2910, 2910, 2910),
    ("20V4000 DS3300", 3410, 3110, 3110, 3110),
    ("20V4000 DS3600", 3730, None, 3390, 3390),
    ("20V4000 DS4000", 4000, 3630, 3630, None),
)
SIXTY_HZ_ROWS: tuple[tuple[str, float, float | None, float, float | None], ...] = (
    ("12V4000 DS1250", 1250, 1125, 1125, 1125),
    ("12V4000 DS1500", 1500, 1400, 1400, 1400),
    ("12V4000 DS 1750", 1750, 1600, 1600, 1600),
    ("16V4000 DS2000", 2000, 1800, 1800, 1800),
    ("16V4000 DS2250", 2250, 2045, 2045, 2045),
    ("20V4000 DS2500", 2500, 2250, 2250, 2250),
    ("20V4000 DS2800", 2800, 2500, 2500, 2500),
    ("20V4000 DS3000", 3000, 2800, 2800, 2800),
)


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def extracted_csv(
    rows: tuple[tuple[str, float, float | None, float, float | None], ...],
    *,
    frequency: float,
) -> bytes:
    stream = io.StringIO(newline="")
    fields = [
        "model",
        "frequency_hz",
        "speed_rpm",
        "standby_kva",
        "prime_emergency_kva",
        "data_center_continuous_kva",
        "prime_kva",
        "locator",
    ]
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    page = SOURCES[frequency]["page"]
    for model, standby, emergency, dcc, prime in rows:
        writer.writerow(
            {
                "model": model,
                "frequency_hz": frequency,
                "speed_rpm": 1500 if frequency == 50 else 1800,
                "standby_kva": standby,
                "prime_emergency_kva": "" if emergency is None else emergency,
                "data_center_continuous_kva": dcc,
                "prime_kva": "" if prime is None else prime,
                "locator": f"{page}, {frequency:g} Hz row {model}",
            }
        )
    return stream.getvalue().encode()


def observation(
    *,
    field: str,
    value: object,
    unit: str | None,
    boundary: str,
    locator: str,
    source_id: str,
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }


def build_record(candidate: dict[str, Any]) -> dict[str, object]:
    frequency = candidate["frequency_hz"]
    source = SOURCES[frequency]
    source_id = source["source_id"]
    locator = candidate["locator"]
    model = candidate["model"]
    boundary = f"{model} {frequency:g} Hz printed generator-set row"
    observations = [
        observation(
            field="standby_apparent_power",
            value=candidate["standby_kva"],
            unit="kVA",
            boundary=boundary,
            locator=locator,
            source_id=source_id,
        ),
        observation(
            field="data_center_continuous_apparent_power",
            value=candidate["data_center_continuous_kva"],
            unit="kVA",
            boundary=boundary,
            locator=locator,
            source_id=source_id,
        ),
        observation(
            field="engine_speed",
            value=candidate["speed_rpm"],
            unit="rpm",
            boundary=boundary,
            locator=locator,
            source_id=source_id,
        ),
    ]
    for field, key in (
        ("prime_power_stationary_emergency_apparent_power", "prime_emergency_kva"),
        ("prime_apparent_power", "prime_kva"),
    ):
        if candidate[key] is not None:
            observations.append(
                observation(
                    field=field,
                    value=candidate[key],
                    unit="kVA",
                    boundary=boundary,
                    locator=locator,
                    source_id=source_id,
                )
            )
    for field, value, unit in (
        ("data_center_continuous_load", "continuous", None),
        ("data_center_continuous_max_load_factor", 100, "%"),
        ("data_center_continuous_overload_available", "10% overload", None),
        ("data_center_continuous_max_operating_hours", "unlimited*", "hours/year"),
        ("uptime_compliance_claim", "Tier III & Tier IV", None),
        ("portfolio_available_voltage_options", source["voltages"], "V"),
        ("document_revision", source["revision"], None),
    ):
        observations.append(
            observation(
                field=field,
                value=value,
                unit=unit,
                boundary=(
                    f"Series 4000 {frequency:g} Hz Data Center Continuous column; "
                    "shared table condition, not an ordered model option"
                ),
                locator=locator,
                source_id=source_id,
            )
        )
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
        "power_conditions",
        "power_rating_kind",
        "record_scope",
        "variant",
    ]
    evidence = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {source_id: None},
        }
        for field in fields
    }
    evidence["apparent_power_kva"]["unit"] = "kVA"
    evidence["frequency_hz"]["unit"] = "Hz"
    return {
        "apparent_power_kva": candidate["data_center_continuous_kva"],
        "capacity_scope": (
            f"Exact mtu {model} {frequency:g} Hz row; normalized value is the OEM's "
            "Data Center Continuous (3F) apparent power, not active kW or facility capacity"
        ),
        "created_at": RETRIEVED_AT,
        "entity_type": "equipment",
        "equipment_category": "backup_generator",
        "evidence_json": compact(evidence),
        "field_sources_json": compact({field: [source_id] for field in fields}),
        "form_factor": "stationary diesel generator set",
        "frequency_hz": frequency,
        "last_verified_at": RETRIEVED_AT,
        "manufacturer": "mtu",
        "model": model,
        "name": f"mtu {model} {frequency:g} Hz Data Center Continuous generator",
        "notes": (
            "The brochure reports kVA only for this row, so active output kW is null. "
            "Portfolio voltage choices and the Tier III/IV compliance statement remain "
            "observations, not a selected winding or issuer-registry certification. "
            "Power may vary with generator voltage and ambient conditions."
        ),
        "observations_json": compact(observations),
        "official_url": source["url"],
        "power_conditions": (
            "OEM Data Center Continuous (3F): continuous load, maximum load factor <=100%, "
            "10% overload available, unlimited operating hours; standard-scope output may "
            "vary with generator voltage and ambient conditions"
        ),
        "power_rating_kind": "Data Center Continuous (3F) apparent power",
        "quality_status": "source_backed",
        "record_id": stable_id("equipment", "mtu", model, f"{frequency:g} Hz", "DCC 3F"),
        "record_scope": "configuration",
        "source_urls": [source["url"]],
        "sources": [source_id],
        "updated_at": RETRIEVED_AT,
        "variant": f"{frequency:g} Hz; {candidate['speed_rpm']:g} rpm; DCC 3F; kVA",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    candidates: list[dict[str, Any]] = []
    for frequency, rows in ((50.0, FIFTY_HZ_ROWS), (60.0, SIXTY_HZ_ROWS)):
        source = SOURCES[frequency]
        staged = parse_generator_rating_matrix(
            extracted_csv(rows, frequency=frequency),
            source_url=source["url"],
            expected_count=len(rows),
        )
        candidates.extend(staged["candidates"])
    records = [build_record(candidate) for candidate in candidates]
    if len(records) != 20 or len({record["record_id"] for record in records}) != 20:
        raise ValueError("Expected 20 unique mtu Series 4000 DCC configurations")
    records.sort(key=lambda record: (record["frequency_hz"], record["model"]))
    args.output.write_text("".join(f"{compact(record)}\n" for record in records), encoding="utf-8")
    print("Wrote 20 reviewed mtu Series 4000 DCC configurations")


if __name__ == "__main__":
    main()
