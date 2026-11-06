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


class _VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self.skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self.skip:
            self.skip -= 1

    def handle_data(self, data: str) -> None:
        if not self.skip:
            self.parts.append(data)


def parse_raxio_facility_page(
    content: bytes, *, source_url: str, expected_code: str | None = None
) -> dict[str, Any]:
    """Stage identity and public facility-design metrics from one Raxio page."""
    if urlsplit(source_url).hostname not in {"raxiogroup.com", "www.raxiogroup.com"}:
        raise ValueError("Expected official Raxio URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())

    def one(pattern: str, label: str) -> str:
        matches = list(dict.fromkeys(re.findall(pattern, text, re.IGNORECASE)))
        if len(matches) != 1:
            raise ValueError(f"Changed Raxio {label} shape")
        return matches[0]

    def optional_one(pattern: str, label: str) -> str | None:
        matches = list(dict.fromkeys(re.findall(pattern, text, re.IGNORECASE)))
        if len(matches) > 1:
            raise ValueError(f"Changed Raxio {label} shape")
        return matches[0] if matches else None

    code = one(r"Raxio data centre:\s*([A-Z0-9]+)", "facility identity")
    if expected_code is not None and code != expected_code:
        raise ValueError("Changed Raxio facility identity")
    it_mw = float(one(r"(\d+(?:\.\d+)?)\s*MW\s+IT Power", "IT-power"))
    rack_count = int(one(r"(\d+(?:,\d+)?)\s*Racks", "rack-capacity").replace(",", ""))
    grid_kv = float(one(r"(\d+(?:\.\d+)?)\s*kV utility supply", "utility-voltage"))
    area = float(
        one(
            r"(\d+(?:,\d+)?)\s*(?:m\s*2|sqm)\s+(?:of\s+)?white space",
            "white-space",
        ).replace(",", "")
    )
    cooling_mw = float(one(r"(\d+(?:\.\d+)?)\s*MW of (?:installed )?cooling provision", "cooling"))
    pue_text = optional_one(r"PUE of (\d+(?:\.\d+)?)", "PUE")
    pue = float(pue_text) if pue_text is not None else None
    status_markers = [
        marker
        for marker in (
            "commissioned October 2025",
            "Opened in 2024",
            "Launched in 2024",
            "Opened in 2023",
            "Opened in 2021",
            "Under Development",
        )
        if marker.casefold() in text.casefold()
    ]
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "external_id": code,
            "it_design_mw": it_mw,
            "rack_capacity": rack_count,
            "data_hall_area_m2": area,
            "connection_voltage_kv": grid_kv,
            "cooling_provision_mw": cooling_mw,
            "pue": pue,
            "status_markers": status_markers,
            "locator": f"Raxio data centre: {code} / current facility page",
        },
        "review_required": True,
    }


def parse_icolo_facility_page(
    content: bytes, *, source_url: str, expected_code: str | None = None
) -> dict[str, Any]:
    """Stage public iColo/Digital Realty facility identity and current metrics."""
    if urlsplit(source_url).hostname not in {"icolo.io", "www.icolo.io"}:
        raise ValueError("Expected official iColo URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())

    codes = list(dict.fromkeys(re.findall(r"\b(MPM1|MBA1|MBA2|NBO1)\b", text)))
    if len(codes) != 1:
        raise ValueError("Changed iColo facility identity shape")
    code = codes[0]
    if expected_code is not None and code != expected_code:
        raise ValueError("Changed iColo facility identity")

    def optional_number(pattern: str, label: str) -> float | None:
        matches = list(dict.fromkeys(re.findall(pattern, text, re.IGNORECASE)))
        if len(matches) > 1:
            raise ValueError(f"Changed iColo {label} shape")
        return float(matches[0].replace(",", "")) if matches else None

    rack_count = optional_number(r"(\d+(?:,\d+)?)\s+(?:Rack Capacity|Racks?)\b", "rack")
    customer_space = optional_number(
        r"(\d+(?:,\d+)?)\s*(?:sqm|m\s*2)\s+(?:IT Space|Total Customer Space)",
        "customer-space",
    )
    campus_area = optional_number(
        r"(\d+(?:,\d+)?)\s*(?:sqm|m\s*2)\s+(?:Campus Size|Total Campus Area)",
        "campus-area",
    )
    lifecycle = next(
        (
            marker
            for marker in (
                "operational since 2017",
                "launched in 2022",
                "launched in September 2019",
            )
            if marker.casefold() in text.casefold()
        ),
        None,
    )
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "external_id": code,
            "rack_capacity": int(rack_count) if rack_count is not None else None,
            "customer_space_m2": customer_space,
            "campus_area_m2": campus_area,
            "lifecycle_marker": lifecycle,
            "locator": f"{code} current facility page / public facility metrics",
        },
        "review_required": True,
    }


def parse_icolo_home_portfolio(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the three exact power/area cards currently printed on iColo's home page."""
    if urlsplit(source_url).hostname not in {"icolo.io", "www.icolo.io"}:
        raise ValueError("Expected official iColo URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    patterns = {
        "MPM1": r"MAPUTO ONE[^0-9]+IT Power:\s*(\d+(?:\.\d+)?)\s*MW\s+Total Area:\s*(\d+(?:,\d+)?)",
        "MBA1": (
            r"MOMBASA ONE[^0-9]+IT Power:\s*(\d+(?:\.\d+)?)\s*MW\s+"
            r"Total Area:\s*(\d+(?:,\d+)?)"
        ),
        "MBA2": r"MOMBASA TWO[^0-9]+IT Load:\s*(\d+(?:\.\d+)?)\s*MW\s+Total Area:\s*(\d+(?:,\d+)?)",
    }
    candidates = []
    for code, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match is None:
            raise ValueError("Changed iColo home portfolio shape")
        candidates.append(
            {
                "external_id": code,
                "it_power_mw": float(match.group(1)),
                "total_area_m2": float(match.group(2).replace(",", "")),
                "locator": f"home page campus card / {code}",
            }
        )
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "review_required": True,
    }


