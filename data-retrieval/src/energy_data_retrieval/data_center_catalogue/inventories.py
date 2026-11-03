"""Offline identity staging for bounded official operator and CDU inventories.

Only named inventory links are retained. Detail-page specifications, lifecycle,
capacity boundaries and reuse conditions still require review before import.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from html.parser import HTMLParser
from typing import Any
from urllib.parse import urljoin, urlsplit


class _Links(HTMLParser):
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
        if tag == "a" and self.href:
            self.links.append((self.href, " ".join(" ".join(self.parts).split())))
            self.href = ""
            self.parts = []


def parse_named_inventory(
    content: bytes, *, source_url: str, expected_count: int
) -> dict[str, Any]:
    """Stage exact atNorth site codes or CoolIT CDU product slugs, fail on drift.

    Duplicate navigation/card links collapse only when their identity and URL
    agree. A second URL for one immutable identity requires manual review.
    Never infer MW, lifecycle, cooling, or physical scope from inventory links.
    """
    host = urlsplit(source_url).hostname
    if host not in {"www.atnorth.com", "www.coolitsystems.com"}:
        raise ValueError("Unsupported official inventory URL")
    if expected_count < 1:
        raise ValueError("Positive expected count required")
    parser = _Links()
    parser.feed(content.decode("utf-8-sig"))
    candidates: dict[str, dict[str, str]] = {}
    for href, text in parser.links:
        url = urljoin(source_url, href)
        parsed = urlsplit(url)
        if parsed.hostname != host or parsed.scheme != "https":
            continue
        if host == "www.atnorth.com":
            match = re.search(r"\b(?:ICE|FIN|SWE|DEN|NOR)\d{2}\b", text)
            if not match or not parsed.path.startswith("/nordic-data-centers/"):
                continue
            identity = match[0]
        else:
            match = re.fullmatch(r"/cdu-product/((?:chx|ahx)\d+)/?", parsed.path)
            if not match:
                continue
            identity = match[1]
        previous = candidates.get(identity)
        if previous and previous["url"] != url:
            raise ValueError(f"Conflicting inventory URL for {identity}")
        candidates[identity] = {
            "external_id": identity,
            "url": url,
            "locator": f"inventory link {identity}",
        }
    if len(candidates) != expected_count:
        raise ValueError(f"Changed inventory shape: {len(candidates)} != {expected_count}")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_required": True,
        "candidates": [candidates[key] for key in sorted(candidates)],
    }


def parse_cdu_spec_matrix(
    content: bytes, *, source_url: str, expected_count: int
) -> dict[str, Any]:
    """Stage an extracted OEM CDU matrix without inventing optional variants.

    The offline CSV keeps the model and its stated rating conditions together.
    It is a review aid, not an importer: source PDF locators and field evidence
    must still be attached before canonical publication.
    """
    host = urlsplit(source_url).hostname
    if host not in {"www.motivaircorp.com", "www.nvent.com"}:
        raise ValueError("Unsupported official CDU source URL")
    if expected_count < 1:
        raise ValueError("Positive expected count required")
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    required = {
        "model",
        "cooling_capacity_kw",
        "cooling_rating_conditions",
        "primary_flow",
        "secondary_flow",
    }
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise ValueError("Missing CDU matrix columns")
    candidates: dict[str, dict[str, Any]] = {}
    for line, row in enumerate(reader, start=2):
        model = (row.get("model") or "").strip()
        conditions = (row.get("cooling_rating_conditions") or "").strip()
        if not model or not conditions:
            raise ValueError(f"Incomplete CDU row {line}")
        try:
            cooling = float(row["cooling_capacity_kw"])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid cooling rating on row {line}") from exc
        if cooling <= 0:
            raise ValueError(f"Invalid cooling rating on row {line}")
        candidate = {
            "model": model,
            "cooling_capacity_kw": cooling,
            "cooling_rating_conditions": conditions,
            "primary_flow": (row.get("primary_flow") or "").strip(),
            "secondary_flow": (row.get("secondary_flow") or "").strip(),
            "locator": f"extracted CDU matrix row {line}",
        }
        previous = candidates.get(model)
        if previous is not None:
            comparable = {key: value for key, value in candidate.items() if key != "locator"}
            prior = {key: value for key, value in previous.items() if key != "locator"}
            if prior != comparable:
                raise ValueError(f"Conflicting CDU row for {model}")
            raise ValueError(f"Duplicate CDU row for {model}")
        candidates[model] = candidate
    if len(candidates) != expected_count:
        raise ValueError(f"Changed CDU matrix shape: {len(candidates)} != {expected_count}")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_required": True,
        "candidates": [candidates[key] for key in sorted(candidates)],
    }
