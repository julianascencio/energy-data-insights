"""Stage the reviewed EFFEKTA BTL overview from local pdftotext -layout text.

No network or automatic identity reconciliation. C20 monobloc Ah is not cell
capacity or energy. Overall terminal height is kept apart from case height.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

SOURCE_URL = "https://www.effekta.com/download/btl-reihe-datenblatt/?wpdmdl=365"


def parse_btl_table(content: bytes, *, source_url: str) -> list[dict[str, Any]]:
    """Fail on unreviewed units, duplicate models and malformed model rows."""
    if source_url != SOURCE_URL:
        raise ValueError("Expected reviewed EFFEKTA BTL source URL")
    text = content.decode("utf-8-sig")
    for marker in ("BTL series", "AGM", "in Ah (C20)", "H (mm)", "Terminal"):
        if marker not in text:
            raise ValueError(f"Missing reviewed header: {marker}")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for line in text.splitlines():
        # Product photographs on page 1 are not specification rows.
        if not re.match(r"^BTL 12-", line):
            continue
        match = re.fullmatch(
            r"(BTL 12-\d+(?: L| LX| S)?)\s+"
            r"(\d+)\s+(\d+)\s+([\d.,]+)\s+(\d+)\s+(\d+)\s+"
            r"(\d+)\s+([\d.]+)\s+(F2|M5|M6|M8)\s*",
            line,
        )
        if not match:
            raise ValueError("Unrecognized BTL specification row")
        model, *values, terminal = match.groups()
        if model in seen:
            raise ValueError(f"Duplicate exact model: {model}")
        seen.add(model)
        voltage, ah, length, width, height, total_height, mass = (
            float(v.replace(",", ".")) for v in values
        )
        if min(voltage, ah, length, width, height, total_height, mass) <= 0:
            raise ValueError("Nonpositive specification")
        if voltage != 12 or total_height < height:
            raise ValueError("Unexpected voltage or terminal height")
        rows.append(
            {
                "model": model,
                "voltage_v": voltage,
                "monobloc_capacity_ah_c20": ah,
                "length_mm": length,
                "width_mm": width,
                "case_height_mm": height,
                "overall_height_mm": total_height,
                "weight_kg": mass,
                "terminal": terminal,
                "source_url": source_url,
                "locator": f"PDF page 2 / printed 129, {model} row",
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    if not rows:
        raise ValueError("No BTL specification rows")
    return rows
