"""Stage the downloaded EU inventory; grant status never becomes plant status."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.innovation_fund import parse_innovation_fund_html

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(
        json.dumps(parse_innovation_fund_html(args.html.read_bytes()), indent=2) + "\n"
    )
