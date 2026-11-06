"""Replay reviewed ERA construction/licensed identities, optionally verifying source text."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.era import accept_new
from energy_data_retrieval.hydro_catalogue.era_planned import new_record
from energy_data_retrieval.hydro_catalogue.era_report import parse_annex

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--text", type=Path)
args = parser.parse_args()
root = Path("catalogues/hydro")
batch = json.loads((root / "research/era-planned-20261106.json").read_text())
if args.text and parse_annex(args.text.read_text()) != batch["parsed_inventory"]:
    raise ValueError("Source drift requires review")
print(
    accept_new(
        root, batch, root / "records/projects/era-planned-20261106.jsonl", record_factory=new_record
    )
)
