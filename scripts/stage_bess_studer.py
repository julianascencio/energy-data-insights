"""Stage a downloaded Studer product page; no network or canonical writes."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.studer import parse_studer_html

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--series", choices=["xtm", "xth", "xts"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(parse_studer_html(args.html.read_bytes(), args.series), indent=2) + "\n"
    )
