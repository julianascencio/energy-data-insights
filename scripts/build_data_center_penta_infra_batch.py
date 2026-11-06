"""Build the reviewed 12-facility Penta Infra displayed-directory batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_penta_infra_directory,
    parse_penta_infra_site_page,
)

RETRIEVED_AT = "2026-11-06T03:30:00Z"
AS_OF = "2026-11-06"
ORG_NAME = "Penta Infra"
ORG_ID = stable_id("organization", ORG_NAME)
DIRECTORY_SOURCE = "penta-infra-directory-current-20261106"
DIRECTORY_URL = "https://penta-infra.com/data-centers/"
META = {
    "amsterdam": ("AMS01", "Amsterdam", "NLD", "under_construction"),
    "geleen": ("GLN01", "Geleen", "NLD", "operational"),
    "leeuwarden-01": ("LEE01", "Leeuwarden", "NLD", "operational"),
    "leeuwarden-02": ("LEE02", "Leeuwarden", "NLD", "operational"),
    "berlin": ("BER01", "Berlin", "DEU", "operational"),
    "cologne": ("CGN01", "Cologne", "DEU", "operational"),
    "duesseldorf": ("DUS01", "Düsseldorf", "DEU", "operational"),
    "hamburg": ("HAM01", "Hamburg", "DEU", "operational"),
    "leipzig": ("LEJ01", "Leipzig", "DEU", "operational"),
    "brussels": ("BRU01", "Brussels", "BEL", "operational"),
    "paris": ("PAR01", "Paris", "FRA", "operational"),
    "copenhagen": ("CPH01", "Copenhagen", "DNK", "operational"),
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *, field: str, value: object, unit: str | None, source_id: str, boundary: str
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": "current directory card and exact facility page",
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }


def load_inputs(capture_dir: Path) -> dict[str, dict[str, Any]]:
    directory_rows = parse_penta_infra_directory(
        (capture_dir / "directory.html").read_bytes(), source_url=DIRECTORY_URL
    )["candidates"]
    directory = {row["external_id"]: row for row in directory_rows}
    if set(directory) != set(META):
        raise ValueError("Changed Penta Infra displayed-directory identity set")
    candidates: dict[str, dict[str, Any]] = {}
    for slug, (code, _locality, _country, expected_status) in META.items():
        url = f"https://penta-infra.com/data-centers/{slug}/"
        detail = parse_penta_infra_site_page(
            (capture_dir / f"{slug}.html").read_bytes(),
            source_url=url,
            expected_code=code,
        )["candidate"]
        listing = directory[slug]
        if listing["status"] != expected_status:
            raise ValueError(f"Changed Penta Infra status for {code}")
        for field in ("it_capacity_mw", "technical_area_m2"):
            if detail[field] != listing[field]:
                raise ValueError(f"Penta Infra directory/detail mismatch for {code} {field}")
        candidates[slug] = {**detail, "status_label": listing["status_label"]}
    return candidates


def observations(slug: str, candidate: dict[str, Any]) -> list[dict[str, object]]:
    code = META[slug][0]
    source_id = f"penta-infra-{slug}-current-20261106"
    rows = [
        observation(
            field="directory_lifecycle_label",
            value=candidate["status_label"],
            unit=None,
            source_id=DIRECTORY_SOURCE,
            boundary=f"Displayed current directory label for {code}",
        ),
        observation(
            field="reported_it_space",
            value=candidate["technical_area_m2"],
            unit="m2",
            source_id=source_id,
            boundary=f"{code} operator-labelled IT space; not land or gross building area",
        ),
    ]
    if slug == "amsterdam":
        rows.append(
            observation(
                field="ready_for_service_target",
                value="H1 2026",
                unit=None,
                source_id=source_id,
                boundary=(
                    "Stale target retained as reported; current page still says the facility "
                    "is being developed, so operation is not inferred"
                ),
            )
        )
    elif slug == "duesseldorf":
        rows.append(
            observation(
                field="future_campus_it_capacity",
                value=9.5,
                unit="MW",
                source_id=source_id,
                boundary=(
                    "Future Düsseldorf campus including DUS01 expansion; not DUS01 current rating"
                ),
            )
        )
    elif slug == "leipzig":
        rows.append(
            observation(
                field="future_campus_identity",
                value="LEJ01 with planned LEJ02",
                unit=None,
                source_id=source_id,
                boundary=(
                    "Future campus statement; LEJ02 is not created without lifecycle "
                    "and rating evidence"
                ),
            )
        )
    elif slug == "paris":
        rows.append(
            observation(
                field="reported_it_capacity_potential_lower_bound",
                value=15.0,
                unit="MW",
                source_id=source_id,
                boundary=(
                    "Narrative states 15+ MW potential; exact 15 MW planned card is "
                    "normalized separately"
                ),
            )
        )
    elif slug == "copenhagen":
        rows.append(
            observation(
                field="future_campus_it_capacity",
                value=7.6,
                unit="MW",
                source_id=source_id,
                boundary=(
                    "Planned CPH01/CPH02/CPH03 campus scope; not CPH01 current facility rating"
                ),
            )
        )
    return rows


def build_record(slug: str, candidate: dict[str, Any]) -> dict[str, object]:
    code, locality, country, status = META[slug]
    source_id = f"penta-infra-{slug}-current-20261106"
    url = f"https://penta-infra.com/data-centers/{slug}/"
    source_ids = [DIRECTORY_SOURCE, source_id]
    fields = [
        "aggregation_role",
        "aliases",
        "capacity_scope",
        "country_code",
        "entities_json",
        "external_ids_json",
        "facility_id",
        "facility_type",
        "it_capacity_basis",
        "it_capacity_mw",
        "locality",
        "name",
        "observations_json",
        "official_url",
        "operator_names",
        "owner_names",
        "record_scope",
        "status",
        "status_as_of",
        "status_date_basis",
        "technical_area_m2",
    ]
    evidence = {
        field: {
            "confidence": "high",
            "locator": candidate["locator"],
            "source_publication_dates": {source: None for source in source_ids},
            **(
                {"unit": "MW"}
                if field == "it_capacity_mw"
                else {"unit": "m2"}
                if field == "technical_area_m2"
                else {}
            ),
        }
        for field in fields
    }
    capacity_basis = "ultimate_planned" if slug == "paris" else "design_maximum"
    capacity_scope = (
        f"{code} facility only; operator-labelled IT capacity and IT space cards. "
        "Future campus expansions and unnamed phases are excluded."
    )
    if slug == "paris":
        capacity_scope += (
            " The exact 15 MW planned card is distinct from the 15+ MW potential narrative."
        )
    return {
        "aggregation_role": "independent",
        "aliases": [locality, code],
        "capacity_scope": capacity_scope,
        "country_code": country,
        "created_at": RETRIEVED_AT,
        "entities_json": compact(
            [
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "owner"},
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "operator"},
            ]
        ),
        "entity_type": "projects",
        "evidence_json": compact(evidence),
        "external_ids_json": compact({"penta_infra": code}),
        "facility_id": stable_id("facility", ORG_NAME, code),
        "facility_type": "colocation",
        "field_sources_json": compact({field: source_ids for field in fields}),
        "it_capacity_basis": capacity_basis,
        "it_capacity_mw": candidate["it_capacity_mw"],
        "last_verified_at": RETRIEVED_AT,
        "locality": locality,
        "name": f"Penta Infra {code}",
        "observations_json": compact(observations(slug, candidate)),
        "official_url": url,
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "source_backed",
        "record_id": stable_id("projects", ORG_NAME, code),
        "record_scope": "facility",
        "source_urls": [DIRECTORY_URL, url],
        "sources": source_ids,
        "status": status,
        "status_as_of": AS_OF,
        "status_date_basis": (
            "Current directory and exact page still state facility is being developed"
            if slug == "amsterdam"
            else "Current operator directory explicitly labels facility in operation"
        ),
        "technical_area_m2": candidate["technical_area_m2"],
        "updated_at": RETRIEVED_AT,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    candidates = load_inputs(args.capture_dir)
    rows = [build_record(slug, candidates[slug]) for slug in META]
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed Penta Infra facility records to {args.output}")


if __name__ == "__main__":
    main()
