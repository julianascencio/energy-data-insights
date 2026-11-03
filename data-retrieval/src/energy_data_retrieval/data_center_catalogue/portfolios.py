"""Offline, allowlisted parsers for public operator portfolio captures.

These parsers stage candidates, never infer operating status, IT MW or campus
boundaries. Callers review candidates before canonical publication. No contact,
access, credential, security or internal network details are extracted.
"""

from __future__ import annotations

import hashlib
import json
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit


class _Portfolio(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.locations: list[list[dict[str, Any]]] = []
        self.rows: list[dict[str, str]] = []
        self.depth = 0
        self.parts: list[str] = []
        self.href = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if "data-locations" in values:
            self.locations.append(json.loads(values["data-locations"] or "null"))
        if tag == "div":
            if self.depth:
                self.depth += 1
            elif "dc-row" in (values.get("class") or "").split():
                self.depth = 1
                self.parts = []
                self.href = ""
        if self.depth and tag == "a":
            self.href = values.get("href") or ""

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "div" and self.depth:
            self.depth -= 1
            if not self.depth:
                self.rows.append(
                    {"text": " ".join(" ".join(self.parts).split()), "href": self.href}
                )


def parse_portfolio(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Return all staged entries and byte checksum; reject changed source shape."""
    host = urlsplit(source_url).hostname
    if host not in {"odatadc.com", "www.nextdc.com"}:
        raise ValueError("Unsupported official portfolio URL")
    parser = _Portfolio()
    parser.feed(content.decode("utf-8-sig"))
    candidates = []
    if host == "odatadc.com":
        if len(parser.locations) != 1 or not isinstance(parser.locations[0], list):
            raise ValueError("Expected exactly one ODATA location inventory")
        for raw in parser.locations[0]:
            if not all(raw.get(k) for k in ("id", "title", "address", "coordinates")):
                raise ValueError("Incomplete ODATA location identity")
            coordinates = [float(v.strip()) for v in raw["coordinates"].split(",")]
            if (
                len(coordinates) != 2
                or not -90 <= coordinates[0] <= 90
                or not -180 <= coordinates[1] <= 180
            ):
                raise ValueError("Invalid ODATA coordinates")
            candidates.append(
                {
                    "external_id": str(raw["id"]),
                    "name": raw["title"],
                    "address": raw["address"],
                    "latitude": coordinates[0],
                    "longitude": coordinates[1],
                    "url": urljoin(source_url, raw.get("url", "")),
                    "locator": f"data-locations[id={raw['id']}]",
                }
            )
    else:
        if not parser.rows:
            raise ValueError("Missing NEXTDC portfolio rows")
        pattern = (
            r"(?P<code>[A-Z]+\d+) (?P<locality>.+?) \| "
            r"(?P<area>.*?)m² \| (?P<power>.*?)MW (?P<status>.+)"
        )
        for raw in parser.rows:
            match = re.fullmatch(pattern, raw["text"])
            if not match:
                raise ValueError("Changed NEXTDC portfolio row shape")
            item = {k: v.strip() for k, v in match.groupdict().items()}
            candidates.append(
                {
                    **item,
                    "external_id": item["code"],
                    "url": urljoin(source_url, raw["href"]) if raw["href"] else None,
                    "locator": f".dc-row {item['code']}",
                }
            )
    identities = [r["external_id"] for r in candidates]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate portfolio identities require review")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "review_required": True,
    }


class _AirTrunkLocations(HTMLParser):
    """Allowlist official location links without retaining page navigation text."""

    def __init__(self) -> None:
        super().__init__()
        self.href = ""
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            self.href = dict(attrs).get("href") or ""
            self.parts = []

    def handle_data(self, data: str) -> None:
        if self.href:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag != "a" or not self.href:
            return
        text = " ".join(" ".join(self.parts).split())
        match = re.match(r"((?:SYD|MEL|JHB|SGP|HKG|TOK|OSK|BOM|MAA|HYD)\d)\b", text)
        if match and "/location/" in self.href:
            self.links.append((match.group(1), self.href))
        self.href = ""
        self.parts = []


def parse_airtrunk_locations(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage AirTrunk's complete named-location inventory for manual review.

    The inventory establishes identities and official detail-page links only. It
    does not establish lifecycle status, electrical boundary, or exact capacity.
    Duplicate legacy URLs for one displayed code are collapsed deterministically.
    """
    if urlsplit(source_url).hostname != "airtrunk.com":
        raise ValueError("Expected official AirTrunk URL")
    parser = _AirTrunkLocations()
    parser.feed(content.decode("utf-8-sig"))
    candidates: dict[str, dict[str, str]] = {}
    for code, href in parser.links:
        url = urljoin(source_url, href)
        previous = candidates.get(code)
        # Prefer the longer current descriptive slug when legacy aliases coexist.
        if previous is None or len(url) > len(previous["url"]):
            candidates[code] = {
                "external_id": code,
                "url": url,
                "locator": f"locations link text {code}",
            }
    if len(candidates) != 22:
        raise ValueError("Changed AirTrunk location inventory shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": [candidates[key] for key in sorted(candidates)],
        "review_required": True,
    }


class _PueTables(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.heading = False
        self.cell = False
        self.text: list[str] = []
        self.year: int | None = None
        self.quarter: int | None = None
        self.row: list[str] = []
        self.table: list[list[str]] | None = None
        self.tables: list[tuple[int | None, int | None, list[list[str]]]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "h2":
            self.heading, self.text = True, []
        elif tag == "table":
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in {"td", "th"} and self.table is not None:
            self.cell, self.text = True, []

    def handle_data(self, data: str) -> None:
        if self.heading or self.cell:
            self.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        text = " ".join(" ".join(self.text).split())
        if tag == "h2":
            self.heading = False
            if match := re.fullmatch(r"(\d{4}) PUE Yearly Report", text):
                self.year, self.quarter = int(match[1]), None
            elif match := re.fullmatch(r"Quarter 0?([1-4])", text):
                self.quarter = int(match[1])
        elif tag in {"td", "th"} and self.cell:
            self.cell = False
            self.row.append(text)
        elif tag == "tr" and self.table is not None:
            self.table.append(self.row)
        elif tag == "table" and self.table is not None:
            self.tables.append((self.year, self.quarter, self.table))
            self.table = None


def parse_google_pue(content: bytes, *, year: int, quarter: int) -> dict[str, Any]:
    """Stage one explicitly selected complete campus table, preserving precision.

    Empty TTM cells stay null. Fleet-wide numbers never become campus records.
    No IT capacity, commissioning date or individual building identity is inferred.
    """
    if quarter not in {1, 2, 3, 4}:
        raise ValueError("Quarter must be 1..4")
    parser = _PueTables()
    parser.feed(content.decode("utf-8-sig"))
    selected = [rows for y, q, rows in parser.tables if (y, q) == (year, quarter)]
    if len(selected) != 1:
        raise ValueError("Expected exactly one selected Google PUE table")
    table = selected[0]
    header = ["Campuses", "Quarterly PUE", "Trailing twelve-month (TTM) PUE"]
    if len(table) < 4 or table[2] != header or table[1][0] != "Fleet":
        raise ValueError("Changed Google PUE table headers")
    candidates = []
    for cells in table[3:]:
        if len(cells) != 3 or not cells[0] or not cells[1]:
            raise ValueError("Incomplete Google PUE campus row")
        for value in cells[1:]:
            if value and (not re.fullmatch(r"\d+(?:\.\d+)?", value) or float(value) < 1):
                raise ValueError("Invalid measured PUE")
        candidates.append(
            {
                "campus": cells[0],
                "quarterly_pue_text": cells[1],
                "ttm_pue_text": cells[2] or None,
                "locator": f"{year} / Quarter {quarter:02d} / Campuses / {cells[0]}",
            }
        )
    if len({r["campus"] for r in candidates}) != len(candidates):
        raise ValueError("Duplicate campus row")
    return {
        "year": year,
        "quarter": quarter,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "review_required": True,
    }
