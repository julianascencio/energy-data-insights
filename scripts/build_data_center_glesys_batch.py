"""Build the reviewed current GleSYS five-location owned-site batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_glesys_finland_integration,
    parse_glesys_owned_portfolio,
    parse_glesys_site_page,
)

RETRIEVED_AT = "2026-11-06T00:52:00Z"
AS_OF = "2026-11-06"
ORG_NAME = "Glesys"
ORG_ID = stable_id("organization", ORG_NAME)
PORTFOLIO_SOURCE = "glesys-owned-data-centers-current-20261106"
PORTFOLIO_URL = "https://glesys.com/locations/our-data-centers/"
INTEGRATION_SOURCE = "glesys-finland-integration-20260203"
INTEGRATION_URL = (
    "https://glesys.com/blog/glesys-strengthens-its-nordic-footprint-through-full-"
    "integration-of-private-cloud-operations-in-finland/"
)

SITES: dict[str, dict[str, str]] = {
    "falkenberg": {
        "name": "Glesys Falkenberg",
        "country": "SWE",
        "locality": "Falkenberg",
        "scope": "facility",
        "filename": "falkenberg.html",
        "url_path": "falkenberg",
    },
    "oulu": {
        "name": "Glesys Oulu campus",
        "country": "FIN",
        "locality": "Oulu",
        "scope": "campus",
        "filename": "oulu.html",
        "url_path": "oulu",
    },
    "pori": {
        "name": "Glesys Pori",
        "country": "FIN",
        "locality": "Ulvila",
        "scope": "facility",
        "filename": "pori.html",
        "url_path": "pori-data-center",
    },
    "stockholm": {
        "name": "Glesys Stockholm",
        "country": "SWE",
        "locality": "Stockholm",
        "scope": "facility",
        "filename": "stockholm.html",
        "url_path": "stockholm",
    },
    "tampere": {
        "name": "Glesys Tampere",
        "country": "FIN",
        "locality": "Tampere",
        "scope": "facility",
        "filename": "tampere.html",
        "url_path": "tampere",
    },
}


def compact(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def observation(
    *, field: str, value: object, unit: str | None, source_id: str, boundary: str, **extra: object
) -> dict[str, object]:
    return {
        "as_of": AS_OF,
        "boundary": boundary,
        "field": field,
        "kind": "reported",
        "locator": "current owned-site page / public metric cards and narrative",
        "source_id": source_id,
        "unit": unit,
        "value": value,
        **extra,
    }


def evidence(fields: list[str], sources: list[str]) -> tuple[str, str]:
    details = {
        field: {
            "confidence": "high",
            "locator": "current owned-site directory and exact site page",
            "source_publication_dates": {
                source: "2026-02-03" if source == INTEGRATION_SOURCE else None for source in sources
            },
        }
        for field in fields
    }
    return compact({field: sources for field in fields}), compact(details)


def load_inputs(capture_dir: Path) -> dict[str, dict[str, Any]]:
    portfolio = parse_glesys_owned_portfolio(
        (capture_dir / "directory.html").read_bytes(), source_url=PORTFOLIO_URL
    )
    parsed = {row["external_id"]: row for row in portfolio["candidates"]}
    if set(parsed) != set(SITES):
        raise ValueError("Changed GleSYS owned-site inventory")
    for slug, meta in SITES.items():
        if parsed[slug]["record_scope"] != meta["scope"]:
            raise ValueError("Changed GleSYS reviewed scope boundary")
    integration = parse_glesys_finland_integration(
        (capture_dir / "integration.html").read_bytes(), source_url=INTEGRATION_URL
    )
    if {row["external_id"] for row in integration["candidates"]} != {"pori", "tampere"}:
        raise ValueError("Changed GleSYS Finland ownership transition")
    candidates: dict[str, dict[str, Any]] = {}
    for slug, meta in SITES.items():
        url = f"https://glesys.com/locations/our-data-centers/{meta['url_path']}/"
        candidates[slug] = parse_glesys_site_page(
            (capture_dir / meta["filename"]).read_bytes(),
            source_url=url,
            expected_site=slug.title(),
        )["candidate"]
    return candidates


def build_record(slug: str, candidate: dict[str, Any]) -> dict[str, object]:
    meta = SITES[slug]
    site_source = f"glesys-{slug}-current-20261106"
    site_url = f"https://glesys.com/locations/our-data-centers/{meta['url_path']}/"
    sources = [PORTFOLIO_SOURCE, site_source]
    if slug in {"pori", "tampere"}:
        sources.append(INTEGRATION_SOURCE)
    observations: list[dict[str, object]] = []

    if slug == "falkenberg":
        observations.extend(
            [
                observation(
                    field="conflicting_reported_power_capacity",
                    value=[
                        candidate["reported_power_mw"],
                        candidate["conflicting_reported_power_mw"],
                    ],
                    unit="MW",
                    source_id=site_source,
                    boundary=(
                        "Metric card says 10 MW while the FAQ says total capacity 5 MW; "
                        "neither identifies IT, grid or facility demand"
                    ),
                ),
                observation(
                    field="conflicting_reported_pue",
                    value=[candidate["pue"], candidate["conflicting_pue"]],
                    unit="ratio",
                    source_id=site_source,
                    boundary=(
                        "Metric card/narrative says 1.1 while the FAQ says 1.2; period unstated"
                    ),
                    measurement_period=None,
                ),
                observation(
                    field="conflicting_maximum_rack_density",
                    value=[candidate["rack_density_kw"], candidate["conflicting_rack_density_kw"]],
                    unit="kW/rack",
                    source_id=site_source,
                    boundary="Metric card says 44 while narrative says 43; no scalar selected",
                ),
            ]
        )
    else:
        if candidate.get("pue") is not None:
            observations.append(
                observation(
                    field="reported_pue",
                    value=candidate["pue"],
                    unit="ratio",
                    source_id=site_source,
                    boundary=f"{slug} operator metric; measurement period unstated",
                    measurement_period=None,
                )
            )
        if candidate.get("rack_density_kw") is not None:
            observations.append(
                observation(
                    field="maximum_rack_density",
                    value=candidate["rack_density_kw"],
                    unit="kW/rack",
                    source_id=site_source,
                    boundary=f"{slug} source-labelled maximum/support value; not equipment input",
                )
            )
        if candidate.get("reported_power_mw") is not None:
            label = "available power" if slug == "tampere" else "power capacity"
            observations.append(
                observation(
                    field="reported_unclassified_power_capacity",
                    value=candidate["reported_power_mw"],
                    unit="MW",
                    source_id=site_source,
                    boundary=(
                        f"{slug} {label}; source does not identify IT, grid or total facility "
                        "demand, so all normalized capacity scalars remain null"
                    ),
                )
            )
    if candidate.get("renewable_electricity_pct") is not None:
        observations.append(
            observation(
                field="reported_renewable_electricity_share",
                value=candidate["renewable_electricity_pct"],
                unit="percent",
                source_id=site_source,
                boundary=(
                    f"{slug} operator electricity-sourcing statement; not a grid-emissions factor"
                ),
            )
        )
    if slug == "oulu":
        observations.extend(
            [
                observation(
                    field="reported_data_center_count",
                    value=int(candidate["data_center_count"]),
                    unit="data centers",
                    source_id=site_source,
                    boundary=(
                        "Oulu aggregate: three established sites plus Campus Oulu; "
                        "no child identities created"
                    ),
                ),
                observation(
                    field="established_site_pue_lower_bound",
                    value=candidate["established_pue_lower_bound"],
                    unit="ratio",
                    source_id=site_source,
                    boundary=(
                        "Three established Oulu sites only; distinct from 1.2 lowest Oulu metric"
                    ),
                    measurement_period=None,
                ),
                observation(
                    field="established_site_maximum_rack_density",
                    value=candidate["established_rack_density_kw"],
                    unit="kW/rack",
                    source_id=site_source,
                    boundary="Three established Oulu sites; distinct from Campus Oulu 250 kW/rack",
                ),
                observation(
                    field="campus_oulu_planned_capacity",
                    value=candidate["campus_oulu_planned_capacity_mw"],
                    unit="MW",
                    source_id=site_source,
                    boundary=(
                        "Campus Oulu phased planned capacity; electrical boundary unstated and "
                        "not normalized as current IT/grid/facility capacity"
                    ),
                ),
            ]
        )
    if slug == "stockholm":
        observations.append(
            observation(
                field="reported_colocation_space",
                value=candidate["reported_colocation_space_m2"],
                unit="m2",
                source_id=site_source,
                boundary="Premium colocation space; not assumed to equal net data-hall area",
            )
        )
    if slug in {"pori", "tampere"}:
        observations.append(
            observation(
                field="ownership_transition",
                value="completed integration from Verne",
                unit=None,
                source_id=INTEGRATION_SOURCE,
                boundary=(
                    f"{slug} current GleSYS operation confirmed by 2026 integration announcement"
                ),
                publication_date="2026-02-03",
            )
        )

    aggregate = meta["scope"] == "campus"
    fields = [
        "aliases",
        "aggregation_role",
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
    if aggregate:
        fields.append("campus_id")
    field_sources, evidence_json = evidence(fields, sources)
    row: dict[str, object] = {
        "aliases": [meta["locality"]],
        "aggregation_role": "aggregate" if aggregate else "independent",
        "capacity_scope": (
            "Oulu four-site aggregate; always excluded from capacity totals; exact child records "
            "remain unresolved"
            if aggregate
            else (
                f"{meta['locality']} independently identified facility; unclassified operator "
                "power claims are excluded from normalized capacity totals"
            )
        ),
        "country_code": meta["country"],
        "created_at": RETRIEVED_AT,
        "entities_json": compact(
            [
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "owner"},
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "operator"},
            ]
        ),
        "entity_type": "projects",
        "evidence_json": evidence_json,
        "external_ids_json": compact({"glesys": slug}),
        "facility_id": stable_id("facility", ORG_NAME, slug),
        "facility_type": "colocation",
        "field_sources_json": field_sources,
        "last_verified_at": RETRIEVED_AT,
        "locality": meta["locality"],
        "name": meta["name"],
        "observations_json": compact(observations),
        "official_url": site_url,
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "needs_review" if slug in {"falkenberg", "oulu"} else "source_backed",
        "record_id": stable_id("projects", ORG_NAME, slug),
        "record_scope": meta["scope"],
        "source_urls": sorted(
            [PORTFOLIO_URL, site_url] + ([INTEGRATION_URL] if slug in {"pori", "tampere"} else [])
        ),
        "sources": sources,
        "status": "operational",
        "status_as_of": AS_OF,
        "status_date_basis": (
            "current owned-site directory plus completed 2026 integration announcement"
            if slug in {"pori", "tampere"}
            else "current owned-site directory"
        ),
        "updated_at": RETRIEVED_AT,
    }
    if aggregate:
        row["campus_id"] = stable_id("campus", ORG_NAME, slug)
    return row


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    candidates = load_inputs(args.capture_dir)
    rows = [build_record(slug, candidates[slug]) for slug in SITES]
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed GleSYS project records to {args.output}")


if __name__ == "__main__":
    main()
