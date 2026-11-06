"""Build the reviewed eight-identity maincubes current-directory batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_maincubes_directory,
    parse_maincubes_site_page,
)

RETRIEVED_AT = "2026-11-06T05:27:14Z"
AS_OF = "2026-11-06"
ORG_NAME = "maincubes"
ORG_ID = stable_id("organization", ORG_NAME)
DIRECTORY_URL = "https://www.maincubes.com/en/data-centers/"
META = {
    "FRA05": ("Frankfurt", "DEU", "facility", None),
    "FRA04": (
        "Frankfurt",
        "DEU",
        "facility",
        "hyperscale-data-center-fra04",
    ),
    "FRA03": (
        "Frankfurt",
        "DEU",
        "facility",
        "carrier-neutral-data-center-fra03",
    ),
    "FRA02": ("Frankfurt", "DEU", "facility", "frankfurt-02"),
    "FRA01": ("Frankfurt", "DEU", "facility", "frankfurt-01"),
    "BER02": (
        "Berlin",
        "DEU",
        "campus",
        "berlin-cloud-ai-provider-campus-ber02",
    ),
    "BER01": ("Berlin", "DEU", "facility", "berlin-01"),
    "AMS01": ("Amsterdam", "NLD", "facility", "amsterdam-01"),
}
STATUS = {
    "Pipeline": "announced",
    "In Planning": "announced",
    "Construction": "under_construction",
    "In Operation": "operational",
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *,
    field: str,
    value: object,
    unit: str | None,
    source_id: str,
    locator: str,
    boundary: str,
    kind: str = "reported",
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": kind,
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
    }


def load_inputs(
    capture_dir: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    directory_rows = parse_maincubes_directory(
        (capture_dir / "data-centers.html").read_bytes(), source_url=DIRECTORY_URL
    )["candidates"]
    directory = {row["external_id"]: row for row in directory_rows}
    if list(directory) != list(META):
        raise ValueError("Changed maincubes current directory identity set")
    details: dict[str, dict[str, Any]] = {}
    for code, (_locality, _country, _scope, slug) in META.items():
        if slug is None:
            continue
        url = f"{DIRECTORY_URL}{slug}/"
        details[code] = parse_maincubes_site_page(
            (capture_dir / f"{code}.html").read_bytes(),
            source_url=url,
            expected_code=code,
        )["candidate"]
        if details[code]["status_label"] != directory[code]["status_label"]:
            raise ValueError(f"Changed maincubes lifecycle agreement for {code}")
    return directory, details


def make_evidence(fields: list[str], source_ids: list[str], locator: str) -> tuple[str, str]:
    field_sources = {field: source_ids for field in fields}
    evidence = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": {source_id: None for source_id in source_ids},
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
    return compact(field_sources), compact(evidence)


def build_record(
    code: str, directory: dict[str, Any], detail: dict[str, Any] | None
) -> dict[str, object]:
    locality, country, scope, slug = META[code]
    directory_source = "maincubes-directory-current-20261106"
    site_source = f"maincubes-{code.lower()}-current-20261106"
    source_ids = [directory_source] if detail is None else [directory_source, site_source]
    url = DIRECTORY_URL if slug is None else f"{DIRECTORY_URL}{slug}/"
    fields = [
        "aggregation_role",
        "aliases",
        "capacity_scope",
        "country_code",
        "entities_json",
        "external_ids_json",
        "facility_id",
        "facility_type",
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
    ]
    if scope == "campus":
        fields.append("campus_id")
    normalize_exact = detail is not None and code != "BER02"
    if normalize_exact:
        fields.extend(["it_capacity_basis", "it_capacity_mw", "technical_area_m2"])
    field_sources, evidence = make_evidence(
        fields,
        source_ids,
        "current directory card and exact site page" if detail else "current directory card",
    )
    observations = [
        observation(
            field="directory_reported_capacity",
            value=(
                directory["reported_capacity_min_mw"]
                if directory["reported_capacity_min_mw"] == directory["reported_capacity_max_mw"]
                else [
                    directory["reported_capacity_min_mw"],
                    directory["reported_capacity_max_mw"],
                ]
            ),
            unit="MW",
            source_id=directory_source,
            locator=directory["locator"],
            boundary=(
                f"{code} directory capacity card; independently bound to IT capacity by "
                "the exact site page"
                if detail is not None
                else (
                    "FRA05 pipeline capacity card; no exact page or electrical boundary, "
                    "so IT/grid/facility capacity remain null"
                )
            ),
        )
    ]
    if code == "BER02" and detail is not None:
        observations.extend(
            [
                observation(
                    field="it_capacity_range",
                    value=[detail["it_capacity_min_mw"], detail["it_capacity_max_mw"]],
                    unit="MW",
                    source_id=site_source,
                    locator=detail["locator"],
                    boundary=(
                        "BER02 whole-campus design range depends on selected design; no "
                        "single scalar or building allocation is selected"
                    ),
                    kind="range",
                ),
                observation(
                    field="technical_area_range",
                    value=[
                        detail["technical_area_min_m2"],
                        detail["technical_area_max_m2"],
                    ],
                    unit="m2",
                    source_id=site_source,
                    locator=detail["locator"],
                    boundary=(
                        "BER02 whole-campus IT-area range depends on liquid- versus "
                        "air-cooled design; no scalar or building allocation is selected"
                    ),
                    kind="range",
                ),
            ]
        )
    capacity_scope = (
        f"{code} facility only; exact site-page IT capacity is a design maximum, not "
        "measured demand or grid capacity"
        if normalize_exact
        else (
            "BER02 whole-campus aggregate; design-dependent IT and technical-area ranges "
            "remain observations and the aggregate is excluded from all capacity sums"
            if code == "BER02"
            else (
                "FRA05 pipeline identity only; the unqualified directory capacity card is "
                "observation-only"
            )
        )
    )
    facility_id = stable_id("facility", ORG_NAME, code)
    row: dict[str, object] = {
        "aggregation_role": "aggregate" if scope == "campus" else "independent",
        "aliases": [code],
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
        "evidence_json": evidence,
        "external_ids_json": compact({"maincubes": code}),
        "facility_id": facility_id,
        "facility_type": "colocation",
        "field_sources_json": field_sources,
        "last_verified_at": RETRIEVED_AT,
        "locality": locality,
        "name": f"maincubes {code}",
        "notes": (
            "Certification, availability, renewable-energy, redundancy and rack-density "
            "claims remain observations or source context; no issuer-registry certification "
            "or deployment is inferred."
        ),
        "observations_json": compact(observations),
        "official_url": url,
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "source_backed",
        "record_id": stable_id("projects", ORG_NAME, code),
        "record_scope": scope,
        "source_urls": [DIRECTORY_URL] if detail is None else [DIRECTORY_URL, url],
        "sources": source_ids,
        "status": STATUS[directory["status_label"]],
        "status_as_of": AS_OF,
        "status_date_basis": (
            "Current exact site page and directory lifecycle label"
            if detail is not None
            else "Current directory pipeline label; no exact site page available"
        ),
        "updated_at": RETRIEVED_AT,
    }
    if scope == "campus":
        row["campus_id"] = stable_id("campus", ORG_NAME, code)
    if normalize_exact and detail is not None:
        row["it_capacity_basis"] = (
            "ultimate_planned" if row["status"] == "announced" else "design_maximum"
        )
        row["it_capacity_mw"] = detail["it_capacity_min_mw"]
        row["technical_area_m2"] = detail["technical_area_min_m2"]
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    directory, details = load_inputs(args.capture_dir)
    rows = [build_record(code, directory[code], details.get(code)) for code in META]
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed maincubes project records to {args.output}")


if __name__ == "__main__":
    main()
