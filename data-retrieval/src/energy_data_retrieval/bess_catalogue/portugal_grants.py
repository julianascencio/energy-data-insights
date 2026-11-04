"""Stage application IDs and grants from the reviewed Portuguese final report.

This adapter does not establish reuse rights or physical project identities.
Input is local pdftotext -layout output of version 1.1 (8 April 2025). Applicant
names, preliminary tables, MVA charging limits and project status are not inferred.
"""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal
from typing import Any


def parse_final_grants(content: bytes) -> list[dict[str, Any]]:
    """Stage all 41 final awards, preserving inconsistent cumulative amounts."""
    text = content.decode("utf-8-sig")
    if "Versão: 1.1" not in text or "08 de abril de 2025" not in text:
        raise ValueError("Unreviewed report version")
    pages = text.split("\f")
    if len(pages) < 28:
        raise ValueError("Expected final tables on PDF pages 27 and 28")
    first = "Tabela 1 deste Relatório Final"
    last = "Tabela 2 deste Relatório Final"
    table = pages[26] + pages[27].split(last)[0]
    if first not in pages[26] or last not in pages[27] or "Lista definitiva" not in table:
        raise ValueError("Missing final award table boundaries")
    rows = []
    previous = Decimal(0)
    money = r"(\d{1,3}(?: \d{3})*,\d{2})"
    pattern = re.compile(r"^\s*(\d+)\s+(\d+)\s+.*?" + money + r"\s*€\s+" + money + r"\s*€\s*$")
    for page_no, page in [(27, pages[26]), (28, pages[27].split(last)[0])]:
        for line in page.splitlines():
            m = pattern.fullmatch(line)
            if not m:
                continue
            rank, application = int(m[1]), int(m[2])
            grant = Decimal(m[3].replace(" ", "").replace(",", "."))
            cumulative = Decimal(m[4].replace(" ", "").replace(",", "."))
            if grant <= 0 or cumulative <= 0:
                raise ValueError("Nonpositive funding")
            difference = cumulative - previous - grant
            rows.append(
                {
                    "rank": rank,
                    "application_id": str(application),
                    "grant_eur": str(grant),
                    "reported_cumulative_eur": str(cumulative),
                    "cumulative_arithmetic_difference_eur": str(difference),
                    "locator": f"PDF page {page_no}, final Table 1, rank {rank}",
                    "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
                    "requires_identity_and_reuse_review": True,
                }
            )
            previous = cumulative
    if [r["rank"] for r in rows] != list(range(1, 42)):
        raise ValueError("Expected all 41 final ranks in source order")
    if len({r["application_id"] for r in rows}) != 41:
        raise ValueError("Duplicate application IDs")
    return rows
