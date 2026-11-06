"""Replay reviewed Nepal DoED construction-licence identities, optionally verifying source text."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.doed import new_record, parse_inventory
from energy_data_retrieval.hydro_catalogue.era import accept_new

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--html", type=Path)
args = parser.parse_args()
root = Path("catalogues/hydro")
batch = json.loads((root / "research/doed-20261106-0001-0100.json").read_text())
if args.html and parse_inventory(args.html.read_text()) != batch["parsed_inventory"]:
    raise ValueError("Source drift requires review")
print(
    accept_new(
        root,
        batch,
        root / "records/projects/doed-20261106-0001-0100.jsonl",
        record_factory=new_record,
    )
)
