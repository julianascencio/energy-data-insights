"""Stage named atNorth/CoolIT inventory links from a reviewed offline capture."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.inventories import parse_named_inventory

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("capture", type=Path)
parser.add_argument("--source-url", required=True)
parser.add_argument("--expected-count", type=int, required=True)
args = parser.parse_args()
print(
    json.dumps(
        parse_named_inventory(
            args.capture.read_bytes(),
            source_url=args.source_url,
            expected_count=args.expected_count,
        ),
        ensure_ascii=False,
        indent=2,
    )
)
