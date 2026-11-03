#!/usr/bin/env python3
"""Stage identities from an offline Africa Data Centres page capture."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_africa_data_centres_footprint,
)

parser = argparse.ArgumentParser()
parser.add_argument("capture", type=Path)
parser.add_argument("--source-url", required=True)
args = parser.parse_args()
print(
    json.dumps(
        parse_africa_data_centres_footprint(args.capture.read_bytes(), source_url=args.source_url),
        indent=2,
        sort_keys=True,
    )
)