def parse_digital_realty_nbo2_release(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the opening and unclassified capacity claim for NBO2."""
    if urlsplit(source_url).hostname != "investor.digitalrealty.com":
        raise ValueError("Expected official Digital Realty investor URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    if "opening of the 6.4-megawatt (MW) Nairobi Two Data Center (NBO2)" not in text:
        raise ValueError("Changed NBO2 opening-release shape")
    if re.search(r"Built alongside Nairobi One \(\s*NBO1\s*\)", text) is None:
        raise ValueError("Missing NBO1/NBO2 campus relationship")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "external_id": "NBO2",
            "reported_capacity_mw": 6.4,
            "opening_date": "2026-09-07",
            "campus_external_id": "Nairobi campus",
            "locator": "opening paragraph and Built alongside Nairobi One paragraph",
        },
        "review_required": True,
    }


def parse_green_mountain_portfolio(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the complete current Green Mountain site list and lifecycle split."""
    if urlsplit(source_url).hostname not in {"greenmountain.no", "www.greenmountain.no"}:
        raise ValueError("Expected official Green Mountain URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    expected = {
        "SVG-Rennesøy": "operational",
        "TEL-Rjukan": "operational",
        "OSL-Enebakk": "operational",
        "OSL-Hamar": "operational",
        "LON-East": "operational",
        "FRA-Mainz": "under_construction",
        "SVG-Undheim": "under_construction",
    }
    required = (
        "currently operates four different data center sites in Norway and one the UK",
        "data center under construction in Undheim, Norway and one in Mainz, Germany",
    )
    if not all(marker.casefold() in text.casefold() for marker in required):
        raise ValueError("Changed Green Mountain portfolio lifecycle shape")
    for code in expected:
        if code not in text:
            raise ValueError("Changed Green Mountain portfolio identity shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": [
            {
                "external_id": code,
                "status": status,
                "locator": f"current data-centers portfolio / {code}",
            }
            for code, status in expected.items()
        ],
        "review_required": True,
    }


def parse_glesys_owned_portfolio(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the complete current GleSYS owned-location directory."""
    if urlsplit(source_url).hostname not in {"glesys.com", "www.glesys.com"}:
        raise ValueError("Expected official GleSYS URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    if "Most of our services run from our own data centers" not in text:
        raise ValueError("Changed GleSYS owned-portfolio shape")
    expected = (
        ("falkenberg", "Falkenberg", "facility"),
        ("oulu", "Oulu", "campus"),
        ("pori", "Pori", "facility"),
        ("stockholm", "Stockholm", "facility"),
        ("tampere", "Tampere", "facility"),
    )
    for _, name, _ in expected:
        if text.count(name) < 2:
            raise ValueError("Changed GleSYS owned-portfolio identity shape")
    if "three enterprise data centers and Campus Oulu" not in text:
        raise ValueError("Changed GleSYS Oulu aggregate shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": [
            {
                "external_id": slug,
                "name": name,
                "record_scope": scope,
                "status": "operational",
                "locator": f"current owned data-center directory / {name}",
            }
            for slug, name, scope in expected
        ],
        "review_required": True,
    }


def parse_glesys_site_page(
    content: bytes, *, source_url: str, expected_site: str | None = None
) -> dict[str, Any]:
    """Stage bounded public metrics from one current GleSYS owned-site page."""
    if urlsplit(source_url).hostname not in {"glesys.com", "www.glesys.com"}:
        raise ValueError("Expected official GleSYS URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    sites = [
        site
        for site in ("Falkenberg", "Oulu", "Pori", "Stockholm", "Tampere")
        if f"{site} data center" in text
    ]
    if len(sites) != 1:
        raise ValueError("Changed GleSYS site identity shape")
    site = sites[0]
    if expected_site is not None and site != expected_site:
        raise ValueError("Changed GleSYS site identity")
    metric_start = text.find(
        "Figures that reflect our Oulu operations"
        if site == "Oulu"
        else f"Metrics of our {site} facility"
    )
    if metric_start < 0:
        metric_start = text.find(f"Key metrics of our {site} facility")
    metric_end = text.find("Built for performance", metric_start)
    if site == "Oulu":
        metric_end = text.find("Room to scale AI in Europe", metric_start)
    if metric_start < 0 or metric_end < 0:
        raise ValueError("Changed GleSYS metric-card shape")
    metrics = text[metric_start:metric_end]

    def one(pattern: str, label: str) -> float | None:
        values = list(dict.fromkeys(float(value) for value in re.findall(pattern, metrics)))
        if len(values) > 1:
            raise ValueError(f"Changed GleSYS {label} shape")
        return values[0] if values else None

    candidate: dict[str, Any] = {
        "external_id": site.casefold(),
        "pue": one(r"(\d+(?:\.\d+)?)\s+PUE\b", "PUE"),
        "renewable_electricity_pct": one(
            r"(\d+(?:\.\d+)?)\s+%\s+Powered entirely by renewable electricity",
            "renewable-electricity",
        ),
        "rack_density_kw": one(r"(\d+(?:\.\d+)?)\s+(?:max )?kW/rack", "rack-density"),
        "reported_power_mw": one(r"(\d+(?:\.\d+)?)\s+MW\b", "power-capacity"),
        "data_center_count": one(r"(\d+(?:\.\d+)?)\s+data centers\b", "site-count"),
        "locator": f"current {site} page / public metric cards and narrative",
    }
    if site == "Falkenberg":
        required = (
            "With up to 43 kW per rack aircooled",
            "achieving a PUE of 1.2",
            "With a total capacity of 5 MW",
        )
        if not all(marker in text for marker in required):
            raise ValueError("Changed GleSYS Falkenberg conflict shape")
        candidate.update(
            {
                "conflicting_pue": 1.2,
                "conflicting_rack_density_kw": 43.0,
                "conflicting_reported_power_mw": 5.0,
            }
        )
    elif site == "Oulu":
        required = (
            "Our three data centers at Elektroniikkatie 5, Elektroniikkatie 15 "
            "and Yrttipellontie 1",
            "Campus Oulu adds room to scale AI and HPC workloads with up to "
            "300 MW of planned capacity",
            "Four interconnected data centers",
            "Across the three sites, up to 22 kW per rack",
            "With PUE values as low as 1.3",
            "has capacity available now, and is being built out in phases toward "
            "300 MW of planned capacity",
        )
        if not all(marker in text for marker in required):
            raise ValueError("Changed GleSYS Oulu campus shape")
        candidate.update(
            {
                "established_site_count": 3,
                "established_rack_density_kw": 22.0,
                "established_pue_lower_bound": 1.3,
                "campus_oulu_planned_capacity_mw": 300.0,
            }
        )
    elif site == "Stockholm":
        area = re.search(r"providing\s+(\d+)\s+m² of premium colocation space", text)
        if area is None:
            raise ValueError("Changed GleSYS Stockholm area shape")
        candidate["reported_colocation_space_m2"] = float(area.group(1))
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": candidate,
        "review_required": True,
    }


def parse_glesys_finland_integration(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the completed ownership transition for Pori and Tampere."""
    if urlsplit(source_url).hostname not in {"glesys.com", "www.glesys.com"}:
        raise ValueError("Expected official GleSYS URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    required = (
        "completed the integration of private cloud services and two Finnish data "
        "centers previously operated under Verne",
        "production environments now operating in Helsinki, Pori, and Tampere",
        "transition was completed without any service disruption",
    )
    if not all(marker in text for marker in required):
        raise ValueError("Changed GleSYS Finland integration shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": [
            {
                "external_id": site.casefold(),
                "status": "operational",
                "former_operator": "Verne",
                "locator": "2026 completed-integration announcement",
            }
            for site in ("Pori", "Tampere")
        ],
        "review_required": True,
    }


def parse_ecodatacenter_portfolio(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the complete current EcoDataCenter site directory."""
    if urlsplit(source_url).hostname not in {"ecodatacenter.tech", "www.ecodatacenter.tech"}:
        raise ValueError("Expected official EcoDataCenter URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    required = (
        "Sites 2",
        "EcoDataCenter 1 - Falun",
        "EcoDataCenter 2 - Borlänge",
        "Our biggest project yet, under construction",
    )
    if not all(marker in text for marker in required):
        raise ValueError("Changed EcoDataCenter portfolio shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": [
            {
                "external_id": "ecodatacenter-1",
                "name": "EcoDataCenter 1",
                "locality": "Falun",
                "record_scope": "facility",
                "status": "operational",
                "locator": "current data-center directory / Falun",
            },
            {
                "external_id": "ecodatacenter-2",
                "name": "EcoDataCenter 2",
                "locality": "Borlänge",
                "record_scope": "campus",
                "status": "under_construction",
                "locator": "current data-center directory / Borlänge",
            },
        ],
        "review_required": True,
    }


def parse_ecodatacenter_site_page(
    content: bytes, *, source_url: str, expected_site: str | None = None
) -> dict[str, Any]:
    """Stage bounded metrics from the Falun or Borlänge current site page."""
    if urlsplit(source_url).hostname not in {"ecodatacenter.tech", "www.ecodatacenter.tech"}:
        raise ValueError("Expected official EcoDataCenter URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    sites = [site for site in ("EcoDataCenter 1", "EcoDataCenter 2") if site in text]
    if expected_site not in {"EcoDataCenter 1", "EcoDataCenter 2"}:
        raise ValueError("Expected an exact EcoDataCenter site identity")
    if expected_site not in sites:
        raise ValueError("Changed EcoDataCenter site identity")
    if expected_site == "EcoDataCenter 1":
        required = (
            "A large-scale data center site for HPC, AI in Falun, Sweden",
            "Renewable electricity on-site 100 %",
            "75% comes from hydropower and 25% from wind power",
            "Total available power 80 MW",
            "PUE 1.2 Achieved according to ISO standards",
        )
        if not all(marker in text for marker in required):
            raise ValueError("Changed EcoDataCenter 1 metric shape")
        candidate = {
            "external_id": "ecodatacenter-1",
            "locality": "Falun",
            "reported_power_mw": 80.0,
            "renewable_electricity_pct": 100.0,
            "hydropower_pct": 75.0,
            "wind_power_pct": 25.0,
            "reported_pue": 1.2,
            "locator": "current Falun page / metric cards and narrative",
        }
    else:
        required = (
            "Renewable electricity on-site 100 %",
            "Total available power up to 600 MW",
            "Total available land 200 k m2",
            "Construction start 2025",
            "All environmental permits have been approved",
            "Construction began in September 2025",
            "first phase of the site set to be completed by mid-2027",
        )
        if not all(marker in text for marker in required):
            raise ValueError("Changed EcoDataCenter 2 metric shape")
        candidate = {
            "external_id": "ecodatacenter-2",
            "locality": "Borlänge",
            "reported_power_upper_bound_mw": 600.0,
            "renewable_electricity_pct": 100.0,
            "reported_land_area_m2": 200000.0,
            "construction_start": "2025-09",
            "first_phase_target": "2027-mid-year",
            "environmental_permits": "approved",
            "locator": "current Borlänge page / metric cards and construction narrative",
        }
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": candidate,
        "review_required": True,
    }


def parse_ecodatacenter_smedjebacken_announcement(
    content: bytes, *, source_url: str
) -> dict[str, Any]:
    """Stage the announced third EcoDataCenter campus without inferring permits."""
    if urlsplit(source_url).hostname not in {"ecodatacenter.tech", "www.ecodatacenter.tech"}:
        raise ValueError("Expected official EcoDataCenter URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    required = (
        "EcoDataCenter to Establish Third Datacenter Campus in Sweden",
        "25.08.2026",
        "signed an agreement with Smedjebacken Municipality for the purchase of land",
        "purchase covers 52 hectares of land",
        "building and environmental permits are finalized",
        "anticipated in early 2027",
        "green light of an immediate 150MW with credible opportunity to expand further",
    )
    if not all(marker in text for marker in required):
        raise ValueError("Changed EcoDataCenter Smedjebacken announcement shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "external_id": "ecodatacenter-3",
            "locality": "Smedjebacken",
            "reported_land_area_hectares": 52.0,
            "reported_unclassified_power_mw": 150.0,
            "construction_target": "2027-early",
            "publication_date": "2026-08-25",
            "status": "announced",
            "locator": "dated land-purchase and third-campus announcement",
        },
        "review_required": True,
    }


def parse_penta_infra_directory(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the exact 12 facilities displayed in Penta Infra's current directory."""
    if urlsplit(source_url).hostname not in {"penta-infra.com", "www.penta-infra.com"}:
        raise ValueError("Expected official Penta Infra URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    expected = (
        ("amsterdam", "Amsterdam", "under_construction", "RFS H1 2026", 8.0, 4000.0),
        ("geleen", "Geleen", "operational", "In operation", 0.75, 320.0),
        ("leeuwarden-01", "Leeuwarden 01", "operational", "In operation", 0.45, 400.0),
        ("leeuwarden-02", "Leeuwarden 02", "operational", "In operation", 0.4, 400.0),
        ("berlin", "Berlin", "operational", "In operation", 2.7, 1800.0),
        ("cologne", "Cologne", "operational", "In operation", 0.2, 500.0),
        ("duesseldorf", "Düsseldorf", "operational", "In operation", 2.4, 1942.0),
        ("hamburg", "Hamburg", "operational", "In operation", 4.4, 2500.0),
        ("leipzig", "Leipzig", "operational", "In operation", 2.8, 1500.0),
        ("brussels", "Brussels", "operational", "In operation", 7.2, 3500.0),
        ("paris", "Paris", "operational", "In operation", 15.0, 4200.0),
        ("copenhagen", "Copenhagen", "operational", "In operation", 1.6, 1000.0),
    )
    positions: list[int] = []
    candidates: list[dict[str, Any]] = []
    for slug, name, status, label, capacity_mw, area_m2 in expected:
        capacity_label = (
            f"{int(capacity_mw * 1000)} kW"
            if capacity_mw < 1
            else f"{str(capacity_mw).replace('.', ',').removesuffix(',0')} MW"
        )
        area_label = f"{int(area_m2):,}".replace(",", ".") + " m²"
        marker = f"{name} {label}"
        position = text.find(marker)
        if position < 0:
            raise ValueError(f"Changed Penta Infra directory card for {name}")
        card_end = text.find("View more", position)
        if card_end < 0:
            raise ValueError(f"Changed Penta Infra directory boundary for {name}")
        card = text[position:card_end]
        if capacity_label not in card or area_label not in card:
            raise ValueError(f"Changed Penta Infra directory metrics for {name}")
        positions.append(position)
        candidates.append(
            {
                "external_id": slug,
                "name": name,
                "status": status,
                "status_label": label,
                "it_capacity_mw": capacity_mw,
                "technical_area_m2": area_m2,
                "url": urljoin(source_url, f"{slug}/"),
                "locator": f"current directory card / {name}",
            }
        )
    if positions != sorted(positions) or len(set(positions)) != len(expected):
        raise ValueError("Changed Penta Infra directory order or duplicate identity")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "review_required": True,
    }


def parse_penta_infra_site_page(
    content: bytes, *, source_url: str, expected_code: str
) -> dict[str, Any]:
    """Stage exact IT-capacity and IT-space cards from one Penta Infra site page."""
    if urlsplit(source_url).hostname not in {"penta-infra.com", "www.penta-infra.com"}:
        raise ValueError("Expected official Penta Infra URL")
    if not re.fullmatch(r"[A-Z]{3}\d{2}", expected_code):
        raise ValueError("Expected an exact Penta Infra facility code")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    start = text.find(f"Penta Infra {expected_code}")
    end = text.find("About the region", start)
    if start < 0 or end < 0:
        raise ValueError("Changed Penta Infra facility identity or metric boundary")
    metric_section = text[start:end]
    capacity = re.search(
        r"(\d+(?:[.,]\d+)?)\s*(MW|kW)\s+(planned\s+)?IT capacity\b",
        metric_section,
    )
    area = re.search(r"(\d+(?:[.,]\d+)?)\s*m²\s+IT space\b", metric_section)
    if capacity is None or area is None:
        raise ValueError("Changed Penta Infra facility metric-card shape")

    def decimal(value: str) -> float:
        return float(value.replace(".", "").replace(",", "."))

    capacity_value = decimal(capacity.group(1))
    if capacity.group(2) == "kW":
        capacity_value /= 1000
    candidate: dict[str, Any] = {
        "external_id": expected_code,
        "it_capacity_mw": capacity_value,
        "it_capacity_is_planned": bool(capacity.group(3)),
        "technical_area_m2": decimal(area.group(1)),
        "locator": f"current {expected_code} page / IT capacity and IT space cards",
    }
    future_markers = {
        "AMS01": ("currently being developed", "Ready for service planned in H1-2026"),
        "CPH01": (
            "planned IT capacity of 7,6 MW",
            "expansion will lead into CPH02 and eventually CPH03",
        ),
        "DUS01": (
            "up to 9,5 planned MW of IT capacity",
            "Düsseldorf data center campus",
        ),
        "LEJ01": ("expanded into a data center campus together with Penta Infra LEJ02",),
        "PAR01": ("IT capacity potential of 15+ MW",),
    }
    if expected_code in future_markers:
        if not all(marker in text for marker in future_markers[expected_code]):
            raise ValueError(f"Changed Penta Infra {expected_code} future-scope shape")
        candidate["future_scope_markers"] = list(future_markers[expected_code])
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": candidate,
        "review_required": True,
    }


def parse_bulk_infrastructure_directory(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the exact three sites displayed in Bulk's current directory."""
    if urlsplit(source_url).hostname not in {
        "bulkinfrastructure.com",
        "www.bulkinfrastructure.com",
    }:
        raise ValueError("Expected official Bulk Infrastructure URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    expected = (
        ("OS-IX", "Oslo Internet Exchange - OS-IX", "14 MW colocation"),
        ("N01", "Norway Data Center Campus - N01", "scaling to 1GW"),
        ("DK01", "Denmark Data Center Campus - DK01", "30 MW power secured"),
    )
    positions: list[int] = []
    candidates: list[dict[str, str]] = []
    for code, name, metric in expected:
        position = text.find(name)
        if position < 0 or metric not in text[position : position + 500]:
            raise ValueError(f"Changed Bulk Infrastructure directory card for {code}")
        positions.append(position)
        candidates.append(
            {
                "external_id": code,
                "name": name,
                "reported_power_text": metric,
                "locator": f"current data-center directory card / {code}",
            }
        )
    if positions != sorted(positions) or len(set(positions)) != 3:
        raise ValueError("Changed Bulk Infrastructure directory order or identities")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "review_required": True,
    }


def parse_bulk_infrastructure_site_page(
    content: bytes, *, source_url: str, expected_code: str
) -> dict[str, Any]:
    """Stage bounded public site facts without classifying generic power claims."""
    if urlsplit(source_url).hostname not in {
        "bulkinfrastructure.com",
        "www.bulkinfrastructure.com",
    }:
        raise ValueError("Expected official Bulk Infrastructure URL")
    if expected_code not in {"OS-IX", "N01", "DK01"}:
        raise ValueError("Expected an exact Bulk Infrastructure site code")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    markers = {
        "OS-IX": (
            "Opened in 2014",
            "14MW of 2N redundant predominately renewable power",
        ),
        "N01": (
            "300-hectare (3km²) site",
            "up to 1GW power",
            "125MVA high-voltage primary substations",
        ),
        "DK01": (
            "Located in Esbjerg",
            "up to 2,300m² of white space",
        ),
    }
    if not all(marker in text for marker in markers[expected_code]):
        raise ValueError(f"Changed Bulk Infrastructure {expected_code} page shape")
    candidate: dict[str, Any] = {
        "external_id": expected_code,
        "locator": f"current {expected_code} public site page",
    }
    if expected_code == "OS-IX":
        candidate.update(opened_year=2014, reported_unclassified_power_mw=14.0)
    elif expected_code == "N01":
        candidate.update(
            campus_land_hectares=300.0,
            reported_unclassified_power_mw=1000.0,
            substation_apparent_power_mva=125.0,
        )
    else:
        candidate["technical_area_m2"] = 2300.0
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": candidate,
        "review_required": True,
    }


