"""Stage Meta's complete displayed global data-center fleet for review."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.portfolios import parse_meta_locations

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("capture", type=Path, help="Captured official HTML")
parser.add_argument("--source-url", required=True)
parser.add_argument("--expected-count", type=int)
args = parser.parse_args()
print(
    json.dumps(
        parse_meta_locations(
            args.capture.read_bytes(),
            source_url=args.source_url,
            expected_count=args.expected_count,
        ),
        ensure_ascii=False,
        indent=2,
    )
)
