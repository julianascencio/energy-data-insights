"""Stage public identity and design metrics from one Raxio facility page."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.portfolios import parse_raxio_facility_page

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("capture", type=Path, help="Captured official facility HTML")
parser.add_argument("--source-url", required=True)
parser.add_argument("--expected-code")
args = parser.parse_args()
print(
    json.dumps(
        parse_raxio_facility_page(
            args.capture.read_bytes(),
            source_url=args.source_url,
            expected_code=args.expected_code,
        ),
        ensure_ascii=False,
        indent=2,
    )
)