def parse_bulk_infrastructure_n01_expansion(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the dated N01 facility-expansion claims as observations only."""
    if urlsplit(source_url).hostname not in {
        "bulkinfrastructure.com",
        "www.bulkinfrastructure.com",
    }:
        raise ValueError("Expected official Bulk Infrastructure URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    markers = (
        "23rd January, 2024",
        "new 42MW data center facility",
        "42MW of IT space",
        "12MW data center facility",
        "ready for service in 2023",
        "300MW of additional, redundant power capacity",
        "grow beyond 1000MW",
    )
    if not all(marker in text for marker in markers):
        raise ValueError("Changed Bulk Infrastructure N01 expansion release shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "publication_date": "2024-01-23",
            "existing_facility_mw": 12.0,
            "existing_facility_ready_year": 2023,
            "expansion_it_space_mw": 42.0,
            "expansion_target_year": 2024,
            "future_power_mw": 300.0,
            "campus_power_potential_mw": 1000.0,
            "locator": "dated 2024 N01 expansion announcement",
        },
        "review_required": True,
    }


def parse_bulk_infrastructure_operations(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Verify the operator's current three-campus operating statement."""
    if urlsplit(source_url).hostname not in {
        "bulkinfrastructure.com",
        "www.bulkinfrastructure.com",
    }:
        raise ValueError("Expected official Bulk Infrastructure URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    marker = (
        "Operating three campuses across the Norway and Denmark \N{EN DASH} N01 data center "
        "campus in Kristiansand, DK01 data center campus in Esbjerg and OS-IX in Oslo"
    )
    if marker not in text:
        raise ValueError("Changed Bulk Infrastructure operating-portfolio statement")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "operating_codes": ["N01", "DK01", "OS-IX"],
        "review_required": True,
    }


