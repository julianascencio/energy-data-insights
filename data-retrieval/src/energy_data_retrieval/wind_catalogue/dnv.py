"""Offline dated DNV register selection; applicants are not inferred manufacturers."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime
from typing import Any

HEADER = (
    "CERTIFICATION SCHEME",
    "CERTIFICATION SCHEME LONG",
    "CUSTOMER/APPLICANT",
    "CERTIFICATE/STATEMENT",
    "IDENTIFICATION OF OBJECT/PROJECT",
    "DATE ISSUED",
    "VALID UNTIL",
)


def gearbox_partition(rows: Iterable[tuple[Any, ...]]) -> list[dict[str, Any]]:
    """Select complete DNV-SE-0074 gearbox mentions, including non-equipment holds.

    Keep statements, applicants and expired dates exactly scoped to the register.
    This does not establish present validity or infer equipment specifications.
    """
    return component_partition(rows, gearbox_mentions=True)


def component_partition(
    rows: Iterable[tuple[Any, ...]], *, gearbox_mentions: bool
) -> list[dict[str, Any]]:
    """Select one exhaustive complementary text partition, not a component taxonomy.

    A model without the word gearbox falls in the non-mention partition even if
    it is a gearbox. Statement scope and applicant remain uninterpreted.
    """
    rows = iter(rows)
    if tuple(next(rows, ())) != HEADER:
        raise ValueError("Unexpected DNV register header")
    result = []
    seen = set()
    for number, row in enumerate(rows, 2):
        if len(row) != 7:
            raise ValueError("Unexpected register width")
        if row[0] != "CC DNV-SE-0074" or (
            ("gearbox" in str(row[4]).casefold()) != gearbox_mentions
        ):
            continue
        if not row[3] or row[3] in seen:
            raise ValueError("Missing or duplicate certificate identifier")
        seen.add(row[3])
        dates = []
        for value in row[5:]:
            if value is not None and not isinstance(value, (date, datetime)):
                raise ValueError("Expected Excel date or null")
            dates.append(
                value.date().isoformat()
                if isinstance(value, datetime)
                else value.isoformat()
                if value
                else None
            )
        result.append(
            dict(
                row=number,
                scheme=row[0],
                applicant=row[2],
                certificate=row[3],
                object=row[4],
                issued=dates[0],
                valid_until=dates[1],
            )
        )
    return result
