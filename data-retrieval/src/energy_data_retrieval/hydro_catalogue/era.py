"""Uganda ERA dated capacity cells and explicitly reviewed station insertions."""

import io
import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

import openpyxl
from openpyxl.utils import get_column_letter

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records

from .catalogue import stable_id, upsert_records, validate_catalogue
from .gppd import evidence_record
from .ons_new import name_key

SOURCE_ID = "uganda-era-capacity-202609"
REPORT_ID = "uganda-era-environment-2023"
SHEET = "Installed capacity since 2000"


def parse_inventory(data: bytes) -> list[dict[str, Any]]:
    """Read all three hydro sections; never replace blanks with zero or add totals."""
    book = openpyxl.load_workbook(io.BytesIO(data), read_only=True, data_only=True)
    sheet = book[SHEET]
    if tuple(c.value for c in sheet[9][3:30]) != tuple(range(2000, 2027)):
        raise ValueError("Unexpected ERA year columns")
    sections = {10: "Grid large hydro", 18: "Grid mini hydro", 80: "Off-grid mini hydro"}
    markers = {
        10: "Hydro electricity - Large Hydros",
        18: "Hydro-Electricity - Mini-hydros",
        80: "Hydro Electricity- Minihydros",
    }
    for index, name in markers.items():
        if sheet.cell(index, 3).value != name:
            raise ValueError("Unexpected hydro section boundary")
    if sheet.cell(47, 3).value != "Solar PV" or sheet.cell(85, 3).value != "Solar PV":
        raise ValueError("Unexpected end of hydro section")
    result = []
    seen = set()
    for index in [*range(11, 18), *range(19, 47), *range(81, 85)]:
        row = list(
            next(sheet.iter_rows(min_row=index, max_row=index, max_col=30, values_only=True))
        )
        name = row[2]
        if not isinstance(name, str) or not name.strip() or name in seen:
            raise ValueError("Missing or duplicate hydro name")
        seen.add(name)
        section = sections[10 if index < 18 else 18 if index < 80 else 80]
        observations = []
        for column, year in enumerate(range(2000, 2027), 4):
            value = row[column - 1]
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, (float, int))
                or not math.isfinite(value)
                or value < 0
            ):
                raise ValueError("Invalid generating capacity")
            observations.append(
                dict(
                    field="installed_capacity_mw",
                    value=value,
                    unit="MW",
                    kind="reported",
                    period=str(year) if year < 2026 else "2026 (as of September)",
                    boundary="ERA named station/year; not current operating capacity",
                    source_id=SOURCE_ID,
                    locator=f"{SHEET}!{get_column_letter(column)}{index}; {name}",
                    uncertainty="Not quantified; blank is unknown, zero remains reported zero",
                )
            )
        if all(o["value"] is None for o in observations):
            raise ValueError("Empty hydro statistics row")
        result.append(dict(row=index, source_name=name, section=section, observations=observations))
    book.close()
    return result


def new_record(entry: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Use frozen catalogue accessions, not row numbers masquerading as licences."""
    item, review = entry["inventory"], entry["review"]
    if (
        review.get("decision") != "reviewed_new_identity"
        or review.get("source_name") != item["source_name"]
        or not review.get("accession")
        or not review.get("identity_basis")
        or not review.get("report_locator")
    ):
        raise ValueError("Explicit regulator identity review required")
    row = evidence_record(
        dict(
            record_id=stable_id("projects", "reviewed-accession", review["accession"]),
            entity_type="projects",
            name=review["name"],
            aliases=review["aliases"],
            country_code="UGA",
            record_scope="plant",
            capacity_scope="ERA station or documented phase; overlap unresolved",
            aggregation_role="unresolved",
            status="unknown",
            status_as_of=now[:10],
            status_date_basis="Review date; dated inventory does not establish current operation",
            technology="unknown",
            external_ids_json="{}",
            observations_json=canonical_json(item["observations"]),
            extensions_json=canonical_json(
                dict(
                    era_inventory=item,
                    era_identity_review=review,
                    registry_id_status=(
                        "No official licence identifier supplied; accession is catalogue-owned"
                    ),
                )
            ),
        ),
        source_id=SOURCE_ID,
        now=now,
        locator=f"{SHEET}; row {item['row']}; per-cell locators retained",
    )
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    for field in ("name", "aliases", "extensions_json"):
        fs[field].append(REPORT_ID)
        ev[field]["locator"] += "; " + review["report_locator"]
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        sources=sorted(set(row["sources"] + [REPORT_ID])),
    )
    return row


def accept_new(
    root: Path,
    batch: dict[str, Any],
    output: Path,
    *,
    record_factory: Callable[..., dict[str, Any]] = new_record,
) -> int:
    """Preflight all accessions and names/aliases before writing; exact replay is a no-op."""
    existing = load_records(root)
    lookup = {r["record_id"]: r for r in existing}
    incoming = [record_factory(e, now=batch["reviewed_at"]) for e in batch["accepted"]]
    if len({r["record_id"] for r in incoming}) != len(incoming):
        raise ValueError("Duplicate incoming accession")
    new = []
    for row in incoming:
        if row["record_id"] in lookup:
            if lookup[row["record_id"]] != row:
                raise ValueError("Existing evidence differs; conflict review")
            continue
        names = {name_key(n) for n in [row["name"], *row["aliases"]]}
        for prior in existing + new:
            if prior["country_code"] == row["country_code"] and names & {
                name_key(n) for n in [prior["name"], *(prior.get("aliases") or [])]
            }:
                raise ValueError("Name collision requires identity review")
        new.append(row)
    combined, conflicts = upsert_records(existing, new, now=batch["reviewed_at"])
    if conflicts:
        raise ValueError("Insertion conflict")
    validate_catalogue(combined, json.loads((root / "sources.json").read_text()))
    if new:
        if output.exists():
            raise ValueError("Refuse to overwrite shard")
        output.write_text(
            "".join(canonical_json(r) + "\n" for r in sorted(new, key=lambda r: r["record_id"]))
        )
    return len(new)