def parse_green_mountain_facility_page(
    content: bytes, *, source_url: str, expected_code: str | None = None
) -> dict[str, Any]:
    """Stage bounded public design facts from one Green Mountain site page."""
    if urlsplit(source_url).hostname not in {"greenmountain.no", "www.greenmountain.no"}:
        raise ValueError("Expected official Green Mountain URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    codes = [
        code
        for code in (
            "SVG-Rennesøy",
            "TEL-Rjukan",
            "OSL-Enebakk",
            "OSL-Hamar",
            "LON-East",
            "FRA-Mainz",
            "SVG-Undheim",
        )
        if re.search(rf"Data Centers\s+{re.escape(code)}\b", text)
    ]
    if len(codes) != 1:
        raise ValueError("Changed Green Mountain site identity shape")
    code = codes[0]
    if expected_code is not None and code != expected_code:
        raise ValueError("Changed Green Mountain site identity")

    def number(pattern: str, label: str) -> float | None:
        values: list[float] = []
        for match in re.findall(pattern, text, re.IGNORECASE):
            token = match.replace(" ", "").replace(",", "")
            if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", token):
                token = token.replace(".", "")
            value = float(token)
            if value not in values:
                values.append(value)
        if len(values) > 1:
            raise ValueError(f"Changed Green Mountain {label} shape")
        return values[0] if values else None

    candidate: dict[str, Any] = {
        "external_id": code,
        "campus_area_m2": number(
            r"(\d(?:[\d .]*\d)?)\s*m2\s+Total Campus Footprint", "campus-area"
        ),
        "total_it_capacity_mw": number(r"([\d.]+)\s*MW\s+Total IT Capacity", "total-IT-capacity"),
        "potential_site_capacity_mw": number(
            r"([\d.]+)\s*MW\s+Potential Site Capacity", "potential-site-capacity"
        ),
        "total_site_capacity_mw": number(
            r"([\d.]+)\s*MW\s+Total Site Capacity", "total-site-capacity"
        ),
        "secured_power_capacity_mw": number(
            r"([\d.]+)\s*MW\s+Secured Power Capacity", "secured-power"
        ),
        "power_capacity_mw": number(r"([\d.]+)\s*MW\s+Power Capacity", "power-capacity"),
        "average_pue": number(r"([\d.]+)\s+Average PUE", "average-PUE"),
        "grid_supplies": number(r"([\d.]+)\s+Grid [Ss]upplies", "grid-supplies"),
        "building_count": number(r"([\d.]+)\s+Buildings\s+Campus Size", "buildings"),
        "it_space_m2": number(r"Power Capacity\s+(\d(?:[\d .]*\d)?)\s*m2\s+IT Space", "IT-space"),
        "existing_it_space_m2": number(
            r"(\d(?:[\d .]*\d)?)\s*m2\s+of IT space in existing buildings",
            "existing-IT-space",
        ),
        "planned_it_space_m2": number(
            r"(\d(?:[\d .]*\d)?)\s+IT space in planned buildings", "planned-IT-space"
        ),
        "locator": f"current {code} site page / public metric cards and narrative",
    }
    if code == "TEL-Rjukan":
        if "1 .08\u2013 1.20 Average PUE" not in text or "site consists of 4 buildings" not in text:
            raise ValueError("Changed TEL-Rjukan PUE/building shape")
        candidate.update(
            {
                "average_pue": None,
                "average_pue_min": 1.08,
                "average_pue_max": 1.20,
                "building_count": 4,
            }
        )
    elif code == "OSL-Enebakk":
        markers = (
            "line-of-sight capacity of 94 MW",
            "first 4 MW building was completed in October 2020",
            "new 14,5 MW colocation building was completed",
            "In 2024, another 10 MW building was completed",
        )
        if not all(marker in text for marker in markers):
            raise ValueError("Changed OSL-Enebakk building narrative")
        candidate["building_count"] = 3
    elif code == "OSL-Hamar":
        markers = (
            "initial three buildings are now fully complete and in operation",
            "entire 90 MW capacity",
            "option to expand their capacity to 150 MW",
        )
        if not all(marker in text for marker in markers):
            raise ValueError("Changed OSL-Hamar phase narrative")
        candidate.update({"building_count": 5, "operational_it_capacity_mw": 90.0})
    elif code == "LON-East":
        if (
            "30 MW of new capacity secured" not in text
            or "Maximum cooling capacity: 40 MW" not in text
        ):
            raise ValueError("Changed LON-East capacity narrative")
        candidate.update(
            {
                "existing_space_m2": number(
                    r"(\d(?:[\d .]*\d)?)\s*m2\s+Space in existing building",
                    "existing-space",
                ),
                "construction_space_m2": number(
                    r"(\d(?:[\d .]*\d)?)\s*m2\s+Space currently in construction",
                    "construction-space",
                ),
                "new_secured_capacity_mw": 30.0,
                "maximum_cooling_capacity_mw": 40.0,
            }
        )
    elif code == "FRA-Mainz":
        markers = (
            "new 54 MW data center site in Mainz",
            "three planned data center buildings",
            "Ready for service: Q4 2026",
            "Power Capacity: 54 MW (80 MW in 2026)",
        )
        if not all(marker in text for marker in markers):
            raise ValueError("Changed FRA-Mainz construction/capacity narrative")
        candidate.update({"future_power_capacity_mw": 80.0, "building_count": 3})
    elif code == "SVG-Undheim":
        markers = (
            "two interconnected data center buildings",
            "total IT capacity of 80 MW",
            "Construction is currently underway",
            "full completion scheduled for 2028",
        )
        if not all(marker in text for marker in markers):
            raise ValueError("Changed SVG-Undheim construction/capacity narrative")
        candidate.update({"total_it_capacity_mw": 80.0, "building_count": 2})
    elif code == "SVG-Rennesøy":
        if "Build Year: 2013" not in text or "6 mountain halls" not in text:
            raise ValueError("Changed SVG-Rennesøy facility narrative")
        candidate["building_count"] = 6
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": candidate,
        "review_required": True,
    }


