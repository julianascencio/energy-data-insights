"""Select a reviewed GEM partition only after verifying the complete accepted set."""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from typing import Any


def select_reviewed_gem_batch(
    rows: list[dict[str, Any]],
    *,
    review: dict[str, Any],
    summary: dict[str, Any],
    batch: int,
) -> list[dict[str, Any]]:
    """Validate a disjoint, exhaustive ledger and return one unchanged partition.

    This is publication selection, not a new acceptance or deduplication decision.
    A partial input, altered ID set, duplicate row or inconsistent batch ledger
    fails before any output. Country counts and every partition count are checked.
    """
    ids = [row["record_id"] for row in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate accepted record ID")
    digest = hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
    if digest != review["accepted_ids_sha256"] or len(rows) != review["accepted"]:
        raise ValueError("Complete reviewed GEM identity set required")
    if len(rows) != summary["new_projects"]:
        raise ValueError("Summary/review count mismatch")
    if any(
        row["entity_type"] != "projects" or review["source_id"] not in row["sources"]
        for row in rows
    ):
        raise ValueError("Unexpected entity or source in GEM batch")
    prefixes: set[str] = set()
    numbers: set[int] = set()
    selected = None
    for partition in summary["batches"]:
        number = partition["batch"]
        start, end = partition["prefix_start"], partition["prefix_end"]
        if (
            number in numbers
            or not re.fullmatch(r"[0-9a-f]{2}", start)
            or not re.fullmatch(r"[0-9a-f]{2}", end)
            or start > end
        ):
            raise ValueError("Invalid batch number or prefix range")
        numbers.add(number)
        covered = {f"{i:02x}" for i in range(int(start, 16), int(end, 16) + 1)}
        if prefixes & covered:
            raise ValueError("Overlapping batch prefix ranges")
        prefixes.update(covered)
        subset = [row for row in rows if row["record_id"][:2] in covered]
        countries = dict(Counter(row["country_code"] for row in subset))
        if (
            len(subset) != partition["new_projects"]
            or countries != partition["new_country_counts"]
            or len(countries) != partition["countries"]
        ):
            raise ValueError("Batch counts or country distribution changed")
        if number == batch:
            selected = subset
    if prefixes != {f"{i:02x}" for i in range(256)}:
        raise ValueError("Batch ledger does not cover all UUID prefixes")
    if selected is None:
        raise ValueError("Unknown batch number")
    return sorted(selected, key=lambda row: row["record_id"])
