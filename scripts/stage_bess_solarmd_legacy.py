"""Stage a reviewed local Solar MD unsuffixed SS7000 table; never fetch or upsert."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.solarmd import parse_legacy_ss7000

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("input", type=Path, help="JSON eleven-row table from PDF page 9")
parser.add_argument("--revision", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output.write_text(
    json.dumps(
        parse_legacy_ss7000(json.loads(args.input.read_text()), revision=args.revision), indent=2
    )
    + "\n"
)
