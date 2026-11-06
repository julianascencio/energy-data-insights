"""Replay historical AHA provenance enrichment without changing physical ratings."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.aha_provenance import enrich_provenance
from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    batch = json.loads(parser.parse_args().batch.read_text())
    count = replay_reviewed(
        Path("catalogues/hydro"),
        batch["accepted"],
        lambda row, entry: enrich_provenance(row, now=batch["reviewed_at"]),
    )
    print(f"Enriched field provenance for {count} existing identities")


if __name__ == "__main__":
    main()