def parse_maincubes_directory(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the complete current maincubes directory identity set.

    Directory capacity cards establish only a reported number or range. They do
    not establish an IT boundary; exact facility pages are reviewed separately
    before any scalar is normalized.
    """
    if urlsplit(source_url).hostname not in {"maincubes.com", "www.maincubes.com"}:
        raise ValueError("Expected official maincubes URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    expected = {
        "FRA05": "Pipeline",
        "FRA04": "In Planning",
        "FRA03": "In Operation",
        "FRA02": "In Operation",
        "FRA01": "In Operation",
        "BER02": "Construction",
        "BER01": "In Operation",
        "AMS01": "In Operation",
    }
    candidates = []
    for code, status in expected.items():
        pattern = (
            rf"\b{code}\s+{re.escape(status)}\s+"
            rf"(?:Hyperscale & HPC|Government-Leased|Colocation(?:/OCP Ready™)?)\s+"
            rf"(\d+(?:[\u2013-]\d+)?)\s+MW\s+Capacity(?:\s+\(N\+1\))?"
        )
        values = list(dict.fromkeys(re.findall(pattern, text)))
        if len(values) != 1:
            raise ValueError(f"Changed maincubes directory row for {code}")
        bounds = [float(value) for value in re.split(r"[\u2013-]", values[0])]
        candidates.append(
            {
                "external_id": code,
                "status_label": status,
                "reported_capacity_min_mw": bounds[0],
                "reported_capacity_max_mw": bounds[-1],
                "locator": f"current directory card / {code}",
            }
        )
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "review_required": True,
    }


def parse_maincubes_site_page(
    content: bytes, *, source_url: str, expected_code: str
) -> dict[str, Any]:
    """Stage explicit IT-capacity and IT-area facts from one maincubes page."""
    if urlsplit(source_url).hostname not in {"maincubes.com", "www.maincubes.com"}:
        raise ValueError("Expected official maincubes URL")
    if expected_code not in {"AMS01", "FRA01", "FRA02", "BER01", "FRA03", "FRA04", "BER02"}:
        raise ValueError("Unexpected maincubes site code")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    spaced_code = f"{expected_code[:3]} {expected_code[3:]}"
    if expected_code not in text and spaced_code not in text:
        raise ValueError("Changed maincubes site identity")
    status_labels = {
        "AMS01": "In Operation",
        "FRA01": "In Operation",
        "FRA02": "In Operation",
        "BER01": "In Operation",
        "FRA03": "In Operation",
        "FRA04": "In Planning",
        "BER02": "Construction",
    }
    status = status_labels[expected_code]
    if status not in text:
        raise ValueError("Changed maincubes site lifecycle")

    capacity_tokens: list[str] = []
    for pattern in (
        r"IT capacity:\s*(\d+(?:[\u2013-]\d+)?)\s*MW",
        r"(\d+(?:[\u2013-]\d+)?)\s*MW\s+IT [Cc]apacity",
    ):
        capacity_tokens.extend(re.findall(pattern, text))
    capacity_tokens = list(dict.fromkeys(capacity_tokens))
    if len(capacity_tokens) != 1:
        raise ValueError("Changed maincubes IT-capacity shape")
    capacity_bounds = [float(value) for value in re.split(r"[\u2013-]", capacity_tokens[0])]

    area_tokens = list(
        dict.fromkeys(re.findall(r"IT area:\s*(\d[\d,]*(?:[\u2013-]\d[\d,]*)?)\s*m²", text))
    )
    if len(area_tokens) != 1:
        raise ValueError("Changed maincubes IT-area shape")
    area_bounds = [
        float(value.replace(",", "")) for value in re.split(r"[\u2013-]", area_tokens[0])
    ]
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "external_id": expected_code,
            "status_label": status,
            "it_capacity_min_mw": capacity_bounds[0],
            "it_capacity_max_mw": capacity_bounds[-1],
            "technical_area_min_m2": area_bounds[0],
            "technical_area_max_m2": area_bounds[-1],
            "locator": f"current {expected_code} page / IT capacity and IT area",
        },
        "review_required": True,
    }


class _DatacenterUnitedCards(HTMLParser):
    """Collect only explicit directory-card attributes, never map/contact data."""

    def __init__(self) -> None:
        super().__init__()
        self.cards: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("data-name"):
            self.cards.append(
                {
                    "name": values["data-name"] or "",
                    "description": values.get("data-description") or "",
                    "path": values.get("data-url") or "",
                }
            )


def parse_datacenter_united_directory(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the exact 14 facility identities displayed in the current directory."""
    if urlsplit(source_url).hostname not in {
        "datacenterunited.com",
        "www.datacenterunited.com",
    }:
        raise ValueError("Expected official Datacenter United URL")
    parser = _DatacenterUnitedCards()
    parser.feed(content.decode("utf-8-sig"))
    expected = [
        "DC Antwerp 1",
        "DC Antwerp 2",
        "DC Antwerp 3",
        "DC Burcht",
        "DC Mechelen",
        "DC Evere 1",
        "DC Evere 2",
        "DC Brussels",
        "DC Machelen",
        "DC Ghent",
        "DC Ghent 2",
        "DC Hasselt 1",
        "DC Oostkamp",
        "DC Mouscron",
    ]
    cards = [card for card in parser.cards if card["name"] in expected]
    if [card["name"] for card in cards] != expected:
        raise ValueError("Changed Datacenter United directory identity set")
    if cards[10]["description"].strip().lower() != "under construction":
        raise ValueError("Changed Datacenter United Ghent 2 lifecycle")
    for card in cards:
        card.update(
            {
                "external_id": card.pop("name"),
                "status_label": (
                    "under_construction"
                    if card["description"].strip().lower() == "under construction"
                    else "operational"
                ),
                "locator": f"current directory card / {card.get('external_id', '')}",
            }
        )
        card["locator"] = f"current directory card / {card['external_id']}"
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": cards,
        "review_required": True,
    }


