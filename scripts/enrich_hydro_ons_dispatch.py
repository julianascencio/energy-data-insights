"""Replay reviewed ONS dispatch/state metadata without replacing unit observations."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.ons import enrich_dispatch_metadata
from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    batch = json.loads(parser.parse_args().batch.read_text())
    count = replay_reviewed(
        Path("catalogues/hydro"),
        batch["accepted"],
        lambda row, entry: enrich_dispatch_metadata(row, now=batch["reviewed_at"]),
    )
    print(f"Enriched {count} existing ONS records with dispatch/state metadata")


if __name__ == "__main__":
    main()
