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
    rows: list[dict[str, Any]] = []
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


def parse_2026_grants(content: bytes) -> list[dict[str, Any]]:
    """Stage the 45-row final C21-i18/2026 table, never physical projects.

    GGS charging observations have no unit in this table and are retained as
    unit-unspecified strings, not MW. Zero funding is not an awarded grant.
    Applicant names and company tax identifiers are deliberately not exported.
    """
    text = content.decode("utf-8-sig")
    required = (
        "após sorteio de desempate",
        "01/C21-i18/2026",
        "Totalizador",
        "Capacidade de",
        "(MWh)",
        "[GGS]",
        "80 250 000,00 EUR",
    )
    if not all(token in text for token in required):
        raise ValueError("Unreviewed 2026 final table headers or control total")
    money = r"(\d{1,3}(?: \d{3})*,\d{2})"
    number = r"(\d+(?: \d{3})*,\d+)"
    pattern = re.compile(
        r"^\s*(\d+)\s+.+?\s+\d{9}\s+"
        + money
        + r"\s+EUR\s+"
        + money
        + r"\s+EUR\s+"
        + number
        + r"\s+"
        + number
        + r"\s+\d+\s+\d+\s+\d+\s+\d+\s+.+?\s+"
        + r"(Elegível com proposta favorável de financiamento|"
        + r"Elegível sem proposta de financiamento)\s*$"
    )
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if not re.match(r"^\s*\d+\s+", line):
            continue
        match = pattern.fullmatch(line)
        if match is None:
            raise ValueError(f"Malformed candidate row at line {line_number}")
        values = [Decimal(match[i].replace(" ", "").replace(",", ".")) for i in range(2, 6)]
        eligible, grant, energy, ggs = values
        favorable = "favorável" in match[6]
        if min(values) < 0 or energy <= 0 or (grant > 0) != favorable or grant > eligible:
            raise ValueError("Inconsistent funding, energy or classification")
        rows.append(
            {
                "application_id": match[1],
                "programme": "01/C21-i18/2026",
                "eligible_cost_eur": str(eligible),
                "proposed_funding_eur": str(grant),
                "storage_energy_mwh": str(energy),
                "energy_basis": "unspecified",
                "ggs_charging_observation": str(ggs),
                "ggs_unit": None,
                "favorable_funding_proposal": favorable,
                "locator": f"PDF page 1; application {match[1]}; text line {line_number}",
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
                "requires_identity_and_reuse_review": True,
            }
        )
    if len(rows) != 45 or len({r["application_id"] for r in rows}) != 45:
        raise ValueError("Expected 45 distinct application IDs")
    if sum(Decimal(r["proposed_funding_eur"]) for r in rows) != Decimal("80250000.00"):
        raise ValueError("Funding control total mismatch")
    return rows