def parse_datacenter_united_site_page(
    content: bytes, *, source_url: str, expected_group: str
) -> dict[str, Any]:
    """Fail closed on grouped facility identity and construction markers."""
    if urlsplit(source_url).hostname not in {
        "datacenterunited.com",
        "www.datacenterunited.com",
    }:
        raise ValueError("Expected official Datacenter United URL")
    markers = {
        "antwerp": ("DC Antwerp", "ANTW1 and ANTW2"),
        "flanders": ("DC Flanders",),
        "evere": ("DC Evere",),
        "ghent": ("DC Ghent", "Coming : Ghent 2"),
        "mouscron": ("DC Mouscron", "currently under development"),
    }
    if expected_group not in markers:
        raise ValueError("Unexpected Datacenter United site group")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split()).replace("&", "and")
    if not all(marker in text for marker in markers[expected_group]):
        raise ValueError("Changed Datacenter United site identity or lifecycle")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "group": expected_group,
            "locator": f"current {expected_group} facility page",
        },
        "review_required": True,
    }


def parse_rack_centre_campus(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage Rack Centre's explicit two-building Lagos campus boundary.

    Campus totals are returned separately from the two named facilities. Callers
    must keep the campus aggregate excluded from capacity totals and must not use
    the published total to fill either building.
    """
    if urlsplit(source_url).hostname not in {"rack-centre.com", "www.rack-centre.com"}:
        raise ValueError("Expected official Rack Centre URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    markers = (
        "Two facilities. One connected campus.",
        "Rack Centre LGS 1",
        "Rack Centre LGS 2",
        "13.5 MW total IT power",
        "7,200 sqm net lettable space",
        "6 data halls",
        "White space 3,240 sqm",
    )
    if not all(marker in text for marker in markers):
        raise ValueError("Changed Rack Centre campus identity or capacity shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "external_id": "Lagos Campus",
            "facility_codes": ["LGS1", "LGS2"],
            "it_capacity_mw": 13.5,
            "technical_area_m2": 7200.0,
            "lgs2_white_space_m2": 3240.0,
            "locator": "current Lagos campus page / campus buildings and specifications",
        },
        "review_required": True,
    }


def parse_rack_centre_facility_page(
    content: bytes, *, source_url: str, expected_code: str
) -> dict[str, Any]:
    """Stage exact Rack Centre LGS1/LGS2 IT ratings without merging areas."""
    if urlsplit(source_url).hostname not in {"rack-centre.com", "www.rack-centre.com"}:
        raise ValueError("Expected official Rack Centre URL")
    if expected_code not in {"LGS1", "LGS2"}:
        raise ValueError("Unexpected Rack Centre facility code")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    if f"Rack Centre {expected_code[:3]} {expected_code[3:]}" not in text:
        raise ValueError("Changed Rack Centre facility identity")
    if expected_code == "LGS1":
        markers = (
            "1.5MW I.T Load",
            "Tier III TCCF Constructed facility certified",
            "WHITE SPACE 1,094 SQM",
            "100% Uptime Since 2013",
        )
        if not all(marker in text for marker in markers):
            raise ValueError("Changed Rack Centre LGS1 specification shape")
        candidate = {
            "external_id": expected_code,
            "it_capacity_mw": 1.5,
            "technical_area_m2": 1094.0,
            "status_year": 2013,
            "locator": "current LGS1 page / data center specifications",
        }
    else:
        markers = (
            "IT POWER CAPACITY 12 MW",
            "Utility Power Supply Capacity of 25mva",
            "WHITE SPACE 7200 Sqm.",
            "6 Data Halls each of 2 MW IT Load",
        )
        if not all(marker in text for marker in markers):
            raise ValueError("Changed Rack Centre LGS2 specification shape")
        candidate = {
            "external_id": expected_code,
            "it_capacity_mw": 12.0,
            "reported_white_space_m2": 7200.0,
            "utility_apparent_power_mva": 25.0,
            "data_hall_count": 6,
            "locator": "current LGS2 page / data center specifications",
        }
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": candidate,
        "review_required": True,
    }


def parse_rack_centre_lgs2_commissioning(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage the exact dated LGS2 commissioning event and reported IT load."""
    if urlsplit(source_url).hostname not in {"rack-centre.com", "www.rack-centre.com"}:
        raise ValueError("Expected official Rack Centre URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split()).replace("\N{RIGHT SINGLE QUOTATION MARK}", "'")
    markers = (
        "Rack Centre's LGS2 12MW Data Centre Commissioned",
        "commissioning of the data centre held",
        "Thursday, April 10, 2025",
        "12MW IT load LGS2",
    )
    if not all(marker in text for marker in markers):
        raise ValueError("Changed Rack Centre LGS2 commissioning evidence")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "external_id": "LGS2",
            "commissioning_date": "2025-04-10",
            "it_capacity_mw": 12.0,
            "locator": "commissioning article / event date and 12 MW IT load",
        },
        "review_required": True,
    }


