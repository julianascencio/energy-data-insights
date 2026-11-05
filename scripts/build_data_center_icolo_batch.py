"""Build the reviewed current iColo/Digital Realty East Africa facility batch."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import cast

from energy_data_retrieval.data_center_catalogue.catalogue import stable_id
from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_digital_realty_nbo2_release,
    parse_icolo_facility_page,
    parse_icolo_home_portfolio,
)

RETRIEVED_AT = "2026-11-05T23:23:00Z"
AS_OF = "2026-11-05"
ORG_NAME = "Digital Realty"
ORG_ID = stable_id("organization", ORG_NAME)
NAIROBI_CAMPUS_ID = stable_id("campus", ORG_NAME, "Nairobi campus")
NAIROBI_PARENT_ID = stable_id("projects", ORG_NAME, "Nairobi campus")
NBO2_URL = (
    "https://investor.digitalrealty.com/news-releases/news-release-details/"
    "digital-realty-strengthens-nairobi-east-africa-digital-gateway"
)

FACILITIES = {
    "MPM1": {
        "name": "Digital Realty MPM1 Maputo One",
        "country": "MOZ",
        "locality": "Maputo",
        "commissioning_date": "2023-02-07",
        "page": "https://www.icolo.io/location/mpm1/",
    },
    "MBA1": {
        "name": "Digital Realty MBA1 Mombasa One",
        "country": "KEN",
        "locality": "Mombasa",
        "page": "https://www.icolo.io/location/mba1/",
    },
    "MBA2": {
        "name": "Digital Realty MBA2 Mombasa Two",
        "country": "KEN",
        "locality": "Mombasa",
        "page": "https://www.icolo.io/location/mba2/",
    },
    "NBO1": {
        "name": "Digital Realty NBO1 Nairobi One",
        "country": "KEN",
        "locality": "Nairobi",
        "page": "https://www.icolo.io/location/nbo1/",
    },
    "NBO2": {
        "name": "Digital Realty NBO2 Nairobi Two",
        "country": "KEN",
        "locality": "Nairobi",
        "commissioning_date": "2026-09-07",
        "page": NBO2_URL,
    },
}

SPEC_ASSERTIONS = {
    "MPM1": ("TOTAL AREA", "5,000 sqm", "2 X 400 kVA (320kW) DCC", "Design 1.4"),
    "MBA1": ("TOTAL AREA", "2,400sqm", "4 X 800 kVA DCC", "Design 1.4"),
    "MBA2": ("TOTAL AREA", "4,460 sqm", "4 X 1,220kW Data Center Continuous duty", "Design 1.4"),
    "NBO1": ("TOTAL AREA", "4,046 sqm", "4 X 850 kVA/645kW Data Center", "Design 1.4"),
}

SOURCE_URLS = {
    "icolo-home-current-20261105": "https://www.icolo.io/",
    "icolo-mpm1-current-20261105": "https://www.icolo.io/location/mpm1/",
    "icolo-mpm1-spec-current-20261105": "https://www.icolo.io/wp-content/uploads/2023/03/MPM1_Technical-Specification-Sheet.pdf",
    "icolo-mpm1-opening-20230207": "https://www.icolo.io/news/icolo-announces-opening-of-mpm1-data-center-in-maputo/",
    "icolo-mba1-current-20261105": "https://www.icolo.io/location/mba1/",
    "icolo-mba1-spec-current-20261105": "https://www.icolo.io/wp-content/uploads/2022/02/MBA1_Technical-Specification-Sheet.pdf",
    "icolo-mba2-current-20261105": "https://www.icolo.io/location/mba2/",
    "icolo-mba2-spec-current-20261105": "https://www.icolo.io/wp-content/uploads/2023/03/MBA2_Technical-Specification-Sheet.pdf",
    "icolo-nbo1-current-20261105": "https://www.icolo.io/location/nbo1/",
    "icolo-nbo1-spec-current-20261105": "https://www.icolo.io/wp-content/uploads/2022/02/NBO1_Technical-Specification-Sheet.pdf",
    "icolo-kenya-solar-current-20261105": "https://www.icolo.io/news/contributing-positively-to-kenyas-renewable-energy-grid-with-solar/",
    "digital-realty-nbo2-opening-20260907": NBO2_URL,
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
    as_of: str = AS_OF,
    kind: str = "reported",
    **extra: object,
) -> dict[str, object]:
    return {
        "as_of": as_of,
        "boundary": boundary,
        "field": field,
        "kind": kind,
        "locator": locator,
        "source_id": source_id,
        "unit": unit,
        "value": value,
        **extra,
    }


def evidence(fields: list[str], sources: list[str], locator: str) -> tuple[str, str]:
    dates = {
        source: ("2026-09-07" if source == "digital-realty-nbo2-opening-20260907" else None)
        for source in sources
    }
    details = {
        field: {
            "confidence": "high",
            "locator": locator,
            "source_publication_dates": dates,
            **({"unit": "MW"} if field == "it_capacity_mw" else {}),
            **({"unit": "m2"} if field == "data_hall_area_m2" else {}),
        }
        for field in fields
    }
    return compact({field: sources for field in fields}), compact(details)


def load_inputs(
    capture_dir: Path,
) -> tuple[dict[str, dict[str, object]], dict[str, object], dict[str, object]]:
    pages: dict[str, dict[str, object]] = {}
    for code in ("MPM1", "MBA1", "MBA2", "NBO1"):
        pages[code] = parse_icolo_facility_page(
            (capture_dir / f"{code.lower()}.html").read_bytes(),
            source_url=str(FACILITIES[code]["page"]),
            expected_code=code,
        )["candidate"]
        spec_text = (capture_dir / f"{code.lower()}.txt").read_text(encoding="utf-8")
        if not all(fragment in spec_text for fragment in SPEC_ASSERTIONS[code]):
            raise ValueError(f"Changed {code} technical specification sheet shape")
    home = parse_icolo_home_portfolio(
        (capture_dir / "home.html").read_bytes(), source_url="https://www.icolo.io/"
    )
    nbo2 = parse_digital_realty_nbo2_release(
        (capture_dir / "nbo2-release.html").read_bytes(), source_url=NBO2_URL
    )["candidate"]
    return pages, {row["external_id"]: row for row in home["candidates"]}, nbo2


def build_facility(
    code: str,
    pages: dict[str, dict[str, object]],
    home: dict[str, object],
    nbo2: dict[str, object],
) -> dict[str, object]:
    meta = FACILITIES[code]
    page_source = f"icolo-{code.lower()}-current-20261105"
    sources = [page_source] if code != "NBO2" else ["digital-realty-nbo2-opening-20260907"]
    observations: list[dict[str, object]] = []
    data_hall_area: float | None = None
    it_capacity: float | None = None
    commissioning_date = meta.get("commissioning_date")

    if code != "NBO2":
        candidate = pages[code]
        customer_space = candidate["customer_space_m2"]
        data_hall_area = float(cast(float, customer_space)) if customer_space is not None else None
        rack_count = candidate["rack_capacity"]
        if rack_count is not None:
            observations.append(
                observation(
                    field="rack_capacity_design",
                    value=rack_count,
                    unit="racks",
                    source_id=page_source,
                    locator="current facility page public metric cards",
                    boundary=f"{code} design rack capacity; not installed or occupied racks",
                )
            )
        if candidate["campus_area_m2"] is not None:
            observations.append(
                observation(
                    field="reported_campus_area",
                    value=candidate["campus_area_m2"],
                    unit="m2",
                    source_id=page_source,
                    locator="current facility page public metric cards",
                    boundary=f"{code} labelled campus area; not normalized data-hall area",
                )
            )
        observations.append(
            observation(
                field="design_pue",
                value=1.4,
                unit="ratio",
                source_id=f"icolo-{code.lower()}-spec-current-20261105",
                locator="technical specification sheet / Efficiency",
                boundary=f"{code} design PUE; no measured period disclosed",
                kind="design",
                measurement_period=None,
            )
        )
        sources.append(f"icolo-{code.lower()}-spec-current-20261105")
        if candidate["lifecycle_marker"] is not None:
            observations.append(
                observation(
                    field="lifecycle_marker",
                    value=candidate["lifecycle_marker"],
                    unit=None,
                    source_id=page_source,
                    locator="current facility page introduction",
                    boundary=f"{code} source precision retained; no exact date inferred",
                )
            )

    if code in home:
        home_source = "icolo-home-current-20261105"
        sources.append(home_source)
        home_candidate = cast(dict[str, object], home[code])
        it_capacity = float(cast(float, home_candidate["it_power_mw"]))
        observations.append(
            observation(
                field="reported_total_area",
                value=home_candidate["total_area_m2"],
                unit="m2",
                source_id=home_source,
                locator=f"home page campus card / {code}",
                boundary=(
                    f"{code} total-area card; facility/campus boundary differs from other "
                    "dated official pages and is not normalized"
                ),
            )
        )
    if code == "NBO1":
        sources.append("icolo-kenya-solar-current-20261105")
        it_capacity = 0.825
        observations.append(
            observation(
                field="customer_it_load_capability",
                value=825,
                unit="kW",
                source_id="icolo-kenya-solar-current-20261105",
                locator="solar systems paragraph",
                boundary="NBO1 customer-power capability; not measured demand",
            )
        )
    if code == "MBA1":
        sources.append("icolo-kenya-solar-current-20261105")
        observations.append(
            observation(
                field="historical_customer_it_load_capability",
                value=675,
                unit="kW",
                source_id="icolo-kenya-solar-current-20261105",
                locator="solar systems paragraph",
                boundary=(
                    "MBA1 earlier customer-power capability; superseded for normalization "
                    "by current 0.9 MW home card"
                ),
            )
        )
    if code == "MPM1":
        sources.append("icolo-mpm1-opening-20230207")
        observations.extend(
            [
                observation(
                    field="opening_phase_rack_capacity",
                    value=80,
                    unit="racks",
                    source_id="icolo-mpm1-opening-20230207",
                    locator="opening release facility description",
                    boundary="MPM1 first development phase; approximate source qualifier retained",
                    as_of="2023-02-07",
                    qualifier="approximately",
                ),
                observation(
                    field="reported_campus_area",
                    value=9500,
                    unit="m2",
                    source_id="icolo-mpm1-opening-20230207",
                    locator="opening release facility description",
                    boundary=(
                        "MPM1 campus area; conflicts with current home-card 5,000 m2 total "
                        "area and is not normalized"
                    ),
                    as_of="2023-02-07",
                ),
            ]
        )
    if code == "NBO2":
        observations.append(
            observation(
                field="reported_capacity",
                value=nbo2["reported_capacity_mw"],
                unit="MW",
                source_id="digital-realty-nbo2-opening-20260907",
                locator=str(nbo2["locator"]),
                boundary=(
                    "NBO2 opening claim; electrical boundary is not stated, so IT/facility/"
                    "grid capacity remain null"
                ),
                as_of="2026-09-07",
                kind="unspecified",
            )
        )

    sources = list(dict.fromkeys(sources))
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
    if data_hall_area is not None:
        fields.append("data_hall_area_m2")
    if it_capacity is not None:
        fields.extend(["it_capacity_basis", "it_capacity_mw"])
    if commissioning_date is not None:
        fields.append("commissioning_date")
    if code in {"NBO1", "NBO2"}:
        fields.extend(["campus_id", "parent_record_id"])
    locator = "current facility page, current portfolio card and dated issuer release as applicable"
    field_sources, evidence_json = evidence(fields, sources, locator)
    row: dict[str, object] = {
        "aliases": [f"iColo {code}"],
        "aggregation_role": "child" if code in {"NBO1", "NBO2"} else "independent",
        "capacity_scope": (
            f"{code} facility only; normalized IT values are stated design/customer-power "
            "capabilities; "
            "not measured demand"
            if it_capacity is not None
            else f"{code} facility only; unclassified reported capacity is observation-only"
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
        "external_ids_json": compact({"icolo": code}),
        "facility_id": stable_id("facility", ORG_NAME, code),
        "facility_type": "colocation",
        "field_sources_json": field_sources,
        "last_verified_at": RETRIEVED_AT,
        "locality": meta["locality"],
        "name": meta["name"],
        "observations_json": compact(observations),
        "official_url": meta["page"],
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "source_backed" if code != "NBO2" else "needs_review",
        "record_id": stable_id("projects", ORG_NAME, code),
        "record_scope": "facility",
        "source_urls": sorted({SOURCE_URLS[source] for source in sources}),
        "sources": sources,
        "status": "operational",
        "status_as_of": "2026-09-07" if code == "NBO2" else AS_OF,
        "status_date_basis": (
            "dated Digital Realty opening release"
            if code == "NBO2"
            else "current operator page; dated lifecycle marker retained where available"
        ),
        "updated_at": RETRIEVED_AT,
    }
    if data_hall_area is not None:
        row["data_hall_area_m2"] = data_hall_area
    if it_capacity is not None:
        row["it_capacity_basis"] = "design_maximum"
        row["it_capacity_mw"] = it_capacity
    if commissioning_date is not None:
        row["commissioning_date"] = commissioning_date
    if code in {"NBO1", "NBO2"}:
        row["campus_id"] = NAIROBI_CAMPUS_ID
        row["parent_record_id"] = NAIROBI_PARENT_ID
    return row


def build_campus() -> dict[str, object]:
    source = "digital-realty-nbo2-opening-20260907"
    fields = [
        "aliases",
        "aggregation_role",
        "campus_id",
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
    field_sources, evidence_json = evidence(
        fields, [source], "NBO2 opening paragraph and Built alongside Nairobi One paragraph"
    )
    return {
        "aliases": ["iColo Nairobi campus"],
        "aggregation_role": "aggregate",
        "campus_id": NAIROBI_CAMPUS_ID,
        "capacity_scope": (
            "Nairobi campus aggregate containing NBO1 and NBO2; always excluded from "
            "capacity sums; no campus capacity is normalized because the 6.4 MW NBO2 claim "
            "has an unstated electrical boundary"
        ),
        "country_code": "KEN",
        "created_at": RETRIEVED_AT,
        "entities_json": compact(
            [
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "owner"},
                {"name": ORG_NAME, "organization_id": ORG_ID, "role": "operator"},
            ]
        ),
        "entity_type": "projects",
        "evidence_json": evidence_json,
        "external_ids_json": compact({"digital_realty": "Nairobi campus"}),
        "facility_id": stable_id("facility", ORG_NAME, "Nairobi campus"),
        "facility_type": "colocation",
        "field_sources_json": field_sources,
        "last_verified_at": RETRIEVED_AT,
        "locality": "Nairobi",
        "name": "Digital Realty Nairobi campus",
        "observations_json": compact(
            [
                observation(
                    field="nbo2_reported_capacity_addition",
                    value=6.4,
                    unit="MW",
                    source_id=source,
                    locator="release subheading and opening paragraph",
                    boundary=(
                        "NBO2 addition to Nairobi campus; electrical boundary unstated and "
                        "not normalized"
                    ),
                    as_of="2026-09-07",
                    kind="unspecified",
                )
            ]
        ),
        "official_url": NBO2_URL,
        "operator_names": [ORG_NAME],
        "owner_names": [ORG_NAME],
        "quality_status": "needs_review",
        "record_id": NAIROBI_PARENT_ID,
        "record_scope": "campus",
        "source_urls": [NBO2_URL],
        "sources": [source],
        "status": "operational",
        "status_as_of": "2026-09-07",
        "status_date_basis": "dated NBO2 opening release explicitly identifying the Nairobi campus",
        "updated_at": RETRIEVED_AT,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture_dir", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    pages, home, nbo2 = load_inputs(args.capture_dir)
    rows = [build_facility(code, pages, home, nbo2) for code in FACILITIES]
    rows.append(build_campus())
    args.output.write_text("".join(f"{compact(row)}\n" for row in rows), encoding="utf-8")
    print(f"Wrote {len(rows)} reviewed iColo/Digital Realty project records to {args.output}")


if __name__ == "__main__":
    main()
