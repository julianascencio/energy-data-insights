"""Validate a complete reviewed enrichment batch before writing any JSONL shard."""

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def replay_reviewed(
    root: Path,
    accepted: list[dict[str, Any]],
    transform: Callable[[dict[str, Any], dict[str, Any]], dict[str, Any]],
) -> int:
    """Reject duplicate/missing identities and transformation conflicts before writes.

    The callback receives an existing record and its explicitly reviewed entry.
    Unreviewed records are preserved. This is validation-before-write, not a
    filesystem transaction; an I/O failure still requires deterministic replay.
    """
    lookup = {entry["record_id"]: entry for entry in accepted}
    if len(lookup) != len(accepted):
        raise ValueError("Duplicate reviewed record identity")
    seen: set[str] = set()
    staged: dict[Path, str] = {}
    for path in sorted((root / "records").rglob("*.jsonl")):
        original = path.read_text()
        rows = [json.loads(line) for line in original.splitlines()]
        for i, row in enumerate(rows):
            identity = row["record_id"]
            if identity in seen:
                raise ValueError("Duplicate canonical record identity")
            seen.add(identity)
            if identity in lookup:
                created_at = row["created_at"]
                updated = transform(row, lookup[identity])
                if updated["record_id"] != identity or updated["created_at"] != created_at:
                    raise ValueError("Replay changed immutable identity or creation date")
                rows[i] = updated
        text = "".join(canonical_json(row) + "\n" for row in rows)
        if text != original:
            staged[path] = text
    if missing := lookup.keys() - seen:
        raise ValueError(f"Reviewed identities absent from catalogue: {sorted(missing)}")
    for path, text in staged.items():
        path.write_text(text)
    return len(lookup)
