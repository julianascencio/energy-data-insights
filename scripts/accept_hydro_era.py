"""Replay reviewed ERA identities; optionally reparse the original workbook."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.era import accept_new, parse_inventory

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--workbook", type=Path)
args = parser.parse_args()
root = Path("catalogues/hydro")
batch = json.loads((root / "research/era-202609-reviewed.json").read_text())
if args.workbook and parse_inventory(args.workbook.read_bytes()) != batch["parsed_inventory"]:
    raise ValueError("Source drift; review before replay")
print(accept_new(root, batch, root / "records/projects/era-202609-new.jsonl"))
