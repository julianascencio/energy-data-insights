"""Replay reviewed KenGen annual observations; optionally verify original PDF text."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.kengen import enrich_reviewed, parse_statistics
from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, required=True)
    parser.add_argument(
        "--text", type=Path, help="pdftotext -layout output for source verification"
    )
    args = parser.parse_args()
    batch = json.loads(args.batch.read_text())
    if args.text:
        parsed = parse_statistics(args.text.read_text())
        if parsed != batch["parsed_inventory"]:
            raise ValueError("Source statistics changed; review before replay")
    count = replay_reviewed(
        Path("catalogues/hydro"),
        batch["accepted"],
        lambda row, entry: enrich_reviewed(row, entry, now=batch["reviewed_at"]),
    )
    print(f"Enriched {count} reviewed KenGen identities")


if __name__ == "__main__":
    main()
