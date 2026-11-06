"""Replay explicit ONS registry/name crosswalks; never discover alias matches."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.ons import enrich, enrich_dispatch_metadata
from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    batch = json.loads(parser.parse_args().batch.read_text())
    count = replay_reviewed(
        Path("catalogues/hydro"),
        batch["accepted"],
        lambda row, entry: enrich_dispatch_metadata(
            enrich(
                row,
                entry["inventory"],
                source_id=entry["source_id"],
                identity_source_id="wri_brazil_identity",
                now=batch["reviewed_at"],
                review=entry["review"],
            ),
            now=batch["reviewed_at"],
        ),
    )
    print(f"Applied {count} explicitly reviewed ONS alias enrichments")


if __name__ == "__main__":
    main()
