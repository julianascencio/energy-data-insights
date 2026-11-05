"""Offline Spanish BOE battery discovery and checksum-pinned notice inspection.

Titles select review candidates only. A battery mention can be a procurement,
wind addendum, or several projects; none automatically becomes a canonical site.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from typing import Any


def _xml(content: bytes) -> ET.Element:
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("External declarations are not accepted")
    try:
        return ET.fromstring(content)
    except ET.ParseError as exc:
        raise ValueError("Invalid BOE XML") from exc


def select_battery_notices(content: bytes, *, expected_date: str) -> list[dict[str, str]]:
    """Select all battery-title mentions across every daily issue and section."""
    root = _xml(content)
    if (
        root.findtext("status/code") != "200"
        or root.findtext(".//sumario/metadatos/fecha_publicacion") != expected_date
    ):
        raise ValueError("BOE response/date mismatch")
    out = []
    seen = set()
    for item in root.findall(".//item"):
        title = item.findtext("titulo", "")
        if "bater" not in title.casefold():
            continue
        ident = item.findtext("identificador", "")
        url = item.findtext("url_xml", "")
        if not re.fullmatch(r"BOE-[AB]-\d{4}-\d+", ident) or ident in seen:
            raise ValueError("Invalid or duplicate notice identifier")
        if url != "https://www.boe.es/diario_boe/xml.php?id=" + ident:
            raise ValueError("Unexpected notice URL")
        seen.add(ident)
        out.append(
            {"notice_id": ident, "title": title, "url": url, "publication_date": expected_date}
        )
    return out


def inspect_notice(content: bytes, *, expected_id: str, sha256: str) -> dict[str, Any]:
    """Return numbered native paragraphs for human field and identity review."""
    if hashlib.sha256(content).hexdigest() != sha256:
        raise ValueError("Original notice checksum mismatch")
    root = _xml(content)
    if root.tag != "documento" or root.findtext("metadatos/identificador") != expected_id:
        raise ValueError("Notice identity mismatch")
    paragraphs = [" ".join("".join(p.itertext()).split()) for p in root.findall("./texto/p")]
    if not paragraphs:
        raise ValueError("Missing notice body")
    return {
        "notice_id": expected_id,
        "publication_date": root.findtext("metadatos/fecha_publicacion"),
        "decision_date": root.findtext("metadatos/fecha_disposicion"),
        "source_updated_at": root.get("fecha_actualizacion"),
        "title": root.findtext("metadatos/titulo"),
        "paragraphs": paragraphs,
    }
