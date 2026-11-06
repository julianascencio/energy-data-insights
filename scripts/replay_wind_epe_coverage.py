"""Verify all-state EPE roster coverage without accepting additional projects."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.wind_catalogue.epe import audit_coverage, parse_id_response


def main() -> None:
    """Verify saved candidates, explicit empty queries, and the national roster."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    parser.add_argument("--originals", type=Path)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_text())
    partitions = {}
    for state, entry in audit["partitions"].items():
        ids = entry["ids"]
        if entry.get("ledger"):
            path = Path(entry["ledger"])
            if path.name != str(path):
                raise ValueError("Ledger paths must be basenames")
            ledger = json.loads((args.audit.parent / path).read_text())
            candidates = ledger["all_reviewed_candidates"]
            if (
                sorted(c["object_id"] for c in candidates) != sorted(ids)
                or any(c["original"]["sigufprincipal"] != state for c in candidates)
                or ledger["reviewed"] != len(ids)
                or ledger["complete_selected_partition"] is not True
            ):
                raise ValueError("Coverage differs from reviewed partition")
        elif ids:
            raise ValueError("Populated partition has no reviewed ledger")
        partitions[state] = ids
    for query in audit["queries"]:
        if query["before_ids"] != query["after_ids"]:
            raise ValueError("Coverage ID query drift")
        if args.originals is not None:
            for when in ("before", "after"):
                name = query[when + "_file"]
                if Path(name).name != name:
                    raise ValueError("Capture filenames must be basenames")
                ids = parse_id_response(
                    (args.originals / name).read_bytes(), query[when + "_sha256"]
                )
                if ids != query[when + "_ids"]:
                    raise ValueError("Coverage IDs differ from original response")
    by_scope = {q["scope"]: q for q in audit["queries"]}
    required = {"national", "unknown"} | {s for s, ids in partitions.items() if not ids}
    if len(by_scope) != len(audit["queries"]) or set(by_scope) != required:
        raise ValueError("Missing, duplicate, or unexpected coverage queries")
    for state, ids in partitions.items():
        if not ids and by_scope[state]["before_ids"] != []:
            raise ValueError("Empty state has nonempty query")
    result = audit_coverage(
        partitions,
        expected_ids=by_scope["national"]["before_ids"],
        confirmed_ids=by_scope["national"]["after_ids"],
        unknown_state_ids=by_scope["unknown"]["before_ids"],
    )
    if result != audit["result"]:
        raise ValueError("Coverage result differs from audit")
    print(f"Verified {result['reviewed_ids']} IDs across 27 states; no record writes")


if __name__ == "__main__":
    main()
