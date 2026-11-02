"""Stage ADB IATI battery activities without treating financing as physical assets."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Any


def stage_adb_battery_activities(content: bytes) -> list[dict[str, Any]]:
    """Return source-native observations, excluding contacts and country centroids.

    Activity status and dates describe financing implementation, not plant COD.
    Separate loan/guarantee activities need manual physical-project reconciliation.
    """
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("DTD/entity declarations are not supported")
    root = ET.fromstring(content)
    if root.tag != "iati-activities" or root.get("version") != "2.03":
        raise ValueError("Expected IATI 2.03 activities")
    rows = []
    seen = set()
    for activity in root.findall("iati-activity"):
        identifier = activity.findtext("iati-identifier", "").strip()
        if not identifier.startswith("XM-DAC-46004-"):
            raise ValueError("Expected ADB activity identifier")
        if identifier in seen:
            raise ValueError("Duplicate activity identifier")
        seen.add(identifier)
        title = " ".join(activity.findtext("title/narrative", "").split())
        descriptions = [
            " ".join(element.itertext()).strip() for element in activity.findall("description")
        ]
        if not re.search(r"\b(?:battery|batteries|BESS)\b", " ".join([title, *descriptions]), re.I):
            continue
        status = activity.find("activity-status")
        rows.append(
            {
                "activity_id": identifier,
                "title": title,
                "descriptions": descriptions,
                "generated_at": root.get("generated-datetime"),
                "updated_at": activity.get("last-updated-datetime"),
                "activity_status_code": status.get("code") if status is not None else None,
                "activity_dates": [dict(e.attrib) for e in activity.findall("activity-date")],
                "implementing_entities": [
                    " ".join(e.findtext("narrative", "").split())
                    for e in activity.findall("participating-org")
                    if e.get("role") == "4"
                ],
            }
        )
    return rows