def parse_uptime_rack_centre_story(content: bytes, *, source_url: str) -> dict[str, Any]:
    """Stage issuer evidence for the original Rack Centre Lagos facility.

    The issuer story predates LGS2 and identifies the original facility's launch
    and award months. It does not establish any certification for LGS2.
    """
    if urlsplit(source_url).hostname not in {"uptimeinstitute.com", "www.uptimeinstitute.com"}:
        raise ValueError("Expected official Uptime Institute URL")
    parser = _VisibleText()
    parser.feed(content.decode("utf-8-sig"))
    text = " ".join(" ".join(parser.parts).split())
    markers = (
        "Client Story: Rack Centre Tier III Certification of Constructed Facility",
        "Tier Certification of Design Documents in May, 2014",
        "Tier Certification of Constructed Facility in April, 2017",
        "launch of the company in October, 2013",
    )
    if not all(marker in text for marker in markers):
        raise ValueError("Changed Uptime Rack Centre issuer evidence")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidate": {
            "issuer": "Uptime Institute",
            "issuer_identity": "Rack Centre Lagos Data Centre",
            "tier": "Tier III",
            "awards": [
                {
                    "award": "Tier Certification of Design Documents",
                    "date_precision": "month",
                    "date": "2014-05",
                },
                {
                    "award": "Tier Certification of Constructed Facility",
                    "date_precision": "month",
                    "date": "2017-04",
                },
            ],
            "launch_period": "2013-10",
            "locator": "issuer client story / certification and launch chronology",
        },
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


_CARRIER_19DV_ROW = re.compile(
    r"^(19DV-\S+)\s+([\d,]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)\s+"
    r"([\d.]+)\s+([\d,]+)\s+([\d.]+)\s+([\d.]+)\s+(DN\d+)\s+"
    r"([\d.]+)\s+([\d.]+)\s+(DN\d+)\s+([\d,]+)\s+([\d,]+)\s+"
    r"([\d,]+)\s+([\d,]+)\s+([\d,]+)\s+([\d,]+)\s*$",
    re.MULTILINE,
)


