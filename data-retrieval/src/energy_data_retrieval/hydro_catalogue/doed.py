"""Nepal DoED construction licences: bounded provenance, not operating status."""

import math
import re
from collections import Counter
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record
from .ons_new import name_key

SOURCE_ID = "doed-construction-over1-20261106"


class _Table(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.row: list[str] = []
        self.parts: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag == "tr":
            self.row = []
        elif tag in {"td", "th"}:
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.parts is not None:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.parts is not None:
            self.row.append(" ".join(" ".join(self.parts).split()))
            self.parts = None
        elif tag == "tr" and self.row:
            self.rows.append(self.row)


def parse_inventory(html: str) -> list[dict[str, Any]]:
    """Preserve four bounding coordinates and unconverted licence date strings."""
    parser = _Table()
    parser.feed(html)
    expected = [
        "S No",
        "Project",
        "Capacity (MW)",
        "River",
        "Lic No",
        "Isuue Date",
        "Validity",
        "Promoter",
        "Address",
        "Latitiude N",
        "Longitude E",
        "VDC/District",
    ]
    if not parser.rows or parser.rows[0] != expected:
        raise ValueError("Unexpected licence table headers")
    result = []
    for index, cells in enumerate(parser.rows[1:], 1):
        if len(cells) != 14 or cells[0] != str(index) or not cells[1] or not cells[4]:
            raise ValueError("Malformed licence identity/row")
        mw = float(cells[2])
        if not math.isfinite(mw) or mw <= 0:
            raise ValueError("Invalid licensed capacity")
        result.append(
            dict(
                row=index,
                name=cells[1],
                capacity_mw=mw,
                river=cells[3],
                licence=cells[4],
                issue_date_raw=cells[5],
                validity_raw=cells[6],
                promoter=cells[7],
                bounds_raw=cells[9:13],
                district_raw=cells[13],
            )
        )
    if not result or len({r["licence"] for r in result}) != len(result):
        raise ValueError("Empty or duplicate licence inventory")
    return result


def parse_updated_date(html: str) -> str:
    """Require one explicit page update date; do not convert licence calendar strings."""
    matches = sorted(set(re.findall(r"Updated on\s*-\s*([A-Za-z]+ \d{1,2}, \d{4})", html)))
    if len(matches) != 1:
        raise ValueError("Require one explicit source update date")
    return datetime.strptime(matches[0], "%B %d, %Y").date().isoformat()


def validate_reviewed_batch(batch: dict[str, Any]) -> None:
    """Require exhaustive, disjoint decisions within a frozen source-row partition."""
    inventory, partition = batch["parsed_inventory"], batch["partition"]
    if [r["row"] for r in inventory] != list(range(1, len(inventory) + 1)):
        raise ValueError("Nonsequential frozen inventory")
    if len({r["licence"] for r in inventory}) != len(inventory):
        raise ValueError("Duplicate frozen licence identity")
    first, last = partition["first_row"], partition["last_row"]
    if not 1 <= first <= last <= len(inventory) or partition["total_source_rows"] != len(inventory):
        raise ValueError("Invalid source partition")
    expected_next = last + 1 if last < len(inventory) else None
    if partition["next_row"] != expected_next:
        raise ValueError("Invalid continuation cursor")
    decisions = batch["accepted"] + batch["held"]
    if sorted(e["inventory"]["row"] for e in decisions) != list(range(first, last + 1)):
        raise ValueError("Partition decisions must be exhaustive and disjoint")
    for entry in decisions:
        item = entry["inventory"]
        if item != inventory[item["row"] - 1]:
            raise ValueError("Reviewed evidence differs from frozen source")
    counts = Counter(name_key(r["name"]) for r in inventory)
    if any(counts[name_key(e["inventory"]["name"])] > 1 for e in batch["accepted"]):
        raise ValueError("Duplicate source name requires separate identity review")
    if batch["new"] != len(batch["accepted"]):
        raise ValueError("Accepted count differs from decisions")


def new_record(
    entry: dict[str, Any], *, now: str, source_id: str = SOURCE_ID, source_as_of: str | None = None
) -> dict[str, Any]:
    """Accept only explicitly reviewed licence identities; preserve unknown scope."""
    item, review = entry["inventory"], entry["review"]
    if (
        review.get("decision") != "reviewed_new_identity"
        or review.get("licence") != item["licence"]
        or not review.get("identity_basis")
    ):
        raise ValueError("Explicit licence identity review required")
    if source_as_of and date.fromisoformat(source_as_of) > date.fromisoformat(now[:10]):
        raise ValueError("Source update date after retrieval")
    locator = f"Construction License Hydro >1 MW; S No {item['row']}; Lic No {item['licence']}"
    return evidence_record(
        dict(
            record_id=stable_id("projects", "Nepal-DoED-construction-hydro-over1", item["licence"]),
            entity_type="projects",
            name=item["name"],
            aliases=[],
            country_code="NPL",
            river=item["river"] or None,
            developer_names=[item["promoter"]] if item["promoter"] else [],
            record_scope="plant",
            capacity_scope="Licensed project; overlap unresolved",
            aggregation_role="unresolved",
            status="unknown",
            status_as_of=now[:10],
            status_date_basis=(
                "Retrieval date; licence table membership does not verify current lifecycle"
            ),
            technology="unknown",
            external_ids_json=canonical_json(
                {"Nepal-DoED-construction-hydro-over1": item["licence"]}
            ),
            observations_json=canonical_json(
                [
                    dict(
                        field="licensed_capacity_mw",
                        value=item["capacity_mw"],
                        unit="MW",
                        kind="reported",
                        period=source_as_of or now[:10],
                        source_id=source_id,
                        locator=locator + "; Capacity (MW)",
                        boundary="Licensed project rating; not operating/installed power",
                        uncertainty=(
                            "Page update date; individual licence measurement vintage unknown"
                            if source_as_of
                            else "Source measurement vintage unprovided; retrieval date only"
                        ),
                    )
                ]
            ),
            extensions_json=canonical_json(
                dict(
                    doed_inventory=item,
                    doed_identity_review=review,
                    date_basis=(
                        "Source strings retained; calendar and Gregorian conversion unverified"
                    ),
                    location_basis=(
                        "Four source coordinate bounds retained verbatim; not a plant point"
                    ),
                    promoter_basis="DoED promoter field, not verified owner/operator",
                )
            ),
        ),
        source_id=source_id,
        now=now,
        locator=locator + "; original named columns in doed_inventory",
    )
