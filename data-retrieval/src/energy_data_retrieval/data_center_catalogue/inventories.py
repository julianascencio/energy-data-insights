"""Offline staging for bounded official operator and equipment inventories.

Only named inventory links are retained. Detail-page specifications, lifecycle,
capacity boundaries and reuse conditions still require review before import.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
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


class _TableRows(HTMLParser):
    """Collect visible table-cell text while ignoring page chrome."""

    def __init__(self) -> None:
        super().__init__()
        self.in_row = False
        self.in_cell = False
        self.cell_parts: list[str] = []
        self.row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag == "tr":
            self.in_row = True
            self.row = []
        elif self.in_row and tag in {"th", "td"}:
            self.in_cell = True
            self.cell_parts = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.cell_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.in_cell and tag in {"th", "td"}:
            self.row.append(" ".join(" ".join(self.cell_parts).split()))
            self.in_cell = False
            self.cell_parts = []
        elif self.in_row and tag == "tr":
            if self.row:
                self.rows.append(self.row)
            self.in_row = False
            self.row = []


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


def parse_power_equipment_matrix(
    content: bytes, *, source_url: str, expected_count: int
) -> dict[str, Any]:
    """Stage exact transformer/switchgear table rows for manual review.

    Maximum voltage/current values remain limits rather than nominal inputs,
    and transformer kVA is never converted to active kW.
    """
    host = urlsplit(source_url).hostname
    if host not in {"www.eaton.com", "www.siemens.com"}:
        raise ValueError("Unsupported official power-equipment source URL")
    if expected_count < 1:
        raise ValueError("Positive expected count required")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    required = {"category", "manufacturer", "model", "variant", "locator"}
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise ValueError("Missing power-equipment matrix columns")
    candidates: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    numeric = {
        "apparent_power_kva",
        "max_voltage_kv",
        "max_short_circuit_ka",
        "max_current_a",
        "weight_kg",
    }
    for line, row in enumerate(reader, start=2):
        candidate = {key: (row.get(key) or "").strip() for key in required}
        if candidate["category"] not in {"transformer", "switchgear"}:
            raise ValueError(f"Unsupported power-equipment category on row {line}")
        if not all(candidate.values()):
            raise ValueError(f"Incomplete power-equipment row {line}")
        for field in numeric:
            raw = (row.get(field) or "").strip()
            if not raw:
                candidate[field] = None
                continue
            try:
                value = float(raw)
            except ValueError as exc:
                raise ValueError(f"Invalid {field} on row {line}") from exc
            if value <= 0:
                raise ValueError(f"Invalid {field} on row {line}")
            candidate[field] = value
        identity: tuple[str, str, str, str] = (
            candidate["category"],
            candidate["manufacturer"],
            candidate["model"],
            candidate["variant"],
        )
        if identity in candidates:
            raise ValueError(f"Duplicate power-equipment row for {identity}")
        candidates[identity] = candidate
    if len(candidates) != expected_count:
        raise ValueError(
            f"Changed power-equipment matrix shape: {len(candidates)} != {expected_count}"
        )
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_required": True,
        "candidates": [candidates[key] for key in sorted(candidates)],
    }


def parse_server_accelerator_matrix(
    content: bytes, *, source_url: str, expected_count: int
) -> dict[str, Any]:
    """Stage explicit OEM server/accelerator compatibility rows for review.

    The adapter accepts only rows which the OEM marks supported. Accelerator
    power remains a per-device limit and is never promoted to server or rack
    input. A range can be retained in ``max_power_text`` while the normalized
    scalar stays null.
    """
    host = urlsplit(source_url).hostname
    if host not in {"www.dell.com", "www.delltechnologies.com"}:
        raise ValueError("Unsupported official server-matrix source URL")
    if expected_count < 1:
        raise ValueError("Positive expected count required")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    required = {
        "manufacturer",
        "server_model",
        "accelerator_vendor",
        "accelerator_model",
        "compatibility",
        "max_power_text",
        "locator",
    }
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise ValueError("Missing server/accelerator matrix columns")
    candidates: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for line, row in enumerate(reader, start=2):
        candidate = {key: (row.get(key) or "").strip() for key in required}
        if not all(candidate.values()):
            raise ValueError(f"Incomplete server/accelerator row {line}")
        if candidate["manufacturer"] != "Dell":
            raise ValueError(f"Unexpected server manufacturer on row {line}")
        if candidate["compatibility"].casefold() != "supported":
            raise ValueError(f"Unverified compatibility on row {line}")
        raw_power = (row.get("max_power_w") or "").strip()
        if raw_power:
            try:
                power = float(raw_power)
            except ValueError as exc:
                raise ValueError(f"Invalid accelerator power on row {line}") from exc
            if power <= 0:
                raise ValueError(f"Invalid accelerator power on row {line}")
            candidate["max_power_w"] = power
        else:
            candidate["max_power_w"] = None
        generation = (row.get("server_generation") or "").strip()
        if generation:
            candidate["server_generation"] = generation
        identity = (
            candidate["manufacturer"],
            candidate["server_model"],
            candidate["accelerator_model"],
            generation,
        )
        if identity in candidates:
            raise ValueError(f"Duplicate server/accelerator row for {identity}")
        candidates[identity] = candidate
    if len(candidates) != expected_count:
        raise ValueError(
            f"Changed server/accelerator matrix shape: {len(candidates)} != {expected_count}"
        )
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_required": True,
        "candidates": [candidates[key] for key in sorted(candidates)],
    }


def parse_server_accelerator_shipping_matrix(
    content: bytes, *, source_url: str, expected_count: int
) -> dict[str, Any]:
    """Stage OEM shipping rows without treating maxima as installed counts.

    Blank quantities remain null. Parenthesized quantities are retained only as
    configuration-dependent OEM maxima; callers must not promote them to an
    installed accelerator count or multiply them into server/rack power.
    """
    host = urlsplit(source_url).hostname
    if host not in {"www.dell.com", "www.delltechnologies.com"}:
        raise ValueError("Unsupported official server-shipping source URL")
    if expected_count < 1:
        raise ValueError("Positive expected count required")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    required = {
        "manufacturer",
        "server_generation",
        "server_model",
        "accelerator_vendor",
        "accelerator_model",
        "shipping_status",
        "max_shipping_quantity",
        "locator",
    }
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise ValueError("Missing server/accelerator shipping columns")
    candidates: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for line, row in enumerate(reader, start=2):
        candidate = {key: (row.get(key) or "").strip() for key in required}
        if not all(candidate[key] for key in required - {"max_shipping_quantity"}):
            raise ValueError(f"Incomplete server/accelerator shipping row {line}")
        if candidate["manufacturer"] != "Dell":
            raise ValueError(f"Unexpected server manufacturer on row {line}")
        if candidate["shipping_status"].casefold() != "shipping":
            raise ValueError(f"Unverified shipping status on row {line}")
        raw_quantity = candidate.pop("max_shipping_quantity")
        if raw_quantity:
            try:
                quantity = int(raw_quantity)
            except ValueError as exc:
                raise ValueError(f"Invalid maximum shipping quantity on row {line}") from exc
            if quantity <= 0:
                raise ValueError(f"Invalid maximum shipping quantity on row {line}")
            candidate["max_shipping_quantity"] = quantity
        else:
            candidate["max_shipping_quantity"] = None
        identity = (
            candidate["server_generation"],
            candidate["server_model"],
            candidate["accelerator_vendor"],
            candidate["accelerator_model"],
        )
        if identity in candidates:
            raise ValueError(f"Duplicate server/accelerator shipping row for {identity}")
        candidates[identity] = candidate
    if len(candidates) != expected_count:
        raise ValueError(
            f"Changed server/accelerator shipping shape: {len(candidates)} != {expected_count}"
        )
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_required": True,
        "candidates": [candidates[key] for key in sorted(candidates)],
    }


def parse_generator_rating_matrix(
    content: bytes, *, source_url: str, expected_count: int
) -> dict[str, Any]:
    """Stage exact OEM generator rating rows without converting kVA to kW.

    The extracted matrix must retain one source row per model/frequency pair.
    Rows without an explicit Data Center Continuous rating are not candidates;
    omission decisions remain in the research ledger. Portfolio voltage lists,
    duty claims and other shared conditions remain observations during review.
    """
    parsed_url = urlsplit(source_url)
    if (
        parsed_url.scheme != "https"
        or parsed_url.hostname != "www.mtu-solutions.com"
        or not parsed_url.path.endswith(".pdf")
    ):
        raise ValueError("Unsupported official generator matrix URL")
    if expected_count < 1:
        raise ValueError("Positive expected count required")
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    required = {
        "model",
        "frequency_hz",
        "speed_rpm",
        "standby_kva",
        "prime_emergency_kva",
        "data_center_continuous_kva",
        "prime_kva",
        "locator",
    }
    if reader.fieldnames is None or set(reader.fieldnames) != required:
        raise ValueError("Unexpected generator matrix columns")

    def positive_number(
        raw_value: str | None, field: str, *, line: int, required_value: bool
    ) -> float | None:
        raw = (raw_value or "").strip().replace(",", "")
        if not raw:
            if required_value:
                raise ValueError(f"Missing {field} on row {line}")
            return None
        try:
            value = float(raw)
        except ValueError as exc:
            raise ValueError(f"Invalid {field} on row {line}") from exc
        if value <= 0:
            raise ValueError(f"Invalid {field} on row {line}")
        return value

    candidates: dict[tuple[str, float], dict[str, Any]] = {}
    for line, row in enumerate(reader, start=2):
        model = row["model"].strip()
        locator = row["locator"].strip()
        if not model or not locator:
            raise ValueError(f"Incomplete generator identity on row {line}")

        frequency = positive_number(
            row["frequency_hz"], "frequency_hz", line=line, required_value=True
        )
        speed = positive_number(row["speed_rpm"], "speed_rpm", line=line, required_value=True)
        assert frequency is not None and speed is not None
        candidate = {
            "model": model,
            "frequency_hz": frequency,
            "speed_rpm": speed,
            "standby_kva": positive_number(
                row["standby_kva"], "standby_kva", line=line, required_value=True
            ),
            "prime_emergency_kva": positive_number(
                row["prime_emergency_kva"],
                "prime_emergency_kva",
                line=line,
                required_value=False,
            ),
            "data_center_continuous_kva": positive_number(
                row["data_center_continuous_kva"],
                "data_center_continuous_kva",
                line=line,
                required_value=True,
            ),
            "prime_kva": positive_number(
                row["prime_kva"], "prime_kva", line=line, required_value=False
            ),
            "locator": locator,
        }
        identity = (model, frequency)
        if identity in candidates:
            raise ValueError(f"Duplicate generator rating row for {identity}")
        candidates[identity] = candidate
    if len(candidates) != expected_count:
        raise ValueError(f"Changed generator matrix shape: {len(candidates)} != {expected_count}")
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_required": True,
        "candidates": [candidates[key] for key in sorted(candidates)],
    }


def parse_supermicro_nvidia_systems(
    content: bytes, *, source_url: str, expected_count: int
) -> dict[str, Any]:
    """Stage exact current Supermicro HGX B200/B300 system rows.

    The official NVIDIA-certified systems table may list one system more than
    once under different certification states. Those rows collapse only when
    every hardware field agrees, while all distinct certification states are
    retained. Per-GPU power and memory never become server or rack totals.
    """
    parsed_url = urlsplit(source_url)
    if (
        parsed_url.hostname != "www.supermicro.com"
        or parsed_url.scheme != "https"
        or parsed_url.path.rstrip("/") != "/en/accelerators/nvidia-certified-systems"
    ):
        raise ValueError("Unsupported official Supermicro inventory URL")
    if expected_count < 1:
        raise ValueError("Positive expected count required")
    parser = _TableRows()
    parser.feed(content.decode("utf-8-sig"))
    candidates: dict[str, dict[str, Any]] = {}
    for row_number, row in enumerate(parser.rows, start=1):
        if len(row) < 11 or not any(token in row[1] for token in ("B200", "B300")):
            continue
        model = re.sub(r"^(AS)\s+-", r"\1-", row[0].strip())
        if not re.fullmatch(r"(?:ARS|AS|SYS)-[A-Z0-9-]+", model):
            raise ValueError(f"Invalid Supermicro model on table row {row_number}")
        count_match = re.fullmatch(r"(\d+) GPU", row[4])
        power_match = re.fullmatch(r"Configurable up to ([\d,]+)W", row[6])
        memory_match = re.fullmatch(r"([\d.]+)GB (.+)", row[7])
        cpu_count_match = re.fullmatch(r"(\d+) CPUs", row[9])
        if (
            count_match is None
            or power_match is None
            or memory_match is None
            or cpu_count_match is None
        ):
            raise ValueError(f"Incomplete Supermicro rating on table row {row_number}")
        candidate: dict[str, Any] = {
            "model": model,
            "accelerator_model": row[1],
            "cooling_method": row[2] or None,
            "accelerator_form_factor": row[3],
            "accelerator_count": int(count_match.group(1)),
            "integration": row[5],
            "accelerator_power_w_per_gpu": float(power_match.group(1).replace(",", "")),
            "memory_gb_per_gpu": float(memory_match.group(1)),
            "memory_type": memory_match.group(2),
            "cpu_family": row[8],
            "cpu_count": int(cpu_count_match.group(1)),
            "certification_states": [row[10]],
            "locator": f"current NVIDIA-certified systems table row {row_number}",
        }
        previous = candidates.get(model)
        if previous is not None:
            comparable = {
                key: value
                for key, value in candidate.items()
                if key not in {"certification_states", "locator"}
            }
            prior = {
                key: value
                for key, value in previous.items()
                if key not in {"certification_states", "locator"}
            }
            if prior != comparable:
                raise ValueError(f"Conflicting Supermicro rows for {model}")
            previous["certification_states"] = sorted(
                set(previous["certification_states"] + candidate["certification_states"])
            )
            previous["locator"] += f" and {row_number}"
            continue
        candidates[model] = candidate
    if len(candidates) != expected_count:
        raise ValueError(
            f"Changed Supermicro system inventory shape: {len(candidates)} != {expected_count}"
        )
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_required": True,
        "candidates": [candidates[key] for key in sorted(candidates)],
    }


def parse_lenovo_gpu_comparison(
    content: bytes, *, source_url: str, expected_count: int
) -> dict[str, Any]:
    """Stage Lenovo's current GPU-option table from its embedded JSON payload.

    The comparison page contains withdrawn and available products together. Only
    rows explicitly marked ``Available`` are staged. Board GPU count and per-GPU
    TDP remain separate; this adapter never multiplies them into server or rack
    input power. A staged row still requires field-level evidence review before
    canonical publication.
    """
    parsed_url = urlsplit(source_url)
    if parsed_url.hostname != "lenovopress.lenovo.com" or parsed_url.scheme != "https":
        raise ValueError("Unsupported official Lenovo comparison URL")
    if expected_count < 1:
        raise ValueError("Positive expected count required")
    text = content.decode("utf-8-sig")
    anchor = text.find("scrollY: null")
    marker = text.find("data: {", max(anchor, 0))
    if anchor < 0 or marker < 0:
        raise ValueError("Lenovo comparison payload not found")
    start = marker + len("data: ")
    depth = 0
    in_string = False
    escaped = False
    end: int | None = None
    for index, character in enumerate(text[start:], start=start):
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise ValueError("Unterminated Lenovo comparison payload")
    try:
        payload = json.loads(text[start:end])
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid Lenovo comparison payload") from exc
    attributes = {item["label"]: item["id"] for item in payload["attributes"]}
    values = {item["id"]: item.get("val") for item in payload["values"]}
    required = {
        "Description",
        "Form factor ",
        "Number of GPUs (Note 1)",
        "Part number ",
        "Feature code",
        "Announcement date",
        "Availability",
        "GPU Architecture",
        "GPU Memory type",
        "GPU Memory (GB)",
        "Memory Bandwidth GB/s",
        "TDP Max Power Consumption (W)",
        "Cooling method",
    }
    if not required <= set(attributes):
        raise ValueError("Missing Lenovo comparison attributes")

    def value(row: dict[str, Any], label: str) -> Any:
        attribute_id = attributes[label]
        cell = row.get(f"c_{attribute_id}")
        return values.get(cell.get("v_id")) if cell else None

    candidates: dict[str, dict[str, Any]] = {}
    for row in payload["transposed_rows"]:
        if value(row, "Availability") != "Available":
            continue
        feature_code = str(value(row, "Feature code") or "").strip()
        part_number = str(value(row, "Part number ") or "").strip()
        identity = part_number if part_number != "CTO Only" else feature_code
        if not identity or not feature_code:
            raise ValueError("Available Lenovo row lacks an orderable identity")
        try:
            gpu_count = int(value(row, "Number of GPUs (Note 1)"))
            memory_gb = float(value(row, "GPU Memory (GB)"))
            bandwidth_gbps = float(value(row, "Memory Bandwidth GB/s"))
            tdp_w = float(value(row, "TDP Max Power Consumption (W)"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid Lenovo numeric field for {identity}") from exc
        if min(gpu_count, memory_gb, bandwidth_gbps, tdp_w) <= 0:
            raise ValueError(f"Invalid Lenovo numeric field for {identity}")
        candidate = {
            "product_id": row["p_id"],
            "product_name": row["p_name"],
            "description": value(row, "Description"),
            "form_factor": value(row, "Form factor "),
            "gpu_count": gpu_count,
            "part_number": part_number,
            "feature_code": feature_code,
            "announcement_date": value(row, "Announcement date"),
            "withdrawal_date": value(row, "Withdrawal date")
            if "Withdrawal date" in attributes
            else None,
            "architecture": value(row, "GPU Architecture"),
            "memory_type": value(row, "GPU Memory type"),
            "memory_gb_per_gpu": memory_gb,
            "memory_bandwidth_gbps_per_gpu": bandwidth_gbps,
            "nvlink": value(row, "NVIDIA NVLink") if "NVIDIA NVLink" in attributes else None,
            "interconnect": value(row, "Interconnect Bandwidth (GB/sec)")
            if "Interconnect Bandwidth (GB/sec)" in attributes
            else None,
            "host_interface": value(row, "Host Interface")
            if "Host Interface" in attributes
            else None,
            "mig": value(row, "Multi-Instance GPU (MIG)")
            if "Multi-Instance GPU (MIG)" in attributes
            else None,
            "tdp_w_per_gpu": tdp_w,
            "cooling_method": value(row, "Cooling method"),
            "performance": {
                label: value(row, label)
                for label in attributes
                if label.startswith("Peak ") and value(row, label) is not None
            },
            "locator": f"current comparison row {row['p_name']} ({identity})",
        }
        if identity in candidates:
            raise ValueError(f"Duplicate Lenovo orderable identity {identity}")
        candidates[identity] = candidate
    if len(candidates) != expected_count:
        raise ValueError(
            f"Changed Lenovo available inventory shape: {len(candidates)} != {expected_count}"
        )
    return {
        "source_url": source_url,
        "sha256": hashlib.sha256(content).hexdigest(),
        "review_required": True,
        "candidates": [candidates[key] for key in sorted(candidates)],
    }
