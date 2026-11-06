"""Nepal DoED construction licences: bounded provenance, not operating status."""

import math
from html.parser import HTMLParser
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record

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


def new_record(entry: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Accept only explicitly reviewed licence identities; preserve unknown scope."""
    item, review = entry["inventory"], entry["review"]
    if (
        review.get("decision") != "reviewed_new_identity"
        or review.get("licence") != item["licence"]
        or not review.get("identity_basis")
    ):
        raise ValueError("Explicit licence identity review required")
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
                        period=now[:10],
                        source_id=SOURCE_ID,
                        locator=locator + "; Capacity (MW)",
                        boundary="Licensed project rating; not operating/installed power",
                        uncertainty="Source measurement vintage unprovided; retrieval date only",
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
        source_id=SOURCE_ID,
        now=now,
        locator=locator + "; original named columns in doed_inventory",
    )
