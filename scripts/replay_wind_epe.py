"""Check a reviewed EPE batch against the canonical catalogue without writes."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.wind_catalogue import load_records
from energy_data_retrieval.wind_catalogue.epe import reconcile, verify_capture


def main() -> None:
    """Verify every accepted observation is already present and unchanged."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("batch", type=Path)
    parser.add_argument("--root", type=Path, default=Path("catalogues/wind"))
    parser.add_argument(
        "--originals", type=Path, help="Verify retained original response bytes too"
    )
    args = parser.parse_args()
    batch = json.loads(args.batch.read_text())
    if args.originals is not None:
        verify_capture(batch, args.originals)
    rows = load_records(args.root)
    accepted, decisions = reconcile(
        batch["all_reviewed_candidates"],
        rows,
        source_id=batch["source_id"],
        identity_source_id="wri-brazil-ceg-identity",
        now=batch["retrieved_at"],
    )
    by_id = {row["record_id"]: row for row in rows}
    if any(row != by_id[row["record_id"]] for row in accepted):
        raise ValueError("Batch has unapplied or changed observations")
    if decisions != batch["decisions"]:
        raise ValueError("Identity decisions differ from reviewed ledger")
    print(f"Verified {len(accepted)} unchanged records; {len(decisions)} decisions; no writes")


if __name__ == "__main__":
    main()
