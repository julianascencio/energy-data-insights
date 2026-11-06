"""Reproduce the reviewed EIA hydro enrichment from retained bounded evidence."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.eia import enrich
from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("catalogues/hydro"))
    parser.add_argument("--batch", type=Path)
    args = parser.parse_args()
    root = args.root
    batch_path = args.batch or root / "research/eia-2025-0001-0500.json"
    batch = json.loads(batch_path.read_text())
    count = replay_reviewed(
        root,
        batch["accepted"],
        lambda row, entry: enrich(
            row,
            entry["inventory"],
            source_id=batch["source_id"],
            identity_source_id="wri_usa_identity",
            now=batch["reviewed_at"],
        ),
    )
    print(f"Applied {count} EIA enrichments; no new plant identities")


if __name__ == "__main__":
    main()
