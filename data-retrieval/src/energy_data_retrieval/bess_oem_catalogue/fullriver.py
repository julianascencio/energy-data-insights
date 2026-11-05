"""Stage selected Fullriver DC cards without inferring ratings or model variants."""

import re
from html.parser import HTMLParser
from typing import TypedDict


class Card(TypedDict):
    """One exact model with separate native unit panels."""

    model: str
    panels: dict[str, dict[str, str]]


class _Cards(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[tuple[str, set[str], list[str]]] = []
        self.rows: list[dict[str, str]] = []
        self.row: dict[str, str] = {}
        self.label = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        classes = set((dict(attrs).get("class") or "").split())
        if "card-batt" in classes:
            if self.stack:
                raise ValueError("Nested battery cards")
            self.row = {}
        if (self.stack or "card-batt" in classes) and tag not in {
            "img",
            "br",
            "hr",
            "input",
            "source",
            "link",
            "meta",
            "wbr",
        }:
            self.stack.append((tag, classes, []))

    def handle_data(self, data: str) -> None:
        for _, _, parts in self.stack:
            parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        actual, classes, parts = self.stack.pop()
        if actual != tag:
            raise ValueError("Unbalanced card markup")
        value = " ".join("".join(parts).split())
        if "card-batt__model" in classes:
            if "model" in self.row:
                raise ValueError("Duplicate model heading")
            self.row["model"] = value
        if "card-batt__specs--label" in classes:
            self.label = value
        if "card-batt__specs--value" in classes:
            if not self.label or self.label in self.row or not value:
                raise ValueError("Missing or duplicate card field")
            self.row[self.label] = value
            self.label = ""
        if "card-batt" in classes:
            self.rows.append(self.row)


def parse_cards(content: bytes, *, expected_models: list[str]) -> list[Card]:
    """Return metric/imperial observations for explicitly reviewed exact models.

    Requires two complete unit panels per selected model. Other models are ignored,
    never fuzzy-matched. Capacity has no inferred discharge rate. Reserve minutes,
    current and dimensions remain strings with original units for manual review.
    """
    if not expected_models or len(set(expected_models)) != len(expected_models):
        raise ValueError("Expected unique reviewed models")
    parser = _Cards()
    parser.feed(content.decode("utf-8-sig"))
    if parser.stack:
        raise ValueError("Incomplete card markup")
    result: list[Card] = []
    for model in expected_models:
        rows = [r for r in parser.rows if r.get("model") == model]
        if len(rows) != 2:
            raise ValueError(f"Expected two unit panels: {model}")
        panels: dict[str, dict[str, str]] = {}
        for row in rows:
            if not {"model", "Group", "Capacity", "Dimms", "Weight"} <= row.keys():
                raise ValueError("Incomplete card fields")
            unit = "metric" if row["Dimms"].endswith(" mm") else "imperial"
            patterns = {
                "Capacity": r"\d+(?:\.\d+)? Ah",
                "Dimms": r"\d+(?:\.\d+)? x \d+(?:\.\d+)? x \d+(?:\.\d+)? "
                + ("mm" if unit == "metric" else "in"),
                "Weight": r"\d+(?:\.\d+)? " + ("kg" if unit == "metric" else "lbs"),
            }
            for key, value in row.items():
                if key in {"model", "Group"}:
                    continue
                pattern = patterns.get(key)
                if pattern is None and re.fullmatch(r"Reserve Capacity @ \d+A", key):
                    pattern = r"\d+(?:\.\d+)? min"
                if pattern is None or not re.fullmatch(pattern, value):
                    raise ValueError(f"Unreviewed label/unit: {key}")
            if unit in panels:
                raise ValueError("Duplicate unit panel")
            panels[unit] = row
        result.append({"model": model, "panels": panels})
    return result
