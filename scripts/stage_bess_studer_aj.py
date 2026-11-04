"""Stage a local AJ OEM page; identities and reuse require separate review."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.studer_aj import MODELS, parse_aj_html

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--series", choices=sorted(MODELS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(parse_aj_html(args.html.read_bytes(), args.series), indent=2) + "\n"
    )
