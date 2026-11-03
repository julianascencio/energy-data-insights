"""Stage the reviewed PGE four-lot eForms notice; never resolve site identities."""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from typing import Any


def parse_pge_notice(content: bytes) -> list[dict[str, Any]]:
    """Extract named candidates from notice 719197-2026, version 01.

    This source-specific adapter checks the tender, lot sizes and battery CPV.
    CPV supports battery classification, not chemistry, capacity or operation.
    Lot-level NUTS codes are deliberately omitted: each lot spans several sites.
    Contact names, email addresses and phone numbers are never returned.
    """
    if b"<!DOCTYPE" in content.upper() or b"<!ENTITY" in content.upper():
        raise ValueError("DTD/entity declarations are not accepted")
    root = ET.fromstring(content)
    if (
        root.tag != "{urn:oasis:names:specification:ubl:schema:xsd:ContractNotice-2}ContractNotice"
        or root.findtext("{*}ID") != "5e67cf82-9d8c-4e4f-ad98-d8c202232abd"
        or root.findtext("{*}VersionID") != "01"
        or root.findtext("{*}IssueDate") != "2026-10-16Z"
        or root.findtext("{*}ProcurementProject/{*}ID") != "POST/EOD/EOD/BM/00319/2026"
    ):
        raise ValueError("Unreviewed PGE notice or revision")
    lots = root.findall("{*}ProcurementProjectLot")
    if [lot.findtext("{*}ID") for lot in lots] != ["LOT-0001", "LOT-0002", "LOT-0003", "LOT-0004"]:
        raise ValueError("Missing, repeated or reordered lots")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for lot, expected_count in zip(lots, [5, 6, 6, 5], strict=True):
        lot_id = lot.findtext("{*}ID")
        project = lot.find("{*}ProcurementProject")
        if project is None:
            raise ValueError("Missing lot project")
        cpv = [x.text for x in project.findall(".//{*}ItemClassificationCode")]
        if "31440000" not in cpv:
            raise ValueError("Missing explicit battery procurement classification")
        title = project.findtext("{*}Name") or ""
        names = re.findall(r"MEE (.*?)(?=, MEE | oraz MEE |$)", title.rstrip("."))
        if len(names) != expected_count:
            raise ValueError("Unreviewed site-list layout or count")
        duration = project.find("{*}PlannedPeriod/{*}DurationMeasure")
        if duration is None or duration.text != "28" or duration.get("unitCode") != "MONTH":
            raise ValueError("Unreviewed delivery period")
        for position, name in enumerate(names, 1):
            if name in seen:
                raise ValueError("Duplicate incoming site name; review identity")
            seen.add(name)
            rows.append(
                {
                    "source_site_name": name,
                    "notice_id": "719197-2026",
                    "notice_version": "01",
                    "lot_id": lot_id,
                    "site_position_in_lot": position,
                    "battery_classification": "CPV 31440000 in this storage-construction lot",
                    "required_delivery_months": 28,
                    "review_required": True,
                    "original_xml_sha256": hashlib.sha256(content).hexdigest(),
                }
            )
    return rows
