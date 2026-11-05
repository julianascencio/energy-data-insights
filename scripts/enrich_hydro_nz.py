"""Reproduce the reviewed NZ hydro enrichment from retained bounded evidence."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.nz import enrich_reviewed as enrich
from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed


def main() -> None:
    root = Path("catalogues/hydro")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, default=root / "research/nz-reviewed-20261105.json")
    batch = json.loads(parser.parse_args().batch.read_text())
    count = replay_reviewed(
        root,
        batch["accepted"],
        lambda row, entry: enrich(
            row,
            entry["inventory"],
            owner_source_id=entry["owner_source_id"],
            reviewed_record_id=row["record_id"],
            now=batch["reviewed_at"],
        ),
    )
    print(f"Applied {count} NZ enrichments; no new plant identities")


if __name__ == "__main__":
    main()
