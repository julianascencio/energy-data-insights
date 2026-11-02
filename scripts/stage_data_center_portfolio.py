"""Stage a captured NEXTDC or ODATA portfolio for explicit source review."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.portfolios import parse_portfolio

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("capture", type=Path)
parser.add_argument("--source-url", required=True)
args = parser.parse_args()
print(
    json.dumps(
        parse_portfolio(args.capture.read_bytes(), source_url=args.source_url),
        ensure_ascii=False,
        indent=2,
    )
)
