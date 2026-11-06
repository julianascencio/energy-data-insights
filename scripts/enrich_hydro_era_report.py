"""Replay the reviewed ERA historical station assertions."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.era_report import enrich_reviewed, parse_annex
from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed

root = Path("catalogues/hydro")
batch = json.loads((root / "research/era-report-20261106.json").read_text())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--text", type=Path)
args = parser.parse_args()
if args.text and parse_annex(args.text.read_text()) != batch["parsed_inventory"]:
    raise ValueError("Report drift requires review")
print(
    replay_reviewed(
        root,
        batch["accepted"],
        lambda row, entry: enrich_reviewed(row, entry, now=batch["reviewed_at"]),
    )
)
