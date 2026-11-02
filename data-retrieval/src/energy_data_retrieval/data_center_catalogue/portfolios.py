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
