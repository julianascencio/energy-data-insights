"""Stage a reviewed local Solar MD SS70xx-05 table; never fetch or upsert."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.solarmd import parse_ss70xx

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("input", type=Path, help="JSON ten-row table from PDF page 4")
parser.add_argument("--edition", required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
args.output.write_text(
    json.dumps(parse_ss70xx(json.loads(args.input.read_text()), edition=args.edition), indent=2)
    + "\n"
)
