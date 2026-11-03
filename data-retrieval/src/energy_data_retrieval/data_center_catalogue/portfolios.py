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


class _AfricaDataCentresFootprint(HTMLParser):
    """Collect only named facility links from the public footprint navigation."""

    def __init__(self) -> None:
        super().__init__()
        self.href = ""
        self.parts: list[str] = []
        self.links: list[tuple[str, str, str]] = []

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
        match = re.fullmatch(r"(JHB1|JHB2|CPT1|NBO1|LOS1)\s+(.+)", text)
        if match:
            self.links.append((match.group(1), match.group(2), self.href))
        self.href = ""
        self.parts = []


def parse_africa_data_centres_footprint(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the complete five-facility footprint displayed by the operator.

    Navigation establishes identities and official detail links only. Facility
    status, capacity, certification and geography still require source review.
    Duplicate desktop/mobile navigation entries are collapsed by immutable code.
    """
    if urlsplit(source_url).hostname != "www.africadatacentres.com":
        raise ValueError("Expected official Africa Data Centres URL")
    parser = _AfricaDataCentresFootprint()
    parser.feed(content.decode("utf-8-sig"))
    candidates: dict[str, dict[str, str]] = {}
    for code, locality, href in parser.links:
        candidate = {
            "external_id": code,
            "locality": locality,
            "url": urljoin(source_url, href),
            "locator": f"Pan-African Footprint link text {code}",
        }
        previous = candidates.setdefault(code, candidate)
        if previous != candidate:
            raise ValueError("Conflicting Africa Data Centres footprint identity")
    if set(candidates) != {"JHB1", "JHB2", "CPT1", "NBO1", "LOS1"}:
        raise ValueError("Changed Africa Data Centres footprint shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": [candidates[key] for key in sorted(candidates)],
        "review_required": True,
    }


def parse_schneider_galaxy_vs_model_list(
    content: bytes, *, source_url: str, expected_count: int | None = None
) -> dict[str, Any]:
    """Stage exact Galaxy VS commercial references from extracted PDF text.

    Only explicit 400 V model-list entries are returned. Battery options are
    retained as source text and are never expanded into possible combinations.
    Electrical ratings and performance tables still require manual review.
    """
    if not (urlsplit(source_url).hostname or "").endswith("se.com"):
        raise ValueError("Expected official Schneider Electric URL")
    text = " ".join(content.decode("utf-8-sig").split())
    matches = re.findall(
        r"Galaxy VS UPS (\d+) kW 400 V, (.+?) \((GVSUPS[A-Z0-9]+)\)",
        text,
    )
    candidates: dict[str, dict[str, Any]] = {}
    for rating, configuration, sku in matches:
        row = {
            "commercial_reference": sku,
            "rated_active_power_kw": int(rating),
            "configuration": configuration,
            "locator": f"Model list / {sku}",
        }
        previous = candidates.setdefault(sku, row)
        if previous != row:
            raise ValueError("Conflicting Schneider commercial reference")
    if not candidates or (expected_count is not None and len(candidates) != expected_count):
        raise ValueError("Changed Schneider Galaxy VS model-list shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": [candidates[key] for key in sorted(candidates)],
        "review_required": True,
    }


def parse_stulz_cyberair_3pro_dx_table(
    content: bytes, *, source_url: str, expected_count: int | None = None
) -> dict[str, Any]:
    """Stage explicit fixed-speed R410A CyberAir 3PRO DX configurations.

    The adapter consumes layout-preserving text extracted from STULZ's official
    technical-data PDF. It deliberately selects only the two fixed-speed tables
    (ASR ``A`` and free-cooling ALR ``GE``); modulating and R134a tables remain
    separate configurations and are not combined with these rows.
    """
    return _parse_stulz_cyberair_3pro_dx_table(
        content,
        source_url=source_url,
        expected_count=expected_count,
        compressor_kind="fixed-speed",
    )


def parse_stulz_cyberair_3pro_dx_modulating_table(
    content: bytes, *, source_url: str, expected_count: int | None = None
) -> dict[str, Any]:
    """Stage explicit modulating-EC-compressor R410A configurations.

    ASR ``AS`` and free-cooling ALR ``GES`` are separate documented models.
    The parser never combines their values with fixed-speed or R134a tables.
    """
    return _parse_stulz_cyberair_3pro_dx_table(
        content,
        source_url=source_url,
        expected_count=expected_count,
        compressor_kind="modulating-ec",
    )


def parse_stulz_cyberair_3pro_dx_r134a_table(
    content: bytes, *, source_url: str, expected_count: int | None = None
) -> dict[str, Any]:
    """Stage only the explicitly populated fixed-speed R134a rows.

    The OEM table includes unavailable model columns. Those columns are removed
    using the printed ``N/A`` airflow mask; blanks are never filled from R410A.
    """
    if not (urlsplit(source_url).hostname or "").endswith("stulz.es"):
        raise ValueError("Expected official STULZ URL")
    text = content.decode("utf-8-sig")
    marker = "CyberAir 3PRO DX (ASR/ALR) - R134a - Technical Data"
    if marker not in text:
        raise ValueError("Missing R134a CyberAir 3PRO table")
    r134a = text.split(marker, 1)[1]

    def line(block: str, label: str) -> str:
        value = next((row for row in block.splitlines() if row.strip().startswith(label)), None)
        if value is None:
            raise ValueError(f"Missing STULZ table row: {label}")
        return value

    def values(block: str, label: str, unit: str | None = None) -> list[str]:
        row = line(block, label)
        tail = row.split(unit, 1)[1] if unit else row[row.find(label) + len(label) :]
        pattern = r"\d+\s*/\s*\d+" if label.startswith("Number of circuits") else r"\d[\d.,]*"
        return [item.replace(" ", "") for item in re.findall(pattern, tail)]

    def number(value: str) -> float:
        return float(value.replace(".", "").replace(",", "."))

    candidates: list[dict[str, Any]] = []
    sections = [
        (
            "ASR",
            "A",
            "Air cooled with fixed speed compressor",
            "Free cooling with fixed speed compressor",
        ),
        ("ALR", "GE", "Free cooling with fixed speed compressor", "Remarks:"),
    ]
    for family, suffix, start, end in sections:
        if start not in r134a or end not in r134a:
            raise ValueError("Changed STULZ R134a table shape")
        block = r134a.split(start, 1)[1].split(end, 1)[0]
        header = line(block, f"{family} xxx {suffix}")
        models = re.findall(r"\b\d{3,4}\b", header.split(suffix, 1)[1])
        airflow_line = line(block, "Air flow").split("m³/h", 1)[1]
        airflow_cells = re.findall(r"N/A|\d[\d.,]*", airflow_line)
        if len(airflow_cells) != len(models):
            raise ValueError("Changed STULZ R134a availability mask")
        available = [index for index, cell in enumerate(airflow_cells) if cell != "N/A"]
        rows = {
            "cooling_total_kw": values(block, "Cooling capacity (total = sensible)", "kW"),
            "cooling_net_kw": values(block, "Cooling capacity (net)", "kW"),
            "fan_power_kw": values(block, "Fan power consumption", "kW"),
            "compressor_power_kw": values(block, "Compressor power consumption", "kW"),
            "input_power_kw": values(block, "Total power consumption", "kW"),
            "supply_air_temperature_c": values(block, "Supply air temperature", "°C"),
            "eer_kw_per_kw": values(block, "EER", "kW/kW"),
            "circuits_compressors": values(block, "Number of circuits / compressors"),
            "weight_kg": values(block, "Weight", "kg"),
        }
        if family == "ALR":
            rows["free_cooling_water_temperature_c"] = values(
                block, "Water temp. for 100% free cooling", "°C"
            )
            rows["medium_volume_flow_m3_h"] = values(block, "Medium volume flow", "m³/h")
        if any(len(row) != len(available) for row in rows.values()):
            raise ValueError("Changed STULZ R134a populated row width")
        for position, model_index in enumerate(available):
            code = models[model_index]
            candidates.append(
                {
                    "model": f"{family} {code} {suffix}",
                    "refrigerant": "R134a",
                    "airflow_m3_h": number(airflow_cells[model_index]),
                    **{
                        key: row[position]
                        if key == "circuits_compressors"
                        else number(row[position])
                        for key, row in rows.items()
                    },
                    "locator": f"R134a / {family} xxx {suffix} / {code}",
                }
            )
    if not candidates or (expected_count is not None and len(candidates) != expected_count):
        raise ValueError("Changed STULZ CyberAir R134a table shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "rating_conditions": {
            "voltage_v": 400,
            "phases": 3,
            "frequency_hz": 50,
            "return_air_temperature_c": 33,
            "return_air_relative_humidity_pct": 30,
            "condensing_temperature_c": 45,
            "external_static_pressure_pa": 20,
        },
        "review_required": True,
    }


def _parse_stulz_cyberair_3pro_dx_table(
    content: bytes,
    *,
    source_url: str,
    expected_count: int | None,
    compressor_kind: str,
) -> dict[str, Any]:
    if not (urlsplit(source_url).hostname or "").endswith("stulz.es"):
        raise ValueError("Expected official STULZ URL")
    text = content.decode("utf-8-sig")
    if "CyberAir 3PRO DX (ASR/ALR) - R410A - Technical Data" not in text:
        raise ValueError("Missing R410A CyberAir 3PRO table")
    r410a = text.split("CyberAir 3PRO DX (ASR/ALR) - R410A - Technical Data", 1)[1]
    r410a = r410a.split("CyberAir 3PRO DX (ASR/ALR) - R134a - Technical Data", 1)[0]

    def row_values(block: str, label: str, unit: str | None = None) -> list[str]:
        line = next((line for line in block.splitlines() if line.strip().startswith(label)), None)
        if line is None:
            raise ValueError(f"Missing STULZ table row: {label}")
        tail = (
            line.split(unit, 1)[1] if unit else line[len(line) - len(line.lstrip()) + len(label) :]
        )
        pattern = r"\d+\s*/\s*\d+" if label.startswith("Number of circuits") else r"\d[\d.,]*"
        return [value.replace(" ", "") for value in re.findall(pattern, tail)]

    candidates: list[dict[str, Any]] = []
    if compressor_kind == "fixed-speed":
        sections = [
            (
                "ASR",
                "A",
                "Air cooled with fixed speed compressor",
                "Air cooled with modulating",
            ),
            (
                "ALR",
                "GE",
                "Free cooling with fixed speed compressor",
                "Free cooling with modulating",
            ),
        ]
    elif compressor_kind == "modulating-ec":
        sections = [
            (
                "ASR",
                "AS",
                "Air cooled with modulating EC compressor",
                "Free cooling with fixed speed compressor",
            ),
            (
                "ALR",
                "GES",
                "Free cooling with modulating EC compressor",
                "Remarks:",
            ),
        ]
    else:  # pragma: no cover - private defensive boundary
        raise ValueError("Unsupported STULZ compressor table")
    for family, suffix, start, end in sections:
        if start not in r410a or end not in r410a:
            raise ValueError("Changed STULZ fixed-speed table shape")
        block = r410a.split(start, 1)[1].split(end, 1)[0]
        header = next(
            (
                line
                for line in block.splitlines()
                if line.strip().startswith(f"{family} xxx {suffix}")
            ),
            None,
        )
        if header is None:
            raise ValueError("Missing STULZ model header")
        models = re.findall(r"\b\d{3,4}\b", header.split(suffix, 1)[1])
        rows = {
            "airflow_m3_h": row_values(block, "Air flow", "m³/h"),
            "cooling_total_kw": row_values(block, "Cooling capacity (total = sensible)", "kW"),
            "cooling_net_kw": row_values(block, "Cooling capacity (net)", "kW"),
            "fan_power_kw": row_values(block, "Fan power consumption", "kW"),
            "compressor_power_kw": row_values(block, "Compressor power consumption", "kW"),
            "input_power_kw": row_values(block, "Total power consumption", "kW"),
            "supply_air_temperature_c": row_values(block, "Supply air temperature", "°C"),
            "eer_kw_per_kw": row_values(block, "EER", "kW/kW"),
            "circuits_compressors": row_values(block, "Number of circuits / compressors"),
            "weight_kg": row_values(block, "Weight", "kg"),
        }
        if compressor_kind == "modulating-ec" and family == "ALR":
            rows["free_cooling_water_temperature_c"] = row_values(
                block, "Water temp. for 100% free cooling", "°C"
            )
            rows["medium_volume_flow_m3_h"] = row_values(block, "Medium volume flow", "m³/h")
        if any(len(values) != len(models) for values in rows.values()):
            raise ValueError(f"Changed STULZ {compressor_kind} row width")

        def number(value: str) -> float:
            return float(value.replace(".", "").replace(",", "."))

        for index, code in enumerate(models):
            candidates.append(
                {
                    "model": f"{family} {code} {suffix}",
                    "refrigerant": "R410A",
                    **{
                        key: values[index]
                        if key == "circuits_compressors"
                        else number(values[index])
                        for key, values in rows.items()
                    },
                    "locator": f"R410A / {family} xxx {suffix} / {code}",
                }
            )
    if not candidates or (expected_count is not None and len(candidates) != expected_count):
        raise ValueError(f"Changed STULZ CyberAir {compressor_kind} table shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "rating_conditions": {
            "voltage_v": 400,
            "phases": 3,
            "frequency_hz": 50,
            "return_air_temperature_c": 33,
            "return_air_relative_humidity_pct": 30,
            "condensing_temperature_c": 45,
            "external_static_pressure_pa": 20,
        },
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


class _MetaLocations(HTMLParser):
    """Collect only the current global-fleet cards from Meta's official page."""

    def __init__(self) -> None:
        super().__init__()
        self.region: str | None = None
        self.current: dict[str, str | None] | None = None
        self.capture: str | None = None
        self.parts: list[str] = []
        self.rows: list[dict[str, str | None]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        classes = (values.get("class") or "").split()
        if tag == "h2" and "data-center-location-header" in classes:
            self.capture, self.parts = "region", []
        elif tag == "article" and "wp-block-fbdc-card" in classes:
            self.current = {"region": self.region}
        elif self.current is not None and tag == "p" and "card__eyebrow-text" in classes:
            self.capture, self.parts = "jurisdiction", []
        elif self.current is not None and tag == "h3" and "card__title" in classes:
            self.capture, self.parts = "locality", []
        elif self.current is not None and tag == "p" and "card__excerpt" in classes:
            self.capture, self.parts = "summary", []
        elif self.current is not None and tag == "a" and "card__primary-cta" in classes:
            self.current["url"] = values.get("href")

    def handle_data(self, data: str) -> None:
        if self.capture:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.capture == "region" and tag == "h2":
            self.region = " ".join(" ".join(self.parts).split())
            self.capture = None
        elif self.capture == "jurisdiction" and tag == "p" and self.current is not None:
            self.current["jurisdiction"] = " ".join(" ".join(self.parts).split())
            self.capture = None
        elif self.capture == "locality" and tag == "h3" and self.current is not None:
            self.current["locality"] = " ".join(" ".join(self.parts).split())
            self.capture = None
        elif self.capture == "summary" and tag == "p" and self.current is not None:
            self.current["summary"] = " ".join(" ".join(self.parts).split())
            self.capture = None
        elif tag == "article" and self.current is not None:
            self.rows.append(self.current)
            self.current = None
            self.capture = None


def parse_meta_locations(
    content: bytes, *, source_url: str, expected_count: int | None = None
) -> dict[str, Any]:
    """Stage Meta's complete displayed fleet without inferring lifecycle or MW."""
    if urlsplit(source_url).hostname != "datacenters.atmeta.com":
        raise ValueError("Expected official Meta Data Centers URL")
    parser = _MetaLocations()
    parser.feed(content.decode("utf-8-sig"))
    required = {"region", "jurisdiction", "locality", "summary", "url"}
    candidates: list[dict[str, str]] = []
    for raw in parser.rows:
        if not required <= raw.keys() or not all(raw[key] for key in required):
            raise ValueError("Incomplete Meta fleet card")
        candidates.append(
            {
                **{key: str(raw[key]).strip() for key in required},
                "url": urljoin(source_url, str(raw["url"]).strip()).removesuffix("%20"),
                "locator": f"Our global data center fleet / {raw['region']} / {raw['locality']}",
            }
        )
    identities = [(row["region"].casefold(), row["locality"].casefold()) for row in candidates]
    if (
        not candidates
        or len(identities) != len(set(identities))
        or (expected_count is not None and len(candidates) != expected_count)
    ):
        raise ValueError("Changed Meta global-fleet shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "review_required": True,
    }


def parse_vertiv_powerups6000_table(
    content: bytes, *, source_url: str, expected_count: int | None = None
) -> dict[str, Any]:
    """Stage explicit PowerUPS 6000 kVA/topology configurations.

    The shared family specifications are returned as rating conditions. The
    parser does not calculate kW from the stated unity output power factor and
    does not assign the layout's grouped dimensions or efficiency range to an
    individual rating.
    """
    if not (urlsplit(source_url).hostname or "").endswith("vertiv.com"):
        raise ValueError("Expected official Vertiv URL")
    text = " ".join(content.decode("utf-8-sig").split())
    if "Vertiv™ PowerUPS 6000 industrial" not in text:
        raise ValueError("Missing Vertiv PowerUPS 6000 table")
    configurations = [
        ("single-phase", "single-phase", [6]),
        ("three-phase", "single-phase", [10, 20, 30, 40, 60, 80, 100, 120]),
        ("three-phase", "three-phase", [10, 20, 30, 40, 60, 80, 100, 120, 160, 200]),
    ]
    candidates: list[dict[str, Any]] = []
    for input_topology, output_topology, expected_ratings in configurations:
        label = f"{input_topology.capitalize()} input/{output_topology}"
        match = re.search(rf"{re.escape(label)} (?P<ratings>(?:\d+ )+)output", text)
        if match is None:
            raise ValueError(f"Missing PowerUPS topology row: {label}")
        ratings = [int(value) for value in re.findall(r"\d+", match["ratings"])]
        if ratings != expected_ratings:
            raise ValueError("Changed Vertiv PowerUPS 6000 rating row")
        for rating in ratings:
            candidates.append(
                {
                    "model": "PowerUPS 6000",
                    "variant": f"{rating} kVA; {input_topology} input; {output_topology} output",
                    "apparent_power_kva": rating,
                    "input_topology": input_topology,
                    "output_topology": output_topology,
                    "input_voltage_text": (
                        "220/230/240 V" if input_topology == "single-phase" else "380/400/415 V"
                    ),
                    "output_voltage_text": (
                        "220/230/240 V" if output_topology == "single-phase" else "380/400/415 V"
                    ),
                    "locator": f"Technical specifications / {label} output / {rating} kVA",
                }
            )
    if not candidates or (expected_count is not None and len(candidates) != expected_count):
        raise ValueError("Changed Vertiv PowerUPS 6000 table shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "shared_conditions": {
            "rated_input_frequency_text": "50/60 Hz",
            "input_frequency_range_text": "40-70 Hz",
            "input_power_factor": 0.95,
            "output_power_factor": 1.0,
            "operating_temperature_min_c": 0,
            "operating_temperature_max_c": 50,
            "communications": ["MODBUS", "SNMP", "dry contact", "RJ45"],
        },
        "review_required": True,
    }
