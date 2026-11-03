"""Stage one explicit STULZ CyberAir 3PRO DX R410A table for review."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.data_center_catalogue.portfolios import (
    parse_stulz_cyberair_3pro_dx_modulating_table,
    parse_stulz_cyberair_3pro_dx_table,
)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("capture", type=Path, help="Layout-preserving UTF-8 text from the PDF")
parser.add_argument("--source-url", required=True)
parser.add_argument("--expected-count", type=int)
parser.add_argument(
    "--compressor",
    choices=("fixed-speed", "modulating-ec"),
    default="fixed-speed",
)
args = parser.parse_args()
adapter = (
    parse_stulz_cyberair_3pro_dx_modulating_table
    if args.compressor == "modulating-ec"
    else parse_stulz_cyberair_3pro_dx_table
)
print(
    json.dumps(
        adapter(
            args.capture.read_bytes(),
            source_url=args.source_url,
            expected_count=args.expected_count,
        ),
        ensure_ascii=False,
        indent=2,
    )
)
