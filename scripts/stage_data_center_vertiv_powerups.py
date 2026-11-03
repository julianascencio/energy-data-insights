"""Stage explicit Vertiv PowerUPS 6000 topology/rating configurations."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_vertiv_powerups6000_table,
)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("capture", type=Path, help="Layout-preserving UTF-8 PDF text")
parser.add_argument("--source-url", required=True)
parser.add_argument("--expected-count", type=int)
args = parser.parse_args()
print(
    json.dumps(
        parse_vertiv_powerups6000_table(
            args.capture.read_bytes(),
            source_url=args.source_url,
            expected_count=args.expected_count,
        ),
        ensure_ascii=False,
        indent=2,
    )
)
