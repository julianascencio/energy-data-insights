"""Review-only staging of NEPRA's corporate distributed-generation directory.

The directory mixes solar, thermal, portfolio and licence-transfer observations.
Nothing returned here is a canonical project, an ownership decision, or evidence
that a licensed facility operates today. Reuse rights require separate review.
"""

from __future__ import annotations

import re
from collections import Counter
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit

from .sam import verify_sha256


def _space(value: str) -> str:
    return " ".join(value.split())


class _Directory(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[dict[str, Any]] = []
        self.current: dict[str, Any] | None = None
        self.heading = False
        self.in_table = False
        self.cell: list[str] | None = None
        self.cells: list[str] = []
        self.links: list[str] = []

    def _finish_cell(self) -> None:
        if self.cell is not None:
            self.cells.append(_space("".join(self.cell)))
            self.cell = None

    def _finish_row(self) -> None:
        self._finish_cell()
        if self.cells and self.current is not None:
            self.current["rows"].append((self.cells, self.links))
        self.cells, self.links = [], []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h6":
            if self.heading or self.in_table:
                raise ValueError("NEPRA heading/table structure changed")
            self.current = {"heading": "", "rows": [], "tables": 0}
            self.blocks.append(self.current)
            self.heading = True
        elif tag == "table" and self.current is not None:
            if self.in_table:
                raise ValueError("Nested NEPRA tables require review")
            self.in_table = True
            self.current["tables"] += 1
        elif tag == "tr" and self.in_table:
            self._finish_row()
        elif tag in {"td", "th"} and self.in_table:
            self._finish_cell()
            self.cell = []
        elif tag == "a" and self.in_table:
            href = dict(attrs).get("href")
            if href:
                self.links.append(href)
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self.heading and self.current is not None:
            self.current["heading"] += data
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "h6":
            self.heading = False
        elif tag in {"td", "th"} and self.cell is not None:
            self._finish_cell()
        elif tag == "tr" and self.in_table and self.current is not None:
            self._finish_row()
        elif tag == "table":
            self._finish_row()
            self.in_table = False


def _official_url(value: str, source_url: str) -> str | None:
    url = urljoin(source_url, value)
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in {"nepra.org.pk", "www.nepra.org.pk"}:
        return None
    return url


def stage_nepra_review(content: bytes, *, sha256: str, source_url: str) -> dict[str, Any]:
    """Pin bytes and stage corporate solar observations without accepting assets.

    Capacity spelling/units, licence numbers and transfer links remain native.
    Same-company licences are never merged; duplicate licence numbers are flagged.
    An explicit PV description is distinguished from generic ``Solar``. Unknown
    non-corporate headings are omitted, rather than exporting possible individuals.
    """
    verify_sha256(content, sha256)
    if len(content) > 2_000_000 or _official_url(source_url, source_url) != source_url:
        raise ValueError("NEPRA source URL or size requires review")
    parser = _Directory()
    parser.feed(content.decode("utf-8-sig"))
    parser.close()
    if parser.heading or parser.in_table or parser.cell is not None:
        raise ValueError("Incomplete NEPRA directory structure")
    candidates: list[dict[str, Any]] = []
    excluded: Counter[str] = Counter()
    for index, block in enumerate(parser.blocks):
        name = _space(block["heading"])
        if not re.search(r"\b(?:limited|ltd|company|corporation)\b", name, re.I):
            excluded["noncorporate_heading_omitted"] += 1
            continue
        if block["tables"] != 1:
            raise ValueError("NEPRA corporate block must have one reviewed table")
        fields: dict[str, str] = {}
        documents = []
        for cells, links in block["rows"]:
            if len(cells) != 2:
                raise ValueError("NEPRA row columns changed")
            label, value = cells
            if label in {"Plant Detail", "Plant Type", "Gross Capacity", "Licence No."}:
                if label in fields:
                    raise ValueError("Duplicate NEPRA native field")
                fields[label] = value
            for href in links:
                url = _official_url(href, source_url)
                if url and re.search(
                    r"licen[cs]e|determination|decision|modification", label, re.I
                ):
                    documents.append({"label": label, "url": url})
        if not {"Plant Type", "Gross Capacity", "Licence No."} <= fields.keys():
            raise ValueError("NEPRA required native columns missing")
        detail = fields.get("Plant Detail", "")
        solar = "solar" in fields["Plant Type"].casefold()
        pv = bool(
            re.search(r"\bpv\b|photo\s*voltaic", detail, re.I)
            or re.search(r"(?:mono|poly)\s*crystalline.*solar\s+modules", detail, re.I)
        )
        if not solar and not pv:
            excluded["non_solar_block"] += 1
            continue
        reasons = [
            "review_only_not_canonical",
            "reuse_rights_unassessed",
            "project_or_portfolio_scope_unreviewed",
            "licence_not_current_operation_or_ownership",
            "gross_capacity_not_assigned_ac_or_dc",
        ]
        if not pv:
            reasons.append("generic_solar_not_explicit_pv")
        if pv and not solar:
            reasons.append("non_solar_plant_type_requires_review")
        if not re.fullmatch(r"\d+(?:\.\d+)?\s*(?:MWp|kWp|MW|kW)", fields["Gross Capacity"]):
            reasons.append("unparsed_capacity_notation")
        if not re.fullmatch(r"SGC/\d+/\d{4}", fields["Licence No."]):
            reasons.append("licence_notation_requires_review")
        candidates.append(
            {
                "candidate_locator": f"h6/table block {index + 1}",
                "source_sha256": sha256,
                "source_url": source_url,
                "corporate_heading": name,
                "native_fields": fields,
                "explicit_pv_description": pv,
                "documents": documents,
                "review_reasons": reasons,
            }
        )
    if not parser.blocks or not any(block["tables"] for block in parser.blocks):
        raise ValueError("No NEPRA directory headings; access wall or schema change")
    numbers = Counter(re.sub(r"\s+", "", c["native_fields"]["Licence No."]) for c in candidates)
    for candidate in candidates:
        number = re.sub(r"\s+", "", candidate["native_fields"]["Licence No."])
        if numbers[number] > 1:
            candidate["review_reasons"].append("duplicate_source_licence_number")
    return {
        "accepted_canonical_records": 0,
        "directory_blocks_seen": len(parser.blocks),
        "candidates": candidates,
        "excluded_counts": dict(excluded),
    }
