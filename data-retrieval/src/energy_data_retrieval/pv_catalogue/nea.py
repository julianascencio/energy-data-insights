"""Offline staging of NEA monthly centralized-PV registration attachments.

Registration is not commissioning, operation or proof of whole-project scope.
This reader returns review candidates only; it never creates canonical records.
"""

from __future__ import annotations

import hashlib
import io
import math
import re
import xml.etree.ElementTree as ET
import zipfile
from typing import Any

NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
HEADERS = ["序号", "项目编码", "项目名称", "装机容量(MW)", "项目所在地"]


def _text(element: ET.Element) -> str:
    return "".join(node.text or "" for node in element.findall(".//w:t", NS)).strip()


def read_nea_pv_registrations(content: bytes, *, sha256: str) -> list[dict[str, Any]]:
    """Verify pinned DOCX bytes and the explicitly labelled centralized-PV table."""
    if hashlib.sha256(content).hexdigest() != sha256:
        raise ValueError("NEA source checksum changed")
    if len(content) > 10_000_000:
        raise ValueError("NEA attachment exceeds size bound")
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        member = archive.getinfo("word/document.xml")
        if member.file_size > 5_000_000:
            raise ValueError("NEA document XML exceeds size bound")
        xml = archive.read(member)
    if b"<!DOCTYPE" in xml or b"<!ENTITY" in xml:
        raise ValueError("Unsupported XML declarations")
    body = ET.fromstring(xml).find("w:body", NS)
    if body is None:
        raise ValueError("Missing document body")
    heading = ""
    cohorts = []
    for element in body:
        if element.tag == f"{{{NS['w']}}}p":
            heading = _text(element) or heading
        elif element.tag == f"{{{NS['w']}}}tbl":
            label = re.fullmatch(
                r"[一二三四五六七八九十]+、集中式光伏发电[\uff08(](\d+)个[\uff09)]", heading
            )
            if label:
                cohorts.append((element, int(label[1])))
            heading = ""
    if len(cohorts) != 1:
        raise ValueError("Expected one explicit centralized photovoltaic cohort")
    table, expected = cohorts[0]
    rows = [[_text(cell) for cell in row.findall("w:tc", NS)] for row in table.findall("w:tr", NS)]
    if not rows or rows[0] != HEADERS or not 1 <= expected <= 500 or len(rows) != expected + 1:
        raise ValueError("NEA public schema or cohort count changed")
    result = []
    seen = set()
    for index, cells in enumerate(rows[1:], start=1):
        if len(cells) != 5:
            raise ValueError("Unexpected/private columns or merged cells")
        sequence, code, name, power, locality = cells
        if sequence != str(index) or not re.fullmatch(r"PPC\d{13}[A-Z0-9]", code) or code in seen:
            raise ValueError("Invalid, duplicate or non-centralized-PV registry code")
        if not name or not locality or not re.fullmatch(r"\d+(?:\.\d+)?", power):
            raise ValueError("Missing identity or ambiguous capacity")
        capacity = float(power)
        if not math.isfinite(capacity) or capacity <= 0:
            raise ValueError("Invalid native registered capacity")
        seen.add(code)
        result.append(
            {
                "registry_code": code,
                "native_name": name,
                "native_locality": locality,
                "registered_capacity_mw": capacity,
                "capacity_basis": "Native installed MW; AC/DC unspecified",
                "locator": f"Centralized-PV table; row {index}; project code {code}",
                "review_flags": [
                    "Registration does not establish construction, commissioning or operation",
                    "Reconcile project codes, local names and phases before canonical upsert",
                    "Do not derive dates or coordinates from the registry code or locality",
                ],
            }
        )
    return result
