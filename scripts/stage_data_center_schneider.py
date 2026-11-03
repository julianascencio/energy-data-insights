"""Stage extracted Schneider Galaxy VS model-list text for source review."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_schneider_galaxy_vs_model_list,
)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("capture", type=Path, help="UTF-8 text produced from the official PDF")
parser.add_argument("--source-url", required=True)
parser.add_argument("--expected-count", type=int)
args = parser.parse_args()
print(
    json.dumps(
        parse_schneider_galaxy_vs_model_list(
            args.capture.read_bytes(),
            source_url=args.source_url,
            expected_count=args.expected_count,
        ),
        ensure_ascii=False,
        indent=2,
    )
)