def parse_carrier_19dv_table(
    content: bytes, *, source_url: str, expected_count: int | None = None
) -> dict[str, Any]:
    """Stage exact Carrier AquaEdge 19DV table configurations.

    Each row is an explicitly documented model at either 400 V/50 Hz or
    380 V/60 Hz. Cooling, input power and COP/IPLV observations retain the
    shared AHRI water-temperature and fouling-factor rating conditions.
    """
    host = urlsplit(source_url).hostname or ""
    if not (host.endswith("carrier.com") or host.endswith("carrier.com.cn")):
        raise ValueError("Expected official Carrier URL")
    text = content.decode("utf-8-sig")
    required_markers = (
        "19DV\nCENTRIFUGAL CHILLER",
        "Air-conditioning (400V-3ph-50Hz)",
        "Air-conditioning (380V-3ph-60Hz)",
        "standard AHRI condition",
    )
    if not all(marker in text for marker in required_markers):
        raise ValueError("Missing Carrier 19DV table or rating conditions")

    def number(value: str) -> float:
        return float(value.replace(",", ""))

    candidates: list[dict[str, Any]] = []
    for match in _CARRIER_19DV_ROW.finditer(text):
        values = match.groups()
        model = values[0]
        if model.endswith("9"):
            voltage_v, frequency_hz = 400, 50
        elif model.endswith("3"):
            voltage_v, frequency_hz = 380, 60
        else:
            raise ValueError("Unrecognized Carrier 19DV electrical configuration")
        candidates.append(
            {
                "model": model,
                "variant": f"{voltage_v} V; 3 phase; {frequency_hz} Hz",
                "cooling_capacity_kw": number(values[1]),
                "cooling_capacity_tons": number(values[2]),
                "input_power_kw": number(values[3]),
                "full_load_cop": number(values[4]),
                "iplv_ip": number(values[5]),
                "input_current_a": number(values[6]),
                "evaporator_flow_l_s": number(values[7]),
                "evaporator_pressure_drop_kpa": number(values[8]),
                "evaporator_connection": values[9],
                "condenser_flow_l_s": number(values[10]),
                "condenser_pressure_drop_kpa": number(values[11]),
                "condenser_connection": values[12],
                "length_mm": number(values[13]),
                "width_mm": number(values[14]),
                "height_mm": number(values[15]),
                "operating_weight_kg": number(values[16]),
                "rigging_weight_kg": number(values[17]),
                "refrigerant_charge_kg": number(values[18]),
                "input_voltage_v": voltage_v,
                "frequency_hz": frequency_hz,
                "locator": (f"Air-conditioning ({voltage_v}V-3ph-{frequency_hz}Hz) / {model}"),
            }
        )
    identities = [row["model"] for row in candidates]
    if (
        not candidates
        or len(identities) != len(set(identities))
        or (expected_count is not None and len(candidates) != expected_count)
    ):
        raise ValueError("Changed Carrier 19DV table shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "shared_conditions": {
            "leaving_evaporator_water_c": 6.7,
            "entering_evaporator_water_c": 12.2,
            "entering_condenser_water_c": 29.4,
            "leaving_condenser_water_c": 34.6,
            "evaporator_fouling_m2_k_kw": 0.0180,
            "condenser_fouling_m2_k_kw": 0.0440,
            "water_side_design_pressure_mpa": 1.0,
            "evaporator_and_condenser_passes": 2,
            "refrigerant": "R-1233zd(E)",
            "communications": ["BACnet", "Modbus"],
        },
        "review_required": True,
    }


class _HtmlTables(HTMLParser):
    """Collect visible table cells without presentation markup."""

    def __init__(self) -> None:
        super().__init__()
        self.table_depth = 0
        self.row: list[str] | None = None
        self.cell_parts: list[str] | None = None
        self.tables: list[list[list[str]]] = []
        self.current_table: list[list[str]] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self.table_depth += 1
            if self.table_depth == 1:
                self.current_table = []
        elif self.table_depth == 1 and tag == "tr":
            self.row = []
        elif self.table_depth == 1 and tag in {"th", "td"} and self.row is not None:
            self.cell_parts = []

    def handle_data(self, data: str) -> None:
        if self.cell_parts is not None:
            self.cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"th", "td"} and self.cell_parts is not None and self.row is not None:
            self.row.append(" ".join(" ".join(self.cell_parts).split()))
            self.cell_parts = None
        elif tag == "tr" and self.row is not None and self.current_table is not None:
            if self.row:
                self.current_table.append(self.row)
            self.row = None
        elif tag == "table" and self.table_depth:
            self.table_depth -= 1
            if self.table_depth == 0 and self.current_table:
                self.tables.append(self.current_table)
                self.current_table = None


def _kw_kva(value: str) -> tuple[float, float] | None:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)", value.strip())
    return (float(match[1]), float(match[2])) if match else None


def parse_cummins_generator_table(
    content: bytes,
    *,
    source_url: str,
    expected_count: int | None = None,
) -> dict[str, Any]:
    """Stage exact Cummins rows with a Data Center Continuous rating.

    Duplicate live-page rows are reconciled only when values agree. Differing
    prime, standby or continuous ratings are returned as conflicts; the
    independently consistent DCC kW/kVA pair is never calculated.
    """
    if urlsplit(source_url).hostname != "www.cummins.com":
        raise ValueError("Expected official Cummins URL")
    parser = _HtmlTables()
    parser.feed(content.decode("utf-8-sig"))
    tables = [
        table
        for table in parser.tables
        if table
        and table[0]
        and table[0][0].casefold() == "generator model"
        and "Data Center Continuous kW / kVA" in table[0]
    ]
    if len(tables) != 1:
        raise ValueError("Expected one Cummins generator model table")
    header, *raw_rows = tables[0]
    grouped: dict[tuple[str, float], list[dict[str, str]]] = {}
    for values in raw_rows:
        if len(values) != len(header):
            continue
        row = dict(zip(header, values, strict=True))
        dcc = _kw_kva(row["Data Center Continuous kW / kVA"])
        if dcc is None or not row["generator model"] or not row["Hz"]:
            continue
        try:
            frequency_hz = float(row["Hz"])
        except ValueError as exc:
            raise ValueError("Invalid Cummins frequency") from exc
        grouped.setdefault((row["generator model"], frequency_hz), []).append(row)

    candidates = []
    rating_columns = {
        "prime": "Prime kW / kVA",
        "standby": "Standby kW / kVA",
        "continuous": "Continuous kW / kVA",
        "data_center_continuous": "Data Center Continuous kW / kVA",
    }
    for (model, frequency_hz), rows in grouped.items():
        ratings: dict[str, list[dict[str, float | str]]] = {}
        conflicts: dict[str, list[dict[str, float | str]]] = {}
        for key, column in rating_columns.items():
            parsed_values = {_kw_kva(row.get(column, "")) for row in rows}
            values = sorted(value for value in parsed_values if value is not None)
            payload: list[dict[str, float | str]] = [
                {"kw": value[0], "kva": value[1]} for value in values
            ]
            if len(payload) > 1:
                conflicts[f"{key}_rating"] = payload
            elif payload:
                ratings[key] = payload
        dcc = ratings.get("data_center_continuous")
        if dcc is None or conflicts.get("data_center_continuous_rating"):
            raise ValueError("Conflicting Cummins Data Center Continuous rating")
        engine_models = sorted({row.get("engine model", "") for row in rows} - {""})
        if len(engine_models) > 1:
            conflicts["engine_model"] = [{"value": value} for value in engine_models]
        candidates.append(
            {
                "model": model,
                "frequency_hz": frequency_hz,
                "fuel_type": "Diesel",
                "data_center_continuous_kw": dcc[0]["kw"],
                "data_center_continuous_kva": dcc[0]["kva"],
                "ratings": ratings,
                "engine_model": engine_models[0] if len(engine_models) == 1 else None,
                "conflicts": conflicts,
                "locator": f"generator model table / {model} / {frequency_hz:g} Hz",
            }
        )
    identities = [(row["model"], row["frequency_hz"]) for row in candidates]
    if (
        not candidates
        or len(identities) != len(set(identities))
        or (expected_count is not None and len(candidates) != expected_count)
    ):
        raise ValueError("Changed Cummins generator table shape")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "candidates": candidates,
        "review_required": True,
    }
